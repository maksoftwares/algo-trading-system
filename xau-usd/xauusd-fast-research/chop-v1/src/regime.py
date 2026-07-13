from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RegimeResult:
    bars: pd.DataFrame
    episodes: pd.DataFrame


def wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int, prefix: str = "mid_") -> pd.Series:
    previous = frame[f"{prefix}close"].shift(1)
    tr = pd.concat(
        [
            frame[f"{prefix}high"] - frame[f"{prefix}low"],
            (frame[f"{prefix}high"] - previous).abs(),
            (frame[f"{prefix}low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return wilder(tr, period)


def adx(frame: pd.DataFrame, period: int) -> pd.Series:
    high, low = frame["mid_high"], frame["mid_low"]
    up, down = high.diff(), -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=frame.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=frame.index)
    atr_value = atr(frame, period)
    plus_di = 100.0 * wilder(plus_dm, period) / atr_value
    minus_di = 100.0 * wilder(minus_dm, period) / atr_value
    denominator = plus_di + minus_di
    dx = 100.0 * (plus_di - minus_di).abs() / denominator.replace(0.0, np.nan)
    return wilder(dx, period)


def apply_hysteresis(core: pd.Series, hard_exit: pd.Series, enter_count: int = 2, exit_count: int = 2) -> tuple[pd.Series, pd.Series]:
    active = False
    good = bad = episode = 0
    states: list[bool] = []
    ids: list[int] = []
    for qualifies, exits in zip(core.fillna(False), hard_exit.fillna(False), strict=True):
        if active:
            bad = bad + 1 if not qualifies else 0
            if exits or bad >= exit_count:
                active = False
                bad = good = 0
        else:
            good = good + 1 if qualifies else 0
            if good >= enter_count:
                active = True
                episode += 1
                good = bad = 0
        states.append(active)
        ids.append(episode if active else 0)
    return pd.Series(states, index=core.index), pd.Series(ids, index=core.index, dtype="int64")


def _percentile_previous(values: pd.Series, window: int) -> pd.Series:
    array = values.to_numpy(dtype=float)
    result = np.full(len(array), np.nan)
    for i in range(window, len(array)):
        prior = array[i - window : i]
        if np.isfinite(array[i]) and np.isfinite(prior).all():
            result[i] = 100.0 * float(np.count_nonzero(prior <= array[i])) / window
    return pd.Series(result, index=values.index)


def classify_chop(h4: pd.DataFrame, settings: dict[str, Any]) -> RegimeResult:
    result = h4.copy()
    period = int(settings["atr_period_h4"])
    lookback = int(settings["lookback_h4"])
    result["atr14_h4"] = atr(result, period)
    result["adx14_h4"] = adx(result, int(settings["adx_period_h4"]))
    movement = result["mid_close"].diff().abs().rolling(lookback, min_periods=lookback).sum()
    displacement = (result["mid_close"] - result["mid_close"].shift(lookback)).abs()
    result["er24"] = displacement / movement.replace(0.0, np.nan)
    result["displacement_atr24"] = displacement / result["atr14_h4"]
    width = result["mid_high"].rolling(lookback, min_periods=lookback).max() - result["mid_low"].rolling(lookback, min_periods=lookback).min()
    result["range_width_atr24"] = width / result["atr14_h4"]
    finite = np.isfinite(result[["atr14_h4", "adx14_h4", "er24", "displacement_atr24", "range_width_atr24"]]).all(axis=1)
    core = (
        finite
        & (result["atr14_h4"] > 0)
        & (result["adx14_h4"] <= float(settings["adx_max"]))
        & (result["er24"] <= float(settings["er_max"]))
        & (result["displacement_atr24"] <= float(settings["displacement_atr_max"]))
        & result["range_width_atr24"].between(float(settings["range_width_atr_min"]), float(settings["range_width_atr_max"]), inclusive="both")
    )
    hard_exit = (
        (result["adx14_h4"] > float(settings["exit_adx"]))
        | (result["er24"] > float(settings["exit_er"]))
        | (result["displacement_atr24"] > float(settings["exit_displacement_atr"]))
    )
    result["core_qualifies"] = core
    result["chop_active"], result["chop_episode_id"] = apply_hysteresis(
        core, hard_exit, int(settings["entry_consecutive"]), int(settings["exit_consecutive"])
    )
    result["atr_percentile_756"] = _percentile_previous(result["atr14_h4"], 756)
    result["volatility_subtype"] = np.select(
        [result["atr_percentile_756"] < 33, result["atr_percentile_756"].between(33, 66, inclusive="both"), result["atr_percentile_756"] > 66],
        ["LOW_VOL_CHOP", "MEDIUM_VOL_CHOP", "HIGH_VOL_CHOP"],
        default="VOL_SUBTYPE_UNAVAILABLE",
    )
    result["range_width_subtype"] = np.select(
        [result["range_width_atr24"] < 3.0, result["range_width_atr24"].between(3.0, 5.0, inclusive="both")],
        ["NARROW_CHOP", "MEDIUM_WIDTH_CHOP"], default="WIDE_CHOP",
    )
    ema50 = result["mid_close"].ewm(span=50, adjust=False, min_periods=50).mean()
    result["ema50_slope_atr"] = (ema50 - ema50.shift(6)) / result["atr14_h4"]
    result["drift_subtype"] = np.select(
        [result["ema50_slope_atr"] > 0.25, result["ema50_slope_atr"] < -0.25],
        ["UPWARD_DRIFT_CHOP", "DOWNWARD_DRIFT_CHOP"], default="FLAT_CHOP",
    )
    episodes = episode_census(result)
    return RegimeResult(bars=result, episodes=episodes)


def episode_census(regime: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    active = regime.loc[regime["chop_episode_id"] > 0]
    for episode_id, group in active.groupby("chop_episode_id", sort=True):
        start = group["timestamp_utc"].iloc[0]
        end = group["timestamp_utc"].iloc[-1] + pd.Timedelta(hours=4)
        rows.append({
            "chop_episode_id": int(episode_id), "start_time": start.isoformat(), "end_time": end.isoformat(),
            "duration_hours": float((end - start).total_seconds() / 3600),
            "duration_days": float((end - start).total_seconds() / 86400), "h4_bars": int(len(group)),
            "average_adx": float(group["adx14_h4"].mean()), "median_adx": float(group["adx14_h4"].median()),
            "average_er": float(group["er24"].mean()), "median_er": float(group["er24"].median()),
            "average_atr": float(group["atr14_h4"].mean()),
            "range_width_price": float(group["mid_high"].max() - group["mid_low"].min()),
            "absolute_net_displacement": float(abs(group["mid_close"].iloc[-1] - group["mid_close"].iloc[0])),
        })
    return pd.DataFrame(rows)


def attach_regime(entry_bars: pd.DataFrame, regime_bars: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "timestamp_utc", "chop_active", "chop_episode_id", "adx14_h4", "er24", "displacement_atr24",
        "range_width_atr24", "volatility_subtype", "range_width_subtype", "drift_subtype",
    ]
    right = regime_bars[columns].sort_values("timestamp_utc")
    result = pd.merge_asof(
        entry_bars.sort_values("timestamp_utc"), right, on="timestamp_utc", direction="backward", allow_exact_matches=True
    )
    open_lookup = right.rename(columns={"timestamp_utc": "_h4_close", "chop_active": "chop_active_at_open"})[["_h4_close", "chop_active_at_open"]]
    result = pd.merge_asof(
        result.sort_values("bar_start_utc"), open_lookup.sort_values("_h4_close"),
        left_on="bar_start_utc", right_on="_h4_close", direction="backward", allow_exact_matches=True,
    ).drop(columns=["_h4_close"])
    result["chop_active"] = result["chop_active"].fillna(False).astype(bool)
    result["chop_active_at_open"] = result["chop_active_at_open"].fillna(False).astype(bool)
    result["chop_episode_id"] = result["chop_episode_id"].fillna(0).astype(int)
    return result.sort_values("timestamp_utc").reset_index(drop=True)
