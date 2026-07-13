from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


REGIMES = ("UNSAFE_SHOCK", "TREND_UP", "TREND_DOWN", "COMPRESSION", "BALANCED_RANGE", "TRANSITION_UNKNOWN")


@dataclass(frozen=True)
class RouterResult:
    bars: pd.DataFrame
    census: pd.DataFrame


def wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["mid_close"].shift(1)
    true_range = pd.concat([
        frame["mid_high"] - frame["mid_low"],
        (frame["mid_high"] - previous).abs(),
        (frame["mid_low"] - previous).abs(),
    ], axis=1).max(axis=1)
    return wilder(true_range, period)


def adx(frame: pd.DataFrame, period: int) -> pd.Series:
    up, down = frame["mid_high"].diff(), -frame["mid_low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=frame.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=frame.index)
    atr_value = atr(frame, period)
    plus_di = 100.0 * wilder(plus_dm, period) / atr_value
    minus_di = 100.0 * wilder(minus_dm, period) / atr_value
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return wilder(dx, period)


def previous_percentile(values: pd.Series, window: int) -> pd.Series:
    array = values.to_numpy(dtype=float)
    result = np.full(len(array), np.nan)
    for index in range(window, len(array)):
        prior = array[index - window:index]
        if np.isfinite(array[index]) and np.isfinite(prior).all():
            result[index] = 100.0 * float(np.count_nonzero(prior <= array[index])) / window
    return pd.Series(result, index=values.index)


def apply_router_hysteresis(raw: pd.Series, entry_count: int, exit_count: int) -> tuple[pd.Series, pd.Series]:
    owner = "TRANSITION_UNKNOWN"
    candidate = "TRANSITION_UNKNOWN"
    candidate_count = nonqualifying = episode = 0
    owners: list[str] = []
    episodes: list[int] = []
    for desired in raw:
        desired = str(desired)
        if desired == "UNSAFE_SHOCK":
            if owner != desired:
                episode += 1
            owner, candidate, candidate_count, nonqualifying = desired, desired, 0, 0
        elif desired == owner:
            candidate, candidate_count, nonqualifying = desired, 0, 0
        else:
            nonqualifying += 1
            if desired == candidate:
                candidate_count += 1
            else:
                candidate, candidate_count = desired, 1
            if nonqualifying >= exit_count and candidate_count >= entry_count:
                owner = candidate
                episode += 1
                candidate_count = nonqualifying = 0
        owners.append(owner)
        episodes.append(episode)
    return pd.Series(owners, index=raw.index), pd.Series(episodes, index=raw.index, dtype="int64")


def classify_regimes(h4: pd.DataFrame, settings: dict[str, Any]) -> RouterResult:
    frame = h4.copy()
    atr_period = int(settings["atr_period"])
    lookback = int(settings["er_lookback"])
    frame["atr14_h4"] = atr(frame, atr_period)
    frame["adx14_h4"] = adx(frame, int(settings["adx_period"]))
    movement = frame["mid_close"].diff().abs().rolling(lookback, min_periods=lookback).sum()
    displacement = (frame["mid_close"] - frame["mid_close"].shift(lookback)).abs()
    frame["er24_h4"] = displacement / movement.replace(0.0, np.nan)
    frame["ema50_h4"] = frame["mid_close"].ewm(span=int(settings["ema_period"]), adjust=False, min_periods=int(settings["ema_period"])).mean()
    frame["ema_slope_atr_h4"] = (frame["ema50_h4"] - frame["ema50_h4"].shift(int(settings["ema_slope_bars"]))) / frame["atr14_h4"]
    width = frame["mid_high"].rolling(int(settings["range_lookback"]), min_periods=int(settings["range_lookback"])).max() - frame["mid_low"].rolling(int(settings["range_lookback"]), min_periods=int(settings["range_lookback"])).min()
    frame["range_width_atr24_h4"] = width / frame["atr14_h4"]
    frame["displacement_atr24_h4"] = displacement / frame["atr14_h4"]
    frame["atr_percentile_h4"] = previous_percentile(frame["atr14_h4"], int(settings["atr_percentile_lookback"]))
    frame["opening_gap_atr_h4"] = (frame["mid_open"] - frame["mid_close"].shift(1)).abs() / frame["atr14_h4"]
    finite = np.isfinite(frame[["atr14_h4", "adx14_h4", "er24_h4", "ema50_h4", "ema_slope_atr_h4", "range_width_atr24_h4", "displacement_atr24_h4", "atr_percentile_h4"]]).all(axis=1)
    unsafe = (~frame["data_valid"]) | (frame["atr_percentile_h4"] >= float(settings["unsafe_atr_percentile"])) | (frame["opening_gap_atr_h4"] >= float(settings["unsafe_gap_atr"]))
    trend_up = finite & (frame["adx14_h4"] >= float(settings["trend_adx_min"])) & (frame["er24_h4"] >= float(settings["trend_er_min"])) & (frame["mid_close"] > frame["ema50_h4"]) & (frame["ema_slope_atr_h4"] >= float(settings["trend_slope_atr_min"]))
    trend_down = finite & (frame["adx14_h4"] >= float(settings["trend_adx_min"])) & (frame["er24_h4"] >= float(settings["trend_er_min"])) & (frame["mid_close"] < frame["ema50_h4"]) & (frame["ema_slope_atr_h4"] <= -float(settings["trend_slope_atr_min"]))
    compression = finite & (frame["adx14_h4"] <= float(settings["compression_adx_max"])) & (frame["atr_percentile_h4"] <= float(settings["compression_atr_percentile_max"])) & (frame["range_width_atr24_h4"] <= float(settings["compression_width_atr_max"])) & ~trend_up & ~trend_down
    balanced = finite & (frame["adx14_h4"] <= float(settings["range_adx_max"])) & (frame["er24_h4"] <= float(settings["range_er_max"])) & (frame["displacement_atr24_h4"] <= float(settings["range_displacement_atr_max"])) & frame["range_width_atr24_h4"].between(float(settings["range_width_atr_min"]), float(settings["range_width_atr_max"]), inclusive="both") & ~trend_up & ~trend_down & ~compression
    frame["raw_regime"] = np.select(
        [unsafe, trend_up, trend_down, compression, balanced],
        ["UNSAFE_SHOCK", "TREND_UP", "TREND_DOWN", "COMPRESSION", "BALANCED_RANGE"],
        default="TRANSITION_UNKNOWN",
    )
    frame["regime"], frame["regime_episode_id"] = apply_router_hysteresis(frame["raw_regime"], int(settings["entry_consecutive"]), int(settings["exit_consecutive"]))
    rows = []
    for episode_id, group in frame.groupby("regime_episode_id", sort=True):
        if int(episode_id) == 0:
            continue
        rows.append({
            "regime_episode_id": int(episode_id), "regime": str(group["regime"].iloc[0]),
            "start_time": group["timestamp_utc"].iloc[0], "end_time": group["timestamp_utc"].iloc[-1],
            "h4_bars": int(len(group)), "duration_hours": float(len(group) * 4),
            "median_adx": float(group["adx14_h4"].median()), "median_er": float(group["er24_h4"].median()),
        })
    return RouterResult(frame, pd.DataFrame(rows))


def attach_regime(bars: pd.DataFrame, h4: pd.DataFrame) -> pd.DataFrame:
    columns = ["timestamp_utc", "regime", "raw_regime", "regime_episode_id", "atr14_h4", "adx14_h4", "er24_h4", "atr_percentile_h4", "ema_slope_atr_h4"]
    right = h4[columns].sort_values("timestamp_utc")
    result = pd.merge_asof(bars.sort_values("timestamp_utc"), right, on="timestamp_utc", direction="backward", allow_exact_matches=True)
    open_right = right.rename(columns={"timestamp_utc": "_h4_close", "regime": "regime_at_open", "regime_episode_id": "regime_episode_at_open"})[["_h4_close", "regime_at_open", "regime_episode_at_open"]]
    result = pd.merge_asof(result.sort_values("bar_start_utc"), open_right, left_on="bar_start_utc", right_on="_h4_close", direction="backward", allow_exact_matches=True).drop(columns="_h4_close")
    result["regime"] = result["regime"].fillna("TRANSITION_UNKNOWN")
    result["regime_at_open"] = result["regime_at_open"].fillna("TRANSITION_UNKNOWN")
    result["regime_episode_id"] = result["regime_episode_id"].fillna(0).astype(int)
    result["regime_episode_at_open"] = result["regime_episode_at_open"].fillna(0).astype(int)
    return result.sort_values("timestamp_utc").reset_index(drop=True)
