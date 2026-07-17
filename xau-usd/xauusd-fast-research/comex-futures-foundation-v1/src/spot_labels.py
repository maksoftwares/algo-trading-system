from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Mapping

import numpy as np
import pandas as pd

from foundation import ROOT


REPO_ROOT = ROOT.parents[2]
DEFAULT_LABEL_CONFIG = ROOT / "config" / "spot_label_contract_v1.json"
HOUR_MS = 60 * 60 * 1000


class SpotLabelError(RuntimeError):
    """Raised when a candidate cannot be labeled without violating the contract."""


def load_label_config(path: Path = DEFAULT_LABEL_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_dukascopy_foundation() -> Any:
    source = REPO_ROOT / "multi-asset" / "data-foundation" / "dukascopy-ticks-v1" / "src"
    if not source.is_dir():
        raise SpotLabelError(f"Dukascopy foundation source is missing: {source}")
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    from dukascopy_tick_foundation import foundation

    return foundation


def resolve_spot_storage(config: Mapping[str, Any]) -> Path:
    source = config["spot_source"]
    value = os.environ.get(source["storage_environment_variable"], source["default_storage_root"])
    path = Path(value).resolve()
    if not path.is_dir():
        raise SpotLabelError(f"Dukascopy storage root is missing: {path}")
    return path


class CompletedM5Atr:
    def __init__(self, frame: pd.DataFrame, *, bar_width_ms: int) -> None:
        required = {"timestamp_ms", "atr"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise SpotLabelError(f"M5 feature cache is missing columns: {missing}")
        clean = frame[["timestamp_ms", "atr"]].copy()
        clean["timestamp_ms"] = pd.to_numeric(clean["timestamp_ms"], errors="raise").astype("int64")
        clean["atr"] = pd.to_numeric(clean["atr"], errors="coerce")
        clean = clean.sort_values("timestamp_ms", kind="stable").reset_index(drop=True)
        if clean["timestamp_ms"].duplicated().any():
            raise SpotLabelError("M5 feature cache contains duplicate bar timestamps.")
        self.timestamps = clean["timestamp_ms"].to_numpy(dtype=np.int64)
        self.atr = clean["atr"].to_numpy(dtype=float)
        self.bar_width_ms = int(bar_width_ms)

    def at_decision(self, decision_timestamp_ms: int) -> float | None:
        latest_completed_start = int(decision_timestamp_ms) - self.bar_width_ms
        index = int(np.searchsorted(self.timestamps, latest_completed_start, side="right") - 1)
        if index < 0 or not np.isfinite(self.atr[index]) or self.atr[index] <= 0:
            return None
        return float(self.atr[index])


def load_completed_atr(config: Mapping[str, Any], storage_root: Path) -> CompletedM5Atr:
    source = config["spot_source"]
    path = storage_root / source["m5_feature_cache"]
    if not path.is_file():
        raise SpotLabelError(f"M5 feature cache is missing: {path}")
    return CompletedM5Atr(
        pd.read_parquet(path, columns=["timestamp_ms", "atr"]),
        bar_width_ms=int(source["m5_bar_width_ms"]),
    )


class VerifiedSpotTickStore:
    def __init__(self, *, storage_root: Path, symbol: str, foundation: Any) -> None:
        self.storage_root = storage_root.resolve()
        self.symbol = symbol
        self.foundation = foundation
        self.validated_months: set[tuple[int, int]] = set()

    def _ensure_month(self, year: int, month: int) -> None:
        key = (year, month)
        if key in self.validated_months:
            return
        try:
            self.foundation.validate_month_acquisition_manifest(
                self.storage_root, self.symbol, year, month
            )
        except Exception as exc:
            raise SpotLabelError(f"Invalid Dukascopy month {year:04d}-{month:02d}") from exc
        self.validated_months.add(key)

    @lru_cache(maxsize=512)
    def load_hour(self, hour_timestamp_ms: int) -> tuple[Any, ...]:
        hour_timestamp_ms -= hour_timestamp_ms % HOUR_MS
        hour = datetime.fromtimestamp(hour_timestamp_ms / 1000, UTC)
        self._ensure_month(hour.year, hour.month)
        path = self.foundation.raw_hour_path(self.storage_root, self.symbol, hour)
        if not path.is_file():
            raise SpotLabelError(f"Missing Dukascopy raw hour: {path}")
        try:
            ticks = tuple(self.foundation.decode_payload(path.read_bytes(), self.symbol, path.name))
        except Exception as exc:
            raise SpotLabelError(f"Invalid Dukascopy raw hour: {path}") from exc
        if any(
            not hour_timestamp_ms <= int(tick.timestamp_ms) < hour_timestamp_ms + HOUR_MS
            for tick in ticks
        ):
            raise SpotLabelError(f"Tick outside raw-hour boundary: {path}")
        return ticks

    def ticks_between(self, start_timestamp_ms: int, end_timestamp_ms: int) -> Iterator[Any]:
        hour = start_timestamp_ms - start_timestamp_ms % HOUR_MS
        while hour <= end_timestamp_ms:
            for tick in self.load_hour(hour):
                timestamp = int(tick.timestamp_ms)
                if start_timestamp_ms <= timestamp <= end_timestamp_ms:
                    yield tick
            hour += HOUR_MS

    def first_tick_strictly_after(self, timestamp_ms: int, maximum_delay_ms: int) -> Any | None:
        for tick in self.ticks_between(timestamp_ms, timestamp_ms + maximum_delay_ms):
            if int(tick.timestamp_ms) > timestamp_ms:
                return tick
        return None


def _timestamp_ms(value: Any) -> int:
    return int(pd.Timestamp(value).timestamp() * 1000)


def _iso_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, UTC).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _split(timestamp_ms: int, config: Mapping[str, Any]) -> str | None:
    for name, (start, end) in config["splits"].items():
        if _timestamp_ms(start) <= timestamp_ms < _timestamp_ms(end):
            return str(name)
    return None


def _candidate_value(candidate: Mapping[str, Any], key: str) -> Any:
    value = candidate[key]
    return value.item() if hasattr(value, "item") else value


def _empty_label(
    candidate: Mapping[str, Any], *, status: str, reason: str, split: str | None = None
) -> dict[str, Any]:
    return {
        "candidate_id": str(candidate.get("candidate_id", "")),
        "family": str(_candidate_value(candidate, "family")),
        "direction": str(_candidate_value(candidate, "direction")),
        "decision_time_utc": pd.Timestamp(_candidate_value(candidate, "feature_time_utc")).isoformat(),
        "split": split,
        "status": status,
        "reason": reason,
    }


def label_one(
    candidate: Mapping[str, Any],
    *,
    atr_source: CompletedM5Atr,
    tick_store: VerifiedSpotTickStore,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    decision_ms = _timestamp_ms(_candidate_value(candidate, "feature_time_utc"))
    split = _split(decision_ms, config)
    if split is None:
        return _empty_label(candidate, status="INELIGIBLE", reason="OUTSIDE_SPLITS")
    family_name = str(_candidate_value(candidate, "family"))
    direction = str(_candidate_value(candidate, "direction"))
    if family_name not in config["families"] or direction not in {"LONG", "SHORT"}:
        return _empty_label(
            candidate, status="INELIGIBLE", reason="UNKNOWN_FAMILY_OR_DIRECTION", split=split
        )
    atr = atr_source.at_decision(decision_ms)
    if atr is None:
        return _empty_label(
            candidate, status="INELIGIBLE", reason="NO_COMPLETED_ATR", split=split
        )

    execution = config["execution"]
    entry_tick = tick_store.first_tick_strictly_after(
        decision_ms, int(execution["maximum_entry_delay_ms"])
    )
    if entry_tick is None:
        return _empty_label(candidate, status="INELIGIBLE", reason="NO_ENTRY_QUOTE", split=split)
    entry_ms = int(entry_tick.timestamp_ms)
    entry_bid = float(entry_tick.bid)
    entry_ask = float(entry_tick.ask)
    entry_spread = entry_ask - entry_bid
    if entry_spread < 0:
        raise SpotLabelError("Entry quote is crossed.")
    entry_price = entry_ask if direction == "LONG" else entry_bid

    family = config["families"][family_name]
    stop_distance = max(
        float(family["atr_stop_multiple"]) * atr,
        float(family["spread_stop_multiple"]) * entry_spread,
        float(family["minimum_stop_distance_usd"]),
    )
    ounces = float(execution["ounces"])
    risk_usd = stop_distance * ounces
    if risk_usd > float(execution["maximum_initial_risk_usd"]):
        return _empty_label(candidate, status="INELIGIBLE", reason="RISK_CAP", split=split)
    reward_r = float(family["reward_r"])
    if direction == "LONG":
        stop = entry_price - stop_distance
        target = entry_price + reward_r * stop_distance
    else:
        stop = entry_price + stop_distance
        target = entry_price - reward_r * stop_distance

    deadline = entry_ms + int(family["maximum_hold_minutes"]) * 60_000
    grace_end = deadline + int(execution["timeout_exit_grace_ms"])
    mfe = 0.0
    mae = 0.0
    exit_tick = None
    exit_price = None
    exit_reason = ""
    for tick in tick_store.ticks_between(entry_ms, grace_end):
        timestamp = int(tick.timestamp_ms)
        side_price = float(tick.bid) if direction == "LONG" else float(tick.ask)
        favorable = side_price - entry_price if direction == "LONG" else entry_price - side_price
        mfe = max(mfe, favorable)
        mae = max(mae, -favorable)
        if timestamp <= deadline:
            stop_hit = side_price <= stop if direction == "LONG" else side_price >= stop
            target_hit = side_price >= target if direction == "LONG" else side_price <= target
            if stop_hit or target_hit:
                exit_tick = tick
                exit_price = side_price
                exit_reason = "STOP" if stop_hit else "TARGET"
                break
        if timestamp >= deadline:
            exit_tick = tick
            exit_price = side_price
            exit_reason = "TIMEOUT"
            break
    if exit_tick is None or exit_price is None:
        return _empty_label(candidate, status="UNRESOLVED", reason="NO_EXIT_QUOTE", split=split)

    exit_ms = int(exit_tick.timestamp_ms)
    price_move = exit_price - entry_price if direction == "LONG" else entry_price - exit_price
    gross_pnl = price_move * ounces
    holding_cost = (exit_ms - entry_ms) / (24 * HOUR_MS) * float(
        execution["holding_cost_per_24h_usd"]
    )
    ticket_cost = float(execution["ticket_cost_usd"])
    baseline_net = gross_pnl - ticket_cost - holding_cost
    stress_cost = risk_usd * float(execution["stress_slippage_r"])
    stress_net = baseline_net - stress_cost
    candidate_id = str(candidate.get("candidate_id") or f"{family_name}:{decision_ms}:{direction}")
    return {
        "candidate_id": candidate_id,
        "family": family_name,
        "direction": direction,
        "decision_time_utc": _iso_ms(decision_ms),
        "split": split,
        "status": "RESOLVED",
        "reason": "",
        "entry_time_utc": _iso_ms(entry_ms),
        "exit_time_utc": _iso_ms(exit_ms),
        "entry_delay_ms": entry_ms - decision_ms,
        "entry_bid": entry_bid,
        "entry_ask": entry_ask,
        "entry_price": entry_price,
        "entry_spread": entry_spread,
        "atr_completed_m5": atr,
        "stop_distance": stop_distance,
        "planned_stop": stop,
        "planned_target": target,
        "reward_r": reward_r,
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "duration_seconds": (exit_ms - entry_ms) / 1000.0,
        "risk_usd": risk_usd,
        "gross_pnl_usd": gross_pnl,
        "ticket_cost_usd": ticket_cost,
        "holding_cost_usd": holding_cost,
        "baseline_net_pnl_usd": baseline_net,
        "stress_cost_usd": stress_cost,
        "stress_net_pnl_usd": stress_net,
        "gross_r": gross_pnl / risk_usd,
        "baseline_net_r": baseline_net / risk_usd,
        "stress_net_r": stress_net / risk_usd,
        "mfe_r": mfe / stop_distance,
        "mae_r": mae / stop_distance,
        "profitable_after_stress": int(stress_net > 0),
    }


def label_candidates(
    candidates: pd.DataFrame,
    *,
    atr_source: CompletedM5Atr,
    tick_store: VerifiedSpotTickStore,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    required = {"feature_time_utc", "family", "direction"}
    missing = sorted(required - set(candidates.columns))
    if missing:
        raise SpotLabelError(f"Candidates are missing columns: {missing}")
    key = ["feature_time_utc", "family", "direction"]
    if candidates.duplicated(key).any():
        raise SpotLabelError("Candidates contain duplicate family-time-direction keys.")
    rows = [
        label_one(row, atr_source=atr_source, tick_store=tick_store, config=config)
        for row in candidates.to_dict("records")
    ]
    return pd.DataFrame(rows)


def serializable_tick(tick: Any) -> dict[str, Any]:
    if is_dataclass(tick):
        return asdict(tick)
    return dict(tick)
