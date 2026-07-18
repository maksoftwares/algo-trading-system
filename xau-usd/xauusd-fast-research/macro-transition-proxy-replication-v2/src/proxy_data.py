from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Callable, Mapping, Sequence
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd


class SourceValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class DecodedHour:
    tick_count: int
    m15_rows: tuple[dict[str, Any], ...]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def official_url(origin: str, kind: str, source_code: str, hour: datetime | None = None) -> str:
    base = origin.rstrip("/")
    if kind == "instrument":
        result = f"{base}/instruments/{source_code}"
    elif kind == "ticks" and hour is not None:
        utc_hour = hour.astimezone(UTC)
        result = (
            f"{base}/ticks/{source_code}/{utc_hour.year}/{utc_hour.month}/"
            f"{utc_hour.day}/{utc_hour.hour}"
        )
    else:
        raise ValueError(f"Unsupported official URL kind: {kind}")
    validate_official_url(result, origin)
    return result


def validate_official_url(url: str, origin: str) -> None:
    parsed = urllib.parse.urlparse(url)
    expected = urllib.parse.urlparse(origin)
    if parsed.scheme != "https" or parsed.netloc != expected.netloc:
        raise SourceValidationError(f"Non-official source URL rejected: {url}")
    if parsed.query or parsed.fragment or ".." in parsed.path:
        raise SourceValidationError(f"Malformed source URL rejected: {url}")


def _payload_count(payload: Mapping[str, Any]) -> int:
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    missing = [name for name in arrays if not isinstance(payload.get(name), list)]
    if missing:
        raise SourceValidationError(f"Payload arrays missing or invalid: {missing}")
    lengths = {name: len(payload[name]) for name in arrays}
    if len(set(lengths.values())) != 1:
        raise SourceValidationError(f"Payload arrays differ in length: {lengths}")
    try:
        multiplier = float(payload["multiplier"])
        int(payload["timestamp"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceValidationError("Payload base values are invalid") from exc
    if not math.isfinite(multiplier) or multiplier <= 0.0:
        raise SourceValidationError("Payload multiplier must be positive")
    return lengths["times"]


def decode_hour(raw: bytes, hour: datetime) -> DecodedHour:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceValidationError(f"Invalid source JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SourceValidationError("Source payload is not an object")
    count = _payload_count(payload)
    if count == 0:
        return DecodedHour(0, ())

    try:
        timestamp = int(payload["timestamp"])
        bid = float(payload["bid"])
        ask = float(payload["ask"])
        multiplier = float(payload["multiplier"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceValidationError("Non-empty payload base price is invalid") from exc

    start_ms = int(hour.astimezone(UTC).timestamp() * 1000)
    end_ms = start_ms + 3_600_000
    previous = -1
    buckets: dict[int, dict[str, Any]] = {}
    for index in range(count):
        try:
            timestamp += int(payload["times"][index])
            bid = round(bid + float(payload["bids"][index]) * multiplier, 9)
            ask = round(ask + float(payload["asks"][index]) * multiplier, 9)
            bid_volume = float(payload["bidVolumes"][index])
            ask_volume = float(payload["askVolumes"][index])
        except (TypeError, ValueError) as exc:
            raise SourceValidationError(f"Invalid tick at index {index}") from exc
        if timestamp < previous or timestamp < start_ms or timestamp >= end_ms:
            raise SourceValidationError("Tick timestamps are not monotonic inside the requested hour")
        if not (math.isfinite(bid) and math.isfinite(ask) and bid > 0.0 and ask >= bid):
            raise SourceValidationError("Invalid bid/ask tick")
        if not (
            math.isfinite(bid_volume)
            and math.isfinite(ask_volume)
            and bid_volume >= 0.0
            and ask_volume >= 0.0
        ):
            raise SourceValidationError("Invalid best-side volume")
        bucket_start = timestamp // 900_000 * 900_000
        current = buckets.get(bucket_start)
        if current is None:
            current = {
                "timestamp_ms": bucket_start + 900_000,
                "mid_close": (bid + ask) / 2.0,
                "tick_count": 0,
            }
            buckets[bucket_start] = current
        current["mid_close"] = (bid + ask) / 2.0
        current["tick_count"] += 1
        previous = timestamp
    rows = tuple(buckets[key] for key in sorted(buckets))
    return DecodedHour(count, rows)


def acquisition_hours(
    start: datetime, end_exclusive: datetime, utc_hours: Sequence[int]
) -> list[datetime]:
    if start.tzinfo is None or end_exclusive.tzinfo is None:
        raise ValueError("Acquisition boundaries must be timezone-aware")
    allowed = tuple(sorted({int(hour) for hour in utc_hours}))
    if not allowed or allowed[0] < 0 or allowed[-1] > 23:
        raise ValueError("UTC hours must be between 0 and 23")
    day = start.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    final = end_exclusive.astimezone(UTC)
    result: list[datetime] = []
    while day < final:
        if day.weekday() < 5:
            for hour in allowed:
                value = day + timedelta(hours=hour)
                if start <= value < final:
                    result.append(value)
        day += timedelta(days=1)
    return result


def raw_hour_path(root: Path, symbol: str, hour: datetime) -> Path:
    return (
        root
        / "raw"
        / symbol
        / f"year={hour.year:04d}"
        / f"month={hour.month:02d}"
        / f"{hour:%Y%m%d%H}.json.gz"
    )


def http_fetch(url: str, timeout_seconds: int) -> tuple[bytes, Mapping[str, str], int]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "xauusd-macro-transition-proxy-replication-v2/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return (
            response.read(),
            {key.lower(): value for key, value in response.headers.items()},
            int(response.status),
        )


def acquire_hour(
    root: Path,
    origin: str,
    symbol: str,
    source_code: str,
    hour: datetime,
    timeout_seconds: int,
    quarantine_invalid: bool = False,
    fetcher: Callable[[str, int], tuple[bytes, Mapping[str, str], int]] = http_fetch,
) -> dict[str, Any]:
    path = raw_hour_path(root, symbol, hour)
    relative = str(path.relative_to(root)).replace("\\", "/")
    url = official_url(origin, "ticks", source_code, hour)
    if path.is_file():
        try:
            compressed = path.read_bytes()
            raw = gzip.decompress(compressed)
            try:
                decoded = decode_hour(raw, hour)
            except SourceValidationError as exc:
                if not quarantine_invalid:
                    raise
                return {
                    "symbol": symbol,
                    "source_code": source_code,
                    "hour_utc": hour.astimezone(UTC).isoformat(),
                    "url": url,
                    "status": "SOURCE_INVALID_HOUR_QUARANTINED",
                    "attempts": 0,
                    "http_status": 200,
                    "raw_bytes": len(raw),
                    "raw_sha256": sha256_bytes(raw),
                    "compressed_bytes": len(compressed),
                    "compressed_sha256": sha256_bytes(compressed),
                    "tick_count": 0,
                    "m15_rows": 0,
                    "path": relative,
                    "quarantine_reason": f"{type(exc).__name__}: {exc}",
                }
            return {
                "symbol": symbol,
                "source_code": source_code,
                "hour_utc": hour.astimezone(UTC).isoformat(),
                "url": url,
                "status": "RESUMED_VALID",
                "attempts": 0,
                "http_status": 200,
                "raw_bytes": len(raw),
                "raw_sha256": sha256_bytes(raw),
                "compressed_bytes": len(compressed),
                "compressed_sha256": sha256_bytes(compressed),
                "tick_count": decoded.tick_count,
                "m15_rows": len(decoded.m15_rows),
                "path": relative,
            }
        except (OSError, gzip.BadGzipFile, SourceValidationError):
            path.unlink(missing_ok=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    last_error = ""
    for attempt in (1, 2):
        raw = b""
        status = 0
        try:
            raw, headers, status = fetcher(url, timeout_seconds)
            if status != 200:
                raise SourceValidationError(f"HTTP status {status}")
            decoded = decode_hour(raw, hour)
            compressed = gzip.compress(raw, compresslevel=6, mtime=0)
            partial = path.with_suffix(path.suffix + ".part")
            partial.write_bytes(compressed)
            os.replace(partial, path)
            return {
                "symbol": symbol,
                "source_code": source_code,
                "hour_utc": hour.astimezone(UTC).isoformat(),
                "url": url,
                "status": "DOWNLOADED_VALID",
                "attempts": attempt,
                "http_status": status,
                "raw_bytes": len(raw),
                "raw_sha256": sha256_bytes(raw),
                "compressed_bytes": len(compressed),
                "compressed_sha256": sha256_bytes(compressed),
                "tick_count": decoded.tick_count,
                "m15_rows": len(decoded.m15_rows),
                "etag": headers.get("etag", ""),
                "last_modified": headers.get("last-modified", ""),
                "path": relative,
            }
        except (OSError, urllib.error.URLError, SourceValidationError) as exc:
            if quarantine_invalid and status == 200 and raw:
                compressed = gzip.compress(raw, compresslevel=6, mtime=0)
                partial = path.with_suffix(path.suffix + ".part")
                partial.write_bytes(compressed)
                os.replace(partial, path)
                return {
                    "symbol": symbol,
                    "source_code": source_code,
                    "hour_utc": hour.astimezone(UTC).isoformat(),
                    "url": url,
                    "status": "SOURCE_INVALID_HOUR_QUARANTINED",
                    "attempts": attempt,
                    "http_status": status,
                    "raw_bytes": len(raw),
                    "raw_sha256": sha256_bytes(raw),
                    "compressed_bytes": len(compressed),
                    "compressed_sha256": sha256_bytes(compressed),
                    "tick_count": 0,
                    "m15_rows": 0,
                    "path": relative,
                    "quarantine_reason": f"{type(exc).__name__}: {exc}",
                }
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt == 1:
                time.sleep(0.25)
    return {
        "symbol": symbol,
        "source_code": source_code,
        "hour_utc": hour.astimezone(UTC).isoformat(),
        "url": url,
        "status": "FAILED_AFTER_ONE_RETRY",
        "attempts": 2,
        "http_status": "",
        "raw_bytes": 0,
        "raw_sha256": "",
        "compressed_bytes": 0,
        "compressed_sha256": "",
        "tick_count": 0,
        "m15_rows": 0,
        "path": relative,
        "error": last_error,
    }


def acquire_symbol(
    root: Path,
    origin: str,
    symbol: str,
    source_code: str,
    hours: Sequence[datetime],
    timeout_seconds: int,
    concurrency: int,
    quarantined_hours: set[str] | None = None,
    progress: Callable[[int, int, str], None] | None = None,
) -> list[dict[str, Any]]:
    if not 1 <= concurrency <= 8:
        raise ValueError("Concurrency must be between one and eight")
    rows: list[dict[str, Any]] = []
    quarantined = quarantined_hours or set()
    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="dukas-proxy") as pool:
        futures = {
            pool.submit(
                acquire_hour,
                root,
                origin,
                symbol,
                source_code,
                hour,
                timeout_seconds,
                hour.astimezone(UTC).isoformat() in quarantined,
            ): hour
            for hour in hours
        }
        total = len(futures)
        for number, future in enumerate(as_completed(futures), 1):
            rows.append(future.result())
            if progress is not None and (number % 100 == 0 or number == total):
                progress(number, total, symbol)
    rows.sort(key=lambda row: str(row["hour_utc"]))
    failures = [row for row in rows if row["status"] == "FAILED_AFTER_ONE_RETRY"]
    if failures:
        example = failures[0]
        raise RuntimeError(
            f"{len(failures)} {symbol} hours failed; first={example['hour_utc']} {example.get('error', '')}"
        )
    return rows


def acquire_metadata(
    root: Path,
    origin: str,
    symbol: str,
    source_code: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    url = official_url(origin, "instrument", source_code)
    raw, _, status = http_fetch(url, timeout_seconds)
    if status != 200:
        raise SourceValidationError(f"Metadata HTTP status {status}")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SourceValidationError("Instrument metadata is invalid JSON") from exc
    if payload.get("code") != source_code or float(payload.get("pipValue", 0.0)) <= 0.0:
        raise SourceValidationError(f"Instrument metadata identity failed for {source_code}")
    path = root / "metadata" / f"{symbol}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".json.part")
    partial.write_bytes(raw)
    os.replace(partial, path)
    histories = payload.get("histories", [])
    tick_starts = [int(item["from"]) for item in histories if item.get("period") == "TICK"]
    if len(tick_starts) != 1:
        raise SourceValidationError(f"Exactly one tick-history boundary required for {source_code}")
    return {
        "symbol": symbol,
        "source_code": source_code,
        "url": url,
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "tick_history_start_ms": tick_starts[0],
        "pip_value": float(payload["pipValue"]),
        "description": str(payload.get("description", "")),
    }


def build_cache(root: Path, acquisition_manifest_path: Path, cache_path: Path) -> dict[str, Any]:
    manifest = json.loads(acquisition_manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("hours")
    if not isinstance(rows, list) or not rows:
        raise SourceValidationError("Acquisition manifest has no hourly rows")
    output: list[dict[str, Any]] = []
    for row in rows:
        if row.get("status") not in {
            "DOWNLOADED_VALID",
            "RESUMED_VALID",
            "SOURCE_INVALID_HOUR_QUARANTINED",
        }:
            raise SourceValidationError("Acquisition manifest contains an invalid status")
        path = (root / str(row["path"])).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise SourceValidationError("Raw path escapes the proxy root") from exc
        compressed = path.read_bytes()
        if sha256_bytes(compressed) != row["compressed_sha256"]:
            raise SourceValidationError(f"Compressed SHA mismatch: {row['path']}")
        raw = gzip.decompress(compressed)
        if sha256_bytes(raw) != row["raw_sha256"]:
            raise SourceValidationError(f"Raw SHA mismatch: {row['path']}")
        hour = datetime.fromisoformat(str(row["hour_utc"])).astimezone(UTC)
        if row["status"] == "SOURCE_INVALID_HOUR_QUARANTINED":
            try:
                decode_hour(raw, hour)
            except SourceValidationError:
                continue
            raise SourceValidationError(
                f"Quarantined payload unexpectedly became valid: {row['path']}"
            )
        decoded = decode_hour(raw, hour)
        if decoded.tick_count != int(row["tick_count"]):
            raise SourceValidationError(f"Tick count mismatch: {row['path']}")
        output.extend({"symbol": row["symbol"], **item} for item in decoded.m15_rows)
    frame = pd.DataFrame(output)
    if frame.empty:
        raise SourceValidationError("No proxy M15 closes were decoded")
    frame["timestamp_utc"] = pd.to_datetime(frame.pop("timestamp_ms"), unit="ms", utc=True)
    frame = frame[["timestamp_utc", "symbol", "mid_close", "tick_count"]]
    frame = frame.sort_values(["symbol", "timestamp_utc"], kind="mergesort").reset_index(drop=True)
    if frame.duplicated(["symbol", "timestamp_utc"]).any():
        raise SourceValidationError("Duplicate symbol/timestamp proxy rows")
    if (~np.isfinite(frame["mid_close"]) | frame["mid_close"].le(0.0)).any():
        raise SourceValidationError("Invalid proxy M15 midpoint")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(cache_path, index=False)
    inventory = []
    for symbol, group in frame.groupby("symbol", sort=True):
        inventory.append(
            {
                "symbol": symbol,
                "rows": int(len(group)),
                "first_timestamp_utc": group["timestamp_utc"].min().isoformat(),
                "last_timestamp_utc": group["timestamp_utc"].max().isoformat(),
                "tick_count": int(group["tick_count"].sum()),
            }
        )
    return {
        "schema_version": "xauusd_macro_transition_proxy_m15_v2",
        "acquisition_manifest": str(acquisition_manifest_path.relative_to(root)).replace("\\", "/"),
        "acquisition_manifest_sha256": sha256_file(acquisition_manifest_path),
        "cache": str(cache_path.relative_to(root)).replace("\\", "/"),
        "cache_bytes": int(cache_path.stat().st_size),
        "cache_sha256": sha256_file(cache_path),
        "rows": int(len(frame)),
        "inventory": inventory,
        "metadata": manifest.get("metadata", []),
    }


def load_proxy_cache(config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = config["proxy_source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]), str(source["default_storage_root"])
        )
    )
    root = storage / str(source["root"])
    cache = root / str(source["cache"])
    manifest_path = root / str(source["cache_manifest"])
    expected_cache = str(source["cache_sha256"])
    expected_manifest = str(source["cache_manifest_sha256"])
    if expected_cache.startswith("TO_BE_") or expected_manifest.startswith("TO_BE_"):
        raise ValueError("Proxy cache hashes have not been locked into the config")
    if sha256_file(cache) != expected_cache or sha256_file(manifest_path) != expected_manifest:
        raise SourceValidationError("Proxy cache or manifest SHA-256 mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(cache)
    if len(frame) != int(manifest["rows"]):
        raise SourceValidationError("Proxy cache row count differs from its manifest")
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame = frame.sort_values(["symbol", "timestamp_utc"], kind="mergesort").reset_index(drop=True)
    if frame.duplicated(["symbol", "timestamp_utc"]).any():
        raise SourceValidationError("Duplicate proxy cache key")
    evidence = {
        "root": str(root),
        "cache": str(cache),
        "cache_sha256": expected_cache,
        "manifest": str(manifest_path),
        "manifest_sha256": expected_manifest,
        "inventory": manifest["inventory"],
    }
    return frame, evidence


def _contiguous_log_return(close: pd.Series, timestamp: pd.Series, bars: int, minutes: int) -> pd.Series:
    elapsed = timestamp - timestamp.shift(bars)
    values = np.log(close / close.shift(bars))
    return values.where(elapsed.eq(pd.Timedelta(minutes=minutes)))


def build_pressure_frame(
    cache: pd.DataFrame, proxy_symbol: str, settings: Mapping[str, Any]
) -> pd.DataFrame:
    required = {"DOLLARIDXUSD", proxy_symbol}
    available = set(cache["symbol"].astype(str).unique())
    if not required.issubset(available):
        raise ValueError(f"Missing pressure symbols: {sorted(required.difference(available))}")
    dollar = cache.loc[
        cache["symbol"].eq("DOLLARIDXUSD"), ["timestamp_utc", "mid_close"]
    ].rename(columns={"mid_close": "dxy_close"})
    proxy = cache.loc[
        cache["symbol"].eq(proxy_symbol), ["timestamp_utc", "mid_close"]
    ].rename(columns={"mid_close": "bond_close"})
    frame = dollar.merge(proxy, on="timestamp_utc", how="inner", validate="one_to_one")
    frame = frame.sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)
    bars = int(settings["return_bars"])
    minutes = int(settings["return_elapsed_minutes"])
    scale_hours = int(settings["scale_elapsed_hours"])
    minimum = int(settings["minimum_prior_observations"])
    timestamp = frame["timestamp_utc"]
    for name, sign in (
        ("dxy", float(settings["dxy_pressure_sign"])),
        ("bond", float(settings["bond_pressure_sign"])),
    ):
        returns = _contiguous_log_return(frame[f"{name}_close"], timestamp, bars, minutes)
        indexed = pd.Series(returns.to_numpy(dtype=float), index=pd.DatetimeIndex(timestamp))
        prior_scale = indexed.rolling(
            f"{scale_hours}h", min_periods=minimum, closed="left"
        ).std(ddof=0)
        frame[f"{name}_pressure_H1_D2"] = (
            sign * returns.to_numpy(dtype=float) / prior_scale.to_numpy(dtype=float)
        )
    return frame[
        ["timestamp_utc", "dxy_pressure_H1_D2", "bond_pressure_H1_D2"]
    ].copy()
