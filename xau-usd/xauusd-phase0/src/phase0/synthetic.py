from __future__ import annotations

import pandas as pd


def synthetic_context_for_expert(expert: str) -> dict:
    if expert == "compression_retest_continuation_v0":
        return _compression_retest_continuation_context()
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
    if expert == "ny_failed_london_reversal_v0":
        return _ny_failed_london_reversal_context()
    if expert == "post_spike_short_v0":
        return _post_spike_short_context()
    if expert == "squeeze_breakout_long_v0":
        return _squeeze_breakout_long_context()
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
