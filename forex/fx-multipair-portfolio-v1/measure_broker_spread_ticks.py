"""Measure the real Capital.com demo FX spread from broker tick history.

`measure_broker_costs.py` could only read a weekend-wide live quote, and this
terminal refuses `copy_rates_*` ("Call failed" - it is serving a backtest data
path with no bar history synced). `copy_ticks_range` does work, which is the
better source anyway: actual broker bid/ask.

The output replaces the *assumed* cost model in `src/report.py`, which is the
single largest caveat on every rejection recorded so far.

Reported per symbol: median / p25 / p75 / p95 spread over liquid hours only
(07:00-20:00 UTC, Monday-Friday), plus a full by-hour profile, because FX spread
is strongly time-of-day dependent and the Asia and rollover windows are much
wider than the London/NY overlap.

Safety contract: read-only tick copy. No orders, no modifications, demo-only.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
LIQUID_HOURS = range(7, 20)

SYMBOLS = (
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
    "EURGBP", "EURJPY", "GBPJPY", "EURAUD", "AUDJPY", "CHFJPY", "AUDNZD",
    "USDMXN", "USDZAR", "USDPLN", "USDCNH",
)
# Two full trading weeks ending at the most recent Friday close.
WINDOW_START = datetime(2026, 7, 13)
WINDOW_END = datetime(2026, 7, 25)


def main() -> int:
    if not mt5.initialize():
        print(f"initialize failed: {mt5.last_error()}")
        return 1
    try:
        account = mt5.account_info()
        if account is None or account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            print("REFUSING: not a demo account.")
            return 2
        print(f"account {account.login} @ {account.server} (read-only tick copy)")
        print(f"window {WINDOW_START.date()} .. {WINDOW_END.date()}, liquid hours 07-20 UTC\n")

        report: dict[str, object] = {
            "schema_version": "fx_broker_spread_ticks_v1",
            "access": "READ_ONLY_COPY_TICKS_NO_ORDERS",
            "account": {"login": account.login, "server": account.server},
            "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
            "liquid_hours_utc": [LIQUID_HOURS.start, LIQUID_HOURS.stop],
            "symbols": {},
        }
        print(
            f"{'symbol':9s} {'ticks':>9} {'pip':>7} | liquid-hours spread in PIPS  "
            f"{'p25':>6} {'med':>6} {'p75':>6} {'p95':>6} | {'allhrs_med':>10}"
        )
        print("-" * 92)

        for symbol in SYMBOLS:
            if not mt5.symbol_select(symbol, True):
                print(f"{symbol:9s} not selectable")
                continue
            info = mt5.symbol_info(symbol)
            ticks = mt5.copy_ticks_range(
                symbol, WINDOW_START, WINDOW_END, mt5.COPY_TICKS_INFO
            )
            if ticks is None or len(ticks) == 0:
                print(f"{symbol:9s} no ticks ({mt5.last_error()})")
                continue

            frame = pd.DataFrame(ticks)
            frame = frame[(frame["bid"] > 0) & (frame["ask"] > 0)]
            stamps = pd.to_datetime(frame["time_msc"], unit="ms", utc=True)
            point = info.point
            pip_points = 10.0 if info.digits in (3, 5) else 1.0
            spread_pips = ((frame["ask"] - frame["bid"]) / point / pip_points).to_numpy()
            hour = stamps.dt.hour.to_numpy()
            weekday = stamps.dt.weekday.to_numpy()

            liquid = np.isin(hour, list(LIQUID_HOURS)) & (weekday < 5)
            liquid_spread = spread_pips[liquid]
            if liquid_spread.size == 0:
                print(f"{symbol:9s} no liquid-hour ticks")
                continue

            by_hour = {
                int(h): round(float(np.median(spread_pips[(hour == h) & (weekday < 5)])), 3)
                for h in range(24)
                if ((hour == h) & (weekday < 5)).sum() > 50
            }
            record = {
                "ticks": int(len(frame)),
                "digits": info.digits,
                "point": point,
                "pip_points": pip_points,
                "spread_pips_liquid_p25": round(float(np.quantile(liquid_spread, 0.25)), 3),
                "spread_pips_liquid_median": round(float(np.median(liquid_spread)), 3),
                "spread_pips_liquid_p75": round(float(np.quantile(liquid_spread, 0.75)), 3),
                "spread_pips_liquid_p95": round(float(np.quantile(liquid_spread, 0.95)), 3),
                "spread_pips_allhours_median": round(float(np.median(spread_pips)), 3),
                "spread_points_liquid_median": round(float(np.median(liquid_spread)) * pip_points, 2),
                "spread_pips_median_by_hour_utc": by_hour,
                "swap_long": info.swap_long,
                "swap_short": info.swap_short,
            }
            report["symbols"][symbol] = record
            print(
                f"{symbol:9s} {record['ticks']:>9} {pip_points:>7.0f} | "
                f"{record['spread_pips_liquid_p25']:>28.2f} "
                f"{record['spread_pips_liquid_median']:>6.2f} "
                f"{record['spread_pips_liquid_p75']:>6.2f} "
                f"{record['spread_pips_liquid_p95']:>6.2f} | "
                f"{record['spread_pips_allhours_median']:>10.2f}"
            )

        out = ROOT / "outputs" / "BROKER_SPREAD_TICKS.json"
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\nwrote {out}")

        found = report["symbols"]
        if found:
            print("\nby-hour median spread (pips), majors — shows the session cost profile:")
            for symbol in ("EURUSD", "GBPUSD", "USDJPY"):
                if symbol in found:
                    profile = found[symbol]["spread_pips_median_by_hour_utc"]
                    line = " ".join(f"{h:02d}:{v:.1f}" for h, v in sorted(profile.items()))
                    print(f"  {symbol}: {line}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
