from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_symmetric_rsi_1p5r import (
    _walk_exit,
)


def _m5() -> pd.DataFrame:
    index = pd.date_range(
        "2026-01-01T00:00:00Z", periods=3, freq="5min"
    )
    return pd.DataFrame(
        {
            "bid_open": [1.1000, 1.1000, 1.1000],
            "bid_high": [1.1016, 1.1001, 1.1001],
            "bid_low": [1.0989, 1.0999, 1.0999],
            "bid_close": [1.1000, 1.1000, 1.1000],
            "ask_open": [1.1001, 1.1001, 1.1001],
            "ask_high": [1.1017, 1.1002, 1.1002],
            "ask_low": [1.0990, 1.1000, 1.1000],
            "ask_close": [1.1001, 1.1001, 1.1001],
        },
        index=index,
    )


def test_long_same_bar_ambiguity_is_stop_first() -> None:
    m5 = _m5()
    timestamp, price, reason = _walk_exit(
        m5,
        0,
        m5.index[-1],
        "LONG",
        1.0990,
        1.1015,
        0.00007,
        0.00001,
    )
    assert timestamp == m5.index[0]
    assert reason == "STOP"
    assert price < 1.0990


def test_short_exit_uses_ask_and_stop_first() -> None:
    m5 = _m5()
    timestamp, price, reason = _walk_exit(
        m5,
        0,
        m5.index[-1],
        "SHORT",
        1.1015,
        1.0990,
        0.00007,
        0.00001,
    )
    assert timestamp == m5.index[0]
    assert reason == "STOP"
    assert price > 1.1015
