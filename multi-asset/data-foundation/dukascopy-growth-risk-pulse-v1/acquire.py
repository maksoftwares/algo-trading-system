from __future__ import annotations

import argparse
import calendar
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from src.foundation import (
    canonical_json,
    deterministic_gzip,
    raw_hour_path,
    read_stored_hour,
    sha256_bytes,
    sha256_file,
    validate_hour_payload,
    write_json,
)


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "dukascopy_growth_risk_pulse_v1.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def month_keys(start: datetime, end_exclusive: datetime) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    cursor = datetime(start.year, start.month, 1, tzinfo=UTC)
    while cursor < end_exclusive:
        result.append((cursor.year, cursor.month))
        cursor = datetime(
            cursor.year + int(cursor.month == 12),
            1 if cursor.month == 12 else cursor.month + 1,
            1,
            tzinfo=UTC,
        )
    return result


def hours_in_month(year: int, month: int) -> list[datetime]:
    start = datetime(year, month, 1, tzinfo=UTC)
    return [
        start + timedelta(hours=index)
        for index in range(calendar.monthrange(year, month)[1] * 24)
    ]


def instrument_map() -> dict[str, dict[str, object]]:
    return {str(item["symbol"]): item for item in CONFIG["instruments"]}


def official_tick_url(spec: dict[str, object], hour: datetime) -> str:
    code = str(spec["source_code"])
    return (
        f"{CONFIG['official_origin']}/ticks/{code}/"
        f"{hour.year}/{hour.month}/{hour.day}/{hour.hour}"
    )


def freeze_instrument_metadata(
    root: Path, spec: dict[str, object], client: httpx.Client
) -> dict[str, object]:
    symbol = str(spec["symbol"])
    code = str(spec["source_code"])
    url = f"{CONFIG['official_origin']}/instruments/{code}"
    response = client.get(url)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != code:
        raise ValueError(f"instrument metadata code mismatch for {symbol}")
    if int(payload.get("priceScale")) != int(spec["price_scale"]):
        raise ValueError(f"instrument metadata price scale mismatch for {symbol}")
    if float(payload.get("pipValue")) != float(spec["pip_size"]):
        raise ValueError(f"instrument metadata pip value mismatch for {symbol}")
    path = root / "metadata" / f"{symbol}.json"
    encoded = canonical_json(payload)
    if path.is_file() and path.read_bytes() != encoded:
        raise ValueError(f"instrument metadata changed for {symbol}")
    write_json(path, payload)
    return {
        "symbol": symbol,
        "url": url,
        "sha256": sha256_file(path),
        "path": str(path.relative_to(root)).replace("\\", "/"),
    }


def acquire_hour(
    root: Path,
    spec: dict[str, object],
    hour: datetime,
    client: httpx.Client,
) -> dict[str, object]:
    symbol = str(spec["symbol"])
    price_scale = int(spec["price_scale"])
    path = raw_hour_path(root, symbol, hour)
    path.parent.mkdir(parents=True, exist_ok=True)
    url = official_tick_url(spec, hour)
    relative = str(path.relative_to(root)).replace("\\", "/")
    file_id = f"{symbol}-{hour:%Y%m%d%H}"

    if path.is_file():
        try:
            raw, ticks = read_stored_hour(path, hour, price_scale)
            return {
                "symbol": symbol,
                "hour_utc": iso_utc(hour),
                "source_file_id": file_id,
                "url": url,
                "status": "RESUMED_VALID",
                "attempts": 0,
                "http_status": 200,
                "source_bytes": len(raw),
                "stored_bytes": path.stat().st_size,
                "source_sha256": sha256_bytes(raw),
                "stored_sha256": sha256_file(path),
                "tick_count": len(ticks),
                "path": relative,
            }
        except (OSError, ValueError):
            path.chmod(0o666)
            path.unlink()

    last_error = ""
    for attempt in (1, 2):
        try:
            response = client.get(url)
            if response.status_code != 200:
                raise ValueError(f"HTTP status {response.status_code}")
            raw = response.content
            ticks = validate_hour_payload(raw, hour, price_scale)
            stored = deterministic_gzip(raw)
            partial = path.with_suffix(".gz.part")
            partial.write_bytes(stored)
            os.replace(partial, path)
            return {
                "symbol": symbol,
                "hour_utc": iso_utc(hour),
                "source_file_id": file_id,
                "url": url,
                "status": "DOWNLOADED_VALID",
                "attempts": attempt,
                "http_status": response.status_code,
                "source_bytes": len(raw),
                "stored_bytes": len(stored),
                "source_sha256": sha256_bytes(raw),
                "stored_sha256": sha256_bytes(stored),
                "tick_count": len(ticks),
                "etag": response.headers.get("etag", ""),
                "last_modified": response.headers.get("last-modified", ""),
                "path": relative,
            }
        except Exception as exc:  # source and network failures are persisted
            last_error = f"{type(exc).__name__}: {exc}"
    return {
        "symbol": symbol,
        "hour_utc": iso_utc(hour),
        "source_file_id": file_id,
        "url": url,
        "status": "FAILED_AFTER_ONE_RETRY",
        "attempts": 2,
        "source_bytes": 0,
        "stored_bytes": 0,
        "source_sha256": "",
        "stored_sha256": "",
        "tick_count": 0,
        "path": relative,
        "error": last_error,
    }


def acquire_month(
    root: Path,
    spec: dict[str, object],
    year: int,
    month: int,
    client: httpx.Client,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with ThreadPoolExecutor(
        max_workers=int(CONFIG["maximum_concurrency"]),
        thread_name_prefix=str(spec["symbol"]).lower(),
    ) as executor:
        futures = {
            executor.submit(acquire_hour, root, spec, hour, client): hour
            for hour in hours_in_month(year, month)
        }
        for future in as_completed(futures):
            rows.append(future.result())
    return sorted(rows, key=lambda row: str(row["hour_utc"]))


def validate_and_freeze_month(
    root: Path,
    spec: dict[str, object],
    year: int,
    month: int,
    rows: list[dict[str, object]],
) -> dict[str, object]:
    symbol = str(spec["symbol"])
    expected_hours = hours_in_month(year, month)
    if len(rows) != len(expected_hours):
        raise ValueError(f"wrong hourly cardinality for {symbol} {year:04d}-{month:02d}")
    failures = [
        row
        for row in rows
        if row["status"] not in {"DOWNLOADED_VALID", "RESUMED_VALID"}
    ]
    if failures:
        raise ValueError(f"source acquisition failures: {failures[:3]}")
    partition = (
        root / "raw" / symbol / f"year={year:04d}" / f"month={month:02d}"
    )
    for hour, row in zip(expected_hours, rows, strict=True):
        if row["hour_utc"] != iso_utc(hour) or row["symbol"] != symbol:
            raise ValueError("cross-hour or cross-symbol acquisition row")
        path = root / str(row["path"])
        try:
            path.resolve().relative_to(partition.resolve())
        except ValueError as exc:
            raise ValueError("source path escapes its month partition") from exc
        if not path.is_file() or sha256_file(path) != row["stored_sha256"]:
            raise ValueError(f"stored source hash mismatch: {path}")
        read_stored_hour(
            path,
            hour,
            int(spec["price_scale"]),
            str(row["source_sha256"]),
        )

    acquisition_path = partition / "_ACQUISITION_MANIFEST.json"
    frozen_path = partition / "_FROZEN_MANIFEST.json"
    for path in (acquisition_path, frozen_path):
        if path.exists():
            path.chmod(0o666)
    write_json(
        acquisition_path,
        {
            "symbol": symbol,
            "source_code": spec["source_code"],
            "month": f"{year:04d}-{month:02d}",
            "rows": rows,
        },
    )
    raw_paths = [root / str(row["path"]) for row in rows]
    write_json(
        frozen_path,
        {
            "symbol": symbol,
            "month": f"{year:04d}-{month:02d}",
            "expected_hour_files": len(expected_hours),
            "observed_hour_files": len(raw_paths),
            "complete": True,
            "frozen": True,
            "stored_files_sha256": sha256_bytes(
                canonical_json(
                    [(path.name, sha256_file(path)) for path in sorted(raw_paths)]
                )
            ),
        },
    )
    for path in (*raw_paths, acquisition_path, frozen_path):
        path.chmod(0o444)
    return {
        "symbol": symbol,
        "month": f"{year:04d}-{month:02d}",
        "hours": len(rows),
        "ticks": sum(int(row["tick_count"]) for row in rows),
        "source_bytes": sum(int(row["source_bytes"]) for row in rows),
        "stored_bytes": sum(int(row["stored_bytes"]) for row in rows),
        "complete": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True, choices=sorted(instrument_map()))
    parser.add_argument("--start-month")
    parser.add_argument("--end-month")
    args = parser.parse_args()

    root = Path(
        os.getenv(
            CONFIG["storage_environment_variable"], CONFIG["default_storage_root"]
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    spec = instrument_map()[args.symbol]
    start = datetime.fromisoformat(CONFIG["start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(
        CONFIG["end_exclusive_utc"].replace("Z", "+00:00")
    )
    selected = month_keys(start, end)
    if args.start_month:
        selected = [
            item
            for item in selected
            if f"{item[0]:04d}-{item[1]:02d}" >= args.start_month
        ]
    if args.end_month:
        selected = [
            item
            for item in selected
            if f"{item[0]:04d}-{item[1]:02d}" <= args.end_month
        ]

    limits = httpx.Limits(
        max_connections=int(CONFIG["maximum_concurrency"]),
        max_keepalive_connections=int(CONFIG["maximum_concurrency"]),
    )
    headers = {
        "User-Agent": "DUKASCOPY_GROWTH_RISK_PULSE_FOUNDATION_V1/1.0",
        "Accept": "application/json",
    }
    with httpx.Client(timeout=60.0, limits=limits, headers=headers) as client:
        metadata = freeze_instrument_metadata(root, spec, client)
        print(json.dumps(metadata, sort_keys=True), flush=True)
        for year, month in selected:
            rows = acquire_month(root, spec, year, month, client)
            summary = validate_and_freeze_month(
                root, spec, year, month, rows
            )
            print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
