from __future__ import annotations

import pandas as pd

from regime import apply_router_hysteresis, attach_regime, previous_percentile


def test_prior_percentile_does_not_use_future_value() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 4.0, 100.0])
    first = previous_percentile(values, 3)
    mutated = values.copy(); mutated.iloc[4] = 9999.0
    second = previous_percentile(mutated, 3)
    assert first.iloc[3] == second.iloc[3]


def test_router_requires_two_closes_but_unsafe_is_immediate() -> None:
    raw = pd.Series(["TRANSITION_UNKNOWN", "TREND_UP", "TREND_UP", "COMPRESSION", "UNSAFE_SHOCK"])
    owner, _ = apply_router_hysteresis(raw, 2, 2)
    assert owner.iloc[1] == "TRANSITION_UNKNOWN"
    assert owner.iloc[2] == "TREND_UP"
    assert owner.iloc[3] == "TREND_UP"
    assert owner.iloc[4] == "UNSAFE_SHOCK"


def test_lower_timeframe_never_receives_unclosed_h4_label() -> None:
    h4 = pd.DataFrame({
        "timestamp_utc": pd.to_datetime(["2020-01-01 04:00Z", "2020-01-01 08:00Z"]),
        "regime": ["TREND_UP", "COMPRESSION"], "raw_regime": ["TREND_UP", "COMPRESSION"],
        "regime_episode_id": [1, 2], "atr14_h4": [1.0, 1.0], "adx14_h4": [30.0, 20.0],
        "er24_h4": [0.5, 0.2], "atr_percentile_h4": [50.0, 20.0], "ema_slope_atr_h4": [0.3, 0.0],
    })
    bars = pd.DataFrame({
        "bar_start_utc": pd.to_datetime(["2020-01-01 07:45Z", "2020-01-01 08:00Z"]),
        "timestamp_utc": pd.to_datetime(["2020-01-01 08:00Z", "2020-01-01 08:15Z"]),
    })
    attached = attach_regime(bars, h4)
    assert attached.iloc[0]["regime_at_open"] == "TREND_UP"
    assert attached.iloc[0]["regime"] == "COMPRESSION"
    assert attached.iloc[1]["regime_at_open"] == "COMPRESSION"
