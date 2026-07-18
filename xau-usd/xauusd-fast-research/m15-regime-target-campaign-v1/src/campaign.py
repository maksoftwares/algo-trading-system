from __future__ import annotations

import hashlib
import heapq
import itertools
import json
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


MECHANICS: dict[str, tuple[str, ...]] = {
    "CHOP": (
        "CHOP_SESSION_VWAP_TARGET",
        "CHOP_ASIAN_ROTATION_TARGET",
        "CHOP_ASIAN_FALSE_BREAK_TARGET",
        "CHOP_PRIOR_DAY_SWEEP_TARGET",
        "CHOP_ROLLING_MEAN_TARGET",
    ),
    "TRANSITION": (
        "TRANS_POST_COMPRESSION_IMPULSE_TARGET",
        "TRANS_POST_CHOP_BREAKOUT_TARGET",
        "TRANS_TREND_REACTIVATION_TARGET",
        "TRANS_RANGE_REENTRY_TARGET",
        "TRANS_SESSION_EXPANSION_TARGET",
    ),
}


def _space(**values: list[Any]) -> Iterable[dict[str, Any]]:
    keys = tuple(values)
    return (
        dict(zip(keys, combination, strict=True))
        for combination in itertools.product(*(values[key] for key in keys))
    )


def parameter_space(mechanic: str) -> Iterable[dict[str, Any]]:
    stops = [0.75, 1.0, 1.25, 1.5, 2.0]
    holds = [1, 2, 3, 4, 6, 8, 12]
    liquid = ["POST_ASIA", "LONDON", "LONDON_NY", "NEW_YORK"]
    reward_bounds = {
        "target_r_min": [0.75, 1.0],
        "target_r_max": [2.5, 4.0],
    }
    if mechanic == "CHOP_SESSION_VWAP_TARGET":
        return _space(
            deviation_atr=[0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0],
            body_min=[0.0, 0.1, 0.2, 0.3],
            require_confirmation=[False, True],
            minimum_day_bars=[16, 24, 32, 40],
            hour_window=["ALL", *liquid],
            stop_atr=stops,
            hold_hours=holds,
            **reward_bounds,
        )
    if mechanic == "CHOP_ASIAN_ROTATION_TARGET":
        return _space(
            edge_fraction=[0.0, 0.05, 0.1, 0.15, 0.2],
            asia_range_atr_min=[1.0, 1.5, 2.0, 2.5],
            asia_range_atr_max=[4.0, 6.0, 8.0, 12.0],
            require_confirmation=[False, True],
            hour_window=liquid,
            stop_atr=stops,
            hold_hours=holds,
            **reward_bounds,
        )
    if mechanic == "CHOP_ASIAN_FALSE_BREAK_TARGET":
        return _space(
            sweep_atr=[0.0, 0.05, 0.1, 0.2, 0.3],
            close_back_atr=[0.0, 0.05, 0.1, 0.2],
            wick_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            hour_window=liquid,
            stop_atr=stops,
            hold_hours=holds,
            **reward_bounds,
        )
    if mechanic == "CHOP_PRIOR_DAY_SWEEP_TARGET":
        return _space(
            sweep_atr=[0.0, 0.05, 0.1, 0.2, 0.3],
            close_back_atr=[0.0, 0.05, 0.1, 0.2],
            wick_min=[0.1, 0.2, 0.3, 0.4],
            target_anchor=["DAY_OPEN", "PRIOR_DAY_MID", "VWAP"],
            hour_window=["ALL", *liquid],
            stop_atr=stops,
            hold_hours=holds,
            **reward_bounds,
        )
    if mechanic == "CHOP_ROLLING_MEAN_TARGET":
        return _space(
            lookback=[16, 24, 32, 48, 72, 96],
            deviation_atr=[0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
            require_confirmation=[False, True],
            efficiency_max=[0.15, 0.25, 0.35, 0.45],
            hour_window=["ALL", *liquid],
            stop_atr=stops,
            hold_hours=holds,
            **reward_bounds,
        )
    if mechanic == "TRANS_POST_COMPRESSION_IMPULSE_TARGET":
        return _space(
            transition_age_max=[4, 8, 16, 32, 48],
            momentum_bars=[1, 2, 4, 8, 16],
            momentum_atr=[0.25, 0.4, 0.6, 0.8, 1.0],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=["ALL", *liquid],
            stop_atr=stops,
            target_r=[1.0, 1.25, 1.5, 2.0, 2.5],
            hold_hours=holds,
        )
    if mechanic == "TRANS_POST_CHOP_BREAKOUT_TARGET":
        return _space(
            transition_age_max=[4, 8, 16, 32, 48],
            lookback=[8, 12, 16, 24, 32, 48],
            breakout_atr=[0.0, 0.05, 0.1, 0.2, 0.3],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=["ALL", *liquid],
            stop_atr=stops,
            target_r=[1.0, 1.25, 1.5, 2.0, 2.5],
            hold_hours=holds,
        )
    if mechanic == "TRANS_TREND_REACTIVATION_TARGET":
        return _space(
            transition_age_max=[4, 8, 16, 32, 48],
            touch_atr=[-0.1, 0.0, 0.1, 0.2, 0.35, 0.5],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=["ALL", *liquid],
            stop_atr=stops,
            target_r=[1.0, 1.25, 1.5, 2.0, 2.5],
            hold_hours=holds,
        )
    if mechanic == "TRANS_RANGE_REENTRY_TARGET":
        return _space(
            source=["ANY", "ANY_TREND", "COMPRESSION", "CHOP"],
            transition_age_max=[8, 16, 32, 48],
            lookback=[8, 12, 16, 24, 32, 48],
            sweep_atr=[0.0, 0.05, 0.1, 0.2, 0.3],
            close_back_atr=[0.0, 0.05, 0.1, 0.2],
            wick_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=["ALL", *liquid],
            stop_atr=stops,
            hold_hours=holds,
            **reward_bounds,
        )
    if mechanic == "TRANS_SESSION_EXPANSION_TARGET":
        return _space(
            source=["ANY", "COMPRESSION", "CHOP", "ANY_TREND"],
            transition_age_max=[8, 16, 32, 48],
            breakout_atr=[0.0, 0.05, 0.1, 0.2, 0.3],
            body_min=[0.1, 0.2, 0.3, 0.4],
            asia_range_atr_max=[4.0, 6.0, 8.0, 12.0],
            hour_window=liquid,
            stop_atr=stops,
            target_r=[1.0, 1.25, 1.5, 2.0, 2.5],
            hold_hours=holds,
        )
    raise KeyError(mechanic)


def generate_manifest(selection: Mapping[str, Any]) -> pd.DataFrame:
    per_mechanic = int(selection["variants_per_mechanic"])
    attempt = int(selection["attempt_first"])
    rows: list[dict[str, Any]] = []
    for owner, mechanics in MECHANICS.items():
        for mechanic in mechanics:
            valid_space = (
                params
                for params in parameter_space(mechanic)
                if float(params.get("target_r_min", 0.0))
                < float(params.get("target_r_max", float("inf")))
            )
            candidates = heapq.nsmallest(
                per_mechanic,
                valid_space,
                key=lambda params: hashlib.sha256(
                    f"{owner}|{mechanic}|{json.dumps(params, sort_keys=True)}".encode("ascii")
                ).hexdigest(),
            )
            if len(candidates) != per_mechanic:
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
        raise ValueError("Attempt boundary does not match contract")
    if result["variant_id"].duplicated().any():
        raise ValueError("Duplicate variant IDs")
    return result


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    loss = (-delta.clip(upper=0.0)).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    return 100.0 - 100.0 / (1.0 + gain / loss.replace(0.0, np.nan))


def prepare_features(
    m15: pd.DataFrame,
    h4: pd.DataFrame,
    config: Mapping[str, Any],
    adaptive_module: Any,
    regime_module: Any,
) -> pd.DataFrame:
    frame = adaptive_module.prepare_h4(m15, config["signal"])
    classified = regime_module.classify_h4(h4, config["regime"])
    frame = regime_module.attach_regime(frame, classified)
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    close = frame["mid_close"]
    high = frame["mid_high"]
    low = frame["mid_low"]
    bar_range = (high - low).replace(0.0, np.nan)
    frame["body"] = (close - frame["mid_open"]).abs() / bar_range
    frame["candle_direction"] = np.sign(close - frame["mid_open"]).astype(int)
    frame["lower_wick"] = (np.minimum(frame["mid_open"], close) - low) / bar_range
    frame["upper_wick"] = (high - np.maximum(frame["mid_open"], close)) / bar_range
    for period in (2, 3, 4, 6, 9, 14):
        frame[f"rsi_{period}"] = _rsi(close, period)
    for bars in (1, 2, 4, 8, 12, 16, 24, 32, 48, 72, 96):
        frame[f"return_{bars}_local"] = close.diff(bars)
        if bars >= 8:
            frame[f"prior_high_{bars}"] = high.shift(1).rolling(bars, min_periods=bars).max()
            frame[f"prior_low_{bars}"] = low.shift(1).rolling(bars, min_periods=bars).min()
            frame[f"prior_mean_{bars}"] = close.shift(1).rolling(bars, min_periods=bars).mean()

    timestamp = pd.to_datetime(frame["bar_start_utc"], utc=True)
    day = timestamp.dt.normalize()
    hour = timestamp.dt.hour
    frame["utc_day"] = day
    frame["hour"] = hour
    grouped = frame.groupby("utc_day", sort=False)
    frame["day_bar_number"] = grouped.cumcount() + 1
    frame["day_open"] = grouped["mid_open"].transform("first")
    typical = (high + low + close) / 3.0
    weight = frame["tick_count"].astype(float).clip(lower=1.0)
    frame["anchored_vwap"] = (
        (typical * weight).groupby(day, sort=False).cumsum()
        / weight.groupby(day, sort=False).cumsum()
    )
    frame["vwap_deviation_atr"] = (close - frame["anchored_vwap"]) / frame["atr14"]

    asian = hour.between(0, 5)
    asian_high_partial = high.where(asian).groupby(day, sort=False).cummax()
    asian_low_partial = low.where(asian).groupby(day, sort=False).cummin()
    frame["asian_high"] = asian_high_partial.groupby(day, sort=False).ffill()
    frame["asian_low"] = asian_low_partial.groupby(day, sort=False).ffill()
    frame["asian_mid"] = (frame["asian_high"] + frame["asian_low"]) / 2.0
    frame["asian_range_atr"] = (frame["asian_high"] - frame["asian_low"]) / frame["atr14"]

    daily = frame.groupby("utc_day", sort=True).agg(
        day_high=("mid_high", "max"), day_low=("mid_low", "min")
    )
    prior_daily = daily.shift(1)
    frame["prior_day_high"] = day.map(prior_daily["day_high"])
    frame["prior_day_low"] = day.map(prior_daily["day_low"])
    frame["prior_day_mid"] = (frame["prior_day_high"] + frame["prior_day_low"]) / 2.0

    resolved = frame["regime"].isin(("TREND_UP", "TREND_DOWN", "COMPRESSION", "CHOP"))
    frame["last_resolved_regime"] = frame["regime"].where(resolved).ffill()
    frame["ancestry_direction"] = frame["last_resolved_regime"].map(
        {"TREND_UP": 1, "TREND_DOWN": -1}
    ).fillna(0).astype(int)
    run = frame["regime"].ne(frame["regime"].shift(1)).cumsum()
    age = frame.groupby(run, sort=False).cumcount() + 1
    frame["transition_age_m15"] = age.where(frame["regime"].eq("TRANSITION_UNKNOWN"), 0).astype(int)
    return frame


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
    return ancestor.eq(source)


def _break_direction(frame: pd.DataFrame, lookback: int, buffer_atr: float) -> pd.Series:
    up = frame["mid_close"].gt(frame[f"prior_high_{lookback}"] + buffer_atr * frame["atr14"])
    down = frame["mid_close"].lt(frame[f"prior_low_{lookback}"] - buffer_atr * frame["atr14"])
    return pd.Series(np.select([up, down], [1, -1], default=0), index=frame.index, dtype=int)


def _false_break(
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


def target_series(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any], direction: pd.Series
) -> pd.Series:
    if mechanic == "CHOP_SESSION_VWAP_TARGET":
        return frame["anchored_vwap"]
    if mechanic in ("CHOP_ASIAN_ROTATION_TARGET", "CHOP_ASIAN_FALSE_BREAK_TARGET"):
        return frame["asian_mid"]
    if mechanic == "CHOP_PRIOR_DAY_SWEEP_TARGET":
        anchor = str(params["target_anchor"])
        return {
            "DAY_OPEN": frame["day_open"],
            "PRIOR_DAY_MID": frame["prior_day_mid"],
            "VWAP": frame["anchored_vwap"],
        }[anchor]
    if mechanic == "CHOP_ROLLING_MEAN_TARGET":
        return frame[f"prior_mean_{int(params['lookback'])}"]
    if mechanic == "TRANS_RANGE_REENTRY_TARGET":
        lookback = int(params["lookback"])
        return (frame[f"prior_high_{lookback}"] + frame[f"prior_low_{lookback}"]) / 2.0
    return frame["mid_close"] + direction * float(params["target_r"]) * float(params["stop_atr"]) * frame["atr14"]


def signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series, pd.Series]:
    close = frame["mid_close"]
    atr = frame["atr14"]
    candle = frame["candle_direction"]
    regime = frame["regime"]
    hour = _hour_mask(frame, str(params["hour_window"]))
    direction = pd.Series(0, index=frame.index, dtype=int)

    if mechanic == "CHOP_SESSION_VWAP_TARGET":
        deviation = frame["vwap_deviation_atr"]
        direction = -np.sign(deviation).fillna(0).astype(int)
        confirmation = direction.mul(candle).gt(0) if bool(params["require_confirmation"]) else True
        mask = (
            regime.eq("CHOP")
            & deviation.abs().ge(float(params["deviation_atr"]))
            & frame["day_bar_number"].ge(int(params["minimum_day_bars"]))
            & frame["body"].ge(float(params["body_min"]))
            & confirmation
        )
    elif mechanic == "CHOP_ASIAN_ROTATION_TARGET":
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
    elif mechanic == "CHOP_ASIAN_FALSE_BREAK_TARGET":
        direction = _false_break(
            frame,
            frame["asian_high"],
            frame["asian_low"],
            float(params["sweep_atr"]),
            float(params["close_back_atr"]),
            float(params["wick_min"]),
        )
        mask = regime.eq("CHOP") & direction.ne(0)
    elif mechanic == "CHOP_PRIOR_DAY_SWEEP_TARGET":
        direction = _false_break(
            frame,
            frame["prior_day_high"],
            frame["prior_day_low"],
            float(params["sweep_atr"]),
            float(params["close_back_atr"]),
            float(params["wick_min"]),
        )
        mask = regime.eq("CHOP") & direction.ne(0)
    elif mechanic == "CHOP_ROLLING_MEAN_TARGET":
        lookback = int(params["lookback"])
        deviation = (close - frame[f"prior_mean_{lookback}"]) / atr
        direction = -np.sign(deviation).fillna(0).astype(int)
        confirmation = direction.mul(candle).gt(0) if bool(params["require_confirmation"]) else True
        mask = (
            regime.eq("CHOP")
            & deviation.abs().ge(float(params["deviation_atr"]))
            & frame["efficiency_ratio"].le(float(params["efficiency_max"]))
            & direction.ne(0)
            & confirmation
        )
    elif mechanic == "TRANS_POST_COMPRESSION_IMPULSE_TARGET":
        momentum = frame[f"return_{int(params['momentum_bars'])}_local"]
        direction = np.sign(momentum).fillna(0).astype(int)
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & frame["last_resolved_regime"].eq("COMPRESSION")
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & momentum.abs().div(atr).ge(float(params["momentum_atr"]))
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_POST_CHOP_BREAKOUT_TARGET":
        direction = _break_direction(frame, int(params["lookback"]), float(params["breakout_atr"]))
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & frame["last_resolved_regime"].eq("CHOP")
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & direction.ne(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_TREND_REACTIVATION_TARGET":
        direction = frame["ancestry_direction"].astype(int)
        touch = pd.Series(
            np.where(
                direction.gt(0),
                frame["mid_low"].le(frame["ema_fast"] + float(params["touch_atr"]) * atr),
                frame["mid_high"].ge(frame["ema_fast"] - float(params["touch_atr"]) * atr),
            ),
            index=frame.index,
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & touch
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_RANGE_REENTRY_TARGET":
        lookback = int(params["lookback"])
        direction = _false_break(
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
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & direction.ne(0)
        )
    elif mechanic == "TRANS_SESSION_EXPANSION_TARGET":
        up = close.gt(frame["asian_high"] + float(params["breakout_atr"]) * atr)
        down = close.lt(frame["asian_low"] - float(params["breakout_atr"]) * atr)
        direction = pd.Series(np.select([up, down], [1, -1], default=0), index=frame.index, dtype=int)
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & _source_mask(frame, str(params["source"]))
            & frame["transition_age_m15"].le(int(params["transition_age_max"]))
            & frame["asian_range_atr"].le(float(params["asia_range_atr_max"]))
            & direction.ne(0)
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
        )
    else:
        raise KeyError(mechanic)

    target = target_series(frame, mechanic, params, pd.Series(direction, index=frame.index))
    risk = float(params["stop_atr"]) * atr
    reward_r = pd.Series(direction, index=frame.index).mul(target - close).div(risk)
    if "target_r_min" in params:
        target_ok = reward_r.between(
            float(params["target_r_min"]), float(params["target_r_max"]), inclusive="both"
        )
    else:
        target_ok = reward_r.ge(0.5)
    valid = (
        pd.Series(mask, index=frame.index).fillna(False)
        & pd.Series(direction, index=frame.index).ne(0)
        & hour
        & target_ok.fillna(False)
        & np.isfinite(atr)
        & atr.gt(0.0)
    )
    return valid.astype(bool), pd.Series(direction, index=frame.index).astype(int), target.astype(float)


def execution_arrays(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "starts": frame["bar_start_utc"].astype("int64").to_numpy(),
        "ends": frame["bar_end_utc"].astype("int64").to_numpy(),
        "signals": frame["timestamp_utc"].astype("int64").to_numpy(),
        **{
            column: frame[column].to_numpy(dtype=float)
            for column in (
                "bid_open", "bid_high", "bid_low", "bid_close",
                "ask_open", "ask_high", "ask_low", "ask_close", "atr14",
            )
        },
    }


def simulate_trade(
    arrays: Mapping[str, np.ndarray],
    signal_index: int,
    direction: int,
    target: float,
    stop_atr: float,
    hold_hours: float,
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    entry_index = signal_index + 1
    if entry_index >= len(arrays["starts"]):
        return None
    gap_minutes = (int(arrays["starts"][entry_index]) - int(arrays["signals"][signal_index])) / 60_000_000_000
    if gap_minutes < 0.0 or gap_minutes > float(execution["maximum_entry_gap_minutes"]):
        return None
    atr_value = float(arrays["atr14"][signal_index])
    risk = float(stop_atr) * atr_value
    if not np.isfinite(risk) or risk <= 0.0 or not np.isfinite(target):
        return None
    entry = float(arrays["ask_open"][entry_index] if direction > 0 else arrays["bid_open"][entry_index])
    if direction * (target - entry) <= 0.0:
        return None
    spread = float(arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index])
    if spread < 0.0 or spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    stop = entry - direction * risk
    deadline = int(arrays["starts"][entry_index]) + int(float(hold_hours) * 3_600_000_000_000)
    exit_index = -1
    exit_price = float("nan")
    exit_reason = "NO_EXIT"
    for position in range(entry_index, len(arrays["starts"])):
        start = int(arrays["starts"][position])
        executable_open = float(arrays["bid_open"][position] if direction > 0 else arrays["ask_open"][position])
        if start >= deadline:
            horizon_gap = (start - deadline) / 3_600_000_000_000
            if horizon_gap > float(execution["maximum_horizon_gap_hours"]):
                return None
            exit_index, exit_price, exit_reason = position, executable_open, "FIXED_HORIZON"
            break
        stop_at_open = executable_open <= stop if direction > 0 else executable_open >= stop
        target_at_open = executable_open >= target if direction > 0 else executable_open <= target
        if stop_at_open:
            exit_index, exit_price, exit_reason = position, executable_open, "GAP_THROUGH_STOP"
            break
        if target_at_open:
            exit_index, exit_price, exit_reason = position, target, "TARGET_AT_OPEN"
            break
        stop_hit = float(arrays["bid_low"][position]) <= stop if direction > 0 else float(arrays["ask_high"][position]) >= stop
        target_hit = float(arrays["bid_high"][position]) >= target if direction > 0 else float(arrays["ask_low"][position]) <= target
        if stop_hit:
            exit_index, exit_price = position, stop
            exit_reason = "STOP_AMBIGUOUS" if target_hit else "STOP"
            break
        if target_hit:
            exit_index, exit_price, exit_reason = position, target, "TARGET"
            break
    if exit_index < 0:
        return None
    entry_time = pd.Timestamp(int(arrays["starts"][entry_index]), unit="ns", tz="UTC")
    exit_ns = (
        int(arrays["starts"][exit_index])
        if exit_reason in ("FIXED_HORIZON", "GAP_THROUGH_STOP", "TARGET_AT_OPEN")
        else int(arrays["ends"][exit_index])
    )
    exit_time = pd.Timestamp(exit_ns, unit="ns", tz="UTC")
    gross_r = direction * (exit_price - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    costs_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "signal_time": pd.Timestamp(int(arrays["signals"][signal_index]), unit="ns", tz="UTC"),
        "entry_time": entry_time,
        "exit_time": exit_time,
        "direction": "LONG" if direction > 0 else "SHORT",
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread_r": spread / risk,
        "gross_r": gross_r,
        "stress_net_r": gross_r - costs_r - float(execution["stress_slippage_r"]),
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "exit_reason": exit_reason,
    }


def simulate_variant(
    frame: pd.DataFrame,
    arrays: Mapping[str, np.ndarray],
    manifest_row: Any,
    execution: Mapping[str, Any],
    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None],
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mask, direction, targets = signal_mask_direction(frame, str(manifest_row.mechanic), params)
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        target = float(targets.iat[int(signal_index)])
        key = (
            int(signal_index), sign, round(target, 8),
            float(params["stop_atr"]), float(params["hold_hours"]),
        )
        if key not in outcome_cache:
            outcome_cache[key] = simulate_trade(
                arrays,
                int(signal_index),
                sign,
                target,
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
