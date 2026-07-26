"""Acquire daily FX rates for the tradeable major universe from FRED.

Why this source. The Dukascopy archive on disk holds only three USD majors, and
`REJECTIONS.md` R1 plus the intraday and swing censuses show no price-only edge
there at retail cost. Cross-sectional FX work needs a real universe and a long
history; FRED supplies seven majors from 1999 for free, which is ~27 years
against the 5.5 the design window had.

Limitations recorded deliberately: FRED daily values are noon-New-York buying
rates, not tradeable bid/ask, and there is no intraday path. They are used to
establish *whether* a cross-sectional premium exists. Execution realism for any
surviving signal must come from the Dukascopy M5 bid/ask cache (for the three
pairs it covers) or from broker data before promotion.
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

# series -> (pair, invert) where invert=True means the series quotes the pair
# upside down relative to market convention.
SERIES = {
    "DEXUSEU": ("EURUSD", False),  # USD per EUR
    "DEXUSUK": ("GBPUSD", False),  # USD per GBP
    "DEXUSAL": ("AUDUSD", False),  # USD per AUD
    "DEXUSNZ": ("NZDUSD", False),  # USD per NZD
    "DEXJPUS": ("USDJPY", False),  # JPY per USD
    "DEXCAUS": ("USDCAD", False),  # CAD per USD
    "DEXSZUS": ("USDCHF", False),  # CHF per USD
}
TIMEOUT = 60


def fetch(series: str) -> pd.Series:
    url = FRED_CSV.format(series=series)
    request = urllib.request.Request(url, headers={"User-Agent": "fx-multipair-research/1.0"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        raw = response.read()
    frame = pd.read_csv(io.BytesIO(raw))
    date_column, value_column = frame.columns[0], frame.columns[1]
    frame[value_column] = pd.to_numeric(frame[value_column], errors="coerce")
    out = pd.Series(
        frame[value_column].to_numpy(),
        index=pd.to_datetime(frame[date_column]),
        name=series,
    ).dropna()
    return out


def main() -> int:
    (CACHE / "fred").mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.Series] = {}
    manifest: dict[str, object] = {
        "schema_version": "fx_fred_daily_v1",
        "source": "https://fred.stlouisfed.org/graph/fredgraph.csv",
        "convention_note": "noon New York buying rates; not tradeable bid/ask",
        "series": {},
    }

    for series, (pair, invert) in SERIES.items():
        values = fetch(series)
        if invert:
            values = 1.0 / values
        frames[pair] = values
        manifest["series"][series] = {
            "pair": pair,
            "observations": int(values.size),
            "first": str(values.index[0].date()),
            "last": str(values.index[-1].date()),
        }
        print(
            f"{series:9s} -> {pair:7s} {values.size:6d} obs  "
            f"{values.index[0].date()} .. {values.index[-1].date()}"
        )

    panel = pd.DataFrame(frames).sort_index()
    # Keep only rows where every pair quoted, so cross-sectional ranks are fair.
    complete = panel.dropna()
    path = CACHE / "fred" / "FX_DAILY_MAJORS.parquet"
    complete.to_parquet(path)
    manifest["panel"] = {
        "rows_any": int(len(panel)),
        "rows_complete": int(len(complete)),
        "first_complete": str(complete.index[0].date()),
        "last_complete": str(complete.index[-1].date()),
        "pairs": list(complete.columns),
        "path": str(path),
    }
    (CACHE / "fred" / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        f"\npanel: {len(complete):,} complete daily rows "
        f"{complete.index[0].date()} .. {complete.index[-1].date()}  "
        f"({len(complete.columns)} pairs)"
    )
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
