from __future__ import annotations

import hashlib
import itertools
import json
import math
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy import stats


MECHANICS: dict[str, tuple[str, ...]] = {
    "DOWNTREND": (
        "DOWN_FAILED_RALLY_SHORT",
        "DOWN_RSI_RALLY_FADE_SHORT",
        "DOWN_BEAR_FLAG_BREAK_SHORT",
        "DOWN_ACCELERATION_SHORT",
        "DOWN_EXHAUSTION_BOUNCE_LONG",
    ),
    "COMPRESSION": (
        "COMP_RELEASE_BREAKOUT",
        "COMP_RELEASE_EXPANSION",
        "COMP_FALSE_BREAK_FADE",
        "COMP_FIRST_TREND",
        "LOW_VOL_SESSION_BREAK",
    ),
    "CHOP": (
        "CHOP_ZSCORE_FADE",
        "CHOP_RSI_FADE",
        "CHOP_EDGE_REJECTION",
        "CHOP_BREAKOUT",
        "CHOP_CANDLE_MOMENTUM",
    ),
    "TRANSITION": (
        "TRANS_RETURN_MOMENTUM",
        "TRANS_RANGE_BREAKOUT",
        "TRANS_EMA_PULLBACK",
        "TRANS_EXHAUSTION_FADE",
        "TRANS_SESSION_CONTINUE",
    ),
}


def _space(**values: list[Any]) -> list[dict[str, Any]]:
    keys = tuple(values)
    return [
        dict(zip(keys, combination, strict=True))
        for combination in itertools.product(*(values[key] for key in keys))
    ]


def parameter_space(mechanic: str) -> list[dict[str, Any]]:
    hours = ["ALL", "LIQUID", "LONDON", "NEW_YORK"]
    stops = [0.8, 1.0, 1.25, 1.5, 2.0]
    if mechanic == "DOWN_FAILED_RALLY_SHORT":
        return _space(
            pullback_atr=[-0.1, 0.0, 0.1, 0.2, 0.35, 0.5],
            body_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            close_location_max=[0.3, 0.45, 0.6],
            hour_window=hours,
            hold_hours=[4, 8, 12, 18, 24, 36],
            stop_atr=stops,
        )
    if mechanic == "DOWN_RSI_RALLY_FADE_SHORT":
        return _space(
            rsi_period=[2, 3, 4, 6, 9],
            rsi_high=[55, 60, 65, 70, 75, 80],
            body_min=[0.1, 0.2, 0.3, 0.4],
            require_cross=[False, True],
            hour_window=hours,
            hold_hours=[4, 8, 12, 18, 24, 36],
            stop_atr=stops,
        )
    if mechanic == "DOWN_BEAR_FLAG_BREAK_SHORT":
        return _space(
            flag_bars=[2, 3, 4, 6, 8, 12],
            prior_rally_atr=[-0.25, 0.0, 0.15, 0.3, 0.5],
            breakout_atr=[0.0, 0.05, 0.1, 0.2],
            body_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=hours,
            hold_hours=[4, 8, 12, 18, 24, 36],
            stop_atr=stops,
        )
    if mechanic == "DOWN_ACCELERATION_SHORT":
        return _space(
            momentum_bars=[2, 3, 4, 6, 8, 12],
            momentum_atr=[0.4, 0.6, 0.8, 1.0, 1.25, 1.5],
            body_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "DOWN_EXHAUSTION_BOUNCE_LONG":
        return _space(
            rsi_period=[2, 3, 4, 6, 9],
            rsi_low=[10, 15, 20, 25, 30, 35],
            range_atr_min=[0.8, 1.0, 1.25, 1.5, 2.0],
            lower_wick_min=[0.15, 0.3, 0.45, 0.6],
            require_bullish=[False, True],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "COMP_RELEASE_BREAKOUT":
        return _space(
            recent_bars=[4, 8, 12, 24],
            lookback=[4, 6, 8, 12, 18, 24],
            breakout_atr=[0.0, 0.05, 0.1, 0.2],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "COMP_RELEASE_EXPANSION":
        return _space(
            recent_bars=[4, 8, 12, 24],
            range_atr_min=[0.8, 1.0, 1.25, 1.5, 2.0],
            body_min=[0.2, 0.3, 0.4, 0.5, 0.6],
            efficiency_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "COMP_FALSE_BREAK_FADE":
        return _space(
            lookback=[4, 6, 8, 12, 18, 24],
            sweep_atr=[0.0, 0.05, 0.1, 0.2],
            close_back_atr=[0.0, 0.05, 0.1, 0.2],
            wick_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
        )
    if mechanic == "COMP_FIRST_TREND":
        return _space(
            recent_bars=[4, 8, 12, 24],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=hours,
            hold_hours=[4, 8, 12, 18, 24, 36],
            stop_atr=stops,
        )
    if mechanic == "LOW_VOL_SESSION_BREAK":
        return _space(
            lookback=[4, 6, 8, 12, 18, 24],
            atr_ratio_max=[0.6, 0.7, 0.8, 0.9, 1.0],
            breakout_atr=[0.0, 0.05, 0.1, 0.2],
            hour_window=["LIQUID", "LONDON", "NEW_YORK"],
            body_min=[0.1, 0.2, 0.3, 0.4],
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
        )
    if mechanic == "CHOP_ZSCORE_FADE":
        return _space(
            lookback=[12, 18, 24, 36, 48],
            z_min=[1.0, 1.25, 1.5, 1.75, 2.0, 2.5],
            require_confirmation=[False, True],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "CHOP_RSI_FADE":
        return _space(
            rsi_period=[2, 3, 4, 6, 9],
            rsi_tail=[10, 15, 20, 25, 30],
            require_confirmation=[False, True],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "CHOP_EDGE_REJECTION":
        return _space(
            lookback=[8, 12, 18, 24, 36, 48],
            edge_fraction=[0.1, 0.15, 0.2, 0.25, 0.3],
            wick_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            require_confirmation=[False, True],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
        )
    if mechanic == "CHOP_BREAKOUT":
        return _space(
            lookback=[4, 6, 8, 12, 18, 24],
            breakout_atr=[0.0, 0.05, 0.1, 0.2],
            body_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
        )
    if mechanic == "CHOP_CANDLE_MOMENTUM":
        return _space(
            range_atr_min=[0.5, 0.75, 1.0, 1.25, 1.5],
            body_min=[0.2, 0.3, 0.4, 0.5, 0.6],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=hours,
            hold_hours=[1, 2, 4, 6, 8, 12],
            stop_atr=stops,
        )
    if mechanic == "TRANS_RETURN_MOMENTUM":
        return _space(
            momentum_bars=[1, 2, 3, 4, 6, 8, 12],
            momentum_atr=[0.2, 0.35, 0.5, 0.75, 1.0],
            body_min=[0.1, 0.2, 0.3, 0.4],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "TRANS_RANGE_BREAKOUT":
        return _space(
            lookback=[4, 6, 8, 12, 18, 24],
            breakout_atr=[0.0, 0.05, 0.1, 0.2],
            body_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24],
            stop_atr=stops,
        )
    if mechanic == "TRANS_EMA_PULLBACK":
        return _space(
            touch_atr=[-0.1, 0.0, 0.1, 0.2, 0.35, 0.5],
            body_min=[0.1, 0.2, 0.3, 0.4, 0.5],
            efficiency_min=[0.05, 0.15, 0.25, 0.35],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18, 24, 36],
            stop_atr=stops,
        )
    if mechanic == "TRANS_EXHAUSTION_FADE":
        return _space(
            rsi_period=[2, 3, 4, 6, 9],
            rsi_tail=[10, 15, 20, 25, 30],
            range_atr_min=[0.8, 1.0, 1.25, 1.5, 2.0],
            wick_min=[0.1, 0.2, 0.3, 0.4],
            hour_window=hours,
            hold_hours=[2, 4, 6, 8, 12, 18],
            stop_atr=stops,
        )
    if mechanic == "TRANS_SESSION_CONTINUE":
        return _space(
            momentum_bars=[1, 2, 3, 4, 6],
            momentum_atr=[0.15, 0.25, 0.4, 0.6, 0.8],
            hour_window=["LIQUID", "LONDON", "NEW_YORK"],
            body_min=[0.1, 0.2, 0.3, 0.4],
            hold_hours=[1, 2, 4, 6, 8, 12],
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
            for params in candidates:
                canonical = json.dumps(
                    params, sort_keys=True, separators=(",", ":")
                )
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
    expected = int(selection["total_attempts"])
    if len(result) != expected:
        raise ValueError(f"Expected {expected} attempts, generated {len(result)}")
    if int(result["attempt_no"].iat[-1]) != int(selection["attempt_last"]):
        raise ValueError("Attempt-number boundary does not match the contract")
    if result["variant_id"].duplicated().any():
        raise ValueError("Duplicate variant IDs")
    return result


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0).ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()
    loss = (-delta.clip(upper=0.0)).ewm(
        alpha=1.0 / period, adjust=False, min_periods=period
    ).mean()
    return 100.0 - 100.0 / (1.0 + gain / loss.replace(0.0, np.nan))


def prepare_features(
    h1: pd.DataFrame,
    h4: pd.DataFrame,
    config: Mapping[str, Any],
    adaptive_module: Any,
    regime_module: Any,
) -> pd.DataFrame:
    frame = adaptive_module.prepare_h4(h1, config["signal"])
    classified = regime_module.classify_h4(h4, config["regime"])
    frame = regime_module.attach_regime(frame, classified)
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(
        drop=True
    )
    close = frame["mid_close"]
    high = frame["mid_high"]
    low = frame["mid_low"]
    bar_range = high.sub(low).replace(0.0, np.nan)
    frame["body"] = close.sub(frame["mid_open"]).abs().div(bar_range)
    frame["candle_direction"] = np.sign(close - frame["mid_open"]).astype(int)
    frame["close_location_local"] = close.sub(low).div(bar_range)
    frame["lower_wick"] = np.minimum(frame["mid_open"], close).sub(low).div(
        bar_range
    )
    frame["upper_wick"] = high.sub(
        np.maximum(frame["mid_open"], close)
    ).div(bar_range)
    frame["hour"] = frame["timestamp_utc"].dt.hour
    for period in (2, 3, 4, 6, 9, 14):
        frame[f"rsi_{period}"] = _rsi(close, period)
    for bars in (1, 2, 3, 4, 6, 8, 12, 18, 24, 36, 48):
        frame[f"return_{bars}_local"] = close.diff(bars)
        if bars > 1:
            frame[f"prior_high_{bars}"] = (
                high.shift(1).rolling(bars, min_periods=bars).max()
            )
            frame[f"prior_low_{bars}"] = (
                low.shift(1).rolling(bars, min_periods=bars).min()
            )
            frame[f"prior_mean_{bars}"] = (
                close.shift(1).rolling(bars, min_periods=bars).mean()
            )
            frame[f"prior_std_{bars}"] = (
                close.shift(1).rolling(bars, min_periods=bars).std(ddof=0)
            )
    compression = frame["regime"].eq("COMPRESSION")
    for bars in (4, 8, 12, 24):
        frame[f"compression_recent_{bars}"] = (
            compression.shift(1)
            .rolling(bars, min_periods=1)
            .max()
            .fillna(False)
            .astype(bool)
        )
    return frame


def _hour_mask(frame: pd.DataFrame, name: str) -> pd.Series:
    hour = frame["hour"]
    if name == "ALL":
        return pd.Series(True, index=frame.index)
    if name == "LIQUID":
        return hour.between(5, 18)
    if name == "LONDON":
        return hour.between(7, 12)
    if name == "NEW_YORK":
        return hour.between(12, 18)
    raise KeyError(name)


def _break_direction(
    frame: pd.DataFrame, lookback: int, breakout_atr: float
) -> pd.Series:
    up = frame["mid_close"].gt(
        frame[f"prior_high_{lookback}"] + breakout_atr * frame["atr14"]
    )
    down = frame["mid_close"].lt(
        frame[f"prior_low_{lookback}"] - breakout_atr * frame["atr14"]
    )
    return pd.Series(
        np.select([up, down], [1, -1], default=0), index=frame.index, dtype=int
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

    if mechanic == "DOWN_FAILED_RALLY_SHORT":
        direction[:] = -1
        touched = frame["mid_high"].shift(1).ge(
            frame["ema_fast"].shift(1)
            - float(params["pullback_atr"]) * atr.shift(1)
        )
        mask = (
            regime.eq("TREND_DOWN")
            & touched
            & close.lt(frame["ema_fast"])
            & candle.lt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
            & frame["close_location_local"].le(
                float(params["close_location_max"])
            )
        )
    elif mechanic == "DOWN_RSI_RALLY_FADE_SHORT":
        direction[:] = -1
        rsi = frame[f"rsi_{int(params['rsi_period'])}"]
        prior_high = rsi.shift(1).ge(float(params["rsi_high"]))
        trigger = (
            prior_high & rsi.lt(float(params["rsi_high"]))
            if bool(params["require_cross"])
            else prior_high
        )
        mask = (
            regime.eq("TREND_DOWN")
            & trigger
            & candle.lt(0)
            & close.lt(frame["ema_fast"])
            & frame["body"].ge(float(params["body_min"]))
        )
    elif mechanic == "DOWN_BEAR_FLAG_BREAK_SHORT":
        direction[:] = -1
        bars = int(params["flag_bars"])
        prior_rally = frame[f"return_{bars}_local"].shift(1).div(atr.shift(1))
        mask = (
            regime.eq("TREND_DOWN")
            & prior_rally.ge(float(params["prior_rally_atr"]))
            & close.lt(
                frame[f"prior_low_{bars}"]
                - float(params["breakout_atr"]) * atr
            )
            & candle.lt(0)
            & frame["body"].ge(float(params["body_min"]))
        )
    elif mechanic == "DOWN_ACCELERATION_SHORT":
        direction[:] = -1
        momentum = frame[
            f"return_{int(params['momentum_bars'])}_local"
        ].div(atr)
        mask = (
            regime.eq("TREND_DOWN")
            & momentum.le(-float(params["momentum_atr"]))
            & candle.lt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "DOWN_EXHAUSTION_BOUNCE_LONG":
        direction[:] = 1
        confirmation = candle.gt(0) if bool(params["require_bullish"]) else True
        mask = (
            regime.eq("TREND_DOWN")
            & frame[f"rsi_{int(params['rsi_period'])}"].le(
                float(params["rsi_low"])
            )
            & frame["range_atr"].ge(float(params["range_atr_min"]))
            & frame["lower_wick"].ge(float(params["lower_wick_min"]))
            & confirmation
        )
    elif mechanic == "COMP_RELEASE_BREAKOUT":
        direction = _break_direction(
            frame, int(params["lookback"]), float(params["breakout_atr"])
        )
        mask = (
            frame[f"compression_recent_{int(params['recent_bars'])}"]
            & ~regime.eq("UNSAFE_SHOCK")
            & direction.ne(0)
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "COMP_RELEASE_EXPANSION":
        direction = candle.astype(int)
        mask = (
            frame[f"compression_recent_{int(params['recent_bars'])}"]
            & ~regime.eq("UNSAFE_SHOCK")
            & direction.ne(0)
            & frame["range_atr"].ge(float(params["range_atr_min"]))
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "COMP_FALSE_BREAK_FADE":
        lookback = int(params["lookback"])
        high = frame[f"prior_high_{lookback}"]
        low = frame[f"prior_low_{lookback}"]
        swept_high = (
            frame["mid_high"].gt(high + float(params["sweep_atr"]) * atr)
            & close.lt(high - float(params["close_back_atr"]) * atr)
            & frame["upper_wick"].ge(float(params["wick_min"]))
        )
        swept_low = (
            frame["mid_low"].lt(low - float(params["sweep_atr"]) * atr)
            & close.gt(low + float(params["close_back_atr"]) * atr)
            & frame["lower_wick"].ge(float(params["wick_min"]))
        )
        direction = pd.Series(
            np.select([swept_high, swept_low], [-1, 1], default=0),
            index=frame.index,
            dtype=int,
        )
        mask = (
            (regime.eq("COMPRESSION") | regime.shift(1).eq("COMPRESSION"))
            & direction.ne(0)
        )
    elif mechanic == "COMP_FIRST_TREND":
        direction = pd.Series(
            np.select(
                [regime.eq("TREND_UP"), regime.eq("TREND_DOWN")],
                [1, -1],
                default=0,
            ),
            index=frame.index,
            dtype=int,
        )
        mask = (
            frame[f"compression_recent_{int(params['recent_bars'])}"]
            & direction.ne(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "LOW_VOL_SESSION_BREAK":
        direction = _break_direction(
            frame, int(params["lookback"]), float(params["breakout_atr"])
        )
        mask = (
            frame["atr_ratio"].shift(1).le(float(params["atr_ratio_max"]))
            & direction.ne(0)
            & frame["body"].ge(float(params["body_min"]))
        )
    elif mechanic == "CHOP_ZSCORE_FADE":
        lookback = int(params["lookback"])
        zscore = close.sub(frame[f"prior_mean_{lookback}"]).div(
            frame[f"prior_std_{lookback}"].replace(0.0, np.nan)
        )
        direction = -np.sign(zscore).fillna(0).astype(int)
        confirmation = (
            direction.mul(candle).gt(0)
            if bool(params["require_confirmation"])
            else True
        )
        mask = (
            regime.eq("CHOP")
            & zscore.abs().ge(float(params["z_min"]))
            & direction.ne(0)
            & confirmation
        )
    elif mechanic == "CHOP_RSI_FADE":
        rsi = frame[f"rsi_{int(params['rsi_period'])}"]
        tail = float(params["rsi_tail"])
        direction = pd.Series(
            np.select([rsi.le(tail), rsi.ge(100.0 - tail)], [1, -1], default=0),
            index=frame.index,
            dtype=int,
        )
        confirmation = (
            direction.mul(candle).gt(0)
            if bool(params["require_confirmation"])
            else True
        )
        mask = regime.eq("CHOP") & direction.ne(0) & confirmation
    elif mechanic == "CHOP_EDGE_REJECTION":
        lookback = int(params["lookback"])
        prior_high = frame[f"prior_high_{lookback}"]
        prior_low = frame[f"prior_low_{lookback}"]
        location = close.sub(prior_low).div(
            prior_high.sub(prior_low).replace(0.0, np.nan)
        )
        edge = float(params["edge_fraction"])
        direction = pd.Series(
            np.select(
                [location.le(edge), location.ge(1.0 - edge)],
                [1, -1],
                default=0,
            ),
            index=frame.index,
            dtype=int,
        )
        wick = pd.Series(
            np.where(direction.gt(0), frame["lower_wick"], frame["upper_wick"]),
            index=frame.index,
        )
        confirmation = (
            direction.mul(candle).gt(0)
            if bool(params["require_confirmation"])
            else True
        )
        mask = (
            regime.eq("CHOP")
            & direction.ne(0)
            & wick.ge(float(params["wick_min"]))
            & confirmation
        )
    elif mechanic == "CHOP_BREAKOUT":
        direction = _break_direction(
            frame, int(params["lookback"]), float(params["breakout_atr"])
        )
        mask = (
            regime.eq("CHOP")
            & direction.ne(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "CHOP_CANDLE_MOMENTUM":
        direction = candle.astype(int)
        mask = (
            regime.eq("CHOP")
            & direction.ne(0)
            & frame["range_atr"].ge(float(params["range_atr_min"]))
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_RETURN_MOMENTUM":
        momentum = frame[
            f"return_{int(params['momentum_bars'])}_local"
        ]
        direction = np.sign(momentum).fillna(0).astype(int)
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & momentum.abs().div(atr).ge(float(params["momentum_atr"]))
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_RANGE_BREAKOUT":
        direction = _break_direction(
            frame, int(params["lookback"]), float(params["breakout_atr"])
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_EMA_PULLBACK":
        direction = pd.Series(
            np.select(
                [frame["ema_fast"].gt(frame["ema_slow"]), frame["ema_fast"].lt(frame["ema_slow"])],
                [1, -1],
                default=0,
            ),
            index=frame.index,
            dtype=int,
        )
        touch = pd.Series(
            np.where(
                direction.gt(0),
                frame["mid_low"].le(
                    frame["ema_fast"] + float(params["touch_atr"]) * atr
                ),
                frame["mid_high"].ge(
                    frame["ema_fast"] - float(params["touch_atr"]) * atr
                ),
            ),
            index=frame.index,
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & touch
            & direction.mul(candle).gt(0)
            & frame["body"].ge(float(params["body_min"]))
            & frame["efficiency_ratio"].ge(float(params["efficiency_min"]))
        )
    elif mechanic == "TRANS_EXHAUSTION_FADE":
        rsi = frame[f"rsi_{int(params['rsi_period'])}"]
        tail = float(params["rsi_tail"])
        direction = pd.Series(
            np.select([rsi.le(tail), rsi.ge(100.0 - tail)], [1, -1], default=0),
            index=frame.index,
            dtype=int,
        )
        wick = pd.Series(
            np.where(direction.gt(0), frame["lower_wick"], frame["upper_wick"]),
            index=frame.index,
        )
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & frame["range_atr"].ge(float(params["range_atr_min"]))
            & wick.ge(float(params["wick_min"]))
        )
    elif mechanic == "TRANS_SESSION_CONTINUE":
        momentum = frame[
            f"return_{int(params['momentum_bars'])}_local"
        ]
        direction = np.sign(momentum).fillna(0).astype(int)
        mask = (
            regime.eq("TRANSITION_UNKNOWN")
            & direction.ne(0)
            & momentum.abs().div(atr).ge(float(params["momentum_atr"]))
            & frame["body"].ge(float(params["body_min"]))
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


def simulate_h1_outcome(
    frame: pd.DataFrame,
    signal_index: int,
    direction: int,
    stop_atr: float,
    hold_hours: float,
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    entry_index = signal_index + 1
    if entry_index >= len(frame):
        return None
    signal = frame.iloc[signal_index]
    entry_bar = frame.iloc[entry_index]
    signal_time = pd.Timestamp(signal["timestamp_utc"])
    entry_time = pd.Timestamp(entry_bar["bar_start_utc"])
    gap_minutes = (entry_time - signal_time).total_seconds() / 60.0
    if gap_minutes < 0.0 or gap_minutes > float(
        execution["maximum_entry_gap_minutes"]
    ):
        return None
    atr_value = float(signal["atr14"])
    if not np.isfinite(atr_value) or atr_value <= 0.0:
        return None
    entry = float(entry_bar["ask_open"] if direction > 0 else entry_bar["bid_open"])
    risk = float(stop_atr) * atr_value
    spread = float(entry_bar["ask_open"] - entry_bar["bid_open"])
    if spread < 0.0 or spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    stop = entry - direction * risk
    deadline = entry_time + pd.Timedelta(hours=float(hold_hours))
    exit_time = pd.Timestamp(entry_bar["timestamp_utc"])
    exit_price = float(
        entry_bar["bid_close"] if direction > 0 else entry_bar["ask_close"]
    )
    exit_reason = "END_OF_DATA"
    for position in range(entry_index, len(frame)):
        bar = frame.iloc[position]
        bar_start = pd.Timestamp(bar["bar_start_utc"])
        if bar_start >= deadline:
            exit_time = bar_start
            exit_price = float(
                bar["bid_open"] if direction > 0 else bar["ask_open"]
            )
            exit_reason = "FIXED_HORIZON"
            break
        executable_open = float(
            bar["bid_open"] if direction > 0 else bar["ask_open"]
        )
        if (direction > 0 and executable_open <= stop) or (
            direction < 0 and executable_open >= stop
        ):
            exit_time = bar_start
            exit_price = executable_open
            exit_reason = "GAP_THROUGH_STOP"
            break
        stop_hit = (
            float(bar["bid_low"]) <= stop
            if direction > 0
            else float(bar["ask_high"]) >= stop
        )
        if stop_hit:
            exit_time = pd.Timestamp(bar["timestamp_utc"])
            exit_price = stop
            exit_reason = "STOP"
            break
        exit_time = pd.Timestamp(bar["timestamp_utc"])
        exit_price = float(
            bar["bid_close"] if direction > 0 else bar["ask_close"]
        )
    gross_r = direction * (exit_price - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "signal_time": signal_time,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "direction": "LONG" if direction > 0 else "SHORT",
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread_r": spread / risk,
        "gross_r": gross_r,
        "stress_net_r": gross_r
        - extra_cost_r
        - float(execution["stress_slippage_r"]),
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "exit_reason": exit_reason,
    }


def simulate_variant(
    frame: pd.DataFrame,
    manifest_row: Any,
    execution: Mapping[str, Any],
    outcome_cache: dict[tuple[Any, ...], dict[str, Any] | None],
) -> pd.DataFrame:
    params = json.loads(str(manifest_row.parameters_json))
    mask, direction = signal_mask_direction(
        frame, str(manifest_row.mechanic), params
    )
    selected: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        sign = int(direction.iat[int(signal_index)])
        key = (
            int(signal_index),
            sign,
            float(params["stop_atr"]),
            float(params["hold_hours"]),
        )
        if key not in outcome_cache:
            outcome_cache[key] = simulate_h1_outcome(
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
        if daily_count.get(day, 0) >= int(
            execution["maximum_trades_per_variant_utc_day"]
        ):
            continue
        selected.append(outcome)
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)


def profit_factor(values: pd.Series) -> float:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(
        ([0.0], values.fillna(0.0).to_numpy(dtype=float).cumsum())
    )
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity)) if len(equity) else 0.0


def one_sided_daily_pvalue(
    trades: pd.DataFrame, source_days: pd.DatetimeIndex
) -> float:
    daily = pd.Series(0.0, index=source_days)
    if not trades.empty:
        observed = trades.assign(
            day=pd.to_datetime(trades["entry_time"], utc=True).dt.normalize()
        ).groupby("day", sort=True)["stress_net_r"].sum()
        daily.loc[daily.index.intersection(observed.index)] = observed.reindex(
            daily.index.intersection(observed.index)
        )
    values = daily.to_numpy(dtype=float)
    if len(values) < 2 or float(values.mean()) <= 0.0:
        return 1.0
    deviation = float(values.std(ddof=1))
    if deviation == 0.0:
        return 0.0
    result = stats.ttest_1samp(values, 0.0, alternative="greater")
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def bh_adjust(values: pd.Series) -> pd.Series:
    clean = values.astype(float).clip(lower=0.0, upper=1.0)
    order = np.argsort(clean.to_numpy(), kind="mergesort")
    ranked = clean.to_numpy()[order]
    count = len(ranked)
    adjusted = np.minimum.accumulate(
        (ranked * count / np.arange(1, count + 1))[::-1]
    )[::-1]
    result = np.empty(count, dtype=float)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return pd.Series(result, index=values.index)


def _summary(values: pd.Series) -> dict[str, Any]:
    return {
        "trades": int(len(values)),
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
    }


def score_variant(
    trades: pd.DataFrame,
    frame: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    values = (
        trades["stress_net_r"].astype(float)
        if not trades.empty
        else pd.Series(dtype=float)
    )
    row: dict[str, Any] = {f"whole_{key}": value for key, value in _summary(values).items()}
    era_summaries: list[dict[str, Any]] = []
    for name, (raw_start, raw_end) in config["windows"].items():
        start, end = pd.Timestamp(raw_start), pd.Timestamp(raw_end)
        segment = (
            trades.loc[
                trades["entry_time"].ge(start) & trades["entry_time"].lt(end)
            ]
            if not trades.empty
            else trades
        )
        summary = _summary(
            segment["stress_net_r"].astype(float)
            if not segment.empty
            else pd.Series(dtype=float)
        )
        era_summaries.append(summary)
        for key, value in summary.items():
            row[f"{name}_{key}"] = value
    removed = values.drop(values.nlargest(min(5, len(values))).index)
    row["top_winners_removed_stress_net_r"] = float(removed.sum())
    source_days = pd.DatetimeIndex(
        frame["bar_start_utc"].dt.normalize().drop_duplicates().sort_values()
    )
    row["daily_pvalue"] = one_sided_daily_pvalue(trades, source_days)
    gates = config["economic_gates"]
    row["minimum_era_trades"] = min(item["trades"] for item in era_summaries)
    row["minimum_era_stress_pf"] = min(
        float(item["stress_pf"]) for item in era_summaries
    )
    row["minimum_era_average_stress_r"] = min(
        float(item["average_stress_r"]) for item in era_summaries
    )
    checks = {
        "minimum_total_trades": row["whole_trades"]
        >= int(gates["minimum_total_trades"]),
        "minimum_trades_each_era": row["minimum_era_trades"]
        >= int(gates["minimum_trades_each_era"]),
        "minimum_stress_pf_each_era": row["minimum_era_stress_pf"]
        >= float(gates["minimum_stress_pf_each_era"]),
        "minimum_average_stress_r_each_era": row[
            "minimum_era_average_stress_r"
        ]
        >= float(gates["minimum_average_stress_r_each_era"]),
        "minimum_total_stress_pf": row["whole_stress_pf"]
        >= float(gates["minimum_total_stress_pf"]),
        "maximum_closed_drawdown_r": row["whole_closed_drawdown_r"]
        <= float(gates["maximum_closed_drawdown_r"]),
        "minimum_top_winners_removed_net_r": row[
            "top_winners_removed_stress_net_r"
        ]
        > float(gates["minimum_top_winners_removed_net_r"]),
    }
    row["gate_checks_json"] = json.dumps(checks, sort_keys=True)
    row["economic_pass"] = bool(all(checks.values()))
    return row
