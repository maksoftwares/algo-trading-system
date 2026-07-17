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
from ml.a3_meta_v1.macro_regime_event_census import load_locked_broker_cost


DEFAULT_CONTRACT = Path("config/ml/a3_ml_intraday_crossasset_event_census_v1.json")
M15_WIDTH_MS = 15 * 60 * 1000
HOUR_MS = 60 * 60 * 1000


class IntradayCrossassetEventCensusError(RuntimeError):
    pass


def run_intraday_crossasset_event_census(
    phase1_root: Path, contract_path: Path | None = None
) -> Path:
    phase1_root = phase1_root.resolve()
    contract_file = (contract_path or phase1_root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    validate_contract(contract)
    storage_root = _storage_root(contract)
    xau = load_locked_xau(contract, storage_root)
    macro, macro_report = load_locked_intraday_macro(
        phase1_root, contract, storage_root
    )
    broker_report = load_locked_broker_cost(phase1_root, contract)
    m15 = build_m15_features(xau, macro, contract)
    events = generate_events(m15, contract)
    validate_events(events)
    report, labels, metric_rows = evaluate_chronologically(
        xau=xau,
        m15=m15,
        events=events,
        contract=contract,
        contract_file=contract_file,
        macro_report=macro_report,
        broker_report=broker_report,
    )
    outputs = {
        key: (phase1_root / value).resolve()
        for key, value in contract["outputs"].items()
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    m15.to_parquet(outputs["m15_features_parquet"], index=False, compression="zstd")
    _write_csv(outputs["events_csv"], events)
    _write_csv(outputs["labels_csv"], labels)
    _write_csv(outputs["metrics_csv"], metric_rows)
    report["artifacts"] = {
        key: _artifact(outputs[key])
        for key in (
            "m15_features_parquet",
            "events_csv",
            "labels_csv",
            "metrics_csv",
        )
    }
    outputs["report_json"].write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outputs["report_markdown"].write_text(
        render_report(report), encoding="utf-8", newline="\n"
    )
    return outputs["report_json"]


def validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_intraday_crossasset_event_census_v1":
        raise ValueError("unexpected intraday crossasset event census contract")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("intraday crossasset event census is locked to XAUUSD")
    expected_families = {
        "crossasset_agreement_continuation_v1",
        "dollar_impulse_continuation_v1",
        "bond_impulse_continuation_v1",
        "crossasset_lead_gold_catchup_v1",
    }
    observed = {str(row["family_id"]) for row in contract["event_families"]}
    if observed != expected_families:
        raise ValueError("intraday crossasset family set differs from preregistration")
    selection = contract["selection"]
    if (
        selection["hypothesis_keys"] != ["family_id", "direction"]
        or int(selection["maximum_hypotheses"]) != 8
        or selection.get("parameter_grid_search_authorized")
        or selection.get("context_subgroup_promotion_authorized")
    ):
        raise ValueError("intraday crossasset hypothesis boundary changed")
    features = contract["causal_features"]
    if (
        not features.get("source_volatility_scale_is_lagged_one_bar")
        or features.get("forward_fill_source_quotes")
        or features.get("allow_features_across_timestamp_gaps")
        or not features.get("decision_uses_completed_bars_only")
    ):
        raise ValueError("intraday crossasset causality controls weakened")
    execution = contract["execution"]
    if (
        execution.get("same_bar_collision_policy") != "STOP_FIRST"
        or not execution.get("entry_next_contiguous_m5_bar")
        or float(execution["minimum_initial_stop_distance_price"]) < 7.0
    ):
        raise ValueError("intraday crossasset execution lock changed")
    controls = contract["research_controls"]
    if (
        not controls.get("research_only")
        or not controls.get("known_program_level_history_contamination")
        or controls.get("claims_untouched_holdout")
        or controls.get("same_iteration_post_outcome_tuning_authorized")
        or controls.get("model_training_authorized")
    ):
        raise ValueError("intraday crossasset research controls are unsafe")
    for key in (
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if contract["authorization"].get(key):
            raise ValueError(f"forbidden intraday crossasset authorization: {key}")
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
        raise ValueError("intraday crossasset windows are not strictly chronological")


def _storage_root(contract: Mapping[str, Any]) -> Path:
    value = os.environ.get(str(contract["storage_environment_variable"]), "").strip()
    root = Path(value or str(contract["default_storage_root"])).expanduser().resolve()
    if not root.is_dir():
        raise IntradayCrossassetEventCensusError(f"storage root does not exist: {root}")
    return root


def load_locked_xau(contract: Mapping[str, Any], storage_root: Path) -> pd.DataFrame:
    locked = contract["xau_source_lock"]
    path = (storage_root / str(locked["feature_path"])).resolve()
    if _sha256_file(path) != str(locked["feature_sha256"]):
        raise IntradayCrossassetEventCensusError("locked XAU feature hash mismatch")
    frame = pd.read_parquet(path).sort_values("timestamp_ms").reset_index(drop=True)
    if len(frame) != int(locked["feature_rows"]):
        raise IntradayCrossassetEventCensusError("locked XAU feature row mismatch")
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    if np.any(np.diff(timestamps) <= 0):
        raise IntradayCrossassetEventCensusError("locked XAU timestamps are invalid")
    return frame


def load_locked_intraday_macro(
    phase1_root: Path, contract: Mapping[str, Any], storage_root: Path
) -> tuple[pd.DataFrame, dict[str, Any]]:
    locked = contract["intraday_macro_source_lock"]
    report_path = (phase1_root / str(locked["report_path"])).resolve()
    if _sha256_file(report_path) != str(locked["report_sha256"]):
        raise IntradayCrossassetEventCensusError("intraday macro report hash mismatch")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if str(report["classification"]) != str(locked["required_classification"]):
        raise IntradayCrossassetEventCensusError("intraday macro source is not valid")
    manifest_path = (storage_root / str(locked["manifest_path"])).resolve()
    if _sha256_file(manifest_path) != str(locked["manifest_sha256"]):
        raise IntradayCrossassetEventCensusError(
            "intraday macro manifest hash mismatch"
        )
    feature_path = (storage_root / str(locked["feature_path"])).resolve()
    if _sha256_file(feature_path) != str(locked["feature_sha256"]):
        raise IntradayCrossassetEventCensusError("intraday macro feature hash mismatch")
    frame = (
        pd.read_parquet(feature_path).sort_values("timestamp_ms").reset_index(drop=True)
    )
    if len(frame) != int(locked["feature_rows"]):
        raise IntradayCrossassetEventCensusError("intraday macro feature row mismatch")
    timestamps = frame["timestamp_ms"].to_numpy(dtype=np.int64)
    if np.any(np.diff(timestamps) <= 0):
        raise IntradayCrossassetEventCensusError(
            "intraday macro timestamps are invalid"
        )
    return frame, report


def build_m15_features(
    xau: pd.DataFrame, macro: pd.DataFrame, contract: Mapping[str, Any]
) -> pd.DataFrame:
    xau_columns = [
        "timestamp_ms",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
        "mid_open",
        "mid_high",
        "mid_low",
        "mid_close",
        "atr",
    ]
    macro_columns = [
        "timestamp_ms",
        "dollaridxusd_mid_open",
        "dollaridxusd_mid_high",
        "dollaridxusd_mid_low",
        "dollaridxusd_mid_close",
        "ustbondtrusd_mid_open",
        "ustbondtrusd_mid_high",
        "ustbondtrusd_mid_low",
        "ustbondtrusd_mid_close",
        "dollaridxusd_available",
        "ustbondtrusd_available",
    ]
    work = xau[xau_columns].copy()
    work["source_last_index"] = np.arange(len(xau), dtype=np.int64)
    work = work.merge(
        macro[macro_columns], on="timestamp_ms", how="left", validate="one_to_one"
    )
    for column in ("dollaridxusd_available", "ustbondtrusd_available"):
        work[column] = work[column].fillna(False).astype(bool)
    start = _parse_ms(contract["windows"]["train_start_utc"])
    end = _parse_ms(contract["windows"]["exam_end_exclusive_utc"])
    work = work.loc[
        (work["timestamp_ms"] >= start) & (work["timestamp_ms"] < end)
    ].copy()
    work["m15_bucket"] = work["timestamp_ms"] - work["timestamp_ms"] % M15_WIDTH_MS
    grouped = work.groupby("m15_bucket", sort=True)
    bars = grouped.agg(
        source_bar_count=("timestamp_ms", "size"),
        first_timestamp_ms=("timestamp_ms", "min"),
        last_timestamp_ms=("timestamp_ms", "max"),
        source_last_index=("source_last_index", "last"),
        bid_open=("bid_open", "first"),
        bid_high=("bid_high", "max"),
        bid_low=("bid_low", "min"),
        bid_close=("bid_close", "last"),
        ask_open=("ask_open", "first"),
        ask_high=("ask_high", "max"),
        ask_low=("ask_low", "min"),
        ask_close=("ask_close", "last"),
        mid_open=("mid_open", "first"),
        mid_high=("mid_high", "max"),
        mid_low=("mid_low", "min"),
        mid_close=("mid_close", "last"),
        atr=("atr", "last"),
        dollar_open=("dollaridxusd_mid_open", "first"),
        dollar_high=("dollaridxusd_mid_high", "max"),
        dollar_low=("dollaridxusd_mid_low", "min"),
        dollar_close=("dollaridxusd_mid_close", "last"),
        bond_open=("ustbondtrusd_mid_open", "first"),
        bond_high=("ustbondtrusd_mid_high", "max"),
        bond_low=("ustbondtrusd_mid_low", "min"),
        bond_close=("ustbondtrusd_mid_close", "last"),
        dollar_available=("dollaridxusd_available", "all"),
        bond_available=("ustbondtrusd_available", "all"),
    ).reset_index(names="timestamp_ms")
    complete = (
        (bars["source_bar_count"] == 3)
        & (bars["first_timestamp_ms"] == bars["timestamp_ms"])
        & (bars["last_timestamp_ms"] == bars["timestamp_ms"] + 2 * BAR_WIDTH_MS)
    )
    bars = bars.loc[complete].reset_index(drop=True)
    bars["decision_timestamp_ms"] = bars["timestamp_ms"] + M15_WIDTH_MS
    bars["decision_time_utc"] = pd.to_datetime(
        bars["decision_timestamp_ms"], unit="ms", utc=True
    )
    bars["decision_hour_utc"] = bars["decision_time_utc"].dt.hour
    bars["decision_date_utc"] = bars["decision_time_utc"].dt.strftime("%Y-%m-%d")
    bars["dollar_available"] = bars["dollar_available"].astype(bool)
    bars["bond_available"] = bars["bond_available"].astype(bool)
    _add_standardized_source_returns(bars, "dollar", contract)
    _add_standardized_source_returns(bars, "bond", contract)
    for lookback in contract["causal_features"]["xau_return_lookbacks_m15_bars"]:
        n = int(lookback)
        contiguous = (
            bars["timestamp_ms"] - bars["timestamp_ms"].shift(n) == n * M15_WIDTH_MS
        )
        bars[f"xau_return_{n}_atr"] = (
            (bars["mid_close"] - bars["mid_close"].shift(n)) / bars["atr"]
        ).where(contiguous & (bars["atr"] > 0))
    body_range = bars["mid_high"] - bars["mid_low"]
    bars["body_fraction"] = (
        (bars["mid_close"] - bars["mid_open"]).abs() / body_range.replace(0.0, np.nan)
    ).fillna(0.0)
    start_hour = int(contract["aggregation"]["decision_start_hour_utc_inclusive"])
    end_hour = int(contract["aggregation"]["decision_end_hour_utc_exclusive"])
    bars["inside_decision_session"] = bars["decision_hour_utc"].between(
        start_hour, end_hour - 1
    )
    bars["joined_source_available"] = bars["dollar_available"] & bars["bond_available"]
    required = ["dollar_z_4", "bond_z_4", "xau_return_1_atr", "xau_return_4_atr", "atr"]
    bars["base_feature_available"] = (
        bars[required].replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
        & bars["inside_decision_session"]
    )
    return bars.replace([np.inf, -np.inf], np.nan)


def _add_standardized_source_returns(
    frame: pd.DataFrame, prefix: str, contract: Mapping[str, Any]
) -> None:
    close = frame[f"{prefix}_close"]
    available = frame[f"{prefix}_available"].astype(bool)
    contiguous_one = (
        frame["timestamp_ms"] - frame["timestamp_ms"].shift(1) == M15_WIDTH_MS
    )
    one_bar = np.log(close / close.shift(1)).where(
        contiguous_one & available & available.shift(1, fill_value=False)
    )
    feature_contract = contract["causal_features"]
    volatility = (
        one_bar.rolling(
            int(feature_contract["source_volatility_window_m15_bars"]),
            min_periods=int(feature_contract["source_volatility_minimum_periods"]),
        )
        .std(ddof=0)
        .shift(1)
    )
    frame[f"{prefix}_prior_volatility"] = volatility
    for lookback in feature_contract["source_return_lookbacks_m15_bars"]:
        n = int(lookback)
        contiguous = (
            frame["timestamp_ms"] - frame["timestamp_ms"].shift(n) == n * M15_WIDTH_MS
        )
        available_window = (
            available.astype(int).rolling(n + 1, min_periods=n + 1).sum() == n + 1
        )
        raw_return = np.log(close / close.shift(n))
        frame[f"{prefix}_log_return_{n}"] = raw_return.where(
            contiguous & available_window
        )
        frame[f"{prefix}_z_{n}"] = (raw_return / (volatility * math.sqrt(n))).where(
            contiguous & available_window & (volatility > 0)
        )


def generate_events(
    frame: pd.DataFrame, contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    maximum_per_day = int(
        contract["event_controls"]["maximum_events_per_family_direction_utc_day"]
    )
    for family in contract["event_families"]:
        lookback = int(family["source_lookback_m15_bars"])
        for direction, sign in (("LONG", 1.0), ("SHORT", -1.0)):
            dollar = -sign * frame[f"dollar_z_{lookback}"]
            bond = sign * frame[f"bond_z_{lookback}"]
            xau_15 = sign * frame["xau_return_1_atr"]
            mask = frame["inside_decision_session"].astype(bool)
            if "minimum_directional_dollar_z" in family:
                mask &= dollar >= float(family["minimum_directional_dollar_z"])
            if "minimum_directional_bond_z" in family:
                mask &= bond >= float(family["minimum_directional_bond_z"])
            mask &= xau_15 >= float(family["minimum_directional_xau_return_15m_atr"])
            if "minimum_directional_xau_return_60m_atr" in family:
                xau_60 = sign * frame["xau_return_4_atr"]
                mask &= xau_60 >= float(
                    family["minimum_directional_xau_return_60m_atr"]
                )
                mask &= xau_60 <= float(
                    family["maximum_directional_xau_return_60m_atr"]
                )
            finite = np.isfinite(dollar) & np.isfinite(bond) & np.isfinite(xau_15)
            mask &= finite & (frame["atr"] > 0)
            cooldown_ms = int(family["cooldown_minutes_per_direction"]) * 60_000
            last_decision = -(10**18)
            day_count: Counter[str] = Counter()
            for index in np.flatnonzero(mask.fillna(False).to_numpy(dtype=bool)):
                row = frame.iloc[index]
                decision = int(row["decision_timestamp_ms"])
                day = str(row["decision_date_utc"])
                if (
                    decision - last_decision < cooldown_ms
                    or day_count[day] >= maximum_per_day
                ):
                    continue
                event = _make_event(
                    row,
                    family,
                    direction,
                    dollar.iloc[index],
                    bond.iloc[index],
                    contract,
                )
                if event is None:
                    continue
                output.append(event)
                last_decision = decision
                day_count[day] += 1
    return sorted(
        output,
        key=lambda row: (
            int(row["decision_timestamp_ms"]),
            str(row["family_id"]),
            str(row["direction"]),
        ),
    )


def _make_event(
    row: Mapping[str, Any],
    family: Mapping[str, Any],
    direction: str,
    directional_dollar_z: float,
    directional_bond_z: float,
    contract: Mapping[str, Any],
) -> dict[str, Any] | None:
    decision = int(row["decision_timestamp_ms"])
    split = _split(decision, contract)
    if split is None:
        return None
    _, segment_end = _segment_bounds(split, contract)
    hold_hours = int(contract["execution"]["maximum_hold_hours"])
    if decision + hold_hours * HOUR_MS > segment_end:
        return None
    identity = f"{family['family_id']}|{decision}|{direction}"
    return {
        "event_id": hashlib.sha256(identity.encode("ascii")).hexdigest(),
        "family_id": str(family["family_id"]),
        "mechanism": str(family["mechanism"]),
        "direction": direction,
        "split": split,
        "signal_m15_start_utc": _iso_ms(int(row["timestamp_ms"])),
        "decision_timestamp_ms": decision,
        "decision_time_utc": _iso_ms(decision),
        "source_last_index": int(row["source_last_index"]),
        "atr": float(row["atr"]),
        "signal_open": float(row["mid_open"]),
        "signal_high": float(row["mid_high"]),
        "signal_low": float(row["mid_low"]),
        "signal_close": float(row["mid_close"]),
        "body_fraction": float(row["body_fraction"]),
        "directional_dollar_z": float(directional_dollar_z),
        "directional_bond_z": float(directional_bond_z),
        "directional_xau_return_15m_atr": (1.0 if direction == "LONG" else -1.0)
        * float(row["xau_return_1_atr"]),
        "directional_xau_return_60m_atr": (1.0 if direction == "LONG" else -1.0)
        * float(row["xau_return_4_atr"]),
    }


def validate_events(events: Sequence[Mapping[str, Any]]) -> None:
    ids = [str(row["event_id"]) for row in events]
    if len(ids) != len(set(ids)):
        raise IntradayCrossassetEventCensusError("duplicate crossasset event IDs")
    ordered = sorted(
        events,
        key=lambda row: (
            int(row["decision_timestamp_ms"]),
            str(row["family_id"]),
            str(row["direction"]),
        ),
    )
    if list(events) != ordered:
        raise IntradayCrossassetEventCensusError(
            "crossasset events are non-chronological"
        )


def label_event(
    xau: pd.DataFrame, event: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Any]:
    identity = _label_identity(event)
    entry_index = int(event["source_last_index"]) + 1
    if entry_index >= len(xau):
        return _empty_label(identity, "UNRESOLVED", "NEXT_BAR_UNAVAILABLE")
    entry_row = xau.iloc[entry_index]
    decision = int(event["decision_timestamp_ms"])
    if int(entry_row["timestamp_ms"]) != decision:
        return _empty_label(identity, "INELIGIBLE", "NEXT_BAR_NOT_CONTIGUOUS")
    direction = str(event["direction"])
    entry_price = float(
        entry_row["ask_open"] if direction == "LONG" else entry_row["bid_open"]
    )
    native_spread = float(entry_row["ask_open"] - entry_row["bid_open"])
    execution = contract["execution"]
    atr = float(event["atr"])
    buffer = float(execution["structural_signal_bar_buffer_atr"]) * atr
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
    stop_distance = max(
        float(execution["minimum_initial_stop_distance_price"]),
        float(execution["stop_atr"]) * atr,
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
    maximum_cost_r = float(execution["maximum_total_stressed_entry_cost_r"])
    if cost_r > maximum_cost_r and not math.isclose(
        cost_r, maximum_cost_r, rel_tol=1e-12, abs_tol=1e-12
    ):
        return _empty_label(identity, "INELIGIBLE", "STRESSED_ENTRY_COST_R")
    horizon_end = decision + int(execution["maximum_hold_hours"]) * HOUR_MS
    timestamps = xau["timestamp_ms"].to_numpy(dtype=np.int64)
    end_index = int(np.searchsorted(timestamps, horizon_end, side="left") - 1)
    if end_index < entry_index:
        return _empty_label(identity, "UNRESOLVED", "HORIZON_UNAVAILABLE")
    _, segment_end = _segment_bounds(str(event["split"]), contract)
    if horizon_end > segment_end:
        return _empty_label(identity, "UNRESOLVED", "SEGMENT_HORIZON_UNAVAILABLE")
    stop = (
        entry_price - stop_distance
        if direction == "LONG"
        else entry_price + stop_distance
    )
    target_distance = float(execution["target_r"]) * stop_distance
    target = (
        entry_price + target_distance
        if direction == "LONG"
        else entry_price - target_distance
    )
    exit_index = end_index
    exit_price: float | None = None
    exit_reason = "TIMEOUT"
    for index in range(entry_index, end_index + 1):
        row = xau.iloc[index]
        if direction == "LONG":
            if float(row["bid_open"]) <= stop:
                exit_index, exit_price, exit_reason = (
                    index,
                    float(row["bid_open"]),
                    "STOP",
                )
                break
            if float(row["bid_open"]) >= target:
                exit_index, exit_price, exit_reason = (
                    index,
                    float(row["bid_open"]),
                    "TARGET",
                )
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
                exit_index, exit_price, exit_reason = (
                    index,
                    float(row["ask_open"]),
                    "TARGET",
                )
                break
            if float(row["ask_high"]) >= stop:
                exit_index, exit_price, exit_reason = index, stop, "STOP"
                break
            if float(row["ask_low"]) <= target:
                exit_index, exit_price, exit_reason = index, target, "TARGET"
                break
    if exit_price is None:
        row = xau.iloc[exit_index]
        exit_price = float(
            row["bid_close"] if direction == "LONG" else row["ask_close"]
        )
    move = exit_price - entry_price if direction == "LONG" else entry_price - exit_price
    gross_pnl = move * quantity
    exit_time_ms = int(xau.iloc[exit_index]["timestamp_ms"]) + BAR_WIDTH_MS
    duration_hours = (exit_time_ms - decision) / HOUR_MS
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
        "entry_time_utc": _iso_ms(decision),
        "exit_time_utc": _iso_ms(exit_time_ms),
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
            "atr",
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


def evaluate_chronologically(
    *,
    xau: pd.DataFrame,
    m15: pd.DataFrame,
    events: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
    contract_file: Path,
    macro_report: Mapping[str, Any],
    broker_report: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    family_ids = [str(row["family_id"]) for row in contract["event_families"]]
    keys = [
        (family, direction) for family in family_ids for direction in ("LONG", "SHORT")
    ]
    source_days = _source_days(m15, contract)
    hypotheses: dict[str, dict[str, Any]] = {
        f"{family}:{direction}": {} for family, direction in keys
    }
    opened = set(keys)
    labels: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    survivors: dict[str, list[str]] = {}
    for segment, gate_key in (
        ("train", "train_gates"),
        ("validation", "validation_gates"),
        ("internal_test", "internal_test_gates"),
        ("exam", "exam_gates"),
    ):
        next_opened: set[tuple[str, str]] = set()
        survivors[segment] = []
        for family, direction in keys:
            name = f"{family}:{direction}"
            is_open = (family, direction) in opened
            if not is_open:
                hypotheses[name][segment] = {
                    "opened_for_decision": False,
                    "metrics": None,
                    "gates": None,
                    "passed": False,
                }
                continue
            selected_events = [
                row
                for row in events
                if row["split"] == segment
                and row["family_id"] == family
                and row["direction"] == direction
            ]
            segment_labels = [
                label_event(xau, event, contract) for event in selected_events
            ]
            labels.extend(segment_labels)
            resolved = [row for row in segment_labels if row["status"] == "RESOLVED"]
            metrics = policy_metrics(
                resolved,
                source_days[segment],
                bootstrap_samples=int(
                    contract["selection"]["calendar_month_bootstrap_samples"]
                )
                if segment == "train"
                else 0,
                bootstrap_seed=_bootstrap_seed(contract, family, direction),
            )
            gates = policy_gates(metrics, contract["selection"][gate_key])
            passed = all(gates.values())
            hypotheses[name][segment] = {
                "opened_for_decision": True,
                "candidate_events": len(selected_events),
                "label_status_counts": dict(
                    Counter(row["status"] for row in segment_labels)
                ),
                "metrics": metrics,
                "gates": gates,
                "passed": passed,
            }
            metric_rows.append(
                {
                    "family_id": family,
                    "direction": direction,
                    "segment": segment,
                    **metrics,
                    "passes": passed,
                    "failed_gates": "|".join(
                        key for key, value in gates.items() if not value
                    ),
                }
            )
            if passed:
                next_opened.add((family, direction))
                survivors[segment].append(name)
        opened = next_opened
    opened_events = len(labels)
    labeled = sum(row["status"] != "UNRESOLVED" for row in labels)
    label_share = labeled / opened_events if opened_events else 1.0
    xau_days = _active_xau_days(xau, contract)
    joined_days = int(
        m15.loc[
            m15["inside_decision_session"] & m15["joined_source_available"],
            "decision_date_utc",
        ].nunique()
    )
    joined_share = joined_days / xau_days if xau_days else 0.0
    quality_config = contract["quality_gates"]
    quality = {
        "all_source_hashes_and_rows_match": True,
        "broker_cost_report_hash_and_values_match": str(broker_report["classification"])
        == str(contract["broker_cost_source_lock"]["required_classification"]),
        "joined_source_day_share_ge_minimum": joined_share
        >= float(quality_config["minimum_joined_source_day_share"]),
        "resolved_or_ineligible_event_share_ge_minimum": label_share
        >= float(quality_config["minimum_resolved_or_ineligible_event_share"]),
        "event_ids_unique": len({row["event_id"] for row in events}) == len(events),
        "events_chronological": list(events)
        == sorted(
            events,
            key=lambda row: (
                row["decision_timestamp_ms"],
                row["family_id"],
                row["direction"],
            ),
        ),
        "features_are_causal": True,
    }
    classification = _classification(quality, survivors)
    final_survivors = survivors["exam"]
    resolved_count = sum(row["status"] == "RESOLVED" for row in labels)
    trainability_config = contract["downstream_label_trainability"]
    has_long = any(name.endswith(":LONG") for name in final_survivors)
    has_short = any(name.endswith(":SHORT") for name in final_survivors)
    trainability_gates = {
        "resolved_candidates_ge_minimum": resolved_count
        >= int(trainability_config["minimum_resolved_candidate_events"]),
        "final_survivors_ge_minimum": len(final_survivors)
        >= int(trainability_config["minimum_final_research_survivors"]),
        "long_and_short_final_survivors": has_long and has_short,
    }
    report = {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "source_locks": {
            "xau_feature_sha256": str(contract["xau_source_lock"]["feature_sha256"]),
            "intraday_macro_feature_sha256": str(
                contract["intraday_macro_source_lock"]["feature_sha256"]
            ),
            "intraday_macro_report_sha256": str(
                contract["intraday_macro_source_lock"]["report_sha256"]
            ),
            "intraday_macro_classification": str(macro_report["classification"]),
            "broker_cost_report_sha256": str(
                contract["broker_cost_source_lock"]["report_sha256"]
            ),
        },
        "m15_rows": len(m15),
        "source_days": source_days,
        "coverage": {
            "xau_active_days": xau_days,
            "joined_intraday_source_days": joined_days,
            "joined_source_day_share": joined_share,
        },
        "event_count": len(events),
        "event_counts_by_family_direction_split": dict(
            Counter(
                f"{row['family_id']}:{row['direction']}:{row['split']}"
                for row in events
            )
        ),
        "opened_label_count": opened_events,
        "resolved_label_count": resolved_count,
        "label_status_counts": dict(Counter(row["status"] for row in labels)),
        "resolved_or_ineligible_label_share": label_share,
        "hypotheses": hypotheses,
        "survivors": survivors,
        "quality_gates": quality,
        "label_trainability": {
            "gates": trainability_gates,
            "passes": all(trainability_gates.values()),
            "model_training_authorized": False,
        },
        "authorization": {
            **contract["authorization"],
            "model_training_authorized": False,
            "strategy_promotion_authorized": False,
            "demo_or_live_authorized": False,
        },
        "decision": _decision(classification),
    }
    return report, labels, metric_rows


def _source_days(frame: pd.DataFrame, contract: Mapping[str, Any]) -> dict[str, int]:
    output = {}
    for split in ("train", "validation", "internal_test", "exam"):
        start, end = _segment_bounds(split, contract)
        mask = (
            (frame["decision_timestamp_ms"] >= start)
            & (frame["decision_timestamp_ms"] < end)
            & frame["base_feature_available"]
        )
        output[split] = int(frame.loc[mask, "decision_date_utc"].nunique())
    return output


def _active_xau_days(xau: pd.DataFrame, contract: Mapping[str, Any]) -> int:
    start = _parse_ms(contract["windows"]["train_start_utc"])
    end = _parse_ms(contract["windows"]["exam_end_exclusive_utc"])
    timestamps = pd.to_datetime(
        xau.loc[
            (xau["timestamp_ms"] >= start) & (xau["timestamp_ms"] < end), "timestamp_ms"
        ],
        unit="ms",
        utc=True,
    )
    return int(timestamps.dt.floor("D").nunique())


def _split(timestamp_ms: int, contract: Mapping[str, Any]) -> str | None:
    windows = contract["windows"]
    boundaries = (
        ("train", windows["train_start_utc"], windows["train_end_exclusive_utc"]),
        (
            "validation",
            windows["train_end_exclusive_utc"],
            windows["validation_end_exclusive_utc"],
        ),
        (
            "internal_test",
            windows["validation_end_exclusive_utc"],
            windows["internal_test_end_exclusive_utc"],
        ),
        (
            "exam",
            windows["internal_test_end_exclusive_utc"],
            windows["exam_end_exclusive_utc"],
        ),
    )
    for name, start, end in boundaries:
        if _parse_ms(start) <= timestamp_ms < _parse_ms(end):
            return name
    return None


def _segment_bounds(split: str, contract: Mapping[str, Any]) -> tuple[int, int]:
    windows = contract["windows"]
    mapping = {
        "train": (windows["train_start_utc"], windows["train_end_exclusive_utc"]),
        "validation": (
            windows["train_end_exclusive_utc"],
            windows["validation_end_exclusive_utc"],
        ),
        "internal_test": (
            windows["validation_end_exclusive_utc"],
            windows["internal_test_end_exclusive_utc"],
        ),
        "exam": (
            windows["internal_test_end_exclusive_utc"],
            windows["exam_end_exclusive_utc"],
        ),
    }
    start, end = mapping[split]
    return _parse_ms(start), _parse_ms(end)


def _bootstrap_seed(contract: Mapping[str, Any], family: str, direction: str) -> int:
    identity = f"{contract['selection']['bootstrap_seed']}|{family}|{direction}"
    return int(hashlib.sha256(identity.encode("ascii")).hexdigest()[:8], 16)


def _classification(
    quality: Mapping[str, bool], survivors: Mapping[str, Sequence[str]]
) -> str:
    if not all(quality.values()):
        return "INTRADAY_CROSSASSET_EVENT_CENSUS_INVALID"
    if not survivors["train"]:
        return "INTRADAY_CROSSASSET_NO_TRAIN_SURVIVOR"
    if not survivors["validation"]:
        return "INTRADAY_CROSSASSET_NO_VALIDATION_SURVIVOR"
    if not survivors["internal_test"]:
        return "INTRADAY_CROSSASSET_NO_INTERNAL_TEST_SURVIVOR"
    if not survivors["exam"]:
        return "INTRADAY_CROSSASSET_NO_EXAM_SURVIVOR"
    return "INTRADAY_CROSSASSET_RESEARCH_SURVIVOR"


def _decision(classification: str) -> str:
    if classification == "INTRADAY_CROSSASSET_RESEARCH_SURVIVOR":
        return "Replay final research survivors with exact ticks and shared-account controls; no demo action is authorized."
    if classification == "INTRADAY_CROSSASSET_EVENT_CENSUS_INVALID":
        return "Fix source, causality, or label-quality failures before interpreting economic results."
    return (
        "Reject this fixed crossasset branch without same-iteration threshold repair."
    )


def render_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Intraday Cross-Asset Event Census V1 Report",
        "",
        f"Classification: `{report['classification']}`",
        "",
        f"Events: `{report['event_count']}`. Resolved opened labels: `{report['resolved_label_count']}`.",
        f"Joined source-day share: `{report['coverage']['joined_source_day_share']:.4%}`.",
        "",
        "## Chronological Results",
        "",
    ]
    for name, result in report["hypotheses"].items():
        train = result["train"]
        if train["metrics"] is None:
            continue
        metrics = train["metrics"]
        lines.append(
            f"- {name} train: {metrics['events']} events, PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{train['passed']}`."
        )
        for segment in ("validation", "internal_test", "exam"):
            payload = result[segment]
            if not payload["opened_for_decision"]:
                continue
            metrics = payload["metrics"]
            lines.append(
                f"- {name} {segment}: {metrics['events']} events, {metrics['events_per_source_day']:.3f}/day, PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{payload['passed']}`."
            )
    lines.extend(
        [
            "",
            f"Final research survivors: `{report['survivors']['exam']}`.",
            f"Label trainability passes: `{report['label_trainability']['passes']}`.",
            "",
            "## Decision",
            "",
            str(report["decision"]),
            "",
            "No model training, Python demo prediction, EA consumption, or broker action is authorized.",
            "",
        ]
    )
    return "\n".join(lines)
