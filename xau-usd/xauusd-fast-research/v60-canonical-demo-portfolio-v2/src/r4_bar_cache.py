from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterable, Mapping

import numpy as np
import pandas as pd


CACHE_SCHEMA = "xauusd_v60_r4_per_file_bar_cache_v2"
BAR_WIDTH_MS = 5 * 60 * 1000


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_identity(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.resolve()).replace("\\", "/"),
        "bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _cache_key(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:24]


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
    fd, temporary = tempfile.mkstemp(
        prefix=path.name, suffix=".tmp.parquet", dir=path.parent
    )
    os.close(fd)
    try:
        frame.to_parquet(temporary, index=False)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_or_refresh(
    path: Path,
    loader_config: dict[str, Any],
    quality: Mapping[str, Any],
    cache_directory: Path,
    original_loader: Callable[..., tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]],
    original_aggregate: Callable[..., pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], bool]:
    key = _cache_key(path)
    parquet_path = cache_directory / f"{key}.parquet"
    boundary_path = cache_directory / f"{key}.boundary.parquet"
    metadata_path = cache_directory / f"{key}.json"
    identity = _source_identity(path)
    contract_sha256 = _canonical_sha256(
        {"loader_config": loader_config, "quality": dict(quality)}
    )
    if parquet_path.is_file() and boundary_path.is_file() and metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            metadata.get("schema_version") == CACHE_SCHEMA
            and metadata.get("source_identity") == identity
            and metadata.get("contract_sha256") == contract_sha256
            and metadata.get("parquet_sha256") == _sha256_file(parquet_path)
            and metadata.get("boundary_sha256") == _sha256_file(boundary_path)
        ):
            return (
                pd.read_parquet(parquet_path),
                pd.read_parquet(boundary_path),
                metadata,
                True,
            )

    ticks, audit, daily = original_loader([path], loader_config)
    bars = original_aggregate(
        ticks,
        completed_through=pd.Timestamp("2100-01-01", tz="UTC"),
        quality=quality,
    )
    if ticks.empty:
        boundary = pd.DataFrame(
            columns=[
                "tick_time_msc",
                "bid",
                "ask",
                "spread_price",
                "source_row",
                "date_utc",
            ]
        )
    else:
        buckets = ticks["tick_time_msc"].astype(np.int64)
        buckets = buckets - buckets % BAR_WIDTH_MS
        selected = buckets.eq(int(buckets.iloc[0])) | buckets.eq(int(buckets.iloc[-1]))
        boundary = ticks.loc[
            selected,
            [
                "tick_time_msc",
                "bid",
                "ask",
                "spread_price",
                "source_row",
                "date_utc",
            ],
        ].copy()
    _atomic_parquet(parquet_path, bars)
    _atomic_parquet(boundary_path, boundary)
    metadata = {
        "schema_version": CACHE_SCHEMA,
        "source_identity": identity,
        "contract_sha256": contract_sha256,
        "parquet_sha256": _sha256_file(parquet_path),
        "boundary_sha256": _sha256_file(boundary_path),
        "source_files": audit.get("source_files", []),
        "raw_rows": int(audit.get("raw_rows", 0)),
        "unique_rows": int(audit.get("unique_rows", len(ticks))),
        "daily_source_quality": daily.to_dict(orient="records"),
    }
    _atomic_json(metadata_path, metadata)
    return bars, boundary, metadata, False


def _recalculate_global_fields(
    bars: pd.DataFrame,
    *,
    completed_through: pd.Timestamp,
) -> pd.DataFrame:
    result = bars.sort_values("timestamp_ms", kind="mergesort").reset_index(drop=True)
    if result["timestamp_ms"].duplicated().any():
        raise ValueError("R4 bar-cache boundary correction left duplicate M5 buckets")
    result = result.loc[result["bar_end_utc"] <= pd.Timestamp(completed_through)].copy()
    result["tick_imbalance_5m"] = result["tick_signed_move"].div(
        result["tick_move_count"].replace(0, np.nan)
    )
    result["tick_imbalance_15m"] = result["tick_signed_move"].rolling(3).sum().div(
        result["tick_move_count"].rolling(3).sum().replace(0, np.nan)
    )
    contiguous = (result["timestamp_ms"] - result["timestamp_ms"].shift(2)).eq(
        10 * 60 * 1000
    )
    quality_15m = result["quote_quality_passed"].rolling(3).sum().eq(3)
    result["quote_contiguous_15m"] = contiguous & quality_15m
    result.loc[~result["quote_contiguous_15m"], "tick_imbalance_15m"] = np.nan
    baseline = result["xau_tick_count"].rolling(288, min_periods=96).median()
    result["quote_intensity_ratio"] = result["xau_tick_count"].div(
        baseline.replace(0.0, np.nan)
    )
    return result.reset_index(drop=True)


def load_quote_bars_cached(
    paths: Iterable[Path],
    loader_config: dict[str, Any],
    *,
    quality: Mapping[str, Any],
    completed_through: pd.Timestamp,
    cache_directory: Path,
    original_loader: Callable[..., tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]],
    original_aggregate: Callable[..., pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    ordered_paths = sorted(Path(value) for value in paths)
    frames: list[pd.DataFrame] = []
    boundary_frames: list[pd.DataFrame] = []
    metadata_rows: list[dict[str, Any]] = []
    hits = 0
    for source_order, path in enumerate(ordered_paths):
        frame, boundary, metadata, hit = _load_or_refresh(
            path,
            loader_config,
            quality,
            cache_directory,
            original_loader,
            original_aggregate,
        )
        hits += int(hit)
        if not frame.empty:
            frame = frame.copy()
            frame["_source_file_order"] = source_order
            frames.append(frame)
        if not boundary.empty:
            boundary = boundary.copy()
            boundary["_source_file_order"] = source_order
            boundary_frames.append(boundary)
        metadata_rows.append(metadata)
    bars = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not bars.empty:
        bars = bars.sort_values(
            ["timestamp_ms", "_source_file_order"], kind="mergesort"
        )
        duplicate_buckets = bars.loc[
            bars["timestamp_ms"].duplicated(keep=False), "timestamp_ms"
        ].unique()
        if len(duplicate_buckets):
            boundary_ticks = pd.concat(boundary_frames, ignore_index=True)
            boundary_ticks["_bucket"] = (
                boundary_ticks["tick_time_msc"].astype(np.int64) // BAR_WIDTH_MS
            ) * BAR_WIDTH_MS
            corrections: list[pd.DataFrame] = []
            for bucket in duplicate_buckets:
                selected = boundary_ticks.loc[boundary_ticks["_bucket"].eq(bucket)]
                selected = (
                    selected.sort_values(
                        ["tick_time_msc", "_source_file_order", "source_row"],
                        kind="mergesort",
                    )
                    .drop_duplicates("tick_time_msc", keep="last")
                    .drop(columns=["_source_file_order", "_bucket"])
                    .reset_index(drop=True)
                )
                correction = original_aggregate(
                    selected,
                    completed_through=pd.Timestamp("2100-01-01", tz="UTC"),
                    quality=quality,
                )
                if len(correction) != 1:
                    raise ValueError("R4 boundary correction did not produce one M5 bar")
                corrections.append(correction)
            bars = bars.loc[~bars["timestamp_ms"].isin(duplicate_buckets)].copy()
            bars = pd.concat([bars, *corrections], ignore_index=True)
        bars = bars.drop(columns="_source_file_order", errors="ignore")
        bars = _recalculate_global_fields(bars, completed_through=completed_through)

    daily_records = [
        row
        for metadata in metadata_rows
        for row in metadata.get("daily_source_quality", [])
    ]
    daily = pd.DataFrame(daily_records)
    if not daily.empty:
        daily = (
            daily.groupby("date_utc", as_index=False)
            .agg(
                raw_rows=("raw_rows", "sum"),
                unique_milliseconds=("unique_milliseconds", "sum"),
            )
            .sort_values("date_utc")
            .reset_index(drop=True)
        )
        daily["duplicate_millisecond_rows"] = (
            daily["raw_rows"] - daily["unique_milliseconds"]
        )
        daily["duplicate_millisecond_share"] = (
            daily["duplicate_millisecond_rows"] / daily["raw_rows"]
        )
    raw_rows = sum(int(row.get("raw_rows", 0)) for row in metadata_rows)
    unique_rows = sum(int(row.get("unique_rows", 0)) for row in metadata_rows)
    audit = {
        "source_files": [
            record
            for metadata in metadata_rows
            for record in metadata.get("source_files", [])
        ],
        "raw_rows": raw_rows,
        "unique_rows": unique_rows,
        "duplicate_millisecond_rows": raw_rows - unique_rows,
        "daily_source_quality": daily.to_dict(orient="records"),
        "bar_cache": {
            "schema_version": CACHE_SCHEMA,
            "files": len(ordered_paths),
            "hits": hits,
            "misses": len(ordered_paths) - hits,
        },
    }
    return bars, audit, daily
