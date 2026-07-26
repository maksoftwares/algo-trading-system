"""Shared metrics so every stage reports the same numbers the same way."""

from __future__ import annotations

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Cost model. The ASSUMED values below were used for R1-R6; the MEASURED values
# come from `measure_broker_spread_ticks.py` reading real Capital.com MENA demo
# tick history (outputs/BROKER_SPREAD_TICKS.json).
#
# The broker quotes a *fixed* spread: p25 == median == p95 at every hour except
# the 21:00 UTC rollover. That is why MEASURED_SPREAD_POINTS is a constant per
# symbol rather than a markup over the variable Dukascopy quote.
#
# Real cost is ~30% below what R1-R6 assumed for EURUSD. It does not overturn
# any rejection: R1's families and R4's drift both fail at *zero* cost, which
# bounds anything a cheaper spread could rescue.
# --------------------------------------------------------------------------
MEASURED_SPREAD_POINTS = {
    "AUDUSD": 6.0,
    "EURUSD": 7.0,
    "USDJPY": 12.0,
    "GBPUSD": 13.0,
    "USDCHF": 14.0,
    "NZDUSD": 16.0,
    "USDCAD": 20.0,
    "USDCNH": 100.0,
    "USDMXN": 212.0,
    "USDPLN": 247.0,
    "USDZAR": 500.0,
}
SLIPPAGE_POINTS = 2.0
STOP_SLIPPAGE_POINTS = 2.0

# Assumed model retained verbatim so R1-R6 stay exactly reproducible.
COSTS: dict[str, dict[str, float]] = {
    "EURUSD": {"spread_markup_points": 9.0, "slippage_points": 2.0, "stop_slippage_points": 2.0},
    "GBPUSD": {"spread_markup_points": 9.0, "slippage_points": 2.0, "stop_slippage_points": 2.0},
    "USDJPY": {"spread_markup_points": 10.0, "slippage_points": 2.0, "stop_slippage_points": 2.0},
}
ROUND_TRIP_COST_POINTS = {"EURUSD": 16.0, "GBPUSD": 22.0, "USDJPY": 18.0}

# Measured round trip = fixed spread + entry slip + stop slip.
MEASURED_ROUND_TRIP_POINTS = {
    symbol: spread + SLIPPAGE_POINTS + STOP_SLIPPAGE_POINTS
    for symbol, spread in MEASURED_SPREAD_POINTS.items()
}


def measured_costs(symbol: str, raw_median_spread_points: float) -> dict[str, float]:
    """Cost kwargs that reproduce the broker's fixed spread on Dukascopy quotes.

    Dukascopy quotes carry their own variable spread, so the markup needed is the
    gap up to the broker's fixed spread. Clamped at zero because in a handful of
    stressed moments the raw spread already exceeds the broker's fixed quote —
    a fixed-spread broker genuinely underprices liquidity in thin conditions.
    """
    markup = max(MEASURED_SPREAD_POINTS[symbol] - raw_median_spread_points, 0.0)
    return {
        "spread_markup_points": markup,
        "slippage_points": SLIPPAGE_POINTS,
        "stop_slippage_points": STOP_SLIPPAGE_POINTS,
    }
STOP_FLOOR_POINTS = {symbol: 10.0 * cost for symbol, cost in ROUND_TRIP_COST_POINTS.items()}

PARTITIONS = {
    "design": ("2016-07-01", "2022-01-01"),
    "validation": ("2022-01-01", "2024-07-01"),
    "final_exam": ("2024-07-01", "2026-07-01"),
}


def profit_factor(net: np.ndarray) -> float | None:
    gross_profit = float(net[net > 0].sum())
    gross_loss = float(-net[net <= 0].sum())
    if gross_loss <= 0:
        return None if gross_profit <= 0 else float("inf")
    return gross_profit / gross_loss


def max_closed_drawdown(net: np.ndarray) -> float:
    if net.size == 0:
        return 0.0
    equity = np.cumsum(net)
    return float(np.max(np.maximum.accumulate(equity) - equity))


def pf_excluding_best(net: np.ndarray, fraction: float = 0.05) -> float | None:
    """PF after dropping the best ``fraction`` of trades — a concentration test."""
    if net.size == 0:
        return None
    drop = int(np.ceil(net.size * fraction))
    kept = np.sort(net)[: net.size - drop] if drop else net
    return profit_factor(kept)


def monthly_net(trades: pd.DataFrame) -> pd.Series:
    if trades.empty:
        return pd.Series(dtype=float)
    stamps = pd.to_datetime(trades["exit_ms"], unit="ms", utc=True)
    return trades.groupby(stamps.dt.strftime("%Y-%m"))["net_usd"].sum()


def active_days(trades: pd.DataFrame) -> int:
    if trades.empty:
        return 0
    stamps = pd.to_datetime(trades["entry_ms"], unit="ms", utc=True)
    return int(stamps.dt.strftime("%Y-%m-%d").nunique())


def summarize(trades: pd.DataFrame, account_usd: float = 10_000.0) -> dict:
    """One metric dict used by design, validation, exam and portfolio stages."""
    if trades.empty:
        return {"trades": 0, "profit_factor": None, "net_usd": 0.0}
    net = trades["net_usd"].to_numpy()
    months = monthly_net(trades)
    drawdown = max_closed_drawdown(net)
    wins = net[net > 0]
    losses = net[net <= 0]
    return {
        "trades": int(net.size),
        "win_rate_pct": round(100.0 * wins.size / net.size, 2),
        "net_usd": round(float(net.sum()), 2),
        "profit_factor": None if profit_factor(net) is None else round(profit_factor(net), 4),
        "expectancy_usd": round(float(net.mean()), 4),
        "avg_win_usd": round(float(wins.mean()), 4) if wins.size else 0.0,
        "avg_loss_usd": round(float(losses.mean()), 4) if losses.size else 0.0,
        "avg_stop_points": round(float(trades["stop_points"].mean()), 1),
        "max_closed_drawdown_usd": round(drawdown, 2),
        "max_closed_drawdown_pct": round(100.0 * drawdown / account_usd, 3),
        "pf_excluding_best_5pct": (
            None
            if pf_excluding_best(net) is None
            else round(pf_excluding_best(net), 4)
        ),
        "active_days": active_days(trades),
        "trades_per_active_day": round(net.size / max(active_days(trades), 1), 3),
        "months_active": int(months.size),
        "months_positive": int((months > 0).sum()),
        "months_positive_pct": round(100.0 * float((months > 0).mean()), 1) if months.size else 0.0,
        "median_bars_held": int(trades["bars_held"].median()),
        "timeout_pct": round(100.0 * float((trades["exit_reason"] == "timeout").mean()), 1),
        "ambiguous_bars": int(trades["ambiguous_bar"].sum()),
    }


def slice_window(bars: pd.DataFrame, start: str, end_exclusive: str) -> pd.DataFrame:
    stamps = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
    mask = (stamps >= start) & (stamps < end_exclusive)
    return bars.loc[mask].reset_index(drop=True)
