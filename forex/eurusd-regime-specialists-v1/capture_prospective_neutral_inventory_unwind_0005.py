from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from capture_prospective_neutral_ownership import (
    DEFAULT_OUTPUT_ROOT as DEFAULT_OWNERSHIP_ROOT,
)
from capture_prospective_neutral_ownership import (
    _cached_hour,
    _validated_existing_ownership,
    decode_ticks,
    sha256_bytes,
    write_immutable,
)
from eurusd_regime_specialists.prospective_neutral_macro_crossasset_execution import (
    verify_neutral_ownership_record,
)
from eurusd_regime_specialists.research import PACKAGE_ROOT, sha256_file


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_inventory_unwind_0005_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_INVENTORY_UNWIND_0005_"
    "PREREG_2026_07_29.sha256.json"
)
DEFAULT_SOURCE_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-inventory-unwind-0005-v1/source"
)
DEFAULT_LEDGER_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-inventory-unwind-0005-v1/ledger"
)
PIP = 0.0001


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_preregistration() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_prospective_start") is not True
        or lock.get("historical_backtest_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Prospective 00:05 preregistration is incomplete")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(
                f"Prospective 00:05 implementation drift: {relative}"
            )
    return lock


def _timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.as_unit("ns")


def _entry_date(value: Any) -> pd.Timestamp:
    timestamp = _timestamp(value).floor("D")
    if _timestamp(value) != timestamp:
        raise ValueError("Entry date must be UTC midnight")
    return timestamp


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item) for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            _serialize(value),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            _serialize(value),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def source_hours(entry_date: Any) -> list[pd.Timestamp]:
    day = _entry_date(entry_date)
    return list(
        pd.date_range(
            day - pd.Timedelta(hours=4),
            day - pd.Timedelta(hours=1),
            freq="h",
        )
    )


def inventory_signal(
    ticks: pd.DataFrame,
    *,
    threshold_pips: float,
) -> dict[str, Any]:
    required = {"timestamp_utc", "bid", "ask"}
    if not required.issubset(ticks.columns):
        raise ValueError("Inventory ticks have an invalid schema")
    ordered = ticks.copy()
    ordered["timestamp_utc"] = pd.to_datetime(
        ordered["timestamp_utc"], utc=True
    ).dt.as_unit("ns")
    ordered = ordered.sort_values("timestamp_utc").reset_index(drop=True)
    if ordered.empty:
        raise ValueError("Inventory ticks are empty")
    first = ordered.iloc[0]
    last = ordered.iloc[-1]
    first_mid = 0.5 * (float(first["bid"]) + float(first["ask"]))
    last_mid = 0.5 * (float(last["bid"]) + float(last["ask"]))
    displacement_pips = (last_mid - first_mid) / PIP
    threshold = float(threshold_pips)
    side = (
        "SHORT"
        if displacement_pips >= threshold
        else "LONG"
        if displacement_pips <= -threshold
        else "CASH"
    )
    return {
        "first_tick_time_utc": first["timestamp_utc"],
        "last_tick_time_utc": last["timestamp_utc"],
        "first_mid": first_mid,
        "last_mid": last_mid,
        "displacement_pips": displacement_pips,
        "absolute_displacement_pips": abs(displacement_pips),
        "threshold_pips": threshold,
        "side": side,
        "signal_eligible": side in ("LONG", "SHORT"),
    }


def _existing_record(
    root: Path,
    folder: str,
    day: pd.Timestamp,
    *,
    prefix: str,
) -> dict[str, Any] | None:
    paths = sorted((root / folder).glob(f"{prefix}_{day:%Y-%m-%d}_*.json"))
    if not paths:
        return None
    if len(paths) != 1:
        raise RuntimeError(f"Multiple immutable {prefix} records exist")
    path = paths[0]
    payload = path.read_bytes()
    digest = sha256_bytes(payload)
    if path.name != f"{prefix}_{day:%Y-%m-%d}_{digest[:16]}.json":
        raise RuntimeError(f"{prefix} filename/hash drift")
    record = json.loads(payload)
    hash_field = (
        "source_record_sha256"
        if prefix == "SOURCE"
        else "decision_sha256"
    )
    core = {key: value for key, value in record.items() if key != hash_field}
    if record.get(hash_field) != _canonical_hash(core):
        raise RuntimeError(f"{prefix} canonical hash drift")
    return {
        **record,
        "relative_path": path.relative_to(root).as_posix(),
        "file_sha256": digest,
    }


def capture_source(
    entry_date: Any,
    *,
    source_root: Path = DEFAULT_SOURCE_ROOT,
    ownership_root: Path = DEFAULT_OWNERSHIP_ROOT,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    cfg = load_config()
    day = _entry_date(entry_date)
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _timestamp(now_utc)
    )
    start = _timestamp(cfg["prospective_start_utc"])
    if day < start:
        raise ValueError("Entry date precedes prospective start")
    existing = _existing_record(
        source_root, "records", day, prefix="SOURCE"
    )
    if existing is not None:
        return existing
    earliest = day + pd.Timedelta(minutes=3)
    deadline = day + pd.Timedelta(minutes=4)
    if observed < earliest:
        return {
            "status": "WAITING_FOR_SOURCE_CAPTURE_CLOCK",
            "entry_date_utc": day,
            "earliest_capture_utc": earliest,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    if observed > deadline:
        return {
            "status": "MISSED_SOURCE_DEADLINE_NO_BACKFILL",
            "entry_date_utc": day,
            "source_deadline_utc": deadline,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    raw_links: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []
    for hour in source_hours(day):
        cached = _cached_hour(ownership_root, "EURUSD", hour)
        if cached is None:
            return {
                "status": "WAITING_FOR_CACHED_COMPLETED_EURUSD_HOURS",
                "entry_date_utc": day,
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
                "late_hour_utc": hour,
                "source_observed_at_utc": market_observed,
                "source_deadline_utc": deadline,
                "network_request_made": False,
                "broker_action_allowed": False,
            }
        raw_relative = Path(str(metadata["raw_relative_path"]))
        raw_path = ownership_root / raw_relative
        metadata_relative = (
            Path("metadata") / "EURUSD" / raw_relative.name
        )
        metadata_path = ownership_root / metadata_relative
        if (
            sha256_file(raw_path) != str(metadata["raw_sha256"])
            or not metadata_path.is_file()
        ):
            raise RuntimeError("Cached inventory source evidence drift")
        frames.append(decode_ticks(payload, "EURUSD", hour))
        raw_links.append(
            {
                "hour_utc": hour,
                "observed_at_utc": market_observed,
                "raw_relative_path": raw_relative,
                "raw_sha256": str(metadata["raw_sha256"]),
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": sha256_file(metadata_path),
            }
        )
    ticks = pd.concat(frames, ignore_index=True)
    signal = inventory_signal(
        ticks,
        threshold_pips=float(
            cfg["inventory_source"][
                "minimum_absolute_displacement_pips"
            ]
        ),
    )
    core = {
        "schema_version": (
            "eurusd_neutral_prospective_inventory_source_v1"
        ),
        "status": (
            "SOURCE_SIGNAL"
            if signal["signal_eligible"]
            else "SOURCE_CASH_SUBTHRESHOLD"
        ),
        "entry_date_utc": day.strftime("%Y-%m-%d"),
        "source_window_start_utc": day - pd.Timedelta(hours=4),
        "source_window_end_utc": day,
        "source_captured_at_utc": observed,
        "source_observed_at_utc": max(
            row["observed_at_utc"] for row in raw_links
        ),
        "raw_links": raw_links,
        "signal": signal,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }
    record = {
        **core,
        "source_record_sha256": _canonical_hash(core),
    }
    payload = _json_bytes(record)
    digest = sha256_bytes(payload)
    relative = (
        Path("records")
        / f"SOURCE_{day:%Y-%m-%d}_{digest[:16]}.json"
    )
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
    day = _timestamp(
        f"{source['entry_date_utc']}T00:00:00Z"
    ).floor("D")
    created = _timestamp(created_at_utc)
    decision_time = day + pd.Timedelta(minutes=4)
    latest_creation = day + pd.Timedelta(minutes=5) - pd.Timedelta(
        nanoseconds=1
    )
    if created < decision_time:
        raise ValueError("Decision cannot be created before 00:04 UTC")
    source_observed = _timestamp(source["source_observed_at_utc"])
    ownership_observed = _timestamp(
        ownership["ownership_observed_at_utc"]
    )
    reasons: list[str] = []
    if day.weekday() >= 5:
        reasons.append("WEEKEND")
    if source_observed > decision_time:
        reasons.append("LATE_SOURCE")
    if ownership_observed > decision_time:
        reasons.append("LATE_OWNERSHIP")
    if not bool(ownership["is_neutral"]):
        reasons.append("NOT_NEUTRAL")
    if float(ownership["state_staleness_hours"]) > float(
        config["neutral_ownership"]["maximum_state_staleness_hours"]
    ):
        reasons.append("STALE_OWNERSHIP")
    source_side = str(source["signal"]["side"])
    if source_side not in ("LONG", "SHORT"):
        reasons.append("SUBTHRESHOLD")
    if created > latest_creation:
        reasons.append("MISSED_DECISION_CREATION_DEADLINE")
    status = "SIGNAL" if not reasons else "CASH"
    core = {
        "schema_version": (
            "eurusd_neutral_prospective_inventory_decision_v1"
        ),
        "campaign_id": config["campaign_id"],
        "entry_date_utc": day.strftime("%Y-%m-%d"),
        "decision_time_utc": decision_time,
        "decision_created_at_utc": created,
        "entry_time_utc": day + pd.Timedelta(minutes=5),
        "status": status,
        "reasons": reasons,
        "side": source_side if status == "SIGNAL" else "CASH",
        "source_record_sha256": source["source_record_sha256"],
        "source_file_sha256": source["file_sha256"],
        "ownership_evidence_sha256": ownership[
            "ownership_evidence_sha256"
        ],
        "inventory_displacement_pips": float(
            source["signal"]["displacement_pips"]
        ),
        "fixed_stop_pips": float(config["risk"]["fixed_stop_pips"]),
        "fixed_target_pips": float(config["risk"]["fixed_target_pips"]),
        "maximum_hold_hours": int(
            config["risk"]["maximum_hold_hours"]
        ),
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "broker_action_allowed": False,
    }
    return {**core, "decision_sha256": _canonical_hash(core)}


def evaluate(
    entry_date: Any,
    *,
    source_root: Path = DEFAULT_SOURCE_ROOT,
    ownership_root: Path = DEFAULT_OWNERSHIP_ROOT,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    cfg = load_config()
    day = _entry_date(entry_date)
    existing = _existing_record(
        ledger_root, "decisions", day, prefix="DECISION"
    )
    if existing is not None:
        return existing
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _timestamp(now_utc)
    )
    if observed < day + pd.Timedelta(minutes=4):
        return {
            "status": "WAITING_FOR_DECISION_CLOCK",
            "entry_date_utc": day,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    source = _existing_record(
        source_root, "records", day, prefix="SOURCE"
    )
    ownership_link = _validated_existing_ownership(
        ownership_root, day
    )
    if source is None or ownership_link is None:
        placeholder_source = source or {
            "entry_date_utc": day.strftime("%Y-%m-%d"),
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
        decision = build_decision(
            placeholder_source,
            placeholder_ownership,
            config=cfg,
            created_at_utc=observed,
        )
        missing = []
        if source is None:
            missing.append("MISSING_ON_TIME_SOURCE_RECORD")
        if ownership_link is None:
            missing.append("MISSING_ON_TIME_OWNERSHIP_RECORD")
        decision["reasons"] = sorted(
            set([*decision["reasons"], *missing])
        )
        decision["decision_sha256"] = _canonical_hash(
            {
                key: value
                for key, value in decision.items()
                if key != "decision_sha256"
            }
        )
    else:
        ownership_path = (
            ownership_root
            / ownership_link["ownership_record_relative_path"]
        )
        ownership = json.loads(
            ownership_path.read_text(encoding="utf-8")
        )
        verify_neutral_ownership_record(ownership)
        ownership["file_sha256"] = sha256_file(ownership_path)
        decision = build_decision(
            source,
            ownership,
            config=cfg,
            created_at_utc=observed,
        )
    payload = _json_bytes(decision)
    digest = sha256_bytes(payload)
    relative = (
        Path("decisions")
        / f"DECISION_{day:%Y-%m-%d}_{digest[:16]}.json"
    )
    write_immutable(ledger_root / relative, payload)
    return {
        **_serialize(decision),
        "relative_path": relative.as_posix(),
        "file_sha256": digest,
        "network_request_made": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("source", "evaluate"))
    parser.add_argument("--entry-date", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_preregistration()
    result = (
        capture_source(args.entry_date)
        if args.command == "source"
        else evaluate(args.entry_date)
    )
    print(json.dumps(_serialize(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
