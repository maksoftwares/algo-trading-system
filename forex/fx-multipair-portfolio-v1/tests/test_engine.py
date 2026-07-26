"""Contract tests for the execution engine.

These pin the properties that make backtest output trustworthy: which side of
the book each leg pays, that fills use the named bar's open and nothing later,
stop-first resolution on ambiguous bars, and quote-currency conversion.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine import CostModel, RunConfig, Signals, SymbolSpec, simulate  # noqa: E402

M5 = 300_000
EPS = 1e-9


def make_bars(bid_mid: list[float], spread_price: float, start_ms: int = 1_500_000_000_000) -> pd.DataFrame:
    """Flat bars at the given bid levels; high==low==open==close per bar."""
    n = len(bid_mid)
    bid = np.asarray(bid_mid, dtype=float)
    return pd.DataFrame(
        {
            "timestamp_ms": start_ms + np.arange(n, dtype=np.int64) * M5,
            "bid_open": bid,
            "bid_high": bid,
            "bid_low": bid,
            "bid_close": bid,
            "ask_open": bid + spread_price,
            "ask_high": bid + spread_price,
            "ask_low": bid + spread_price,
            "ask_close": bid + spread_price,
            "tick_count": np.full(n, 10, dtype=np.int32),
        }
    )


def one_signal(index: int, direction: int, stop_points: float, rr: float) -> Signals:
    return Signals(
        entry_index=np.array([index], dtype=np.int64),
        direction=np.array([direction], dtype=np.int64),
        stop_min_points=np.array([stop_points], dtype=float),
        stop_atr_points=np.array([0.0], dtype=float),
        stop_ref_price=np.array([np.nan], dtype=float),
        rr=np.array([rr], dtype=float),
        stop_cap_points=np.array([1e9], dtype=float),
    )


EURUSD = SymbolSpec.of("EURUSD")
USDJPY = SymbolSpec.of("USDJPY")
NO_COST = CostModel()


def test_long_entry_pays_the_ask():
    bars = make_bars([1.1000] * 5, spread_price=0.00010)
    trades = simulate(bars, one_signal(1, 1, 100, 1.0), EURUSD, NO_COST, RunConfig())
    assert len(trades) == 1
    # ask_open at bar 1 is 1.1001, not the 1.1000 bid.
    assert trades.loc[0, "entry_price"] == pytest.approx(1.10010, abs=EPS)


def test_short_entry_pays_the_bid():
    bars = make_bars([1.1000] * 5, spread_price=0.00010)
    trades = simulate(bars, one_signal(1, -1, 100, 1.0), EURUSD, NO_COST, RunConfig())
    assert trades.loc[0, "entry_price"] == pytest.approx(1.10000, abs=EPS)


def test_long_target_is_tested_on_the_bid_path():
    """A long entered at 1.10010 with a 100pt stop targets 1.10110 on the bid.

    Bar 2 bid reaches exactly 1.10110 -> target. If the engine wrongly used the
    ask path it would have triggered a bar earlier.
    """
    bars = make_bars([1.1000, 1.1000, 1.10110, 1.1000], spread_price=0.00010)
    trades = simulate(bars, one_signal(1, 1, 100, 1.0), EURUSD, NO_COST, RunConfig())
    assert trades.loc[0, "exit_reason"] == "target"
    assert trades.loc[0, "exit_index"] == 2
    # 100 points on 0.01 lot EURUSD = 100 * 100000 * 0.01 * 0.00001 = $1.00
    assert trades.loc[0, "net_usd"] == pytest.approx(1.0, abs=1e-6)


def test_long_target_not_triggered_by_ask_path_alone():
    """Bid peaks one point short of target; ask would have crossed it."""
    bars = make_bars([1.1000, 1.1000, 1.10109, 1.1000], spread_price=0.00010)
    trades = simulate(bars, one_signal(1, 1, 100, 1.0), EURUSD, NO_COST, RunConfig())
    assert trades.loc[0, "exit_reason"] != "target"


def test_long_stop_loses_exactly_one_r():
    bars = make_bars([1.1000, 1.1000, 1.09910, 1.1000], spread_price=0.00010)
    trades = simulate(bars, one_signal(1, 1, 100, 1.0), EURUSD, NO_COST, RunConfig())
    assert trades.loc[0, "exit_reason"] == "stop"
    assert trades.loc[0, "net_usd"] == pytest.approx(-1.0, abs=1e-6)


def test_short_stop_is_tested_on_the_ask_path():
    bars = make_bars([1.1000, 1.1000, 1.10090, 1.1000], spread_price=0.00010)
    trades = simulate(bars, one_signal(1, -1, 100, 1.0), EURUSD, NO_COST, RunConfig())
    # short entered at bid 1.10000, stop 1.10100 on the ask; bar 2 ask = 1.10100
    assert trades.loc[0, "exit_reason"] == "stop"
    assert trades.loc[0, "exit_index"] == 2


def test_fill_uses_the_named_bar_open_not_earlier_bars():
    """Prices before the entry bar must not influence the fill or the exit."""
    calm = make_bars([1.1000, 1.1000, 1.1000, 1.10110, 1.1000], spread_price=0.00010)
    spiky = calm.copy()
    for column in ("bid_open", "bid_high", "bid_low", "bid_close"):
        spiky.loc[0, column] = 1.2000
    for column in ("ask_open", "ask_high", "ask_low", "ask_close"):
        spiky.loc[0, column] = 1.20010

    signal = one_signal(2, 1, 100, 1.0)
    a = simulate(calm, signal, EURUSD, NO_COST, RunConfig())
    b = simulate(spiky, signal, EURUSD, NO_COST, RunConfig())
    assert a.loc[0, "entry_price"] == pytest.approx(b.loc[0, "entry_price"], abs=EPS)
    assert a.loc[0, "exit_index"] == b.loc[0, "exit_index"]
    assert a.loc[0, "net_usd"] == pytest.approx(b.loc[0, "net_usd"], abs=1e-9)


def test_ambiguous_bar_resolves_to_the_stop():
    """One bar spans both levels: the stop must win and be flagged."""
    bars = make_bars([1.1000] * 4, spread_price=0.00010)
    bars.loc[2, "bid_low"] = 1.09910
    bars.loc[2, "bid_high"] = 1.10110
    trades = simulate(bars, one_signal(1, 1, 100, 1.0), EURUSD, NO_COST, RunConfig())
    assert trades.loc[0, "exit_reason"] == "stop"
    assert bool(trades.loc[0, "ambiguous_bar"]) is True


def test_timeout_exit_closes_on_the_bid_for_a_long():
    bars = make_bars([1.1000] * 10, spread_price=0.00010)
    config = RunConfig(max_hold_bars=3)
    trades = simulate(bars, one_signal(1, 1, 500, 5.0), EURUSD, NO_COST, config)
    assert trades.loc[0, "exit_reason"] == "timeout"
    assert trades.loc[0, "exit_index"] == 4
    assert trades.loc[0, "exit_price"] == pytest.approx(1.1000, abs=EPS)
    # paid the spread on entry, received bid on exit -> lost exactly the spread
    assert trades.loc[0, "net_usd"] == pytest.approx(-0.10, abs=1e-6)


def test_spread_markup_widens_both_sides():
    bars = make_bars([1.1000] * 5, spread_price=0.00010)
    costs = CostModel(spread_markup_points=10.0)  # +10 points total, 5 each side
    trades = simulate(bars, one_signal(1, 1, 100, 1.0), EURUSD, costs, RunConfig())
    assert trades.loc[0, "entry_price"] == pytest.approx(1.100150, abs=EPS)


def test_commission_is_charged_both_sides():
    bars = make_bars([1.1000, 1.1000, 1.10110, 1.1000], spread_price=0.00010)
    costs = CostModel(commission_per_lot_per_side_usd=30.0)
    trades = simulate(bars, one_signal(1, 1, 100, 1.0), EURUSD, costs, RunConfig(lot=0.01))
    assert trades.loc[0, "commission_usd"] == pytest.approx(0.60, abs=1e-9)
    assert trades.loc[0, "net_usd"] == pytest.approx(1.0 - 0.60, abs=1e-6)


def test_jpy_quote_converts_to_usd():
    """100 points on USDJPY at 0.01 lot = 100 JPY, converted at the exit rate.

    Fill is the ask 150.010, so the target sits at 150.110 on the bid path.
    """
    bars = make_bars([150.000, 150.000, 150.110, 150.000], spread_price=0.010)
    trades = simulate(bars, one_signal(1, 1, 100, 1.0), USDJPY, NO_COST, RunConfig(lot=0.01))
    assert trades.loc[0, "exit_reason"] == "target"
    expected = 100 * (100_000 * 0.01 * 0.001) / float(trades.loc[0, "exit_price"])
    assert trades.loc[0, "net_usd"] == pytest.approx(expected, rel=1e-9)
    assert trades.loc[0, "net_usd"] == pytest.approx(0.666, abs=0.002)


def test_stop_reference_price_widens_the_stop():
    """stop_ref_price acts as a level; the engine converts it using the fill."""
    bars = make_bars([1.1000] * 30, spread_price=0.00010)
    signal = Signals(
        entry_index=np.array([1]),
        direction=np.array([1]),
        stop_min_points=np.array([30.0]),
        stop_atr_points=np.array([40.0]),
        stop_ref_price=np.array([1.09810]),  # 200 points below the 1.10010 fill
        rr=np.array([1.0]),
        stop_cap_points=np.array([1e9]),
    )
    trades = simulate(bars, signal, EURUSD, NO_COST, RunConfig())
    assert trades.loc[0, "stop_points"] == pytest.approx(200.0, abs=1e-6)


def test_stop_cap_truncates():
    bars = make_bars([1.1000] * 30, spread_price=0.00010)
    signal = Signals(
        entry_index=np.array([1]),
        direction=np.array([1]),
        stop_min_points=np.array([30.0]),
        stop_atr_points=np.array([900.0]),
        stop_ref_price=np.array([np.nan]),
        rr=np.array([1.0]),
        stop_cap_points=np.array([700.0]),
    )
    trades = simulate(bars, signal, EURUSD, NO_COST, RunConfig())
    assert trades.loc[0, "stop_points"] == pytest.approx(700.0, abs=1e-6)


def test_one_position_only_blocks_overlapping_signals():
    bars = make_bars([1.1000] * 40, spread_price=0.00010)
    signals = Signals(
        entry_index=np.array([1, 2, 3]),
        direction=np.array([1, 1, 1]),
        stop_min_points=np.array([500.0] * 3),
        stop_atr_points=np.zeros(3),
        stop_ref_price=np.full(3, np.nan),
        rr=np.array([5.0] * 3),
        stop_cap_points=np.array([1e9] * 3),
    )
    trades = simulate(bars, signals, EURUSD, NO_COST, RunConfig(max_hold_bars=10))
    assert len(trades) == 1, "second and third signals arrive while flat is false"


def test_max_entries_per_day_is_enforced():
    bars = make_bars([1.1000] * 200, spread_price=0.00010)
    starts = np.array([1, 4, 7, 10])
    signals = Signals(
        entry_index=starts,
        direction=np.ones(4, dtype=int),
        stop_min_points=np.full(4, 100.0),
        stop_atr_points=np.zeros(4),
        stop_ref_price=np.full(4, np.nan),
        rr=np.full(4, 1.0),
        stop_cap_points=np.full(4, 1e9),
    )
    bars.loc[2, "bid_high"] = 1.10110
    bars.loc[5, "bid_high"] = 1.10110
    bars.loc[8, "bid_high"] = 1.10110
    bars.loc[11, "bid_high"] = 1.10110
    trades = simulate(bars, signals, EURUSD, NO_COST, RunConfig(max_entries_per_day=2))
    assert len(trades) == 2


def test_signals_beyond_the_series_are_dropped():
    bars = make_bars([1.1000] * 5, spread_price=0.00010)
    trades = simulate(bars, one_signal(4, 1, 100, 1.0), EURUSD, NO_COST, RunConfig())
    assert trades.empty
