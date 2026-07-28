from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from capture_prospective_neutral_ownership import (
    _cached_hour,
    _day,
    _utc,
    build_h1_bar,
    decode_ticks,
    fetch_hour,
    required_hours,
    sha256_bytes,
    write_immutable,
)
from capture_prospective_neutral_ownership import (
    load_config as load_ownership_config,
)

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "frozen_prospective_neutral_ownership_prewarm_v1.json"
LOCK_PATH = (
    ROOT / "EURUSD_NEUTRAL_PROSPECTIVE_OWNERSHIP_PREWARM_PREREG_2026_07_28.sha256.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-macro-crossasset-agreement-v1/ownership"
)
SCHEMA_VERSION = "eurusd_prospective_neutral_ownership_prewarm_v1"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_prospective_start_and_first_ownership_record")
        is not True
    ):
        raise RuntimeError("Ownership prewarm is not preregistered")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = _sha256_file(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Ownership prewarm lock mismatch: {relative}")
        checked[relative] = actual
    cfg = load_config()
    for section in (
        "ownership_contract",
        "ownership_config",
        "ownership_capture_source",
    ):
        reference = cfg[section]
        if _sha256_file(ROOT / reference["path"]) != reference["sha256"]:
            raise RuntimeError(f"Ownership prewarm reference drift: {section}")
    return checked


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(_serialize(value), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _validate_contract() -> tuple[dict[str, Any], tuple[str, ...]]:
    cfg = load_config()
    ownership = load_ownership_config()
    symbols = tuple(cfg["target"]["symbols"])
    if symbols != tuple(ownership["provider"]["symbols"]):
        raise RuntimeError("Prewarm symbols drifted from ownership contract")
    if int(cfg["target"]["lookback_calendar_days"]) != int(
        ownership["capture"]["lookback_calendar_days"]
    ):
        raise RuntimeError("Prewarm lookback drifted from ownership contract")
    expected = len(symbols) * int(cfg["target"]["lookback_calendar_days"]) * 24
    if expected != int(cfg["target"]["total_required_symbol_hours"]):
        raise RuntimeError("Prewarm total symbol-hour contract is invalid")
    return cfg, symbols


def _cache_reference(
    output_root: Path,
    symbol: str,
    hour: pd.Timestamp,
    *,
    deep_validate: bool,
) -> dict[str, Any] | None:
    cached = _cached_hour(output_root, symbol, hour)
    if cached is None:
        return None
    payload, metadata = cached
    if (
        str(metadata.get("symbol")) != symbol
        or _utc(metadata.get("hour_utc")) != hour
        or _utc(metadata.get("observed_at_utc")) < hour + pd.Timedelta(hours=1)
    ):
        raise RuntimeError("Cached ownership hour linkage drift")
    raw_relative = Path(str(metadata.get("raw_relative_path")))
    expected_parent = Path("raw") / symbol
    if (
        raw_relative.is_absolute()
        or raw_relative.parent != expected_parent
        or not raw_relative.name.startswith(f"{hour:%Y%m%dT%H0000Z}_")
    ):
        raise RuntimeError("Cached ownership raw path drift")
    raw_path = output_root / raw_relative
    metadata_relative = Path("metadata") / symbol / raw_relative.name
    metadata_path = output_root / metadata_relative
    if not raw_path.is_file() or not metadata_path.is_file():
        raise RuntimeError("Cached ownership evidence is incomplete")
    raw_hash = sha256_bytes(payload)
    if raw_hash != str(metadata.get("raw_sha256")):
        raise RuntimeError("Cached ownership payload hash drift")
    if deep_validate:
        ticks = decode_ticks(payload, symbol, hour)
        build_h1_bar(
            ticks,
            hour,
            _utc(metadata["observed_at_utc"]),
        )
    return {
        "symbol": symbol,
        "hour_utc": hour,
        "observed_at_utc": _utc(metadata["observed_at_utc"]),
        "raw_relative_path": raw_relative.as_posix(),
        "raw_sha256": raw_hash,
        "metadata_relative_path": metadata_relative.as_posix(),
        "metadata_sha256": _sha256_file(metadata_path),
    }


def _inventory(
    eligible_date: Any,
    output_root: Path,
    observed_at_utc: Any,
) -> tuple[dict[str, Any], list[tuple[pd.Timestamp, str]]]:
    cfg, symbols = _validate_contract()
    day = _day(eligible_date)
    start = _utc(cfg["prospective_start_utc"])
    if day < start:
        raise ValueError("Prewarm target precedes prospective start")
    observed = _utc(observed_at_utc)
    lag = int(cfg["completion_boundary"]["minimum_lag_after_hour_end_seconds"])
    hours = required_hours(
        day,
        lookback_calendar_days=int(cfg["target"]["lookback_calendar_days"]),
    )
    safe_hours = [
        hour for hour in hours if observed >= hour + pd.Timedelta(hours=1, seconds=lag)
    ]
    pending_hours = len(hours) - len(safe_hours)
    missing: list[tuple[pd.Timestamp, str]] = []
    references: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in symbols}
    for symbol in symbols:
        for hour in safe_hours:
            reference = _cache_reference(
                output_root,
                symbol,
                hour,
                deep_validate=False,
            )
            if reference is None:
                missing.append((hour, symbol))
            else:
                references[symbol].append(reference)
    missing.sort(key=lambda item: (item[0], item[1]))
    per_symbol: dict[str, dict[str, Any]] = {}
    for symbol, rows in references.items():
        digest = hashlib.sha256()
        for row in rows:
            digest.update(row["raw_relative_path"].encode("utf-8"))
            digest.update(bytes.fromhex(row["raw_sha256"]))
            digest.update(bytes.fromhex(row["metadata_sha256"]))
        per_symbol[symbol] = {
            "safely_completed_hours": len(safe_hours),
            "cached_hours": len(rows),
            "missing_hours": len(safe_hours) - len(rows),
            "first_cached_hour_utc": (rows[0]["hour_utc"] if rows else None),
            "last_cached_hour_utc": (rows[-1]["hour_utc"] if rows else None),
            "cache_chain_sha256": digest.hexdigest(),
        }
    total_required = len(hours) * len(symbols)
    safely_completed = len(safe_hours) * len(symbols)
    cached = sum(len(rows) for rows in references.values())
    public = {
        "schema_version": SCHEMA_VERSION,
        "eligible_date": day,
        "evaluated_at_utc": observed,
        "total_required_symbol_hours": total_required,
        "safely_completed_symbol_hours": safely_completed,
        "not_yet_safe_symbol_hours": pending_hours * len(symbols),
        "cached_symbol_hours": cached,
        "missing_safe_symbol_hours": len(missing),
        "completion_ratio": (cached / total_required if total_required else 0.0),
        "per_symbol": per_symbol,
        "historical_pnl_loaded": False,
        "oracle_or_outcome_loaded": False,
        "ownership_record_created": False,
        "signal_generated": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }
    return public, missing


def prewarm_status(
    eligible_date: Any,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns") if now_utc is None else _utc(now_utc)
    )
    result, _ = _inventory(eligible_date, output_root, observed)
    result["status"] = (
        "PREWARM_COMPLETE"
        if result["cached_symbol_hours"] == result["total_required_symbol_hours"]
        else (
            "PREWARM_COMPLETE_FOR_SAFELY_COMPLETED_HOURS"
            if result["missing_safe_symbol_hours"] == 0
            else "PREWARM_REQUIRED"
        )
    )
    return _serialize(result)


def _fetch_and_store(
    output_root: Path,
    symbol: str,
    hour: pd.Timestamp,
    *,
    fetcher: Callable[[str, pd.Timestamp], tuple[bytes, dict[str, Any]]],
    attempts: int,
    retry_delays: tuple[float, ...],
    minimum_lag_seconds: int,
) -> tuple[dict[str, Any], int]:
    last_error: Exception | None = None
    for used_attempts in range(1, attempts + 1):
        try:
            payload, metadata = fetcher(symbol, hour)
            if (
                str(metadata.get("symbol")) != symbol
                or _utc(metadata.get("hour_utc")) != hour
            ):
                raise RuntimeError("Prewarm fetch linkage drift")
            observed = _utc(metadata.get("observed_at_utc"))
            if observed < hour + pd.Timedelta(hours=1, seconds=minimum_lag_seconds):
                raise RuntimeError("Prewarm fetch predates safe H1 completion")
            ticks = decode_ticks(payload, symbol, hour)
            build_h1_bar(ticks, hour, observed)
            raw_hash = sha256_bytes(payload)
            name = f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
            raw_relative = Path("raw") / symbol / name
            metadata_relative = Path("metadata") / symbol / name
            metadata_payload = {
                "schema_version": ("eurusd_prospective_neutral_hour_v1"),
                **metadata,
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
            }
            write_immutable(
                output_root / metadata_relative,
                _json_bytes(metadata_payload),
            )
            write_immutable(output_root / raw_relative, payload)
            reference = _cache_reference(
                output_root,
                symbol,
                hour,
                deep_validate=True,
            )
            if reference is None:
                raise RuntimeError("Prewarmed hour was not cache-compatible")
            return reference, used_attempts
        except Exception as error:  # noqa: BLE001 - frozen retry boundary
            last_error = error
            if used_attempts < attempts:
                time.sleep(retry_delays[used_attempts - 1])
    assert last_error is not None
    raise last_error


def prewarm_capture(
    eligible_date: Any,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    now_utc: Any | None = None,
    max_new_requests: int | None = None,
    fetcher: Callable[[str, pd.Timestamp], tuple[bytes, dict[str, Any]]] = fetch_hour,
) -> dict[str, Any]:
    cfg, _ = _validate_contract()
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns") if now_utc is None else _utc(now_utc)
    )
    before, missing = _inventory(eligible_date, output_root, observed)
    configured_limit = int(cfg["transport"]["maximum_new_requests_per_run"])
    limit = configured_limit if max_new_requests is None else int(max_new_requests)
    if limit < 1 or limit > configured_limit:
        raise ValueError(f"max_new_requests must be from 1 through {configured_limit}")
    selected = missing[:limit]
    if not selected:
        return prewarm_status(eligible_date, output_root, now_utc=observed)
    attempts = int(cfg["transport"]["maximum_attempts_per_request"])
    retry_delays = tuple(
        float(value) for value in cfg["transport"]["retry_delays_seconds"]
    )
    if len(retry_delays) != attempts - 1:
        raise RuntimeError("Prewarm retry-delay contract is invalid")
    lag = int(cfg["completion_boundary"]["minimum_lag_after_hour_end_seconds"])
    workers = min(int(cfg["transport"]["maximum_workers"]), len(selected))
    references: list[dict[str, Any]] = []
    network_attempts = 0
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _fetch_and_store,
                output_root,
                symbol,
                hour,
                fetcher=fetcher,
                attempts=attempts,
                retry_delays=retry_delays,
                minimum_lag_seconds=lag,
            ): (hour, symbol)
            for hour, symbol in selected
        }
        for future in as_completed(futures):
            hour, symbol = futures[future]
            try:
                reference, used_attempts = future.result()
                references.append(reference)
                network_attempts += used_attempts
            except Exception as error:  # noqa: BLE001 - aggregate worker failures
                network_attempts += attempts
                errors.append(f"{symbol} {hour.isoformat()}: {error}")
    if errors:
        raise RuntimeError(
            "Ownership prewarm batch failed closed: " + " | ".join(errors)
        )
    after, _ = _inventory(eligible_date, output_root, observed)
    capture_observed = max(row["observed_at_utc"] for row in references)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "PREWARM_BATCH_CAPTURED",
        "eligible_date": _day(eligible_date),
        "batch_started_from_status": before,
        "batch_completed_status": after,
        "new_cached_symbol_hours": len(references),
        "network_request_attempts": network_attempts,
        "maximum_workers": workers,
        "capture_observed_at_utc": capture_observed,
        "compatibility": {
            "primary_ownership_cache_layout": True,
            "new_payloads_deep_validated": True,
            "ownership_record_created": False,
            "signal_generated": False,
        },
        "historical_pnl_loaded": False,
        "oracle_or_outcome_loaded": False,
        "broker_action_allowed": False,
    }
    inventory_hash = sha256_bytes(
        json.dumps(
            _serialize(after["per_symbol"]),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    manifest["cache_inventory_sha256"] = inventory_hash
    payload = _json_bytes(manifest)
    payload_hash = sha256_bytes(payload)
    relative = Path("prewarm_manifests") / (
        f"PREWARM_{_day(eligible_date):%Y-%m-%d}_"
        f"{capture_observed:%Y%m%dT%H%M%SZ}_"
        f"{payload_hash[:16]}.json"
    )
    write_immutable(output_root / relative, payload)
    result = {
        **after,
        "status": (
            "PREWARM_COMPLETE"
            if after["cached_symbol_hours"] == after["total_required_symbol_hours"]
            else (
                "PREWARM_COMPLETE_FOR_SAFELY_COMPLETED_HOURS"
                if after["missing_safe_symbol_hours"] == 0
                else "PREWARM_PARTIAL"
            )
        ),
        "new_cached_symbol_hours": len(references),
        "network_request_attempts": network_attempts,
        "manifest_relative_path": relative,
        "manifest_sha256": payload_hash,
        "network_request_made": True,
    }
    return _serialize(result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status", "capture"))
    parser.add_argument("--eligible-date")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--max-new-requests", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_lock()
    cfg = load_config()
    eligible = (
        cfg["target"]["first_eligible_date_utc"]
        if args.eligible_date is None
        else args.eligible_date
    )
    if args.command == "status":
        result = prewarm_status(eligible, args.output_root)
    else:
        result = prewarm_capture(
            eligible,
            args.output_root,
            max_new_requests=args.max_new_requests,
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
