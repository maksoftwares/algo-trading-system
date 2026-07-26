"""Build the multi-pair M5 bid/ask bar cache from the Dukascopy tick archive.

Usage:
    python build_bars.py                       # all symbols, full window
    python build_bars.py --symbols EURUSD      # one symbol
    python build_bars.py --months 2024-01 2024-02
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import (  # noqa: E402
    BAR_COLUMNS,
    INSTRUMENTS,
    build_month_m5,
    cache_path,
    iso,
    sha256_file,
)

DEFAULT_STORAGE = Path(r"D:\AlgoTradingData\C_DRIVE\DukascopyTickDataFoundationV1")
DEFAULT_CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
START = (2016, 7)
END = (2026, 6)  # inclusive


def month_range(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    months: list[tuple[int, int]] = []
    year, month = start
    while (year, month) <= end:
        months.append((year, month))
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return months


def _worker(args: tuple[str, str, int, int]) -> tuple[str, int, int, bytes, int, int]:
    storage, symbol, year, month = args
    frame = build_month_m5(Path(storage), symbol, year, month)
    hour_files = int(frame.attrs.get("hour_files", 0))
    return symbol, year, month, frame.to_parquet(index=False), len(frame), hour_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FX M5 bid/ask bar cache")
    parser.add_argument("--storage", default=str(DEFAULT_STORAGE))
    parser.add_argument("--cache", default=str(DEFAULT_CACHE))
    parser.add_argument("--symbols", nargs="*", default=sorted(INSTRUMENTS))
    parser.add_argument("--months", nargs="*", default=None, help="YYYY-MM values")
    parser.add_argument("--workers", type=int, default=min(16, (os.cpu_count() or 4)))
    args = parser.parse_args()

    storage = Path(args.storage)
    cache = Path(args.cache)
    (cache / "bars").mkdir(parents=True, exist_ok=True)

    if args.months:
        months = [tuple(int(part) for part in value.split("-")) for value in args.months]
    else:
        months = month_range(START, END)

    jobs = [(str(storage), symbol, year, month) for symbol in args.symbols for (year, month) in months]
    print(f"decoding {len(jobs)} symbol-months with {args.workers} workers", flush=True)

    collected: dict[str, list[pd.DataFrame]] = {symbol: [] for symbol in args.symbols}
    hour_file_counts: dict[str, int] = {symbol: 0 for symbol in args.symbols}
    started = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_worker, job): job for job in jobs}
        for future in as_completed(futures):
            symbol, year, month, blob, rows, hour_files = future.result()
            collected[symbol].append(pd.read_parquet(__import__("io").BytesIO(blob)))
            hour_file_counts[symbol] += hour_files
            done += 1
            if done % 30 == 0 or done == len(jobs):
                rate = done / max(time.time() - started, 1e-9)
                print(
                    f"  {done}/{len(jobs)} months  ({rate:.1f}/s, "
                    f"{(len(jobs) - done) / max(rate, 1e-9):.0f}s left)",
                    flush=True,
                )

    manifest: dict[str, object] = {
        "schema_version": "fx_multipair_m5_bidask_v1",
        "built_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "storage_root": str(storage),
        "window": {"start": f"{START[0]}-{START[1]:02d}", "end": f"{END[0]}-{END[1]:02d}"},
        "columns": list(BAR_COLUMNS),
        "symbols": {},
    }

    for symbol in args.symbols:
        frame = (
            pd.concat(collected[symbol], ignore_index=True)
            .drop_duplicates("timestamp_ms", keep="last")
            .sort_values("timestamp_ms", kind="stable", ignore_index=True)
        )
        path = cache_path(cache, symbol)
        frame.to_parquet(path, index=False, compression="zstd")
        spread = (frame["ask_close"] - frame["bid_close"]).to_numpy()
        manifest["symbols"][symbol] = {
            "m5_bars": int(len(frame)),
            "raw_hour_files": hour_file_counts[symbol],
            "first_bar_utc": iso(int(frame["timestamp_ms"].iloc[0])),
            "last_bar_utc": iso(int(frame["timestamp_ms"].iloc[-1])),
            "median_spread_price": float(pd.Series(spread).median()),
            "median_spread_points": float(
                pd.Series(spread).median() / float(INSTRUMENTS[symbol]["point_size"])
            ),
            "negative_spread_bars": int((spread < 0).sum()),
            "path": str(path),
            "sha256": sha256_file(path),
        }
        print(
            f"{symbol}: {len(frame):,} M5 bars  "
            f"{manifest['symbols'][symbol]['first_bar_utc']} .. "
            f"{manifest['symbols'][symbol]['last_bar_utc']}  "
            f"median spread {manifest['symbols'][symbol]['median_spread_points']:.1f} pts",
            flush=True,
        )

    manifest_path = cache / "bars" / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nmanifest: {manifest_path}")
    print(f"elapsed: {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
