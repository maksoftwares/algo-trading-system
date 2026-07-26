"""Integrity and coverage report for the M5 bid/ask cache.

Checks the properties a backtest silently depends on: monotonic unique
timestamps, non-negative spreads, OHLC containment, weekday coverage against
the expected 288 bars/day, and spread distribution per year.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import INSTRUMENTS, add_time_columns, iso, load_m5  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")


def check_symbol(symbol: str) -> dict:
    frame = load_m5(CACHE, symbol)
    point = float(INSTRUMENTS[symbol]["point_size"])
    stamps = frame["timestamp_ms"].to_numpy(np.int64)

    spread = frame["ask_close"].to_numpy() - frame["bid_close"].to_numpy()
    timed = add_time_columns(frame)
    per_day = timed.groupby("date").size()
    weekday = timed["weekday"].to_numpy()

    spread_by_year = (
        pd.DataFrame({"year": timed["year"], "spread_points": spread / point})
        .groupby("year")["spread_points"]
        .agg(["median", lambda s: s.quantile(0.95)])
        .rename(columns={"<lambda_0>": "p95"})
    )

    bad_bid = int((frame["bid_high"] < frame["bid_low"]).sum())
    bad_ask = int((frame["ask_high"] < frame["ask_low"]).sum())
    contain_bid = int(
        (
            (frame["bid_open"] > frame["bid_high"])
            | (frame["bid_open"] < frame["bid_low"])
            | (frame["bid_close"] > frame["bid_high"])
            | (frame["bid_close"] < frame["bid_low"])
        ).sum()
    )

    return {
        "symbol": symbol,
        "m5_bars": int(len(frame)),
        "first_bar_utc": iso(int(stamps[0])),
        "last_bar_utc": iso(int(stamps[-1])),
        "duplicate_timestamps": int(len(stamps) - len(np.unique(stamps))),
        "non_monotonic": int((np.diff(stamps) <= 0).sum()),
        "negative_spread_bars": int((spread < 0).sum()),
        "zero_spread_bars": int((spread == 0).sum()),
        "inverted_bid_bars": bad_bid,
        "inverted_ask_bars": bad_ask,
        "bid_containment_violations": contain_bid,
        "median_spread_points": float(np.median(spread) / point),
        "p95_spread_points": float(np.quantile(spread, 0.95) / point),
        "p99_spread_points": float(np.quantile(spread, 0.99) / point),
        "distinct_dates": int(per_day.size),
        "weekend_bars_sat": int((weekday == 5).sum()),
        "weekend_bars_sun": int((weekday == 6).sum()),
        "full_days_288": int((per_day == 288).sum()),
        "thin_days_lt_200": int((per_day < 200).sum()),
        "median_bars_per_date": float(per_day.median()),
        "spread_points_by_year": {
            int(year): {"median": float(row["median"]), "p95": float(row["p95"])}
            for year, row in spread_by_year.iterrows()
        },
    }


def main() -> int:
    report = {"schema_version": "fx_multipair_bar_integrity_v1", "symbols": {}}
    for symbol in sorted(INSTRUMENTS):
        result = check_symbol(symbol)
        report["symbols"][symbol] = result
        print(
            f"{symbol}: {result['m5_bars']:,} bars | dup={result['duplicate_timestamps']} "
            f"nonmono={result['non_monotonic']} negspread={result['negative_spread_bars']} "
            f"inverted={result['inverted_bid_bars'] + result['inverted_ask_bars']} "
            f"contain={result['bid_containment_violations']}"
        )
        print(
            f"    spread pts: median={result['median_spread_points']:.1f} "
            f"p95={result['p95_spread_points']:.1f} p99={result['p99_spread_points']:.1f} | "
            f"dates={result['distinct_dates']} full288={result['full_days_288']} "
            f"thin<200={result['thin_days_lt_200']} sat={result['weekend_bars_sat']}"
        )
        by_year = result["spread_points_by_year"]
        trend = "  ".join(f"{year}:{stat['median']:.1f}" for year, stat in sorted(by_year.items()))
        print(f"    median spread by year -> {trend}")

    out = ROOT / "outputs" / "BAR_INTEGRITY.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {out}")

    problems = [
        f"{symbol}: {key}={value}"
        for symbol, result in report["symbols"].items()
        for key, value in result.items()
        if key
        in (
            "duplicate_timestamps",
            "non_monotonic",
            "negative_spread_bars",
            "inverted_bid_bars",
            "inverted_ask_bars",
            "bid_containment_violations",
        )
        and isinstance(value, int)
        and value > 0
    ]
    print("INTEGRITY: " + ("PASS" if not problems else "ISSUES -> " + "; ".join(problems)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
