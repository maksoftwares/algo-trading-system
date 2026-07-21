from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
UPSTREAM_SRC = (
    REPO_ROOT / "multi-asset" / "data-foundation" / "dukascopy-ticks-v1" / "src"
)
sys.path.insert(0, str(UPSTREAM_SRC))

from dukascopy_tick_foundation import foundation  # noqa: E402
from src.foundation import sha256_file, validate_hour_payload  # noqa: E402


CONFIG = json.loads(
    (ROOT / "config" / "dukascopy_vol_index_v1.json").read_text(encoding="utf-8")
)


def months(start: datetime, end_exclusive: datetime) -> list[tuple[int, int]]:
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


def acquire_hour(
    root: Path,
    symbol: str,
    hour: datetime,
    maximum_invalid_fraction: float,
    client: httpx.Client,
) -> dict[str, object]:
    path = foundation.raw_hour_path(root, symbol, hour)
    path.parent.mkdir(parents=True, exist_ok=True)
    url = foundation.official_tick_url(symbol, hour)
    relative = str(path.relative_to(root)).replace("\\", "/")

    if path.is_file():
        try:
            _, quality = validate_hour_payload(
                path.read_bytes(), hour, maximum_invalid_fraction
            )
            return {
                "symbol": symbol,
                "hour_utc": foundation.iso_utc(hour),
                "source_file_id": f"{symbol}-{hour:%Y%m%d%H}",
                "url": url,
                "status": "RESUMED_VALID",
                "attempts": 0,
                "http_status": 200,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "tick_count": int(quality["valid_tick_count"]),
                **quality,
                "path": relative,
            }
        except (OSError, ValueError, json.JSONDecodeError):
            path.chmod(0o666)
            path.unlink()

    last_error = ""
    for attempt in (1, 2):
        try:
            response = client.get(url)
            raw = response.content
            headers = {key.lower(): value for key, value in response.headers.items()}
            status = response.status_code
            if status != 200:
                raise ValueError(f"HTTP status {status}")
            _, quality = validate_hour_payload(raw, hour, maximum_invalid_fraction)
            partial = path.with_suffix(".json.part")
            partial.write_bytes(raw)
            os.replace(partial, path)
            return {
                "symbol": symbol,
                "hour_utc": foundation.iso_utc(hour),
                "source_file_id": f"{symbol}-{hour:%Y%m%d%H}",
                "url": url,
                "status": "DOWNLOADED_VALID",
                "attempts": attempt,
                "http_status": status,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "tick_count": int(quality["valid_tick_count"]),
                **quality,
                "etag": headers.get("etag", ""),
                "last_modified": headers.get("last-modified", ""),
                "path": relative,
            }
        except Exception as exc:  # network and source errors are persisted
            last_error = f"{type(exc).__name__}: {exc}"
    return {
        "symbol": symbol,
        "hour_utc": foundation.iso_utc(hour),
        "source_file_id": f"{symbol}-{hour:%Y%m%d%H}",
        "url": url,
        "status": "FAILED_AFTER_ONE_RETRY",
        "attempts": 2,
        "bytes": 0,
        "sha256": "",
        "tick_count": 0,
        "path": relative,
        "error": last_error,
    }


def acquire_month(
    root: Path,
    symbol: str,
    year: int,
    month: int,
    maximum_invalid_fraction: float,
    client: httpx.Client,
) -> list[dict[str, object]]:
    hours = foundation.hours_in_month(year, month)
    rows: list[dict[str, object]] = []
    with ThreadPoolExecutor(
        max_workers=int(CONFIG["maximum_concurrency"]), thread_name_prefix="volidx"
    ) as executor:
        futures = {
            executor.submit(
                acquire_hour, root, symbol, hour, maximum_invalid_fraction, client
            ): hour
            for hour in hours
        }
        for future in as_completed(futures):
            rows.append(future.result())
    return sorted(rows, key=lambda row: str(row["hour_utc"]))


def validate_month(root: Path, rows: list[dict[str, object]]) -> None:
    failures = [
        row
        for row in rows
        if row["status"] not in {"DOWNLOADED_VALID", "RESUMED_VALID"}
    ]
    if failures:
        raise ValueError(f"VOLIDX acquisition failures: {failures[:3]}")
    for row in rows:
        path = root / str(row["path"])
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise ValueError(f"VOLIDX source hash mismatch: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-month")
    parser.add_argument("--end-month")
    args = parser.parse_args()

    root = Path(
        os.getenv(
            CONFIG["storage_environment_variable"], CONFIG["default_storage_root"]
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    symbol = CONFIG["symbol"]
    foundation.INSTRUMENTS[symbol] = {
        "source_code": CONFIG["source_code"],
        "pip_size": CONFIG["pip_size"],
        "price_scale": CONFIG["price_scale"],
    }
    start = datetime.fromisoformat(CONFIG["start_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(CONFIG["end_exclusive_utc"].replace("Z", "+00:00"))
    selected = months(start, end)
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
        "User-Agent": "DUKASCOPY_VOL_INDEX_FOUNDATION_V1/1.0",
        "Accept": "application/json",
    }
    with httpx.Client(timeout=60.0, limits=limits, headers=headers) as client:
        for year, month in selected:
            rows = acquire_month(
                root,
                symbol,
                year,
                month,
                float(CONFIG["maximum_invalid_quote_fraction_per_hour"]),
                client,
            )
            foundation.write_month_acquisition_manifest(root, symbol, year, month, rows)
            validate_month(root, rows)
            frozen = foundation.freeze_raw_month(root, symbol, year, month)
            print(
                json.dumps(
                    {
                        "month": f"{year:04d}-{month:02d}",
                        "hours": len(rows),
                        "ticks": sum(int(row["tick_count"]) for row in rows),
                        "bytes": sum(int(row["bytes"]) for row in rows),
                        "complete": frozen["complete"],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
