from __future__ import annotations

import hashlib
import json
import math
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_confirmed_event_specialists import (
    BAR_WIDTH_MS,
    _artifact,
    _iso_ms,
    _parse_ms,
    _sha256_file,
    _write_csv,
)
from ml.a3_meta_v1.dukascopy_event_census import policy_gates, policy_metrics


DEFAULT_CONTRACT = Path("config/ml/a3_ml_macro_regime_event_census_v1.json")
H1_WIDTH_MS = 60 * 60 * 1000
DAY_MS = 24 * H1_WIDTH_MS


class MacroRegimeEventCensusError(RuntimeError):
    pass


def run_macro_regime_event_census(
    phase1_root: Path, contract_path: Path | None = None
) -> Path:
    phase1_root = phase1_root.resolve()
    contract_file = (contract_path or phase1_root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    validate_contract(contract)
    m5 = load_locked_dukascopy_source(contract)
    broker_report = load_locked_broker_cost(phase1_root, contract)
    macro = load_locked_macro_source(contract)
    h1 = aggregate_h1(m5, contract)
    h1 = attach_causal_macro(h1, macro, contract)
    events = generate_events(h1, contract)
    validate_events(events)
    labels = label_events(m5, events, contract)
    report = build_report(
        phase1_root=phase1_root,
        contract_file=contract_file,
        contract=contract,
        broker_report=broker_report,
        h1=h1,
        events=events,
        labels=labels,
    )
    outputs = {
        key: (phase1_root / value).resolve() for key, value in contract["outputs"].items()
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    h1.to_csv(outputs["h1_features_csv"], index=False)
    _write_csv(outputs["events_csv"], events)
    _write_csv(outputs["labels_csv"], labels)
    _write_csv(outputs["metrics_csv"], report.pop("_metric_rows"))
    report["artifacts"] = {
        key: _artifact(outputs[key])
        for key in ("h1_features_csv", "events_csv", "labels_csv", "metrics_csv")
    }
    outputs["report_json"].write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outputs["report_markdown"].write_text(render_report(report), encoding="utf-8")
    return outputs["report_json"]


def validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_macro_regime_event_census_v1":
        raise ValueError("unexpected macro regime event census contract")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("macro regime event census V1 is locked to XAUUSD")
    if int(contract["macro_source_lock"]["availability_lag_calendar_days"]) < 2:
        raise ValueError("macro availability lag must be at least two calendar days")
    if not contract["macro_source_lock"].get(
        "current_vintage_revision_risk_disclosed"
    ):
        raise ValueError("macro revision risk must be disclosed")
    if len(contract["macro_source_lock"]["series"]) != 4:
        raise ValueError("macro source set differs from preregistration")
    families = {str(row["family_id"]) for row in contract["event_families"]}
    expected = {
        "macro_aligned_h1_trend_pullback_v1",
        "macro_aligned_h1_range_break_v1",
        "macro_shock_h1_continuation_v1",
        "macro_divergence_h1_reclaim_v1",
    }
    if families != expected:
        raise ValueError("macro event family set differs from preregistration")
    selection = contract["selection"]
    if (
        selection["hypothesis_keys"] != ["family_id", "direction"]
        or int(selection["maximum_hypotheses"]) != 8
        or selection.get("parameter_grid_search_authorized")
        or selection.get("context_subgroup_promotion_authorized")
    ):
        raise ValueError("macro hypothesis boundary differs from preregistration")
    controls = contract["research_controls"]
    if (
        not controls.get("research_only")
        or not controls.get("known_program_level_history_contamination")
        or controls.get("claims_untouched_holdout")
        or controls.get("same_iteration_post_outcome_tuning_authorized")
        or controls.get("model_training_authorized")
    ):
        raise ValueError("macro research controls are unsafe")
    for key in (
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if contract["authorization"].get(key):
            raise ValueError(f"forbidden macro census authorization: {key}")
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
        raise ValueError("macro census windows are not strictly chronological")


def load_locked_dukascopy_source(contract: Mapping[str, Any]) -> pd.DataFrame:
    locked = contract["dukascopy_source_lock"]
    root = Path(
        os.environ.get(str(locked["storage_environment_variable"]), "").strip()
        or str(locked["default_storage_root"])
    ).expanduser().resolve()
    path = (root / str(locked["feature_path"])).resolve()
    if _sha256_file(path) != str(locked["feature_sha256"]):
        raise MacroRegimeEventCensusError("macro census Dukascopy hash mismatch")
    frame = pd.read_parquet(path).sort_values("timestamp_ms").reset_index(drop=True)
    if len(frame) != int(locked["feature_rows"]):
        raise MacroRegimeEventCensusError("macro census Dukascopy row mismatch")
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    if np.any(np.diff(timestamps) <= 0):
        raise MacroRegimeEventCensusError("macro census Dukascopy chronology mismatch")
    return frame


def load_locked_broker_cost(
    phase1_root: Path, contract: Mapping[str, Any]
) -> dict[str, Any]:
    locked = contract["broker_cost_source_lock"]
    path = (phase1_root / str(locked["report_path"])).resolve()
    if _sha256_file(path) != str(locked["report_sha256"]):
        raise MacroRegimeEventCensusError("macro census broker-cost report hash mismatch")
    report = json.loads(path.read_text(encoding="utf-8"))
    cost = report["locked_cost_assumption"]
    checks = (
        str(report["classification"]) == str(locked["required_classification"]),
        math.isclose(
            float(cost["broker_spread_floor_price"]),
            float(locked["broker_spread_floor_price"]),
        ),
        math.isclose(
            float(cost["additional_execution_cost_usd_per_0p01_lot"]),
            float(locked["additional_execution_cost_usd_per_0p01_lot"]),
        ),
        math.isclose(
            float(cost["maximum_total_stressed_entry_cost_r"]),
            float(locked["maximum_total_stressed_entry_cost_r"]),
        ),
        math.isclose(
            float(cost["minimum_initial_stop_distance_price"]),
            float(locked["minimum_initial_stop_distance_price"]),
        ),
    )
    if not all(checks):
        raise MacroRegimeEventCensusError("macro census broker-cost values mismatch")
    return report


def load_locked_macro_source(contract: Mapping[str, Any]) -> pd.DataFrame:
    locked = contract["macro_source_lock"]
    root = Path(str(locked["root"])).expanduser().resolve()
    start = pd.Timestamp(str(locked["observation_start"]), tz="UTC")
    end = pd.Timestamp(str(locked["observation_end"]), tz="UTC")
    series_frames = []
    for source in locked["series"]:
        path = (root / str(source["filename"])).resolve()
        if _sha256_file(path) != str(source["sha256"]):
            raise MacroRegimeEventCensusError(
                f"macro source hash mismatch: {source['series_id']}"
            )
        raw = pd.read_csv(path)
        if len(raw) != int(source["rows"]):
            raise MacroRegimeEventCensusError(
                f"macro source row mismatch: {source['series_id']}"
            )
        series_id = str(source["series_id"])
        if list(raw.columns) != ["observation_date", series_id]:
            raise MacroRegimeEventCensusError(
                f"macro source schema mismatch: {series_id}"
            )
        raw["observation_date"] = pd.to_datetime(raw["observation_date"], utc=True)
        if (
            raw["observation_date"].min() != start
            or raw["observation_date"].max() != end
            or not raw["observation_date"].is_monotonic_increasing
            or raw["observation_date"].duplicated().any()
        ):
            raise MacroRegimeEventCensusError(
                f"macro source date identity mismatch: {series_id}"
            )
        raw[series_id] = pd.to_numeric(raw[series_id], errors="coerce")
        valid = raw.dropna(subset=[series_id]).copy()
        valid[f"{series_id}_source_date"] = valid["observation_date"]
        for observations in contract["macro_features"]["change_observations"]:
            observations = int(observations)
            valid[f"{series_id}_change_{observations}"] = valid[series_id].diff(
                observations
            )
            if series_id == "DTWEXBGS":
                valid[f"{series_id}_pct_change_{observations}"] = 100.0 * (
                    valid[series_id] / valid[series_id].shift(observations) - 1.0
                )
        series_frames.append(valid.set_index("observation_date"))
    combined = pd.concat(series_frames, axis=1, join="outer").sort_index()
    calendar = pd.date_range(start=start, end=end, freq="D")
    combined = combined.reindex(calendar).ffill()
    combined.index.name = "macro_cutoff_date"
    combined["curve_2s10"] = combined["DGS10"] - combined["DGS2"]
    combined["breakeven_10y"] = combined["DGS10"] - combined["DFII10"]
    macro = contract["macro_features"]
    combined["macro_shock_score"] = -combined["DFII10_change_1"] / float(
        macro["shock_score"]["real_yield_scale_percentage_points"]
    ) - combined["DTWEXBGS_pct_change_1"] / float(
        macro["shock_score"]["broad_dollar_scale_pct"]
    )
    return combined.reset_index()


def aggregate_h1(frame: pd.DataFrame, contract: Mapping[str, Any]) -> pd.DataFrame:
    source = frame.sort_values("timestamp_ms").reset_index(drop=True).copy()
    source["source_index"] = np.arange(len(source), dtype=np.int64)
    source["h1_bucket"] = source["timestamp_ms"] - source["timestamp_ms"] % H1_WIDTH_MS
    group = source.groupby("h1_bucket", sort=True)
    named: dict[str, tuple[str, str]] = {
        "timestamp_first": ("timestamp_ms", "min"),
        "timestamp_last": ("timestamp_ms", "max"),
        "source_bar_count": ("timestamp_ms", "count"),
        "source_last_index": ("source_index", "max"),
        "tick_spread_mean": ("tick_spread_mean", "mean"),
        "tick_spread_last": ("tick_spread_last", "last"),
        "tick_spread_max": ("tick_spread_max", "max"),
        "tick_imbalance": ("tick_imbalance_5m", "mean"),
        "quote_intensity_ratio": ("quote_intensity_ratio", "mean"),
    }
    for prefix in ("mid", "bid", "ask"):
        named[f"{prefix}_open"] = (f"{prefix}_open", "first")
        named[f"{prefix}_high"] = (f"{prefix}_high", "max")
        named[f"{prefix}_low"] = (f"{prefix}_low", "min")
        named[f"{prefix}_close"] = (f"{prefix}_close", "last")
    out = group.agg(**named).reset_index().rename(columns={"h1_bucket": "timestamp_ms"})
    required = int(contract["aggregation"]["required_source_bars"])
    out = out[
        (out["source_bar_count"] == required)
        & (out["timestamp_first"] == out["timestamp_ms"])
        & (out["timestamp_last"] == out["timestamp_ms"] + (required - 1) * BAR_WIDTH_MS)
    ].copy()
    previous = out["mid_close"].shift(1)
    true_range = pd.concat(
        [
            out["mid_high"] - out["mid_low"],
            (out["mid_high"] - previous).abs(),
            (out["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    aggregation = contract["aggregation"]
    atr_bars = int(aggregation["h1_atr_bars"])
    out["atr"] = true_range.ewm(
        alpha=1 / atr_bars, adjust=False, min_periods=atr_bars
    ).mean()
    out["ema_fast"] = out["mid_close"].ewm(
        span=int(aggregation["ema_fast_bars"]), adjust=False
    ).mean()
    out["ema_slow"] = out["mid_close"].ewm(
        span=int(aggregation["ema_slow_bars"]), adjust=False
    ).mean()
    slope_lag = int(aggregation["ema_slope_lag_bars"])
    out["ema_fast_slope_atr"] = (
        out["ema_fast"] - out["ema_fast"].shift(slope_lag)
    ) / out["atr"]
    out["h1_return_atr"] = (out["mid_close"] - previous) / out["atr"]
    candle_range = (out["mid_high"] - out["mid_low"]).replace(0, np.nan)
    out["body_fraction"] = (out["mid_close"] - out["mid_open"]).abs() / candle_range
    range_bars = int(aggregation["prior_range_bars"])
    out["prior_range_high"] = out["mid_high"].shift(1).rolling(range_bars).max()
    out["prior_range_low"] = out["mid_low"].shift(1).rolling(range_bars).min()
    out["decision_timestamp_ms"] = out["timestamp_ms"] + H1_WIDTH_MS
    out["decision_time_utc"] = out["decision_timestamp_ms"].map(
        lambda value: _iso_ms(int(value))
    )
    out["date_utc"] = pd.to_datetime(
        out["decision_timestamp_ms"], unit="ms", utc=True
    ).dt.strftime("%Y-%m-%d")
    return out.replace([np.inf, -np.inf], np.nan).reset_index(drop=True)


def attach_causal_macro(
    h1: pd.DataFrame, macro: pd.DataFrame, contract: Mapping[str, Any]
) -> pd.DataFrame:
    result = h1.copy()
    lag_days = int(contract["macro_source_lock"]["availability_lag_calendar_days"])
    decision_dates = pd.to_datetime(
        result["decision_timestamp_ms"], unit="ms", utc=True
    ).dt.floor("D")
    result["macro_cutoff_date"] = decision_dates - pd.to_timedelta(lag_days, unit="D")
    result = result.merge(macro, on="macro_cutoff_date", how="left", validate="many_to_one")
    source_columns = [
        column for column in result.columns if column.endswith("_source_date")
    ]
    result["macro_latest_source_date"] = result[source_columns].max(axis=1)
    result["macro_lag_enforced"] = result[source_columns].le(
        result["macro_cutoff_date"], axis=0
    ).all(axis=1)
    observations = int(contract["macro_features"]["alignment_observations"])
    real_change = result[f"DFII10_change_{observations}"]
    dollar_change = result[f"DTWEXBGS_pct_change_{observations}"]
    long_config = contract["macro_features"]["long_alignment"]
    short_config = contract["macro_features"]["short_alignment"]
    result["macro_long_aligned"] = (
        real_change <= float(long_config["real_yield_change_lte"])
    ) & (dollar_change <= float(long_config["broad_dollar_pct_change_lte"]))
    result["macro_short_aligned"] = (
        real_change >= float(short_config["real_yield_change_gte"])
    ) & (dollar_change >= float(short_config["broad_dollar_pct_change_gte"]))
    return result


def generate_events(
    frame: pd.DataFrame, contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    families = {str(row["family_id"]): row for row in contract["event_families"]}
    events = []
    events.extend(
        _trend_pullback_events(
            frame, families["macro_aligned_h1_trend_pullback_v1"], contract
        )
    )
    events.extend(
        _range_break_events(
            frame, families["macro_aligned_h1_range_break_v1"], contract
        )
    )
    events.extend(
        _macro_shock_events(
            frame, families["macro_shock_h1_continuation_v1"], contract
        )
    )
    events.extend(
        _divergence_reclaim_events(
            frame, families["macro_divergence_h1_reclaim_v1"], contract
        )
    )
    return sorted(
        events,
        key=lambda row: (
            int(row["decision_timestamp_ms"]),
            str(row["family_id"]),
            str(row["direction"]),
        ),
    )


def _trend_pullback_events(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    gap = (frame["ema_fast"] - frame["ema_slow"]) / frame["atr"]
    common = _finite_mask(frame) & (frame["body_fraction"] > 0)
    long_mask = (
        common
        & frame["macro_long_aligned"]
        & (gap >= float(family["minimum_ema_gap_atr"]))
        & (frame["ema_fast_slope_atr"] > 0)
        & (frame["mid_low"] <= frame["ema_fast"])
        & (frame["mid_close"] >= frame["ema_fast"])
        & (frame["mid_close"] > frame["mid_open"])
    )
    short_mask = (
        common
        & frame["macro_short_aligned"]
        & (gap <= -float(family["minimum_ema_gap_atr"]))
        & (frame["ema_fast_slope_atr"] < 0)
        & (frame["mid_high"] >= frame["ema_fast"])
        & (frame["mid_close"] <= frame["ema_fast"])
        & (frame["mid_close"] < frame["mid_open"])
    )
    return _events_from_masks(frame, family, long_mask, short_mask, contract)


def _range_break_events(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    common = _finite_mask(frame) & (
        frame["body_fraction"] >= float(family["minimum_body_fraction"])
    )
    distance = float(family["minimum_close_outside_atr"]) * frame["atr"]
    long_mask = (
        common
        & frame["macro_long_aligned"]
        & (frame["mid_close"] >= frame["prior_range_high"] + distance)
    )
    short_mask = (
        common
        & frame["macro_short_aligned"]
        & (frame["mid_close"] <= frame["prior_range_low"] - distance)
    )
    return _events_from_masks(frame, family, long_mask, short_mask, contract)


def _macro_shock_events(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    shock = contract["macro_features"]["shock_score"]
    common = _finite_mask(frame) & (
        frame["body_fraction"] >= float(family["minimum_body_fraction"])
    )
    long_mask = (
        common
        & (frame["macro_shock_score"] >= float(shock["long_score_gte"]))
        & (frame["h1_return_atr"] >= float(family["minimum_h1_return_atr"]))
        & (frame["mid_close"] > frame["mid_open"])
    )
    short_mask = (
        common
        & (frame["macro_shock_score"] <= float(shock["short_score_lte"]))
        & (frame["h1_return_atr"] <= -float(family["minimum_h1_return_atr"]))
        & (frame["mid_close"] < frame["mid_open"])
    )
    return _events_from_masks(frame, family, long_mask, short_mask, contract)


def _divergence_reclaim_events(
    frame: pd.DataFrame, family: Mapping[str, Any], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    common = _finite_mask(frame) & (
        frame["body_fraction"] >= float(family["minimum_body_fraction"])
    )
    excursion = float(family["minimum_excursion_atr"]) * frame["atr"]
    long_mask = (
        common
        & frame["macro_long_aligned"]
        & (frame["mid_low"] <= frame["prior_range_low"] - excursion)
        & (frame["mid_close"] > frame["prior_range_low"])
        & (frame["mid_close"] > frame["mid_open"])
    )
    short_mask = (
        common
        & frame["macro_short_aligned"]
        & (frame["mid_high"] >= frame["prior_range_high"] + excursion)
        & (frame["mid_close"] < frame["prior_range_high"])
        & (frame["mid_close"] < frame["mid_open"])
    )
    return _events_from_masks(frame, family, long_mask, short_mask, contract)


def _events_from_masks(
    frame: pd.DataFrame,
    family: Mapping[str, Any],
    long_mask: pd.Series,
    short_mask: pd.Series,
    contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    output = []
    cooldown = int(family["cooldown_hours_per_direction"]) * H1_WIDTH_MS
    for direction, mask in (("LONG", long_mask), ("SHORT", short_mask)):
        last_decision = -10**18
        for index in np.flatnonzero(mask.fillna(False).to_numpy(dtype=bool)):
            row = frame.iloc[index]
            decision = int(row["decision_timestamp_ms"])
            if decision - last_decision < cooldown:
                continue
            event = _make_event(row, family, direction, contract)
            if event is not None:
                output.append(event)
                last_decision = decision
    return output


def _make_event(
    row: Mapping[str, Any],
    family: Mapping[str, Any],
    direction: str,
    contract: Mapping[str, Any],
) -> dict[str, Any] | None:
    decision = int(row["decision_timestamp_ms"])
    split = _split(decision, contract)
    if split is None:
        return None
    identity = f"{family['family_id']}|{decision}|{direction}"
    return {
        "event_id": hashlib.sha256(identity.encode("ascii")).hexdigest(),
        "family_id": str(family["family_id"]),
        "mechanism": str(family["mechanism"]),
        "direction": direction,
        "split": split,
        "signal_h1_start_utc": _iso_ms(int(row["timestamp_ms"])),
        "decision_timestamp_ms": decision,
        "decision_time_utc": _iso_ms(decision),
        "source_last_index": int(row["source_last_index"]),
        "atr": float(row["atr"]),
        "signal_open": float(row["mid_open"]),
        "signal_high": float(row["mid_high"]),
        "signal_low": float(row["mid_low"]),
        "signal_close": float(row["mid_close"]),
        "body_fraction": float(row["body_fraction"]),
        "prior_range_high": float(row["prior_range_high"]),
        "prior_range_low": float(row["prior_range_low"]),
        "macro_cutoff_date": str(pd.Timestamp(row["macro_cutoff_date"]).date()),
        "macro_latest_source_date": str(
            pd.Timestamp(row["macro_latest_source_date"]).date()
        ),
        "real_yield": float(row["DFII10"]),
        "real_yield_change_5": float(row["DFII10_change_5"]),
        "broad_dollar": float(row["DTWEXBGS"]),
        "broad_dollar_pct_change_5": float(row["DTWEXBGS_pct_change_5"]),
        "curve_2s10": float(row["curve_2s10"]),
        "breakeven_10y": float(row["breakeven_10y"]),
        "macro_shock_score": float(row["macro_shock_score"]),
        "stop_atr": float(family["stop_atr"]),
        "structural_buffer_atr": float(family["structural_buffer_atr"]),
        "target_r": float(family["target_r"]),
        "maximum_hold_hours": int(family["maximum_hold_hours"]),
    }


def validate_events(events: Sequence[Mapping[str, Any]]) -> None:
    ids = [str(row["event_id"]) for row in events]
    if len(ids) != len(set(ids)):
        raise MacroRegimeEventCensusError("duplicate macro event IDs")
    if list(events) != sorted(
        events,
        key=lambda row: (
            int(row["decision_timestamp_ms"]),
            str(row["family_id"]),
            str(row["direction"]),
        ),
    ):
        raise MacroRegimeEventCensusError("macro events are non-chronological")


def label_events(
    frame: pd.DataFrame,
    events: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [_label_event(frame, event, contract) for event in events]


def _label_event(
    frame: pd.DataFrame, event: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Any]:
    entry_index = int(event["source_last_index"]) + 1
    identity = _label_identity(event)
    if entry_index >= len(frame):
        return _empty_label(identity, "UNRESOLVED", "NEXT_BAR_UNAVAILABLE")
    entry_row = frame.iloc[entry_index]
    if int(entry_row["timestamp_ms"]) != int(event["decision_timestamp_ms"]):
        return _empty_label(identity, "INELIGIBLE", "NEXT_BAR_NOT_CONTIGUOUS")
    direction = str(event["direction"])
    entry_price = float(entry_row["ask_open"] if direction == "LONG" else entry_row["bid_open"])
    native_spread = float(entry_row["ask_open"] - entry_row["bid_open"])
    atr = float(event["atr"])
    buffer = float(event["structural_buffer_atr"]) * atr
    structural_stop = (
        float(event["signal_low"]) - buffer
        if direction == "LONG"
        else float(event["signal_high"]) + buffer
    )
    structural_distance = (
        entry_price - structural_stop
        if direction == "LONG"
        else structural_stop - entry_price
    )
    execution = contract["execution"]
    stop_distance = max(
        float(execution["minimum_initial_stop_distance_price"]),
        float(event["stop_atr"]) * atr,
        structural_distance,
    )
    quantity = float(execution["lot_size"]) * float(
        execution["contract_size_ounces_per_lot"]
    )
    risk_usd = stop_distance * quantity
    if risk_usd > float(execution["maximum_initial_risk_usd"]):
        return _empty_label(identity, "INELIGIBLE", "INITIAL_RISK_USD")
    floor_spread = float(execution["broker_spread_floor_price"])
    additional_price = float(execution["additional_execution_cost_usd"]) / quantity
    stressed_entry_cost_price = max(native_spread, floor_spread) + additional_price
    cost_r = stressed_entry_cost_price / stop_distance
    if cost_r > float(execution["maximum_total_stressed_entry_cost_r"]):
        return _empty_label(identity, "INELIGIBLE", "STRESSED_ENTRY_COST_R")
    maximum_bars = int(event["maximum_hold_hours"]) * 12
    end_index = entry_index + maximum_bars - 1
    _, segment_end = _segment_bounds(str(event["split"]), contract)
    if end_index >= len(frame) or int(frame.iloc[end_index]["timestamp_ms"]) + BAR_WIDTH_MS > segment_end:
        return _empty_label(identity, "UNRESOLVED", "SEGMENT_HORIZON_UNAVAILABLE")
    stop = entry_price - stop_distance if direction == "LONG" else entry_price + stop_distance
    target_distance = float(event["target_r"]) * stop_distance
    target = entry_price + target_distance if direction == "LONG" else entry_price - target_distance
    exit_index = end_index
    exit_price: float | None = None
    exit_reason = "TIMEOUT"
    for index in range(entry_index, end_index + 1):
        row = frame.iloc[index]
        if direction == "LONG":
            if float(row["bid_open"]) <= stop:
                exit_index, exit_price, exit_reason = index, float(row["bid_open"]), "STOP"
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
                exit_index, exit_price, exit_reason = index, float(row["ask_open"]), "STOP"
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
    gross_pnl = move * quantity
    duration_ms = int(frame.iloc[exit_index]["timestamp_ms"]) + BAR_WIDTH_MS - int(
        event["decision_timestamp_ms"]
    )
    duration_hours = duration_ms / H1_WIDTH_MS
    spread_floor_uplift = max(0.0, floor_spread - native_spread) * quantity
    holding_cost = duration_hours / 24.0 * float(execution["holding_cost_per_24h_usd"])
    stress_cost = (
        spread_floor_uplift
        + float(execution["additional_execution_cost_usd"])
        + holding_cost
    )
    stress_pnl = gross_pnl - stress_cost
    return {
        **identity,
        "status": "RESOLVED",
        "entry_time_utc": _iso_ms(int(event["decision_timestamp_ms"])),
        "exit_time_utc": _iso_ms(int(frame.iloc[exit_index]["timestamp_ms"]) + BAR_WIDTH_MS),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "native_entry_spread": native_spread,
        "broker_spread_floor": floor_spread,
        "stressed_entry_cost_price": stressed_entry_cost_price,
        "stressed_entry_cost_r": cost_r,
        "stop_distance": stop_distance,
        "target_distance": target_distance,
        "initial_risk_usd": risk_usd,
        "duration_hours": duration_hours,
        "exit_reason": exit_reason,
        "gross_pnl_usd": gross_pnl,
        "stress_cost_usd": stress_cost,
        "stress_net_pnl_usd": stress_pnl,
        "gross_r": gross_pnl / risk_usd,
        "stress_net_r": stress_pnl / risk_usd,
    }


def _label_identity(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: event[key]
        for key in (
            "event_id",
            "family_id",
            "direction",
            "split",
            "decision_time_utc",
            "macro_cutoff_date",
            "macro_latest_source_date",
            "atr",
            "target_r",
            "maximum_hold_hours",
        )
    }


def _empty_label(
    identity: Mapping[str, Any], status: str, reason: str
) -> dict[str, Any]:
    return {
        **dict(identity),
        "status": status,
        "entry_time_utc": "",
        "exit_time_utc": "",
        "entry_price": None,
        "exit_price": None,
        "native_entry_spread": None,
        "broker_spread_floor": None,
        "stressed_entry_cost_price": None,
        "stressed_entry_cost_r": None,
        "stop_distance": None,
        "target_distance": None,
        "initial_risk_usd": None,
        "duration_hours": None,
        "exit_reason": reason,
        "gross_pnl_usd": None,
        "stress_cost_usd": None,
        "stress_net_pnl_usd": None,
        "gross_r": None,
        "stress_net_r": None,
    }


def build_report(
    *,
    phase1_root: Path,
    contract_file: Path,
    contract: Mapping[str, Any],
    broker_report: Mapping[str, Any],
    h1: pd.DataFrame,
    events: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    del phase1_root
    resolved = [row for row in labels if row["status"] == "RESOLVED"]
    source_days = _source_days(h1, contract)
    family_ids = [str(row["family_id"]) for row in contract["event_families"]]
    metrics_by_key = {}
    metric_rows = []
    for family in family_ids:
        for direction in ("LONG", "SHORT"):
            for segment in ("train", "validation", "internal_test", "exam"):
                rows = [
                    row
                    for row in resolved
                    if row["family_id"] == family
                    and row["direction"] == direction
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
                    bootstrap_seed=_bootstrap_seed(contract, family, direction),
                )
                metrics_by_key[(family, direction, segment)] = metrics
                metric_rows.append(
                    {
                        "family_id": family,
                        "direction": direction,
                        "segment": segment,
                        **metrics,
                    }
                )
    hypotheses = {}
    survivors = {key: [] for key in ("train", "validation", "internal_test", "exam")}
    for family in family_ids:
        for direction in ("LONG", "SHORT"):
            name = f"{family}:{direction}"
            result = {}
            opened = True
            for segment, gate_key in (
                ("train", "train_gates"),
                ("validation", "validation_gates"),
                ("internal_test", "internal_test_gates"),
                ("exam", "exam_gates"),
            ):
                metrics = metrics_by_key[(family, direction, segment)]
                gates = policy_gates(metrics, contract["selection"][gate_key])
                passed = opened and all(gates.values())
                result[segment] = {
                    "opened_for_decision": opened,
                    "metrics": metrics,
                    "gates": gates,
                    "passed": passed,
                }
                if passed:
                    survivors[segment].append(name)
                opened = passed
            hypotheses[name] = result
    event_count = len(events)
    labeled_ids = {
        str(row["event_id"]) for row in labels if row["status"] != "UNRESOLVED"
    }
    label_share = len(labeled_ids) / event_count if event_count else 0.0
    windows = _window_h1(h1, contract)
    macro_columns = [
        "DFII10_change_5",
        "DTWEXBGS_pct_change_5",
        "macro_shock_score",
        "macro_latest_source_date",
    ]
    macro_coverage = float(windows[macro_columns].notna().all(axis=1).mean()) if len(windows) else 0.0
    lag_enforced = bool(windows["macro_lag_enforced"].fillna(False).all()) if len(windows) else False
    quality = {
        "dukascopy_hash_and_rows_match": True,
        "broker_cost_report_hash_and_values_match": str(broker_report["classification"])
        == str(contract["broker_cost_source_lock"]["required_classification"]),
        "macro_hashes_and_rows_match": True,
        "macro_availability_lag_enforced": lag_enforced,
        "macro_coverage_share_ge_minimum": macro_coverage
        >= float(contract["quality_gates"]["minimum_macro_coverage_share"]),
        "resolved_or_ineligible_event_share_ge_minimum": label_share
        >= float(
            contract["quality_gates"]["minimum_resolved_or_ineligible_event_share"]
        ),
        "event_ids_unique": len({row["event_id"] for row in events}) == event_count,
        "events_chronological": list(events)
        == sorted(
            events,
            key=lambda row: (
                row["decision_timestamp_ms"],
                row["family_id"],
                row["direction"],
            ),
        ),
    }
    classification = _classification(quality, survivors)
    return {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "dukascopy_feature_sha256": str(
            contract["dukascopy_source_lock"]["feature_sha256"]
        ),
        "broker_cost_report_sha256": str(
            contract["broker_cost_source_lock"]["report_sha256"]
        ),
        "macro_source_hashes": {
            row["series_id"]: row["sha256"]
            for row in contract["macro_source_lock"]["series"]
        },
        "h1_rows": len(h1),
        "macro_coverage_share": macro_coverage,
        "source_days": source_days,
        "event_count": event_count,
        "event_counts_by_family_direction": dict(
            Counter(f"{row['family_id']}:{row['direction']}" for row in events)
        ),
        "label_status_counts": dict(Counter(row["status"] for row in labels)),
        "label_exit_reason_counts": dict(Counter(row["exit_reason"] for row in labels)),
        "resolved_or_ineligible_event_share": label_share,
        "quality_gates": quality,
        "hypotheses": hypotheses,
        "stage_survivors": survivors,
        "authorization": {
            **dict(contract["authorization"]),
            "specialist_hypothesis_candidates": survivors["exam"],
            "model_training_authorized": False,
            "demo_or_live_authorized": False,
        },
        "limitations": [
            "Macro inputs use current-vintage history and retain disclosed revision risk.",
            "All retrospective periods have known program-level research contamination.",
            "M5 barrier screens require exact-tick replay before any portfolio use.",
            "A macro census survivor would authorize a hypothesis, not trading.",
        ],
        "_metric_rows": metric_rows,
    }


def _classification(
    quality: Mapping[str, bool], survivors: Mapping[str, Sequence[str]]
) -> str:
    if not all(quality.values()):
        return "MACRO_REGIME_EVENT_CENSUS_INVALID"
    if not survivors["train"]:
        return "MACRO_REGIME_EVENT_CENSUS_NO_TRAIN_SURVIVOR"
    if not survivors["validation"]:
        return "MACRO_REGIME_EVENT_CENSUS_NO_VALIDATION_SURVIVOR"
    if not survivors["internal_test"]:
        return "MACRO_REGIME_EVENT_CENSUS_NO_INTERNAL_TEST_SURVIVOR"
    if not survivors["exam"]:
        return "MACRO_REGIME_EVENT_CENSUS_NO_EXAM_SURVIVOR"
    return "MACRO_REGIME_EVENT_CENSUS_SPECIALIST_HYPOTHESIS_CANDIDATE"


def _finite_mask(frame: pd.DataFrame) -> pd.Series:
    columns = [
        "atr",
        "ema_fast",
        "ema_slow",
        "ema_fast_slope_atr",
        "h1_return_atr",
        "body_fraction",
        "prior_range_high",
        "prior_range_low",
        "DFII10_change_5",
        "DTWEXBGS_pct_change_5",
        "macro_shock_score",
    ]
    finite = pd.Series(
        np.isfinite(frame[columns].to_numpy(dtype=float)).all(axis=1), index=frame.index
    )
    return finite & frame["macro_lag_enforced"].fillna(False).astype(bool)


def _source_days(frame: pd.DataFrame, contract: Mapping[str, Any]) -> dict[str, int]:
    result = {}
    for segment in ("train", "validation", "internal_test", "exam"):
        start, end = _segment_bounds(segment, contract)
        selected = frame[
            (frame["decision_timestamp_ms"] >= start)
            & (frame["decision_timestamp_ms"] < end)
        ]
        result[segment] = int(selected["date_utc"].nunique())
    return result


def _window_h1(frame: pd.DataFrame, contract: Mapping[str, Any]) -> pd.DataFrame:
    start = _parse_ms(contract["windows"]["train_start_utc"])
    end = _parse_ms(contract["windows"]["exam_end_exclusive_utc"])
    return frame[
        (frame["decision_timestamp_ms"] >= start)
        & (frame["decision_timestamp_ms"] < end)
    ]


def _split(timestamp_ms: int, contract: Mapping[str, Any]) -> str | None:
    for segment in ("train", "validation", "internal_test", "exam"):
        start, end = _segment_bounds(segment, contract)
        if start <= timestamp_ms < end:
            return segment
    return None


def _segment_bounds(segment: str, contract: Mapping[str, Any]) -> tuple[int, int]:
    windows = contract["windows"]
    starts = {
        "train": "train_start_utc",
        "validation": "train_end_exclusive_utc",
        "internal_test": "validation_end_exclusive_utc",
        "exam": "internal_test_end_exclusive_utc",
    }
    ends = {
        "train": "train_end_exclusive_utc",
        "validation": "validation_end_exclusive_utc",
        "internal_test": "internal_test_end_exclusive_utc",
        "exam": "exam_end_exclusive_utc",
    }
    return _parse_ms(windows[starts[segment]]), _parse_ms(windows[ends[segment]])


def _bootstrap_seed(
    contract: Mapping[str, Any], family: str, direction: str
) -> int:
    base = int(contract["selection"]["bootstrap_seed"])
    digest = hashlib.sha256(f"{family}|{direction}".encode("ascii")).digest()
    return base + int.from_bytes(digest[:4], "big")


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Macro Regime Event Census V1 Report",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "## Quality",
        "",
        f"- H1 rows: `{payload['h1_rows']}`",
        f"- Macro coverage: `{payload['macro_coverage_share']:.4%}`",
        f"- Events: `{payload['event_count']}`",
        f"- Resolved or ineligible share: `{payload['resolved_or_ineligible_event_share']:.4%}`",
    ]
    lines.extend(
        f"- {name}: `{'PASS' if passed else 'FAIL'}`"
        for name, passed in payload["quality_gates"].items()
    )
    lines.extend(["", "## Hypotheses", ""])
    for name, result in payload["hypotheses"].items():
        train = result["train"]
        metrics = train["metrics"]
        lines.append(
            f"- `{name}`: train pass `{str(train['passed']).lower()}`, "
            f"events `{metrics['events']}`, PF `{metrics['stress_profit_factor']}`, "
            f"average R `{metrics['average_stress_r']:.4f}`"
        )
    lines.extend(
        [
            "",
            "## Decision Boundary",
            "",
            f"- Exam hypothesis candidates: `{payload['stage_survivors']['exam']}`",
            "- Model training authorization: `false`",
            "- Demo or live authorization: `false`",
            "",
        ]
    )
    return "\n".join(lines)
