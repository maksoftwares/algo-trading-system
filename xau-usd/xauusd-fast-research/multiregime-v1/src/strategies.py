from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from regime import atr


TREND_ID = "MR_TREND_PULLBACK_CONTINUATION_V1"
COMPRESSION_ID = "MR_COMPRESSION_BREAKOUT_V1"
FAILED_AUCTION_ID = "MR_FAILED_AUCTION_REVERSAL_V1"
FAMILY_IDS = (TREND_ID, COMPRESSION_ID, FAILED_AUCTION_ID)


def build_h1_structure(h1: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    result = h1.copy()
    result["h1_ema20"] = result["mid_close"].ewm(span=20, adjust=False, min_periods=20).mean()
    result["h1_ema50"] = result["mid_close"].ewm(span=50, adjust=False, min_periods=50).mean()
    result["h1_ema20_rising_3"] = result["h1_ema20"] > result["h1_ema20"].shift(3)
    result["h1_ema20_falling_3"] = result["h1_ema20"] < result["h1_ema20"].shift(3)
    result["h1_box_high"] = result["mid_high"].shift(1).rolling(lookback, min_periods=lookback).max()
    result["h1_box_low"] = result["mid_low"].shift(1).rolling(lookback, min_periods=lookback).min()
    result["h1_box_mid"] = 0.5 * (result["h1_box_high"] + result["h1_box_low"])
    result["h1_structure_time"] = result["timestamp_utc"]
    return result


def attach_h1_structure(m15: pd.DataFrame, h1_structure: pd.DataFrame) -> pd.DataFrame:
    columns = ["h1_structure_time", "h1_ema20", "h1_ema50", "h1_ema20_rising_3", "h1_ema20_falling_3", "h1_box_high", "h1_box_low", "h1_box_mid"]
    return pd.merge_asof(
        m15.sort_values("timestamp_utc"), h1_structure[columns].sort_values("h1_structure_time"),
        left_on="timestamp_utc", right_on="h1_structure_time", direction="backward", allow_exact_matches=True,
    ).sort_values("timestamp_utc").reset_index(drop=True)


def _candle_features(frame: pd.DataFrame) -> dict[str, pd.Series]:
    width = (frame["mid_high"] - frame["mid_low"]).replace(0.0, np.nan)
    return {
        "bull_body": (frame["mid_close"] - frame["mid_open"]) / width,
        "bear_body": (frame["mid_open"] - frame["mid_close"]) / width,
        "close_upper": (frame["mid_close"] - frame["mid_low"]) / width,
        "close_lower": (frame["mid_high"] - frame["mid_close"]) / width,
    }


def _rows(frame: pd.DataFrame, mask: pd.Series, family: str, direction: str) -> pd.DataFrame:
    selected = frame.loc[mask.fillna(False)].copy()
    selected["strategy_id"] = family
    selected["direction"] = direction
    selected["signal_time"] = selected["timestamp_utc"]
    return selected


def trend_signals(frame: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    features = _candle_features(frame)
    atr15 = frame["atr15"]
    swing = int(settings["swing_bars"])
    long_condition = (
        (frame["regime"] == "TREND_UP") & (frame["h1_ema20"] > frame["h1_ema50"])
        & frame["h1_ema20_rising_3"].fillna(False) & (frame["mid_low"] <= frame["h1_ema20"])
        & (frame["mid_close"] > frame["h1_ema20"]) & (features["bull_body"] >= 0.50) & (features["close_upper"] >= 0.75)
    )
    short_condition = (
        (frame["regime"] == "TREND_DOWN") & (frame["h1_ema20"] < frame["h1_ema50"])
        & frame["h1_ema20_falling_3"].fillna(False) & (frame["mid_high"] >= frame["h1_ema20"])
        & (frame["mid_close"] < frame["h1_ema20"]) & (features["bear_body"] >= 0.50) & (features["close_lower"] >= 0.75)
    )
    candidates = []
    for direction, condition in (("LONG", long_condition), ("SHORT", short_condition)):
        trigger = condition & ~condition.shift(1, fill_value=False)
        rows = _rows(frame, trigger, TREND_ID, direction)
        index = rows.index
        rows["stop_frozen"] = (
            frame["mid_low"].rolling(swing, min_periods=swing).min().loc[index] - float(settings["stop_buffer_atr"]) * atr15.loc[index]
            if direction == "LONG" else
            frame["mid_high"].rolling(swing, min_periods=swing).max().loc[index] + float(settings["stop_buffer_atr"]) * atr15.loc[index]
        )
        rows["target_kind"] = "R_MULTIPLE"
        rows["target_value"] = float(settings["target_r"])
        rows["required_regime"] = "TREND_UP" if direction == "LONG" else "TREND_DOWN"
        rows["setup_key"] = rows["regime_episode_id"].astype(str) + ":" + direction + ":" + rows["signal_time"].astype(str)
        rows["min_stop_atr"] = float(settings["min_stop_atr"]); rows["max_stop_atr"] = float(settings["max_stop_atr"])
        rows["minimum_reward_r"] = 1.0
        rows["max_hold_hours"] = float(settings["max_hold_hours"]); rows["cooldown_hours"] = float(settings["cooldown_hours"])
        candidates.append(rows)
    return pd.concat(candidates, ignore_index=True) if candidates else pd.DataFrame()


def compression_signals(frame: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    features = _candle_features(frame); atr15 = frame["atr15"]
    upper = frame["h1_box_high"] + float(settings["breakout_buffer_atr"]) * atr15
    lower = frame["h1_box_low"] - float(settings["breakout_buffer_atr"]) * atr15
    long_condition = (frame["regime"] == "COMPRESSION") & (frame["mid_close"] >= upper) & (frame["mid_close"].shift(1) < upper) & (features["bull_body"] >= 0.60) & (features["close_upper"] >= 0.80)
    short_condition = (frame["regime"] == "COMPRESSION") & (frame["mid_close"] <= lower) & (frame["mid_close"].shift(1) > lower) & (features["bear_body"] >= 0.60) & (features["close_lower"] >= 0.80)
    candidates = []
    for direction, condition in (("LONG", long_condition), ("SHORT", short_condition)):
        rows = _rows(frame, condition, COMPRESSION_ID, direction)
        index = rows.index
        rows["stop_frozen"] = (
            frame.loc[index, "mid_low"] - float(settings["stop_buffer_atr"]) * atr15.loc[index]
            if direction == "LONG" else frame.loc[index, "mid_high"] + float(settings["stop_buffer_atr"]) * atr15.loc[index]
        )
        rows["target_kind"] = "R_MULTIPLE"; rows["target_value"] = float(settings["target_r"])
        rows["required_regime"] = "COMPRESSION"
        rows["setup_key"] = rows["h1_structure_time"].astype(str) + ":" + direction
        rows = rows.drop_duplicates("setup_key", keep="first")
        rows["min_stop_atr"] = float(settings["min_stop_atr"]); rows["max_stop_atr"] = float(settings["max_stop_atr"])
        rows["minimum_reward_r"] = 1.0
        rows["max_hold_hours"] = float(settings["max_hold_hours"]); rows["cooldown_hours"] = float(settings["cooldown_hours"])
        candidates.append(rows)
    return pd.concat(candidates, ignore_index=True) if candidates else pd.DataFrame()


def failed_auction_signals(frame: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    features = _candle_features(frame); atr15 = frame["atr15"]
    long_condition = (
        (frame["regime"] == "BALANCED_RANGE") & (frame["mid_low"] <= frame["h1_box_low"] - float(settings["sweep_buffer_atr"]) * atr15)
        & (frame["mid_close"] > frame["h1_box_low"]) & (features["bull_body"] >= 0.40) & (features["close_upper"] >= 0.65)
    )
    short_condition = (
        (frame["regime"] == "BALANCED_RANGE") & (frame["mid_high"] >= frame["h1_box_high"] + float(settings["sweep_buffer_atr"]) * atr15)
        & (frame["mid_close"] < frame["h1_box_high"]) & (features["bear_body"] >= 0.40) & (features["close_lower"] >= 0.65)
    )
    candidates = []
    for direction, condition in (("LONG", long_condition), ("SHORT", short_condition)):
        rows = _rows(frame, condition, FAILED_AUCTION_ID, direction)
        index = rows.index
        rows["stop_frozen"] = (
            frame.loc[index, "mid_low"] - float(settings["stop_buffer_atr"]) * atr15.loc[index]
            if direction == "LONG" else frame.loc[index, "mid_high"] + float(settings["stop_buffer_atr"]) * atr15.loc[index]
        )
        rows["target_kind"] = "ABSOLUTE"; rows["target_value"] = frame.loc[index, "h1_box_mid"]
        rows["required_regime"] = "BALANCED_RANGE"
        rows["setup_key"] = rows["regime_episode_id"].astype(str) + ":" + direction
        rows = rows.drop_duplicates("setup_key", keep="first")
        rows["min_stop_atr"] = 0.0; rows["max_stop_atr"] = float("inf")
        rows["minimum_reward_r"] = float(settings["minimum_reward_r"])
        rows["max_hold_hours"] = float(settings["max_hold_hours"]); rows["cooldown_hours"] = float(settings["cooldown_hours"])
        candidates.append(rows)
    return pd.concat(candidates, ignore_index=True) if candidates else pd.DataFrame()


def generate_signals(m15: pd.DataFrame, h1: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    structure = build_h1_structure(h1, int(config["strategies"]["compression"]["box_h1_bars"]))
    frame = attach_h1_structure(m15, structure)
    frame["atr15"] = atr(frame, 14)
    frames = [
        trend_signals(frame, config["strategies"]["trend"]),
        compression_signals(frame, config["strategies"]["compression"]),
        failed_auction_signals(frame, config["strategies"]["failed_auction"]),
    ]
    frames = [item for item in frames if not item.empty]
    if not frames:
        return pd.DataFrame()
    result = pd.concat(frames, ignore_index=True)
    return result.sort_values(["signal_time", "strategy_id", "direction"], kind="mergesort").reset_index(drop=True)
