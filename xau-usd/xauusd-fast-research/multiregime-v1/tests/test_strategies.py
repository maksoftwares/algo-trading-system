from __future__ import annotations

import pandas as pd

from strategies import build_h1_structure, compression_signals, failed_auction_signals, trend_signals


def _frame() -> pd.DataFrame:
    times = pd.date_range("2020-01-01 00:15", periods=6, freq="15min", tz="UTC")
    frame = pd.DataFrame({"timestamp_utc": times, "bar_start_utc": times - pd.Timedelta(minutes=15)})
    frame["mid_open"] = 100.0; frame["mid_high"] = 101.0; frame["mid_low"] = 99.0; frame["mid_close"] = 100.0
    frame["atr15"] = 1.0; frame["regime"] = "TRANSITION_UNKNOWN"; frame["regime_episode_id"] = 1
    frame["h1_ema20"] = 100.0; frame["h1_ema50"] = 99.0; frame["h1_ema20_rising_3"] = True; frame["h1_ema20_falling_3"] = False
    frame["h1_box_high"] = 101.0; frame["h1_box_low"] = 99.0; frame["h1_box_mid"] = 100.0
    frame["h1_structure_time"] = pd.Timestamp("2019-12-31 23:00", tz="UTC")
    return frame


def test_h1_box_excludes_current_h1_bar() -> None:
    times = pd.date_range("2020-01-01 01:00", periods=22, freq="1h", tz="UTC")
    h1 = pd.DataFrame({"timestamp_utc": times, "mid_close": 100.0, "mid_high": range(22), "mid_low": range(22)})
    result = build_h1_structure(h1, 20)
    assert result.iloc[20]["h1_box_high"] == 19
    assert result.iloc[21]["h1_box_high"] == 20


def test_trend_long_fixture_matches_frozen_numeric_rules() -> None:
    frame = _frame(); index = frame.index[-1]
    frame.loc[index, ["regime", "mid_open", "mid_high", "mid_low", "mid_close"]] = ["TREND_UP", 99.8, 101.0, 99.5, 100.8]
    settings = {"swing_bars": 5, "stop_buffer_atr": 0.1, "min_stop_atr": 0.75, "max_stop_atr": 2.0, "target_r": 2.0, "max_hold_hours": 24, "cooldown_hours": 4}
    result = trend_signals(frame, settings)
    assert len(result.loc[(result["direction"] == "LONG")]) == 1
    assert result.iloc[0]["max_hold_hours"] == 24


def test_compression_breakout_fixture_uses_frozen_box() -> None:
    frame = _frame(); index = frame.index[-1]
    frame.loc[index - 1, "mid_close"] = 100.5
    frame.loc[index, ["regime", "mid_open", "mid_high", "mid_low", "mid_close"]] = ["COMPRESSION", 100.5, 101.8, 100.4, 101.7]
    settings = {"box_h1_bars": 20, "breakout_buffer_atr": 0.1, "stop_buffer_atr": 0.1, "min_stop_atr": 0.75, "max_stop_atr": 1.75, "target_r": 2.0, "max_hold_hours": 12, "cooldown_hours": 6}
    result = compression_signals(frame, settings)
    assert len(result) == 1 and result.iloc[0]["direction"] == "LONG"


def test_failed_auction_fixture_is_distinct_boundary_rejection() -> None:
    frame = _frame(); index = frame.index[-1]
    frame.loc[index, ["regime", "mid_open", "mid_high", "mid_low", "mid_close"]] = ["BALANCED_RANGE", 101.5, 102.0, 100.5, 100.7]
    settings = {"range_h1_bars": 20, "sweep_buffer_atr": 0.1, "stop_buffer_atr": 0.1, "minimum_reward_r": 1.5, "max_hold_hours": 12, "cooldown_hours": 6}
    result = failed_auction_signals(frame, settings)
    assert len(result) == 1 and result.iloc[0]["direction"] == "SHORT"
    assert result.iloc[0]["target_value"] == 100.0
