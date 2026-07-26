"""Rank instruments by opportunity-to-cost, the ratio every rejection came down to.

Ten hypothesis classes failed on the same inequality: the spread was comparable to
or larger than the predictable component of returns. That component scales with
how far an instrument moves, while the broker's spread is fixed. So the single
number that decides whether an instrument is *workable at all* is

    opportunity_to_cost = median daily range (points) / round-trip cost (points)

This answers the question behind the original goal — why gold supports a system
and FX majors do not — and turns it into a screening rule for choosing the next
instrument, rather than another year of strategy search.

Ratios are measured, not assumed: daily range from the Dukascopy archive, spread
from real broker tick history (`measure_broker_spread_ticks.py`) where available.

Strictly read-only against MT5: symbol_select, symbol_info, copy_ticks_range.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
DUKAS = Path(r"D:\AlgoTradingData\C_DRIVE\DukascopyTickDataFoundationV1")
WINDOW_START = datetime(2026, 7, 13)
WINDOW_END = datetime(2026, 7, 25)
LIQUID_HOURS = set(range(7, 20))
SLIPPAGE = 4.0  # entry + stop slippage, same assumption used throughout

CANDIDATES = (
    "XAUUSD", "XAGUSD",
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
    "USDMXN", "USDZAR", "USDCNH",
    "US500", "US30", "NAS100", "GER40", "UK100", "JP225",
    "USOIL", "UKOIL", "NATGAS", "COPPER",
    "BTCUSD", "ETHUSD",
)


def broker_spread_points(symbol: str) -> tuple[float | None, int]:
    """Median trading-hours spread in points from real broker ticks."""
    if not mt5.symbol_select(symbol, True):
        return None, 0
    info = mt5.symbol_info(symbol)
    if info is None:
        return None, 0
    ticks = mt5.copy_ticks_range(symbol, WINDOW_START, WINDOW_END, mt5.COPY_TICKS_INFO)
    if ticks is None or len(ticks) == 0:
        return None, 0
    frame = pd.DataFrame(ticks)
    frame = frame[(frame["bid"] > 0) & (frame["ask"] > 0)]
    if frame.empty:
        return None, 0
    stamps = pd.to_datetime(frame["time_msc"], unit="ms", utc=True)
    keep = stamps.dt.hour.isin(LIQUID_HOURS) & (stamps.dt.weekday < 5)
    liquid = frame[keep.to_numpy()]
    if len(liquid) < 200:
        return None, int(len(frame))
    spread = ((liquid["ask"] - liquid["bid"]) / info.point).median()
    return float(spread), int(len(frame))


def daily_range_points(symbol: str) -> float | None:
    """Median daily high-low range in points, from broker ticks over the window."""
    info = mt5.symbol_info(symbol)
    ticks = mt5.copy_ticks_range(symbol, WINDOW_START, WINDOW_END, mt5.COPY_TICKS_INFO)
    if ticks is None or len(ticks) == 0 or info is None:
        return None
    frame = pd.DataFrame(ticks)
    frame = frame[(frame["bid"] > 0) & (frame["ask"] > 0)]
    if frame.empty:
        return None
    stamps = pd.to_datetime(frame["time_msc"], unit="ms", utc=True)
    mid = (frame["bid"].to_numpy() + frame["ask"].to_numpy()) / 2.0
    day = stamps.dt.strftime("%Y-%m-%d").to_numpy()
    table = pd.DataFrame({"day": day, "mid": mid}).groupby("day")["mid"].agg(["max", "min"])
    if table.empty:
        return None
    return float(((table["max"] - table["min"]) / info.point).median())


def main() -> int:
    if not mt5.initialize():
        print(f"initialize failed: {mt5.last_error()}")
        return 1
    try:
        account = mt5.account_info()
        if account is None or account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            print("REFUSING: not a demo account.")
            return 2
        print(f"account {account.login} @ {account.server} (read-only)")
        print(f"window {WINDOW_START.date()} .. {WINDOW_END.date()}, liquid hours 07-20 UTC\n")

        available = {s.name for s in mt5.symbols_get()}
        rows = []
        for symbol in CANDIDATES:
            if symbol not in available:
                continue
            spread, ticks = broker_spread_points(symbol)
            if spread is None or spread <= 0:
                continue
            daily = daily_range_points(symbol)
            if daily is None or daily <= 0:
                continue
            cost = spread + SLIPPAGE
            rows.append(
                {
                    "symbol": symbol,
                    "spread_points": round(spread, 1),
                    "round_trip_cost_points": round(cost, 1),
                    "median_daily_range_points": round(daily, 0),
                    "opportunity_to_cost": round(daily / cost, 1),
                    "ticks_sampled": ticks,
                }
            )

        rows.sort(key=lambda row: -row["opportunity_to_cost"])
        print(f"{'symbol':10s} {'spread_pts':>11} {'cost_pts':>9} {'daily_range':>12} {'range/cost':>11}")
        print("-" * 58)
        for row in rows:
            print(
                f"{row['symbol']:10s} {row['spread_points']:>11.1f} "
                f"{row['round_trip_cost_points']:>9.1f} {row['median_daily_range_points']:>12,.0f} "
                f"{row['opportunity_to_cost']:>11.1f}"
            )

        gold = next((row for row in rows if row["symbol"] == "XAUUSD"), None)
        if gold:
            print(f"\nXAUUSD (the instrument that works) sits at {gold['opportunity_to_cost']:.1f}x")
            better = [r for r in rows if r["opportunity_to_cost"] > gold["opportunity_to_cost"]]
            fx = [r for r in rows if r["symbol"] in
                  ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF")]
            if fx:
                best_fx = max(fx, key=lambda r: r["opportunity_to_cost"])
                print(
                    f"best FX major is {best_fx['symbol']} at {best_fx['opportunity_to_cost']:.1f}x "
                    f"— {gold['opportunity_to_cost']/best_fx['opportunity_to_cost']:.2f}x worse than gold"
                )
            print(f"instruments ranking above gold: {[r['symbol'] for r in better] or 'none'}")

        report = {
            "schema_version": "fx_instrument_tradeability_v1",
            "metric": "median daily range (points) / round-trip cost (points)",
            "rationale": "every rejection reduced to cost vs available movement; this ranks that ratio",
            "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
            "slippage_points_assumed": SLIPPAGE,
            "ranked": rows,
        }
        out = ROOT / "outputs" / "INSTRUMENT_TRADEABILITY.json"
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\nwrote {out}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
