from __future__ import annotations

import pandas as pd


def synthetic_context_for_expert(expert: str) -> dict:
    if expert == "trend_pullback":
        return _trend_context()
    if expert == "breakout_retest":
        return _breakout_context()
    if expert == "range_mr":
        return _range_context()
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
