from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from capture_prospective_dukascopy_event_m5 import (
    decode_ticks,
    fetch_hour,
    sha256_bytes,
    sha256_file,
    write_immutable,
)
from capture_prospective_neutral_gdelt_relative_tone import (
    load_and_verify_preregistration,
)
from run_prospective_neutral_gdelt_relative_tone import (
    DEFAULT_LEDGER_ROOT,
    _entry_date,
    _utc,
    _validated_existing_decision,
)

DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-gdelt-relative-tone-v1/path"
)
ROOT = Path(__file__).resolve().parent
PATH_IMPLEMENTATION_LOCK = (
    ROOT
    / (
        "EURUSD_NEUTRAL_PROSPECTIVE_GDELT_RELATIVE_TONE_PATH_"
        "IMPLEMENTATION_2026_07_28.sha256.json"
    )
)
MACRO_LEDGER_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-macro-crossasset-agreement-v1/ledger"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_gdelt_trade_path_v1"
MINIMUM_CAPTURE_LAG_SECONDS = 60


def verify_path_implementation_lock() -> dict[str, Any]:
    lock = json.loads(
        PATH_IMPLEMENTATION_LOCK.read_text(encoding="utf-8")
    )
    if lock.get("locked_before_first_signal_and_path_outcome") is not True:
        raise RuntimeError("GDELT path implementation was not locked in time")
    for relative, expected in lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"GDELT path implementation drift: {relative}")
    for reference in (
        lock["strategy_preregistration"],
        lock["source_and_decision_implementation"],
    ):
        if sha256_file(ROOT / reference["path"]) != reference["sha256"]:
            raise RuntimeError("GDELT path lock reference drift")
    return lock


def _timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.as_unit("ns")


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def required_path_hours(
    entry_time_utc: Any,
    *,
    maximum_hold_hours: int = 4,
) -> list[pd.Timestamp]:
    entry = _timestamp(entry_time_utc)
    deadline = entry + pd.Timedelta(hours=maximum_hold_hours)
    first = entry.floor("h")
    last = deadline.floor("h")
    return list(pd.date_range(first, last, freq="h"))


def path_capture_ready(
    entry_time_utc: Any,
    observed_at_utc: Any,
    *,
    maximum_hold_hours: int = 4,
    minimum_lag_seconds: int = MINIMUM_CAPTURE_LAG_SECONDS,
) -> bool:
    entry = _timestamp(entry_time_utc)
    observed = _timestamp(observed_at_utc)
    deadline = entry + pd.Timedelta(hours=maximum_hold_hours)
    return observed >= deadline + pd.Timedelta(
        seconds=minimum_lag_seconds
    )


def _macro_conflict(
    entry_time: pd.Timestamp,
    macro_ledger_root: Path,
) -> dict[str, Any] | None:
    for path in sorted(
        macro_ledger_root.glob("signals/records/*.json")
    ):
        record = json.loads(path.read_text(encoding="utf-8"))
        if str(record.get("side")) not in ("LONG", "SHORT"):
            continue
        macro_entry = _timestamp(record["entry_time_utc"])
        conservative_exit = macro_entry + pd.Timedelta(hours=12)
        if macro_entry <= entry_time <= conservative_exit:
            return {
                "signal_id": str(record["signal_id"]),
                "entry_time_utc": macro_entry,
                "conservative_exit_time_utc": conservative_exit,
                "policy": (
                    "ASSUME_MACRO_POSITION_OPEN_FOR_FULL_FROZEN_12H_HOLD"
                ),
            }
    return None


def _entry_quotes(
    bid: float,
    ask: float,
    *,
    minimum_spread_pips: float,
) -> dict[str, float]:
    pip = 0.0001
    actual_spread = (ask - bid) / pip
    effective_spread = max(actual_spread, minimum_spread_pips)
    mid = 0.5 * (bid + ask)
    return {
        "actual_spread_pips": actual_spread,
        "effective_spread_pips": effective_spread,
        "effective_bid": mid - 0.5 * effective_spread * pip,
        "effective_ask": mid + 0.5 * effective_spread * pip,
    }


def execute_ticks(
    decision: dict[str, Any],
    ticks: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    side = str(decision["side"])
    if side not in ("LONG", "SHORT"):
        raise ValueError("Tick execution requires a directional signal")
    day = pd.Timestamp(decision["entry_date_utc"], tz="UTC")
    entry_time = day + pd.Timedelta(
        hours=0,
        minutes=20,
    )
    risk = config["risk"]
    entry_config = config["decision_and_entry"]
    deadline = entry_time + pd.Timedelta(
        hours=int(risk["maximum_hold_hours"])
    )
    ordered = ticks.copy()
    ordered["timestamp_utc"] = pd.to_datetime(
        ordered["timestamp_utc"], utc=True
    ).dt.as_unit("ns")
    ordered = ordered.sort_values("timestamp_utc").reset_index(drop=True)
    entry_rows = ordered[ordered["timestamp_utc"].ge(entry_time)]
    if entry_rows.empty:
        return {
            "status": "NO_TRADE_MISSING_ENTRY_TICK",
            "side": side,
            "entry_time_utc": entry_time,
            "deadline_utc": deadline,
        }
    entry_tick = entry_rows.iloc[0]
    quotes = _entry_quotes(
        float(entry_tick["bid"]),
        float(entry_tick["ask"]),
        minimum_spread_pips=float(
            entry_config["minimum_retail_spread_pips"]
        ),
    )
    if quotes["actual_spread_pips"] > float(
        entry_config["maximum_entry_spread_pips"]
    ):
        return {
            "status": "NO_TRADE_EXCESS_ENTRY_SPREAD",
            "side": side,
            "entry_time_utc": entry_time,
            "entry_tick_time_utc": entry_tick["timestamp_utc"],
            **quotes,
        }
    pip = 0.0001
    slippage = float(
        entry_config["adverse_slippage_pips_per_side"]
    )
    stop_pips = float(risk["fixed_stop_pips"])
    target_pips = float(risk["fixed_target_pips"])
    if side == "LONG":
        entry_fill = quotes["effective_ask"] + slippage * pip
        stop_price = entry_fill - stop_pips * pip
        target_price = entry_fill + target_pips * pip
    else:
        entry_fill = quotes["effective_bid"] - slippage * pip
        stop_price = entry_fill + stop_pips * pip
        target_price = entry_fill - target_pips * pip
    path = ordered[
        ordered["timestamp_utc"].ge(entry_tick["timestamp_utc"])
        & ordered["timestamp_utc"].lt(deadline)
    ]
    exit_reason: str | None = None
    exit_tick: pd.Series | None = None
    barrier_price: float | None = None
    for _, tick in path.iterrows():
        observed_price = float(tick["bid"] if side == "LONG" else tick["ask"])
        if (
            side == "LONG"
            and observed_price <= stop_price
            or side == "SHORT"
            and observed_price >= stop_price
        ):
            exit_reason = "STOP"
            exit_tick = tick
            barrier_price = stop_price
            break
        if (
            side == "LONG"
            and observed_price >= target_price
            or side == "SHORT"
            and observed_price <= target_price
        ):
            exit_reason = "TARGET"
            exit_tick = tick
            barrier_price = target_price
            break
    if exit_tick is None:
        time_rows = ordered[ordered["timestamp_utc"].ge(deadline)]
        if time_rows.empty:
            return {
                "status": "PENDING_MISSING_TIME_EXIT_TICK",
                "side": side,
                "entry_time_utc": entry_time,
                "deadline_utc": deadline,
            }
        exit_reason = "TIME"
        exit_tick = time_rows.iloc[0]
    market_exit = float(
        exit_tick["bid"] if side == "LONG" else exit_tick["ask"]
    )
    exit_fill = (
        market_exit - slippage * pip
        if side == "LONG"
        else market_exit + slippage * pip
    )
    direction = 1.0 if side == "LONG" else -1.0
    pnl_pips = direction * (exit_fill - entry_fill) / pip
    result_r = pnl_pips / stop_pips
    stress_r = (
        result_r
        - float(risk["extra_round_trip_stress_pips"]) / stop_pips
    )
    return {
        "status": "CLOSED",
        "side": side,
        "entry_time_utc": entry_time,
        "entry_tick_time_utc": entry_tick["timestamp_utc"],
        "entry_bid": float(entry_tick["bid"]),
        "entry_ask": float(entry_tick["ask"]),
        **quotes,
        "entry_fill": entry_fill,
        "stop_price": stop_price,
        "target_price": target_price,
        "exit_time_utc": exit_tick["timestamp_utc"],
        "exit_bid": float(exit_tick["bid"]),
        "exit_ask": float(exit_tick["ask"]),
        "market_exit_price": market_exit,
        "barrier_price": barrier_price,
        "exit_fill": exit_fill,
        "exit_reason": exit_reason,
        "pnl_pips": pnl_pips,
        "r": result_r,
        "extra_half_pip_stress_r": stress_r,
        "fixed_stop_pips": stop_pips,
        "fixed_target_pips": target_pips,
        "adverse_slippage_pips_per_side": slippage,
    }


def _existing_result(
    output_root: Path,
    decision_id: str,
) -> dict[str, Any] | None:
    paths = sorted(
        output_root.glob(f"manifests/PATH_{decision_id}_*.json")
    )
    if not paths:
        return None
    if len(paths) != 1:
        raise RuntimeError("Multiple GDELT path manifests exist")
    path = paths[0]
    payload = path.read_bytes()
    digest = sha256_bytes(payload)
    if path.name != f"PATH_{decision_id}_{digest[:16]}.json":
        raise RuntimeError("GDELT path manifest name/hash drift")
    manifest = json.loads(payload)
    for raw in manifest.get("raw_snapshots", []):
        if (
            sha256_file(output_root / raw["raw_relative_path"])
            != raw["raw_sha256"]
            or sha256_file(output_root / raw["metadata_relative_path"])
            != raw["metadata_sha256"]
        ):
            raise RuntimeError("GDELT path raw evidence drift")
    return {
        **manifest,
        "manifest_relative_path": path.relative_to(
            output_root
        ).as_posix(),
        "manifest_sha256": digest,
        "network_request_made": False,
    }


def capture_trade_path(
    entry_date: Any,
    *,
    ledger_root: Path = DEFAULT_LEDGER_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    macro_ledger_root: Path = MACRO_LEDGER_ROOT,
    now_utc: Any | None = None,
    fetcher: Callable[
        [str, pd.Timestamp], tuple[bytes, dict[str, Any]]
    ] = fetch_hour,
) -> dict[str, Any]:
    config, _ = load_and_verify_preregistration()
    path_lock = verify_path_implementation_lock()
    day = _entry_date(entry_date)
    decision = _validated_existing_decision(ledger_root, day)
    if decision is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "WAITING_FOR_IMMUTABLE_DECISION",
            "entry_date_utc": day.isoformat(),
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    decision_id = decision["decision_sha256"]
    existing = _existing_result(output_root, decision_id)
    if existing is not None:
        return existing
    if decision["status"] != "SIGNAL":
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "CASH_DECISION_NO_TRADE",
            "entry_date_utc": day.isoformat(),
            "decision_id": decision_id,
            "decision_status": decision["status"],
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    entry_time = pd.Timestamp(day, tz="UTC") + pd.Timedelta(minutes=20)
    maximum_hold = int(config["risk"]["maximum_hold_hours"])
    deadline = entry_time + pd.Timedelta(hours=maximum_hold)
    observed = (
        pd.Timestamp.now(tz="UTC").as_unit("ns")
        if now_utc is None
        else _timestamp(now_utc)
    )
    if not path_capture_ready(
        entry_time,
        observed,
        maximum_hold_hours=maximum_hold,
    ):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "WAITING_FOR_4H_PATH_COMPLETION",
            "entry_date_utc": day.isoformat(),
            "decision_id": decision_id,
            "entry_time_utc": entry_time,
            "deadline_utc": deadline,
            "earliest_capture_utc": deadline
            + pd.Timedelta(seconds=MINIMUM_CAPTURE_LAG_SECONDS),
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    conflict = _macro_conflict(entry_time, macro_ledger_root)
    if conflict is not None:
        execution = {
            "status": "SKIPPED_CONSERVATIVE_MACRO_POSITION_CONFLICT",
            "side": decision["side"],
            "entry_time_utc": entry_time,
            "conflict": conflict,
        }
        raw_records: list[dict[str, Any]] = []
        network_request_made = False
    else:
        raw_records = []
        frames: list[pd.DataFrame] = []
        for hour in required_path_hours(
            entry_time,
            maximum_hold_hours=maximum_hold,
        ):
            payload, metadata = fetcher("EURUSD", hour)
            if str(metadata.get("symbol")) != "EURUSD":
                raise RuntimeError("GDELT path fetch returned another symbol")
            if _utc(metadata.get("hour_utc")) != hour:
                raise RuntimeError("GDELT path fetch returned another hour")
            raw_hash = sha256_bytes(payload)
            raw_relative = (
                Path("raw")
                / decision_id
                / f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
            )
            metadata_relative = (
                Path("metadata")
                / decision_id
                / f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
            )
            write_immutable(output_root / raw_relative, payload)
            metadata_payload = {
                "schema_version": SCHEMA_VERSION,
                "decision_id": decision_id,
                **metadata,
                "raw_relative_path": raw_relative.as_posix(),
                "raw_sha256": raw_hash,
            }
            write_immutable(
                output_root / metadata_relative,
                _json_bytes(_serialize(metadata_payload)),
            )
            frames.append(decode_ticks(payload, "EURUSD", hour))
            raw_records.append(
                {
                    "hour_utc": hour,
                    "observed_at_utc": _utc(metadata["observed_at_utc"]),
                    "raw_relative_path": raw_relative,
                    "raw_sha256": raw_hash,
                    "metadata_relative_path": metadata_relative,
                    "metadata_sha256": sha256_file(
                        output_root / metadata_relative
                    ),
                }
            )
        ticks = pd.concat(frames, ignore_index=True)
        execution = execute_ticks(decision, ticks, config)
        network_request_made = True
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": execution["status"],
        "entry_date_utc": day.isoformat(),
        "decision_id": decision_id,
        "decision_relative_path": decision["decision_relative_path"],
        "decision_sha256": decision_id,
        "entry_time_utc": entry_time,
        "deadline_utc": deadline,
        "captured_at_utc": observed,
        "path_implementation_lock_sha256": sha256_file(
            PATH_IMPLEMENTATION_LOCK
        ),
        "path_implementation_locked_at_utc": path_lock["locked_at_utc"],
        "raw_snapshots": raw_records,
        "execution": execution,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "broker_action_allowed": False,
    }
    payload = _json_bytes(_serialize(manifest))
    digest = sha256_bytes(payload)
    relative = (
        Path("manifests")
        / f"PATH_{decision_id}_{digest[:16]}.json"
    )
    write_immutable(output_root / relative, payload)
    return _serialize(
        {
            **manifest,
            "manifest_relative_path": relative,
            "manifest_sha256": digest,
            "network_request_made": network_request_made,
        }
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture",))
    parser.add_argument("--entry-date", required=True)
    parser.add_argument(
        "--ledger-root",
        type=Path,
        default=DEFAULT_LEDGER_ROOT,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument(
        "--macro-ledger-root",
        type=Path,
        default=MACRO_LEDGER_ROOT,
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    result = capture_trade_path(
        args.entry_date,
        ledger_root=args.ledger_root,
        output_root=args.output_root,
        macro_ledger_root=args.macro_ledger_root,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
