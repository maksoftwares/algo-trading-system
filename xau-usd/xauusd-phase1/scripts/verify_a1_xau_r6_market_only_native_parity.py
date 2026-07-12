"""Fail-closed verifier for the locked NP1 market-only native evidence packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import build_a1_xau_r6_market_only_native_parity_oracle as B


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONTRACT = ROOT / "docs" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_SOURCE_CONTRACT_V1.json"
OUTPUT_SCHEMA = ROOT / "docs" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_OUTPUT_SCHEMA_V1.json"
LOCK_MANIFEST = ROOT / "outputs" / "manifests" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_LOCK_MANIFEST_V1.json"


@dataclass(frozen=True)
class VerificationResult:
    status: str
    errors: tuple[str, ...]
    metrics: dict[str, Any]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def load_contracts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source, schema, manifest = read_json(SOURCE_CONTRACT), read_json(OUTPUT_SCHEMA), read_json(LOCK_MANIFEST)
    for relative, item in manifest["artifacts"].items():
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size != item["size_bytes"] or sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"NP1 lock manifest mismatch: {relative}")
    authority = source["python_router_authority"]
    path = ROOT / authority["path"].removeprefix("xau-usd/xauusd-phase1/")
    if not path.is_file() or sha256_file(path) != authority["sha256"]:
        raise RuntimeError("PYTHON_ROUTER_AUTHORITY_MISMATCH")
    return source, schema, manifest


def load_python_router(source_contract: dict[str, Any]) -> Any:
    authority = source_contract["python_router_authority"]
    path = ROOT / authority["path"].removeprefix("xau-usd/xauusd-phase1/")
    if sha256_file(path) != authority["sha256"]:
        raise RuntimeError("PYTHON_ROUTER_AUTHORITY_MISMATCH")
    name = "a1_xau_r6_pinned_python_router"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("PYTHON_ROUTER_AUTHORITY_MISMATCH")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    required = [authority["function"], *authority["numerical_and_data_dependencies"]]
    missing = [item for item in required if not hasattr(module, item)]
    if missing:
        raise RuntimeError(f"PYTHON_ROUTER_AUTHORITY_MISMATCH: {missing}")
    return module


def read_tsv(path: Path, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if list(reader.fieldnames or ()) != list(expected_columns):
            raise ValueError(f"TSV header mismatch: {path}")
        return list(reader)


def verify_source_equivalence(path: Path, generated_source: Path) -> list[str]:
    errors: list[str] = []
    payload = read_json(path)
    source = B.assert_pinned_source().decode("utf-8")
    generated = generated_source.read_text(encoding="utf-8")
    for row in payload.get("blocks", []):
        source_raw = source.encode()[row["source_start_byte_offset"] : row["source_end_byte_offset"]]
        generated_raw = generated.encode()[row["generated_start_byte_offset"] : row["generated_end_byte_offset"]]
        if source_raw != generated_raw:
            errors.append(f"source block differs: {row.get('signature')}")
        if hashlib.sha256(source_raw).hexdigest() != row.get("source_raw_sha256"):
            errors.append(f"source block hash mismatch: {row.get('signature')}")
        if hashlib.sha256(generated_raw).hexdigest() != row.get("generated_raw_sha256"):
            errors.append(f"generated block hash mismatch: {row.get('signature')}")
        if row.get("exact_equal") is not True:
            errors.append(f"source-equivalence flag false: {row.get('signature')}")
    if len(payload.get("blocks", [])) != len(B.BLOCK_NAMES):
        errors.append("source-equivalence block count mismatch")
    try:
        B.assert_source_safety(generated)
    except RuntimeError as exc:
        errors.append(str(exc))
    return errors


def verify_assertions(path: Path, schema: dict[str, Any]) -> list[str]:
    contract = schema["native_assertions"]
    rows = read_tsv(path, contract["columns"])
    by_id: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_id.setdefault(row["assertion_id"], []).append(row)
    errors = []
    for assertion_id in contract["required_assertion_ids"]:
        matching = by_id.get(assertion_id, [])
        if not matching or any(row["passed"].lower() != "true" for row in matching):
            errors.append(f"required assertion did not pass: {assertion_id}")
    return errors


def verify_nonrecursive_manifest(evidence_dir: Path, schema: dict[str, Any]) -> list[str]:
    manifest_path, sidecar = evidence_dir / "manifest.json", evidence_dir / "manifest.sha256"
    errors: list[str] = []
    if not manifest_path.is_file() or not sidecar.is_file():
        return ["manifest pair missing"]
    payload = read_json(manifest_path)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return ["manifest artifacts must be a list"]
    listed = {row.get("relative_path") for row in artifacts if isinstance(row, dict)}
    if {"manifest.json", "manifest.sha256"} & listed:
        errors.append("manifest pair must be excluded from manifest artifact rows")
    expected = set(schema["exact_tree"]) - {"manifest.json", "manifest.sha256"}
    if listed != expected:
        errors.append("manifest artifact path set mismatch")
    for row in artifacts:
        if not isinstance(row, dict) or set(row) != {"relative_path", "size_bytes", "sha256"}:
            errors.append("manifest artifact row schema mismatch")
            continue
        path = evidence_dir / row["relative_path"]
        if not path.is_file() or path.stat().st_size != row["size_bytes"] or sha256_file(path) != row["sha256"]:
            errors.append(f"manifest artifact mismatch: {row['relative_path']}")
    expected_sidecar = sha256_file(manifest_path) + "\n"
    if sidecar.read_text(encoding="ascii") != expected_sidecar:
        errors.append("manifest.sha256 mismatch")
    return errors


def parse_native_report(path: Path) -> tuple[int, int, list[str]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    errors: list[str] = []
    def metric(label: str) -> int:
        match = re.search(rf"{re.escape(label)}\s*:?</td>\s*<td[^>]*>\s*([0-9,]+)", text, re.IGNORECASE)
        if match is None:
            match = re.search(rf"{re.escape(label)}\s*[:=]\s*([0-9,]+)", text, re.IGNORECASE)
        if match is None:
            errors.append(f"native report missing {label}")
            return -1
        return int(match.group(1).replace(",", ""))
    return metric("Total Trades"), metric("Total Deals"), errors


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_bars(path: Path, schema: dict[str, Any], router: Any) -> list[Any]:
    rows = read_tsv(path, schema["bar_exports"]["columns"])
    bars = [
        router.Bar(_dt(row["open_time_broker"]), float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]))
        for row in rows
    ]
    router.validate_bars(bars)
    return bars


def _close(native: float, python: float, rule: dict[str, float]) -> bool:
    if not math.isfinite(native) or not math.isfinite(python):
        return False
    limit = max(rule["absolute_tolerance"], rule["relative_tolerance"] * max(abs(native), abs(python)))
    return abs(native - python) <= limit


def verify_python_router_parity(run_dir: Path, source: dict[str, Any], schema: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    router = load_python_router(source)
    h1 = load_bars(run_dir / "native_h1_bars.tsv", schema, router)
    h4 = load_bars(run_dir / "native_h4_bars.tsv", schema, router)
    d1 = load_bars(run_dir / "native_d1_bars.tsv", schema, router)
    rows = read_tsv(run_dir / "native_router_rows.tsv", schema["native_router_rows"]["columns"])
    acceptance = schema["parity"]["acceptance"]
    errors: list[str] = []
    state_matches = 0
    availability_matches = 0
    timestamps = [row["timestamp_broker"] for row in rows]
    if timestamps != sorted(set(timestamps)):
        errors.append("native Router decision keys are not unique and ordered")
    for row in rows:
        decision = _dt(row["timestamp_broker"])
        python_state = router.classify_router(h1=h1, h4=h4, d1=d1, decision=decision)
        native_state = row["state_name"]
        state_matches += int(python_state == native_state)
        python_available = python_state != "UNKNOWN"
        native_available = row["data_available"].lower() == "true"
        availability_matches += int(python_available == native_available)
        if python_state != native_state:
            errors.append(f"Router state mismatch at {row['timestamp_broker']}: native={native_state} python={python_state}")
        if python_available != native_available:
            errors.append(f"Router availability mismatch at {row['timestamp_broker']}")
        if python_available:
            h1_i = router._last_completed_index(h1, decision)
            h4_i = router._last_completed_index(h4, decision)
            d1_i = router._last_completed_index(d1, decision)
            h1_atr, d1_atr = router.wilder_atr(h1), router.wilder_atr(d1)
            h4_fast, h4_slow = router.ema([bar.close for bar in h4[: h4_i + 1]], 20), router.ema([bar.close for bar in h4[: h4_i + 1]], 50)
            d1_fast, d1_slow = router.ema([bar.close for bar in d1[: d1_i + 1]], 20), router.ema([bar.close for bar in d1[: d1_i + 1]], 50)
            d1_60 = [value for value in d1_atr[d1_i - 59 : d1_i + 1] if value is not None]
            d1_252 = [value for value in d1_atr[d1_i - 251 : d1_i + 1] if value is not None]
            five = d1[d1_i - 4 : d1_i + 1]
            box_width = max(bar.high for bar in five) - min(bar.low for bar in five)
            median_range = router.median([bar.high - bar.low for bar in d1[d1_i - 19 : d1_i + 1]])
            numeric = {
                "h1_atr14_shift1": (h1_atr[h1_i], "atr"),
                "h1_shock_ratio": ((h1[h1_i].high - h1[h1_i].low) / h1_atr[h1_i], "atr"),
                "h4_ema20_shift1": (h4_fast[h4_i], "ema"),
                "h4_ema50_shift1": (h4_slow[h4_i], "ema"),
                "h4_ema20_shift6": (h4_fast[h4_i - 5], "ema"),
                "h4_ema50_shift6": (h4_slow[h4_i - 5], "ema"),
                "d1_ema20_shift1": (d1_fast[d1_i], "ema"),
                "d1_ema50_shift1": (d1_slow[d1_i], "ema"),
                "d1_ema20_shift2": (d1_fast[d1_i - 1], "ema"),
                "d1_ema50_shift2": (d1_slow[d1_i - 1], "ema"),
                "d1_ema20_shift6": (d1_fast[d1_i - 5], "ema"),
                "d1_ema50_shift6": (d1_slow[d1_i - 5], "ema"),
                "d1_ema20_shift7": (d1_fast[d1_i - 6], "ema"),
                "d1_ema50_shift7": (d1_slow[d1_i - 6], "ema"),
                "d1_atr14_shift1": (d1_atr[d1_i], "atr"),
                "d1_atr_percentile_60_shift1": (router.percentile_rank(d1_60, d1_atr[d1_i]), "percentile"),
                "d1_atr_percentile_252_shift1": (router.percentile_rank(d1_252, d1_atr[d1_i]), "percentile"),
                "d1_box_width_5": (box_width, "compression_metrics"),
                "d1_box_average_5": (box_width / 5.0, "compression_metrics"),
                "d1_median_range_20": (median_range, "compression_metrics"),
                "d1_compression_box_to_median_ratio": ((box_width / 5.0) / median_range, "compression_metrics"),
            }
            for field, (python_value, rule_name) in numeric.items():
                if not row[field] or not _close(float(row[field]), float(python_value), acceptance[rule_name]):
                    errors.append(f"numeric parity mismatch at {row['timestamp_broker']}: {field}")
    total = len(rows)
    metrics = {
        "native_decision_rows": total,
        "state_exact_match_rate": state_matches / total if total else 0.0,
        "data_availability_exact_match_rate": availability_matches / total if total else 0.0,
    }
    if not total:
        errors.append("native Router decision-row coverage is empty")
    return errors, metrics


def verify_ordercalcprofit(run_dir: Path, schema: dict[str, Any]) -> list[str]:
    probe_contract = schema["native_ordercalcprofit"]
    rows = read_tsv(run_dir / probe_contract["file"], probe_contract["columns"])
    ids = [row["probe_id"] for row in rows]
    errors: list[str] = []
    if ids != probe_contract["required_probe_ids"]:
        errors.append("OrderCalcProfit probe identity/order mismatch")
    if any(row["success"].lower() != "true" or row["evidence_class"] != probe_contract["evidence_class"] for row in rows):
        errors.append("OrderCalcProfit native probe failure")
    return errors


def verify_evidence_directory(evidence_dir: Path) -> VerificationResult:
    source, schema, _ = load_contracts()
    errors: list[str] = []
    expected = set(schema["exact_tree"])
    actual = {path.relative_to(evidence_dir).as_posix() for path in evidence_dir.rglob("*") if path.is_file()}
    if actual != expected:
        errors.append("exact evidence tree mismatch")
    errors.extend(verify_nonrecursive_manifest(evidence_dir, schema))
    generated = evidence_dir / "compiled" / B.ORACLE_NAME
    equivalence = evidence_dir / "compiled" / "source_equivalence.json"
    if generated.is_file() and equivalence.is_file():
        errors.extend(verify_source_equivalence(equivalence, generated))
    else:
        errors.append("compiled source/equivalence artifact missing")
    metrics: dict[str, Any] = {}
    for run_id in ("run1", "run2"):
        run_dir = evidence_dir / "runs" / run_id
        try:
            errors.extend(verify_assertions(run_dir / "native_assertions.tsv", schema))
            trades, deals, report_errors = parse_native_report(run_dir / "native_report.htm")
            errors.extend(report_errors)
            if trades != 0 or deals != 0:
                errors.append(f"{run_id} native report is not zero action")
            if (run_dir / "order.zero").stat().st_size != 0 or (run_dir / "deal.zero").stat().st_size != 0:
                errors.append(f"{run_id} zero sentinel is nonempty")
            parity_errors, parity_metrics = verify_python_router_parity(run_dir, source, schema)
            errors.extend(parity_errors)
            errors.extend(verify_ordercalcprofit(run_dir, schema))
            metrics[run_id] = parity_metrics
        except (FileNotFoundError, ValueError, RuntimeError, KeyError, IndexError) as exc:
            errors.append(f"{run_id}: {exc}")
    if any("source block" in error or "source-equivalence" in error for error in errors):
        status = "R6_NP1_SOURCE_EQUIVALENCE_FAIL"
    elif any("zero" in error.lower() or "trade" in error.lower() or "deal" in error.lower() for error in errors):
        status = "R6_NP1_ZERO_ACTION_CONTRACT_FAIL"
    elif errors:
        status = "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"
    else:
        status = "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS"
    return VerificationResult(status, tuple(errors), metrics)


def _main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    args = parser.parse_args(argv)
    result = verify_evidence_directory(args.evidence_dir.resolve())
    print(json.dumps({"status": result.status, "errors": result.errors, "metrics": result.metrics}, indent=2))
    return 0 if result.status == "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
