from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_ROOT = Path(
    "D:/AlgoTradingData/research/"
    "eurusd-neutral-coinbase-stablecoin-eur-v1"
)
BASE_URL = "https://api.exchange.coinbase.com"
PRODUCTS = ("USDC-EUR", "USDT-EUR")
GRANULARITY_SECONDS = 300
FIRST_DATE = "2022-01-01"
LAST_DATE = "2026-06-30"
WINDOW_LEAD_MINUTES = 15
WINDOW_END_MINUTES = 45
EXPECTED_BARS_PER_DATE = 12
CANDLE_COLUMNS = [
    "open_time_epoch",
    "low",
    "high",
    "open",
    "close",
    "base_volume",
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


def eligible_dates(
    start_date: str = FIRST_DATE,
    end_date: str = LAST_DATE,
) -> list[str]:
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    from eurusd_regime_specialists.neutral_binance_eurusdt_flow import (
        load_parent_points,
    )

    points = load_parent_points(include_outcomes=False)
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    dates = (
        points[
            points["entry_time_utc"].ge(start)
            & points["entry_time_utc"].lt(end)
        ]["eligible_date"]
        .drop_duplicates()
        .sort_values()
    )
    return dates.tolist()


def date_window(date: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    midnight = pd.Timestamp(date, tz="UTC")
    return (
        midnight - pd.Timedelta(minutes=WINDOW_LEAD_MINUTES),
        midnight + pd.Timedelta(minutes=WINDOW_END_MINUTES),
    )


def candle_url(product: str, date: str) -> str:
    start, end = date_window(date)
    query = urllib.parse.urlencode(
        {
            "granularity": GRANULARITY_SECONDS,
            "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    return f"{BASE_URL}/products/{product}/candles?{query}"


def product_url(product: str) -> str:
    return f"{BASE_URL}/products/{product}"


def fetch_bytes(
    url: str,
    *,
    maximum_attempts: int = 7,
) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
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
                    "date": response.headers.get("Date", ""),
                    "content_type": response.headers.get(
                        "Content-Type", ""
                    ),
                    "cache_control": response.headers.get(
                        "Cache-Control", ""
                    ),
                }
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt == maximum_attempts:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = (
                float(retry_after)
                if retry_after is not None
                else min(2**attempt, 30)
            )
            time.sleep(delay)
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
        ) as exc:
            last_error = exc
            if attempt < maximum_attempts:
                time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"Unable to download {url}") from last_error


def parse_product(payload: bytes, expected: str) -> dict[str, Any]:
    decoded = json.loads(payload)
    required = {
        "id",
        "base_currency",
        "quote_currency",
        "quote_increment",
        "base_increment",
        "status",
    }
    if not isinstance(decoded, dict) or not required.issubset(decoded):
        raise RuntimeError("Unexpected Coinbase product schema")
    if decoded["id"] != expected:
        raise RuntimeError(
            f"Coinbase product mismatch: {decoded['id']!r} != {expected!r}"
        )
    return decoded


def parse_candles(
    payload: bytes,
    product: str,
    date: str,
) -> pd.DataFrame:
    decoded = json.loads(payload)
    if not isinstance(decoded, list):
        raise RuntimeError("Unexpected Coinbase candle response schema")
    if any(
        not isinstance(row, list) or len(row) != len(CANDLE_COLUMNS)
        for row in decoded
    ):
        raise RuntimeError("Unexpected Coinbase candle row schema")
    if not decoded:
        return pd.DataFrame(
            columns=[
                "product",
                "eligible_date",
                "open_time_utc",
                "close_time_utc",
                "open",
                "high",
                "low",
                "close",
                "base_volume",
            ]
        )
    frame = pd.DataFrame(decoded, columns=CANDLE_COLUMNS)
    numeric = CANDLE_COLUMNS
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["open_time_utc"] = pd.to_datetime(
        frame["open_time_epoch"], unit="s", utc=True
    )
    frame["close_time_utc"] = (
        frame["open_time_utc"]
        + pd.Timedelta(seconds=GRANULARITY_SECONDS)
    )
    start, end = date_window(date)
    frame = frame[
        frame["open_time_utc"].ge(start)
        & frame["open_time_utc"].lt(end)
    ].copy()
    frame["product"] = product
    frame["eligible_date"] = date
    columns = [
        "product",
        "eligible_date",
        "open_time_utc",
        "close_time_utc",
        "open",
        "high",
        "low",
        "close",
        "base_volume",
    ]
    frame = frame[columns].sort_values("open_time_utc")
    if frame["open_time_utc"].duplicated().any():
        raise RuntimeError(f"Duplicate Coinbase candle: {product} {date}")
    if (
        frame[["open", "high", "low", "close"]].le(0).any().any()
        or frame["base_volume"].lt(0).any()
    ):
        raise RuntimeError(
            f"Invalid Coinbase candle price/volume: {product} {date}"
        )
    if (
        frame["high"].lt(frame[["open", "close", "low"]].max(axis=1)).any()
        or frame["low"].gt(frame[["open", "close", "high"]].min(axis=1)).any()
    ):
        raise RuntimeError(f"Invalid Coinbase OHLC: {product} {date}")
    return frame.reset_index(drop=True)


def acquire_payload(
    url: str,
    path: Path,
    *,
    force: bool,
) -> tuple[bytes, dict[str, Any]]:
    if path.exists() and not force:
        payload = path.read_bytes()
        return payload, {
            "url": url,
            "path": path.as_posix(),
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
            "from_cache": True,
            "response_headers": {},
        }
    payload, headers = fetch_bytes(url)
    atomic_write(path, payload)
    return payload, {
        "url": url,
        "path": path.as_posix(),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "from_cache": False,
        "response_headers": headers,
    }


def acquire(
    output_root: Path,
    *,
    force: bool,
    delay_seconds: float,
) -> dict[str, Any]:
    raw_root = output_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    dates = eligible_dates()
    product_records: dict[str, Any] = {}
    raw_records: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []

    for product in PRODUCTS:
        payload, record = acquire_payload(
            product_url(product),
            raw_root / product / "PRODUCT.json",
            force=force,
        )
        metadata = parse_product(payload, product)
        record["metadata"] = {
            key: metadata.get(key)
            for key in (
                "id",
                "base_currency",
                "quote_currency",
                "quote_increment",
                "base_increment",
                "status",
                "trading_disabled",
                "fx_stablecoin",
            )
        }
        product_records[product] = record
        if not record["from_cache"]:
            time.sleep(delay_seconds)

    total = len(PRODUCTS) * len(dates)
    completed = 0
    for date in dates:
        for product in PRODUCTS:
            url = candle_url(product, date)
            path = raw_root / product / f"{date}.json"
            payload, record = acquire_payload(
                url, path, force=force
            )
            frame = parse_candles(payload, product, date)
            record.update(
                {
                    "product": product,
                    "eligible_date": date,
                    "parsed_bars": int(len(frame)),
                }
            )
            raw_records.append(record)
            frames.append(frame)
            completed += 1
            if not record["from_cache"]:
                time.sleep(delay_seconds)
        if completed % 50 == 0 or completed == total:
            print(
                f"Coinbase stablecoin/EUR acquisition "
                f"{completed}/{total}",
                flush=True,
            )

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(
        ["product", "open_time_utc"]
    ).reset_index(drop=True)
    duplicates = combined.duplicated(["product", "open_time_utc"])
    if duplicates.any():
        raise RuntimeError(
            f"Duplicate normalized Coinbase rows: {int(duplicates.sum())}"
        )

    output_root.mkdir(parents=True, exist_ok=True)
    parquet_path = (
        output_root / "COINBASE_STABLECOIN_EUR_M5.parquet"
    )
    combined.to_parquet(
        parquet_path, index=False, compression="zstd"
    )

    required_index = {
        date: pd.date_range(
            *date_window(date),
            freq="5min",
            inclusive="left",
        )
        for date in dates
    }
    coverage: dict[str, Any] = {}
    complete_by_product: dict[str, set[str]] = {}
    for product in PRODUCTS:
        product_frame = combined[combined["product"].eq(product)]
        complete: set[str] = set()
        missing_bars = 0
        zero_volume = 0
        for date in dates:
            subset = product_frame[
                product_frame["eligible_date"].eq(date)
            ]
            actual = pd.DatetimeIndex(subset["open_time_utc"])
            missing = required_index[date].difference(actual)
            missing_bars += len(missing)
            zero_volume += int(subset["base_volume"].eq(0).sum())
            if (
                len(missing) == 0
                and len(subset) == EXPECTED_BARS_PER_DATE
                and subset["base_volume"].gt(0).all()
            ):
                complete.add(date)
        complete_by_product[product] = complete
        coverage[product] = {
            "normalized_rows": int(len(product_frame)),
            "complete_twelve_bar_dates_positive_volume": int(
                len(complete)
            ),
            "missing_required_m5_bars": int(missing_bars),
            "zero_volume_bars": int(zero_volume),
            "first_open_utc": (
                product_frame["open_time_utc"].min().isoformat()
                if len(product_frame)
                else None
            ),
            "last_open_utc": (
                product_frame["open_time_utc"].max().isoformat()
                if len(product_frame)
                else None
            ),
        }
    both_complete = set(dates)
    for complete in complete_by_product.values():
        both_complete &= complete

    downloaded_requests = int(
        sum(not record["from_cache"] for record in raw_records)
    )
    cached_requests = int(
        sum(record["from_cache"] for record in raw_records)
    )
    raw_chain = hashlib.sha256()
    for record in sorted(
        raw_records,
        key=lambda value: (
            value["product"],
            value["eligible_date"],
        ),
    ):
        raw_chain.update(bytes.fromhex(record["sha256"]))
    product_chain = hashlib.sha256()
    for product in PRODUCTS:
        product_chain.update(
            bytes.fromhex(product_records[product]["sha256"])
        )

    manifest = {
        "source": "Coinbase Exchange public REST product candles",
        "documentation": (
            "https://docs.cdp.coinbase.com/api-reference/"
            "exchange-api/rest-api/products/get-product-candles"
        ),
        "authentication_required": False,
        "base_url": BASE_URL,
        "products": list(PRODUCTS),
        "granularity_seconds": GRANULARITY_SECONDS,
        "candle_schema": CANDLE_COLUMNS,
        "caveat": (
            "Coinbase documents that historical rates can be incomplete "
            "and omits intervals with no ticks; no gap is filled here."
        ),
        "eligible_dates": len(dates),
        "first_eligible_date": min(dates),
        "last_eligible_date": max(dates),
        "requests": len(raw_records),
        "raw_response_chain_sha256": raw_chain.hexdigest(),
        "product_metadata_chain_sha256": product_chain.hexdigest(),
        "coverage": coverage,
        "both_products_complete_positive_volume_dates": int(
            len(both_complete)
        ),
        "both_products_complete_date_list_sha256": sha256_bytes(
            "\n".join(sorted(both_complete)).encode("utf-8")
        ),
        "normalized_rows": int(len(combined)),
        "parquet_path": parquet_path.as_posix(),
        "parquet_bytes": parquet_path.stat().st_size,
        "parquet_sha256": sha256_file(parquet_path),
        "product_metadata": {
            product: {
                key: product_records[product][key]
                for key in (
                    "url",
                    "path",
                    "bytes",
                    "sha256",
                    "metadata",
                )
            }
            for product in PRODUCTS
        },
        "raw_responses": [
            {
                key: record[key]
                for key in (
                    "url",
                    "path",
                    "bytes",
                    "sha256",
                    "product",
                    "eligible_date",
                    "parsed_bars",
                )
            }
            for record in raw_records
        ],
    }
    manifest_path = output_root / "MANIFEST.json"
    atomic_write(
        manifest_path,
        json.dumps(manifest, indent=2).encode("utf-8"),
    )
    return {
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": sha256_file(manifest_path),
        **{
            key: manifest[key]
            for key in (
                "eligible_dates",
                "requests",
                "raw_response_chain_sha256",
                "coverage",
                "both_products_complete_positive_volume_dates",
                "normalized_rows",
                "parquet_path",
                "parquet_bytes",
                "parquet_sha256",
            )
        },
        "downloaded_requests": downloaded_requests,
        "cached_requests": cached_requests,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        nargs="?",
        choices=("download", "rebuild"),
        default="download",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--delay-seconds", type=float, default=0.13)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.delay_seconds < 0:
        raise ValueError("Delay must be nonnegative")
    if args.command == "rebuild":
        expected = len(PRODUCTS) * len(eligible_dates())
        raw_count = sum(
            len(list((args.root / "raw" / product).glob("*.json")))
            - int((args.root / "raw" / product / "PRODUCT.json").exists())
            for product in PRODUCTS
        )
        if raw_count != expected:
            raise RuntimeError(
                f"Cache incomplete: {raw_count} != {expected}"
            )
    result = acquire(
        args.root,
        force=args.force,
        delay_seconds=args.delay_seconds,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
