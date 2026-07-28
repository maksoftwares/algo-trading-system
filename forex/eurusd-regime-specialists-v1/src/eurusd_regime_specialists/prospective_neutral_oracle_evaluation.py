from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import load_ensemble_config
from .prospective_neutral_macro_crossasset_execution import (
    verify_neutral_ownership_record,
)
from .research import PACKAGE_ROOT, PIP, build_state_table, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_prospective_neutral_oracle_evaluation_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_ORACLE_EVALUATION_PREREG_2026_07_28.sha256.json"
)
DENSE_TARGET_R = 1.5
DENSE_HOLD_HOURS = 12
DENSE_RISK_TIERS_PIPS = (4.0, 3.0)
TARGET_TRADES_PER_DAY = 4
MINIMUM_RETAIL_SPREAD_PIPS = 0.7
ADVERSE_SLIPPAGE_PIPS_PER_SIDE = 0.1
REGIME_DEFINITIONS = {
    "JOINT_COMPRESSION": "Non-shock DXY and EURUSD joint compression",
    "USD_DOWN": "Non-compressed USD-down regime",
    "NEUTRAL": "Non-compressed neutral USD regime",
    "USD_UP": "Non-compressed USD-up regime",
    "SHOCK": "Causal cross-asset shock state",
    "MISSING_CONTEXT": "No completed causal state was available",
}


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Prospective oracle evaluation is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Prospective oracle lock mismatch: {relative}")
        checked[relative] = actual
    cfg = load_config()
    references = (
        ("execution_contract", "path", "sha256"),
        ("ownership_contract", "path", "sha256"),
        ("historical_oracle_algorithm", "path", "sha256"),
        ("classifier_contract", "path", "sha256"),
        (
            "market_source",
            "capture_reference_path",
            "capture_reference_sha256",
        ),
    )
    for section, path_key, hash_key in references:
        reference = cfg[section]
        actual = sha256_file(PACKAGE_ROOT / reference[path_key])
        if actual != reference[hash_key]:
            raise RuntimeError(f"Prospective oracle reference drift: {section}")
    return checked


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def _day(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    if timestamp != timestamp.floor("D"):
        raise ValueError("Oracle date must be UTC midnight")
    return timestamp.as_unit("ns")


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


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def oracle_capture_ready(
    oracle_date: Any,
    observed_at_utc: Any,
    *,
    minimum_capture_lag_seconds: int = 60,
) -> bool:
    day = _day(oracle_date)
    observed = _utc(observed_at_utc)
    return observed >= day + pd.Timedelta(hours=36, seconds=minimum_capture_lag_seconds)


def required_oracle_hours(oracle_date: Any) -> list[pd.Timestamp]:
    day = _day(oracle_date)
    return list(pd.date_range(day, periods=36, freq="h"))


def _normalize_m5(m5: pd.DataFrame) -> pd.DataFrame:
    frame = m5.copy()
    if "timestamp_utc" in frame.columns:
        timestamps = pd.to_datetime(frame.pop("timestamp_utc"), utc=True).dt.as_unit(
            "ns"
        )
        frame.index = pd.DatetimeIndex(timestamps, name="timestamp_utc")
    elif isinstance(frame.index, pd.DatetimeIndex):
        if frame.index.tz is None:
            raise ValueError("Oracle M5 index must be timezone-aware")
        frame.index = frame.index.tz_convert("UTC").as_unit("ns")
        frame.index.name = "timestamp_utc"
    else:
        raise ValueError("Oracle M5 requires UTC timestamps")
    required = {
        f"{side}_{field}"
        for side in ("bid", "ask")
        for field in ("open", "high", "low")
    }
    if not required.issubset(frame.columns):
        raise ValueError("Oracle M5 lacks executable bid/ask prices")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("Oracle M5 timestamps must be unique and ordered")
    values = frame[list(required)].astype(float)
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("Oracle M5 contains non-finite prices")
    return frame


def _target_before_stop_candidate(
    position: int,
    index: pd.DatetimeIndex,
    arrays: dict[str, np.ndarray],
    risk_pips: float,
    spread_floor: float,
    slippage: float,
) -> dict[str, Any] | None:
    risk = risk_pips * PIP
    target_distance = DENSE_TARGET_R * risk
    deadline = index[position] + pd.Timedelta(hours=DENSE_HOLD_HOURS)
    end = int(index.searchsorted(deadline, side="right"))
    end = min(end, len(index))
    candidates: list[dict[str, Any]] = []

    entry = (
        max(
            arrays["ask_open"][position],
            arrays["bid_open"][position] + spread_floor,
        )
        + slippage
    )
    stop = entry - risk
    target = entry + target_distance
    for cursor in range(position, end):
        if arrays["bid_low"][cursor] <= stop:
            break
        if arrays["bid_high"][cursor] >= target:
            exit_price = max(arrays["bid_open"][cursor], target) - slippage
            candidates.append(
                {
                    "exit_position": cursor,
                    "side": "LONG",
                    "entry_price": entry,
                    "stop_price": stop,
                    "target_price": target,
                    "exit_price": exit_price,
                    "r": (exit_price - entry) / risk,
                    "fixed_0p01_lot_usd": (exit_price - entry) * 1000.0,
                }
            )
            break

    entry = arrays["bid_open"][position] - slippage
    stop = entry + risk
    target = entry - target_distance
    for cursor in range(position, end):
        ask_open = max(
            arrays["ask_open"][cursor],
            arrays["bid_open"][cursor] + spread_floor,
        )
        ask_high = max(
            arrays["ask_high"][cursor],
            arrays["bid_high"][cursor] + spread_floor,
        )
        ask_low = max(
            arrays["ask_low"][cursor],
            arrays["bid_low"][cursor] + spread_floor,
        )
        if ask_high >= stop:
            break
        if ask_low <= target:
            exit_price = min(ask_open, target) + slippage
            candidates.append(
                {
                    "exit_position": cursor,
                    "side": "SHORT",
                    "entry_price": entry,
                    "stop_price": stop,
                    "target_price": target,
                    "exit_price": exit_price,
                    "r": (entry - exit_price) / risk,
                    "fixed_0p01_lot_usd": (entry - exit_price) * 1000.0,
                }
            )
            break
    if not candidates:
        return None
    chosen = min(
        candidates,
        key=lambda item: (
            item["exit_position"],
            0 if item["side"] == "LONG" else 1,
        ),
    )
    chosen["entry_position"] = position
    chosen["risk_distance"] = risk
    chosen["risk_pips"] = risk_pips
    return chosen


def assign_oracle_regimes(
    trades: pd.DataFrame,
    state: pd.DataFrame,
) -> pd.DataFrame:
    if trades.empty:
        return trades.assign(
            state_time_utc=pd.Series(dtype="datetime64[ns, UTC]"),
            matched_state_time_utc=pd.Series(dtype="datetime64[ns, UTC]"),
            direction=pd.Series(dtype=str),
            shock=pd.Series(dtype=bool),
            DXY_compressed=pd.Series(dtype=bool),
            EURUSD_compressed=pd.Series(dtype=bool),
            regime=pd.Series(dtype=str),
            regime_definition=pd.Series(dtype=str),
        )
    frame = trades.copy()
    frame["state_time_utc"] = (
        pd.to_datetime(frame["entry_time_utc"], utc=True).dt.floor("h")
        - pd.Timedelta(hours=1)
    ).dt.as_unit("ns")
    context = (
        state[
            [
                "direction",
                "shock",
                "DXY_compressed",
                "EURUSD_compressed",
            ]
        ]
        .reset_index()
        .rename(columns={"timestamp_utc": "matched_state_time_utc"})
        .sort_values("matched_state_time_utc")
    )
    context["matched_state_time_utc"] = pd.to_datetime(
        context["matched_state_time_utc"], utc=True
    ).dt.as_unit("ns")
    joined = pd.merge_asof(
        frame.sort_values("state_time_utc"),
        context,
        left_on="state_time_utc",
        right_on="matched_state_time_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    joined["regime"] = "MISSING_CONTEXT"
    valid = joined["direction"].notna()
    shock = valid & joined["shock"].astype("boolean").fillna(False)
    joined.loc[shock, "regime"] = "SHOCK"
    nonshock = valid & ~joined["shock"].astype("boolean").fillna(True)
    compressed = (
        nonshock
        & joined["DXY_compressed"].astype("boolean").fillna(False)
        & joined["EURUSD_compressed"].astype("boolean").fillna(False)
    )
    joined.loc[compressed, "regime"] = "JOINT_COMPRESSION"
    remaining = nonshock & ~compressed
    for direction in ("USD_DOWN", "NEUTRAL", "USD_UP"):
        joined.loc[remaining & joined["direction"].eq(direction), "regime"] = direction
    joined["regime_definition"] = joined["regime"].map(REGIME_DEFINITIONS)
    return joined.sort_values(["entry_time_utc", "oracle_trade_number"]).reset_index(
        drop=True
    )


def build_daily_perfect_oracle(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    oracle_date: Any,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    day = _day(oracle_date)
    frame = _normalize_m5(m5)
    index = frame.index
    positions = [
        position
        for position, timestamp in enumerate(index)
        if timestamp.floor("D") == day
    ]
    arrays = {
        column: frame[column].to_numpy(dtype=float)
        for column in (
            "bid_open",
            "bid_high",
            "bid_low",
            "ask_open",
            "ask_high",
            "ask_low",
        )
    }
    spread_floor = MINIMUM_RETAIL_SPREAD_PIPS * PIP
    slippage = ADVERSE_SLIPPAGE_PIPS_PER_SIDE * PIP
    winners: list[dict[str, Any]] = []
    selected_risk: float | None = None
    for risk_pips in DENSE_RISK_TIERS_PIPS:
        winners = []
        for position in positions:
            candidate = _target_before_stop_candidate(
                position,
                index,
                arrays,
                risk_pips,
                spread_floor,
                slippage,
            )
            if candidate is None:
                continue
            winners.append(candidate)
            if len(winners) == TARGET_TRADES_PER_DAY:
                break
        if len(winners) == TARGET_TRADES_PER_DAY:
            selected_risk = risk_pips
            break
    if len(winners) != TARGET_TRADES_PER_DAY or selected_risk is None:
        return pd.DataFrame(), {
            "status": "ORACLE_UNAVAILABLE_INSUFFICIENT_FOUR_WINNERS",
            "oracle_date": day.strftime("%Y-%m-%d"),
            "candidate_m5_bars": len(positions),
            "winner_count": len(winners),
            "risk_tier_pips": None,
        }
    records: list[dict[str, Any]] = []
    for rank, winner in enumerate(winners, start=1):
        item = dict(winner)
        entry_position = int(item.pop("entry_position"))
        exit_position = int(item.pop("exit_position"))
        records.append(
            {
                "oracle_date": day.strftime("%Y-%m-%d"),
                "oracle_trade_number": rank,
                "side": item.pop("side"),
                "entry_time_utc": index[entry_position],
                "exit_time_utc": index[exit_position],
                "exit_reason": "TARGET_KNOWN_IN_FUTURE",
                "nominal_target_r": DENSE_TARGET_R,
                "risk_tier_pips": selected_risk,
                "fallback_risk_tier": (selected_risk != DENSE_RISK_TIERS_PIPS[0]),
                **item,
            }
        )
    trades = assign_oracle_regimes(pd.DataFrame(records), state)
    return trades, {
        "status": "ORACLE_COMPLETE",
        "oracle_date": day.strftime("%Y-%m-%d"),
        "candidate_m5_bars": len(positions),
        "winner_count": len(trades),
        "risk_tier_pips": selected_risk,
        "neutral_winners": int(trades["regime"].eq("NEUTRAL").sum()),
    }


def _safe_path(root: Path, value: Any) -> Path:
    relative = Path(str(value))
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("Ownership context path escapes its root")
    root_resolved = root.resolve()
    path = (root / relative).resolve()
    if path != root_resolved and root_resolved not in path.parents:
        raise RuntimeError("Ownership context path escapes its root")
    return path


def load_next_day_context(
    ownership_root: Path,
    oracle_date: Any,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    day = _day(oracle_date)
    eligible = day + pd.Timedelta(days=1)
    manifests = sorted(
        ownership_root.glob(f"manifests/MANIFEST_{eligible:%Y-%m-%d}_*.json")
    )
    if not manifests:
        raise FileNotFoundError("Next-day ownership context is not captured")
    if len(manifests) != 1:
        raise RuntimeError("Next-day context has multiple manifests")
    manifest_path = manifests[0]
    manifest_payload = manifest_path.read_bytes()
    manifest_hash = _sha256_bytes(manifest_payload)
    if manifest_path.name != (
        f"MANIFEST_{eligible:%Y-%m-%d}_{manifest_hash[:16]}.json"
    ):
        raise RuntimeError("Next-day ownership manifest name/hash drift")
    manifest = json.loads(manifest_payload)
    if manifest.get("broker_action_allowed") is not False:
        raise RuntimeError("Next-day context broker boundary drift")
    record_reference = manifest["ownership_record"]
    record_path = _safe_path(ownership_root, record_reference["relative_path"])
    if (
        not record_path.is_file()
        or sha256_file(record_path) != record_reference["sha256"]
    ):
        raise RuntimeError("Next-day ownership record hash drift")
    record = json.loads(record_path.read_bytes())
    verify_neutral_ownership_record(record)
    if str(record["eligible_date"]) != eligible.strftime("%Y-%m-%d"):
        raise RuntimeError("Next-day ownership record date drift")
    inventory = manifest.get("source_inventory", {})
    required = {
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "DOLLARIDXUSD",
        "USTBONDTRUSD",
    }
    if set(inventory) != required:
        raise RuntimeError("Next-day context lacks five source inventories")
    bars: dict[str, pd.DataFrame] = {}
    for symbol, evidence in inventory.items():
        path = _safe_path(ownership_root, evidence["normalized_relative_path"])
        if not path.is_file() or sha256_file(path) != evidence["normalized_sha256"]:
            raise RuntimeError(f"Next-day normalized context hash drift: {symbol}")
        frame = pd.read_parquet(path)
        if not isinstance(frame.index, pd.DatetimeIndex):
            raise TypeError("Context H1 lacks a DatetimeIndex")
        if frame.index.tz is None:
            raise RuntimeError("Context H1 index is timezone-naive")
        frame.index = frame.index.tz_convert("UTC").as_unit("ns")
        bars[symbol] = frame
    classifier = load_ensemble_config()["classifier"]
    state = build_state_table(
        bars["DOLLARIDXUSD"],
        bars["USTBONDTRUSD"],
        {symbol: bars[symbol] for symbol in ("EURUSD", "GBPUSD", "USDJPY")},
        classifier,
    )
    if state.empty:
        raise RuntimeError("Next-day context produced no common state")
    return state, {
        "eligible_date": eligible,
        "ownership_observed_at_utc": _utc(manifest["ownership_observed_at_utc"]),
        "ownership_manifest_relative_path": (
            manifest_path.relative_to(ownership_root).as_posix()
        ),
        "ownership_manifest_sha256": manifest_hash,
        "ownership_record_relative_path": (
            record_path.relative_to(ownership_root).as_posix()
        ),
        "ownership_record_sha256": sha256_file(record_path),
        "ownership_evidence_sha256": str(record["ownership_evidence_sha256"]),
    }


__all__ = [
    "ADVERSE_SLIPPAGE_PIPS_PER_SIDE",
    "CONFIG_PATH",
    "DENSE_HOLD_HOURS",
    "DENSE_RISK_TIERS_PIPS",
    "DENSE_TARGET_R",
    "LOCK_PATH",
    "MINIMUM_RETAIL_SPREAD_PIPS",
    "TARGET_TRADES_PER_DAY",
    "assign_oracle_regimes",
    "build_daily_perfect_oracle",
    "load_config",
    "load_next_day_context",
    "oracle_capture_ready",
    "required_oracle_hours",
    "verify_lock",
]
