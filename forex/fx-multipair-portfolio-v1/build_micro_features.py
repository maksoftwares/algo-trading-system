"""Extract per-M5-bar tick microstructure features from the Dukascopy archive.

Motivation: every test in R1-R6 read OHLC bars only, and this repo's own record
for gold is that "tick-microstructure features carry most of the edge"
(PF 1.89 -> 1.10 without them). The archive turns out to carry real top-of-book
depth (bidVolumes/askVolumes are populated quoted sizes, not synthetic), so this
is a genuinely different information source rather than another bar geometry.

Features per M5 bar, all computed from ticks inside that bar only:

* ``depth_imbalance``  mean (bidVol - askVol) / (bidVol + askVol). Classic
  order-book imbalance.
* ``micro_dev_points`` mean deviation of the microprice from the mid, in points.
  Microprice = (bid*askVol + ask*bidVol) / (bidVol + askVol): heavier bid depth
  pulls it toward the ask. The standard short-horizon predictor.
* ``quote_asym``       (ask-only quote moves - bid-only moves) / moves. Dealers
  move the side under pressure first.
* ``signed_flow``      mean sign of mid changes.
* ``rv_points``        sum |mid change|, in points (realised activity).
* ``spread_mean_points`` / ``spread_max_points``
* ``tick_count`` / ``depth_total`` mean (bidVol + askVol).

Written alongside the M5 bar cache so the census can join on ``timestamp_ms``.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import INSTRUMENTS, M5_MS, iso, raw_month_dir, sha256_file  # noqa: E402

DEFAULT_STORAGE = Path(r"D:\AlgoTradingData\C_DRIVE\DukascopyTickDataFoundationV1")
DEFAULT_CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
START = (2016, 7)
END = (2026, 6)

FEATURE_COLUMNS = (
    "timestamp_ms",
    "depth_imbalance",
    "micro_dev_points",
    "quote_asym",
    "signed_flow",
    "rv_points",
    "spread_mean_points",
    "spread_max_points",
    "tick_count",
    "depth_total",
)


def month_range(start, end):
    months, (year, month) = [], start
    while (year, month) <= end:
        months.append((year, month))
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return months


def _hour_features(raw: bytes, point: float) -> dict[str, np.ndarray] | None:
    payload = json.loads(raw)
    times = payload["times"]
    if not times or len(times) < 2:
        return None
    base_ts = int(payload["timestamp"])
    multiplier = float(payload["multiplier"])
    ts = base_ts + np.cumsum(np.asarray(times, dtype=np.int64))
    bid = float(payload["bid"]) + np.cumsum(np.asarray(payload["bids"], dtype=np.float64)) * multiplier
    ask = float(payload["ask"]) + np.cumsum(np.asarray(payload["asks"], dtype=np.float64)) * multiplier
    bid_volume = np.asarray(payload["bidVolumes"], dtype=np.float64)
    ask_volume = np.asarray(payload["askVolumes"], dtype=np.float64)

    depth = bid_volume + ask_volume
    safe_depth = np.where(depth > 0, depth, np.nan)
    imbalance = (bid_volume - ask_volume) / safe_depth
    mid = (bid + ask) / 2.0
    microprice = (bid * ask_volume + ask * bid_volume) / safe_depth
    micro_dev = (microprice - mid) / point
    spread = (ask - bid) / point

    delta_mid = np.diff(mid, prepend=mid[0])
    delta_mid[0] = 0.0
    delta_bid = np.diff(bid, prepend=bid[0])
    delta_ask = np.diff(ask, prepend=ask[0])
    ask_only = ((delta_ask != 0) & (delta_bid == 0)).astype(np.float64)
    bid_only = ((delta_bid != 0) & (delta_ask == 0)).astype(np.float64)

    slots = ts - (ts % M5_MS)
    starts = np.flatnonzero(np.r_[True, slots[1:] != slots[:-1]])

    def mean_by(values: np.ndarray) -> np.ndarray:
        totals = np.add.reduceat(np.nan_to_num(values, nan=0.0), starts)
        counts = np.add.reduceat(np.isfinite(values).astype(np.float64), starts)
        return totals / np.where(counts > 0, counts, np.nan)

    def sum_by(values: np.ndarray) -> np.ndarray:
        return np.add.reduceat(values, starts)

    counts = sum_by(np.ones(ts.size))
    moves = sum_by(ask_only + bid_only)
    return {
        "timestamp_ms": slots[starts].astype(np.int64),
        "depth_imbalance": mean_by(imbalance),
        "micro_dev_points": mean_by(micro_dev),
        "quote_asym": (sum_by(ask_only) - sum_by(bid_only)) / np.where(moves > 0, moves, np.nan),
        "signed_flow": sum_by(np.sign(delta_mid)) / counts,
        "rv_points": sum_by(np.abs(delta_mid)) / point,
        "spread_mean_points": mean_by(spread),
        "spread_max_points": np.maximum.reduceat(spread, starts),
        "tick_count": counts,
        "depth_total": mean_by(depth),
    }


def _worker(args) -> tuple[str, bytes, int]:
    storage, symbol, year, month = args
    point = float(INSTRUMENTS[symbol]["point_size"])
    directory = raw_month_dir(Path(storage), symbol, year, month)
    chunks = []
    for path in sorted(directory.glob("*.json")):
        if path.name.startswith("_"):
            continue
        features = _hour_features(path.read_bytes(), point)
        if features is not None:
            chunks.append(features)
    if not chunks:
        frame = pd.DataFrame({name: np.empty(0) for name in FEATURE_COLUMNS})
        frame["timestamp_ms"] = frame["timestamp_ms"].astype(np.int64)
    else:
        frame = pd.DataFrame(
            {name: np.concatenate([chunk[name] for chunk in chunks]) for name in FEATURE_COLUMNS}
        )
    return symbol, frame.to_parquet(index=False), len(frame)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build M5 microstructure features")
    parser.add_argument("--storage", default=str(DEFAULT_STORAGE))
    parser.add_argument("--cache", default=str(DEFAULT_CACHE))
    parser.add_argument("--symbols", nargs="*", default=sorted(INSTRUMENTS))
    parser.add_argument("--workers", type=int, default=min(14, os.cpu_count() or 4))
    args = parser.parse_args()

    cache = Path(args.cache)
    (cache / "micro").mkdir(parents=True, exist_ok=True)
    months = month_range(START, END)
    jobs = [(args.storage, symbol, y, m) for symbol in args.symbols for (y, m) in months]
    print(f"extracting microstructure for {len(jobs)} symbol-months, {args.workers} workers", flush=True)

    collected: dict[str, list[pd.DataFrame]] = {s: [] for s in args.symbols}
    began, done = time.time(), 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(_worker, job) for job in jobs]
        for future in as_completed(futures):
            symbol, blob, _ = future.result()
            collected[symbol].append(pd.read_parquet(io.BytesIO(blob)))
            done += 1
            if done % 60 == 0 or done == len(jobs):
                rate = done / max(time.time() - began, 1e-9)
                print(f"  {done}/{len(jobs)} ({rate:.1f}/s, {(len(jobs)-done)/max(rate,1e-9):.0f}s left)", flush=True)

    manifest = {"schema_version": "fx_micro_features_v1", "columns": list(FEATURE_COLUMNS), "symbols": {}}
    for symbol in args.symbols:
        frame = (
            pd.concat(collected[symbol], ignore_index=True)
            .drop_duplicates("timestamp_ms", keep="last")
            .sort_values("timestamp_ms", kind="stable", ignore_index=True)
        )
        path = cache / "micro" / f"{symbol}_M5_MICRO.parquet"
        frame.to_parquet(path, index=False, compression="zstd")
        manifest["symbols"][symbol] = {
            "rows": int(len(frame)),
            "first_utc": iso(int(frame["timestamp_ms"].iloc[0])),
            "last_utc": iso(int(frame["timestamp_ms"].iloc[-1])),
            "median_depth_total": float(frame["depth_total"].median()),
            "median_abs_micro_dev_points": float(frame["micro_dev_points"].abs().median()),
            "path": str(path),
            "sha256": sha256_file(path),
        }
        print(
            f"{symbol}: {len(frame):,} rows  median depth {frame['depth_total'].median():,.0f}  "
            f"median |micro_dev| {frame['micro_dev_points'].abs().median():.2f} pts"
        )
    (cache / "micro" / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nelapsed {time.time() - began:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
