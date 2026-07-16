from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


DEFAULT_CONTRACT = Path("config/ml/a3_ml_r1_r2_dukascopy_portability_v1.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def month_range(start: str, end: str) -> list[tuple[int, int]]:
    start_year, start_month = (int(value) for value in start.split("-"))
    end_year, end_month = (int(value) for value in end.split("-"))
    if (start_year, start_month) > (end_year, end_month):
        raise ValueError("start month must not be after end month")
    result: list[tuple[int, int]] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        result.append((year, month))
        month += 1
        if month == 13:
            year += 1
            month = 1
    return result


def load_foundation(repo_root: Path) -> Any:
    source = repo_root / "multi-asset" / "data-foundation" / "dukascopy-ticks-v1" / "src"
    if not source.is_dir():
        raise FileNotFoundError(source)
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    return importlib.import_module("dukascopy_tick_foundation.foundation")


def resolve_storage_root(contract: Mapping[str, Any]) -> Path:
    env_name = str(contract["storage_environment_variable"])
    configured = os.environ.get(env_name, "").strip() or str(contract["default_storage_root"])
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


def validate_contract(phase1_root: Path, contract: Mapping[str, Any]) -> None:
    authorization = contract["authorization"]
    forbidden = (
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    )
    if not authorization.get("research_only") or any(authorization.get(key) for key in forbidden):
        raise ValueError("contract contains forbidden authorization")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("this lane is locked to XAUUSD")
    period = contract["period"]
    months = month_range(str(period["start_month"]), str(period["end_month"]))
    if len(months) != int(period["expected_months"]):
        raise ValueError("expected month count does not match the locked period")
    for source in contract["source_lock"]:
        path = phase1_root / str(source["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path) != source["sha256"]:
            raise ValueError(f"source hash mismatch: {source['path']}")
    _validate_mt5_effective_inputs(phase1_root, contract["mt5_effective_input_contract"])


def _validate_mt5_effective_inputs(phase1_root: Path, lock: Mapping[str, Any]) -> None:
    report = json.loads((phase1_root / str(lock["report_path"])).read_text(encoding="utf-8"))
    variants = {row["name"]: row["native_effective_inputs"] for row in report["variants"]}
    for name, required in lock["variants"].items():
        if name not in variants:
            raise ValueError(f"locked MT5 variant is missing: {name}")
        expected = {**lock["common"], **required}
        mismatches = {
            key: {"expected": value, "observed": variants[name].get(key)}
            for key, value in expected.items()
            if str(variants[name].get(key)) != str(value)
        }
        if mismatches:
            raise ValueError(f"MT5 effective input mismatch for {name}: {mismatches}")


def inventory_month(
    storage_root: Path,
    symbol: str,
    year: int,
    month: int,
    foundation: Any,
) -> dict[str, Any]:
    key = f"{year:04d}-{month:02d}"
    root = storage_root / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"
    before = _partition_signature(root)
    try:
        foundation.validate_month_acquisition_manifest(storage_root, symbol, year, month)
    except (foundation.FoundationError, OSError, ValueError, json.JSONDecodeError) as exc:
        status = "MISSING" if not root.is_dir() else "INVALID"
        return {
            "month": key,
            "status": status,
            "frozen": (root / "_FROZEN_MANIFEST.json").is_file(),
            "hour_files": len(list(root.glob("[0-9]*.json"))) if root.is_dir() else 0,
            "bytes": before["bytes"],
            "partition_signature": before["signature"],
            "error": f"{type(exc).__name__}: {exc}",
        }
    after = _partition_signature(root)
    if before != after:
        raise RuntimeError(f"inventory validation mutated a supposedly read-only month: {key}")
    return {
        "month": key,
        "status": "VALID",
        "frozen": (root / "_FROZEN_MANIFEST.json").is_file(),
        "hour_files": len(list(root.glob("[0-9]*.json"))),
        "bytes": after["bytes"],
        "partition_signature": after["signature"],
        "error": "",
    }


def _partition_signature(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        return {"bytes": 0, "signature": ""}
    files = sorted(path for path in root.iterdir() if path.is_file())
    rows = [(path.name, path.stat().st_size, path.stat().st_mtime_ns) for path in files]
    payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return {"bytes": sum(row[1] for row in rows), "signature": hashlib.sha256(payload).hexdigest()}


def inventory_history(
    storage_root: Path,
    symbol: str,
    months: Sequence[tuple[int, int]],
    foundation: Any,
) -> dict[str, Any]:
    rows = [inventory_month(storage_root, symbol, year, month, foundation) for year, month in months]
    counts = Counter(row["status"] for row in rows)
    return {
        "expected_months": len(months),
        "valid_months": counts["VALID"],
        "missing_months": counts["MISSING"],
        "invalid_months": counts["INVALID"],
        "ready": counts["VALID"] == len(months),
        "rows": rows,
    }


def acquire_missing_history(
    storage_root: Path,
    symbol: str,
    months: Sequence[tuple[int, int]],
    foundation: Any,
    *,
    concurrency: int,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    before = inventory_history(storage_root, symbol, months, foundation)
    targets = [row["month"] for row in before["rows"] if row["status"] != "VALID"]
    attempts: list[dict[str, Any]] = []
    for index, key in enumerate(targets, start=1):
        year, month = (int(value) for value in key.split("-"))
        if progress:
            progress(f"[{index}/{len(targets)}] acquiring {symbol} {key}")
        try:
            rows = foundation.acquire_month(
                storage_root, symbol, year, month, concurrency=concurrency
            )
            manifest = foundation.write_month_acquisition_manifest(
                storage_root, symbol, year, month, rows
            )
            foundation.validate_month_acquisition_manifest(storage_root, symbol, year, month)
            frozen = foundation.freeze_raw_month(storage_root, symbol, year, month)
            if not frozen.get("complete"):
                raise RuntimeError("frozen month is incomplete")
            attempts.append(
                {
                    "month": key,
                    "status": "ACQUIRED_VALID",
                    "manifest": str(manifest),
                    "downloaded_hours": sum(row["status"] == "DOWNLOADED_VALID" for row in rows),
                    "resumed_hours": sum(row["status"] == "RESUMED_VALID" for row in rows),
                    "error": "",
                }
            )
        except Exception as exc:
            attempts.append(
                {
                    "month": key,
                    "status": "ACQUISITION_FAILED",
                    "manifest": "",
                    "downloaded_hours": 0,
                    "resumed_hours": 0,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            if progress:
                progress(f"{symbol} {key} failed: {type(exc).__name__}: {exc}")
    after = inventory_history(storage_root, symbol, months, foundation)
    return {"before": before, "targets": targets, "attempts": attempts, "after": after}


def run_history_inventory(
    phase1_root: Path,
    contract_path: Path | None = None,
    *,
    acquire_missing: bool = False,
    concurrency: int = 4,
    selected_months: Sequence[str] | None = None,
    progress: Callable[[str], None] | None = print,
) -> Path:
    phase1_root = phase1_root.resolve()
    contract_file = (contract_path or phase1_root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    validate_contract(phase1_root, contract)
    repo_root = phase1_root.parents[1]
    foundation = load_foundation(repo_root)
    storage_root = resolve_storage_root(contract)
    locked = month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    selected = set(selected_months or [])
    months = [row for row in locked if not selected or f"{row[0]:04d}-{row[1]:02d}" in selected]
    if selected and len(months) != len(selected):
        raise ValueError("one or more selected months fall outside the locked period")
    if acquire_missing:
        acquisition = acquire_missing_history(
            storage_root,
            str(contract["symbol"]),
            months,
            foundation,
            concurrency=concurrency,
            progress=progress,
        )
        inventory = acquisition["after"]
    else:
        acquisition = None
        inventory = inventory_history(storage_root, str(contract["symbol"]), months, foundation)
    payload = {
        "schema_version": contract["schema_version"],
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "ACQUIRE_MISSING" if acquire_missing else "INVENTORY_ONLY",
        "contract": str(contract_file.relative_to(phase1_root)).replace("\\", "/"),
        "contract_sha256": sha256_file(contract_file),
        "storage_root": str(storage_root),
        "symbol": contract["symbol"],
        "locked_period": contract["period"],
        "selected_months": sorted(selected),
        "inventory": inventory,
        "acquisition": acquisition,
        "classification": "DATA_READY" if inventory["ready"] else "DATA_NOT_READY",
        "authorization": contract["authorization"],
    }
    output_json = phase1_root / contract["outputs"]["inventory_json"]
    output_markdown = phase1_root / contract["outputs"]["inventory_markdown"]
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_markdown.write_text(_render_markdown(payload), encoding="utf-8")
    external = storage_root / contract["external_output_subdirectory"] / "source_inventory_latest.json"
    external.parent.mkdir(parents=True, exist_ok=True)
    external.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_json


def _render_markdown(payload: Mapping[str, Any]) -> str:
    inventory = payload["inventory"]
    missing = [row["month"] for row in inventory["rows"] if row["status"] == "MISSING"]
    invalid = [row["month"] for row in inventory["rows"] if row["status"] == "INVALID"]
    lines = [
        "# A3 ML R1/R2 Dukascopy Source Inventory V1",
        "",
        f"Generated UTC: `{payload['generated_at_utc']}`",
        f"Classification: `{payload['classification']}`",
        f"Mode: `{payload['mode']}`",
        "",
        "## Coverage",
        "",
        f"- Expected months: {inventory['expected_months']}",
        f"- Valid months: {inventory['valid_months']}",
        f"- Missing months: {inventory['missing_months']}",
        f"- Invalid months: {inventory['invalid_months']}",
        f"- Missing keys: {', '.join(missing) if missing else 'none'}",
        f"- Invalid keys: {', '.join(invalid) if invalid else 'none'}",
        "",
        "Research only. No model, EA, terminal, account, order, or position was authorized or changed.",
        "",
    ]
    return "\n".join(lines)
