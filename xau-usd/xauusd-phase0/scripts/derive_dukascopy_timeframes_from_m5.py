"""Derive Dukascopy M15/H1/H4/D1 processed bars from the continuous M5 series.

Why: the downloaded Dukascopy M15/H1/H4/D1 exports for the extended windows
(2016-2021, 2025-H1) contain dozens of multi-day holes (worst: 10 days in
Sep 2017) and fail the matrix loader's continuity check, while the M5 series
is continuity-clean across 2016-01-01 to 2025-06-30. The campaign brief's data
extension step (D2) specifies deriving higher timeframes from acquired M5.
Deriving all four higher timeframes uniformly from M5 also makes bar
construction identical across eras, which is strictly better for the era
integrity gate than mixing downloaded and derived bars.

The previously downloaded higher-timeframe processed files are quarantined to
data/quarantine/dukascopy_downloaded_tf_2026_06_10/ (not deleted).

Research-data engineering only: no strategy rule, gate, window, or config
changes; no MT5 runtime or broker action.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

PHASE0_ROOT = Path(__file__).resolve().parents[1]
import sys as _sys
SYMBOL = _sys.argv[1] if len(_sys.argv) > 1 else "XAUUSD"
BARS_ROOT = PHASE0_ROOT / "data" / "processed" / "bars" / "dukascopy" / SYMBOL
QUARANTINE_ROOT = PHASE0_ROOT / "data" / "quarantine" / "dukascopy_downloaded_tf_2026_06_10"

TIMEFRAMES = {
    "M15": pd.Timedelta(minutes=15),
    "H1": pd.Timedelta(hours=1),
    "H4": pd.Timedelta(hours=4),
    "D1": pd.Timedelta(days=1),
}

COLUMNS = (
    "timestamp_utc,bar_start_utc,bar_end_utc,broker,symbol,timeframe,open,high,low,close,"
    "mid_open,mid_high,mid_low,mid_close,bid_open,bid_high,bid_low,bid_close,"
    "ask_open,ask_high,ask_low,ask_close,spread_open_points,spread_close_points,"
    "spread_median_points,spread_p95_points,tick_count,volume_sum"
).split(",")


def load_m5() -> pd.DataFrame:
    files = sorted((BARS_ROOT / "M5").glob("*.csv"))
    if not files:
        raise RuntimeError("No processed Dukascopy M5 files found.")
    frames = [pd.read_csv(path) for path in files]
    m5 = pd.concat(frames, ignore_index=True)
    m5["bar_start_utc"] = pd.to_datetime(m5["bar_start_utc"], utc=True)
    m5 = m5.drop_duplicates(subset="bar_start_utc").sort_values("bar_start_utc").reset_index(drop=True)
    return m5


def derive(m5: pd.DataFrame, timeframe: str, duration: pd.Timedelta) -> pd.DataFrame:
    grouper = m5["bar_start_utc"].dt.floor(duration)
    grouped = m5.groupby(grouper)
    out = grouped.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        mid_open=("mid_open", "first"),
        mid_high=("mid_high", "max"),
        mid_low=("mid_low", "min"),
        mid_close=("mid_close", "last"),
        spread_median_points=("spread_median_points", "median"),
        spread_p95_points=("spread_p95_points", "max"),
        tick_count=("tick_count", "sum"),
        volume_sum=("volume_sum", "sum"),
    ).reset_index()
    out = out.rename(columns={"bar_start_utc": "bar_start"})
    out["bar_start_utc"] = out["bar_start"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    bar_end = out["bar_start"] + duration
    out["bar_end_utc"] = bar_end.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out["timestamp_utc"] = out["bar_end_utc"]
    out["broker"] = "dukascopy"
    out["symbol"] = SYMBOL
    out["timeframe"] = timeframe
    for column in (
        "bid_open", "bid_high", "bid_low", "bid_close",
        "ask_open", "ask_high", "ask_low", "ask_close",
        "spread_open_points", "spread_close_points",
    ):
        out[column] = pd.NA
    return out[COLUMNS]


def main() -> int:
    m5 = load_m5()
    start_token = m5["bar_start_utc"].iloc[0].strftime("%Y%m%d")
    end_token = (m5["bar_start_utc"].iloc[-1] + pd.Timedelta(minutes=5)).strftime("%Y%m%d")
    print(f"M5 source: {len(m5)} bars, {m5['bar_start_utc'].iloc[0]} to {m5['bar_start_utc'].iloc[-1]}")

    for timeframe, duration in TIMEFRAMES.items():
        tf_dir = BARS_ROOT / timeframe
        tf_dir.mkdir(parents=True, exist_ok=True)
        quarantine_dir = QUARANTINE_ROOT / timeframe
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        moved = 0
        for path in sorted(tf_dir.glob("*.csv")):
            shutil.move(str(path), str(quarantine_dir / path.name))
            moved += 1
        derived = derive(m5, timeframe, duration)
        out_path = tf_dir / f"{SYMBOL}_dukascopy_{timeframe}_{start_token}_{end_token}_derived_from_m5.csv"
        derived.to_csv(out_path, index=False)
        print(f"{timeframe}: quarantined {moved} downloaded file(s); wrote {len(derived)} derived bars -> {out_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
