from __future__ import annotations

import pandas as pd


def synthetic_context_for_expert(expert: str) -> dict:
    if expert == "asia_range_london_breakout_v0":
        return _asia_range_london_breakout_context()
    if expert == "asia_range_london_failed_break_reversal_v0":
        return _asia_range_london_failed_break_reversal_context()
    if expert == "compression_retest_continuation_v0":
        return _compression_retest_continuation_context()
    if expert == "daily_pivot_reclaim_v0":
        return _daily_pivot_reclaim_context()
    if expert == "trend_pullback":
        return _trend_context()
    if expert == "breakout_retest":
        return _breakout_context()
    if expert == "range_mr":
        return _range_context()
    if expert == "emr_inactivity_long_v0":
        return _emr_inactivity_long_context()
    if expert == "extreme_activity_mean_reversion_v0":
        return _extreme_activity_mean_reversion_context()
    if expert == "london_fix_continuation_v0":
        return _london_fix_continuation_context()
    if expert == "liquidity_sweep_reversal_v0":
        return _liquidity_sweep_reversal_context()
    if expert == "m15_inside_bar_breakout_v0":
        return _m15_inside_bar_breakout_context()
    if expert == "m5_impulse_continuation_v0":
        return _m5_impulse_continuation_context()
    if expert == "ny_failed_london_reversal_v0":
        return _ny_failed_london_reversal_context()
    if expert == "ny_am_pullback_continuation_v0":
        return _ny_am_pullback_continuation_context()
    if expert == "ny_london_overlap_compression_break_v0":
        return _ny_london_overlap_compression_break_context()
    if expert == "opening_drive_failed_continuation_v0":
        return _opening_drive_failed_continuation_context()
    if expert == "post_spike_short_v0":
        return _post_spike_short_context()
    if expert == "previous_day_extreme_retest_v0":
        return _previous_day_extreme_retest_context()
    if expert == "round_number_retest_v0":
        return _round_number_retest_context()
    if expert == "session_vwap_reclaim_v0":
        return _session_vwap_reclaim_context()
    if expert == "symbol_normalized_round_retest_v0":
        return _round_number_retest_context()
    if expert == "symbol_round_sweep_reversal_v0":
        return _symbol_round_sweep_reversal_context()
    if expert == "squeeze_breakout_long_v0":
        return _squeeze_breakout_long_context()
    if expert == "swing_breakout_retest_v0":
        return _swing_breakout_retest_context()
    if expert == "weekly_level_reclaim_v0":
        return _weekly_level_reclaim_context()
    raise ValueError(f"Unknown synthetic expert {expert!r}.")


def _base_m5(start: str, periods: int) -> pd.DataFrame:
    times = pd.date_range(start, periods=periods, freq="5min")
    return pd.DataFrame(
        {
            "timestamp_utc": times + pd.Timedelta(minutes=5),
            "bar_start_utc": times,
            "open": [100.0] * periods,
            "high": [100.2] * periods,
            "low": [99.8] * periods,
            "close": [100.0] * periods,
            "mid_open": [100.0] * periods,
            "mid_close": [100.0] * periods,
            "bid_open": [99.9] * periods,
            "ask_open": [100.1] * periods,
            "bid_close": [99.9] * periods,
            "ask_close": [100.1] * periods,
        }
    )


def _trend_context() -> dict:
    m5 = _base_m5("2016-01-04T10:00:00Z", 13)
    m5["low"] = [99.8] * 9 + [99.4, 100.0, 100.0, 100.0]
    m5["open"] = [100.0] * 13
    m5["close"] = [100.0] * 9 + [100.2, 101.8, 101.8, 101.8]
    m5["high"] = [100.2] * 9 + [100.3, 102.2, 102.2, 102.2]
    m5["mid_open"] = m5["open"]
    m5["mid_close"] = m5["close"]
    m5["bid_open"] = m5["open"] - 0.1
    m5["ask_open"] = m5["open"] + 0.1
    m5["bid_close"] = m5["close"] - 0.1
    m5["ask_close"] = m5["close"] + 0.1
    m5["bullish_engulfing"] = [False] * 13
    m5["bearish_engulfing"] = [False] * 13
    m5["bullish_pin_bar"] = [False] * 9 + [True] + [False] * 3
    m5["bearish_pin_bar"] = [False] * 13

    m15 = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-04T10:50:00Z"],
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.2],
            "ema21": [100.0],
            "atr14": [2.0],
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-04T10:00:00Z"],
            "open": [100.0],
            "high": [102.0],
            "low": [98.0],
            "close": [101.0],
            "ema50": [110.0],
            "ema200": [100.0],
            "ema50_slope20": [1.0],
            "atr14": [2.0],
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _breakout_context() -> dict:
    times = pd.date_range("2016-01-05T10:00:00Z", periods=24, freq="5min")
    m5 = _base_m5("2016-01-05T10:00:00Z", 24)
    m5["timestamp_utc"] = times + pd.Timedelta(minutes=5)
    m5["atr14"] = [1.0] * 24
    m5["previous_daily_high"] = [100.0] * 24
    m5["previous_daily_low"] = [90.0] * 24
    m5["previous_weekly_high"] = [pd.NA] * 24
    m5["previous_weekly_low"] = [pd.NA] * 24
    m5["latest_swing_high"] = [pd.NA] * 24
    m5["latest_swing_high_time_utc"] = [pd.NaT] * 24
    m5["latest_swing_low"] = [pd.NA] * 24
    m5["latest_swing_low_time_utc"] = [pd.NaT] * 24
    m5.loc[18, ["open", "high", "low", "close"]] = [100.0, 100.8, 99.8, 100.4]
    m5.loc[20, ["open", "high", "low", "close"]] = [100.2, 100.4, 100.03, 100.1]
    m5.loc[21, ["open", "high", "low", "close"]] = [100.1, 100.5, 100.0, 100.3]
    m5.loc[22, ["open", "high", "low", "close"]] = [100.3, 101.3, 100.3, 101.1]
    for column in ("mid_open", "bid_open", "ask_open"):
        m5[column] = m5["open"]
    for column in ("mid_close", "bid_close", "ask_close"):
        m5[column] = m5["close"]
    m5["bid_open"] = m5["open"] - 0.1
    m5["ask_open"] = m5["open"] + 0.1
    m5["bid_close"] = m5["close"] - 0.1
    m5["ask_close"] = m5["close"] + 0.1
    return {"M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


def _swing_breakout_retest_context() -> dict:
    context = _breakout_context()
    m5 = context["M5"].copy()
    m5["previous_daily_high"] = [pd.NA] * len(m5)
    m5["previous_daily_low"] = [pd.NA] * len(m5)
    m5["previous_weekly_high"] = [pd.NA] * len(m5)
    m5["previous_weekly_low"] = [pd.NA] * len(m5)
    m5["latest_swing_high"] = [100.0] * len(m5)
    m5["latest_swing_high_time_utc"] = [pd.Timestamp("2016-01-05T08:00:00Z")] * len(m5)
    m5["latest_swing_low"] = [90.0] * len(m5)
    m5["latest_swing_low_time_utc"] = [pd.Timestamp("2016-01-05T08:00:00Z")] * len(m5)
    context["M5"] = m5
    return context


def _range_context() -> dict:
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2016-01-04T00:00:00Z", periods=30, freq="1h"),
            "open": [105.0] * 30,
            "high": [106.0] * 30,
            "low": [104.0] * 30,
            "close": [105.0] * 30,
            "adx14": [10.0] * 30,
        }
    )
    highs = [106.0] * 50
    lows = [104.0] * 50
    for index in (0, 10, 20):
        highs[index] = 110.0
    for index in (5, 15, 25):
        lows[index] = 100.0
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2016-01-04T00:00:00Z", periods=50, freq="15min"),
            "open": [105.0] * 50,
            "high": highs,
            "low": lows,
            "close": [105.0] * 50,
            "atr14": [2.0] * 50,
        }
    )
    m5 = _base_m5("2016-01-05T05:00:00Z", 4)
    m5.loc[0, ["open", "high", "low", "close"]] = [100.2, 100.4, 100.1, 100.3]
    m5.loc[1, ["open", "high", "low", "close"]] = [100.2, 100.3, 99.8, 100.1]
    m5.loc[2, ["open", "high", "low", "close"]] = [100.0, 110.5, 100.0, 110.0]
    m5["bullish_pin_bar"] = [True, False, False, False]
    m5["bearish_pin_bar"] = [False, False, False, False]
    return {"H1": h1, "M15": m15, "M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


def _squeeze_breakout_long_context() -> dict:
    m15_times = pd.date_range("2024-01-01T00:15:00Z", periods=140, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 140,
            "high": [102.0] * 120 + [100.1] * 20,
            "low": [98.0] * 120 + [99.9] * 20,
            "close": [100.0] * 140,
        }
    )

    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=430, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 430,
            "high": [100.15] * 430,
            "low": [99.95] * 430,
            "close": [100.0] * 430,
            "atr14": [1.0] * 409 + [0.4] * 21,
            "mid_open": [100.0] * 430,
            "mid_close": [100.0] * 430,
            "bid_open": [99.9] * 430,
            "ask_open": [100.1] * 430,
            "bid_close": [99.9] * 430,
            "ask_close": [100.1] * 430,
        }
    )
    m5.loc[410, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.7, 99.95, 100.55, 0.4]
    m5.loc[410, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.0,
        100.55,
        99.9,
        100.1,
        100.45,
        100.65,
    ]

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T01:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [99.0] * 40,
            "close": [101.0] * 40,
            "ema50": [100.0] * 40,
            "ema50_slope12": [0.1] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _post_spike_short_context() -> dict:
    m5_times = pd.date_range("2024-02-01T00:05:00Z", periods=150, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 150,
            "high": [100.2] * 150,
            "low": [99.8] * 150,
            "close": [100.0] * 150,
            "atr14": [0.5] * 150,
            "mid_open": [100.0] * 150,
            "mid_close": [100.0] * 150,
            "bid_open": [99.9] * 150,
            "ask_open": [100.1] * 150,
            "bid_close": [99.9] * 150,
            "ask_close": [100.1] * 150,
        }
    )
    m5.loc[120, ["open", "high", "low", "close"]] = [100.0, 100.8, 99.95, 100.7]
    m5.loc[121, ["open", "high", "low", "close"]] = [100.7, 101.35, 100.6, 101.2]
    m5.loc[122, ["open", "high", "low", "close"]] = [101.2, 101.55, 101.0, 101.35]
    m5.loc[123, ["open", "high", "low", "close"]] = [101.4, 101.60, 100.75, 100.85]
    for idx in (120, 121, 122, 123):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-02-01T00:15:00Z", periods=60, freq="15min"),
            "open": [100.0] * 60,
            "high": [100.5] * 60,
            "low": [99.4] * 60,
            "close": [100.0] * 60,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-31T00:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [101.0] * 60,
            "low": [99.0] * 60,
            "close": [99.6] * 60,
            "ema50": [100.0] * 60,
            "ema50_slope12": [-0.1] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _emr_inactivity_long_context() -> dict:
    m15_times = pd.date_range("2024-03-01T00:15:00Z", periods=150, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 150,
            "high": [102.0] * 120 + [100.08] * 30,
            "low": [98.0] * 120 + [99.92] * 30,
            "close": [100.0] * 150,
        }
    )

    m5_times = pd.date_range("2024-03-01T00:05:00Z", periods=440, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 440,
            "high": [100.10] * 440,
            "low": [99.90] * 440,
            "close": [100.0] * 440,
            "atr14": [1.0] * 408 + [0.35] * 32,
            "mid_open": [100.0] * 440,
            "mid_close": [100.0] * 440,
            "bid_open": [99.9] * 440,
            "ask_open": [100.1] * 440,
            "bid_close": [99.9] * 440,
            "ask_close": [100.1] * 440,
        }
    )
    m5.loc[410, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.05, 99.20, 99.35, 0.35]
    m5.loc[411, ["open", "high", "low", "close", "atr14"]] = [99.35, 99.45, 98.95, 99.05, 0.35]
    m5.loc[412, ["open", "high", "low", "close", "atr14"]] = [99.05, 99.10, 98.80, 98.90, 0.35]
    m5.loc[413, ["open", "high", "low", "close", "atr14"]] = [98.90, 100.15, 98.75, 100.05, 0.35]
    for idx in (410, 411, 412, 413):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T01:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [101.0] * 60,
            "low": [99.0] * 60,
            "close": [99.8] * 60,
            "ema50": [100.0] * 60,
            "ema50_slope12": [-0.05] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _ny_failed_london_reversal_context() -> dict:
    m5_times = pd.date_range("2024-04-01T06:05:00Z", periods=160, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 160,
            "high": [100.3] * 160,
            "low": [99.7] * 160,
            "close": [100.0] * 160,
            "atr14": [0.5] * 160,
            "mid_open": [100.0] * 160,
            "mid_close": [100.0] * 160,
            "bid_open": [99.9] * 160,
            "ask_open": [100.1] * 160,
            "bid_close": [99.9] * 160,
            "ask_close": [100.1] * 160,
        }
    )
    london_mask = (m5["bar_start_utc"].dt.hour >= 7) & (m5["bar_start_utc"].dt.hour < 11)
    m5.loc[london_mask, ["high", "low"]] = [101.0, 99.0]
    m5.loc[90, ["open", "high", "low", "close"]] = [101.50, 101.60, 100.40, 100.60]
    m5.loc[90, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        101.50,
        100.60,
        101.40,
        101.60,
        100.50,
        100.70,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T06:15:00Z", periods=60, freq="15min"),
            "open": [100.0] * 60,
            "high": [101.0] * 60,
            "low": [99.0] * 60,
            "close": [100.0] * 60,
            "atr14": [1.2] * 60,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T01:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _liquidity_sweep_reversal_context() -> dict:
    m5_times = pd.date_range("2024-04-01T00:05:00Z", periods=440, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 440,
            "high": [100.2] * 440,
            "low": [99.8] * 440,
            "close": [100.0] * 440,
            "atr14": [0.5] * 440,
            "mid_open": [100.0] * 440,
            "mid_close": [100.0] * 440,
            "bid_open": [99.9] * 440,
            "ask_open": [100.1] * 440,
            "bid_close": [99.9] * 440,
            "ask_close": [100.1] * 440,
        }
    )
    first_day = m5["bar_start_utc"].dt.strftime("%Y-%m-%d") == "2024-04-01"
    m5.loc[first_day, ["high", "low"]] = [101.0, 99.0]
    m5.loc[390, ["open", "high", "low", "close"]] = [101.15, 102.00, 100.30, 100.55]
    m5.loc[390, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        101.15,
        100.55,
        101.05,
        101.25,
        100.45,
        100.65,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T00:15:00Z", periods=120, freq="15min"),
            "open": [100.0] * 120,
            "high": [101.0] * 120,
            "low": [99.0] * 120,
            "close": [100.0] * 120,
            "atr14": [1.2] * 120,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T00:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [98.0] * 40,
            "close": [100.0] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _daily_pivot_reclaim_context() -> dict:
    m5_times = pd.date_range("2024-04-01T00:05:00Z", periods=440, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 440,
            "high": [100.2] * 440,
            "low": [99.8] * 440,
            "close": [100.0] * 440,
            "atr14": [0.5] * 440,
            "mid_open": [100.0] * 440,
            "mid_close": [100.0] * 440,
            "bid_open": [99.9] * 440,
            "ask_open": [100.1] * 440,
            "bid_close": [99.9] * 440,
            "ask_close": [100.1] * 440,
        }
    )
    first_day = m5["bar_start_utc"].dt.strftime("%Y-%m-%d") == "2024-04-01"
    m5.loc[first_day, ["high", "low", "close"]] = [101.0, 99.0, 100.0]
    m5.loc[390, ["open", "high", "low", "close"]] = [99.65, 100.45, 99.35, 100.30]
    m5.loc[390, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        99.65,
        100.30,
        99.55,
        99.75,
        100.20,
        100.40,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T00:15:00Z", periods=120, freq="15min"),
            "open": [100.0] * 120,
            "high": [101.0] * 120,
            "low": [99.0] * 120,
            "close": [100.0] * 120,
            "atr14": [1.0] * 120,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T00:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [98.0] * 40,
            "close": [100.0] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _m15_inside_bar_breakout_context() -> dict:
    m5_times = pd.date_range("2024-05-01T06:05:00Z", periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 180,
            "high": [100.2] * 180,
            "low": [99.8] * 180,
            "close": [100.0] * 180,
            "atr14": [0.5] * 180,
            "mid_open": [100.0] * 180,
            "mid_close": [100.0] * 180,
            "bid_open": [99.9] * 180,
            "ask_open": [100.1] * 180,
            "bid_close": [99.9] * 180,
            "ask_close": [100.1] * 180,
        }
    )
    m5.loc[74, ["open", "high", "low", "close"]] = [100.35, 101.05, 100.30, 100.90]
    m5.loc[74, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.35,
        100.90,
        100.25,
        100.45,
        100.80,
        101.00,
    ]

    m15_times = pd.date_range("2024-05-01T06:15:00Z", periods=70, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 70,
            "high": [100.3] * 70,
            "low": [99.7] * 70,
            "close": [100.0] * 70,
            "atr14": [0.7] * 70,
        }
    )
    m15.loc[22, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.80, 99.20, 100.50, 0.7]
    m15.loc[23, ["open", "high", "low", "close", "atr14"]] = [100.35, 100.60, 99.80, 100.20, 0.7]

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:00:00Z", periods=30, freq="1h"),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [101.0] * 30,
            "ema50": [100.0] * 30,
            "ema50_slope12": [0.1] * 30,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _m5_impulse_continuation_context() -> dict:
    m5_times = pd.date_range("2024-05-01T06:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.2] * 120,
            "low": [99.8] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    m5.loc[74, ["open", "high", "low", "close"]] = [100.00, 100.45, 99.95, 100.35]
    m5.loc[75, ["open", "high", "low", "close"]] = [100.35, 100.82, 100.30, 100.76]
    for idx in (74, 75):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:00:00Z", periods=30, freq="1h"),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [101.0] * 30,
            "ema50": [100.0] * 30,
            "ema50_slope12": [0.1] * 30,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _london_fix_continuation_context() -> dict:
    m5_times = pd.date_range("2024-06-03T11:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.3] * 120,
            "low": [99.7] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    local_starts = pd.to_datetime(m5["bar_start_utc"], utc=True).dt.tz_convert("Europe/London")
    pre_fix_mask = (
        (local_starts.dt.hour == 14)
        & (local_starts.dt.minute >= 30)
        & (local_starts.dt.minute < 60)
    )
    m5.loc[pre_fix_mask, ["high", "low"]] = [101.0, 99.0]
    m5.loc[36, ["open", "high", "low", "close"]] = [100.80, 101.60, 100.70, 101.40]
    m5.loc[36, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.80,
        101.40,
        100.70,
        100.90,
        101.30,
        101.50,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-06-03T13:15:00Z", periods=40, freq="15min"),
            "open": [100.0] * 40,
            "high": [101.0] * 40,
            "low": [99.0] * 40,
            "close": [100.0] * 40,
            "atr14": [1.0] * 40,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-06-03T08:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _extreme_activity_mean_reversion_context() -> dict:
    m5_times = pd.date_range("2024-05-01T00:05:00Z", periods=360, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 360,
            "high": [100.2] * 360,
            "low": [99.8] * 360,
            "close": [100.0] * 360,
            "atr14": [1.0] * 360,
            "mid_open": [100.0] * 360,
            "mid_close": [100.0] * 360,
            "bid_open": [99.9] * 360,
            "ask_open": [100.1] * 360,
            "bid_close": [99.9] * 360,
            "ask_close": [100.1] * 360,
        }
    )
    m5.loc[320, ["open", "high", "low", "close"]] = [102.50, 103.00, 99.80, 100.05]
    m5.loc[320, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        102.50,
        100.05,
        102.40,
        102.60,
        99.95,
        100.15,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:15:00Z", periods=140, freq="15min"),
            "open": [100.0] * 140,
            "high": [101.0] * 140,
            "low": [99.0] * 140,
            "close": [100.0] * 140,
            "atr14": [1.5] * 140,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [98.0] * 40,
            "close": [100.0] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _compression_retest_continuation_context() -> dict:
    m15_times = pd.date_range("2024-07-01T00:15:00Z", periods=150, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 150,
            "high": [102.0] * 120 + [100.10] * 30,
            "low": [98.0] * 120 + [99.90] * 30,
            "close": [100.0] * 150,
        }
    )

    m5_times = pd.date_range("2024-07-01T00:05:00Z", periods=450, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 450,
            "high": [100.08] * 450,
            "low": [99.92] * 450,
            "close": [100.0] * 450,
            "atr14": [0.4] * 450,
            "mid_open": [100.0] * 450,
            "mid_close": [100.0] * 450,
            "bid_open": [99.9] * 450,
            "ask_open": [100.1] * 450,
            "bid_close": [99.9] * 450,
            "ask_close": [100.1] * 450,
        }
    )
    m5.loc[410, ["open", "high", "low", "close"]] = [100.00, 100.75, 99.98, 100.55]
    m5.loc[413, ["open", "high", "low", "close"]] = [100.30, 100.38, 100.12, 100.18]
    m5.loc[415, ["open", "high", "low", "close"]] = [100.25, 100.70, 100.22, 100.60]
    for idx in (410, 413, 415):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-07-01T00:00:00Z", periods=50, freq="1h"),
            "open": [100.0] * 50,
            "high": [102.0] * 50,
            "low": [98.0] * 50,
            "close": [100.0] * 50,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _asia_range_london_breakout_context() -> dict:
    m5_times = pd.date_range("2024-08-01T00:05:00Z", periods=160, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 160,
            "high": [100.3] * 160,
            "low": [99.7] * 160,
            "close": [100.0] * 160,
            "atr14": [0.5] * 160,
            "mid_open": [100.0] * 160,
            "mid_close": [100.0] * 160,
            "bid_open": [99.9] * 160,
            "ask_open": [100.1] * 160,
            "bid_close": [99.9] * 160,
            "ask_close": [100.1] * 160,
        }
    )
    asia_mask = (m5["bar_start_utc"].dt.hour >= 0) & (m5["bar_start_utc"].dt.hour < 6)
    m5.loc[asia_mask, ["high", "low"]] = [101.0, 99.0]
    m5.loc[90, ["open", "high", "low", "close"]] = [100.80, 101.70, 100.60, 101.50]
    m5.loc[90, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.80,
        101.50,
        100.70,
        100.90,
        101.40,
        101.60,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-08-01T00:15:00Z", periods=80, freq="15min"),
            "open": [100.0] * 80,
            "high": [101.0] * 80,
            "low": [99.0] * 80,
            "close": [100.0] * 80,
            "atr14": [1.2] * 80,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-08-01T00:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _asia_range_london_failed_break_reversal_context() -> dict:
    context = _asia_range_london_breakout_context()
    m5 = context["M5"].copy()
    m5.loc[90, ["open", "high", "low", "close"]] = [101.30, 101.60, 100.40, 100.60]
    m5.loc[90, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        101.30,
        100.60,
        101.20,
        101.40,
        100.50,
        100.70,
    ]
    context["M5"] = m5
    return context


def _previous_day_extreme_retest_context() -> dict:
    m5_times = pd.date_range("2024-09-01T00:05:00Z", periods=600, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 600,
            "high": [100.2] * 600,
            "low": [99.8] * 600,
            "close": [100.0] * 600,
            "atr14": [0.5] * 600,
            "mid_open": [100.0] * 600,
            "mid_close": [100.0] * 600,
            "bid_open": [99.9] * 600,
            "ask_open": [100.1] * 600,
            "bid_close": [99.9] * 600,
            "ask_close": [100.1] * 600,
        }
    )
    first_day = m5["bar_start_utc"].dt.strftime("%Y-%m-%d") == "2024-09-01"
    m5.loc[first_day, ["high", "low"]] = [101.0, 99.0]
    m5.loc[400, ["open", "high", "low", "close"]] = [100.20, 101.75, 100.15, 101.50]
    m5.loc[403, ["open", "high", "low", "close"]] = [101.30, 101.35, 101.05, 101.15]
    m5.loc[405, ["open", "high", "low", "close"]] = [101.20, 101.70, 101.15, 101.60]
    for idx in (400, 403, 405):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-09-01T00:15:00Z", periods=220, freq="15min"),
            "open": [100.0] * 220,
            "high": [101.0] * 220,
            "low": [99.0] * 220,
            "close": [100.0] * 220,
            "atr14": [1.0] * 220,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-09-01T00:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [102.0] * 60,
            "low": [98.0] * 60,
            "close": [100.0] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _round_number_retest_context() -> dict:
    context = _breakout_context()
    m5 = context["M5"].copy()
    m5["previous_daily_high"] = [pd.NA] * len(m5)
    m5["previous_daily_low"] = [pd.NA] * len(m5)
    m5["previous_weekly_high"] = [pd.NA] * len(m5)
    m5["previous_weekly_low"] = [pd.NA] * len(m5)
    m5["latest_swing_high"] = [pd.NA] * len(m5)
    m5["latest_swing_high_time_utc"] = [pd.NaT] * len(m5)
    m5["latest_swing_low"] = [pd.NA] * len(m5)
    m5["latest_swing_low_time_utc"] = [pd.NaT] * len(m5)
    context["M5"] = m5
    return context


def _symbol_round_sweep_reversal_context() -> dict:
    m5 = _base_m5("2024-12-03T09:00:00Z", 40)
    m5["atr14"] = [1.0] * 40
    m5.loc[30, ["open", "high", "low", "close"]] = [100.00, 100.45, 99.55, 100.25]
    m5.loc[30, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.00,
        100.25,
        99.90,
        100.10,
        100.15,
        100.35,
    ]
    return {"M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


def _ny_am_pullback_continuation_context() -> dict:
    m5_times = pd.date_range("2024-10-01T13:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.2] * 120,
            "low": [99.8] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    m5.loc[6, ["open", "high", "low", "close"]] = [100.00, 100.35, 99.90, 100.25]
    m5.loc[7, ["open", "high", "low", "close"]] = [100.25, 100.75, 100.20, 100.65]
    m5.loc[8, ["open", "high", "low", "close"]] = [100.65, 101.10, 100.60, 101.00]
    m5.loc[9, ["open", "high", "low", "close"]] = [101.00, 101.35, 100.95, 101.20]
    m5.loc[10, ["open", "high", "low", "close"]] = [101.20, 101.40, 101.00, 101.25]
    m5.loc[11, ["open", "high", "low", "close"]] = [101.25, 101.45, 101.05, 101.30]
    m5.loc[24, ["open", "high", "low", "close"]] = [100.95, 101.00, 100.57, 100.75]
    m5.loc[26, ["open", "high", "low", "close"]] = [100.82, 101.28, 100.78, 101.20]
    for idx in (6, 7, 8, 9, 10, 11, 24, 26):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T13:15:00Z", periods=50, freq="15min"),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
            "atr14": [1.0] * 50,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T10:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _ny_london_overlap_compression_break_context() -> dict:
    m15_times = pd.date_range("2024-10-01T00:15:00Z", periods=180, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 180,
            "high": [102.0] * 130 + [100.12] * 50,
            "low": [98.0] * 130 + [99.88] * 50,
            "close": [100.0] * 180,
        }
    )

    m5_times = pd.date_range("2024-10-01T00:05:00Z", periods=500, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 500,
            "high": [100.10] * 500,
            "low": [99.90] * 500,
            "close": [100.0] * 500,
            "atr14": [1.0] * 448 + [0.35] * 52,
            "mid_open": [100.0] * 500,
            "mid_close": [100.0] * 500,
            "bid_open": [99.9] * 500,
            "ask_open": [100.1] * 500,
            "bid_close": [99.9] * 500,
            "ask_close": [100.1] * 500,
        }
    )
    m5.loc[450, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.58, 99.96, 100.50, 0.35]
    m5.loc[450, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.0,
        100.50,
        99.9,
        100.1,
        100.40,
        100.60,
    ]

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T00:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [102.0] * 60,
            "low": [99.0] * 60,
            "close": [101.0] * 60,
            "ema50": [100.0] * 60,
            "ema50_slope12": [0.1] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _opening_drive_failed_continuation_context() -> dict:
    m5_times = pd.date_range("2024-10-01T13:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.2] * 120,
            "low": [99.8] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    for idx, values in {
        6: (100.00, 100.45, 99.95, 100.35),
        7: (100.35, 100.85, 100.30, 100.75),
        8: (100.75, 101.10, 100.70, 101.00),
        9: (101.00, 101.20, 100.92, 101.05),
        10: (101.05, 101.25, 100.95, 101.10),
        11: (101.10, 101.30, 101.00, 101.15),
        16: (101.55, 101.62, 100.80, 100.95),
    }.items():
        m5.loc[idx, ["open", "high", "low", "close"]] = values
        m5.loc[idx, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
            values[0],
            values[3],
            values[0] - 0.1,
            values[0] + 0.1,
            values[3] - 0.1,
            values[3] + 0.1,
        ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T13:15:00Z", periods=50, freq="15min"),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T10:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _weekly_level_reclaim_context() -> dict:
    m5_times = pd.date_range("2024-11-04T00:05:00Z", periods=2300, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 2300,
            "high": [100.2] * 2300,
            "low": [99.8] * 2300,
            "close": [100.0] * 2300,
            "atr14": [0.5] * 2300,
            "mid_open": [100.0] * 2300,
            "mid_close": [100.0] * 2300,
            "bid_open": [99.9] * 2300,
            "ask_open": [100.1] * 2300,
            "bid_close": [99.9] * 2300,
            "ask_close": [100.1] * 2300,
        }
    )
    first_week = m5["bar_start_utc"].dt.isocalendar().week == 45
    m5.loc[first_week, ["high", "low"]] = [101.0, 99.0]
    m5.loc[2100, ["open", "high", "low", "close"]] = [98.70, 99.40, 98.60, 99.20]
    m5.loc[2100, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        98.70,
        99.20,
        98.60,
        98.80,
        99.10,
        99.30,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-11-04T00:15:00Z", periods=780, freq="15min"),
            "open": [100.0] * 780,
            "high": [101.0] * 780,
            "low": [99.0] * 780,
            "close": [100.0] * 780,
            "atr14": [1.0] * 780,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-11-04T00:00:00Z", periods=200, freq="1h"),
            "open": [100.0] * 200,
            "high": [102.0] * 200,
            "low": [98.0] * 200,
            "close": [100.0] * 200,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _session_vwap_reclaim_context() -> dict:
    m5_times = pd.date_range("2024-12-02T06:05:00Z", periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 180,
            "high": [100.2] * 180,
            "low": [99.8] * 180,
            "close": [100.0] * 180,
            "atr14": [0.5] * 180,
            "mid_open": [100.0] * 180,
            "mid_close": [100.0] * 180,
            "bid_open": [99.9] * 180,
            "ask_open": [100.1] * 180,
            "bid_close": [99.9] * 180,
            "ask_close": [100.1] * 180,
        }
    )
    m5.loc[50, ["open", "high", "low", "close"]] = [99.25, 100.20, 99.20, 100.12]
    m5.loc[50, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        99.25,
        100.12,
        99.15,
        99.35,
        100.02,
        100.22,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-12-02T06:15:00Z", periods=70, freq="15min"),
            "open": [100.0] * 70,
            "high": [101.0] * 70,
            "low": [99.0] * 70,
            "close": [100.0] * 70,
            "atr14": [1.0] * 70,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-12-02T00:00:00Z", periods=30, freq="1h"),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [100.0] * 30,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}
