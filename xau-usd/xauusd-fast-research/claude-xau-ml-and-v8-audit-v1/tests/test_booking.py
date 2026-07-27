"""Regression tests for the defects that invalidated GOLD V8.

The first test is the important one: it constructs the exact situation the
original code got wrong and asserts the two implementations disagree. If someone
reintroduces exit-order sizing, this fails.
"""
import numpy as np
import pandas as pd
import pytest

from booking import (streak_sizes, exit_order_sizes_UNSAFE, book, metrics)


def T(*mins):
    """Minutes-from-epoch as datetimes, for readable fixtures."""
    base = pd.Timestamp("2026-01-01", tz="UTC")
    return [base + pd.Timedelta(minutes=m) for m in mins]


# ---------------------------------------------------------------- the core bug

def test_long_holder_is_not_sized_by_trades_that_open_after_it():
    """A position opened first, held longest, must not be sized by losses that
    occurred entirely inside its own holding period.

    T1 enters at 0 and exits at 50. T2 and T3 open and close inside that window
    and both lose. Sorting by EXIT time puts T1 last, so it inherits a 2-loss
    streak from trades that did not exist when it opened - future information.
    """
    entry = T(0, 10, 12)
    exit_ = T(50, 20, 22)
    r = [1.0, -1.0, -1.0]          # T1 wins; T2, T3 lose

    safe = streak_sizes(entry, exit_, r, half_at=2, quarter_at=4)
    unsafe = exit_order_sizes_UNSAFE(exit_, r, half_at=2, quarter_at=4)

    assert safe[0] == 1.0, "T1 opened first with nothing settled - must be full size"
    assert unsafe[0] == 0.5, "exit-order sizing wrongly halves T1"
    assert not np.allclose(safe, unsafe), "the two implementations must differ here"


def test_sizing_uses_only_trades_settled_by_entry_time():
    """Three sequential losers then a fourth trade: the fourth is halved only
    because the first two had actually closed before it opened."""
    entry = T(0, 10, 20, 30)
    exit_ = T(5, 15, 25, 35)
    r = [-1.0, -1.0, -1.0, 1.0]
    s = streak_sizes(entry, exit_, r, half_at=2, quarter_at=4)
    assert list(s) == [1.0, 1.0, 0.5, 0.5]


def test_a_winner_resets_the_streak():
    entry = T(0, 10, 20, 30)
    exit_ = T(5, 15, 25, 35)
    r = [-1.0, -1.0, 1.0, -1.0]
    s = streak_sizes(entry, exit_, r, half_at=2, quarter_at=4)
    assert list(s) == [1.0, 1.0, 0.5, 1.0], "the win at index 2 must clear the streak"


def test_quarter_trip_engages_after_four():
    entry = T(0, 10, 20, 30, 40, 50)
    exit_ = T(5, 15, 25, 35, 45, 55)
    r = [-1.0] * 6
    s = streak_sizes(entry, exit_, r, half_at=2, quarter_at=4)
    assert list(s) == [1.0, 1.0, 0.5, 0.5, 0.25, 0.25]


def test_sizes_are_returned_in_input_order_not_sorted_order():
    """Inputs deliberately out of chronological order; the result must align to
    the rows as given, not to the internal sort."""
    entry = T(30, 0, 10, 20)
    exit_ = T(35, 5, 15, 25)
    r = [1.0, -1.0, -1.0, -1.0]
    s = streak_sizes(entry, exit_, r, half_at=2, quarter_at=4)
    assert s[1] == 1.0 and s[2] == 1.0      # first two chronologically
    assert s[3] == 0.5 and s[0] == 0.5      # after two settled losses


# ------------------------------------------------------------------- the book

def test_slots_are_reserved_at_entry_and_released_by_actual_exit():
    d = pd.DataFrame({"entry_t": T(0, 1, 2, 100), "exit_t": T(50, 60, 70, 110),
                      "i": [1, 2, 3, 4]})
    kept = book(d, K=2)
    assert list(kept.i) == [1, 2, 4], "third overlapping entry blocked; fourth fits"


def test_dedup_keeps_the_highest_ranked_row_per_key():
    d = pd.DataFrame({"entry_t": T(0, 0, 10), "exit_t": T(5, 5, 15),
                      "i": [1, 1, 2], "score": [0.1, 0.9, 0.5]})
    kept = book(d, K=5, dedup_col="i", rank_col="score")
    assert len(kept) == 2
    assert kept.loc[kept.i == 1, "score"].iloc[0] == pytest.approx(0.9)


# ---------------------------------------------------------------- the metrics

def test_profit_factor_is_computed_on_the_reported_dollar_series():
    """PF, P&L and drawdown must all come from the same column. Scaling the
    dollars must move PF only if the scaling is non-uniform."""
    d = pd.DataFrame({"exit_t": T(0, 10, 20, 30),
                      "usd": [100.0, -50.0, 200.0, -100.0]})
    m = metrics(d)
    assert m["pf"] == pytest.approx(300 / 150)
    assert m["usd"] == pytest.approx(150.0)

    uniform = d.assign(usd=d.usd * 3.0)
    assert metrics(uniform)["pf"] == pytest.approx(m["pf"]), \
        "uniform scaling must not change PF"

    nonuniform = d.assign(usd=d.usd * np.array([1.0, 0.5, 1.0, 0.5]))
    assert metrics(nonuniform)["pf"] > m["pf"], \
        "shrinking only the losers must raise PF"


def test_drawdown_is_peak_to_trough_on_the_same_series():
    d = pd.DataFrame({"exit_t": T(0, 10, 20, 30),
                      "usd": [100.0, -30.0, -40.0, 20.0]})
    m = metrics(d)
    assert m["dd"] == pytest.approx(70.0)     # 100 -> 30
    assert m["usd"] == pytest.approx(50.0)


def test_metrics_are_order_independent_of_input_row_order():
    rows = {"exit_t": T(30, 0, 20, 10), "usd": [20.0, 100.0, -40.0, -30.0]}
    a = metrics(pd.DataFrame(rows))
    b = metrics(pd.DataFrame(rows).sample(frac=1.0, random_state=0))
    assert a == b, "metrics must sort by time internally"


def test_empty_input_does_not_raise():
    m = metrics(pd.DataFrame({"exit_t": [], "usd": []}))
    assert m["n"] == 0 and m["pf"] == 0.0
