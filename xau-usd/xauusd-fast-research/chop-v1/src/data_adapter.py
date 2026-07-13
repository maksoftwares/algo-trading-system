from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PRICE_COLUMNS = (
    "mid_open", "mid_high", "mid_low", "mid_close",
    "bid_open", "bid_high", "bid_low", "bid_close",
    "ask_open", "ask_high", "ask_low", "ask_close",
)
SPREAD_COLUMNS = ("spread_open_points", "spread_close_points", "spread_median_points", "spread_p95_points")


@dataclass(frozen=True)
class DataBundle:
    bars: dict[str, pd.DataFrame]
    coverage: dict[str, Any]


def _single_csv(directory: Path) -> Path:
    paths = sorted(directory.glob("*.csv"))
    if len(paths) != 1:
        raise FileNotFoundError(f"Expected one processed-bar CSV in {directory}, found {len(paths)}")
    return paths[0]


def load_native_bars(source_root: Path, timeframe: str) -> pd.DataFrame:
    path = _single_csv(source_root / timeframe)
    usecols = [
        "timestamp_utc", "bar_start_utc", "bar_end_utc", "broker", "symbol", "timeframe",
        *PRICE_COLUMNS, *SPREAD_COLUMNS, "tick_count", "volume_sum",
    ]
    frame = pd.read_csv(path, usecols=usecols, low_memory=False)
    for column in ("timestamp_utc", "bar_start_utc", "bar_end_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    for column in (*PRICE_COLUMNS, *SPREAD_COLUMNS, "tick_count", "volume_sum"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    frame.attrs["source_path"] = str(path)
    frame.attrs["native"] = True
    return frame


def aggregate_m30(m5: pd.DataFrame) -> pd.DataFrame:
    source = m5.copy()
    bucket = source["bar_start_utc"].dt.floor("30min")
    source = source.assign(_bucket=bucket)
    aggregations: dict[str, str] = {
        "mid_open": "first", "mid_high": "max", "mid_low": "min", "mid_close": "last",
        "bid_open": "first", "bid_high": "max", "bid_low": "min", "bid_close": "last",
        "ask_open": "first", "ask_high": "max", "ask_low": "min", "ask_close": "last",
        "spread_open_points": "first", "spread_close_points": "last",
        "spread_median_points": "median", "spread_p95_points": "max",
        "tick_count": "sum", "volume_sum": "sum",
    }
    result = source.groupby("_bucket", sort=True, observed=True).agg(aggregations).reset_index()
    counts = source.groupby("_bucket", sort=True, observed=True).size().to_numpy()
    result = result.loc[counts == 6].reset_index(drop=True)
    result["bar_start_utc"] = result.pop("_bucket")
    result["bar_end_utc"] = result["bar_start_utc"] + pd.Timedelta(minutes=30)
    result["timestamp_utc"] = result["bar_end_utc"]
    result["broker"] = "capital_com"
    result["symbol"] = "XAUUSD"
    result["timeframe"] = "M30"
    result.attrs["source_path"] = str(m5.attrs.get("source_path", "M5"))
    result.attrs["native"] = False
    return result


def _quality(frame: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    timestamps = frame["timestamp_utc"]
    invalid_prices = int((~np.isfinite(frame[list(PRICE_COLUMNS)]) | (frame[list(PRICE_COLUMNS)] <= 0)).any(axis=1).sum())
    expected = pd.Timedelta(minutes={"M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240}[timeframe])
    gaps = timestamps.diff().dropna()
    # Weekend/market closures remain visible but are not fabricated or filled.
    return {
        "rows": int(len(frame)),
        "start": timestamps.min().isoformat(),
        "end": timestamps.max().isoformat(),
        "duplicate_timestamps": int(timestamps.duplicated().sum()),
        "invalid_prices": invalid_prices,
        "gaps_over_3_bars": int((gaps > expected * 3).sum()),
        "maximum_gap_hours": float(gaps.max().total_seconds() / 3600.0) if len(gaps) else 0.0,
        "native": bool(frame.attrs.get("native")),
        "source": frame.attrs.get("source_path", ""),
    }


def load_bundle(repo_root: Path, config: dict[str, Any]) -> DataBundle:
    source_root = repo_root / config["source_root"]
    native = {tf: load_native_bars(source_root, tf) for tf in ("M5", "M15", "H1", "H4")}
    native["M30"] = aggregate_m30(native["M5"])
    requested_start = pd.Timestamp(config["requested_start"])
    requested_end = pd.Timestamp(config["requested_end"])
    actual_start = max(frame["timestamp_utc"].min() for frame in native.values())
    actual_end = min(frame["timestamp_utc"].max() for frame in native.values())
    actual_start = max(actual_start, requested_start)
    actual_end = min(actual_end, requested_end)
    bars = {
        tf: frame.loc[(frame["timestamp_utc"] >= actual_start) & (frame["timestamp_utc"] <= actual_end)].reset_index(drop=True)
        for tf, frame in native.items()
    }
    for tf, frame in bars.items():
        frame.attrs.update(native[tf].attrs)
    years = (actual_end - actual_start).total_seconds() / (365.2425 * 86400)
    coverage = {
        "requested_start": requested_start.isoformat(),
        "requested_end": requested_end.isoformat(),
        "actual_start": actual_start.isoformat(),
        "actual_end": actual_end.isoformat(),
        "common_years": years,
        "status": "DATA_COVERAGE_LIMITED" if years < 8.0 else "DATA_COVERAGE_PARTIAL_REQUESTED_TAIL_MISSING",
        "missing_intervals": ([{"start": actual_end.isoformat(), "end": requested_end.isoformat()}] if actual_end < requested_end else []),
        "timeframes": {tf: _quality(frame, tf) for tf, frame in bars.items()},
        "timestamp_basis": "UTC fields from Capital.com processed broker bars; treated consistently as broker-source timestamps",
    }
    return DataBundle(bars=bars, coverage=coverage)
