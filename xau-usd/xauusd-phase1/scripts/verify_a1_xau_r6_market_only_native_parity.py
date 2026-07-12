"""Deterministic verifier/finalizer for the locked NP1 native evidence packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import build_a1_xau_r6_market_only_native_parity_oracle as B


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONTRACT = ROOT / "docs" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_SOURCE_CONTRACT_V1.json"
OUTPUT_SCHEMA = ROOT / "docs" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_OUTPUT_SCHEMA_V1.json"
LOCK_MANIFEST = ROOT / "outputs" / "manifests" / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_LOCK_MANIFEST_V1.json"
STATE_CODES = {"UNKNOWN": 0, "SHOCK": 1, "UPTREND": 2, "DOWNTREND": 3, "COMPRESSION": 4, "CHOP": 5}
NATIVE_TO_CANONICAL = {name.lower(): name for name in STATE_CODES}


@dataclass
class Buckets:
    invalid: list[str] = field(default_factory=list)
    source: list[str] = field(default_factory=list)
    zero_action: list[str] = field(default_factory=list)
    parity: list[str] = field(default_factory=list)

    def all(self) -> list[str]:
        return [*self.invalid, *self.source, *self.zero_action, *self.parity]


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
    if any(not hasattr(module, item) for item in required):
        raise RuntimeError("PYTHON_ROUTER_AUTHORITY_MISMATCH")
    return module


def read_tsv(path: Path, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if list(reader.fieldnames or ()) != list(expected_columns):
            raise ValueError(f"TSV header mismatch: {path}")
        return list(reader)


def write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def verify_source_equivalence(path: Path, generated_source: Path) -> list[str]:
    errors: list[str] = []
    payload = read_json(path)
    source = B.assert_pinned_source().decode("utf-8")
    generated = generated_source.read_text(encoding="utf-8")
    rows = payload.get("blocks", [])
    if len(rows) != len(B.BLOCK_NAMES):
        errors.append("source-equivalence block count mismatch")
    for row in rows:
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
    return [
        f"required assertion did not pass: {assertion_id}"
        for assertion_id in contract["required_assertion_ids"]
        if not by_id.get(assertion_id)
        or any(row["passed"].lower() != "true" for row in by_id[assertion_id])
    ]


def parse_native_report(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    def metric(label: str) -> int:
        patterns = (
            rf"{re.escape(label)}\s*:?</td>\s*<td[^>]*>\s*([0-9,]+)",
            rf"{re.escape(label)}\s*[:=]\s*([0-9,]+)",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(",", ""))
        raise ValueError(f"native report missing {label}")
    return metric("Total Trades"), metric("Total Deals")


def verify_compile_packet(compiled: Path, buckets: Buckets) -> None:
    source = compiled / B.ORACLE_NAME
    ex5 = compiled / Path(B.ORACLE_NAME).with_suffix(".ex5").name
    log = compiled / "compile_A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY.log"
    equivalence = compiled / "source_equivalence.json"
    for path in (source, ex5, log, equivalence):
        if not path.is_file() or path.stat().st_size == 0:
            buckets.invalid.append(f"compiled artifact missing or empty: {path.name}")
    if buckets.invalid:
        return
    try:
        B.verify_generated_source(source)
        buckets.source.extend(verify_source_equivalence(equivalence, source))
    except (RuntimeError, ValueError, KeyError) as exc:
        buckets.source.append(str(exc))
    text = log.read_text(encoding="utf-8-sig", errors="replace")
    for required in ("MetaEditor executable version: 5.0.0.5833", "0 errors", "0 warnings"):
        if required not in text:
            buckets.invalid.append(f"compile log missing proof: {required}")


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_bar_rows(path: Path, schema: dict[str, Any], router: Any) -> tuple[list[dict[str, str]], list[Any]]:
    rows = read_tsv(path, schema["bar_exports"]["columns"])
    times = [_dt(row["open_time_broker"]) for row in rows]
    if times != sorted(set(times)):
        raise ValueError(f"bar timestamps not unique/increasing: {path.name}")
    bars = [router.Bar(times[i], float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])) for i, row in enumerate(rows)]
    router.validate_bars(bars)
    return rows, bars


def prefix_sha(rows: Sequence[dict[str, str]], columns: Sequence[str], decision: datetime) -> tuple[str, str]:
    causal = [
        row for row, next_row in zip(rows, rows[1:])
        if _dt(next_row["open_time_broker"]) <= decision
    ]
    if not causal:
        raise ValueError("causal prefix is empty")
    data = ("\n".join("\t".join(row[column] for column in columns) for row in causal) + "\n").encode()
    return causal[-1]["open_time_broker"], hashlib.sha256(data).hexdigest()


def _close(native: float, python: float, rule: dict[str, float]) -> tuple[bool, float]:
    if not math.isfinite(native) or not math.isfinite(python):
        return False, math.inf
    difference = abs(native - python)
    limit = max(rule["absolute_tolerance"], rule["relative_tolerance"] * max(abs(native), abs(python)))
    return difference <= limit, difference


def python_metrics(router: Any, h1: Sequence[Any], h4: Sequence[Any], d1: Sequence[Any], decision: datetime) -> tuple[str, dict[str, float]]:
    state = router.classify_router(h1=h1, h4=h4, d1=d1, decision=decision)
    if state == "UNKNOWN":
        return state, {}
    h1_i, h4_i, d1_i = (router._last_completed_index(bars, decision) for bars in (h1, h4, d1))
    h1_atr, d1_atr = router.wilder_atr(h1), router.wilder_atr(d1)
    h4_fast, h4_slow = router.ema([bar.close for bar in h4[: h4_i + 1]], 20), router.ema([bar.close for bar in h4[: h4_i + 1]], 50)
    d1_fast, d1_slow = router.ema([bar.close for bar in d1[: d1_i + 1]], 20), router.ema([bar.close for bar in d1[: d1_i + 1]], 50)
    d1_60 = [value for value in d1_atr[d1_i - 59 : d1_i + 1] if value is not None]
    d1_252 = [value for value in d1_atr[d1_i - 251 : d1_i + 1] if value is not None]
    five = d1[d1_i - 4 : d1_i + 1]
    box_high, box_low = max(bar.high for bar in five), min(bar.low for bar in five)
    width = box_high - box_low
    median_range = router.median([bar.high - bar.low for bar in d1[d1_i - 19 : d1_i + 1]])
    return state, {
        "h1_atr14_shift1": h1_atr[h1_i],
        "h1_shock_ratio": (h1[h1_i].high - h1[h1_i].low) / h1_atr[h1_i],
        "h4_ema20_shift1": h4_fast[h4_i], "h4_ema50_shift1": h4_slow[h4_i],
        "h4_ema20_shift6": h4_fast[h4_i - 5], "h4_ema50_shift6": h4_slow[h4_i - 5],
        "d1_ema20_shift1": d1_fast[d1_i], "d1_ema50_shift1": d1_slow[d1_i],
        "d1_ema20_shift2": d1_fast[d1_i - 1], "d1_ema50_shift2": d1_slow[d1_i - 1],
        "d1_ema20_shift6": d1_fast[d1_i - 5], "d1_ema50_shift6": d1_slow[d1_i - 5],
        "d1_ema20_shift7": d1_fast[d1_i - 6], "d1_ema50_shift7": d1_slow[d1_i - 6],
        "d1_atr14_shift1": d1_atr[d1_i],
        "d1_atr_percentile_60_shift1": router.percentile_rank(d1_60, d1_atr[d1_i]),
        "d1_atr_percentile_252_shift1": router.percentile_rank(d1_252, d1_atr[d1_i]),
        "d1_box_high_5": box_high, "d1_box_low_5": box_low, "d1_box_width_5": width,
        "d1_box_average_5": width / 5.0, "d1_median_range_20": median_range,
        "d1_compression_box_to_median_ratio": (width / 5.0) / median_range,
    }


NUMERIC_RULE = {
    "h1_atr14_shift1": "atr", "h1_shock_ratio": "atr",
    "h4_ema20_shift1": "ema", "h4_ema50_shift1": "ema", "h4_ema20_shift6": "ema", "h4_ema50_shift6": "ema",
    "d1_ema20_shift1": "ema", "d1_ema50_shift1": "ema", "d1_ema20_shift2": "ema", "d1_ema50_shift2": "ema",
    "d1_ema20_shift6": "ema", "d1_ema50_shift6": "ema", "d1_ema20_shift7": "ema", "d1_ema50_shift7": "ema",
    "d1_atr14_shift1": "atr", "d1_atr_percentile_60_shift1": "percentile", "d1_atr_percentile_252_shift1": "percentile",
    "d1_box_high_5": "compression_metrics", "d1_box_low_5": "compression_metrics", "d1_box_width_5": "compression_metrics",
    "d1_box_average_5": "compression_metrics", "d1_median_range_20": "compression_metrics",
    "d1_compression_box_to_median_ratio": "compression_metrics",
}


def verify_router_run(run_id: str, run_dir: Path, source: dict[str, Any], schema: dict[str, Any], buckets: Buckets, source_equivalence_sha256: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    router = load_python_router(source)
    try:
        h1_rows, h1 = load_bar_rows(run_dir / "native_h1_bars.tsv", schema, router)
        h4_rows, h4 = load_bar_rows(run_dir / "native_h4_bars.tsv", schema, router)
        d1_rows, d1 = load_bar_rows(run_dir / "native_d1_bars.tsv", schema, router)
        native = read_tsv(run_dir / "native_router_rows.tsv", schema["native_router_rows"]["columns"])
    except (FileNotFoundError, ValueError, KeyError) as exc:
        buckets.invalid.append(f"{run_id}: {exc}")
        return [], [], {}
    start = _dt(schema["native_router_rows"]["evidence_interval_from_inclusive"])
    end = _dt(schema["native_router_rows"]["evidence_interval_to_exclusive"])
    expected = [row["open_time_broker"] for row in h4_rows if start <= _dt(row["open_time_broker"]) < end]
    actual = [row["timestamp_broker"] for row in native]
    if actual != expected:
        buckets.parity.append(f"{run_id}: H4 decision-row coverage mismatch expected={len(expected)} actual={len(actual)}")
    for row in native:
        if row["run_id"] != run_id or row["symbol"] != "XAUUSD":
            buckets.invalid.append(f"{run_id}: Router row identity mismatch")
        if row["router_source_commit"] != B.SOURCE_COMMIT or row["router_source_blob"] != B.SOURCE_BLOB:
            buckets.source.append(f"{run_id}: Router row source lineage mismatch")
        if row["source_equivalence_sha256"] != source_equivalence_sha256:
            buckets.source.append(f"{run_id}: Router row source-equivalence hash mismatch")
    acceptance = schema["parity"]["acceptance"]
    parity_rows: list[dict[str, Any]] = []
    prefix_rows: list[dict[str, Any]] = []
    states = Counter()
    max_diff = {name: 0.0 for name in ("ema", "atr", "percentile", "compression_metrics")}
    first_mismatch = ""
    for row in native:
        try:
            decision = _dt(row["timestamp_broker"])
            python_state, metrics = python_metrics(router, h1, h4, d1, decision)
            canonical_native = NATIVE_TO_CANONICAL.get(row["state_name"], "INVALID")
            native_code = int(row["state_code"])
            state_match = canonical_native == python_state and native_code == STATE_CODES[python_state]
            available_match = (row["data_available"].lower() == "true") == (python_state != "UNKNOWN")
            states[canonical_native] += 1
            mismatch_fields: list[str] = []
            if not state_match:
                mismatch_fields.append("state")
            if not available_match:
                mismatch_fields.append("data_available")
            for field_name, python_value in metrics.items():
                if not row[field_name]:
                    mismatch_fields.append(field_name)
                    continue
                rule_name = NUMERIC_RULE[field_name]
                matched, difference = _close(float(row[field_name]), float(python_value), acceptance[rule_name])
                max_diff[rule_name] = max(max_diff[rule_name], difference)
                if not matched:
                    mismatch_fields.append(field_name)
            if python_state == "UNKNOWN" and any(row[name] for name in NUMERIC_RULE):
                mismatch_fields.append("unavailable_numeric_not_empty")
            h1_last, h1_hash = prefix_sha(h1_rows, schema["bar_exports"]["columns"], decision)
            h4_last, h4_hash = prefix_sha(h4_rows, schema["bar_exports"]["columns"], decision)
            d1_last, d1_hash = prefix_sha(d1_rows, schema["bar_exports"]["columns"], decision)
            if row["h1_shift1_time"] != h1_last or row["h4_shift1_time"] != h4_last or row["d1_shift1_time"] != d1_last:
                mismatch_fields.append("causal_prefix_last_completed_time")
            if mismatch_fields:
                buckets.parity.append(f"{run_id}: parity mismatch {row['timestamp_broker']}: {','.join(mismatch_fields)}")
                first_mismatch = first_mismatch or f"{row['timestamp_broker']}:{mismatch_fields[0]}"
            parity_rows.append({
                "run_id": run_id, "timestamp_broker": row["timestamp_broker"], "symbol": row["symbol"],
                "native_data_available": row["data_available"], "python_data_available": str(python_state != "UNKNOWN").lower(),
                "native_state_code": native_code, "python_state_code": STATE_CODES[python_state],
                "native_state_name": canonical_native, "python_state_name": python_state,
                "state_exact_match": str(state_match).lower(), "data_available_exact_match": str(available_match).lower(),
                "ema_max_absolute_difference": max_diff["ema"], "atr_max_absolute_difference": max_diff["atr"],
                "percentile_max_absolute_difference": max_diff["percentile"],
                "compression_metric_max_absolute_difference": max_diff["compression_metrics"],
                "first_mismatch_field": mismatch_fields[0] if mismatch_fields else "",
            })
            prefix_rows.append({
                "run_id": run_id, "timestamp_broker": row["timestamp_broker"], "symbol": row["symbol"],
                "h1_last_completed_time": h1_last, "h1_prefix_sha256": h1_hash,
                "h4_last_completed_time": h4_last, "h4_prefix_sha256": h4_hash,
                "d1_last_completed_time": d1_last, "d1_prefix_sha256": d1_hash,
            })
        except (ValueError, KeyError, IndexError, ZeroDivisionError) as exc:
            buckets.parity.append(f"{run_id}: Router parity row invalid: {exc}")
    total = len(native)
    summary = {
        "run_id": run_id, "native_decision_rows": total, "expected_h4_decisions": len(expected),
        "state_counts": dict(sorted(states.items())), "first_mismatch": first_mismatch,
        "ema_max_absolute_difference": max_diff["ema"], "atr_max_absolute_difference": max_diff["atr"],
        "percentile_max_absolute_difference": max_diff["percentile"],
        "compression_metric_max_absolute_difference": max_diff["compression_metrics"],
    }
    return parity_rows, prefix_rows, summary


def verify_ordercalcprofit(run_id: str, run_dir: Path, schema: dict[str, Any], buckets: Buckets) -> list[dict[str, Any]]:
    contract = schema["native_ordercalcprofit"]
    try:
        probes = read_tsv(run_dir / contract["file"], contract["columns"])
        contract_rows = read_tsv(run_dir / "native_contract.tsv", schema["contract_snapshot"]["columns"])
    except (FileNotFoundError, ValueError) as exc:
        buckets.invalid.append(f"{run_id}: {exc}")
        return []
    if len(contract_rows) != 1 or any(value == "" for value in contract_rows[0].values()):
        buckets.invalid.append(f"{run_id}: contract snapshot incomplete")
        return []
    c = contract_rows[0]
    expected_contract = {
        "server": "Capital.ComMena-Demo", "company": "Capital Com Mena Securities Trading L.L.C",
        "account_login": "1025742", "account_currency": "USD", "account_leverage": "50", "symbol": "XAUUSD",
    }
    for key, expected in expected_contract.items():
        if c.get(key) != expected:
            buckets.invalid.append(f"{run_id}: contract environment mismatch {key}={c.get(key)!r}")
    ids = [row["probe_id"] for row in probes]
    if ids != contract["required_probe_ids"] or len(probes) != 12:
        buckets.invalid.append(f"{run_id}: OrderCalcProfit probe identity/order mismatch")
    rows: list[dict[str, Any]] = []
    rule = schema["parity"]["acceptance"]["ordercalcprofit_absolute_loss"]
    tick_size, tick_value_loss = float(c["tick_size"]), float(c["tick_value_loss"])
    for probe in probes:
        if probe["success"].lower() != "true" or probe["evidence_class"] != contract["evidence_class"]:
            buckets.invalid.append(f"{run_id}: native OrderCalcProfit probe failed {probe['probe_id']}")
            continue
        python_loss = abs(float(probe["exit_price"]) - float(probe["entry_price"])) / tick_size * tick_value_loss * float(probe["volume"])
        native_loss = float(probe["absolute_loss"])
        matched, difference = _close(native_loss, python_loss, {
            "absolute_tolerance": rule["absolute_tolerance_account_currency"], "relative_tolerance": rule["relative_tolerance"]
        })
        if not matched:
            buckets.parity.append(f"{run_id}: OrderCalcProfit parity mismatch {probe['probe_id']}")
        rows.append({
            "run_id": run_id, "probe_id": probe["probe_id"], "native_absolute_loss": native_loss,
            "python_absolute_loss": python_loss, "absolute_difference": difference, "match": str(matched).lower(),
        })
    return rows


def normalized_tsv_bytes(path: Path, *, blank_columns: set[str]) -> bytes:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = list(reader.fieldnames or ())
        rows = list(reader)
    for row in rows:
        for column in blank_columns:
            if column in row:
                row[column] = "<NORMALIZED>"
    lines = ["\t".join(columns), *("\t".join(row[column] for column in columns) for row in rows)]
    return ("\n".join(lines) + "\n").encode()


def verify_two_run_determinism(evidence_dir: Path, buckets: Buckets) -> None:
    rules = {
        "native_router_rows.tsv": {"run_id"}, "native_h1_bars.tsv": set(), "native_h4_bars.tsv": set(),
        "native_d1_bars.tsv": set(), "native_contract.tsv": {"timestamp_broker"},
        "native_ordercalcprofit.tsv": set(), "native_assertions.tsv": set(),
    }
    for filename, blank in rules.items():
        try:
            first = normalized_tsv_bytes(evidence_dir / "runs" / "run1" / filename, blank_columns=blank)
            second = normalized_tsv_bytes(evidence_dir / "runs" / "run2" / filename, blank_columns=blank)
            if first != second:
                buckets.parity.append(f"two-run normalized mismatch: {filename}")
        except (FileNotFoundError, ValueError) as exc:
            buckets.invalid.append(f"two-run determinism input invalid: {exc}")


def verify_ini(path: Path, run_id: str, buckets: Buckets) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        buckets.invalid.append(f"{run_id}: tester.ini missing")
        return
    required = (
        "Expert=A1XauR6MarketOnlyNativeParityOracle.ex5", "Symbol=XAUUSD", "Period=M5", "Model=4",
        "FromDate=2015.06.01", "ToDate=2026.07.01", "Deposit=10000", "Currency=USD", "Leverage=50",
        f"InpRunId={run_id}",
        f"InpRouterRowsFileName=np1_{run_id}_native_router_rows.tsv",
        f"InpH1BarsFileName=np1_{run_id}_native_h1_bars.tsv",
        f"InpH4BarsFileName=np1_{run_id}_native_h4_bars.tsv",
        f"InpD1BarsFileName=np1_{run_id}_native_d1_bars.tsv",
        f"InpContractFileName=np1_{run_id}_native_contract.tsv",
        f"InpOrderCalcProfitFileName=np1_{run_id}_native_ordercalcprofit.tsv",
        f"InpAssertionsFileName=np1_{run_id}_native_assertions.tsv",
        f"InpOrderZeroFileName=np1_{run_id}_order.zero",
        f"InpDealZeroFileName=np1_{run_id}_deal.zero",
        "UseRemote=0", "UseCloud=0", "Optimization=0",
    )
    missing = [value for value in required if value not in text]
    if missing:
        buckets.invalid.append(f"{run_id}: tester.ini/effective-input mismatch {missing}")
    if any(value in text for value in ("Login=", "Server=", "Profile=", "Chart=", "Visual=1")):
        buckets.invalid.append(f"{run_id}: tester.ini contains prohibited runtime settings")


def status_for(buckets: Buckets) -> str:
    if buckets.invalid:
        return "R6_NP1_EVIDENCE_INVALID"
    if buckets.source:
        return "R6_NP1_SOURCE_EQUIVALENCE_FAIL"
    if buckets.zero_action:
        return "R6_NP1_ZERO_ACTION_CONTRACT_FAIL"
    if buckets.parity:
        return "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_FAIL"
    return "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS"


def _write_reports(evidence_dir: Path, status: str, buckets: Buckets, metrics: dict[str, Any]) -> None:
    payload = {
        "schema_version": "a1_xau_r6_market_only_native_parity_exact_v1", "status": status,
        "boundary": {"census_generated": False, "pnl_calculated": False, "broker_action": False},
        "errors": {"invalid": buckets.invalid, "source": buckets.source, "zero_action": buckets.zero_action, "parity": buckets.parity},
        "metrics": metrics,
    }
    json_path = evidence_dir / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# A1 XAU R6 Market-Only Native-Parity Exact Evidence", "", f"Status: `{status}`", "",
        "No R6 census, P/L, exit, target, MFE, MAE, demo/live, or broker action was produced.", "", "## Errors", "",
    ]
    errors = buckets.all()
    lines.extend([f"- {error}" for error in errors] if errors else ["- None"])
    (evidence_dir / "A1_XAU_R6_MARKET_ONLY_NATIVE_PARITY_EXACT_20260712.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    (evidence_dir / "test_validation.md").write_text(
        f"# NP1 Validation\n\nTerminal status: `{status}`\n\nError count: `{len(errors)}`\n",
        encoding="utf-8", newline="\n",
    )


def generate_manifest(evidence_dir: Path, schema: dict[str, Any]) -> None:
    excluded = {"manifest.json", "manifest.sha256"}
    expected = set(schema["exact_tree"]) - excluded
    actual = {path.relative_to(evidence_dir).as_posix() for path in evidence_dir.rglob("*") if path.is_file()} - excluded
    if actual != expected:
        raise ValueError(f"cannot generate manifest for incomplete/unexpected tree: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    rows = [
        {"relative_path": relative, "size_bytes": (evidence_dir / relative).stat().st_size, "sha256": sha256_file(evidence_dir / relative)}
        for relative in sorted(expected)
    ]
    manifest = evidence_dir / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": "a1_xau_r6_evidence_manifest_v1", "artifacts": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (evidence_dir / "manifest.sha256").write_text(sha256_file(manifest) + "\n", encoding="ascii", newline="\n")


def verify_nonrecursive_manifest(evidence_dir: Path, schema: dict[str, Any]) -> list[str]:
    manifest, sidecar = evidence_dir / "manifest.json", evidence_dir / "manifest.sha256"
    if not manifest.is_file() or not sidecar.is_file():
        return ["manifest pair missing"]
    payload = read_json(manifest)
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return ["manifest artifacts must be a list"]
    errors: list[str] = []
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
    if sidecar.read_text(encoding="ascii") != sha256_file(manifest) + "\n":
        errors.append("manifest.sha256 mismatch")
    return errors


def finalize_evidence_directory(evidence_dir: Path) -> VerificationResult:
    source, schema, _ = load_contracts()
    buckets = Buckets()
    metrics: dict[str, Any] = {}
    verify_compile_packet(evidence_dir / "compiled", buckets)
    equivalence_path = evidence_dir / "compiled" / "source_equivalence.json"
    source_equivalence_sha256 = sha256_file(equivalence_path) if equivalence_path.is_file() else ""
    parity_rows: list[dict[str, Any]] = []
    prefix_rows: list[dict[str, Any]] = []
    ordercalc_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for run_id in ("run1", "run2"):
        run_dir = evidence_dir / "runs" / run_id
        verify_ini(run_dir / "tester.ini", run_id, buckets)
        try:
            assertion_errors = verify_assertions(run_dir / "native_assertions.tsv", schema)
            for error in assertion_errors:
                if any(name in error for name in ("report_zero_trades", "report_zero_deals", "order_zero_bytes", "deal_zero_bytes", "open_positions_zero", "pending_orders_zero")):
                    buckets.zero_action.append(f"{run_id}: {error}")
                else:
                    buckets.invalid.append(f"{run_id}: {error}")
            trades, deals = parse_native_report(run_dir / "native_report.htm")
            if trades != 0 or deals != 0:
                buckets.zero_action.append(f"{run_id}: native report trades={trades} deals={deals}")
            for sentinel in ("order.zero", "deal.zero"):
                if not (run_dir / sentinel).is_file() or (run_dir / sentinel).stat().st_size != 0:
                    buckets.zero_action.append(f"{run_id}: {sentinel} is missing or nonempty")
        except (FileNotFoundError, ValueError) as exc:
            buckets.invalid.append(f"{run_id}: {exc}")
        rows, prefixes, summary = verify_router_run(run_id, run_dir, source, schema, buckets, source_equivalence_sha256)
        parity_rows.extend(rows); prefix_rows.extend(prefixes); summaries.append(summary)
        ordercalc_rows.extend(verify_ordercalcprofit(run_id, run_dir, schema, buckets))
    verify_two_run_determinism(evidence_dir, buckets)
    parity_dir = evidence_dir / "parity"
    router_columns = ["run_id", *schema["parity"]["router_parity_columns"]]
    prefix_columns = ["run_id", *schema["parity"]["native_prefix_chain_hashes_columns"]]
    order_columns = ["run_id", *schema["parity"]["ordercalcprofit_parity_columns"]]
    write_csv(parity_dir / "router_python_native_parity.csv", router_columns, parity_rows)
    write_csv(parity_dir / "native_prefix_chain_hashes.csv", prefix_columns, prefix_rows)
    write_csv(parity_dir / "ordercalcprofit_python_native_parity.csv", order_columns, ordercalc_rows)
    write_csv(parity_dir / "router_state_summary.csv", ["run_id", "native_decision_rows", "expected_h4_decisions", "state_counts", "first_mismatch", "ema_max_absolute_difference", "atr_max_absolute_difference", "percentile_max_absolute_difference", "compression_metric_max_absolute_difference"], [
        {**row, "state_counts": json.dumps(row.get("state_counts", {}), sort_keys=True)} for row in summaries
    ])
    metrics["runs"] = summaries
    status = status_for(buckets)
    _write_reports(evidence_dir, status, buckets, metrics)
    try:
        generate_manifest(evidence_dir, schema)
    except ValueError as exc:
        buckets.invalid.append(str(exc))
        status = status_for(buckets)
        _write_reports(evidence_dir, status, buckets, metrics)
        try:
            generate_manifest(evidence_dir, schema)
        except ValueError:
            pass
    return VerificationResult(status, tuple(buckets.all()), metrics)


def verify_evidence_directory(evidence_dir: Path) -> VerificationResult:
    result = finalize_evidence_directory(evidence_dir)
    _, schema, _ = load_contracts()
    manifest_errors = verify_nonrecursive_manifest(evidence_dir, schema)
    if manifest_errors:
        errors = (*result.errors, *manifest_errors)
        return VerificationResult("R6_NP1_EVIDENCE_INVALID", tuple(errors), result.metrics)
    return result


def _main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    args = parser.parse_args(argv)
    result = verify_evidence_directory(args.evidence_dir.resolve())
    print(json.dumps({"status": result.status, "errors": result.errors, "metrics": result.metrics}, indent=2))
    return 0 if result.status == "R6_NP1_NATIVE_EVIDENCE_COMPLETE_PYTHON_PARITY_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
