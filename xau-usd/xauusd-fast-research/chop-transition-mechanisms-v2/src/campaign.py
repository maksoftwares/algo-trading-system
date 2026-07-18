from __future__ import annotations

import hashlib
import itertools
import json
from typing import Any, Callable, Mapping

import numpy as np
import pandas as pd


MECHANICS: dict[str, tuple[str, ...]] = {
    "CHOP": (
        "CHOP_ASIAN_FALSE_BREAK_FADE",
        "CHOP_ASIAN_EDGE_ROTATION",
        "CHOP_ANCHORED_VWAP_REVERSION",
        "CHOP_OVERNIGHT_INVENTORY_REVERSAL",
        "CHOP_WEAK_BREAKOUT_ANTISIGNAL",
    ),
    "TRANSITION": (
        "TRANS_ANCESTRY_PULLBACK_CONTINUE",
        "TRANS_ANCESTRY_FAILURE_FADE",
        "TRANS_FIRST_BLOCK_IMPULSE",
        "TRANS_EXHAUSTED_MOMENTUM_ANTISIGNAL",
        "TRANS_RANGE_REENTRY_FADE",
    ),
}


def _space(**values: list[Any]) -> list[dict[str, Any]]:
    keys = tuple(values)
    return [
        dict(zip(keys, combination, strict=True))
        for combination in itertools.product(*(values[key] for key in keys))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    stops = [0.8, 1.0, 1.25, 1.5, 2.0]
    liquid_hours = ["POST_ASIA", "LONDON", "LONDON_NY", "NEW_YORK"]
    if mechanic == "CHOP_ASIAN_FALSE_BREAK_FADE":
        return _space(
            sweep_atr=[0.0, 0.03, 0.05, 0.1, 0.15],
            close_back_atr=[0.0, 0.03, 0.05, 0.1],
            wick_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            asia_range_atr_min=[0.4, 0.6, 0.8, 1.0],
            asia_range_atr_max=[1.5, 2.0, 3.0, 4.0],
            hour_window=liquid_hours,
            hold_hours=[2, 4, 6, 8, 12],
            stop_atr=stops,
        )
    if mechanic == "CHOP_ASIAN_EDGE_ROTATION":
        return _space(
            edge_fraction=[0.05, 0.1, 0.15, 0.2, 0.25],
            asia_range_atr_min=[0.4, 0.6, 0.8, 1.0],
            asia_range_atr_max=[1.5, 2.0, 3.0, 4.0],
            require_confirmation=[False, True],
            hour_window=liquid_hours,
            hold_hours=[2, 4, 6, 8, 12],
            stop_atr=stops,
        )
    if mechanic == "CHOP_ANCHORED_VWAP_REVERSION":
        return _space(
            deviation_atr=[0.25, 0.4, 0.6, 0.8, 1.0, 1.25],
            minimum_day_bars=[4, 6, 8, 10],
            maximum_day_displacement_atr=[1.0, 1.5, 2.0, 3.0],
            require_confirmation=[False, True],
            hour_window=["ALL", *liquid_hours],
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
        )
    if mechanic == "CHOP_OVERNIGHT_INVENTORY_REVERSAL":
        return _space(
            inventory_atr=[0.25, 0.4, 0.6, 0.8, 1.0, 1.25],
            vwap_deviation_atr=[0.0, 0.15, 0.3, 0.5],
            body_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=["LONDON", "LONDON_NY"],
            hold_hours=[2, 4, 6, 8, 12],
            stop_atr=stops,
        )
    if mechanic == "CHOP_WEAK_BREAKOUT_ANTISIGNAL":
        return _space(
            lookback=[4, 6, 8, 12, 18, 24],
            breakout_atr=[0.0, 0.03, 0.05, 0.1, 0.15],
            body_max=[0.35, 0.5, 0.65, 0.8],
            efficiency_max=[0.2, 0.3, 0.4, 0.5],
            hour_window=["ALL", *liquid_hours],
            hold_hours=[1, 2, 4, 6, 8, 12],
            stop_atr=stops,
        )
    if mechanic == "TRANS_ANCESTRY_PULLBACK_CONTINUE":
        return _space(
            transition_age_max=[4, 8, 12, 20, 32, 48],
            touch_atr=[-0.1, 0.0, 0.1, 0.2, 0.35, 0.5],
            body_min=[0.1, 0.2, 0.3, 0.4],
            slope_atr_min=[0.0, 0.05, 0.1, 0.15],
            hour_window=["ALL", *liquid_hours],
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "TRANS_ANCESTRY_FAILURE_FADE":
        return [
            params
            for params in _space(
            transition_age_min=[1, 4, 8, 12],
            transition_age_max=[8, 12, 20, 32, 48],
            momentum_bars=[1, 2, 3, 4, 6, 8],
            failure_momentum_atr=[0.1, 0.2, 0.35, 0.5, 0.75],
            body_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=["ALL", *liquid_hours],
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
            )
            if int(params["transition_age_min"])
            <= int(params["transition_age_max"])
        ]
    if mechanic == "TRANS_FIRST_BLOCK_IMPULSE":
        return _space(
            source=["ANY", "ANY_TREND", "COMPRESSION", "CHOP"],
            transition_age_max=[4, 8, 12],
            momentum_bars=[1, 2, 3, 4, 6],
            momentum_atr=[0.15, 0.25, 0.4, 0.6, 0.8],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=["ALL", *liquid_hours],
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
        )
    if mechanic == "TRANS_EXHAUSTED_MOMENTUM_ANTISIGNAL":
        return _space(
            source=["ANY", "ANY_TREND", "COMPRESSION", "CHOP"],
            transition_age_max=[8, 12, 20, 32, 48],
            momentum_bars=[2, 3, 4, 6, 8, 12],
            momentum_atr=[0.35, 0.5, 0.75, 1.0, 1.25],
            rsi_period=[2, 3, 4, 6, 9],
            rsi_tail=[10, 15, 20, 25, 30, 35],
            hour_window=["ALL", *liquid_hours],
            hold_hours=[2, 4, 6, 8, 12],
            stop_atr=stops,
        )
    if mechanic == "TRANS_RANGE_REENTRY_FADE":
        return _space(
            source=["ANY", "ANY_TREND", "COMPRESSION", "CHOP"],
            transition_age_max=[8, 12, 20, 32, 48],
            lookback=[4, 6, 8, 12, 18, 24],
            sweep_atr=[0.0, 0.03, 0.05, 0.1, 0.15],
            close_back_atr=[0.0, 0.03, 0.05, 0.1],
            wick_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=["ALL", *liquid_hours],
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
        )
    raise KeyError(mechanic)


def generate_manifest(selection: Mapping[str, Any]) -> pd.DataFrame:
    variants_per_mechanic = int(selection["variants_per_mechanic"])
    attempt = int(selection["attempt_first"])
    rows: list[dict[str, Any]] = []
    for owner, mechanics in MECHANICS.items():
        for mechanic in mechanics:
            candidates = sorted(
                parameter_space(mechanic),
                key=lambda params: hashlib.sha256(
                    f"{owner}|{mechanic}|{json.dumps(params, sort_keys=True)}".encode(
                        "ascii"
                    )
                ).hexdigest(),
            )[:variants_per_mechanic]
            if len(candidates) != variants_per_mechanic:
                raise ValueError(f"Insufficient parameter space for {mechanic}")
            for params in candidates:
                canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
                variant_id = hashlib.sha256(
                    f"{owner}|{mechanic}|{canonical}".encode("ascii")
                ).hexdigest()[:16]
                rows.append(
                    {
                        "attempt_no": attempt,
                        "variant_id": variant_id,
                        "regime_owner": owner,
                        "mechanic": mechanic,
                        "parameters_json": canonical,
                    }
                )
                attempt += 1
    result = pd.DataFrame(rows)
    if len(result) != int(selection["total_attempts"]):
        raise ValueError("Attempt count does not match contract")
    if int(result["attempt_no"].iat[-1]) != int(selection["attempt_last"]):
        raise ValueError("Attempt-number boundary does not match contract")
    if result["variant_id"].duplicated().any():
        raise ValueError("Duplicate variant IDs")
    return result


def add_changed_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True).copy()
    timestamp = pd.to_datetime(result["timestamp_utc"], utc=True)
    day = timestamp.dt.normalize()
    hour = timestamp.dt.hour
    result["utc_day"] = day
    result["hour"] = hour
    grouped = result.groupby("utc_day", sort=False)
    result["day_bar_number"] = grouped.cumcount() + 1
    result["day_open"] = grouped["mid_open"].transform("first")

    typical = (result["mid_high"] + result["mid_low"] + result["mid_close"]) / 3.0
    weight = result.get("tick_count", pd.Series(1.0, index=result.index)).astype(float).clip(lower=1.0)
    weighted = typical * weight
    cumulative_weight = weight.groupby(day, sort=False).cumsum()
    result["anchored_vwap"] = weighted.groupby(day, sort=False).cumsum() / cumulative_weight
    result["vwap_deviation_atr"] = (result["mid_close"] - result["anchored_vwap"]) / result["atr14"]
    result["day_displacement_atr"] = (result["mid_close"] - result["day_open"]) / result["atr14"]

    asian = hour.between(0, 5)
    asian_high_partial = result["mid_high"].where(asian).groupby(day, sort=False).cummax()
    asian_low_partial = result["mid_low"].where(asian).groupby(day, sort=False).cummin()
    result["asian_high"] = asian_high_partial.groupby(day, sort=False).ffill()
    result["asian_low"] = asian_low_partial.groupby(day, sort=False).ffill()
    result["asian_close"] = result["mid_close"].where(asian).groupby(day, sort=False).ffill()
    result["asian_range_atr"] = (result["asian_high"] - result["asian_low"]) / result["atr14"]
    result["asian_inventory_atr"] = (result["asian_close"] - result["day_open"]) / result["atr14"]

    resolved = result["regime"].isin(("TREND_UP", "TREND_DOWN", "COMPRESSION", "CHOP"))
    result["last_resolved_regime"] = result["regime"].where(resolved).ffill()
    result["ancestry_direction"] = result["last_resolved_regime"].map(
        {"TREND_UP": 1, "TREND_DOWN": -1}
    ).fillna(0).astype(int)
    run = result["regime"].ne(result["regime"].shift(1)).cumsum()
    age = result.groupby(run, sort=False).cumcount() + 1
    result["transition_age_h1"] = age.where(result["regime"].eq("TRANSITION_UNKNOWN"), 0).astype(int)
    return result


def prepare_features(
    h1: pd.DataFrame,
    h4: pd.DataFrame,
    config: Mapping[str, Any],
    adaptive_module: Any,
    regime_module: Any,
    base_module: Any,
) -> pd.DataFrame:
    return add_changed_features(
        base_module.prepare_features(h1, h4, config, adaptive_module, regime_module)
    )


def _hour_mask(frame: pd.DataFrame, name: str) -> pd.Series:
    hour = frame["hour"]
    if name == "ALL":
        return pd.Series(True, index=frame.index)
    if name == "POST_ASIA":
        return hour.between(6, 18)
    if name == "LONDON":
        return hour.between(6, 11)
    if name == "LONDON_NY":
        return hour.between(6, 17)
    if name == "NEW_YORK":
        return hour.between(12, 18)
    raise KeyError(name)


def _source_mask(frame: pd.DataFrame, source: str) -> pd.Series:
    ancestor = frame["last_resolved_regime"]
    if source == "ANY":
        return pd.Series(True, index=frame.index)
    if source == "ANY_TREND":
        return ancestor.isin(("TREND_UP", "TREND_DOWN"))
    if source in ("TREND_UP", "TREND_DOWN", "COMPRESSION", "CHOP"):
        return ancestor.eq(source)
    raise KeyError(source)


def _break_direction(frame: pd.DataFrame, lookback: int, breakout_atr: float) -> pd.Series:
    up = frame["mid_close"].gt(frame[f"prior_high_{lookback}"] + breakout_atr * frame["atr14"])
    down = frame["mid_close"].lt(frame[f"prior_low_{lookback}"] - breakout_atr * frame["atr14"])
    return pd.Series(np.select([up, down], [1, -1], default=0), index=frame.index, dtype=int)


def _false_break_direction(
    frame: pd.DataFrame,
    high: pd.Series,
    low: pd.Series,
    sweep_atr: float,
    close_back_atr: float,
    wick_min: float,
) -> pd.Series:
    atr = frame["atr14"]
    swept_high = (
        frame["mid_high"].gt(high + sweep_atr * atr)
        & frame["mid_close"].lt(high - close_back_atr * atr)
        & frame["upper_wick"].ge(wick_min)
    )
    swept_low = (
        frame["mid_low"].lt(low - sweep_atr * atr)
        & frame["mid_close"].gt(low + close_back_atr * atr)
        & frame["lower_wick"].ge(wick_min)
    )
    return pd.Series(
        np.select([swept_high, swept_low], [-1, 1], default=0),
        index=frame.index,
        dtype=int,
    )


def signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series]:
    close = frame["mid_close"]
    candle = frame["candle_direction"]
    atr = frame["atr14"]
    regime = frame["regime"]
    hour = _hour_mask(frame, str(params["hour_window"]))
    direction = pd.Series(0, index=frame.index, dtype=int)

    if mechanic == "CHOP_ASIAN_FALSE_BREAK_FADE":
        direction = _false_break_direction(
            frame,
            frame["asian_high"],
            frame["asian_low"],
            float(params["sweep_atr"]),
            float(params["close_back_atr"]),
            float(params["wick_min"]),
        )
        mask = (
            regime.eq("CHOP")
            & frame["asian_range_atr"].between(
                float(params["asia_range_atr_min"]),
                float(params["asia_range_atr_max"]),
                inclusive="both",
            )
            & direction.ne(0)
        )
    elif mechanic == "CHOP_ASIAN_EDGE_ROTATION":
        width = (frame["asian_high"] - frame["asian_low"]).replace(0.0, np.nan)
        location = (close - frame["asian_low"]) / width
        edge = float(params["edge_fraction"])
        direction = pd.Series(
            np.select([location.le(edge), location.ge(1.0 - edge)], [1, -1], default=0),
            index=frame.index,
            dtype=int,
        )
        confirmation = direction.mul(candle).gt(0) if bool(params["require_confirmation"]) else True
        mask = (
            regime.eq("CHOP")
            & frame["asian_range_atr"].between(
                float(params["asia_range_atr_min"]),
                float(params["asia_range_atr_max"]),
                inclusive="both",
            )
            & direction.ne(0)
            & confirmation
        )
    elif mechanic == "CHOP_ANCHORED_VWAP_REVERSION":
        deviation = frame["vwap_deviation_atr"]
        direction = -np.sign(deviation).fillna(0).astype(int)
        confirmation = direction.mul(candle).gt(0) if bool(params["require_confirmation"]) else True
        mask = (
            regime.eq("CHOP")
            & deviation.abs().ge(float(params["deviation_atr"]))
            & frame["day_bar_number"].ge(int(params["minimum_day_bars"]))
            & frame["day_displacement_atr"].abs().le(float(params["maximum_day_displacement_atr"]))
            & direction.ne(0)
            & confirmation
        )
    elif mechanic == "CHOP_OVERNIGHT_INVENTORY_REVERSAL":
        inventory = frame["asian_inventory_atr"]
        direction = -np.sign(inventory).fillna(0).astype(int)
        mask = (
            regime.eq("CHOP")
            & inventory.abs().ge(float(params["inventory_atr"]))
            & frame["vwap_deviation_atr"].abs().ge(float(params["vwap_deviation_atr"]))
            & direction.ne(0)
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
        )
    elif mechanic == "CHOP_WEAK_BREAKOUT_ANTISIGNAL":
        breakout = _break_direction(frame, int(params["lookback"]), float(params["breakout_atr"]))
        direction = -breakout
        mask = (
            regime.eq("CHOP")
            & direction.ne(0)
            & frame["body"].le(float(params["body_max"]))
            & frame["efficiency_ratio"].le(float(params["efficiency_max"]))
        )
    elif mechanic == "TRANS_ANCESTRY_PULLBACK_CONTINUE":
        direction = frame["ancestry_direction"].astype(int)
        touch = pd.Series(
            np.where(
                direction.gt(0),
                frame["mid_low"].le(frame["ema_fast"] + float(params["touch_atr"]) * atr),
                frame["mid_high"].ge(frame["ema_fast"] - float(params["touch_atr"]) * atr),
            ),
            index=frame.index,
        )
        slope_ok = direction.mul(frame["ema_slope_atr_h4"]).ge(float(params["slope_atr_min"]))
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & frame["transition_age_h1"].le(int(params["transition_age_max"]))
            & touch
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & slope_ok
        )
    elif mechanic == "TRANS_ANCESTRY_FAILURE_FADE":
        ancestry = frame["ancestry_direction"].astype(int)
        direction = -ancestry
        momentum = frame[f"return_{int(params['momentum_bars'])}_local"] / atr
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & frame["transition_age_h1"].between(
                int(params["transition_age_min"]), int(params["transition_age_max"]), inclusive="both"
            )
            & direction.mul(momentum).ge(float(params["failure_momentum_atr"]))
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
        )
    elif mechanic == "TRANS_FIRST_BLOCK_IMPULSE":
        momentum = frame[f"return_{int(params['momentum_bars'])}_local"]
        direction = np.sign(momentum).fillna(0).astype(int)
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & _source_mask(frame, str(params["source"]))
            & frame["transition_age_h1"].le(int(params["transition_age_max"]))
            & direction.ne(0)
            & momentum.abs().div(atr).ge(float(params["momentum_atr"]))
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_EXHAUSTED_MOMENTUM_ANTISIGNAL":
        momentum = frame[f"return_{int(params['momentum_bars'])}_local"]
        momentum_direction = np.sign(momentum).fillna(0).astype(int)
        direction = -momentum_direction
        rsi = frame[f"rsi_{int(params['rsi_period'])}"]
        tail = float(params["rsi_tail"])
        extreme = pd.Series(
            np.where(momentum_direction.gt(0), rsi.ge(100.0 - tail), rsi.le(tail)),
            index=frame.index,
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & _source_mask(frame, str(params["source"]))
            & frame["transition_age_h1"].le(int(params["transition_age_max"]))
            & direction.ne(0)
            & momentum.abs().div(atr).ge(float(params["momentum_atr"]))
            & extreme
        )
    elif mechanic == "TRANS_RANGE_REENTRY_FADE":
        lookback = int(params["lookback"])
        direction = _false_break_direction(
            frame,
            frame[f"prior_high_{lookback}"],
            frame[f"prior_low_{lookback}"],
            float(params["sweep_atr"]),
            float(params["close_back_atr"]),
            float(params["wick_min"]),
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & _source_mask(frame, str(params["source"]))
            & frame["transition_age_h1"].le(int(params["transition_age_max"]))
            & direction.ne(0)
        )
    else:
        raise KeyError(mechanic)

    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & pd.Series(direction, index=frame.index).ne(0)
        & hour
        & np.isfinite(atr)
        & atr.gt(0.0)
    )
    return valid.astype(bool), pd.Series(direction, index=frame.index).astype(int)


def simulate_variant(
    frame: pd.DataFrame,
    manifest_row: Any,
    execution: Mapping[str, Any],
    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None],
    outcome_function: Callable[..., dict[str, Any] | None],
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mask, direction = signal_mask_direction(frame, str(manifest_row.mechanic), params)
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        key = (int(signal_index), sign, float(params["stop_atr"]), float(params["hold_hours"]))
        if key not in outcome_cache:
            outcome_cache[key] = outcome_function(
                frame,
                int(signal_index),
                sign,
                float(params["stop_atr"]),
                float(params["hold_hours"]),
                execution,
            )
        outcome = outcome_cache[key]
        if outcome is None:
            continue
        entry_time = pd.Timestamp(outcome["entry_time"])
        if entry_time < position_until:
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= int(execution["maximum_trades_per_variant_utc_day"]):
            continue
        selected.append(outcome)
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)
