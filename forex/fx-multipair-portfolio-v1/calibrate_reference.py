"""Replay the inherited EURUSD M30 RSI/Bollinger fade and stress its spread.

Two purposes:

1. Engine sanity. The inherited MT5 run used a Capital.com feed and broker-local
   hour masks, so exact parity against Dukascopy UTC is impossible; this is a
   plausibility cross-check (trade count, win rate, PF in the right region),
   never a parity claim.
2. The real question. The prior lane recorded that Dukascopy-first EURUSD
   candidates "did not transfer to Capital.com". A 0.8R target on a ~30-70 point
   stop is spread-dominated, so this sweeps broker spread markup to measure how
   fast the edge dies. The answer sets the cost-robustness floor for every
   family this project preregisters.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.engine import CostModel, RunConfig, Signals, SymbolSpec, simulate  # noqa: E402
from src.fxdata import INSTRUMENTS, add_time_columns, load_m5, mid, resample_from_m5  # noqa: E402
from src.indicators import atr, bollinger, decision_to_execution, rolling_min, rsi, shift  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
START = "2022-07-01"
END = "2026-07-01"
BLOCKED_HOURS = (6, 7, 10, 13)


def reference_signals(m5: pd.DataFrame, symbol: str, blocked_hours=BLOCKED_HOURS) -> Signals:
    """The frozen inherited rule, on M30 decisions with M5 execution."""
    point = float(INSTRUMENTS[symbol]["point_size"])
    m30 = resample_from_m5(m5, 30)
    close = mid(m30, "close")
    high = mid(m30, "high")
    low = mid(m30, "low")

    # Indicators read the completed signal bar (shift by 1 at decision time).
    signal_close = shift(close, 1)
    signal_rsi = shift(rsi(close, 14), 1)
    _, _, lower = bollinger(close, 20, 2.0)
    signal_lower = shift(lower, 1)
    signal_atr = shift(atr(high, low, close, 14), 1)
    # Lowest low of the last six completed bars, as of the decision.
    signal_low6 = shift(rolling_min(low, 6), 1)

    hour = pd.to_datetime(m30["timestamp_ms"], unit="ms", utc=True).dt.hour.to_numpy()

    trigger = (
        np.isfinite(signal_close)
        & np.isfinite(signal_lower)
        & np.isfinite(signal_rsi)
        & np.isfinite(signal_atr)
        & (signal_close <= signal_lower)
        & (signal_rsi <= 35.0)
        & ~np.isin(hour, blocked_hours)
    )

    execution = decision_to_execution(m30["timestamp_ms"].to_numpy(), m5["timestamp_ms"].to_numpy(), 30 * 60_000)
    keep = trigger & (execution >= 0)
    picked = np.flatnonzero(keep)

    return Signals(
        entry_index=execution[picked],
        direction=np.ones(picked.size, dtype=np.int64),
        stop_min_points=np.full(picked.size, 30.0),
        stop_atr_points=(1.4 * signal_atr[picked]) / point,
        stop_ref_price=signal_low6[picked],
        rr=np.full(picked.size, 0.8),
        stop_cap_points=np.full(picked.size, 700.0),
    )


def metrics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"trades": 0}
    net = trades["net_usd"].to_numpy()
    wins = net[net > 0]
    losses = net[net <= 0]
    equity = np.cumsum(net)
    drawdown = float(np.max(np.maximum.accumulate(equity) - equity)) if net.size else 0.0
    gross_loss = float(-losses.sum())
    return {
        "trades": int(net.size),
        "win_rate_pct": round(100.0 * wins.size / net.size, 2),
        "net_usd": round(float(net.sum()), 2),
        "profit_factor": round(float(wins.sum() / gross_loss), 4) if gross_loss > 0 else None,
        "avg_stop_points": round(float(trades["stop_points"].mean()), 1),
        "max_closed_drawdown_usd": round(drawdown, 2),
        "median_bars_held": int(trades["bars_held"].median()),
        "ambiguous_bars": int(trades["ambiguous_bar"].sum()),
    }


def main() -> int:
    symbol = "EURUSD"
    m5 = load_m5(CACHE, symbol)
    timed = add_time_columns(m5)
    window = (timed["timestamp_utc"] >= START) & (timed["timestamp_utc"] < END)
    m5 = m5.loc[window].reset_index(drop=True)
    print(f"{symbol} M5 bars in {START}..{END}: {len(m5):,}\n")

    signals = reference_signals(m5, symbol)
    spec = SymbolSpec.of(symbol)
    config = RunConfig(lot=0.01, max_hold_bars=288 * 5, max_entries_per_day=20)

    print("Inherited MT5 reference (Capital.com feed): 831 trades, WR 59.33%, PF 1.20, net $101.82")
    print("Below: same rule on Dukascopy UTC at rising broker spread markup.\n")
    print(f"{'markup_pts':>10} {'eff_spread':>11} {'trades':>7} {'WR%':>7} {'PF':>7} {'net$':>9} {'DD$':>7}")
    print("-" * 64)

    rows = []
    raw_median = 3.0  # EURUSD median raw spread in points, from BAR_INTEGRITY
    for markup in (0.0, 3.0, 7.0, 10.0, 15.0, 20.0):
        costs = CostModel(spread_markup_points=markup)
        result = metrics(simulate(m5, signals, spec, costs, config))
        result["markup_points"] = markup
        result["effective_spread_points"] = raw_median + markup
        rows.append(result)
        pf = result.get("profit_factor")
        print(
            f"{markup:>10.0f} {raw_median + markup:>11.1f} {result['trades']:>7} "
            f"{result['win_rate_pct']:>7.2f} {pf if pf is None else f'{pf:>7.3f}'} "
            f"{result['net_usd']:>9.2f} {result['max_closed_drawdown_usd']:>7.2f}"
        )

    baseline = rows[0]
    print(
        f"\naverage stop {baseline['avg_stop_points']:.0f} points; "
        f"median hold {baseline['median_bars_held']} M5 bars; "
        f"ambiguous bars {baseline['ambiguous_bars']}"
    )
    out = ROOT / "outputs" / "REFERENCE_SPREAD_STRESS.json"
    out.write_text(
        json.dumps(
            {
                "schema_version": "fx_reference_spread_stress_v1",
                "purpose": "engine sanity plus spread-sensitivity diagnosis; not an MT5 parity claim",
                "symbol": symbol,
                "window": {"start": START, "end_exclusive": END},
                "inherited_mt5_reference": {
                    "feed": "Capital.com via MT5 Strategy Tester",
                    "trades": 831,
                    "win_rate_pct": 59.33,
                    "profit_factor": 1.20,
                    "net_usd": 101.82,
                },
                "dukascopy_spread_sweep": rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
