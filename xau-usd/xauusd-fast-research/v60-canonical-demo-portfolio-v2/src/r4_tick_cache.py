from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd


CACHE_SCHEMA = "xauusd_v60_r4_per_file_tick_cache_v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _cache_key(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:24]


def _config_sha256(config: dict[str, Any]) -> str:
    encoded = json.dumps(
        config,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _identity(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.resolve()).replace("\\", "/"),
        "bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_parquet(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp.parquet", dir=path.parent)
    os.close(fd)
    try:
        frame.to_parquet(temporary, index=False)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_or_refresh(
    path: Path,
    config: dict[str, Any],
    cache_directory: Path,
    original_loader: Callable[..., tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]],
) -> tuple[pd.DataFrame, dict[str, Any], bool]:
    key = _cache_key(path)
    parquet_path = cache_directory / f"{key}.parquet"
    metadata_path = cache_directory / f"{key}.json"
    identity = _identity(path)
    config_sha256 = _config_sha256(config)
    if parquet_path.is_file() and metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata.get("schema_version") == CACHE_SCHEMA
            and metadata.get("source_identity") == identity
            and metadata.get("loader_config_sha256") == config_sha256
            and metadata.get("parquet_sha256") == sha256_file(parquet_path)
        ):
            return pd.read_parquet(parquet_path), metadata, True

    frame, audit, daily = original_loader([path], config)
    _atomic_parquet(parquet_path, frame)
    metadata = {
        "schema_version": CACHE_SCHEMA,
        "source_identity": identity,
        "loader_config_sha256": config_sha256,
        "parquet_sha256": sha256_file(parquet_path),
        "source_files": audit.get("source_files", []),
        "raw_rows": int(audit.get("raw_rows", len(frame))),
        "daily_source_quality": daily.to_dict(orient="records"),
    }
    _atomic_json(metadata_path, metadata)
    return frame, metadata, False


def load_ticks_cached(
    paths: Iterable[Path],
    config: dict[str, Any],
    *,
    cache_directory: Path,
    original_loader: Callable[..., tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]],
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    ordered_paths = sorted(Path(value) for value in paths)
    frames: list[pd.DataFrame] = []
    metadata_rows: list[dict[str, Any]] = []
    cache_hits = 0
    for source_order, path in enumerate(ordered_paths):
        frame, metadata, cache_hit = _load_or_refresh(
            path, config, cache_directory, original_loader
        )
        cache_hits += int(cache_hit)
        if not frame.empty:
            frame = frame.copy()
            frame["source_file_order"] = source_order
            frames.append(frame)
        metadata_rows.append(metadata)
    if not frames:
        empty, audit, daily = original_loader([], config)
        audit["cache"] = {
            "schema_version": CACHE_SCHEMA,
            "files": len(ordered_paths),
            "hits": cache_hits,
            "misses": len(ordered_paths) - cache_hits,
        }
        return empty, audit, daily

    raw = pd.concat(frames, ignore_index=True)
    ordered = raw.sort_values(
        ["tick_time_msc", "source_file_order", "source_row"], kind="mergesort"
    )
    ticks = (
        ordered.drop_duplicates("tick_time_msc", keep="last")
        .sort_values("tick_time_msc", kind="mergesort")
        .reset_index(drop=True)
    )
    timestamps = ticks["tick_time_msc"].to_numpy(dtype=np.int64)
    if bool(np.any(np.diff(timestamps) <= 0)):
        raise ValueError("Cached R4 tick timestamps are not strictly increasing")
    ticks["timestamp_utc"] = pd.to_datetime(
        ticks["tick_time_msc"], unit="ms", utc=True
    ).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    daily_records = [
        row
        for metadata in metadata_rows
        for row in metadata.get("daily_source_quality", [])
    ]
    recorded_daily = pd.DataFrame(daily_records)
    if recorded_daily.empty:
        raise ValueError("R4 cache metadata has no daily source-quality records")
    raw_counts = (
        recorded_daily.groupby("date_utc", as_index=False)
        .agg(raw_rows=("raw_rows", "sum"))
    )
    unique_counts = (
        raw.groupby("date_utc", as_index=False)
        .agg(unique_milliseconds=("tick_time_msc", "nunique"))
    )
    raw_daily = (
        raw_counts.merge(unique_counts, on="date_utc", how="outer", validate="one_to_one")
        .fillna(0)
        .sort_values("date_utc")
    )
    raw_daily[["raw_rows", "unique_milliseconds"]] = raw_daily[
        ["raw_rows", "unique_milliseconds"]
    ].astype(np.int64)
    raw_daily["duplicate_millisecond_rows"] = (
        raw_daily["raw_rows"] - raw_daily["unique_milliseconds"]
    )
    raw_daily["duplicate_millisecond_share"] = (
        raw_daily["duplicate_millisecond_rows"] / raw_daily["raw_rows"]
    )
    source_records = [
        record
        for metadata in metadata_rows
        for record in metadata.get("source_files", [])
    ]
    raw_rows = sum(int(metadata.get("raw_rows", 0)) for metadata in metadata_rows)
    audit = {
        "source_files": source_records,
        "raw_rows": raw_rows,
        "unique_rows": int(len(ticks)),
        "duplicate_millisecond_rows": raw_rows - int(len(ticks)),
        "daily_source_quality": raw_daily.to_dict(orient="records"),
        "cache": {
            "schema_version": CACHE_SCHEMA,
            "files": len(ordered_paths),
            "hits": cache_hits,
            "misses": len(ordered_paths) - cache_hits,
        },
    }
    return ticks, audit, raw_daily
