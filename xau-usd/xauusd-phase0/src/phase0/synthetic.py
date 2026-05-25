from __future__ import annotations

import pandas as pd


def synthetic_context_for_expert(expert: str) -> dict:
    if expert == "asia_range_london_breakout_v0":
        return _asia_range_london_breakout_context()
    if expert == "asia_range_london_failed_break_reversal_v0":
        return _asia_range_london_failed_break_reversal_context()
    if expert == "compression_retest_continuation_v0":
        return _compression_retest_continuation_context()
    if expert == "cot_gold_positioning_reversal_v0":
        return _cot_gold_positioning_reversal_context()
    if expert == "d1_compression_h4_expansion_v0":
        return _d1_compression_h4_expansion_context()
    if expert == "d1_inside_day_breakout_v0":
        return _d1_inside_day_breakout_context()
    if expert == "d1_momentum_h4_pullback_v0":
        return _d1_momentum_h4_pullback_context()
    if expert == "d1_multi_day_exhaustion_reversion_v0":
        return _d1_multi_day_exhaustion_reversion_context()
    if expert == "d1_outside_day_followthrough_v0":
        return _d1_outside_day_followthrough_context()
    if expert == "d1_volatility_expansion_reversal_v0":
        return _d1_volatility_expansion_reversal_context()
    if expert == "d1_w1_momentum_h4_pullback_v0":
        return _d1_momentum_h4_pullback_context()
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
    if expert == "gold_fx_proxy_divergence_v0":
        return _gold_fx_proxy_divergence_context()
    if expert == "h1_calendar_drift_state_v0":
        return _h1_calendar_drift_state_context()
    if expert == "h1_m5_path_skew_reversal_v0":
        return _h1_m5_path_skew_reversal_context()
    if expert == "h1_return_autocorrelation_state_v0":
        return _h1_return_autocorrelation_state_context()
    if expert == "h1_smooth_trend_exhaustion_reversal_v0":
        return _h1_smooth_trend_exhaustion_reversal_context()
    if expert == "h1_tick_volume_climax_reversal_v0":
        return _h1_tick_volume_climax_reversal_context()
    if expert == "h1_volatility_squeeze_breakout_v0":
        return _h1_volatility_squeeze_breakout_context()
    if expert == "h1_walk_forward_linear_state_v0":
        return _h1_walk_forward_linear_state_context()
    if expert == "xau_xag_relative_value_v0":
        return _xau_xag_relative_value_context()
    if expert == "h4_d1_momentum_expansion_continuation_v0":
        return _h4_d1_momentum_expansion_continuation_context()
    if expert == "h4_gvz_volatility_panic_reversal_v0":
        return _h4_gvz_volatility_panic_reversal_context()
    if expert == "h4_inside_bar_d1_momentum_breakout_v0":
        return _h4_inside_bar_d1_momentum_breakout_context()
    if expert == "h4_real_yield_proxy_momentum_v0":
        return _h4_real_yield_proxy_momentum_context()
    if expert == "h4_vix_risk_off_reversal_v0":
        return _h4_vix_risk_off_reversal_context()
    if expert == "h4_walk_forward_knn_momentum_state_v0":
        return _h4_walk_forward_knn_momentum_state_context()
    if expert == "xag_lead_xau_followthrough_v0":
        return _xag_lead_xau_followthrough_context()
    if expert == "xau_xag_fx_composite_reversion_v0":
        return _xau_xag_fx_composite_reversion_context()
    if expert == "london_fix_continuation_v0":
        return _london_fix_continuation_context()
    if expert == "liquidity_sweep_continuation_v0":
        return _liquidity_sweep_continuation_context()
    if expert == "liquidity_sweep_reversal_v0":
        return _liquidity_sweep_reversal_context()
    if expert == "m15_inside_bar_breakout_v0":
        return _m15_inside_bar_breakout_context()
    if expert == "m15_two_bar_impulse_continuation_v0":
        return _m15_two_bar_impulse_continuation_context()
    if expert == "m15_two_bar_exhaustion_reversal_v0":
        return _m15_two_bar_exhaustion_reversal_context()
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
    if expert == "session_extreme_retest_v0":
        return _session_extreme_retest_context()
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
    if expert == "w1_d1_momentum_continuation_v0":
        return _w1_d1_momentum_continuation_context()
    if expert == "weekly_level_reclaim_v0":
        return _weekly_level_reclaim_context()
    if expert == "weekly_open_reversion_v0":
        return _weekly_open_reversion_context()
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


def _liquidity_sweep_continuation_context() -> dict:
    context = _liquidity_sweep_reversal_context()
    m5 = context["M5"].copy()
    m5.loc[390, ["open", "high", "low", "close"]] = [100.95, 101.70, 100.85, 101.45]
    m5.loc[390, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.95,
        101.45,
        100.85,
        101.05,
        101.35,
        101.55,
    ]
    context["M5"] = m5
    return context


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


def _d1_momentum_h4_pullback_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=90, freq="1D")
    d1_closes = [100.0 + 0.55 * index for index in range(90)]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.2 for close in d1_closes],
            "high": [close + 1.0 for close in d1_closes],
            "low": [close - 1.0 for close in d1_closes],
            "close": d1_closes,
        }
    )

    h4_times = pd.date_range("2024-03-01T00:00:00Z", periods=180, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [130.0] * 180,
            "high": [130.35] * 180,
            "low": [129.65] * 180,
            "close": [130.0] * 180,
        }
    )
    h4.loc[120, ["open", "high", "low", "close"]] = [129.85, 131.35, 129.45, 130.85]

    m5_times = pd.date_range("2024-03-01T00:05:00Z", periods=9000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [130.0] * 9000,
            "high": [130.5] * 9000,
            "low": [129.5] * 9000,
            "close": [130.0] * 9000,
            "mid_open": [130.0] * 9000,
            "mid_close": [130.0] * 9000,
            "bid_open": [129.9] * 9000,
            "ask_open": [130.1] * 9000,
            "bid_close": [129.9] * 9000,
            "ask_close": [130.1] * 9000,
        }
    )

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:15:00Z", periods=3000, freq="15min"),
            "open": [130.0] * 3000,
            "high": [130.5] * 3000,
            "low": [129.5] * 3000,
            "close": [130.0] * 3000,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:00:00Z", periods=760, freq="1h"),
            "open": [130.0] * 760,
            "high": [130.5] * 760,
            "low": [129.5] * 760,
            "close": [130.0] * 760,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_compression_h4_expansion_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=82, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * 82,
            "high": [102.0] * 82,
            "low": [98.0] * 82,
            "close": [100.0] * 82,
        }
    )
    for idx in range(60, 82):
        d1.loc[idx, ["open", "high", "low", "close"]] = [100.0, 100.4, 99.6, 100.0]

    h4_times = pd.date_range("2024-03-05T00:00:00Z", periods=110, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 110,
            "high": [100.5] * 110,
            "low": [99.5] * 110,
            "close": [100.0] * 110,
        }
    )
    h4.loc[33, ["open", "high", "low", "close"]] = [100.0, 102.0, 99.6, 101.8]

    m5_times = pd.date_range("2024-03-05T00:05:00Z", periods=8000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [101.8] * 8000,
            "high": [102.4] * 8000,
            "low": [101.2] * 8000,
            "close": [101.8] * 8000,
            "mid_open": [101.8] * 8000,
            "mid_close": [101.8] * 8000,
            "bid_open": [101.7] * 8000,
            "ask_open": [101.9] * 8000,
            "bid_close": [101.7] * 8000,
            "ask_close": [101.9] * 8000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-05T00:15:00Z", periods=2700, freq="15min"),
            "open": [101.8] * 2700,
            "high": [102.4] * 2700,
            "low": [101.2] * 2700,
            "close": [101.8] * 2700,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-05T00:00:00Z", periods=680, freq="1h"),
            "open": [101.8] * 680,
            "high": [102.4] * 680,
            "low": [101.2] * 680,
            "close": [101.8] * 680,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_multi_day_exhaustion_reversion_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=80, freq="1D")
    d1_closes = [100.0] * 80
    for idx in range(55, 80):
        d1_closes[idx] = d1_closes[idx - 1] + 1.2
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.3 for close in d1_closes],
            "high": [close + 0.8 for close in d1_closes],
            "low": [close - 0.8 for close in d1_closes],
            "close": d1_closes,
        }
    )

    h4_times = pd.date_range("2024-03-10T00:00:00Z", periods=120, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [128.0] * 120,
            "high": [128.7] * 120,
            "low": [127.3] * 120,
            "close": [128.0] * 120,
        }
    )
    h4.loc[31, ["open", "high", "low", "close"]] = [130.4, 131.2, 128.6, 129.0]

    m5_times = pd.date_range("2024-03-10T00:05:00Z", periods=8000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [129.0] * 8000,
            "high": [129.6] * 8000,
            "low": [128.4] * 8000,
            "close": [129.0] * 8000,
            "mid_open": [129.0] * 8000,
            "mid_close": [129.0] * 8000,
            "bid_open": [128.9] * 8000,
            "ask_open": [129.1] * 8000,
            "bid_close": [128.9] * 8000,
            "ask_close": [129.1] * 8000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-10T00:15:00Z", periods=2700, freq="15min"),
            "open": [129.0] * 2700,
            "high": [129.6] * 2700,
            "low": [128.4] * 2700,
            "close": [129.0] * 2700,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-10T00:00:00Z", periods=680, freq="1h"),
            "open": [129.0] * 680,
            "high": [129.6] * 680,
            "low": [128.4] * 680,
            "close": [129.0] * 680,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _h4_d1_momentum_expansion_continuation_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=90, freq="1D")
    d1_closes = [100.0 + 0.45 * index for index in range(90)]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.2 for close in d1_closes],
            "high": [close + 0.9 for close in d1_closes],
            "low": [close - 0.9 for close in d1_closes],
            "close": d1_closes,
        }
    )

    h4_times = pd.date_range("2024-03-01T00:00:00Z", periods=180, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [130.0] * 180,
            "high": [130.45] * 180,
            "low": [129.55] * 180,
            "close": [130.0] * 180,
        }
    )
    h4.loc[120, ["open", "high", "low", "close"]] = [130.0, 131.8, 129.8, 131.55]

    m5_times = pd.date_range("2024-03-01T00:05:00Z", periods=9000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [131.55] * 9000,
            "high": [132.2] * 9000,
            "low": [130.9] * 9000,
            "close": [131.55] * 9000,
            "mid_open": [131.55] * 9000,
            "mid_close": [131.55] * 9000,
            "bid_open": [131.45] * 9000,
            "ask_open": [131.65] * 9000,
            "bid_close": [131.45] * 9000,
            "ask_close": [131.65] * 9000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:15:00Z", periods=3000, freq="15min"),
            "open": [131.55] * 3000,
            "high": [132.2] * 3000,
            "low": [130.9] * 3000,
            "close": [131.55] * 3000,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:00:00Z", periods=760, freq="1h"),
            "open": [131.55] * 760,
            "high": [132.2] * 760,
            "low": [130.9] * 760,
            "close": [131.55] * 760,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _h4_inside_bar_d1_momentum_breakout_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=90, freq="1D")
    d1_closes = [100.0 + 0.35 * index for index in range(90)]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.2 for close in d1_closes],
            "high": [close + 0.9 for close in d1_closes],
            "low": [close - 0.9 for close in d1_closes],
            "close": d1_closes,
        }
    )

    h4_times = pd.date_range("2024-03-01T00:00:00Z", periods=180, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [130.0] * 180,
            "high": [130.7] * 180,
            "low": [129.3] * 180,
            "close": [130.0] * 180,
        }
    )
    h4.loc[118, ["open", "high", "low", "close"]] = [130.0, 131.2, 128.8, 130.4]
    h4.loc[119, ["open", "high", "low", "close"]] = [130.3, 130.8, 129.7, 130.2]
    h4.loc[120, ["open", "high", "low", "close"]] = [130.4, 132.0, 130.1, 131.8]

    m5_times = pd.date_range("2024-03-01T00:05:00Z", periods=9000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [131.8] * 9000,
            "high": [132.4] * 9000,
            "low": [131.2] * 9000,
            "close": [131.8] * 9000,
            "mid_open": [131.8] * 9000,
            "mid_close": [131.8] * 9000,
            "bid_open": [131.7] * 9000,
            "ask_open": [131.9] * 9000,
            "bid_close": [131.7] * 9000,
            "ask_close": [131.9] * 9000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:15:00Z", periods=3000, freq="15min"),
            "open": [131.8] * 3000,
            "high": [132.4] * 3000,
            "low": [131.2] * 3000,
            "close": [131.8] * 3000,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:00:00Z", periods=760, freq="1h"),
            "open": [131.8] * 760,
            "high": [132.4] * 760,
            "low": [131.2] * 760,
            "close": [131.8] * 760,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _h4_real_yield_proxy_momentum_context() -> dict:
    macro_dates = pd.bdate_range("2022-01-03", periods=360, tz="UTC")
    real_yield: list[float] = []
    dollar_index: list[float] = []
    for index in range(360):
        if index < 240:
            real_yield.append(2.50 + (0.01 if index % 2 else -0.01))
            dollar_index.append(110.0 + (0.05 if index % 2 else -0.04))
        else:
            real_yield.append(2.50 - 0.015 * (index - 239))
            dollar_index.append(110.0 - 0.075 * (index - 239))
    macro = pd.DataFrame(
        {
            "timestamp_utc": macro_dates,
            "real_yield_10y": real_yield,
            "dollar_index_broad": dollar_index,
        }
    )

    h4_periods = 240
    h4_times = pd.date_range(macro_dates[270] + pd.Timedelta(hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.24 if index % 5 else -0.03
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=60, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 60,
            "high": [2005.0] * 60,
            "low": [1995.0] * 60,
            "close": [2001.0] * 60,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h4_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "macro_proxy": macro,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_gvz_volatility_panic_reversal_context() -> dict:
    gvz_dates = pd.bdate_range("2022-01-03", periods=340, tz="UTC")
    gvz_close: list[float] = []
    for index in range(340):
        if index < 260:
            gvz_close.append(18.0 + 0.03 * (index % 8))
        else:
            gvz_close.append(18.0 + 0.24 * (index - 259))
    gvz = pd.DataFrame({"timestamp_utc": gvz_dates, "gvz_close": gvz_close})

    h4_periods = 180
    h4_times = pd.date_range(gvz_dates[300] + pd.Timedelta(hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        if index < 120:
            current -= 1.20
        elif index == 120:
            current += 3.20
        else:
            current += 0.12 if index % 4 else -0.04
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2005.0] * 40,
            "low": [1995.0] * 40,
            "close": [1998.0] * 40,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 288
    m5_times = pd.date_range(h4_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "gvz_volatility": gvz,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_vix_risk_off_reversal_context() -> dict:
    vix_dates = pd.bdate_range("2022-01-03", periods=340, tz="UTC")
    vix_close: list[float] = []
    for index in range(340):
        if index < 260:
            vix_close.append(18.0 + 0.04 * (index % 7))
        else:
            vix_close.append(18.0 + 0.25 * (index - 259))
    vix = pd.DataFrame({"timestamp_utc": vix_dates, "vix_close": vix_close})

    h4_periods = 180
    h4_times = pd.date_range(vix_dates[300] + pd.Timedelta(hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        if index < 120:
            current -= 1.15
        elif index == 120:
            current += 3.10
        else:
            current += 0.10 if index % 4 else -0.04
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")
    h4["high"] = h4[["open", "close"]].max(axis=1) + 5.0
    h4["low"] = h4[["open", "close"]].min(axis=1) - 20.0

    d1_times = pd.date_range(h4_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2005.0] * 40,
            "low": [1995.0] * 40,
            "close": [1998.0] * 40,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 288
    m5_times = pd.date_range(h4_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "vix_risk": vix,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _cot_gold_positioning_reversal_context() -> dict:
    cot_dates = pd.date_range("2020-01-07", periods=210, freq="7D", tz="UTC")
    open_interest = [400000.0] * 210
    mm_net: list[float] = []
    producer_net: list[float] = []
    for index in range(210):
        if index < 160:
            mm_net.append(0.10 + 0.001 * (index % 20))
            producer_net.append(-0.10 - 0.001 * (index % 20))
        else:
            mm_net.append(-0.24 + 0.004 * (index - 159))
            producer_net.append(0.24 - 0.001 * (index - 159))
    cot = pd.DataFrame(
        {
            "report_date": cot_dates,
            "market": ["GOLD - COMMODITY EXCHANGE INC."] * 210,
            "cftc_contract_market_code": ["088691"] * 210,
            "open_interest_all": open_interest,
            "producer_long_all": [160000.0 + max(value, 0) * 400000.0 for value in producer_net],
            "producer_short_all": [160000.0 + max(-value, 0) * 400000.0 for value in producer_net],
            "managed_money_long_all": [150000.0 + max(value, 0) * 400000.0 for value in mm_net],
            "managed_money_short_all": [150000.0 + max(-value, 0) * 400000.0 for value in mm_net],
        }
    )

    h4_periods = 260
    h4_times = pd.date_range(cot_dates[170] + pd.Timedelta(days=6, hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 1900.0
    for index in range(h4_periods):
        current += 0.22 if index % 5 else -0.02
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=80, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [1900.0] * 80,
            "high": [1905.0] * 80,
            "low": [1895.0] * 80,
            "close": [1901.0] * 80,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h4_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "cot_gold": cot,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_walk_forward_knn_momentum_state_context() -> dict:
    h4_periods = 980
    h4_times = pd.date_range("2024-01-01T04:00:00Z", periods=h4_periods, freq="4h")
    h4_closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.28 if index % 4 != 0 else -0.04
        h4_closes.append(current)
    h4_opens = [h4_closes[0] - 0.12, *h4_closes[:-1]]
    h4_highs = [max(open_price, close) + 0.18 for open_price, close in zip(h4_opens, h4_closes)]
    h4_lows = [min(open_price, close) - 0.18 for open_price, close in zip(h4_opens, h4_closes)]
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": h4_opens,
            "high": h4_highs,
            "low": h4_lows,
            "close": h4_closes,
        }
    )

    d1_periods = 220
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=d1_periods, freq="1D")
    d1_closes = [2000.0 + 1.0 * index for index in range(d1_periods)]
    d1_opens = [close - 0.35 for close in d1_closes]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": d1_opens,
            "high": [close + 1.0 for close in d1_closes],
            "low": [open_price - 0.8 for open_price in d1_opens],
            "close": d1_closes,
        }
    )

    last_close = h4_closes[-1]
    m5_times = pd.date_range(h4_times[-1] + pd.Timedelta(minutes=5), periods=240, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 240,
            "high": [last_close + 0.8] * 240,
            "low": [last_close - 0.8] * 240,
            "close": [last_close + 0.1] * 240,
            "mid_open": [last_close] * 240,
            "mid_close": [last_close + 0.1] * 240,
            "bid_open": [last_close - 0.1] * 240,
            "ask_open": [last_close + 0.1] * 240,
            "bid_close": [last_close] * 240,
            "ask_close": [last_close + 0.2] * 240,
        }
    )
    return {"M5": m5, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _w1_d1_momentum_continuation_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=90, freq="1D")
    d1_closes = [100.0 + 0.35 * index for index in range(90)]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.25 for close in d1_closes],
            "high": [close + 0.9 for close in d1_closes],
            "low": [close - 0.9 for close in d1_closes],
            "close": d1_closes,
        }
    )
    d1.loc[70, ["open", "high", "low", "close"]] = [124.2, 126.2, 124.0, 125.9]

    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=26000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [125.9] * 26000,
            "high": [126.5] * 26000,
            "low": [125.3] * 26000,
            "close": [125.9] * 26000,
            "mid_open": [125.9] * 26000,
            "mid_close": [125.9] * 26000,
            "bid_open": [125.8] * 26000,
            "ask_open": [126.0] * 26000,
            "bid_close": [125.8] * 26000,
            "ask_close": [126.0] * 26000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:15:00Z", periods=8700, freq="15min"),
            "open": [125.9] * 8700,
            "high": [126.5] * 8700,
            "low": [125.3] * 8700,
            "close": [125.9] * 8700,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:00:00Z", periods=2200, freq="1h"),
            "open": [125.9] * 2200,
            "high": [126.5] * 2200,
            "low": [125.3] * 2200,
            "close": [125.9] * 2200,
        }
    )
    h4 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:00:00Z", periods=550, freq="4h"),
            "open": [125.9] * 550,
            "high": [126.5] * 550,
            "low": [125.3] * 550,
            "close": [125.9] * 550,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_volatility_expansion_reversal_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=70, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * 70,
            "high": [101.0] * 70,
            "low": [99.0] * 70,
            "close": [100.0] * 70,
        }
    )
    for idx in range(50, 60):
        d1.loc[idx, ["open", "high", "low", "close"]] = [100.0 + idx * 0.1, 102.0 + idx * 0.1, 99.0 + idx * 0.1, 101.0 + idx * 0.1]
    d1.loc[60, ["open", "high", "low", "close"]] = [106.0, 111.0, 105.5, 110.5]

    h4_times = pd.date_range("2024-02-25T00:00:00Z", periods=140, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [108.0] * 140,
            "high": [108.7] * 140,
            "low": [107.3] * 140,
            "close": [108.0] * 140,
        }
    )
    h4.loc[31, ["open", "high", "low", "close"]] = [110.4, 111.2, 108.6, 109.0]

    m5_times = pd.date_range("2024-02-25T00:05:00Z", periods=7000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [109.0] * 7000,
            "high": [109.6] * 7000,
            "low": [108.4] * 7000,
            "close": [109.0] * 7000,
            "mid_open": [109.0] * 7000,
            "mid_close": [109.0] * 7000,
            "bid_open": [108.9] * 7000,
            "ask_open": [109.1] * 7000,
            "bid_close": [108.9] * 7000,
            "ask_close": [109.1] * 7000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-02-25T00:15:00Z", periods=2400, freq="15min"),
            "open": [109.0] * 2400,
            "high": [109.6] * 2400,
            "low": [108.4] * 2400,
            "close": [109.0] * 2400,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-02-25T00:00:00Z", periods=600, freq="1h"),
            "open": [109.0] * 600,
            "high": [109.6] * 600,
            "low": [108.4] * 600,
            "close": [109.0] * 600,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


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


def _m15_two_bar_exhaustion_reversal_context() -> dict:
    periods = 80
    m15_times = pd.date_range("2024-05-02T00:15:00Z", periods=periods, freq="15min")
    closes = [2000.0 + (0.05 if index % 2 == 0 else -0.05) for index in range(periods)]
    opens = [2000.0] * periods
    highs = [2000.45] * periods
    lows = [1999.55] * periods

    opens[-3] = 2000.0
    closes[-3] = 2000.0
    highs[-3] = 2000.45
    lows[-3] = 1999.55
    opens[-2] = 2000.0
    closes[-2] = 1999.05
    highs[-2] = 2000.20
    lows[-2] = 1998.85
    opens[-1] = 1999.05
    closes[-1] = 1997.80
    highs[-1] = 1999.20
    lows[-1] = 1997.60

    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "bar_start_utc": m15_times - pd.Timedelta(minutes=15),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "mid_open": opens,
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": closes,
            "bid_open": [value - 0.01 for value in opens],
            "ask_open": [value + 0.01 for value in opens],
            "bid_close": [value - 0.01 for value in closes],
            "ask_close": [value + 0.01 for value in closes],
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(m15_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.8] * 180,
            "low": [last_close - 0.8] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "M15": m15, "symbol": "XAUUSD", "point_size": 0.01}


def _m15_two_bar_impulse_continuation_context() -> dict:
    periods = 80
    m15_times = pd.date_range("2024-05-03T00:15:00Z", periods=periods, freq="15min")
    closes = [2000.0 + (0.05 if index % 2 == 0 else -0.05) for index in range(periods)]
    opens = [2000.0] * periods
    highs = [2000.45] * periods
    lows = [1999.55] * periods

    opens[-3] = 2000.0
    closes[-3] = 2000.0
    highs[-3] = 2000.45
    lows[-3] = 1999.55
    opens[-2] = 2000.0
    closes[-2] = 2000.95
    highs[-2] = 2001.15
    lows[-2] = 1999.80
    opens[-1] = 2000.95
    closes[-1] = 2002.20
    highs[-1] = 2002.40
    lows[-1] = 2000.80

    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "bar_start_utc": m15_times - pd.Timedelta(minutes=15),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "mid_open": opens,
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": closes,
            "bid_open": [value - 0.01 for value in opens],
            "ask_open": [value + 0.01 for value in opens],
            "bid_close": [value - 0.01 for value in closes],
            "ask_close": [value + 0.01 for value in closes],
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(m15_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.8] * 180,
            "low": [last_close - 0.8] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "M15": m15, "symbol": "XAUUSD", "point_size": 0.01}


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


def _session_extreme_retest_context() -> dict:
    m5 = _base_m5("2024-04-01T00:00:00Z", 120)
    m5["timestamp_utc"] = pd.to_datetime(m5["timestamp_utc"], utc=True)
    m5["bar_start_utc"] = pd.to_datetime(m5["bar_start_utc"], utc=True)
    m5["atr14"] = [1.0] * len(m5)
    asia_mask = m5["bar_start_utc"].dt.hour < 6
    m5.loc[asia_mask, ["high", "low", "close"]] = [100.0, 98.0, 99.0]
    m5.loc[86, ["open", "high", "low", "close"]] = [99.8, 101.0, 99.7, 100.5]
    m5.loc[88, ["open", "high", "low", "close"]] = [100.3, 100.4, 99.95, 100.1]
    m5.loc[89, ["open", "high", "low", "close"]] = [100.1, 100.6, 100.0, 100.5]
    for column in ("mid_open", "bid_open", "ask_open"):
        m5[column] = m5["open"]
    for column in ("mid_close", "bid_close", "ask_close"):
        m5[column] = m5["close"]
    m5["bid_open"] = m5["open"] - 0.1
    m5["ask_open"] = m5["open"] + 0.1
    m5["bid_close"] = m5["close"] - 0.1
    m5["ask_close"] = m5["close"] + 0.1
    return {"M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


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


def _weekly_open_reversion_context() -> dict:
    m15_times = pd.date_range("2024-12-02T00:15:00Z", periods=180, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "bar_start_utc": m15_times - pd.Timedelta(minutes=15),
            "open": [100.0] * 180,
            "high": [100.4] * 180,
            "low": [99.6] * 180,
            "close": [100.0] * 180,
            "atr14": [1.0] * 180,
        }
    )
    m15.loc[128, ["open", "high", "low", "close"]] = [96.0, 97.0, 95.0, 96.8]

    m5_times = pd.date_range("2024-12-02T00:05:00Z", periods=540, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 540,
            "high": [100.2] * 540,
            "low": [99.8] * 540,
            "close": [100.0] * 540,
            "mid_open": [100.0] * 540,
            "mid_close": [100.0] * 540,
            "bid_open": [99.9] * 540,
            "ask_open": [100.1] * 540,
            "bid_close": [99.9] * 540,
            "ask_close": [100.1] * 540,
        }
    )
    return {"M5": m5, "M15": m15, "symbol": "XAUUSD", "point_size": 0.01}


def _gold_fx_proxy_divergence_context() -> dict:
    periods = 380
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    base_returns = [0.0001 if index % 2 == 0 else -0.00008 for index in range(periods)]
    usd_strength_returns = [0.0] * periods
    for index in range(periods - 30, periods):
        usd_strength_returns[index] = 0.0008

    eurusd_returns = [base_returns[index] - usd_strength_returns[index] for index in range(periods)]
    usdjpy_returns = [base_returns[index] + usd_strength_returns[index] for index in range(periods)]
    xau_returns = [0.00005 if index % 3 else -0.00004 for index in range(periods)]
    for index in range(periods - 30, periods):
        xau_returns[index] = 0.002

    xau_close = _price_path(2000.0, xau_returns)
    eurusd_close = _price_path(1.1000, eurusd_returns)
    usdjpy_close = _price_path(145.0, usdjpy_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    eurusd = _ohlc_from_closes(h1_times, eurusd_close, "capital_com", "EURUSD", "H1")
    usdjpy = _ohlc_from_closes(h1_times, usdjpy_close, "capital_com", "USDJPY", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "intermarket_proxy": {"EURUSD": eurusd, "USDJPY": usdjpy},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_return_autocorrelation_state_context() -> dict:
    periods = 240
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    returns = [0.00008 if index % 2 == 0 else -0.00004 for index in range(periods)]
    for index in range(120, periods):
        returns[index] = 0.0012 if index % 3 else 0.0007

    closes = _price_path(2000.0, returns)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(120, periods):
        h1.loc[h1.index[index], "high"] = max(
            float(h1.loc[h1.index[index], "high"]),
            float(h1.loc[h1.index[index], "close"]) + 0.35,
        )

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.9] * 180,
            "low": [last_close - 0.9] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_m5_path_skew_reversal_context() -> dict:
    periods = 80
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0 + (0.15 if index % 2 == 0 else -0.10) for index in range(periods)]
    closes[-2] = 2002.0
    closes[-1] = 1999.75
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(periods - 1):
        h1.loc[h1.index[index], "high"] = max(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) + 0.50
        h1.loc[h1.index[index], "low"] = min(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) - 0.50
    h1.loc[h1.index[-1], "open"] = 2002.0
    h1.loc[h1.index[-1], "high"] = 2002.3
    h1.loc[h1.index[-1], "low"] = 1998.6
    h1.loc[h1.index[-1], "close"] = 1999.75

    m5_rows: list[dict[str, object]] = []
    for h1_index, h1_end in enumerate(h1_times):
        h1_start = h1_end - pd.Timedelta(hours=1)
        if h1_index == periods - 1:
            opens = [
                2002.0,
                2001.3,
                2000.6,
                1999.9,
                1999.3,
                1998.9,
                1998.8,
                1998.9,
                1999.0,
                1999.1,
                1999.3,
                1999.5,
            ]
            closes_m5 = [
                2001.3,
                2000.6,
                1999.9,
                1999.3,
                1998.9,
                1998.8,
                1998.9,
                1999.0,
                1999.1,
                1999.3,
                1999.5,
                1999.75,
            ]
        else:
            start_price = float(h1.iloc[h1_index]["open"])
            end_price = float(h1.iloc[h1_index]["close"])
            step = (end_price - start_price) / 12.0
            opens = [start_price + step * offset for offset in range(12)]
            closes_m5 = [start_price + step * (offset + 1) for offset in range(12)]
        for offset, (open_price, close_price) in enumerate(zip(opens, closes_m5), start=1):
            timestamp = h1_start + pd.Timedelta(minutes=5 * offset)
            high = max(open_price, close_price) + 0.08
            low = min(open_price, close_price) - 0.08
            m5_rows.append(
                {
                    "timestamp_utc": timestamp,
                    "bar_start_utc": timestamp - pd.Timedelta(minutes=5),
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close_price,
                    "mid_open": open_price,
                    "mid_close": close_price,
                    "bid_open": open_price - 0.1,
                    "ask_open": open_price + 0.1,
                    "bid_close": close_price - 0.1,
                    "ask_close": close_price + 0.1,
                }
            )
    m5 = pd.DataFrame(m5_rows)
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_smooth_trend_exhaustion_reversal_context() -> dict:
    periods = 140
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0] * periods
    for index in range(1, 110):
        closes[index] = closes[index - 1] + (0.05 if index % 2 == 0 else -0.04)
    for index in range(110, periods - 1):
        closes[index] = closes[index - 1] - 2.0
    closes[-1] = closes[-2] + 1.2

    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    h1.loc[h1.index[-1], "low"] = min(float(h1.loc[h1.index[-1], "low"]), closes[-2] - 0.3)
    h1.loc[h1.index[-1], "high"] = max(float(h1.loc[h1.index[-1], "high"]), closes[-1] + 0.1)

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.8] * 180,
            "low": [last_close - 0.8] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_tick_volume_climax_reversal_context() -> dict:
    periods = 300
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0 + (0.12 if index % 2 == 0 else -0.08) for index in range(periods)]
    closes[-2] = 2002.0
    closes[-1] = 1999.8
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(periods - 1):
        h1.loc[h1.index[index], "high"] = max(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) + 0.50
        h1.loc[h1.index[index], "low"] = min(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) - 0.50
        h1.loc[h1.index[index], "tick_count"] = 100.0 + (index % 7)
        h1.loc[h1.index[index], "volume_sum"] = 100.0 + (index % 7)
    h1.loc[h1.index[-1], "open"] = 2002.0
    h1.loc[h1.index[-1], "high"] = 2002.4
    h1.loc[h1.index[-1], "low"] = 1998.7
    h1.loc[h1.index[-1], "close"] = 1999.8
    h1.loc[h1.index[-1], "tick_count"] = 380.0
    h1.loc[h1.index[-1], "volume_sum"] = 380.0

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.9] * 180,
            "low": [last_close - 0.9] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_volatility_squeeze_breakout_context() -> dict:
    periods = 340
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0]
    for index in range(1, periods):
        if index < periods - 8:
            change = 0.06 if index % 2 == 0 else -0.05
        else:
            change = 0.45
        closes.append(closes[-1] + change)

    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(periods - 8, periods):
        h1.loc[h1.index[index], "open"] = float(h1.loc[h1.index[index - 1], "close"])
        h1.loc[h1.index[index], "close"] = float(h1.loc[h1.index[index], "open"]) + 0.45
        h1.loc[h1.index[index], "high"] = float(h1.loc[h1.index[index], "close"]) + 0.08
        h1.loc[h1.index[index], "low"] = float(h1.loc[h1.index[index], "open"]) - 0.06
        for column in ("mid_open", "bid_open", "ask_open"):
            h1.loc[h1.index[index], column] = h1.loc[h1.index[index], "open"]
        for column in ("mid_close", "bid_close", "ask_close"):
            h1.loc[h1.index[index], column] = h1.loc[h1.index[index], "close"]

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_walk_forward_linear_state_context() -> dict:
    periods = 1320
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    returns: list[float] = []
    for index in range(periods):
        if index < 240:
            returns.append(0.00005 if index % 2 == 0 else -0.00004)
            continue

        regime = (index // 72) % 4
        if regime in (0, 1):
            returns.append(0.00110 if index % 6 else 0.00045)
        else:
            returns.append(-0.00110 if index % 6 else -0.00045)

    for index in range(periods - 120, periods):
        returns[index] = 0.00115 if index % 6 else 0.00050

    closes = _price_path(2000.0, returns)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    h1["tick_count"] = [120.0 + float(index % 19) + (8.0 if index % 6 else 0.0) for index in range(periods)]
    h1["volume_sum"] = h1["tick_count"]

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_calendar_drift_state_context() -> dict:
    periods = 2400
    horizon = 6
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    target_timestamp = h1_times[-1]
    target_bucket = int(target_timestamp.dayofweek * 24 + target_timestamp.hour)
    returns = [0.00003 if index % 2 == 0 else -0.00002 for index in range(periods)]

    for index, timestamp in enumerate(h1_times[:-horizon]):
        bucket = int(timestamp.dayofweek * 24 + timestamp.hour)
        if bucket != target_bucket:
            continue
        for offset in range(1, horizon + 1):
            returns[index + offset] = 0.00100 if offset % 2 else 0.00075

    closes = _price_path(2000.0, returns)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.8] * 180,
            "low": [last_close - 0.8] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _xau_xag_relative_value_context() -> dict:
    periods = 720
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    xag_returns = [0.00008 if index % 2 == 0 else -0.00005 for index in range(periods)]
    xau_returns = [0.00007 if index % 2 == 0 else -0.00004 for index in range(periods)]
    for index in range(periods - 42, periods - 12):
        xag_returns[index] = 0.0012
        xau_returns[index] = -0.0007
    for index in range(periods - 12, periods):
        xag_returns[index] = 0.0001
        xau_returns[index] = 0.0015

    xau_close = _price_path(2000.0, xau_returns)
    xag_close = _price_path(24.0, xag_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    xag = _ohlc_from_closes(h1_times, xag_close, "capital_com", "XAGUSD", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "relative_value": {"XAGUSD": xag},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _xau_xag_fx_composite_reversion_context() -> dict:
    periods = 760
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    xag_returns = [0.00008 if index % 2 == 0 else -0.00005 for index in range(periods)]
    xau_returns = [0.00005 if index % 2 == 0 else -0.00004 for index in range(periods)]
    eurusd_returns = [0.00003 if index % 2 == 0 else -0.00002 for index in range(periods)]
    usdjpy_returns = [0.00002 if index % 2 == 0 else -0.00003 for index in range(periods)]

    for index in range(periods - 48, periods - 4):
        xag_returns[index] = 0.0011
        xau_returns[index] = -0.00055
        eurusd_returns[index] = 0.00070
        usdjpy_returns[index] = -0.00065
    for index in range(periods - 4, periods):
        xag_returns[index] = 0.00015
        xau_returns[index] = 0.00120
        eurusd_returns[index] = 0.00055
        usdjpy_returns[index] = -0.00055

    xau_close = _price_path(2000.0, xau_returns)
    xag_close = _price_path(24.0, xag_returns)
    eurusd_close = _price_path(1.10, eurusd_returns)
    usdjpy_close = _price_path(145.0, usdjpy_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    xag = _ohlc_from_closes(h1_times, xag_close, "capital_com", "XAGUSD", "H1")
    eurusd = _ohlc_from_closes(h1_times, eurusd_close, "capital_com", "EURUSD", "H1")
    usdjpy = _ohlc_from_closes(h1_times, usdjpy_close, "capital_com", "USDJPY", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "relative_value": {"XAGUSD": xag},
        "intermarket_proxy": {"EURUSD": eurusd, "USDJPY": usdjpy},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _xag_lead_xau_followthrough_context() -> dict:
    periods = 720
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    xag_returns = [0.00004 if index % 2 == 0 else -0.00003 for index in range(periods)]
    xau_returns = [0.00003 if index % 2 == 0 else -0.00002 for index in range(periods)]

    for index in range(periods - 24, periods - 4):
        xag_returns[index] = 0.00120
        xau_returns[index] = 0.00005
    for index in range(periods - 4, periods):
        xag_returns[index] = 0.00040
        xau_returns[index] = 0.00095

    xau_close = _price_path(2000.0, xau_returns)
    xag_close = _price_path(24.0, xag_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    xag = _ohlc_from_closes(h1_times, xag_close, "capital_com", "XAGUSD", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "relative_value": {"XAGUSD": xag},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _price_path(start: float, returns: list[float]) -> list[float]:
    prices: list[float] = []
    current = start
    for value in returns:
        current *= 1.0 + value
        prices.append(current)
    return prices


def _ohlc_from_closes(
    timestamps: pd.DatetimeIndex,
    closes: list[float],
    broker: str,
    symbol: str,
    timeframe: str,
) -> pd.DataFrame:
    opens = [closes[0], *closes[:-1]]
    highs = [max(open_price, close) + 0.05 for open_price, close in zip(opens, closes)]
    lows = [min(open_price, close) - 0.05 for open_price, close in zip(opens, closes)]
    starts = timestamps - pd.Timedelta(hours=1)
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "bar_start_utc": starts,
            "bar_end_utc": timestamps,
            "broker": broker,
            "symbol": symbol,
            "timeframe": timeframe,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "mid_open": opens,
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": closes,
            "bid_open": [value - 0.01 for value in opens],
            "bid_high": [value - 0.01 for value in highs],
            "bid_low": [value - 0.01 for value in lows],
            "bid_close": [value - 0.01 for value in closes],
            "ask_open": [value + 0.01 for value in opens],
            "ask_high": [value + 0.01 for value in highs],
            "ask_low": [value + 0.01 for value in lows],
            "ask_close": [value + 0.01 for value in closes],
            "spread_open_points": [2.0] * len(closes),
            "spread_close_points": [2.0] * len(closes),
            "spread_median_points": [2.0] * len(closes),
            "spread_p95_points": [3.0] * len(closes),
            "tick_count": [10] * len(closes),
            "volume_sum": [100] * len(closes),
        }
    )


def _d1_inside_day_breakout_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=30, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [100.0] * 30,
            "atr14": [5.0] * 30,
        }
    )
    d1.loc[21, ["open", "high", "low", "close"]] = [100.0, 105.0, 95.0, 100.0]
    d1.loc[22, ["open", "high", "low", "close"]] = [100.0, 103.0, 97.0, 100.0]

    h4_times = pd.date_range("2024-01-17T12:00:00Z", periods=50, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
            "atr14": [2.0] * 50,
        }
    )
    h4.loc[34, ["open", "high", "low", "close"]] = [103.5, 106.0, 103.0, 105.5]

    m5 = _base_m5("2024-01-17T12:00:00Z", 240)
    return {"M5": m5, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_outside_day_followthrough_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=30, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [100.0] * 30,
            "atr14": [4.0] * 30,
        }
    )
    d1.loc[21, ["open", "high", "low", "close"]] = [100.0, 103.0, 97.0, 100.0]
    d1.loc[22, ["open", "high", "low", "close"]] = [99.0, 106.0, 96.0, 105.0]

    h4_times = pd.date_range("2024-01-17T12:00:00Z", periods=50, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
            "atr14": [2.0] * 50,
        }
    )
    h4.loc[34, ["open", "high", "low", "close"]] = [105.0, 107.0, 104.7, 106.2]

    m5 = _base_m5("2024-01-17T12:00:00Z", 240)
    return {"M5": m5, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}
