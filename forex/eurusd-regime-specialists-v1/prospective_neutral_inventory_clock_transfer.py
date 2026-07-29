from __future__ import annotations

import argparse
import json
import math
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from datetime import time as datetime_time
from pathlib import Path
from typing import Any

import pandas as pd

from capture_prospective_neutral_inventory_unwind_0005 import (
    _canonical_hash,
    _entry_date,
    _json_bytes,
    _serialize,
    _timestamp,
    inventory_signal,
)
from capture_prospective_neutral_inventory_unwind_0005_path import (
    _evidence_chain,
    _existing_path,
    earliest_path_capture,
    execute_ticks,
    required_path_hours,
)
from capture_prospective_neutral_oracle_day import capture_oracle_date
from capture_prospective_neutral_ownership import (
    DEFAULT_OUTPUT_ROOT as DEFAULT_OWNERSHIP_ROOT,
)
from capture_prospective_neutral_ownership import (
    _validated_existing_ownership,
    capture_ownership,
    decode_ticks,
    fetch_hour,
    sha256_bytes,
    write_immutable,
)
from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    verify_neutral_ownership_record,
)
from eurusd_regime_specialists.prospective_neutral_validation_v1_1 import (
    temporal_oracle_metrics,
)
from eurusd_regime_specialists.research import PACKAGE_ROOT, sha256_file
from prewarm_prospective_neutral_ownership import (
    prewarm_capture as prewarm_ownership,
)
from validate_prospective_neutral_inventory_unwind_0005 import (
    _load_oracle,
    _monthly_metrics,
    trade_metrics,
)

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_inventory_clock_transfer_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT / "EURUSD_NEUTRAL_PROSPECTIVE_INVENTORY_CLOCK_TRANSFER_"
    "PREREG_2026_07_29.sha256.json"
)
DEFAULT_ROOT = Path(
    "D:/AlgoTradingData/prospective/eurusd-neutral-inventory-clock-transfer-v1"
)
DEFAULT_SOURCE_ROOT = DEFAULT_ROOT / "source"
DEFAULT_LEDGER_ROOT = DEFAULT_ROOT / "ledger"
DEFAULT_PATH_ROOT = DEFAULT_ROOT / "path"
DEFAULT_ORACLE_ROOT = DEFAULT_ROOT / "oracle"
FIRST_ENTRY_DATE = date(2026, 7, 30)
SLOTS = ("0605", "1205")


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_preregistration() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {
        "locked_before_prospective_evidence_start": True,
        "locked_with_zero_transfer_source_records": True,
        "locked_with_zero_transfer_decisions": True,
        "locked_with_zero_transfer_paths": True,
        "locked_with_zero_transfer_oracle_records": True,
        "historical_backtest_allowed": False,
        "historical_eurusd_pnl_allowed": False,
        "individual_clock_selection_allowed": False,
        "broker_action_allowed": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("Clock-transfer preregistration is incomplete")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"Clock-transfer implementation drift: {relative}")
    return lock


def _slot(value: str) -> str:
    slot = str(value)
    if slot not in SLOTS:
        raise ValueError(f"Unsupported frozen clock: {slot}")
    return slot


def _clock_hour(slot: str) -> int:
    return int(_slot(slot)[:2])


def entry_time(entry_date: Any, slot: str) -> pd.Timestamp:
    day = _entry_date(entry_date)
    return day + pd.Timedelta(
        hours=_clock_hour(slot),
        minutes=5,
    )


def decision_time(entry_date: Any, slot: str) -> pd.Timestamp:
    return entry_time(entry_date, slot) - pd.Timedelta(minutes=1)


def source_hours(entry_date: Any, slot: str) -> list[pd.Timestamp]:
    end = entry_time(entry_date, slot).floor("h")
    return list(
        pd.date_range(
            end - pd.Timedelta(hours=4),
            end - pd.Timedelta(hours=1),
            freq="h",
        )
    )


def _eligible_day(value: Any) -> pd.Timestamp:
    day = _entry_date(value)
    if day.date() < FIRST_ENTRY_DATE:
        raise ValueError("Entry date precedes the prospective campaign")
    if day.weekday() >= 5:
        raise ValueError("Clock-transfer entry date must be a UTC weekday")
    return day


def _record_key(day: pd.Timestamp, slot: str) -> str:
    return f"{day:%Y-%m-%d}_{_slot(slot)}"


def _existing_slot_record(
    root: Path,
    folder: str,
    day: pd.Timestamp,
    slot: str,
    *,
    prefix: str,
) -> dict[str, Any] | None:
    key = _record_key(day, slot)
    paths = sorted((root / folder).glob(f"{prefix}_{key}_*.json"))
    if not paths:
        return None
    if len(paths) != 1:
        raise RuntimeError(f"Multiple immutable {prefix} records exist")
    path = paths[0]
    payload = path.read_bytes()
    digest = sha256_bytes(payload)
    if path.name != f"{prefix}_{key}_{digest[:16]}.json":
        raise RuntimeError(f"{prefix} filename/hash drift")
    record = json.loads(payload)
    hash_field = "source_record_sha256" if prefix == "SOURCE" else "decision_sha256"
    core = {key_: value for key_, value in record.items() if key_ != hash_field}
    if record.get(hash_field) != _canonical_hash(core):
        raise RuntimeError(f"{prefix} canonical hash drift")
    return {
        **record,
        "relative_path": path.relative_to(root).as_posix(),
        "file_sha256": digest,
    }


def _source_cache_paths(
    source_root: Path,
    hour: pd.Timestamp,
    raw_hash: str,
) -> tuple[Path, Path]:
    name = f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
    return (
        source_root / "raw" / "EURUSD" / name,
        source_root / "metadata" / "EURUSD" / name,
    )


def _cached_source_hour(
    source_root: Path,
    hour_utc: Any,
) -> tuple[bytes, dict[str, Any]] | None:
    hour = _timestamp(hour_utc).floor("h")
    paths = sorted(
        (source_root / "raw" / "EURUSD").glob(f"{hour:%Y%m%dT%H0000Z}_*.json")
    )
    if not paths:
        return None
    if len(paths) != 1:
        raise RuntimeError("Multiple clock-transfer source snapshots exist")
    raw_path = paths[0]
    metadata_path = source_root / "metadata" / "EURUSD" / raw_path.name
    if not metadata_path.is_file():
        raise RuntimeError("Clock-transfer source metadata is missing")
    payload = raw_path.read_bytes()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if (
        sha256_bytes(payload) != str(metadata["raw_sha256"])
        or sha256_file(raw_path) != str(metadata["raw_sha256"])
        or _timestamp(metadata["hour_utc"]) != hour
        or str(metadata["symbol"]) != "EURUSD"
    ):
        raise RuntimeError("Clock-transfer source cache drift")
    return payload, metadata


def prewarm_source_hour(
    entry_date: Any,
    slot: str,
    hour_utc: Any,
    *,
    source_root: Path = DEFAULT_SOURCE_ROOT,
    now_utc: Any | None = None,
    fetcher: Callable[[str, pd.Timestamp], tuple[bytes, dict[str, Any]]] = fetch_hour,
) -> dict[str, Any]:
    cfg = load_config()
    day = _eligible_day(entry_date)
    frozen_slot = _slot(slot)
    hour = _timestamp(hour_utc).floor("h")
    if hour not in source_hours(day, frozen_slot):
        raise ValueError("Prewarm hour is outside the frozen source window")
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _timestamp(now_utc)
    )
    earliest = (
        hour
        + pd.Timedelta(hours=1)
        + pd.Timedelta(
            seconds=int(cfg["inventory_source"]["completed_hour_prewarm_lag_seconds"])
        )
    )
    deadline = decision_time(day, frozen_slot)
    if observed < earliest:
        return {
            "status": "WAITING_FOR_COMPLETED_SOURCE_HOUR",
            "hour_utc": hour,
            "earliest_capture_utc": earliest,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    existing = _cached_source_hour(source_root, hour)
    if existing is not None:
        _, metadata = existing
        return {
            "status": "SOURCE_HOUR_ALREADY_IMMUTABLE",
            "entry_date_utc": day,
            "clock": frozen_slot,
            "hour_utc": hour,
            "observed_at_utc": metadata["observed_at_utc"],
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    if observed > deadline:
        return {
            "status": "MISSED_SOURCE_HOUR_PREWARM_NO_BACKFILL",
            "entry_date_utc": day,
            "clock": frozen_slot,
            "hour_utc": hour,
            "deadline_utc": deadline,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    payload, metadata = fetcher("EURUSD", hour)
    if (
        str(metadata.get("symbol")) != "EURUSD"
        or _timestamp(metadata.get("hour_utc")) != hour
    ):
        raise RuntimeError("Clock-transfer source fetch linkage drift")
    market_observed = _timestamp(metadata.get("observed_at_utc"))
    if market_observed < earliest:
        raise RuntimeError("Source hour evidence predates publication boundary")
    raw_hash = sha256_bytes(payload)
    raw_path, metadata_path = _source_cache_paths(
        source_root,
        hour,
        raw_hash,
    )
    write_immutable(raw_path, payload)
    metadata_payload = {
        "schema_version": ("eurusd_neutral_prospective_inventory_clock_source_hour_v1"),
        "campaign_id": cfg["campaign_id"],
        "entry_date_utc": day.strftime("%Y-%m-%d"),
        "clock": frozen_slot,
        **metadata,
        "raw_relative_path": raw_path.relative_to(source_root),
        "raw_sha256": raw_hash,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "broker_action_allowed": False,
    }
    write_immutable(metadata_path, _json_bytes(metadata_payload))
    return {
        "status": "SOURCE_HOUR_PREWARMED",
        "entry_date_utc": day,
        "clock": frozen_slot,
        "hour_utc": hour,
        "raw_relative_path": raw_path.relative_to(source_root),
        "raw_sha256": raw_hash,
        "metadata_relative_path": metadata_path.relative_to(source_root),
        "metadata_sha256": sha256_file(metadata_path),
        "network_request_made": True,
        "broker_action_allowed": False,
    }


def capture_source(
    entry_date: Any,
    slot: str,
    *,
    source_root: Path = DEFAULT_SOURCE_ROOT,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    cfg = load_config()
    day = _eligible_day(entry_date)
    frozen_slot = _slot(slot)
    existing = _existing_slot_record(
        source_root,
        "records",
        day,
        frozen_slot,
        prefix="SOURCE",
    )
    if existing is not None:
        return existing
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _timestamp(now_utc)
    )
    entry = entry_time(day, frozen_slot)
    earliest = entry - pd.Timedelta(minutes=2)
    deadline = decision_time(day, frozen_slot)
    if observed < earliest:
        return {
            "status": "WAITING_FOR_SOURCE_CAPTURE_CLOCK",
            "entry_date_utc": day,
            "clock": frozen_slot,
            "earliest_capture_utc": earliest,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    if observed > deadline:
        return {
            "status": "MISSED_SOURCE_DEADLINE_NO_BACKFILL",
            "entry_date_utc": day,
            "clock": frozen_slot,
            "source_deadline_utc": deadline,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    frames: list[pd.DataFrame] = []
    raw_links: list[dict[str, Any]] = []
    for hour in source_hours(day, frozen_slot):
        cached = _cached_source_hour(source_root, hour)
        if cached is None:
            return {
                "status": "WAITING_FOR_PREWARMED_SOURCE_HOUR",
                "entry_date_utc": day,
                "clock": frozen_slot,
                "missing_hour_utc": hour,
                "network_request_made": False,
                "broker_action_allowed": False,
            }
        payload, metadata = cached
        market_observed = _timestamp(metadata["observed_at_utc"])
        if market_observed > deadline:
            return {
                "status": "CASH_LATE_SOURCE_EVIDENCE",
                "entry_date_utc": day,
                "clock": frozen_slot,
                "late_hour_utc": hour,
                "source_observed_at_utc": market_observed,
                "source_deadline_utc": deadline,
                "network_request_made": False,
                "broker_action_allowed": False,
            }
        raw_relative = Path(str(metadata["raw_relative_path"]))
        metadata_relative = Path("metadata") / "EURUSD" / raw_relative.name
        frames.append(decode_ticks(payload, "EURUSD", hour))
        raw_links.append(
            {
                "hour_utc": hour,
                "observed_at_utc": market_observed,
                "raw_relative_path": raw_relative,
                "raw_sha256": str(metadata["raw_sha256"]),
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": sha256_file(source_root / metadata_relative),
            }
        )
    signal = inventory_signal(
        pd.concat(frames, ignore_index=True),
        threshold_pips=float(
            cfg["inventory_source"]["minimum_absolute_displacement_pips"]
        ),
    )
    window_end = entry.floor("h")
    core = {
        "schema_version": ("eurusd_neutral_prospective_inventory_clock_source_v1"),
        "campaign_id": cfg["campaign_id"],
        "status": (
            "SOURCE_SIGNAL" if signal["signal_eligible"] else "SOURCE_CASH_SUBTHRESHOLD"
        ),
        "entry_date_utc": day.strftime("%Y-%m-%d"),
        "clock": frozen_slot,
        "source_window_start_utc": window_end - pd.Timedelta(hours=4),
        "source_window_end_utc": window_end,
        "source_captured_at_utc": observed,
        "source_observed_at_utc": max(row["observed_at_utc"] for row in raw_links),
        "raw_links": raw_links,
        "signal": signal,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }
    record = {**core, "source_record_sha256": _canonical_hash(core)}
    payload = _json_bytes(record)
    digest = sha256_bytes(payload)
    key = _record_key(day, frozen_slot)
    relative = Path("records") / f"SOURCE_{key}_{digest[:16]}.json"
    write_immutable(source_root / relative, payload)
    return {
        **_serialize(record),
        "relative_path": relative.as_posix(),
        "file_sha256": digest,
    }


def build_decision(
    source: Mapping[str, Any],
    ownership: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    created_at_utc: Any,
) -> dict[str, Any]:
    day = _entry_date(f"{source['entry_date_utc']}T00:00:00Z")
    frozen_slot = _slot(str(source["clock"]))
    created = _timestamp(created_at_utc)
    decision = decision_time(day, frozen_slot)
    entry = entry_time(day, frozen_slot)
    latest_creation = entry - pd.Timedelta(nanoseconds=1)
    if created < decision:
        raise ValueError("Decision cannot be created before its frozen clock")
    source_observed = _timestamp(source["source_observed_at_utc"])
    ownership_observed = _timestamp(ownership["ownership_observed_at_utc"])
    reasons: list[str] = []
    if day.weekday() >= 5:
        reasons.append("WEEKEND")
    if source_observed > decision:
        reasons.append("LATE_SOURCE")
    if ownership_observed > day + pd.Timedelta(minutes=4):
        reasons.append("LATE_DAILY_OWNERSHIP")
    if not bool(ownership["is_neutral"]):
        reasons.append("NOT_NEUTRAL")
    if float(ownership["state_staleness_hours"]) > float(
        config["neutral_ownership"]["maximum_state_staleness_hours_at_daily_cutoff"]
    ):
        reasons.append("STALE_OWNERSHIP_AT_DAILY_CUTOFF")
    source_side = str(source["signal"]["side"])
    if source_side not in ("LONG", "SHORT"):
        reasons.append("SUBTHRESHOLD")
    if created > latest_creation:
        reasons.append("MISSED_DECISION_CREATION_DEADLINE")
    status = "SIGNAL" if not reasons else "CASH"
    core = {
        "schema_version": ("eurusd_neutral_prospective_inventory_clock_decision_v1"),
        "campaign_id": config["campaign_id"],
        "entry_date_utc": day.strftime("%Y-%m-%d"),
        "clock": frozen_slot,
        "decision_time_utc": decision,
        "decision_created_at_utc": created,
        "entry_time_utc": entry,
        "status": status,
        "reasons": reasons,
        "side": source_side if status == "SIGNAL" else "CASH",
        "source_record_sha256": source["source_record_sha256"],
        "source_file_sha256": source["file_sha256"],
        "ownership_evidence_sha256": ownership["ownership_evidence_sha256"],
        "inventory_displacement_pips": float(source["signal"]["displacement_pips"]),
        "fixed_stop_pips": float(config["risk"]["fixed_stop_pips"]),
        "fixed_target_pips": float(config["risk"]["fixed_target_pips"]),
        "maximum_hold_hours": int(config["risk"]["maximum_hold_hours"]),
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "broker_action_allowed": False,
    }
    return {**core, "decision_sha256": _canonical_hash(core)}


def evaluate(
    entry_date: Any,
    slot: str,
    *,
    source_root: Path = DEFAULT_SOURCE_ROOT,
    ownership_root: Path = DEFAULT_OWNERSHIP_ROOT,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    cfg = load_config()
    day = _eligible_day(entry_date)
    frozen_slot = _slot(slot)
    existing = _existing_slot_record(
        ledger_root,
        "decisions",
        day,
        frozen_slot,
        prefix="DECISION",
    )
    if existing is not None:
        return existing
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _timestamp(now_utc)
    )
    decision = decision_time(day, frozen_slot)
    if observed < decision:
        return {
            "status": "WAITING_FOR_DECISION_CLOCK",
            "entry_date_utc": day,
            "clock": frozen_slot,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    source = _existing_slot_record(
        source_root,
        "records",
        day,
        frozen_slot,
        prefix="SOURCE",
    )
    ownership_link = _validated_existing_ownership(ownership_root, day)
    if source is None or ownership_link is None:
        placeholder_source = source or {
            "entry_date_utc": day.strftime("%Y-%m-%d"),
            "clock": frozen_slot,
            "source_observed_at_utc": observed,
            "source_record_sha256": "0" * 64,
            "file_sha256": "0" * 64,
            "signal": {"side": "CASH", "displacement_pips": 0.0},
        }
        placeholder_ownership = {
            "ownership_observed_at_utc": observed,
            "is_neutral": False,
            "state_staleness_hours": float("inf"),
            "ownership_evidence_sha256": "0" * 64,
        }
        record = build_decision(
            placeholder_source,
            placeholder_ownership,
            config=cfg,
            created_at_utc=observed,
        )
        missing: list[str] = []
        if source is None:
            missing.append("MISSING_ON_TIME_SOURCE_RECORD")
        if ownership_link is None:
            missing.append("MISSING_ON_TIME_OWNERSHIP_RECORD")
        record["reasons"] = sorted({*record["reasons"], *missing})
        record["decision_sha256"] = _canonical_hash(
            {key: value for key, value in record.items() if key != "decision_sha256"}
        )
    else:
        ownership_path = (
            ownership_root / ownership_link["ownership_record_relative_path"]
        )
        ownership = json.loads(ownership_path.read_text(encoding="utf-8"))
        verify_neutral_ownership_record(ownership)
        ownership["file_sha256"] = sha256_file(ownership_path)
        record = build_decision(
            source,
            ownership,
            config=cfg,
            created_at_utc=observed,
        )
    payload = _json_bytes(record)
    digest = sha256_bytes(payload)
    key = _record_key(day, frozen_slot)
    relative = Path("decisions") / f"DECISION_{key}_{digest[:16]}.json"
    write_immutable(ledger_root / relative, payload)
    return {
        **_serialize(record),
        "relative_path": relative.as_posix(),
        "file_sha256": digest,
        "network_request_made": False,
    }


def capture_trade_path(
    entry_date: Any,
    slot: str,
    *,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    output_root: Path = DEFAULT_PATH_ROOT,
    now_utc: Any | None = None,
    fetcher: Callable[[str, pd.Timestamp], tuple[bytes, dict[str, Any]]] = fetch_hour,
) -> dict[str, Any]:
    cfg = load_config()
    day = _eligible_day(entry_date)
    frozen_slot = _slot(slot)
    decision = _existing_slot_record(
        ledger_root,
        "decisions",
        day,
        frozen_slot,
        prefix="DECISION",
    )
    if decision is None:
        return {
            "status": "WAITING_FOR_IMMUTABLE_DECISION",
            "entry_date_utc": day,
            "clock": frozen_slot,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    decision_id = str(decision["decision_sha256"])
    existing = _existing_path(output_root, decision_id)
    if existing is not None:
        return existing
    if decision["status"] != "SIGNAL":
        return {
            "status": "CASH_DECISION_NO_TRADE",
            "entry_date_utc": day,
            "clock": frozen_slot,
            "decision_id": decision_id,
            "decision_status": decision["status"],
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    entry = _timestamp(decision["entry_time_utc"])
    maximum_hold = int(cfg["risk"]["maximum_hold_hours"])
    deadline = entry + pd.Timedelta(hours=maximum_hold)
    earliest = earliest_path_capture(
        entry,
        maximum_hold_hours=maximum_hold,
    )
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _timestamp(now_utc)
    )
    if observed < earliest:
        return {
            "status": "WAITING_FOR_6H_PATH_PUBLICATION",
            "entry_date_utc": day,
            "clock": frozen_slot,
            "decision_id": decision_id,
            "entry_time_utc": entry,
            "deadline_utc": deadline,
            "earliest_capture_utc": earliest,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    raw_records: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []
    for hour in required_path_hours(
        entry,
        maximum_hold_hours=maximum_hold,
    ):
        payload, metadata = fetcher("EURUSD", hour)
        if (
            str(metadata.get("symbol")) != "EURUSD"
            or _timestamp(metadata.get("hour_utc")) != hour
        ):
            raise RuntimeError("Clock-transfer path fetch linkage drift")
        raw_hash = sha256_bytes(payload)
        name = f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
        raw_relative = Path("raw") / decision_id / name
        metadata_relative = Path("metadata") / decision_id / name
        write_immutable(output_root / raw_relative, payload)
        metadata_payload = {
            "schema_version": ("eurusd_neutral_prospective_inventory_clock_path_v1"),
            "campaign_id": cfg["campaign_id"],
            "decision_id": decision_id,
            "clock": frozen_slot,
            **metadata,
            "raw_relative_path": raw_relative,
            "raw_sha256": raw_hash,
            "historical_eurusd_pnl_loaded": False,
            "oracle_rows_loaded": False,
            "broker_action_allowed": False,
        }
        metadata_bytes = _json_bytes(metadata_payload)
        write_immutable(output_root / metadata_relative, metadata_bytes)
        raw_records.append(
            {
                "hour_utc": hour,
                "observed_at_utc": _timestamp(metadata["observed_at_utc"]),
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": sha256_bytes(metadata_bytes),
            }
        )
        frames.append(decode_ticks(payload, "EURUSD", hour))
    market_observed = max(row["observed_at_utc"] for row in raw_records)
    if market_observed < earliest:
        raise RuntimeError("Path evidence predates publication boundary")
    final_hour = max(required_path_hours(entry, maximum_hold_hours=maximum_hold))
    final_hour_observed = next(
        row["observed_at_utc"] for row in raw_records if row["hour_utc"] == final_hour
    )
    if final_hour_observed < earliest:
        raise RuntimeError("Final path hour evidence predates publication boundary")
    execution = execute_ticks(
        decision,
        pd.concat(frames, ignore_index=True),
        cfg,
    )
    manifest = {
        "schema_version": ("eurusd_neutral_prospective_inventory_clock_path_v1"),
        "campaign_id": cfg["campaign_id"],
        "entry_date_utc": day.strftime("%Y-%m-%d"),
        "clock": frozen_slot,
        "decision_id": decision_id,
        "decision_file_sha256": decision["file_sha256"],
        "entry_time_utc": entry,
        "deadline_utc": deadline,
        "path_captured_at_utc": observed,
        "market_observed_at_utc": market_observed,
        "raw_snapshots": raw_records,
        "path_evidence_chain_sha256": _evidence_chain(output_root),
        "execution": execution,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "broker_action_allowed": False,
    }
    payload = _json_bytes(manifest)
    digest = sha256_bytes(payload)
    relative = Path("manifests") / f"PATH_{decision_id}_{digest[:16]}.json"
    write_immutable(output_root / relative, payload)
    return {
        **_serialize(manifest),
        "manifest_relative_path": relative.as_posix(),
        "manifest_sha256": digest,
        "network_request_made": True,
    }


def _load_decisions(
    ledger_root: Path,
    as_of: pd.Timestamp,
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    keys: set[tuple[str, str]] = set()
    for path in sorted((ledger_root / "decisions").glob("DECISION_*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if _timestamp(raw["decision_created_at_utc"]) > as_of:
            continue
        key = (str(raw["entry_date_utc"]), _slot(str(raw["clock"])))
        _eligible_day(f"{key[0]}T00:00:00Z")
        if key in keys:
            raise RuntimeError("Duplicate prospective date/clock decision")
        verified = _existing_slot_record(
            ledger_root,
            "decisions",
            _entry_date(f"{key[0]}T00:00:00Z"),
            key[1],
            prefix="DECISION",
        )
        if verified is None:
            raise RuntimeError("Decision disappeared during validation")
        decisions.append(verified)
        keys.add(key)
    return decisions


def _top_winners_removed(closed: pd.DataFrame) -> dict[str, Any]:
    if closed.empty:
        result = trade_metrics([])
        result["removed_winners"] = 0
        return result
    winner_count = int(closed["r"].gt(0.0).sum())
    removed = max(1, math.ceil(winner_count * 0.05)) if winner_count else 0
    drop_index = closed.nlargest(removed, "r").index if removed else pd.Index([])
    result = trade_metrics(closed.drop(index=drop_index)["r"])
    result["removed_winners"] = removed
    return result


def build_validation_status(
    *,
    evaluated_at_utc: Any | None = None,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    path_root: Path = DEFAULT_PATH_ROOT,
    oracle_root: Path = DEFAULT_ORACLE_ROOT,
) -> dict[str, Any]:
    verify_preregistration()
    cfg = load_config()
    evaluated = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if evaluated_at_utc is None
        else _timestamp(evaluated_at_utc)
    )
    start = _timestamp(cfg["prospective_evidence_start_utc"])
    decisions = _load_decisions(ledger_root, evaluated)
    routed_rows: list[dict[str, Any]] = []
    for decision in decisions:
        row = {
            "signal_id": decision["decision_sha256"],
            "entry_date_utc": decision["entry_date_utc"],
            "entry_time_utc": decision["entry_time_utc"],
            "clock": decision["clock"],
            "side": decision["side"],
            "decision_status": decision["status"],
            "status": "CASH",
        }
        if decision["status"] == "SIGNAL":
            path = _existing_path(
                path_root,
                str(decision["decision_sha256"]),
            )
            if path is None or _timestamp(path["path_captured_at_utc"]) > evaluated:
                row["status"] = "PENDING_PATH"
            else:
                row.update(path["execution"])
                row["signal_id"] = decision["decision_sha256"]
                row["clock"] = decision["clock"]
                row["decision_status"] = decision["status"]
        routed_rows.append(row)
    routed = pd.DataFrame(routed_rows)
    if routed.empty:
        routed = pd.DataFrame(
            columns=[
                "signal_id",
                "entry_date_utc",
                "entry_time_utc",
                "clock",
                "side",
                "decision_status",
                "status",
                "r",
                "extra_half_pip_stress_r",
            ]
        )
    closed = routed[routed["status"].eq("CLOSED")].copy()
    overall = trade_metrics(closed.get("r", pd.Series(dtype=float)))
    stress = trade_metrics(
        closed.get(
            "extra_half_pip_stress_r",
            pd.Series(dtype=float),
        )
    )
    by_side = {
        side: trade_metrics(closed.loc[closed["side"].eq(side), "r"])
        for side in ("LONG", "SHORT")
    }
    by_clock = {
        slot: trade_metrics(closed.loc[closed["clock"].eq(slot), "r"]) for slot in SLOTS
    }
    top_removed = _top_winners_removed(closed)
    monthly = _monthly_metrics(closed)
    oracle, completed_dates = _load_oracle(oracle_root, evaluated)
    temporal_by_clock = {
        slot: temporal_oracle_metrics(
            routed[routed["clock"].eq(slot)],
            oracle,
            completed_dates,
            windows_minutes=[15],
            grid_minutes=int(
                cfg["prospective_admission"]["uniform_entry_grid_minutes"]
            ),
        )
        for slot in SLOTS
    }
    all_oracle_dates = bool(
        len(closed)
        and all(
            temporal_by_clock[slot]["all_closed_trade_oracle_dates_available"]
            for slot in SLOTS
            if by_clock[slot]["trades"] > 0
        )
    )
    same_day_matches = 0
    if all_oracle_dates:
        neutral = oracle[oracle["regime"].eq("NEUTRAL")].copy()
        neutral["oracle_date"] = neutral["oracle_date"].astype(str)
        for _, trade in closed.iterrows():
            day = pd.Timestamp(trade["entry_time_utc"]).strftime("%Y-%m-%d")
            same_day_matches += int(
                (
                    neutral["oracle_date"].eq(day) & neutral["side"].eq(trade["side"])
                ).any()
            )
    same_day_precision = (
        same_day_matches / len(closed) if len(closed) and all_oracle_dates else None
    )
    elapsed_months = max(
        0,
        (evaluated.year - start.year) * 12 + evaluated.month - start.month,
    )
    gates = cfg["prospective_admission"]
    sample_checks = {
        "minimum_calendar_months": elapsed_months
        >= int(gates["minimum_calendar_months"]),
        "minimum_executed_trades": len(closed) >= int(gates["minimum_executed_trades"]),
        "minimum_trades_per_clock": all(
            by_clock[slot]["trades"] >= int(gates["minimum_trades_per_clock"])
            for slot in SLOTS
        ),
        "minimum_each_side_trades": all(
            by_side[side]["trades"] >= int(gates["minimum_each_side_trades"])
            for side in ("LONG", "SHORT")
        ),
        "all_signal_paths_closed": not routed["status"].eq("PENDING_PATH").any(),
    }
    economic_checks = {
        "overall_win_rate": float(gates["minimum_overall_win_rate"])
        <= overall["win_rate"]
        <= float(gates["maximum_overall_win_rate"]),
        "overall_payoff": float(gates["minimum_overall_realized_payoff_ratio"])
        <= overall["realized_payoff_ratio"]
        <= float(gates["maximum_overall_realized_payoff_ratio"]),
        "overall_profit_factor": overall["profit_factor"]
        >= float(gates["minimum_overall_profit_factor"]),
        "extra_half_pip_profit_factor": stress["profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_clock_positive": all(
            by_clock[slot]["profit_factor"]
            >= float(gates["minimum_each_clock_profit_factor"])
            and by_clock[slot]["net_r"] > float(gates["minimum_each_clock_net_r"])
            for slot in SLOTS
        ),
        "both_side_profit_factors": all(
            by_side[side]["profit_factor"]
            >= float(gates["minimum_each_side_profit_factor"])
            for side in ("LONG", "SHORT")
        ),
        "maximum_drawdown": overall["max_drawdown_r"]
        <= float(gates["maximum_drawdown_r"]),
        "top_5pct_removed_profit_factor": top_removed["profit_factor"]
        >= float(gates["minimum_top_5pct_removed_profit_factor"]),
        "positive_active_month_rate": monthly["positive_active_month_rate"]
        >= float(gates["minimum_positive_active_month_rate"]),
        "monthly_profit_concentration": monthly[
            "largest_month_share_of_positive_profit"
        ]
        <= float(gates["maximum_largest_month_share_of_positive_profit"]),
    }
    clock_oracle_checks: dict[str, dict[str, bool]] = {}
    for slot in SLOTS:
        temporal = temporal_by_clock[slot]
        primary = temporal["windows"]["within_15_minutes"]
        clock_oracle_checks[slot] = {
            "all_closed_trade_oracle_dates": bool(
                temporal["all_closed_trade_oracle_dates_available"]
            ),
            "one_prediction_per_date": bool(
                temporal["one_strategy_trade_per_utc_date"]
            ),
            "exact_uniform_null_valid": bool(primary["exact_null_valid"]),
            "temporal_precision": bool(
                primary["precision"] is not None
                and primary["precision"]
                >= float(gates["minimum_each_clock_temporal_oracle_precision"])
            ),
            "temporal_lift": bool(
                primary["precision_lift_over_uniform_time_and_side"] is not None
                and primary["precision_lift_over_uniform_time_and_side"]
                > float(
                    gates[
                        "minimum_each_clock_temporal_lift_over_exact_"
                        "uniform_time_and_side_null"
                    ]
                )
            ),
            "bonferroni_uniform_null_test": bool(
                primary["uniform_time_and_side_poisson_binomial_tail_p_value"]
                is not None
                and primary["uniform_time_and_side_poisson_binomial_tail_p_value"]
                <= float(gates["maximum_each_clock_temporal_uniform_null_p_value"])
            ),
        }
    oracle_checks = {
        "all_closed_trade_oracle_dates": all_oracle_dates,
        "same_day_same_side_precision": bool(
            same_day_precision is not None
            and same_day_precision
            >= float(gates["minimum_same_day_same_side_oracle_precision"])
        ),
        "both_clock_temporal_gates": all(
            all(checks.values()) for checks in clock_oracle_checks.values()
        ),
    }
    sample_passed = bool(all(sample_checks.values()))
    evaluation_ready = bool(sample_passed and all_oracle_dates)
    all_passed = bool(
        sample_passed and all(economic_checks.values()) and all(oracle_checks.values())
    )
    if evaluated < start:
        status = "WAITING_FOR_PROSPECTIVE_START"
    elif not evaluation_ready:
        status = "ACCUMULATING_PROSPECTIVE_EVIDENCE"
    elif all_passed:
        status = "INDEPENDENT_RESEARCH_REVIEW_REQUIRED"
    else:
        status = "REJECTED_WITHOUT_RETUNING"
    return _serialize(
        {
            "schema_version": (
                "eurusd_neutral_prospective_inventory_clock_validation_v1"
            ),
            "status": status,
            "prospective_evidence_start_utc": start,
            "evaluated_at_utc": evaluated,
            "promotion_unit": "POOLED_0605_AND_1205_CLOCK_SPECIALIST",
            "individual_clock_selection_allowed": False,
            "frequency": {
                "eligible_decisions_recorded": len(decisions),
                "signals": int(sum(row["status"] == "SIGNAL" for row in decisions)),
                "cash_decisions": int(
                    sum(row["status"] == "CASH" for row in decisions)
                ),
                "closed_trades": len(closed),
                "elapsed_calendar_months": elapsed_months,
            },
            "overall": overall,
            "by_clock": by_clock,
            "by_side": by_side,
            "extra_half_pip_round_trip": stress,
            "top_5pct_winners_removed": top_removed,
            "monthly": monthly,
            "same_day_oracle_resemblance": {
                "matches": same_day_matches,
                "precision": same_day_precision,
            },
            "temporal_oracle_resemblance_by_clock": temporal_by_clock,
            "clock_oracle_gate_results": clock_oracle_checks,
            "sample_gate_results": sample_checks,
            "economic_and_robustness_gate_results": economic_checks,
            "oracle_gate_results": oracle_checks,
            "all_gates_passed": all_passed,
            "research_review_allowed": all_passed,
            "controlled_demo_ready": False,
            "historical_eurusd_pnl_loaded": False,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    )


@dataclass(frozen=True)
class ScheduledOperation:
    due_at_utc: datetime
    name: str
    entry_date_utc: date
    slot: str | None = None
    source_hour_utc: datetime | None = None


def _at(
    day: date,
    hour: int,
    minute: int,
    second: int = 0,
) -> datetime:
    return datetime.combine(
        day,
        datetime_time(hour, minute, second),
        tzinfo=timezone.utc,
    )


def operations_for_entry_date(
    entry_date_utc: date,
) -> list[ScheduledOperation]:
    if entry_date_utc.weekday() >= 5 or entry_date_utc < FIRST_ENTRY_DATE:
        return []
    prior = entry_date_utc - timedelta(days=1)
    context = entry_date_utc + timedelta(days=1)
    operations: list[ScheduledOperation] = [
        *[
            ScheduledOperation(
                _at(prior, hour, 2),
                "PREWARM_ENTRY_OWNERSHIP",
                entry_date_utc,
            )
            for hour in (21, 22, 23)
        ],
        ScheduledOperation(
            _at(entry_date_utc, 0, 2, 15),
            "CAPTURE_ENTRY_OWNERSHIP",
            entry_date_utc,
        ),
    ]
    for slot in SLOTS:
        hour = _clock_hour(slot)
        for source_hour in range(hour - 4, hour):
            source_dt = _at(entry_date_utc, source_hour, 0)
            operations.append(
                ScheduledOperation(
                    source_dt + timedelta(hours=1, minutes=2),
                    "PREWARM_SOURCE_HOUR",
                    entry_date_utc,
                    slot=slot,
                    source_hour_utc=source_dt,
                )
            )
        operations.extend(
            [
                ScheduledOperation(
                    _at(entry_date_utc, hour, 3),
                    "CAPTURE_SOURCE",
                    entry_date_utc,
                    slot=slot,
                ),
                ScheduledOperation(
                    _at(entry_date_utc, hour, 4),
                    "EVALUATE_DECISION",
                    entry_date_utc,
                    slot=slot,
                ),
                ScheduledOperation(
                    _at(entry_date_utc, hour + 7, 16),
                    "CAPTURE_CLOSED_TRADE_PATH",
                    entry_date_utc,
                    slot=slot,
                ),
                ScheduledOperation(
                    _at(entry_date_utc, hour + 7, 17),
                    "VALIDATE_PROSPECTIVE_LEDGER",
                    entry_date_utc,
                    slot=slot,
                ),
            ]
        )
    operations.extend(
        [
            *[
                ScheduledOperation(
                    _at(entry_date_utc, hour, 2),
                    "PREWARM_ORACLE_CONTEXT",
                    entry_date_utc,
                )
                for hour in (21, 22, 23)
            ],
            ScheduledOperation(
                _at(context, 0, 2, 15),
                "CAPTURE_ORACLE_CONTEXT",
                entry_date_utc,
            ),
            ScheduledOperation(
                _at(context, 12, 2),
                "CAPTURE_COMPLETED_ORACLE_DATE",
                entry_date_utc,
            ),
            ScheduledOperation(
                _at(context, 12, 3),
                "VALIDATE_WITH_ORACLE",
                entry_date_utc,
            ),
        ]
    )
    return sorted(
        operations,
        key=lambda row: (
            row.due_at_utc,
            row.name,
            row.slot or "",
        ),
    )


def next_operation(after_utc: datetime) -> ScheduledOperation:
    if after_utc.tzinfo is None:
        raise ValueError("Scheduler requires a timezone-aware timestamp")
    after = after_utc.astimezone(timezone.utc)
    candidates: list[ScheduledOperation] = []
    for offset in range(-2, 12):
        candidates.extend(
            operations_for_entry_date(after.date() + timedelta(days=offset))
        )
    future = [row for row in candidates if row.due_at_utc > after]
    if not future:
        raise RuntimeError("No future clock-transfer operation found")
    return min(
        future,
        key=lambda row: (
            row.due_at_utc,
            row.entry_date_utc,
            row.name,
            row.slot or "",
        ),
    )


def execute_operation(
    operation: ScheduledOperation,
    *,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    verify_preregistration()
    observed = (
        datetime.now(timezone.utc)
        if now_utc is None
        else now_utc.astimezone(timezone.utc)
    )
    day_text = operation.entry_date_utc.isoformat()
    context_text = (operation.entry_date_utc + timedelta(days=1)).isoformat()
    if operation.name == "PREWARM_ENTRY_OWNERSHIP":
        result = prewarm_ownership(day_text)
    elif operation.name == "CAPTURE_ENTRY_OWNERSHIP":
        deadline = _at(operation.entry_date_utc, 0, 4)
        result = (
            capture_ownership(day_text)
            if observed <= deadline
            else {
                "status": "SKIPPED_LATE_OWNERSHIP_NO_BACKFILL",
                "network_request_made": False,
                "broker_action_allowed": False,
            }
        )
    elif operation.name == "PREWARM_SOURCE_HOUR":
        if operation.slot is None or operation.source_hour_utc is None:
            raise RuntimeError("Source prewarm operation is incomplete")
        result = prewarm_source_hour(
            day_text,
            operation.slot,
            operation.source_hour_utc,
        )
    elif operation.name == "CAPTURE_SOURCE":
        if operation.slot is None:
            raise RuntimeError("Source operation has no frozen clock")
        result = capture_source(day_text, operation.slot)
    elif operation.name == "EVALUATE_DECISION":
        if operation.slot is None:
            raise RuntimeError("Decision operation has no frozen clock")
        result = evaluate(day_text, operation.slot)
    elif operation.name == "CAPTURE_CLOSED_TRADE_PATH":
        if operation.slot is None:
            raise RuntimeError("Path operation has no frozen clock")
        result = capture_trade_path(day_text, operation.slot)
    elif operation.name in (
        "VALIDATE_PROSPECTIVE_LEDGER",
        "VALIDATE_WITH_ORACLE",
    ):
        result = build_validation_status(evaluated_at_utc=observed)
    elif operation.name == "PREWARM_ORACLE_CONTEXT":
        result = prewarm_ownership(context_text)
    elif operation.name == "CAPTURE_ORACLE_CONTEXT":
        result = capture_ownership(context_text)
    elif operation.name == "CAPTURE_COMPLETED_ORACLE_DATE":
        result = capture_oracle_date(
            day_text,
            oracle_root=DEFAULT_ORACLE_ROOT,
            ownership_root=DEFAULT_OWNERSHIP_ROOT,
        )
    else:
        raise ValueError(f"Unknown clock-transfer operation: {operation.name}")
    return _serialize(
        {
            "schema_version": (
                "eurusd_neutral_prospective_inventory_clock_operation_v1"
            ),
            "scheduled_operation": asdict(operation),
            "executed_at_utc": observed,
            "result": result,
            "historical_eurusd_pnl_loaded": False,
            "strategy_or_signal_logic_changed": False,
            "broker_action_allowed": False,
        }
    )


def run_operations() -> int:
    lock = verify_preregistration()
    print(
        json.dumps(
            {
                "status": ("PROSPECTIVE_INVENTORY_CLOCK_OPERATIONS_HELPER_STARTED"),
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "locked_at_utc": lock["locked_at_utc"],
                "historical_backtest_allowed": False,
                "individual_clock_selection_allowed": False,
                "broker_action_allowed": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    operation = next_operation(datetime.now(timezone.utc))
    while True:
        while True:
            remaining = (
                operation.due_at_utc - datetime.now(timezone.utc)
            ).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 30.0))
        try:
            result = execute_operation(operation)
        except Exception as exc:  # noqa: BLE001
            result = {
                "schema_version": (
                    "eurusd_neutral_prospective_inventory_clock_operation_v1"
                ),
                "scheduled_operation": _serialize(asdict(operation)),
                "executed_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "OPERATION_FAILED_CONTINUING",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "historical_eurusd_pnl_loaded": False,
                "broker_action_allowed": False,
            }
        print(json.dumps(_serialize(result), sort_keys=True), flush=True)
        operation = next_operation(operation.due_at_utc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "prewarm-source",
            "source",
            "evaluate",
            "path",
            "status",
            "run",
        ),
    )
    parser.add_argument("--entry-date")
    parser.add_argument("--clock", choices=SLOTS)
    parser.add_argument("--source-hour")
    return parser.parse_args()


def _required(value: str | None, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} is required for this command")
    return value


def main() -> int:
    args = parse_args()
    verify_preregistration()
    if args.command == "run":
        return run_operations()
    if args.command == "status":
        result = build_validation_status()
    elif args.command == "prewarm-source":
        result = prewarm_source_hour(
            _required(args.entry_date, "--entry-date"),
            _required(args.clock, "--clock"),
            _required(args.source_hour, "--source-hour"),
        )
    elif args.command == "source":
        result = capture_source(
            _required(args.entry_date, "--entry-date"),
            _required(args.clock, "--clock"),
        )
    elif args.command == "evaluate":
        result = evaluate(
            _required(args.entry_date, "--entry-date"),
            _required(args.clock, "--clock"),
        )
    else:
        result = capture_trade_path(
            _required(args.entry_date, "--entry-date"),
            _required(args.clock, "--clock"),
        )
    print(json.dumps(_serialize(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
