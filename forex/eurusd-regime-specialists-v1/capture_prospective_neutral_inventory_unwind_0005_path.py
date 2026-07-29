from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

import pandas as pd

from capture_prospective_neutral_inventory_unwind_0005 import (
    DEFAULT_LEDGER_ROOT,
    _entry_date,
    _existing_record,
    _json_bytes,
    _serialize,
    _timestamp,
    load_config,
    verify_preregistration,
)
from capture_prospective_neutral_ownership import (
    decode_ticks,
    fetch_hour,
    sha256_bytes,
    write_immutable,
)
from eurusd_regime_specialists.research import sha256_file


DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-inventory-unwind-0005-v1/path"
)
PIP = 0.0001


def required_path_hours(
    entry_time_utc: Any,
    *,
    maximum_hold_hours: int,
) -> list[pd.Timestamp]:
    entry = _timestamp(entry_time_utc)
    deadline = entry + pd.Timedelta(hours=maximum_hold_hours)
    return list(
        pd.date_range(
            entry.floor("h"),
            deadline.floor("h"),
            freq="h",
        )
    )


def earliest_path_capture(
    entry_time_utc: Any,
    *,
    maximum_hold_hours: int,
    publication_lag_seconds: int = 60,
) -> pd.Timestamp:
    deadline = _timestamp(entry_time_utc) + pd.Timedelta(
        hours=maximum_hold_hours
    )
    final_hour_end = deadline.floor("h") + pd.Timedelta(hours=1)
    return final_hour_end + pd.Timedelta(
        seconds=publication_lag_seconds
    )


def _entry_quotes(
    bid: float,
    ask: float,
    *,
    minimum_spread_pips: float,
) -> dict[str, float]:
    actual = (ask - bid) / PIP
    effective = max(actual, float(minimum_spread_pips))
    mid = 0.5 * (bid + ask)
    return {
        "actual_spread_pips": actual,
        "effective_spread_pips": effective,
        "effective_bid": mid - 0.5 * effective * PIP,
        "effective_ask": mid + 0.5 * effective * PIP,
    }


def execute_ticks(
    decision: Mapping[str, Any],
    ticks: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    side = str(decision["side"])
    if side not in ("LONG", "SHORT"):
        raise ValueError("Tick execution requires a directional signal")
    entry_time = _timestamp(decision["entry_time_utc"])
    risk = config["risk"]
    entry_cfg = config["decision_and_entry"]
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
            entry_cfg["minimum_retail_spread_pips"]
        ),
    )
    if quotes["actual_spread_pips"] > float(
        entry_cfg["maximum_entry_spread_pips"]
    ):
        return {
            "status": "NO_TRADE_EXCESS_ENTRY_SPREAD",
            "side": side,
            "entry_time_utc": entry_time,
            "entry_tick_time_utc": entry_tick["timestamp_utc"],
            **quotes,
        }
    slippage = float(entry_cfg["adverse_slippage_pips_per_side"])
    stop_pips = float(risk["fixed_stop_pips"])
    target_pips = float(risk["fixed_target_pips"])
    if side == "LONG":
        entry_fill = quotes["effective_ask"] + slippage * PIP
        stop_price = entry_fill - stop_pips * PIP
        target_price = entry_fill + target_pips * PIP
    else:
        entry_fill = quotes["effective_bid"] - slippage * PIP
        stop_price = entry_fill + stop_pips * PIP
        target_price = entry_fill - target_pips * PIP
    path = ordered[
        ordered["timestamp_utc"].ge(entry_tick["timestamp_utc"])
        & ordered["timestamp_utc"].lt(deadline)
    ]
    exit_reason: str | None = None
    exit_tick: pd.Series | None = None
    barrier_price: float | None = None
    for _, tick in path.iterrows():
        observed_price = float(
            tick["bid"] if side == "LONG" else tick["ask"]
        )
        stop_hit = (
            side == "LONG"
            and observed_price <= stop_price
            or side == "SHORT"
            and observed_price >= stop_price
        )
        target_hit = (
            side == "LONG"
            and observed_price >= target_price
            or side == "SHORT"
            and observed_price <= target_price
        )
        if stop_hit:
            exit_reason = "STOP"
            exit_tick = tick
            barrier_price = stop_price
            break
        if target_hit:
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
        market_exit - slippage * PIP
        if side == "LONG"
        else market_exit + slippage * PIP
    )
    direction = 1.0 if side == "LONG" else -1.0
    pnl_pips = direction * (exit_fill - entry_fill) / PIP
    result_r = pnl_pips / stop_pips
    stress_r = result_r - float(
        risk["extra_round_trip_stress_pips"]
    ) / stop_pips
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


def _evidence_chain(output_root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(
        [
            *output_root.glob("raw/**/*.json"),
            *output_root.glob("metadata/**/*.json"),
        ],
        key=lambda path: path.relative_to(output_root).as_posix(),
    )
    for path in paths:
        digest.update(
            path.relative_to(output_root).as_posix().encode("utf-8")
        )
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _existing_path(
    output_root: Path,
    decision_id: str,
) -> dict[str, Any] | None:
    paths = sorted(
        output_root.glob(f"manifests/PATH_{decision_id}_*.json")
    )
    if not paths:
        return None
    if len(paths) != 1:
        raise RuntimeError("Multiple inventory path manifests exist")
    path = paths[0]
    payload = path.read_bytes()
    digest = sha256_bytes(payload)
    if path.name != f"PATH_{decision_id}_{digest[:16]}.json":
        raise RuntimeError("Inventory path manifest filename/hash drift")
    manifest = json.loads(payload)
    for raw in manifest.get("raw_snapshots", []):
        if (
            sha256_file(output_root / raw["raw_relative_path"])
            != raw["raw_sha256"]
            or sha256_file(output_root / raw["metadata_relative_path"])
            != raw["metadata_sha256"]
        ):
            raise RuntimeError("Inventory path raw evidence drift")
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
    now_utc: Any | None = None,
    fetcher: Callable[
        [str, pd.Timestamp], tuple[bytes, dict[str, Any]]
    ] = fetch_hour,
) -> dict[str, Any]:
    verify_preregistration()
    cfg = load_config()
    day = _entry_date(entry_date)
    decision = _existing_record(
        ledger_root, "decisions", day, prefix="DECISION"
    )
    if decision is None:
        return {
            "status": "WAITING_FOR_IMMUTABLE_DECISION",
            "entry_date_utc": day,
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
            "decision_id": decision_id,
            "decision_status": decision["status"],
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    entry_time = _timestamp(decision["entry_time_utc"])
    maximum_hold = int(cfg["risk"]["maximum_hold_hours"])
    deadline = entry_time + pd.Timedelta(hours=maximum_hold)
    earliest = earliest_path_capture(
        entry_time,
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
            "decision_id": decision_id,
            "entry_time_utc": entry_time,
            "deadline_utc": deadline,
            "earliest_capture_utc": earliest,
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    raw_records: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []
    for hour in required_path_hours(
        entry_time,
        maximum_hold_hours=maximum_hold,
    ):
        payload, metadata = fetcher("EURUSD", hour)
        if (
            str(metadata.get("symbol")) != "EURUSD"
            or _timestamp(metadata.get("hour_utc")) != hour
        ):
            raise RuntimeError("Inventory path fetch linkage drift")
        raw_hash = sha256_bytes(payload)
        name = f"{hour:%Y%m%dT%H0000Z}_{raw_hash[:16]}.json"
        raw_relative = Path("raw") / decision_id / name
        metadata_relative = Path("metadata") / decision_id / name
        write_immutable(output_root / raw_relative, payload)
        metadata_payload = {
            "schema_version": (
                "eurusd_neutral_prospective_inventory_path_v1"
            ),
            "decision_id": decision_id,
            **metadata,
            "raw_relative_path": raw_relative,
            "raw_sha256": raw_hash,
        }
        metadata_bytes = _json_bytes(metadata_payload)
        write_immutable(output_root / metadata_relative, metadata_bytes)
        raw_records.append(
            {
                "hour_utc": hour,
                "observed_at_utc": _timestamp(
                    metadata["observed_at_utc"]
                ),
                "raw_relative_path": raw_relative,
                "raw_sha256": raw_hash,
                "metadata_relative_path": metadata_relative,
                "metadata_sha256": sha256_bytes(metadata_bytes),
            }
        )
        frames.append(decode_ticks(payload, "EURUSD", hour))
    market_observed = max(
        row["observed_at_utc"] for row in raw_records
    )
    if market_observed < earliest:
        raise RuntimeError("Path evidence predates publication boundary")
    execution = execute_ticks(
        decision,
        pd.concat(frames, ignore_index=True),
        cfg,
    )
    chain = _evidence_chain(output_root)
    manifest = {
        "schema_version": (
            "eurusd_neutral_prospective_inventory_path_v1"
        ),
        "entry_date_utc": day.strftime("%Y-%m-%d"),
        "decision_id": decision_id,
        "decision_file_sha256": decision["file_sha256"],
        "entry_time_utc": entry_time,
        "deadline_utc": deadline,
        "path_captured_at_utc": observed,
        "market_observed_at_utc": market_observed,
        "raw_snapshots": raw_records,
        "path_evidence_chain_sha256": chain,
        "execution": execution,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "broker_action_allowed": False,
    }
    payload = _json_bytes(manifest)
    digest = sha256_bytes(payload)
    relative = (
        Path("manifests")
        / f"PATH_{decision_id}_{digest[:16]}.json"
    )
    write_immutable(output_root / relative, payload)
    return {
        **_serialize(manifest),
        "manifest_relative_path": relative.as_posix(),
        "manifest_sha256": digest,
        "network_request_made": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture",))
    parser.add_argument("--entry-date", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = capture_trade_path(args.entry_date)
    print(json.dumps(_serialize(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
