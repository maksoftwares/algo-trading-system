from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd

from src.snapshot import parse_utc


BAR_MS = 5 * 60 * 1000
SIDES = ("bid", "ask", "mid")


def aggregate_ticks(ticks: list[Any], symbol: str) -> pd.DataFrame:
    prefix = symbol.lower()
    columns = ["timestamp_ms"] + [
        f"{prefix}_{side}_{field}"
        for side in SIDES
        for field in ("open", "high", "low", "close", "volume", "tick_count")
    ]
    if not ticks:
        return pd.DataFrame(columns=columns)
    times = np.fromiter((tick.timestamp_ms for tick in ticks), dtype=np.int64)
    bids = np.fromiter((tick.bid for tick in ticks), dtype=float)
    asks = np.fromiter((tick.ask for tick in ticks), dtype=float)
    bid_volume = np.fromiter((tick.bid_volume for tick in ticks), dtype=float)
    ask_volume = np.fromiter((tick.ask_volume for tick in ticks), dtype=float)
    order = np.argsort(times, kind="stable")
    times = times[order]
    bids = bids[order]
    asks = asks[order]
    bid_volume = bid_volume[order]
    ask_volume = ask_volume[order]
    buckets = times - times % BAR_MS
    starts = np.r_[0, np.flatnonzero(np.diff(buckets)) + 1]
    counts = np.diff(np.r_[starts, len(buckets)])
    ends = starts + counts - 1
    values = {
        "bid": (bids, bid_volume),
        "ask": (asks, ask_volume),
        "mid": ((bids + asks) / 2.0, (bid_volume + ask_volume) / 2.0),
    }
    result: dict[str, Any] = {"timestamp_ms": buckets[starts]}
    for side, (price, volume) in values.items():
        base = f"{prefix}_{side}"
        result[f"{base}_open"] = price[starts]
        result[f"{base}_high"] = np.maximum.reduceat(price, starts)
        result[f"{base}_low"] = np.minimum.reduceat(price, starts)
        result[f"{base}_close"] = price[ends]
        result[f"{base}_volume"] = np.add.reduceat(volume, starts)
        result[f"{base}_tick_count"] = counts.astype(float)
    return pd.DataFrame(result)[columns]


def load_symbol_hours(
    foundation: ModuleType,
    storage_root: Path,
    symbol: str,
    rows: list[dict[str, Any]],
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for row in rows:
        hour = parse_utc(row["hour_utc"])
        path = (storage_root / row["path"]).resolve()
        ticks = foundation.decode_payload(
            path.read_bytes(), symbol, row["source_file_id"]
        )
        if ticks:
            first = datetime.fromtimestamp(ticks[0].timestamp_ms / 1000, UTC)
            last = datetime.fromtimestamp(ticks[-1].timestamp_ms / 1000, UTC)
            if first < hour or last >= hour + timedelta(hours=1):
                raise ValueError(f"tick escaped source hour: {symbol}/{hour}")
        part = aggregate_ticks(ticks, symbol)
        if not part.empty:
            parts.append(part)
    if not parts:
        return aggregate_ticks([], symbol)
    result = pd.concat(parts, ignore_index=True).sort_values(
        "timestamp_ms", kind="mergesort"
    )
    if result["timestamp_ms"].duplicated().any():
        raise ValueError(f"duplicate M5 buckets for {symbol}")
    return result.reset_index(drop=True)


def combine_symbols(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    timestamps = sorted(
        set().union(*(frame["timestamp_ms"].tolist() for frame in frames.values()))
    )
    result = pd.DataFrame({"timestamp_ms": timestamps})
    for symbol, frame in frames.items():
        result = result.merge(
            frame, on="timestamp_ms", how="left", validate="one_to_one"
        )
        result[f"{symbol.lower()}_available"] = result[
            f"{symbol.lower()}_mid_close"
        ].notna()
    result.insert(
        0,
        "timestamp_utc",
        pd.to_datetime(result["timestamp_ms"], unit="ms", utc=True),
    )
    ordered = ["timestamp_utc", "timestamp_ms"]
    for symbol in frames:
        prefix = symbol.lower()
        ordered.extend(
            f"{prefix}_{side}_{field}"
            for side in SIDES
            for field in ("open", "high", "low", "close", "volume", "tick_count")
        )
    ordered.extend(f"{symbol.lower()}_available" for symbol in frames)
    return result[ordered]


def parity_against_frozen(
    rebuilt: pd.DataFrame, frozen: pd.DataFrame, tolerance: float = 1e-10
) -> dict[str, Any]:
    timestamps = rebuilt["timestamp_ms"]
    expected = frozen.loc[frozen["timestamp_ms"].isin(timestamps)].sort_values(
        "timestamp_ms", kind="mergesort"
    )
    actual = rebuilt.sort_values("timestamp_ms", kind="mergesort")
    if len(actual) != len(expected) or not np.array_equal(
        actual["timestamp_ms"].to_numpy(), expected["timestamp_ms"].to_numpy()
    ):
        raise ValueError("macro historical parity timestamp mismatch")
    maximum = 0.0
    for column in actual.columns:
        if column == "timestamp_utc":
            continue
        if column.endswith("_available"):
            if not np.array_equal(
                actual[column].to_numpy(), expected[column].to_numpy()
            ):
                raise ValueError(f"macro availability parity mismatch: {column}")
            continue
        if column == "timestamp_ms":
            continue
        left = actual[column].to_numpy(dtype=float)
        right = expected[column].to_numpy(dtype=float)
        if not np.array_equal(np.isnan(left), np.isnan(right)):
            raise ValueError(f"macro missing-value parity mismatch: {column}")
        finite = np.isfinite(left)
        error = (
            float(np.max(np.abs(left[finite] - right[finite]))) if finite.any() else 0.0
        )
        maximum = max(maximum, error)
        if error > tolerance:
            raise ValueError(f"macro historical parity mismatch {column}: {error}")
    return {"rows": len(actual), "maximum_absolute_error": maximum}
