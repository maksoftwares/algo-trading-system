"""Correct portfolio booking: entry-order state, heap-settled exits, one PF.

This module exists because of a specific defect. Position size in the GOLD V8
work was assigned by walking trades in EXIT order, so a trade's multiplier could
depend on trades that closed after it opened. With ~25h average holds and up to 6
concurrent positions, 63.5% of trades were affected, and correcting it moved the
causal walk-forward from PF 2.034 to 1.202.

Three rules are enforced here so the mistake cannot recur:

  1. STATE IS BUILT IN ENTRY ORDER. Before a trade is sized, only trades whose
     exit time is at or before its ENTRY time are settled, popped from a min-heap.
     Nothing that closes later can influence it.
  2. SLOTS ARE RESERVED AT ENTRY, not at the decision bar. A live EA cannot
     reserve capacity using confirmation or exit information that does not exist
     yet, so neither does this.
  3. PROFIT FACTOR IS COMPUTED ON THE DOLLAR SERIES. The same column that
     produces P&L and drawdown produces PF. Reporting PF on R while reporting
     dollars from a scaled series produced impossible figures such as
     "PF 0.89 with +$1,259" three separate times.

`test_booking.py` contains a regression test that fails against exit-order
sizing and passes here.
"""
from __future__ import annotations
import heapq
import numpy as np
import pandas as pd

__all__ = ["streak_sizes", "book", "metrics", "exit_order_sizes_UNSAFE"]


def streak_sizes(entry_t, exit_t, r, half_at=2, quarter_at=4,
                 half=0.5, quarter=0.25):
    """Position multiplier per trade, derived strictly in entry order.

    A trade is sized using only results already realised at its entry. Streak
    state advances as prior positions settle, popped from a heap of pending
    exits.

    Parameters are positional arrays aligned to one another; the return is an
    array of multipliers in the SAME order as the inputs.
    """
    entry_t = np.asarray(entry_t)
    exit_t = np.asarray(exit_t)
    r = np.asarray(r, dtype=float)
    n = len(entry_t)
    if not (len(exit_t) == len(r) == n):
        raise ValueError("entry_t, exit_t and r must be the same length")

    order = np.argsort(entry_t, kind="mergesort")     # stable: ties keep input order
    sizes = np.ones(n, dtype=float)
    pending: list[tuple] = []                          # (exit_t, r) not yet settled
    streak = 0
    for k in order:
        et = entry_t[k]
        while pending and pending[0][0] <= et:         # settle everything closed by now
            _, past_r = heapq.heappop(pending)
            streak = 0 if past_r > 0 else streak + 1
        sizes[k] = (quarter if streak >= quarter_at
                    else half if streak >= half_at
                    else 1.0)
        heapq.heappush(pending, (exit_t[k], float(r[k])))
    return sizes


def exit_order_sizes_UNSAFE(exit_t, r, half_at=2, quarter_at=4,
                            half=0.5, quarter=0.25):
    """The defective implementation, kept ONLY so the regression test can prove
    the two disagree. Never use this to produce a result."""
    exit_t = np.asarray(exit_t)
    r = np.asarray(r, dtype=float)
    sizes = np.ones(len(r), dtype=float)
    streak = 0
    for k in np.argsort(exit_t, kind="mergesort"):
        sizes[k] = (quarter if streak >= quarter_at
                    else half if streak >= half_at else 1.0)
        streak = 0 if r[k] > 0 else streak + 1
    return sizes


def book(df, K, entry_col="entry_t", exit_col="exit_t", dedup_col=None,
         rank_col=None):
    """Apply a K-slot lockout, reserving at ENTRY and releasing from a heap.

    dedup_col: collapse rows sharing this key to one position (e.g. the decision
    bar), keeping the highest `rank_col` where given.
    """
    d = df.copy()
    if dedup_col is not None:
        if rank_col is not None:
            d = d.sort_values(rank_col, ascending=False)
        d = d.groupby(dedup_col, as_index=False).first()
    d = d.sort_values(entry_col, kind="mergesort").reset_index(drop=True)
    pending: list = []
    keep = []
    for row in d.itertuples():
        et = getattr(row, entry_col)
        while pending and pending[0] <= et:
            heapq.heappop(pending)
        if len(pending) >= K:
            continue
        keep.append(row.Index)
        heapq.heappush(pending, getattr(row, exit_col))
    return d.loc[keep].reset_index(drop=True)


def metrics(df, usd_col="usd", time_col="exit_t"):
    """Win rate, profit factor, P&L, drawdown and green months - every one of
    them computed from `usd_col`, so they cannot disagree with each other."""
    g = df.dropna(subset=[usd_col])
    if not len(g):
        return dict(n=0, wr=0.0, pf=0.0, usd=0.0, dd=0.0, green=0, months=0)
    g = g.sort_values(time_col, kind="mergesort")
    u = g[usd_col].to_numpy(dtype=float)
    w, l = u[u > 0], u[u <= 0]
    eq = np.cumsum(u)
    # strftime rather than to_period: the latter warns and silently drops tz
    m = g.groupby(pd.to_datetime(g[time_col]).dt.strftime("%Y-%m"))[usd_col].sum()
    return dict(
        n=int(len(u)),
        wr=round(100.0 * len(w) / len(u), 1),
        pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 3),
        usd=round(float(u.sum()), 2),
        dd=round(float(np.max(np.maximum.accumulate(eq) - eq)), 2),
        green=int((m > 0).sum()),
        months=int(len(m)),
        worst_month=round(float(m.min()), 2))
