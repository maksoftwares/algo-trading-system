from __future__ import annotations

import calendar
import csv
import hashlib
import json
import math
import os
import shutil
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence


PHASE = "DUKASCOPY_MULTI_ASSET_TICK_DATA_FOUNDATION_V1"
CLASSIFICATIONS = ("READY", "PARTIAL_NOT_READY", "INVALID")
START_UTC = datetime(2016, 7, 1, tzinfo=UTC)
END_UTC = datetime(2026, 6, 30, 23, 59, 59, 999000, tzinfo=UTC)
END_EXCLUSIVE_UTC = datetime(2026, 7, 1, tzinfo=UTC)
OFFICIAL_ORIGIN = "https://jetta.dukascopy.com/v1"
OFFICIAL_WIDGET = "https://widgets.dukascopy.com/en/historical-data-export"
OFFICIAL_HISTORY_DOC = "https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/history-ticks/"
STORAGE_ENV = "DUKASCOPY_TICK_DATA_ROOT"
MAX_CONCURRENCY = 4
TIMEOUT_SECONDS = 60
TIMEFRAMES_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}
PRICE_BASES = ("Bid", "Ask", "Mid")
INSTRUMENTS: dict[str, dict[str, Any]] = {
    "EURUSD": {"source_code": "EUR-USD", "pip_size": 0.0001, "price_scale": 5},
    "GBPUSD": {"source_code": "GBP-USD", "pip_size": 0.0001, "price_scale": 5},
    "USDJPY": {"source_code": "USD-JPY", "pip_size": 0.01, "price_scale": 3},
    "XAUUSD": {"source_code": "XAU-USD", "pip_size": 0.01, "price_scale": 3},
}
NORMALIZED_COLUMNS = (
    "timestamp_utc",
    "timestamp_ms",
    "bid",
    "ask",
    "spread",
    "bid_volume",
    "ask_volume",
    "source_file_id",
    "source_row_index",
)
FORBIDDEN_FIELDS = {
    "signal",
    "trade",
    "entry",
    "exit",
    "pnl",
    "profit",
    "loss",
    "drawdown",
    "leverage",
    "lot",
    "account",
    "risk",
}


class FoundationError(RuntimeError):
    pass


class StorageConfigurationError(FoundationError):
    pass


class SourceValidationError(FoundationError):
    pass


class CorruptRawFileError(FoundationError):
    pass


@dataclass(frozen=True)
class Tick:
    timestamp_ms: int
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float
    source_file_id: str
    source_row_index: int

    @property
    def spread(self) -> float:
        return self.ask - self.bid

    def as_row(self) -> dict[str, Any]:
        return {
            "timestamp_utc": datetime.fromtimestamp(self.timestamp_ms / 1000, UTC),
            "timestamp_ms": self.timestamp_ms,
            "bid": self.bid,
            "ask": self.ask,
            "spread": self.spread,
            "bid_volume": self.bid_volume,
            "ask_volume": self.ask_volume,
            "source_file_id": self.source_file_id,
            "source_row_index": self.source_row_index,
        }


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def iso_utc(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def month_keys(start: datetime = START_UTC, end_exclusive: datetime = END_EXCLUSIVE_UTC) -> list[str]:
    cursor = datetime(start.year, start.month, 1, tzinfo=UTC)
    result: list[str] = []
    while cursor < end_exclusive:
        result.append(f"{cursor.year:04d}-{cursor.month:02d}")
        cursor = datetime(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1, tzinfo=UTC)
    return result


def hours_in_month(year: int, month: int) -> list[datetime]:
    count = calendar.monthrange(year, month)[1] * 24
    start = datetime(year, month, 1, tzinfo=UTC)
    return [start + timedelta(hours=index) for index in range(count)]


def official_tick_url(symbol: str, hour: datetime) -> str:
    spec = INSTRUMENTS[symbol]
    hour = hour.astimezone(UTC)
    return f"{OFFICIAL_ORIGIN}/ticks/{spec['source_code']}/{hour.year}/{hour.month}/{hour.day}/{hour.hour}"


def official_instrument_url(symbol: str) -> str:
    return f"{OFFICIAL_ORIGIN}/instruments/{INSTRUMENTS[symbol]['source_code']}"


def validate_official_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"jetta.dukascopy.com", "widgets.dukascopy.com", "www.dukascopy.com"}:
        raise SourceValidationError(f"non-official or insecure source URL rejected: {url}")


def resolve_storage_root(env: Mapping[str, str] | None = None, lane_root: Path | None = None) -> Path:
    values = os.environ if env is None else env
    raw = values.get(STORAGE_ENV, "").strip()
    if not raw:
        raise StorageConfigurationError(f"{STORAGE_ENV} is required")
    root = Path(raw).expanduser().resolve()
    if lane_root is not None:
        lane = lane_root.resolve()
        try:
            root.relative_to(lane)
        except ValueError:
            pass
        else:
            raise StorageConfigurationError("bulk storage must be outside the Git lane")
    root.mkdir(parents=True, exist_ok=True)
    return root


def storage_preflight(root: Path, estimated_total_bytes: int) -> dict[str, Any]:
    usage = shutil.disk_usage(root)
    required_free = math.ceil(estimated_total_bytes * 1.5)
    return {
        "estimated_total_bytes": estimated_total_bytes,
        "required_free_bytes": required_free,
        "observed_free_bytes": usage.free,
        "passes": usage.free >= required_free,
        "headroom_ratio": usage.free / estimated_total_bytes if estimated_total_bytes else None,
    }


def validate_payload_shape(payload: Mapping[str, Any]) -> int:
    arrays = ("times", "bids", "asks", "bidVolumes", "askVolumes")
    missing = [key for key in ("timestamp", "multiplier", "bid", "ask", *arrays) if key not in payload]
    if missing:
        raise SourceValidationError(f"missing payload fields: {','.join(missing)}")
    lengths = {key: len(payload[key]) if isinstance(payload[key], list) else -1 for key in arrays}
    if len(set(lengths.values())) != 1 or next(iter(lengths.values())) < 0:
        raise SourceValidationError(f"tick arrays are inconsistent: {lengths}")
    if not isinstance(payload["timestamp"], int) or not isinstance(payload["multiplier"], (int, float)):
        raise SourceValidationError("timestamp or multiplier type is invalid")
    if payload["multiplier"] <= 0:
        raise SourceValidationError("multiplier must be positive")
    return lengths["times"]


def _round_source_price(value: float, scale: int) -> float:
    factor = 10**scale
    return math.floor(value * factor + 0.5 + 1e-9) / factor


def decode_payload(raw: bytes, symbol: str, source_file_id: str) -> list[Tick]:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceValidationError(f"invalid source JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SourceValidationError("source payload is not an object")
    count = validate_payload_shape(payload)
    if count == 0:
        return []
    scale = int(INSTRUMENTS[symbol]["price_scale"])
    try:
        timestamp = int(payload["timestamp"])
        bid = float(payload["bid"])
        ask = float(payload["ask"])
        multiplier = float(payload["multiplier"])
    except (TypeError, ValueError) as exc:
        raise SourceValidationError("non-empty payload has invalid base timestamp or price") from exc
    result: list[Tick] = []
    previous_timestamp = -1
    for index in range(count):
        timestamp += int(payload["times"][index])
        bid = _round_source_price(bid + float(payload["bids"][index]) * multiplier, scale)
        ask = _round_source_price(ask + float(payload["asks"][index]) * multiplier, scale)
        bid_volume = float(payload["bidVolumes"][index])
        ask_volume = float(payload["askVolumes"][index])
        if timestamp < previous_timestamp:
            raise SourceValidationError("timestamps are not monotonic")
        if not (bid > 0 and ask > 0 and ask >= bid):
            raise SourceValidationError("non-positive price or negative spread")
        if not (math.isfinite(bid_volume) and math.isfinite(ask_volume) and bid_volume >= 0 and ask_volume >= 0):
            raise SourceValidationError("invalid best-side volume")
        result.append(Tick(timestamp, bid, ask, bid_volume, ask_volume, source_file_id, index))
        previous_timestamp = timestamp
    return result


def validate_hour_payload(raw: bytes, symbol: str, hour: datetime, source_file_id: str) -> int:
    ticks = decode_payload(raw, symbol, source_file_id)
    start_ms = int(hour.astimezone(UTC).timestamp() * 1000)
    end_ms = start_ms + 3_600_000
    if any(tick.timestamp_ms < start_ms or tick.timestamp_ms >= end_ms for tick in ticks):
        raise SourceValidationError("decoded timestamp falls outside requested UTC hour")
    return len(ticks)


def http_fetch(url: str, timeout_seconds: int = TIMEOUT_SECONDS) -> tuple[bytes, dict[str, str], int]:
    validate_official_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": f"{PHASE}/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read()
        return body, {key.lower(): value for key, value in response.headers.items()}, response.status


def raw_hour_path(storage_root: Path, symbol: str, hour: datetime) -> Path:
    return storage_root / "raw" / symbol / f"year={hour.year:04d}" / f"month={hour.month:02d}" / f"{hour:%Y%m%d%H}.json"


def acquire_hour(
    storage_root: Path,
    symbol: str,
    hour: datetime,
    fetcher: Callable[[str, int], tuple[bytes, dict[str, str], int]] = http_fetch,
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> dict[str, Any]:
    path = raw_hour_path(storage_root, symbol, hour)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_id = f"{symbol}-{hour:%Y%m%d%H}"
    url = official_tick_url(symbol, hour)
    if path.exists():
        try:
            count = validate_hour_payload(path.read_bytes(), symbol, hour, file_id)
            return {
                "symbol": symbol, "hour_utc": iso_utc(hour), "source_file_id": file_id,
                "url": url, "status": "RESUMED_VALID", "attempts": 0, "http_status": 200,
                "bytes": path.stat().st_size, "sha256": sha256_file(path), "tick_count": count,
                "etag": "", "last_modified": "", "path": str(path.relative_to(storage_root)).replace("\\", "/"),
            }
        except SourceValidationError:
            path.chmod(0o666)
            path.unlink()
    last_error = ""
    for attempt in (1, 2):
        try:
            body, headers, status = fetcher(url, timeout_seconds)
            if status != 200:
                raise SourceValidationError(f"HTTP status {status}")
            count = validate_hour_payload(body, symbol, hour, file_id)
            partial = path.with_suffix(".json.part")
            partial.write_bytes(body)
            os.replace(partial, path)
            return {
                "symbol": symbol, "hour_utc": iso_utc(hour), "source_file_id": file_id,
                "url": url, "status": "DOWNLOADED_VALID", "attempts": attempt, "http_status": status,
                "bytes": len(body), "sha256": sha256_bytes(body), "tick_count": count,
                "etag": headers.get("etag", ""), "last_modified": headers.get("last-modified", ""),
                "path": str(path.relative_to(storage_root)).replace("\\", "/"),
            }
        except (OSError, urllib.error.URLError, SourceValidationError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt == 1:
                continue
    return {
        "symbol": symbol, "hour_utc": iso_utc(hour), "source_file_id": file_id, "url": url,
        "status": "FAILED_AFTER_ONE_RETRY", "attempts": 2, "http_status": "", "bytes": 0,
        "sha256": "", "tick_count": 0, "etag": "", "last_modified": "",
        "path": str(path.relative_to(storage_root)).replace("\\", "/"), "error": last_error,
    }


def acquire_month(
    storage_root: Path,
    symbol: str,
    year: int,
    month: int,
    concurrency: int = MAX_CONCURRENCY,
    fetcher: Callable[[str, int], tuple[bytes, dict[str, str], int]] = http_fetch,
) -> list[dict[str, Any]]:
    if not 1 <= concurrency <= MAX_CONCURRENCY:
        raise ValueError(f"concurrency must be between 1 and {MAX_CONCURRENCY}")
    hours = hours_in_month(year, month)
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="dukascopy") as executor:
        futures = {executor.submit(acquire_hour, storage_root, symbol, hour, fetcher): hour for hour in hours}
        for future in as_completed(futures):
            rows.append(future.result())
    return sorted(rows, key=lambda row: row["hour_utc"])


def write_month_acquisition_manifest(
    storage_root: Path,
    symbol: str,
    year: int,
    month: int,
    rows: Sequence[Mapping[str, Any]],
) -> Path:
    expected = len(hours_in_month(year, month))
    if len(rows) != expected or any(row.get("symbol") != symbol for row in rows):
        raise CorruptRawFileError("acquisition manifest has wrong symbol or hourly cardinality")
    for row in rows:
        validate_official_url(str(row.get("url", "")))
        if f"/ticks/{INSTRUMENTS[symbol]['source_code']}/" not in str(row["url"]):
            raise CorruptRawFileError("cross-symbol acquisition URL rejected")
    root = storage_root / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"
    path = root / "_ACQUISITION_MANIFEST.json"
    if path.exists():
        path.chmod(0o666)
    write_json(path, {
        "symbol": symbol,
        "month": f"{year:04d}-{month:02d}",
        "rows": sorted(rows, key=lambda row: str(row["hour_utc"])),
    })
    return path


def validate_month_acquisition_manifest(storage_root: Path, symbol: str, year: int, month: int) -> None:
    root = storage_root / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"
    path = root / "_ACQUISITION_MANIFEST.json"
    if not path.is_file():
        raise CorruptRawFileError("monthly acquisition manifest is missing")
    try:
        manifest = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise CorruptRawFileError("monthly acquisition manifest is unreadable") from exc
    if manifest.get("symbol") != symbol or manifest.get("month") != f"{year:04d}-{month:02d}":
        raise CorruptRawFileError("cross-symbol or cross-month acquisition manifest rejected")
    rows = manifest.get("rows")
    if not isinstance(rows, list) or len(rows) != len(hours_in_month(year, month)):
        raise CorruptRawFileError("monthly acquisition manifest is incomplete")
    for row in rows:
        if row.get("symbol") != symbol or row.get("status") not in {"DOWNLOADED_VALID", "RESUMED_VALID"}:
            raise CorruptRawFileError("invalid acquisition row identity or status")
        validate_official_url(str(row.get("url", "")))
        if f"/ticks/{INSTRUMENTS[symbol]['source_code']}/" not in str(row["url"]):
            raise CorruptRawFileError("cross-symbol acquisition URL rejected")
        raw_path = storage_root / str(row.get("path", ""))
        try:
            raw_path.resolve().relative_to(root.resolve())
        except ValueError as exc:
            raise CorruptRawFileError("raw path escapes its symbol-month partition") from exc
        if not raw_path.is_file() or sha256_file(raw_path) != row.get("sha256"):
            raise CorruptRawFileError("raw file missing or checksum mismatch")


def freeze_raw_month(storage_root: Path, symbol: str, year: int, month: int) -> dict[str, Any]:
    root = storage_root / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"
    files = sorted(path for path in root.glob("*.json") if not path.name.startswith("_"))
    expected = len(hours_in_month(year, month))
    for path in files:
        path.chmod(0o444)
    manifest = {
        "symbol": symbol, "month": f"{year:04d}-{month:02d}", "expected_hour_files": expected,
        "observed_hour_files": len(files), "complete": len(files) == expected,
        "frozen": True, "files_sha256": sha256_bytes(canonical_json_bytes([(p.name, sha256_file(p)) for p in files])),
    }
    frozen_manifest = root / "_FROZEN_MANIFEST.json"
    if frozen_manifest.exists():
        frozen_manifest.chmod(0o666)
    write_json(frozen_manifest, manifest)
    frozen_manifest.chmod(0o444)
    acquisition_manifest = root / "_ACQUISITION_MANIFEST.json"
    if acquisition_manifest.exists():
        acquisition_manifest.chmod(0o444)
    return manifest


def iter_raw_month(storage_root: Path, symbol: str, year: int, month: int) -> Iterator[tuple[Path, bytes]]:
    root = storage_root / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"
    for path in sorted(root.glob("*.json")):
        if path.name.startswith("_"):
            continue
        yield path, path.read_bytes()


def timeframe_start_ms(timestamp_ms: int, timeframe: str) -> int:
    minutes = TIMEFRAMES_MINUTES[timeframe]
    width = minutes * 60_000
    return timestamp_ms - timestamp_ms % width


def _basis_price(tick: Tick, basis: str) -> float:
    if basis == "Bid":
        return tick.bid
    if basis == "Ask":
        return tick.ask
    if basis == "Mid":
        return (tick.bid + tick.ask) / 2.0
    raise ValueError(f"unknown basis: {basis}")


def aggregate_bars(ticks: Iterable[Tick], timeframe: str, basis: str) -> list[dict[str, Any]]:
    bars: dict[int, dict[str, Any]] = {}
    for tick in ticks:
        start = timeframe_start_ms(tick.timestamp_ms, timeframe)
        price = _basis_price(tick, basis)
        volume = tick.bid_volume if basis == "Bid" else tick.ask_volume if basis == "Ask" else (tick.bid_volume + tick.ask_volume) / 2.0
        bar = bars.get(start)
        if bar is None:
            bars[start] = {
                "timestamp_ms": start, "open": price, "high": price, "low": price, "close": price,
                "volume": volume, "tick_count": 1,
            }
        else:
            bar["high"] = max(bar["high"], price)
            bar["low"] = min(bar["low"], price)
            bar["close"] = price
            bar["volume"] += volume
            bar["tick_count"] += 1
    return [bars[key] for key in sorted(bars)]


def _update_bar_maps_vectorized(
    ticks: Sequence[Tick],
    bar_maps: dict[tuple[str, str], dict[int, dict[str, Any]]],
) -> None:
    if not ticks:
        return
    import numpy as np

    timestamps = np.fromiter((tick.timestamp_ms for tick in ticks), dtype=np.int64, count=len(ticks))
    bids = np.fromiter((tick.bid for tick in ticks), dtype=np.float64, count=len(ticks))
    asks = np.fromiter((tick.ask for tick in ticks), dtype=np.float64, count=len(ticks))
    bid_volumes = np.fromiter((tick.bid_volume for tick in ticks), dtype=np.float64, count=len(ticks))
    ask_volumes = np.fromiter((tick.ask_volume for tick in ticks), dtype=np.float64, count=len(ticks))
    series = {
        "Bid": (bids, bid_volumes),
        "Ask": (asks, ask_volumes),
        "Mid": ((bids + asks) / 2.0, (bid_volumes + ask_volumes) / 2.0),
    }
    for timeframe, minutes in TIMEFRAMES_MINUTES.items():
        width = minutes * 60_000
        starts = timestamps - timestamps % width
        boundaries = np.flatnonzero(np.r_[True, starts[1:] != starts[:-1]])
        ends = np.r_[boundaries[1:] - 1, len(starts) - 1]
        counts = ends - boundaries + 1
        for basis, (prices, volumes) in series.items():
            highs = np.maximum.reduceat(prices, boundaries)
            lows = np.minimum.reduceat(prices, boundaries)
            volume_sums = np.add.reduceat(volumes, boundaries)
            target = bar_maps[(basis, timeframe)]
            for index, boundary in enumerate(boundaries):
                start = int(starts[boundary])
                incoming = {
                    "timestamp_ms": start,
                    "open": float(prices[boundary]),
                    "high": float(highs[index]),
                    "low": float(lows[index]),
                    "close": float(prices[ends[index]]),
                    "volume": float(volume_sums[index]),
                    "tick_count": int(counts[index]),
                }
                existing = target.get(start)
                if existing is None:
                    target[start] = incoming
                else:
                    existing["high"] = max(existing["high"], incoming["high"])
                    existing["low"] = min(existing["low"], incoming["low"])
                    existing["close"] = incoming["close"]
                    existing["volume"] += incoming["volume"]
                    existing["tick_count"] += incoming["tick_count"]


def _require_pyarrow():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise FoundationError("pyarrow is required for deterministic Parquet Zstd output") from exc
    return pa, pq


def normalized_schema():
    pa, _ = _require_pyarrow()
    return pa.schema([
        ("timestamp_utc", pa.timestamp("ms", tz="UTC")), ("timestamp_ms", pa.int64()),
        ("bid", pa.float64()), ("ask", pa.float64()), ("spread", pa.float64()),
        ("bid_volume", pa.float64()), ("ask_volume", pa.float64()),
        ("source_file_id", pa.string()), ("source_row_index", pa.int32()),
    ])


def bar_schema():
    pa, _ = _require_pyarrow()
    return pa.schema([
        ("timestamp_utc", pa.timestamp("ms", tz="UTC")), ("timestamp_ms", pa.int64()),
        ("open", pa.float64()), ("high", pa.float64()), ("low", pa.float64()), ("close", pa.float64()),
        ("volume", pa.float64()), ("tick_count", pa.int64()),
    ])


def _write_table_deterministic(path: Path, table: Any, schema: Any) -> None:
    _, pq = _require_pyarrow()
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table.cast(schema), path, compression="zstd", compression_level=9, use_dictionary=False,
        write_statistics=True, data_page_version="1.0", row_group_size=100_000,
    )


def normalize_month(storage_root: Path, run_root: Path, symbol: str, year: int, month: int) -> dict[str, Any]:
    validate_month_acquisition_manifest(storage_root, symbol, year, month)
    pa, pq = _require_pyarrow()
    schema = normalized_schema()
    target = run_root / "normalized" / symbol / f"year={year:04d}" / f"month={month:02d}" / "ticks.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    writer = pq.ParquetWriter(target, schema, compression="zstd", compression_level=9, use_dictionary=False, write_statistics=True, data_page_version="1.0")
    tick_count = 0
    first_ms: int | None = None
    last_ms: int | None = None
    duplicate_count = 0
    conflicting_timestamp_count = 0
    current_duplicate_timestamp: int | None = None
    current_timestamp_signatures: set[tuple[float, float, float, float]] = set()
    spread_counts: dict[float, int] = defaultdict(int)
    spread_sum = 0.0
    spread_observations = 0
    gaps_over_60s = 0
    longest_gap_ms = 0
    bar_maps: dict[tuple[str, str], dict[int, dict[str, Any]]] = {
        (basis, timeframe): {} for basis in PRICE_BASES for timeframe in TIMEFRAMES_MINUTES
    }
    try:
        for raw_path, raw in iter_raw_month(storage_root, symbol, year, month):
            ticks = decode_payload(raw, symbol, raw_path.stem)
            if not ticks:
                continue
            rows = [tick.as_row() for tick in ticks]
            table = pa.Table.from_pylist(rows, schema=schema)
            writer.write_table(table, row_group_size=100_000)
            for tick in ticks:
                signature = (tick.bid, tick.ask, tick.bid_volume, tick.ask_volume)
                if current_duplicate_timestamp != tick.timestamp_ms:
                    current_duplicate_timestamp = tick.timestamp_ms
                    current_timestamp_signatures.clear()
                elif current_timestamp_signatures and signature not in current_timestamp_signatures:
                    conflicting_timestamp_count += 1
                if signature in current_timestamp_signatures:
                    duplicate_count += 1
                current_timestamp_signatures.add(signature)
                if last_ms is not None:
                    gap = tick.timestamp_ms - last_ms
                    if gap > 60_000:
                        gaps_over_60s += 1
                    longest_gap_ms = max(longest_gap_ms, gap)
                first_ms = tick.timestamp_ms if first_ms is None else first_ms
                last_ms = tick.timestamp_ms
                spread_key = round(tick.spread, int(INSTRUMENTS[symbol]["price_scale"]))
                spread_counts[spread_key] += 1
                spread_sum += tick.spread
                spread_observations += 1
            tick_count += len(ticks)
            _update_bar_maps_vectorized(ticks, bar_maps)
    finally:
        writer.close()
    bar_rows: list[dict[str, Any]] = []
    for basis in PRICE_BASES:
        for timeframe in TIMEFRAMES_MINUTES:
            bar_map = bar_maps[(basis, timeframe)]
            bars = [bar_map[key] for key in sorted(bar_map)]
            output = run_root / "bars" / symbol / basis.lower() / timeframe / f"year={year:04d}" / f"month={month:02d}" / "bars.parquet"
            table_rows = [{**bar, "timestamp_utc": datetime.fromtimestamp(bar["timestamp_ms"] / 1000, UTC)} for bar in bars]
            table = pa.Table.from_pylist(table_rows, schema=bar_schema())
            _write_table_deterministic(output, table, bar_schema())
            bar_rows.append({
                "symbol": symbol, "month": f"{year:04d}-{month:02d}", "basis": basis, "timeframe": timeframe,
                "bar_count": len(bars), "first_bar_utc": iso_utc(table_rows[0]["timestamp_utc"]) if bars else "",
                "last_bar_utc": iso_utc(table_rows[-1]["timestamp_utc"]) if bars else "",
                "path": str(output.relative_to(run_root)).replace("\\", "/"), "bytes": output.stat().st_size,
                "sha256": sha256_file(output),
            })
    def percentile(q: float) -> float | None:
        if not spread_observations:
            return None
        target = int((spread_observations - 1) * q)
        cumulative = 0
        for value, count in sorted(spread_counts.items()):
            cumulative += count
            if cumulative > target:
                return value
        return max(spread_counts)
    return {
        "partition": {
            "symbol": symbol, "month": f"{year:04d}-{month:02d}", "tick_count": tick_count,
            "first_tick_utc": iso_utc(datetime.fromtimestamp(first_ms / 1000, UTC)) if first_ms is not None else "",
            "last_tick_utc": iso_utc(datetime.fromtimestamp(last_ms / 1000, UTC)) if last_ms is not None else "",
            "path": str(target.relative_to(run_root)).replace("\\", "/"), "bytes": target.stat().st_size,
            "sha256": sha256_file(target), "compression": "zstd", "row_order": "timestamp_then_source_order",
        },
        "integrity": {
            "symbol": symbol, "month": f"{year:04d}-{month:02d}", "tick_count": tick_count,
            "exact_duplicate_count": duplicate_count, "conflicting_same_timestamp_count": conflicting_timestamp_count,
            "negative_spread_count": sum(count for value, count in spread_counts.items() if value < 0),
            "zero_spread_count": spread_counts.get(0.0, 0),
            "gaps_over_60s": gaps_over_60s, "longest_gap_ms": longest_gap_ms,
        },
        "spread": {
            "symbol": symbol, "month": f"{year:04d}-{month:02d}", "observations": spread_observations,
            "min": min(spread_counts) if spread_counts else "", "mean": spread_sum / spread_observations if spread_observations else "",
            "p50": percentile(0.50) if spread_counts else "", "p95": percentile(0.95) if spread_counts else "",
            "max": max(spread_counts) if spread_counts else "",
        },
        "bars": bar_rows,
    }


def compare_run_hashes(run_one: Path, run_two: Path) -> dict[str, Any]:
    def inventory(root: Path) -> dict[str, str]:
        return {
            str(path.relative_to(root)).replace("\\", "/"): sha256_file(path)
            for path in sorted(root.rglob("*.parquet"))
        }
    left = inventory(run_one)
    right = inventory(run_two)
    paths = sorted(set(left) | set(right))
    mismatches = [{"path": path, "run_one": left.get(path, ""), "run_two": right.get(path, "")} for path in paths if left.get(path) != right.get(path)]
    return {
        "identical": not mismatches, "file_count_run_one": len(left), "file_count_run_two": len(right),
        "mismatch_count": len(mismatches), "mismatches": mismatches,
        "run_one_inventory_sha256": sha256_bytes(canonical_json_bytes(left)),
        "run_two_inventory_sha256": sha256_bytes(canonical_json_bytes(right)),
    }


def classify(source_schema_established: bool, material_integrity_failure: bool, complete_months: int, expected_months: int, deterministic: bool) -> str:
    if not source_schema_established or material_integrity_failure or not deterministic:
        return "INVALID"
    if complete_months < expected_months:
        return "PARTIAL_NOT_READY"
    return "READY"


def git_value(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo_root), *args], text=True).strip()


def assert_no_forbidden_output_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in FORBIDDEN_FIELDS:
                raise FoundationError(f"strategy/account field is forbidden: {key}")
            assert_no_forbidden_output_fields(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_forbidden_output_fields(child)


def build_source_contract() -> dict[str, Any]:
    return {
        "phase": PHASE,
        "notices": [
            "OFFICIAL DUKASCOPY HISTORICAL DATA",
            "BID/ASK TICK DATA FOUNDATION",
            "NO STRATEGY SCORING",
            "NO DEPLOYMENT AUTHORIZATION",
        ],
        "authority": "Dukascopy Bank SA official Historical Data Export and JForex historical-tick documentation",
        "service_origin": OFFICIAL_ORIGIN,
        "widget": OFFICIAL_WIDGET,
        "history_tick_documentation": OFFICIAL_HISTORY_DOC,
        "endpoint_template": f"{OFFICIAL_ORIGIN}/ticks/{{source_code}}/{{year}}/{{month}}/{{day}}/{{hour}}",
        "instrument_endpoint_template": f"{OFFICIAL_ORIGIN}/instruments/{{source_code}}",
        "raw_format": "hourly JSON response preserved byte-for-byte",
        "raw_schema": {
            "timestamp": "base Unix epoch milliseconds",
            "multiplier": "price delta multiplier",
            "bid": "base best bid",
            "ask": "base best ask",
            "times": "cumulative timestamp deltas in milliseconds",
            "bids": "cumulative best-bid price deltas",
            "asks": "cumulative best-ask price deltas",
            "bidVolumes": "best-bid volumes by source order",
            "askVolumes": "best-ask volumes by source order",
        },
        "decoder": "timestamp += times[i]; bid/ask += side_delta[i] * multiplier; preserve source array order",
        "timestamp_semantics": "Unix epoch milliseconds interpreted in UTC; requested hourly partitions are [hour, hour+1h)",
        "timezone": "UTC",
        "duplicate_policy": "preserve all source rows; report exact and same-timestamp conflicts; never silently deduplicate",
        "volume_semantics": "best-side quote volume from Dukascopy bidVolumes/askVolumes arrays; no invented trade volume",
        "spread_semantics": "ask - bid from the same source tick",
        "price_bases": {"Bid": "best bid", "Ask": "best ask", "Mid": "(bid + ask) / 2"},
        "bar_boundaries": "UTC epoch-aligned [start,end) intervals; D1 starts 00:00 UTC; H4 starts 00/04/08/12/16/20 UTC",
        "period_start": iso_utc(START_UTC),
        "period_end": iso_utc(END_UTC),
        "partitioning": "symbol/year/month with raw hourly response files inside each resumable monthly partition",
        "retry_policy": "one retry only after a missing, corrupt, non-200, or structurally incomplete response",
        "concurrency_limit": MAX_CONCURRENCY,
        "normalized_format": "Parquet with Zstandard compression and deterministic source order",
        "required_storage_environment_variable": STORAGE_ENV,
        "instruments": INSTRUMENTS,
        "timeframes": list(TIMEFRAMES_MINUTES),
    }
