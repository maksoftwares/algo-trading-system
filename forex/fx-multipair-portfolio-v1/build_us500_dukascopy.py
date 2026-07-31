"""Build US500 M5 bid/ask bars from the Dukascopy index archive.

Same decoder as the FX foundation, with two differences: the index files are
gzipped (`.json.gz`), and the archive lives under DukascopyIndexFoundationV1.

Only complete years are built. The point of this data is the stressed-spread
question the broker's 14 calm months cannot answer, so a half-downloaded year
would be worse than none.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import BAR_COLUMNS, aggregate_m5, decode_hour, iso, sha256_file  # noqa: E402

STORAGE = Path(r"D:\AlgoTradingData\C_DRIVE\DukascopyIndexFoundationV1\raw\US500")
CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
PRICE_SCALE = 3          # USA500.IDX-USD priceScale from the instrument metadata
HOURS_PER_YEAR = 8760


def complete_years(minimum: float = 0.98) -> list[int]:
    found = []
    for directory in sorted(STORAGE.glob("year=*")):
        year = int(directory.name.split("=")[1])
        count = sum(1 for _ in directory.rglob("*.json.gz"))
        expected = HOURS_PER_YEAR + (24 if year % 4 == 0 else 0)
        if count >= expected * minimum:
            found.append(year)
        else:
            print(f"  skipping {year}: {count}/{expected} hours ({count / expected:.0%})")
    return found


def build_year(year: int) -> pd.DataFrame:
    chunks = []
    for path in sorted((STORAGE / f"year={year:04d}").rglob("*.json.gz")):
        try:
            raw = gzip.decompress(path.read_bytes())
        except Exception:
            continue
        try:
            bars = aggregate_m5(decode_hour(raw, PRICE_SCALE))
        except Exception:
            continue
        if bars is not None:
            chunks.append(bars)
    if not chunks:
        return pd.DataFrame({name: np.empty(0) for name in BAR_COLUMNS})
    return pd.DataFrame(
        {name: np.concatenate([chunk[name] for chunk in chunks]) for name in BAR_COLUMNS}
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build US500 M5 bars from Dukascopy")
    parser.add_argument("--years", nargs="*", type=int, default=None)
    args = parser.parse_args()

    print("checking year completeness...")
    years = args.years or complete_years()
    if not years:
        print("no complete years available yet")
        return 1
    print(f"building: {years}\n")

    frames = []
    for year in years:
        frame = build_year(year)
        if frame.empty:
            print(f"  {year}: no bars")
            continue
        frames.append(frame)
        stamps = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
        spread = (frame["ask_close"] - frame["bid_close"]).to_numpy() / 0.1
        print(
            f"  {year}: {len(frame):>7,} M5 bars  {stamps.min().date()} .. {stamps.max().date()}  "
            f"spread median {np.median(spread):.0f} pts  p95 {np.quantile(spread, 0.95):.0f}  "
            f"p99 {np.quantile(spread, 0.99):.0f}"
        )

    bars = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates("timestamp_ms", keep="last")
        .sort_values("timestamp_ms", kind="stable", ignore_index=True)
    )
    (CACHE / "bars").mkdir(parents=True, exist_ok=True)
    path = CACHE / "bars" / "US500_M5_BIDASK_DUKASCOPY.parquet"
    bars.to_parquet(path, index=False, compression="zstd")

    spread = (bars["ask_close"] - bars["bid_close"]).to_numpy() / 0.1
    manifest = {
        "schema_version": "us500_dukascopy_m5_v1",
        "source": "Dukascopy USA500.IDX-USD hourly tick files",
        "years": years,
        "m5_bars": int(len(bars)),
        "first_bar_utc": iso(int(bars["timestamp_ms"].iloc[0])),
        "last_bar_utc": iso(int(bars["timestamp_ms"].iloc[-1])),
        "spread_points_median": float(np.median(spread)),
        "spread_points_p95": float(np.quantile(spread, 0.95)),
        "spread_points_p99": float(np.quantile(spread, 0.99)),
        "negative_spread_bars": int((spread < 0).sum()),
        "path": str(path),
        "sha256": sha256_file(path),
    }
    (CACHE / "bars" / "US500_DUKASCOPY_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"\ntotal {len(bars):,} M5 bars -> {path}")
    print(
        f"spread points: median {manifest['spread_points_median']:.0f}  "
        f"p95 {manifest['spread_points_p95']:.0f}  p99 {manifest['spread_points_p99']:.0f}  "
        f"negative {manifest['negative_spread_bars']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
