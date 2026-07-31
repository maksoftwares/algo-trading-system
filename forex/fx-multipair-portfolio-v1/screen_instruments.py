"""Instrument screen: real broker cost vs real daily range. Read-only.

This is the check the Forex lane learned to run *first*. Eleven hypothesis
classes failed there for one reason — the spread was wider than the predictable
component of returns — and that was knowable in advance from a single ratio:

    tradeability = median daily range / round-trip cost

Measured on this account previously: XAUUSD 211.7x, AUDUSD 33.7x, EURUSD 31.1x.
Everything below ~50x failed. Screening BTCUSD and US500 on the same ratio
decides which instrument is worth a strategy search at all.

Cost and range both come from live broker data, so the ratio is not an
assumption. Strictly read-only: symbol_info, symbol_info_tick, copy_ticks_range.
No orders, no modifications, demo asserted.
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

CANDIDATES = ("BTCUSD", "US500", "XAUUSD", "EURUSD", "AUDUSD", "ETHUSD", "USTEC", "US30")
DAYS_BACK = 21
SLIPPAGE_MULTIPLE = 1.5  # entry+stop slippage modelled as half a spread each side


def measure(symbol: str) -> dict | None:
    if not mt5.symbol_select(symbol, True):
        return None
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    end = datetime.now().replace(tzinfo=None)
    start = end - timedelta(days=DAYS_BACK)
    ticks = mt5.copy_ticks_range(symbol, start, end, mt5.COPY_TICKS_INFO)
    if ticks is None or len(ticks) == 0:
        return {"symbol": symbol, "error": f"no ticks ({mt5.last_error()})"}

    frame = pd.DataFrame(ticks)
    frame = frame[(frame["bid"] > 0) & (frame["ask"] > 0)]
    if frame.empty:
        return {"symbol": symbol, "error": "no valid quotes"}

    point = info.point
    stamps = pd.to_datetime(frame["time_msc"], unit="ms", utc=True)
    spread_points = ((frame["ask"] - frame["bid"]) / point).to_numpy()
    mid = ((frame["ask"] + frame["bid"]) / 2).to_numpy()

    # daily range from tick mids
    day = stamps.dt.strftime("%Y-%m-%d").to_numpy()
    frame2 = pd.DataFrame({"day": day, "mid": mid})
    daily = frame2.groupby("day")["mid"].agg(["max", "min", "mean"])
    daily_range_points = ((daily["max"] - daily["min"]) / point).median()
    median_price = float(np.median(mid))

    spread_median = float(np.median(spread_points))
    round_trip = spread_median * (1.0 + SLIPPAGE_MULTIPLE * 0.5)
    return {
        "symbol": symbol,
        "median_price": round(median_price, 2),
        "point": point,
        "digits": info.digits,
        "spread_points_median": round(spread_median, 1),
        "spread_pct_of_price": round(100.0 * spread_median * point / median_price, 4),
        "round_trip_points": round(round_trip, 1),
        "daily_range_points": round(float(daily_range_points), 1),
        "daily_range_pct": round(100.0 * float(daily_range_points) * point / median_price, 3),
        "tradeability_ratio": round(float(daily_range_points) / round_trip, 1),
        "volume_min": info.volume_min,
        "volume_step": info.volume_step,
        "contract_size": info.trade_contract_size,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "days_observed": int(daily.shape[0]),
        "ticks": int(len(frame)),
    }


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
        print(f"window: last {DAYS_BACK} days\n")

        rows = []
        for symbol in CANDIDATES:
            result = measure(symbol)
            if result is None:
                print(f"{symbol:9s} not available on this server")
                continue
            if "error" in result:
                print(f"{symbol:9s} {result['error']}")
                continue
            rows.append(result)

        rows.sort(key=lambda r: -r["tradeability_ratio"])
        print(
            f"\n{'symbol':9s} {'price':>11} {'spread_pts':>11} {'spread%':>9} "
            f"{'dayrange_pts':>13} {'range%':>8} {'RATIO':>8} {'minlot':>7}"
        )
        print("-" * 84)
        for r in rows:
            print(
                f"{r['symbol']:9s} {r['median_price']:>11,.1f} {r['spread_points_median']:>11,.0f} "
                f"{r['spread_pct_of_price']:>8.3f}% {r['daily_range_points']:>13,.0f} "
                f"{r['daily_range_pct']:>7.2f}% {r['tradeability_ratio']:>8.1f}x {r['volume_min']:>7}"
            )

        print("\nreference from the Forex lane: XAUUSD 211.7x, AUDUSD 33.7x, EURUSD 31.1x")
        print("below ~50x, eleven hypothesis classes failed on cost alone")

        out = ROOT / "outputs" / "INSTRUMENT_SCREEN.json"
        out.write_text(
            json.dumps(
                {
                    "schema_version": "instrument_screen_v1",
                    "account": {"login": account.login, "server": account.server},
                    "days_back": DAYS_BACK,
                    "ratio_definition": "median daily range / (spread * 1.75)",
                    "reference_ratios": {"XAUUSD": 211.7, "AUDUSD": 33.7, "EURUSD": 31.1},
                    "ranked": rows,
                },
                indent=2, sort_keys=True,
            ),
            encoding="utf-8",
        )
        print(f"\nwrote {out}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
