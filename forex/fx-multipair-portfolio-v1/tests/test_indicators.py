"""Contract tests for indicators and the decision->execution mapping.

The mapping is the strategy-layer half of the no-look-ahead guarantee: a
decision bar must not be tradable until it has actually closed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.fxdata import resample_from_m5  # noqa: E402
from src.indicators import (  # noqa: E402
    atr,
    bollinger,
    decision_to_execution,
    rolling_max,
    rsi,
    shift,
)

M5 = 300_000


def test_decision_bar_is_not_tradable_before_it_closes():
    """An M30 bar stamped T must map to the M5 bar opening at T+30min."""
    execution = np.arange(0, 24) * M5  # 2 hours of M5 bars
    decision = np.array([0, 30 * 60_000])  # two M30 bars
    mapped = decision_to_execution(decision, execution, 30 * 60_000)
    assert mapped[0] == 6, "M30 bar at T=0 closes at T=30min, the 7th M5 bar"
    assert execution[mapped[0]] == 30 * 60_000
    assert mapped[1] == 12


def test_decision_mapping_skips_gaps_to_the_next_available_bar():
    """Across a weekend gap the fill is the next bar that exists, not a missing one."""
    execution = np.array([0, M5, 2 * M5, 100 * M5, 101 * M5], dtype=np.int64)
    mapped = decision_to_execution(np.array([0]), execution, 30 * 60_000)
    assert mapped[0] == 3, "no bar at T+30min, so the next existing bar is used"


def test_decision_mapping_returns_minus_one_past_series_end():
    execution = np.arange(0, 4) * M5
    mapped = decision_to_execution(np.array([10 * M5]), execution, 30 * 60_000)
    assert mapped[0] == -1


def test_shift_moves_values_forward_and_blanks_the_head():
    values = np.array([1.0, 2.0, 3.0, 4.0])
    shifted = shift(values, 1)
    assert np.isnan(shifted[0])
    assert shifted[1] == 1.0 and shifted[3] == 3.0


def test_rsi_is_100_for_a_monotonic_rise_and_bounded():
    rising = np.linspace(1.0, 2.0, 60)
    values = rsi(rising, 14)
    assert values[-1] == pytest.approx(100.0, abs=1e-6)
    assert np.all((values >= 0.0) & (values <= 100.0))


def test_rsi_is_50_for_a_flat_series_after_warmup():
    flat = np.full(60, 1.2345)
    # no gains and no losses -> rs is treated as infinite, giving 100 by MT5's
    # convention; assert the documented behaviour rather than guessing 50.
    assert rsi(flat, 14)[-1] == pytest.approx(100.0)


def test_atr_of_constant_range_bars_equals_that_range():
    high = np.full(60, 1.1010)
    low = np.full(60, 1.1000)
    close = np.full(60, 1.1005)
    assert atr(high, low, close, 14)[-1] == pytest.approx(0.0010, abs=1e-9)


def test_bollinger_uses_population_deviation():
    close = np.arange(1, 41, dtype=float)
    middle, upper, lower = bollinger(close, 20, 2.0)
    window = close[20:40]
    assert middle[39] == pytest.approx(window.mean())
    assert upper[39] == pytest.approx(window.mean() + 2.0 * window.std(ddof=0))
    assert lower[39] == pytest.approx(window.mean() - 2.0 * window.std(ddof=0))


def test_rolling_max_excludes_nothing_and_warms_up():
    values = np.array([1.0, 5.0, 3.0, 2.0])
    result = rolling_max(values, 3)
    assert np.isnan(result[1])
    assert result[2] == 5.0 and result[3] == 5.0


def test_resample_from_m5_aggregates_bid_and_ask_independently():
    bars = pd.DataFrame(
        {
            "timestamp_ms": np.arange(6, dtype=np.int64) * M5,
            "bid_open": [1.0, 1.1, 1.2, 2.0, 2.1, 2.2],
            "bid_high": [1.5, 1.6, 1.7, 2.5, 2.6, 2.7],
            "bid_low": [0.5, 0.6, 0.7, 1.5, 1.6, 1.7],
            "bid_close": [1.05, 1.15, 1.25, 2.05, 2.15, 2.25],
            "ask_open": [1.01, 1.11, 1.21, 2.01, 2.11, 2.21],
            "ask_high": [1.51, 1.61, 1.71, 2.51, 2.61, 2.71],
            "ask_low": [0.51, 0.61, 0.71, 1.51, 1.61, 1.71],
            "ask_close": [1.06, 1.16, 1.26, 2.06, 2.16, 2.26],
            "tick_count": np.full(6, 3, dtype=np.int32),
        }
    )
    m15 = resample_from_m5(bars, 15)
    assert len(m15) == 2
    assert m15.loc[0, "bid_open"] == 1.0
    assert m15.loc[0, "bid_high"] == 1.7
    assert m15.loc[0, "bid_low"] == 0.5
    assert m15.loc[0, "bid_close"] == 1.25
    assert m15.loc[0, "ask_high"] == 1.71
    assert m15.loc[0, "m5_bars"] == 3
    assert m15.loc[1, "bid_open"] == 2.0


def test_resample_rejects_non_multiples_of_five():
    bars = pd.DataFrame({"timestamp_ms": np.array([0], dtype=np.int64)})
    with pytest.raises(Exception):
        resample_from_m5(bars, 7)
