"""Month-by-month backtest P&L for every candidate, at measured broker cost.

Answers "what would these have made recently". All figures are **backtest**
P&L at 0.01 lot, priced with the real Capital.com spreads measured from broker
tick history — not the assumed model R1-R6 used, and not live trading. Nothing
here was traded.

Covers 2024-07 .. 2026-06, the most recent 24 months.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from calibrate_reference import reference_signals  # noqa: E402
from run_cross_search import cross_costs, cross_spread_points  # noqa: E402
from src.engine import CostModel, RunConfig, SymbolSpec, simulate  # noqa: E402
from src.fxdata import INSTRUMENTS, load_m5  # noqa: E402
from src.report import (  # noqa: E402
    MEASURED_SPREAD_POINTS,
    SLIPPAGE_POINTS,
    STOP_SLIPPAGE_POINTS,
    measured_costs,
    monthly_net,
    slice_window,
    summarize,
)
from src.strategies import FAMILIES, build_signals  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
START, END = "2024-07-01", "2026-07-01"
LOT = 0.01


def raw_median_spread(bars: pd.DataFrame, symbol: str) -> float:
    point = float(INSTRUMENTS[symbol]["point_size"])
    return float(((bars["ask_close"] - bars["bid_close"]) / point).median())


def run_reference() -> pd.DataFrame:
    symbol = "EURUSD"
    bars = slice_window(load_m5(CACHE, symbol), START, END)
    signals = reference_signals(bars, symbol)
    costs = CostModel(**measured_costs(symbol, raw_median_spread(bars, symbol)))
    config = RunConfig(lot=LOT, max_hold_bars=288 * 5, max_entries_per_day=20)
    return simulate(bars, signals, SymbolSpec.of(symbol), costs, config)


def run_family(family: str, symbol: str, rr: float, atr_mult: float, ctx: float) -> pd.DataFrame:
    bars = slice_window(load_m5(CACHE, symbol), START, END)
    candidates = FAMILIES[family](bars, symbol)
    floor = 10.0 * (MEASURED_SPREAD_POINTS[symbol] + SLIPPAGE_POINTS + STOP_SLIPPAGE_POINTS)
    signals = build_signals(
        candidates, stop_floor_points=floor, context_mult=ctx,
        atr_mult=atr_mult, rr=rr, stop_cap_points=1500.0,
    )
    costs = CostModel(**measured_costs(symbol, raw_median_spread(bars, symbol)))
    hold = 2880 if family == "donchian_h4" else 288
    config = RunConfig(lot=LOT, max_hold_bars=hold, max_entries_per_day=3)
    return simulate(bars, signals, SymbolSpec.of(symbol), costs, config)


def run_gbpjpy() -> pd.DataFrame:
    symbol = "GBPJPY"
    bars = slice_window(load_m5(CACHE, symbol), START, END)
    candidates = FAMILIES["donchian_h4"](bars, symbol)
    floor = 10.0 * (cross_spread_points(symbol) + SLIPPAGE_POINTS + STOP_SLIPPAGE_POINTS)
    signals = build_signals(
        candidates, stop_floor_points=floor, context_mult=0.5,
        atr_mult=3.0, rr=1.2, stop_cap_points=3000.0,
    )
    costs = cross_costs(symbol, raw_median_spread(bars, symbol))
    config = RunConfig(lot=LOT, max_hold_bars=2880, max_entries_per_day=3)
    return simulate(bars, signals, SymbolSpec.of(symbol), costs, config)


def main() -> int:
    print("BACKTEST monthly P&L, 0.01 lot, at MEASURED Capital.com spreads")
    print(f"window {START} .. {END}   (nothing here was traded live)\n")

    candidates: dict[str, pd.DataFrame] = {
        "EURUSD inherited RSI/BB fade (R2)": run_reference(),
        "EURUSD london_breakout (R1 best)": run_family("london_breakout", "EURUSD", 1.5, 3.0, 0.0),
        "USDJPY asia_fade (R1 best)": run_family("asia_fade", "USDJPY", 2.5, 3.0, 0.0),
        "GBPJPY donchian (R9 best candidate)": run_gbpjpy(),
    }

    months = pd.period_range("2024-07", "2026-06", freq="M").astype(str)
    table = pd.DataFrame(index=months)
    summary = {}
    for name, trades in candidates.items():
        series = monthly_net(trades)
        table[name] = [round(float(series.get(m, 0.0)), 2) for m in months]
        result = summarize(trades)
        summary[name] = result

    pd.set_option("display.width", 200)
    print("=== monthly net P&L (USD, 0.01 lot) ===")
    print(table.to_string())

    print("\n=== 24-month totals ===")
    print(f"{'candidate':38s} {'trades':>7} {'net USD':>10} {'PF':>7} {'WR%':>7} {'+months':>8} {'maxDD':>9}")
    print("-" * 92)
    payload = {}
    for name, result in summary.items():
        total = float(table[name].sum())
        pos = int((table[name] > 0).sum())
        print(
            f"{name:38s} {result['trades']:>7} {total:>10.2f} "
            f"{(result.get('profit_factor') or 0):>7.3f} {result.get('win_rate_pct', 0):>7.2f} "
            f"{pos:>4}/{len(months)} {result.get('max_closed_drawdown_usd', 0):>9.2f}"
        )
        payload[name] = {
            "trades": result["trades"],
            "net_usd_24m": round(total, 2),
            "profit_factor": result.get("profit_factor"),
            "win_rate_pct": result.get("win_rate_pct"),
            "positive_months": pos,
            "months": len(months),
            "max_closed_drawdown_usd": result.get("max_closed_drawdown_usd"),
            "monthly_net_usd": {m: float(table.loc[m, name]) for m in months},
        }

    print(
        "\nNOTE ON GBPJPY: it is a synthetic cross registered with a constant point value,\n"
        "so its PF and win rate are valid but its USD column is scaled by a large fixed\n"
        "factor and must not be read as dollars. See INSTRUMENTS in src/fxdata.py.\n"
    )
    print("READ: two candidates are marginally POSITIVE over these 24 months at real cost")
    print("(EURUSD inherited fade PF 1.064, USDJPY asia_fade PF 1.048). Neither is")
    print("deployable: each has a max drawdown roughly 3x its annual profit, and both are")
    print("single-pair picks — R1 rejected these families precisely because no parameter")
    print("set worked on all three pairs, so choosing the best pair is the cherry-pick the")
    print("preregistration forbade. The EURUSD rule was also tuned on this data by the")
    print("earlier lane, so this window is not clean for it either.")
    out = ROOT / "outputs" / "MONTHLY_PNL.json"
    out.write_text(
        json.dumps(
            {
                "schema_version": "fx_monthly_pnl_v1",
                "basis": "backtest only, 0.01 lot, measured Capital.com spreads, nothing traded live",
                "window": {"start": START, "end_exclusive": END},
                "candidates": payload,
            },
            indent=2, sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
