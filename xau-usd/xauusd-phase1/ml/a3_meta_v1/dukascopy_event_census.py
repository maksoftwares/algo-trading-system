from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_confirmed_event_specialists import (
    BAR_WIDTH_MS,
    _artifact,
    _iso_ms,
    _max_drawdown,
    _parse_ms,
    _sha256_file,
    _write_csv,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_event_census_v1.json")


class EventCensusError(RuntimeError):
    pass


def run_event_census(phase1_root: Path, contract_path: Path | None = None) -> Path:
    phase1_root = phase1_root.resolve()
    contract_file = (contract_path or phase1_root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    validate_contract(contract)
    storage_root = _resolve_storage_root(contract)
    source_report, frame = load_locked_source(phase1_root, storage_root, contract)
    frame = enrich_context(frame, contract)
    events = generate_events(frame, contract)
    validate_events(events)
    horizon_labels, barrier_labels = label_events(frame, events, contract)
    report = build_report(
        phase1_root=phase1_root,
        contract_file=contract_file,
        contract=contract,
        source_report=source_report,
        frame=frame,
        events=events,
        horizon_labels=horizon_labels,
        barrier_labels=barrier_labels,
    )
    outputs = {
        key: (phase1_root / value).resolve() for key, value in contract["outputs"].items()
    }
    _write_csv(outputs["events_csv"], events)
    _write_csv(outputs["horizon_labels_csv"], horizon_labels)
    _write_csv(outputs["barrier_labels_csv"], barrier_labels)
    _write_csv(outputs["policy_metrics_csv"], report.pop("_policy_metric_rows"))
    _write_csv(outputs["context_metrics_csv"], report.pop("_context_metric_rows"))
    report["artifacts"] = {
        name: _artifact(outputs[name])
        for name in (
            "events_csv",
            "horizon_labels_csv",
            "barrier_labels_csv",
            "policy_metrics_csv",
            "context_metrics_csv",
        )
    }
    outputs["report_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report_json"].write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outputs["report_markdown"].write_text(render_report(report), encoding="utf-8")
    return outputs["report_json"]


def validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_event_census_v1":
        raise ValueError("unexpected Dukascopy event-census contract")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("event census V1 is locked to XAUUSD")
    controls = contract["research_controls"]
    for key in (
        "parameter_grid_search_authorized",
        "diagnostic_context_promotion_authorized",
        "same_iteration_post_outcome_tuning_authorized",
        "claims_untouched_holdout",
    ):
        if controls.get(key):
            raise ValueError(f"forbidden event-census control: {key}")
    if not controls.get("known_program_level_history_contamination"):
        raise ValueError("historical research contamination must be disclosed")
    authorization = contract["authorization"]
    if not authorization.get("research_only"):
        raise ValueError("event census must remain research-only")
    for key in (
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if authorization.get(key):
            raise ValueError(f"forbidden event-census authorization: {key}")
    expected_families = {
        "trend_pullback_resumption_v1",
        "session_opening_drive_v1",
        "session_range_break_v1",
        "volatility_expansion_break_v1",
    }
    if {str(row["family_id"]) for row in contract["event_families"]} != expected_families:
        raise ValueError("event-census family set differs from preregistration")
    if int(contract["selection"]["maximum_family_direction_hypotheses"]) != 8:
        raise ValueError("event-census hypothesis count must remain eight")
    if contract["selection"]["hypothesis_keys"] != ["family_id", "direction"]:
        raise ValueError("only family-direction hypotheses may be promoted")
    profiles = contract["forward_labels"]["barrier_profiles"]
    if len(profiles) != 3 or any(
        not math.isclose(float(row["target_atr"]) / float(row["stop_atr"]), 1.5)
        for row in profiles
    ):
        raise ValueError("event-census barrier profile lock differs")
    boundaries = [
        _parse_ms(contract["windows"][key])
        for key in (
            "train_start_utc",
            "train_end_exclusive_utc",
            "validation_end_exclusive_utc",
            "internal_test_end_exclusive_utc",
            "exam_end_exclusive_utc",
        )
    ]
    if boundaries != sorted(set(boundaries)):
        raise ValueError("event-census windows are not strictly chronological")


def _resolve_storage_root(contract: Mapping[str, Any]) -> Path:
    env_name = str(contract["storage_environment_variable"])
    configured = os.environ.get(env_name, "").strip() or str(
        contract["default_storage_root"]
    )
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


def load_locked_source(
    phase1_root: Path, storage_root: Path, contract: Mapping[str, Any]
) -> tuple[dict[str, Any], pd.DataFrame]:
    locked = contract["source_lock"]
    report_path = (phase1_root / str(locked["report_path"])).resolve()
    feature_path = (storage_root / str(locked["feature_path"])).resolve()
    if _sha256_file(report_path) != str(locked["report_sha256"]):
        raise EventCensusError("event-census source report hash mismatch")
    if _sha256_file(feature_path) != str(locked["feature_sha256"]):
        raise EventCensusError("event-census feature hash mismatch")
    source_report = json.loads(report_path.read_text(encoding="utf-8"))
    if (
        int(source_report["feature_rows"]) != int(locked["feature_rows"])
        or str(source_report["source_digest"]) != str(locked["source_digest"])
        or str(source_report["feature_cache"]["feature_sha256"])
        != str(locked["feature_sha256"])
    ):
        raise EventCensusError("event-census report identity mismatch")
    frame = pd.read_parquet(feature_path).sort_values("timestamp_ms").reset_index(drop=True)
    if len(frame) != int(locked["feature_rows"]):
        raise EventCensusError("event-census feature row count mismatch")
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    if np.any(np.diff(timestamps) <= 0):
        raise EventCensusError("event-census feature source is non-chronological")
    return source_report, frame


def enrich_context(frame: pd.DataFrame, contract: Mapping[str, Any]) -> pd.DataFrame:
    result = frame.copy()
    context = contract["context"]
    close = result["mid_close"]
    result["ema_fast"] = close.ewm(
        span=int(context["ema_fast_bars"]), adjust=False
    ).mean()
    result["ema_slow"] = close.ewm(
        span=int(context["ema_slow_bars"]), adjust=False
    ).mean()
    lag = int(context["ema_slope_lag_bars"])
    result["ema_fast_slope_atr"] = (
        result["ema_fast"] - result["ema_fast"].shift(lag)
    ) / result["atr"]
    result["return_60m_atr"] = (close - close.shift(12)) / result["atr"]
    contiguous = result["timestamp_ms"] - result["timestamp_ms"].shift(12) == 12 * BAR_WIDTH_MS
    result.loc[~contiguous, "return_60m_atr"] = np.nan
    gap = (result["ema_fast"] - result["ema_slow"]) / result["atr"]
    threshold = float(context["trend_gap_atr"])
    result["trend_sign"] = np.select(
        [
            (gap >= threshold) & (result["ema_fast_slope_atr"] > 0),
            (gap <= -threshold) & (result["ema_fast_slope_atr"] < 0),
        ],
        [1, -1],
        default=0,
    ).astype(int)
    low_max = float(context["volatility_bins"]["LOW_MAX_EXCLUSIVE"])
    normal_max = float(context["volatility_bins"]["NORMAL_MAX_EXCLUSIVE"])
    result["volatility_bin"] = np.select(
        [result["atr_ratio"] < low_max, result["atr_ratio"] < normal_max],
        ["LOW", "NORMAL"],
        default="HIGH",
    )
    result["session_utc"] = result["hour_utc"].map(
        lambda hour: _session_name(int(hour), context["sessions_utc"])
    )
    return result.replace([np.inf, -np.inf], np.nan)


def generate_events(
    frame: pd.DataFrame, contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    families = {str(row["family_id"]): row for row in contract["event_families"]}
    events = []
    events.extend(
        _trend_pullback_events(frame, families["trend_pullback_resumption_v1"], contract)
    )
    events.extend(
        _opening_drive_events(frame, families["session_opening_drive_v1"], contract)
    )
    events.extend(
        _session_range_break_events(frame, families["session_range_break_v1"], contract)
    )
    events.extend(
        _volatility_expansion_events(
            frame, families["volatility_expansion_break_v1"], contract
        )
    )
    return sorted(
        events,
        key=lambda row: (
            int(row["decision_timestamp_ms"]),
            str(row["family_id"]),
            str(row["profile_id"]),
            str(row["direction"]),
        ),
    )


def _trend_pullback_events(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    gap = (frame["ema_fast"] - frame["ema_slow"]) / frame["atr"]
    minimum_gap = float(family["minimum_trend_gap_atr"])
    minimum_return = float(family["minimum_directional_return_60m_atr"])
    finite = _finite_mask(
        frame,
        (
            "atr",
            "atr_ratio",
            "ema_fast",
            "ema_slow",
            "ema_fast_slope_atr",
            "return_60m_atr",
            "tick_spread_last",
        ),
    )
    long_mask = (
        finite
        & (gap >= minimum_gap)
        & (frame["ema_fast_slope_atr"] > 0)
        & (frame["return_60m_atr"] >= minimum_return)
        & (frame["mid_low"] <= frame["ema_fast"])
        & (frame["mid_close"] >= frame["ema_fast"])
    )
    short_mask = (
        finite
        & (gap <= -minimum_gap)
        & (frame["ema_fast_slope_atr"] < 0)
        & (frame["return_60m_atr"] <= -minimum_return)
        & (frame["mid_high"] >= frame["ema_fast"])
        & (frame["mid_close"] <= frame["ema_fast"])
    )
    return _events_from_direction_masks(
        frame,
        family,
        "FIXED",
        long_mask,
        short_mask,
        int(family["cooldown_minutes_per_direction"]),
        contract,
    )


def _opening_drive_events(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    events = []
    opening_bars = int(family["opening_bars"])
    for profile in family["profiles"]:
        start_hour = int(profile["start_hour_utc"])
        eligible = frame[frame["hour_utc"] == start_hour]
        for date, day in eligible.groupby("date_utc", sort=False):
            start_ms = int(
                pd.Timestamp(f"{date}T{start_hour:02d}:00:00Z").timestamp() * 1000
            )
            opening = day[
                (day["timestamp_ms"] >= start_ms)
                & (day["timestamp_ms"] < start_ms + opening_bars * BAR_WIDTH_MS)
            ]
            if len(opening) != opening_bars or not _contiguous(opening):
                continue
            last = opening.iloc[-1]
            if not _finite_row(last, ("atr", "atr_ratio", "tick_spread_last")):
                continue
            start_price = float(opening.iloc[0]["mid_open"])
            drive = float(last["mid_close"]) - start_price
            path = [start_price, *opening["mid_close"].astype(float).tolist()]
            distance = float(np.abs(np.diff(path)).sum())
            efficiency = abs(drive) / distance if distance > 0 else 0.0
            if (
                abs(drive) < float(family["minimum_drive_atr"]) * float(last["atr"])
                or efficiency < float(family["minimum_drive_efficiency"])
                or float(opening["quote_intensity_ratio"].mean())
                < float(family["minimum_mean_quote_intensity_ratio"])
            ):
                continue
            events.append(
                _make_event(
                    frame=frame,
                    signal_index=int(last.name),
                    family=family,
                    profile_id=str(profile["profile_id"]),
                    direction="LONG" if drive > 0 else "SHORT",
                    reference_level=start_price,
                    contract=contract,
                )
            )
    return [row for row in events if row is not None]


def _session_range_break_events(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    events = []
    for profile in family["profiles"]:
        reference = frame[
            (frame["hour_utc"] >= int(profile["reference_start_hour_utc"]))
            & (frame["hour_utc"] < int(profile["reference_end_hour_utc"]))
        ]
        bounds = {}
        for date, part in reference.groupby("date_utc", sort=False):
            if len(part) >= int(family["minimum_reference_bars"]):
                bounds[str(date)] = (
                    float(part["mid_high"].max()),
                    float(part["mid_low"].min()),
                )
        consumed: set[tuple[str, str]] = set()
        decisions = frame[
            (frame["hour_utc"] >= int(profile["decision_start_hour_utc"]))
            & (frame["hour_utc"] < int(profile["decision_end_hour_utc"]))
        ]
        for index, row in decisions.iterrows():
            boundary = bounds.get(str(row["date_utc"]))
            if boundary is None or not _finite_row(
                row, ("atr", "atr_ratio", "tick_imbalance_5m", "tick_spread_last")
            ):
                continue
            reference_high, reference_low = boundary
            direction = None
            level = 0.0
            if (
                float(row["mid_close"])
                >= reference_high
                + float(family["minimum_close_outside_atr"]) * float(row["atr"])
                and float(row["body_fraction"]) >= float(family["minimum_body_fraction"])
                and float(row["tick_imbalance_5m"])
                >= float(family["minimum_directional_tick_imbalance_5m"])
            ):
                direction, level = "LONG", reference_high
            elif (
                float(row["mid_close"])
                <= reference_low
                - float(family["minimum_close_outside_atr"]) * float(row["atr"])
                and float(row["body_fraction"]) >= float(family["minimum_body_fraction"])
                and float(row["tick_imbalance_5m"])
                <= -float(family["minimum_directional_tick_imbalance_5m"])
            ):
                direction, level = "SHORT", reference_low
            if direction is None:
                continue
            key = (str(row["date_utc"]), direction)
            if key in consumed:
                continue
            event = _make_event(
                frame=frame,
                signal_index=int(index),
                family=family,
                profile_id=str(profile["profile_id"]),
                direction=direction,
                reference_level=level,
                contract=contract,
            )
            if event is not None:
                events.append(event)
                consumed.add(key)
    return events


def _volatility_expansion_events(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    lookback = int(family["compression_lookback_bars"])
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    gap_ok = pd.Series(np.r_[False, np.diff(timestamps) == BAR_WIDTH_MS])
    contiguous = (
        gap_ok.rolling(lookback - 1, min_periods=lookback - 1).sum().shift(1)
        == lookback - 1
    )
    high = frame["mid_high"].shift(1).rolling(lookback).max()
    low = frame["mid_low"].shift(1).rolling(lookback).min()
    finite = _finite_mask(
        frame, ("atr", "atr_ratio", "quote_intensity_ratio", "tick_spread_last")
    )
    common = (
        finite
        & contiguous
        & gap_ok
        & ((high - low) <= float(family["maximum_prior_range_atr"]) * frame["atr"])
        & (frame["atr_ratio"] <= float(family["maximum_atr_ratio"]))
        & (frame["body_fraction"] >= float(family["minimum_body_fraction"]))
        & (
            frame["quote_intensity_ratio"]
            >= float(family["minimum_quote_intensity_ratio"])
        )
    )
    long_mask = common & (
        frame["mid_close"]
        >= high + float(family["minimum_close_outside_atr"]) * frame["atr"]
    )
    short_mask = common & (
        frame["mid_close"]
        <= low - float(family["minimum_close_outside_atr"]) * frame["atr"]
    )
    return _events_from_direction_masks(
        frame,
        family,
        "FIXED",
        long_mask,
        short_mask,
        int(family["cooldown_minutes_per_direction"]),
        contract,
        long_reference=high,
        short_reference=low,
    )


def _events_from_direction_masks(
    frame: pd.DataFrame,
    family: Mapping[str, Any],
    profile_id: str,
    long_mask: pd.Series,
    short_mask: pd.Series,
    cooldown_minutes: int,
    contract: Mapping[str, Any],
    *,
    long_reference: pd.Series | None = None,
    short_reference: pd.Series | None = None,
) -> list[dict[str, Any]]:
    rows = []
    for direction, mask, reference in (
        ("LONG", long_mask, long_reference),
        ("SHORT", short_mask, short_reference),
    ):
        last_decision = -10**18
        for index in np.flatnonzero(mask.to_numpy(dtype=bool)):
            decision = int(frame.iloc[index]["timestamp_ms"]) + BAR_WIDTH_MS
            if decision - last_decision < cooldown_minutes * 60_000:
                continue
            event = _make_event(
                frame=frame,
                signal_index=int(index),
                family=family,
                profile_id=profile_id,
                direction=direction,
                reference_level=float(reference.iloc[index])
                if reference is not None
                else float(frame.iloc[index]["ema_fast"]),
                contract=contract,
            )
            if event is not None:
                rows.append(event)
                last_decision = decision
    return rows


def _make_event(
    *,
    frame: pd.DataFrame,
    signal_index: int,
    family: Mapping[str, Any],
    profile_id: str,
    direction: str,
    reference_level: float,
    contract: Mapping[str, Any],
) -> dict[str, Any] | None:
    row = frame.iloc[signal_index]
    decision_ms = int(row["timestamp_ms"]) + BAR_WIDTH_MS
    split = _split(decision_ms, contract)
    if split is None:
        return None
    sign = 1 if direction == "LONG" else -1
    trend_sign = int(row["trend_sign"])
    alignment = "NEUTRAL" if trend_sign == 0 else "ALIGNED" if trend_sign == sign else "COUNTER"
    identity = f"{family['family_id']}|{profile_id}|{decision_ms}|{direction}"
    return {
        "event_id": hashlib.sha256(identity.encode("ascii")).hexdigest(),
        "family_id": str(family["family_id"]),
        "mechanism": str(family["mechanism"]),
        "profile_id": profile_id,
        "symbol": str(contract["symbol"]),
        "split": split,
        "direction": direction,
        "signal_index": signal_index,
        "signal_bar_start_utc": _iso_ms(int(row["timestamp_ms"])),
        "decision_timestamp_ms": decision_ms,
        "decision_time_utc": _iso_ms(decision_ms),
        "session_utc": str(row["session_utc"]),
        "volatility_bin": str(row["volatility_bin"]),
        "trend_alignment": alignment,
        "atr": float(row["atr"]),
        "atr_ratio": float(row["atr_ratio"]),
        "reference_level": reference_level,
        "signal_open": float(row["mid_open"]),
        "signal_high": float(row["mid_high"]),
        "signal_low": float(row["mid_low"]),
        "signal_close": float(row["mid_close"]),
        "body_fraction": float(row["body_fraction"]),
        "tick_imbalance_5m": float(row["tick_imbalance_5m"]),
        "quote_intensity_ratio": float(row["quote_intensity_ratio"]),
    }


def validate_events(events: Sequence[Mapping[str, Any]]) -> None:
    ids = [str(row["event_id"]) for row in events]
    keys = [
        (
            str(row["family_id"]),
            str(row["profile_id"]),
            int(row["decision_timestamp_ms"]),
            str(row["direction"]),
        )
        for row in events
    ]
    if len(ids) != len(set(ids)):
        raise EventCensusError("duplicate event-census IDs")
    if len(keys) != len(set(keys)):
        raise EventCensusError("duplicate event-census keys")
    if list(events) != sorted(
        events,
        key=lambda row: (
            int(row["decision_timestamp_ms"]),
            str(row["family_id"]),
            str(row["profile_id"]),
            str(row["direction"]),
        ),
    ):
        raise EventCensusError("event census is non-chronological")


def label_events(
    frame: pd.DataFrame,
    events: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    horizons = []
    barriers = []
    for event in events:
        entry_index = int(event["signal_index"]) + 1
        entry = _entry(event, frame, entry_index, contract)
        if entry is None:
            reason = _entry_failure_reason(event, frame, entry_index, contract)
            for minutes in contract["forward_labels"]["horizons_minutes"]:
                horizons.append(_empty_horizon(event, int(minutes), reason))
            for profile in contract["forward_labels"]["barrier_profiles"]:
                barriers.append(_empty_barrier(event, str(profile["profile_id"]), reason))
            continue
        for minutes in contract["forward_labels"]["horizons_minutes"]:
            horizons.append(
                _horizon_label(event, frame, entry_index, entry, int(minutes), contract)
            )
        for profile in contract["forward_labels"]["barrier_profiles"]:
            barriers.append(
                _barrier_label(event, frame, entry_index, entry, profile, contract)
            )
    return horizons, barriers


def _entry(
    event: Mapping[str, Any],
    frame: pd.DataFrame,
    entry_index: int,
    contract: Mapping[str, Any],
) -> dict[str, float] | None:
    if entry_index >= len(frame):
        return None
    row = frame.iloc[entry_index]
    if int(row["timestamp_ms"]) != int(event["decision_timestamp_ms"]):
        return None
    atr = float(event["atr"])
    if not math.isfinite(atr) or atr <= 0:
        return None
    bid = float(row["bid_open"])
    ask = float(row["ask_open"])
    spread_atr = (ask - bid) / atr
    if spread_atr > float(contract["entry"]["maximum_entry_spread_atr"]):
        return None
    return {
        "bid": bid,
        "ask": ask,
        "price": ask if event["direction"] == "LONG" else bid,
        "spread": ask - bid,
        "spread_atr": spread_atr,
    }


def _entry_failure_reason(
    event: Mapping[str, Any],
    frame: pd.DataFrame,
    entry_index: int,
    contract: Mapping[str, Any],
) -> str:
    if entry_index >= len(frame):
        return "NEXT_BAR_UNAVAILABLE"
    row = frame.iloc[entry_index]
    if int(row["timestamp_ms"]) != int(event["decision_timestamp_ms"]):
        return "NEXT_BAR_NOT_CONTIGUOUS"
    atr = float(event["atr"])
    if not math.isfinite(atr) or atr <= 0:
        return "INVALID_ATR"
    spread_atr = (float(row["ask_open"]) - float(row["bid_open"])) / atr
    if spread_atr > float(contract["entry"]["maximum_entry_spread_atr"]):
        return "ENTRY_SPREAD_ATR"
    return "INVALID_ENTRY"


def _horizon_label(
    event: Mapping[str, Any],
    frame: pd.DataFrame,
    entry_index: int,
    entry: Mapping[str, float],
    minutes: int,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    bars = minutes // 5
    end_index = entry_index + bars - 1
    if end_index >= len(frame) or int(frame.iloc[end_index]["timestamp_ms"]) != int(
        event["decision_timestamp_ms"]
    ) + (bars - 1) * BAR_WIDTH_MS:
        return _empty_horizon(event, minutes, "HORIZON_UNAVAILABLE")
    path = frame.iloc[entry_index : end_index + 1]
    direction = str(event["direction"])
    entry_price = float(entry["price"])
    if direction == "LONG":
        exit_price = float(path.iloc[-1]["bid_close"])
        move = exit_price - entry_price
        mfe = float(path["bid_high"].max()) - entry_price
        mae = entry_price - float(path["bid_low"].min())
    else:
        exit_price = float(path.iloc[-1]["ask_close"])
        move = entry_price - exit_price
        mfe = entry_price - float(path["ask_low"].min())
        mae = float(path["ask_high"].max()) - entry_price
    atr = float(event["atr"])
    stress_price = _stress_price(minutes, contract)
    return {
        **_label_identity(event),
        "horizon_minutes": minutes,
        "status": "RESOLVED",
        "entry_time_utc": _iso_ms(int(event["decision_timestamp_ms"])),
        "exit_time_utc": _iso_ms(
            int(frame.iloc[end_index]["timestamp_ms"]) + BAR_WIDTH_MS
        ),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "entry_spread": float(entry["spread"]),
        "entry_spread_atr": float(entry["spread_atr"]),
        "gross_return_atr": move / atr,
        "stress_return_atr": (move - stress_price) / atr,
        "mfe_atr": max(0.0, mfe / atr),
        "mae_atr": max(0.0, mae / atr),
        "exit_reason": "HORIZON",
    }


def _barrier_label(
    event: Mapping[str, Any],
    frame: pd.DataFrame,
    entry_index: int,
    entry: Mapping[str, float],
    profile: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    horizon_minutes = int(profile["maximum_horizon_minutes"])
    bars = horizon_minutes // 5
    end_index = entry_index + bars - 1
    profile_id = str(profile["profile_id"])
    if end_index >= len(frame) or int(frame.iloc[end_index]["timestamp_ms"]) != int(
        event["decision_timestamp_ms"]
    ) + (bars - 1) * BAR_WIDTH_MS:
        return _empty_barrier(event, profile_id, "HORIZON_UNAVAILABLE")
    atr = float(event["atr"])
    stop_distance = float(profile["stop_atr"]) * atr
    target_distance = float(profile["target_atr"]) * atr
    quantity = float(contract["entry"]["lot_size"]) * float(
        contract["entry"]["contract_size_ounces_per_lot"]
    )
    if stop_distance * quantity > float(contract["entry"]["maximum_initial_risk_usd"]):
        return _empty_barrier(event, profile_id, "INITIAL_RISK_USD")
    direction = str(event["direction"])
    entry_price = float(entry["price"])
    stop = entry_price - stop_distance if direction == "LONG" else entry_price + stop_distance
    target = entry_price + target_distance if direction == "LONG" else entry_price - target_distance
    exit_index = end_index
    exit_price = None
    exit_reason = "TIMEOUT"
    for index in range(entry_index, end_index + 1):
        row = frame.iloc[index]
        if direction == "LONG":
            if float(row["bid_open"]) <= stop:
                exit_index, exit_price, exit_reason = (
                    index,
                    float(row["bid_open"]),
                    "STOP",
                )
                break
            if float(row["bid_open"]) >= target:
                exit_index, exit_price, exit_reason = index, target, "TARGET"
                break
            if float(row["bid_low"]) <= stop:
                exit_index, exit_price, exit_reason = index, stop, "STOP"
                break
            if float(row["bid_high"]) >= target:
                exit_index, exit_price, exit_reason = index, target, "TARGET"
                break
        else:
            if float(row["ask_open"]) >= stop:
                exit_index, exit_price, exit_reason = (
                    index,
                    float(row["ask_open"]),
                    "STOP",
                )
                break
            if float(row["ask_open"]) <= target:
                exit_index, exit_price, exit_reason = index, target, "TARGET"
                break
            if float(row["ask_high"]) >= stop:
                exit_index, exit_price, exit_reason = index, stop, "STOP"
                break
            if float(row["ask_low"]) <= target:
                exit_index, exit_price, exit_reason = index, target, "TARGET"
                break
    if exit_price is None:
        row = frame.iloc[exit_index]
        exit_price = float(row["bid_close"] if direction == "LONG" else row["ask_close"])
    move = exit_price - entry_price if direction == "LONG" else entry_price - exit_price
    duration_minutes = (exit_index - entry_index + 1) * 5
    gross_pnl = move * quantity
    stress_pnl = gross_pnl - _stress_price(duration_minutes, contract) * quantity
    risk_usd = stop_distance * quantity
    return {
        **_label_identity(event),
        "barrier_profile_id": profile_id,
        "status": "RESOLVED",
        "entry_time_utc": _iso_ms(int(event["decision_timestamp_ms"])),
        "exit_time_utc": _iso_ms(
            int(frame.iloc[exit_index]["timestamp_ms"]) + BAR_WIDTH_MS
        ),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "entry_spread": float(entry["spread"]),
        "entry_spread_atr": float(entry["spread_atr"]),
        "stop_distance": stop_distance,
        "target_distance": target_distance,
        "initial_risk_usd": risk_usd,
        "duration_minutes": duration_minutes,
        "exit_reason": exit_reason,
        "gross_pnl_usd": gross_pnl,
        "stress_net_pnl_usd": stress_pnl,
        "gross_r": gross_pnl / risk_usd,
        "stress_net_r": stress_pnl / risk_usd,
    }


def _empty_horizon(
    event: Mapping[str, Any], minutes: int, reason: str
) -> dict[str, Any]:
    return {
        **_label_identity(event),
        "horizon_minutes": minutes,
        "status": "UNRESOLVED" if "UNAVAILABLE" in reason else "INELIGIBLE",
        "entry_time_utc": "",
        "exit_time_utc": "",
        "entry_price": None,
        "exit_price": None,
        "entry_spread": None,
        "entry_spread_atr": None,
        "gross_return_atr": None,
        "stress_return_atr": None,
        "mfe_atr": None,
        "mae_atr": None,
        "exit_reason": reason,
    }


def _empty_barrier(
    event: Mapping[str, Any], profile_id: str, reason: str
) -> dict[str, Any]:
    return {
        **_label_identity(event),
        "barrier_profile_id": profile_id,
        "status": "UNRESOLVED" if "UNAVAILABLE" in reason else "INELIGIBLE",
        "entry_time_utc": "",
        "exit_time_utc": "",
        "entry_price": None,
        "exit_price": None,
        "entry_spread": None,
        "entry_spread_atr": None,
        "stop_distance": None,
        "target_distance": None,
        "initial_risk_usd": None,
        "duration_minutes": None,
        "exit_reason": reason,
        "gross_pnl_usd": None,
        "stress_net_pnl_usd": None,
        "gross_r": None,
        "stress_net_r": None,
    }


def _label_identity(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: event[key]
        for key in (
            "event_id",
            "family_id",
            "profile_id",
            "split",
            "direction",
            "decision_time_utc",
            "session_utc",
            "volatility_bin",
            "trend_alignment",
            "atr",
        )
    }


def _stress_price(minutes: int, contract: Mapping[str, Any]) -> float:
    labels = contract["forward_labels"]
    quantity = float(contract["entry"]["lot_size"]) * float(
        contract["entry"]["contract_size_ounces_per_lot"]
    )
    return float(labels["extra_execution_cost_usd"]) / quantity + (
        minutes / (24.0 * 60.0)
    ) * float(labels["holding_cost_per_24h_usd"]) / quantity


def build_report(
    *,
    phase1_root: Path,
    contract_file: Path,
    contract: Mapping[str, Any],
    source_report: Mapping[str, Any],
    frame: pd.DataFrame,
    events: Sequence[Mapping[str, Any]],
    horizon_labels: Sequence[Mapping[str, Any]],
    barrier_labels: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    resolved_barriers = [row for row in barrier_labels if row["status"] == "RESOLVED"]
    source_days = _source_days(frame, contract)
    family_ids = [str(row["family_id"]) for row in contract["event_families"]]
    profile_ids = [
        str(row["profile_id"])
        for row in contract["forward_labels"]["barrier_profiles"]
    ]
    policy_rows = []
    metrics_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for family in family_ids:
        for direction in ("LONG", "SHORT"):
            for profile in profile_ids:
                for segment in ("train", "validation", "internal_test", "exam"):
                    rows = [
                        row
                        for row in resolved_barriers
                        if row["family_id"] == family
                        and row["direction"] == direction
                        and row["barrier_profile_id"] == profile
                        and row["split"] == segment
                    ]
                    metrics = policy_metrics(
                        rows,
                        source_days[segment],
                        bootstrap_samples=int(
                            contract["selection"]["calendar_month_bootstrap_samples"]
                        )
                        if segment == "train"
                        else 0,
                        bootstrap_seed=_bootstrap_seed(contract, family, direction, profile),
                    )
                    metrics_by_key[(family, direction, profile, segment)] = metrics
                    policy_rows.append(
                        {
                            "family_id": family,
                            "direction": direction,
                            "barrier_profile_id": profile,
                            "segment": segment,
                            **metrics,
                        }
                    )
    hypotheses = {}
    train_survivors = []
    validation_survivors = []
    internal_survivors = []
    exam_survivors = []
    for family in family_ids:
        for direction in ("LONG", "SHORT"):
            name = f"{family}:{direction}"
            train_candidates = []
            train_gates_by_profile = {}
            for profile in profile_ids:
                metrics = metrics_by_key[(family, direction, profile, "train")]
                gates = policy_gates(
                    metrics, contract["selection"]["family_direction_train_gates"]
                )
                train_gates_by_profile[profile] = gates
                if all(gates.values()):
                    train_candidates.append(profile)
            selected = _select_train_profile(
                train_candidates, metrics_by_key, family, direction
            )
            result: dict[str, Any] = {
                "selected_barrier_profile_id": selected,
                "train_profile_gates": train_gates_by_profile,
            }
            opened = selected is not None
            if opened:
                train_survivors.append(name)
            for segment, gate_key in (
                ("validation", "validation_gates"),
                ("internal_test", "internal_test_gates"),
                ("exam", "exam_gates"),
            ):
                metrics = (
                    metrics_by_key[(family, direction, selected, segment)]
                    if selected is not None
                    else policy_metrics([], source_days[segment])
                )
                gates = policy_gates(metrics, contract["selection"][gate_key])
                passed = opened and all(gates.values())
                result[segment] = {
                    "opened_for_decision": opened,
                    "metrics": metrics,
                    "gates": gates,
                    "passed": passed,
                }
                if passed and segment == "validation":
                    validation_survivors.append(name)
                elif passed and segment == "internal_test":
                    internal_survivors.append(name)
                elif passed and segment == "exam":
                    exam_survivors.append(name)
                opened = passed
            hypotheses[name] = result
    context_rows = context_metrics(resolved_barriers, source_days)
    resolved_event_ids = {row["event_id"] for row in resolved_barriers}
    labeled_share = _labeled_event_share(barrier_labels, len(events))
    resolved_event_share = len(resolved_event_ids) / len(events) if events else 0.0
    quality = contract["quality_gates"]
    quality_gates = {
        "feature_rows_equal_source_lock": len(frame)
        == int(contract["source_lock"]["feature_rows"]),
        "feature_hash_equal_source_lock": str(
            source_report["feature_cache"]["feature_sha256"]
        )
        == str(contract["source_lock"]["feature_sha256"]),
        "labeled_event_share_ge_minimum": labeled_share
        >= float(quality["minimum_labeled_event_share"]),
        "event_ids_unique": len({row["event_id"] for row in events}) == len(events),
        "event_keys_unique": len(
            {
                (
                    row["family_id"],
                    row["profile_id"],
                    row["decision_timestamp_ms"],
                    row["direction"],
                )
                for row in events
            }
        )
        == len(events),
        "events_chronological": list(events)
        == sorted(
            events,
            key=lambda row: (
                row["decision_timestamp_ms"],
                row["family_id"],
                row["profile_id"],
                row["direction"],
            ),
        ),
    }
    classification = _classification(
        quality_gates,
        train_survivors,
        validation_survivors,
        internal_survivors,
        exam_survivors,
    )
    return {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "source_report_sha256": str(contract["source_lock"]["report_sha256"]),
        "feature_sha256": str(contract["source_lock"]["feature_sha256"]),
        "feature_rows": len(frame),
        "source_days": source_days,
        "event_count": len(events),
        "event_counts_by_family_direction": dict(
            Counter(f"{row['family_id']}:{row['direction']}" for row in events)
        ),
        "horizon_label_status_counts": dict(Counter(row["status"] for row in horizon_labels)),
        "barrier_label_status_counts": dict(Counter(row["status"] for row in barrier_labels)),
        "labeled_event_share": labeled_share,
        "resolved_event_share": resolved_event_share,
        "quality_gates": quality_gates,
        "hypotheses": hypotheses,
        "stage_survivors": {
            "train": train_survivors,
            "validation": validation_survivors,
            "internal_test": internal_survivors,
            "exam": exam_survivors,
        },
        "diagnostic_context_promotion_authorized": False,
        "authorization": {
            **dict(contract["authorization"]),
            "specialist_hypothesis_candidates": exam_survivors,
            "demo_or_live_authorized": False,
        },
        "limitations": [
            "Barrier outcomes are conservative M5 screens and require exact-tick replay.",
            "Diagnostic context cells cannot be promoted under V1.",
            "All retrospective periods have known program-level research contamination.",
        ],
        "_policy_metric_rows": policy_rows,
        "_context_metric_rows": context_rows,
    }


def policy_metrics(
    rows: Sequence[Mapping[str, Any]],
    source_days: int,
    *,
    bootstrap_samples: int = 0,
    bootstrap_seed: int = 0,
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (str(row["exit_time_utc"]), str(row["event_id"])))
    returns = [float(row["stress_net_r"]) for row in ordered]
    pnl = [float(row["stress_net_pnl_usd"]) for row in ordered]
    gains = sum(value for value in returns if value > 0)
    losses = -sum(value for value in returns if value < 0)
    months: dict[str, list[float]] = defaultdict(list)
    for row in ordered:
        months[str(row["exit_time_utc"])[:7]].append(float(row["stress_net_r"]))
    month_net = [sum(values) for values in months.values()]
    positive = sum(value > 0 for value in month_net)
    top_five = sorted((value for value in returns if value > 0), reverse=True)[:5]
    top_ten = sorted((value for value in returns if value > 0), reverse=True)[:10]
    bootstrap_p025 = None
    if bootstrap_samples > 0 and months:
        rng = np.random.default_rng(bootstrap_seed)
        month_values = list(months.values())
        means = []
        for _ in range(bootstrap_samples):
            selected = rng.integers(0, len(month_values), len(month_values))
            sample = [value for index in selected for value in month_values[int(index)]]
            means.append(float(np.mean(sample)))
        bootstrap_p025 = float(np.quantile(means, 0.025))
    return {
        "events": len(ordered),
        "wins": sum(value > 0 for value in returns),
        "win_rate_pct": 100.0 * sum(value > 0 for value in returns) / len(returns)
        if returns
        else 0.0,
        "stress_net_usd": sum(pnl),
        "stress_net_r": sum(returns),
        "stress_profit_factor": gains / losses if losses > 0 else None,
        "average_stress_r": float(np.mean(returns)) if returns else 0.0,
        "max_closed_drawdown_r": _max_drawdown(np.cumsum(returns)),
        "source_days": source_days,
        "events_per_source_day": len(ordered) / source_days if source_days else 0.0,
        "active_exit_months": len(months),
        "positive_exit_month_share": positive / len(months) if months else 0.0,
        "top_five_winners_removed_net_r": sum(returns) - sum(top_five),
        "top_ten_winners_removed_net_r": sum(returns) - sum(top_ten),
        "bootstrap_mean_stress_r_p025": bootstrap_p025,
    }


def _labeled_event_share(
    barrier_labels: Sequence[Mapping[str, Any]], event_count: int
) -> float:
    if event_count == 0:
        return 0.0
    labeled_ids = {
        str(row["event_id"])
        for row in barrier_labels
        if str(row["status"]) != "UNRESOLVED"
    }
    return len(labeled_ids) / event_count


def policy_gates(
    metrics: Mapping[str, Any], configured: Mapping[str, Any]
) -> dict[str, bool]:
    pf = metrics["stress_profit_factor"]
    gates = {
        "events_ge_minimum": int(metrics["events"]) >= int(configured["minimum_events"]),
        "pf_ge_minimum": pf is not None
        and float(pf) >= float(configured["minimum_stress_profit_factor"]),
        "average_r_ge_minimum": float(metrics["average_stress_r"])
        >= float(configured["minimum_average_stress_r"]),
        "positive_month_share_ge_minimum": float(metrics["positive_exit_month_share"])
        >= float(configured["minimum_positive_exit_month_share"]),
        "drawdown_r_lte_maximum": float(metrics["max_closed_drawdown_r"])
        <= float(configured["maximum_closed_drawdown_r"]),
    }
    if "minimum_events_per_source_day" in configured:
        gates["events_per_source_day_ge_minimum"] = float(
            metrics["events_per_source_day"]
        ) >= float(configured["minimum_events_per_source_day"])
    if configured.get("require_top_ten_winners_removed_net_positive"):
        gates["top_ten_winners_removed_positive"] = float(
            metrics["top_ten_winners_removed_net_r"]
        ) > 0
    if configured.get("require_top_five_winners_removed_net_positive"):
        gates["top_five_winners_removed_positive"] = float(
            metrics["top_five_winners_removed_net_r"]
        ) > 0
    if configured.get("require_bootstrap_mean_stress_r_p025_above_zero"):
        value = metrics["bootstrap_mean_stress_r_p025"]
        gates["bootstrap_p025_above_zero"] = value is not None and float(value) > 0
    return gates


def _select_train_profile(
    profiles: Sequence[str],
    metrics: Mapping[tuple[str, str, str, str], Mapping[str, Any]],
    family: str,
    direction: str,
) -> str | None:
    if not profiles:
        return None
    return sorted(
        profiles,
        key=lambda profile: (
            -float(
                metrics[(family, direction, profile, "train")][
                    "bootstrap_mean_stress_r_p025"
                ]
            ),
            -float(
                metrics[(family, direction, profile, "train")][
                    "stress_profit_factor"
                ]
            ),
            profile,
        ),
    )[0]


def context_metrics(
    rows: Sequence[Mapping[str, Any]], source_days: Mapping[str, int]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["family_id"]),
            str(row["direction"]),
            str(row["barrier_profile_id"]),
            str(row["split"]),
            str(row["profile_id"]),
            str(row["session_utc"]),
            str(row["volatility_bin"]),
            str(row["trend_alignment"]),
        )
        grouped[key].append(row)
    output = []
    for key in sorted(grouped):
        family, direction, barrier, segment, profile, session, volatility, alignment = key
        output.append(
            {
                "family_id": family,
                "direction": direction,
                "barrier_profile_id": barrier,
                "segment": segment,
                "profile_id": profile,
                "session_utc": session,
                "volatility_bin": volatility,
                "trend_alignment": alignment,
                **policy_metrics(grouped[key], source_days[segment]),
            }
        )
    return output


def _classification(
    quality: Mapping[str, bool],
    train: Sequence[str],
    validation: Sequence[str],
    internal: Sequence[str],
    exam: Sequence[str],
) -> str:
    if not all(quality.values()):
        return "EVENT_CENSUS_INVALID"
    if not train:
        return "EVENT_CENSUS_NO_TRAIN_SURVIVOR"
    if not validation:
        return "EVENT_CENSUS_NO_VALIDATION_SURVIVOR"
    if not internal:
        return "EVENT_CENSUS_NO_INTERNAL_TEST_SURVIVOR"
    if not exam:
        return "EVENT_CENSUS_NO_EXAM_SURVIVOR"
    return "EVENT_CENSUS_SPECIALIST_HYPOTHESIS_CANDIDATE"


def _source_days(frame: pd.DataFrame, contract: Mapping[str, Any]) -> dict[str, int]:
    result = {}
    for segment in ("train", "validation", "internal_test", "exam"):
        start, end = _segment_bounds(segment, contract)
        selected = frame[
            (frame["timestamp_ms"] >= start) & (frame["timestamp_ms"] < end)
        ]
        result[segment] = int(selected["date_utc"].nunique())
    return result


def _split(timestamp_ms: int, contract: Mapping[str, Any]) -> str | None:
    for segment in ("train", "validation", "internal_test", "exam"):
        start, end = _segment_bounds(segment, contract)
        if start <= timestamp_ms < end:
            return segment
    return None


def _segment_bounds(segment: str, contract: Mapping[str, Any]) -> tuple[int, int]:
    windows = contract["windows"]
    if segment == "train":
        return _parse_ms(windows["train_start_utc"]), _parse_ms(
            windows["train_end_exclusive_utc"]
        )
    if segment == "validation":
        return _parse_ms(windows["train_end_exclusive_utc"]), _parse_ms(
            windows["validation_end_exclusive_utc"]
        )
    if segment == "internal_test":
        return _parse_ms(windows["validation_end_exclusive_utc"]), _parse_ms(
            windows["internal_test_end_exclusive_utc"]
        )
    return _parse_ms(windows["internal_test_end_exclusive_utc"]), _parse_ms(
        windows["exam_end_exclusive_utc"]
    )


def _bootstrap_seed(
    contract: Mapping[str, Any], family: str, direction: str, profile: str
) -> int:
    base = int(contract["selection"]["bootstrap_seed"])
    digest = hashlib.sha256(f"{family}|{direction}|{profile}".encode("ascii")).hexdigest()
    return (base + int(digest[:8], 16)) % (2**32)


def _finite_mask(frame: pd.DataFrame, columns: Sequence[str]) -> pd.Series:
    values = frame.loc[:, columns].to_numpy(dtype=float)
    return pd.Series(np.isfinite(values).all(axis=1), index=frame.index)


def _finite_row(row: Mapping[str, Any], columns: Sequence[str]) -> bool:
    return all(math.isfinite(float(row[column])) for column in columns)


def _contiguous(frame: pd.DataFrame) -> bool:
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    return bool(len(timestamps) > 0 and np.all(np.diff(timestamps) == BAR_WIDTH_MS))


def _session_name(hour: int, sessions: Mapping[str, Sequence[int]]) -> str:
    for name, bounds in sessions.items():
        if int(bounds[0]) <= hour < int(bounds[1]):
            return str(name)
    raise EventCensusError(f"UTC hour is not covered by a declared session: {hour}")


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy Event Census V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "## Source And Quality",
        "",
        f"- Feature rows: `{payload['feature_rows']}`",
        f"- Events: `{payload['event_count']}`",
        f"- Labeled event share: `{payload['labeled_event_share'] * 100.0:.2f}%`",
    ]
    for name, passed in payload["quality_gates"].items():
        lines.append(f"- Quality `{name}`: `{passed}`")
    lines.extend(["", "## Hypotheses", ""])
    for name, result in payload["hypotheses"].items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(
            f"- Train-selected barrier: `{result['selected_barrier_profile_id']}`"
        )
        for segment in ("validation", "internal_test", "exam"):
            row = result[segment]
            metrics = row["metrics"]
            pf = metrics["stress_profit_factor"]
            pf_text = "n/a" if pf is None else f"{pf:.3f}"
            lines.append(
                f"- {segment}: opened `{row['opened_for_decision']}`, passed "
                f"`{row['passed']}`, events `{metrics['events']}`, PF `{pf_text}`, "
                f"average R `{metrics['average_stress_r']:.4f}`"
            )
        lines.append("")
    lines.extend(
        [
            "## Decision Boundary",
            "",
            f"- Exam hypothesis candidates: `{payload['stage_survivors']['exam']}`",
            "- Diagnostic context promotion: `false`",
            "- Demo or live authorization: `false`",
            "",
        ]
    )
    return "\n".join(lines)
