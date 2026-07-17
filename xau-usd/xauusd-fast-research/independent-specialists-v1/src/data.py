from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PRICE_COLUMNS = tuple(
    f"{side}_{field}"
    for side in ("bid", "ask", "mid")
    for field in ("open", "high", "low", "close")
)


@dataclass(frozen=True)
class DataBundle:
    bars: dict[str, pd.DataFrame]
    evidence: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_columns(frame: pd.DataFrame, columns: set[str]) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ValueError(f"Feature cache is missing columns: {missing}")


def load_m5(config: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["source"]
    root = Path(os.environ.get(source["storage_environment_variable"], source["default_storage_root"]))
    cache = root / source["feature_cache"]
    manifest_path = root / source["feature_manifest"]
    if not cache.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"Verified feature cache is unavailable below {root}")
    actual_sha = sha256_file(cache)
    if actual_sha != source["feature_sha256"]:
        raise ValueError(f"Feature SHA-256 mismatch: {actual_sha}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(cache)
    _require_columns(frame, {"timestamp_ms", "xau_tick_count", *PRICE_COLUMNS})
    if len(frame) != int(source["expected_rows"]):
        raise ValueError(f"Expected {source['expected_rows']} M5 rows, found {len(frame)}")
    frame = frame.copy()
    frame["bar_start_utc"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    frame["bar_end_utc"] = frame["bar_start_utc"] + pd.Timedelta(minutes=5)
    frame["timestamp_utc"] = frame["bar_end_utc"]
    frame["timeframe"] = "M5"
    frame["tick_count"] = pd.to_numeric(frame["xau_tick_count"], errors="coerce")
    frame = frame.sort_values("bar_start_utc", kind="mergesort").reset_index(drop=True)
    if frame["bar_start_utc"].duplicated().any():
        raise ValueError("Duplicate M5 bar starts detected")
    invalid = (~np.isfinite(frame[list(PRICE_COLUMNS)]) | (frame[list(PRICE_COLUMNS)] <= 0)).any(axis=1)
    if invalid.any():
        raise ValueError(f"Invalid side-specific prices in {int(invalid.sum())} M5 rows")
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    frame = frame.loc[(frame["bar_start_utc"] >= start) & (frame["bar_start_utc"] < end)].reset_index(drop=True)
    evidence = {
        "feature_cache": str(cache),
        "feature_manifest": str(manifest_path),
        "feature_sha256": actual_sha,
        "source_digest": source["source_digest"],
        "manifest": manifest,
        "rows": int(len(frame)),
        "start_utc": frame["bar_start_utc"].min().isoformat(),
        "end_utc": frame["bar_end_utc"].max().isoformat(),
    }
    return frame, evidence


def aggregate_complete_bars(m5: pd.DataFrame, minutes: int, label: str) -> pd.DataFrame:
    if minutes % 5:
        raise ValueError("Aggregate timeframe must be divisible by five minutes")
    expected = minutes // 5
    source = m5.copy()
    source["_bucket"] = source["bar_start_utc"].dt.floor(f"{minutes}min")
    source["_offset"] = ((source["bar_start_utc"] - source["_bucket"]).dt.total_seconds() / 300).astype(int)
    grouped = source.groupby("_bucket", sort=True, observed=True)["_offset"]
    valid = (
        grouped.size().eq(expected)
        & grouped.nunique().eq(expected)
        & grouped.min().eq(0)
        & grouped.max().eq(expected - 1)
        & grouped.sum().eq(expected * (expected - 1) // 2)
    )
    source = source.loc[source["_bucket"].isin(valid.index[valid])]
    aggregations: dict[str, str] = {"tick_count": "sum"}
    for side in ("bid", "ask", "mid"):
        aggregations.update(
            {
                f"{side}_open": "first",
                f"{side}_high": "max",
                f"{side}_low": "min",
                f"{side}_close": "last",
            }
        )
    result = source.groupby("_bucket", sort=True, observed=True).agg(aggregations).reset_index()
    result["bar_start_utc"] = result.pop("_bucket")
    result["bar_end_utc"] = result["bar_start_utc"] + pd.Timedelta(minutes=minutes)
    result["timestamp_utc"] = result["bar_end_utc"]
    result["timeframe"] = label
    result.attrs["incomplete_buckets_dropped"] = int((~valid).sum())
    return result


def load_bundle(config: dict[str, Any]) -> DataBundle:
    m5, evidence = load_m5(config)
    bars = {
        "M5": m5,
        "M15": aggregate_complete_bars(m5, 15, "M15"),
        "M30": aggregate_complete_bars(m5, 30, "M30"),
        "H1": aggregate_complete_bars(m5, 60, "H1"),
        "H4": aggregate_complete_bars(m5, 240, "H4"),
    }
    evidence["timeframes"] = {
        name: {
            "rows": int(len(frame)),
            "start": frame["bar_start_utc"].min().isoformat(),
            "end": frame["bar_end_utc"].max().isoformat(),
            "incomplete_buckets_dropped": int(frame.attrs.get("incomplete_buckets_dropped", 0)),
        }
        for name, frame in bars.items()
    }
    return DataBundle(bars=bars, evidence=evidence)
