from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_ROOT = Path(
    "D:/AlgoTradingData/research/"
    "eurusd-neutral-binance-eurusdt-flow-v1"
)
SYMBOL = "EURUSDT"
INTERVAL = "5m"
BASE_URL = "https://data.binance.vision/data/spot/monthly/klines"
KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "base_volume",
    "close_time",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "ignore",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def months_inclusive(
    start_month: str,
    end_month: str,
) -> list[str]:
    periods = pd.period_range(start_month, end_month, freq="M")
    if periods.empty:
        raise ValueError("No months requested")
    return [str(value) for value in periods]


def archive_name(month: str) -> str:
    return f"{SYMBOL}-{INTERVAL}-{month}.zip"


def archive_url(month: str) -> str:
    name = archive_name(month)
    return f"{BASE_URL}/{SYMBOL}/{INTERVAL}/{name}"


def fetch_bytes(
    url: str,
    *,
    maximum_attempts: int = 5,
) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "*/*",
            "User-Agent": "EURUSD-causal-research/1.0",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, maximum_attempts + 1):
        try:
            with urllib.request.urlopen(
                request, timeout=60
            ) as response:
                return response.read(), {
                    "etag": response.headers.get("ETag", ""),
                    "last_modified": response.headers.get(
                        "Last-Modified", ""
                    ),
                    "content_type": response.headers.get(
                        "Content-Type", ""
                    ),
                }
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
        ) as exc:
            last_error = exc
            if attempt < maximum_attempts:
                time.sleep(min(2**attempt, 20))
    raise RuntimeError(f"Unable to download {url}") from last_error


def expected_checksum(payload: bytes, expected_name: str) -> str:
    text = payload.decode("utf-8").strip()
    fields = text.split()
    if len(fields) < 2:
        raise RuntimeError("Unexpected Binance checksum schema")
    digest = fields[0].lower()
    name = fields[-1].lstrip("*")
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise RuntimeError("Invalid SHA-256 in Binance checksum")
    if Path(name).name != expected_name:
        raise RuntimeError(
            f"Checksum name mismatch: {name!r} != {expected_name!r}"
        )
    return digest


def acquire_month(
    month: str,
    raw_root: Path,
    *,
    force: bool,
) -> dict[str, Any]:
    name = archive_name(month)
    url = archive_url(month)
    checksum_url = f"{url}.CHECKSUM"
    checksum_payload, checksum_headers = fetch_bytes(checksum_url)
    expected = expected_checksum(checksum_payload, name)
    archive_path = raw_root / name
    checksum_path = raw_root / f"{name}.CHECKSUM"
    cached = archive_path.exists() and not force
    if cached:
        actual = sha256_file(archive_path)
        if actual != expected:
            raise RuntimeError(
                f"Cached checksum mismatch for {archive_path}"
            )
        archive_headers: dict[str, str] = {}
    else:
        payload, archive_headers = fetch_bytes(url)
        actual = sha256_bytes(payload)
        if actual != expected:
            raise RuntimeError(
                f"Downloaded checksum mismatch for {name}: "
                f"{actual} != {expected}"
            )
        atomic_write(archive_path, payload)
    atomic_write(checksum_path, checksum_payload)
    return {
        "month": month,
        "archive_url": url,
        "checksum_url": checksum_url,
        "archive_path": str(archive_path),
        "checksum_path": str(checksum_path),
        "bytes": archive_path.stat().st_size,
        "sha256": expected,
        "cached": cached,
        "archive_headers": archive_headers,
        "checksum_headers": checksum_headers,
    }


def _timestamp_unit(values: pd.Series) -> str:
    numeric = pd.to_numeric(values, errors="raise").astype("int64")
    median = int(numeric.median())
    if median >= 100_000_000_000_000:
        return "us"
    if median >= 100_000_000_000:
        return "ms"
    raise RuntimeError(f"Unexpected Binance timestamp magnitude {median}")


def parse_archive(
    path: Path,
    month: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        csv_names = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv")
        ]
        if len(csv_names) != 1:
            raise RuntimeError(
                f"Expected one CSV in {path}, found {csv_names!r}"
            )
        raw = archive.read(csv_names[0])
    frame = pd.read_csv(
        io.BytesIO(raw),
        header=None,
        names=KLINE_COLUMNS,
        dtype=str,
    )
    numeric_open_time = pd.to_numeric(
        frame["open_time"], errors="coerce"
    )
    if numeric_open_time.isna().iloc[0]:
        frame = frame.iloc[1:].reset_index(drop=True)
    unit = _timestamp_unit(frame["open_time"])
    close_unit = _timestamp_unit(frame["close_time"])
    if close_unit != unit:
        raise RuntimeError(f"Mixed timestamp units in {path}")
    frame["open_time_utc"] = pd.to_datetime(
        pd.to_numeric(frame["open_time"], errors="raise"),
        unit=unit,
        utc=True,
    )
    frame["close_time_utc"] = pd.to_datetime(
        pd.to_numeric(frame["close_time"], errors="raise"),
        unit=unit,
        utc=True,
    )
    number_columns = [
        "open",
        "high",
        "low",
        "close",
        "base_volume",
        "quote_volume",
        "trade_count",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ]
    for column in number_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if frame["open_time_utc"].duplicated().any():
        raise RuntimeError(f"Duplicate timestamps in {path}")
    if not (
        frame["open_time_utc"].dt.minute.mod(5).eq(0)
        & frame["open_time_utc"].dt.second.eq(0)
    ).all():
        raise RuntimeError(f"Unaligned 5-minute timestamps in {path}")
    if not (
        frame["high"].ge(frame[["open", "close"]].max(axis=1))
        & frame["low"].le(frame[["open", "close"]].min(axis=1))
        & frame["low"].gt(0)
    ).all():
        raise RuntimeError(f"Invalid price geometry in {path}")
    if not (
        frame["quote_volume"].ge(0)
        & frame["taker_buy_quote_volume"].ge(0)
        & frame["taker_buy_quote_volume"].le(
            frame["quote_volume"] + 1e-8
        )
        & frame["trade_count"].ge(0)
    ).all():
        raise RuntimeError(f"Invalid executed-flow fields in {path}")
    frame["taker_sell_quote_volume"] = (
        frame["quote_volume"] - frame["taker_buy_quote_volume"]
    )
    frame["taker_imbalance"] = np.where(
        frame["quote_volume"].gt(0),
        (
            2.0 * frame["taker_buy_quote_volume"]
            - frame["quote_volume"]
        )
        / frame["quote_volume"],
        0.0,
    )
    frame["source_month"] = month
    output_columns = [
        "open_time_utc",
        "close_time_utc",
        "open",
        "high",
        "low",
        "close",
        "base_volume",
        "quote_volume",
        "trade_count",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "taker_sell_quote_volume",
        "taker_imbalance",
        "source_month",
    ]
    output = frame[output_columns].sort_values(
        "open_time_utc"
    ).reset_index(drop=True)
    return output, {
        "month": month,
        "rows": int(len(output)),
        "timestamp_unit": unit,
        "first_open_utc": output["open_time_utc"].min().isoformat(),
        "last_open_utc": output["open_time_utc"].max().isoformat(),
        "zero_quote_volume_rows": int(
            output["quote_volume"].eq(0).sum()
        ),
    }


def acquire(
    output_root: Path,
    start_month: str,
    end_month: str,
    *,
    force: bool,
    workers: int,
) -> dict[str, Any]:
    raw_root = output_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    months = months_inclusive(start_month, end_month)
    downloads: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {
            pool.submit(
                acquire_month,
                month,
                raw_root,
                force=force,
            ): month
            for month in months
        }
        for future in as_completed(futures):
            month = futures[future]
            downloads[month] = future.result()
    frames: list[pd.DataFrame] = []
    parse_manifests: dict[str, dict[str, Any]] = {}
    for month in months:
        archive_path = Path(downloads[month]["archive_path"])
        frame, parse_manifest = parse_archive(archive_path, month)
        frames.append(frame)
        parse_manifests[month] = parse_manifest
    source = (
        pd.concat(frames, ignore_index=True)
        .sort_values("open_time_utc")
        .reset_index(drop=True)
    )
    if source["open_time_utc"].duplicated().any():
        duplicates = int(source["open_time_utc"].duplicated().sum())
        raise RuntimeError(
            f"Cross-archive duplicate timestamps: {duplicates}"
        )
    expected_index = pd.date_range(
        source["open_time_utc"].min(),
        source["open_time_utc"].max(),
        freq="5min",
    )
    actual_index = pd.DatetimeIndex(source["open_time_utc"])
    missing = expected_index.difference(actual_index)
    parquet_path = output_root / "EURUSDT_5M_EXECUTED_FLOW.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    source.to_parquet(parquet_path, index=False, compression="zstd")
    chain = hashlib.sha256()
    for month in months:
        chain.update(bytes.fromhex(downloads[month]["sha256"]))
    unit_counts: dict[str, int] = {}
    for manifest in parse_manifests.values():
        unit = manifest["timestamp_unit"]
        unit_counts[unit] = unit_counts.get(unit, 0) + 1
    manifest = {
        "source": "Binance official public market-data archive",
        "documentation": (
            "https://github.com/binance/binance-public-data"
        ),
        "authentication_required": False,
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "start_month": start_month,
        "end_month": end_month,
        "archive_files": len(months),
        "archive_chain_sha256": chain.hexdigest(),
        "downloads": [downloads[month] for month in months],
        "parsing": [parse_manifests[month] for month in months],
        "timestamp_unit_archive_counts": unit_counts,
        "rows": int(len(source)),
        "first_open_utc": source["open_time_utc"].min().isoformat(),
        "last_open_utc": source["open_time_utc"].max().isoformat(),
        "missing_five_minute_bars": int(len(missing)),
        "first_missing_open_utc": (
            missing[0].isoformat() if len(missing) else None
        ),
        "zero_quote_volume_rows": int(
            source["quote_volume"].eq(0).sum()
        ),
        "normalized_path": str(parquet_path),
        "normalized_bytes": parquet_path.stat().st_size,
        "normalized_sha256": sha256_file(parquet_path),
    }
    manifest_path = output_root / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_ROOT,
    )
    parser.add_argument("--start-month", default="2020-01")
    parser.add_argument("--end-month", default="2026-06")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = acquire(
        args.output_root,
        args.start_month,
        args.end_month,
        force=bool(args.force),
        workers=int(args.workers),
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
