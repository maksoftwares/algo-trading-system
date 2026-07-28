from __future__ import annotations

import argparse
import hashlib
import json
import os
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
    "eurusd-neutral-dukascopy-event-timing-v1"
)
BASE_URL = (
    "https://freeserv.dukascopy.com/2.0/index.php"
    "?path=economic_calendar_new/getNews"
)
DOCUMENTATION_URL = (
    "https://www.dukascopy.com/trading-tools/widgets/"
    "calendars/economic_calendar"
)
FIRST_DATE = "2019-01-01"
LAST_DATE = "2026-06-30"
NORMALIZED_COLUMNS = [
    "event_id",
    "event_time_utc",
    "country",
    "currency",
    "title",
    "periodicity",
    "impact",
    "tag",
    "actual",
    "actual_norm",
    "forecast",
    "forecast_norm",
    "previous",
    "previous_norm",
    "historical_count",
    "effect",
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


def quarterly_windows(
    start_date: str = FIRST_DATE,
    end_date: str = LAST_DATE,
) -> list[tuple[pd.Timestamp, pd.Timestamp, str]]:
    start = pd.Timestamp(start_date, tz="UTC").normalize()
    final = pd.Timestamp(end_date, tz="UTC").normalize()
    windows: list[tuple[pd.Timestamp, pd.Timestamp, str]] = []
    cursor = start
    while cursor <= final:
        quarter_end = (cursor + pd.offsets.QuarterEnd()).normalize()
        end = min(quarter_end, final)
        key = f"{cursor.year}-Q{cursor.quarter}"
        windows.append((cursor, end, key))
        cursor = end + pd.Timedelta(days=1)
    return windows


def event_url(start: pd.Timestamp, end: pd.Timestamp) -> str:
    until = end + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
    query = urllib.parse.urlencode(
        {
            "since": int(start.timestamp() * 1000),
            "until": int(until.timestamp() * 1000),
        }
    )
    return f"{BASE_URL}&{query}"


def fetch_bytes(
    url: str,
    *,
    maximum_attempts: int = 7,
) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/javascript,*/*;q=0.8",
            "Referer": "https://freeserv.dukascopy.com/2.0/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/150.0 Safari/537.36"
            ),
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, maximum_attempts + 1):
        try:
            with urllib.request.urlopen(
                request, timeout=180
            ) as response:
                payload = response.read()
                if not payload:
                    raise RuntimeError("Empty Dukascopy calendar response")
                return payload
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504):
                raise
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
            RuntimeError,
        ) as exc:
            last_error = exc
        if attempt < maximum_attempts:
            time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"Unable to download {url}") from last_error


def parse_jsonp(payload: bytes) -> list[dict[str, Any]]:
    text = payload.decode("utf-8").strip()
    first = text.find("(")
    last = text.rfind(")")
    if first <= 0 or last <= first:
        raise RuntimeError("Unexpected Dukascopy JSONP wrapper")
    callback = text[:first].strip()
    if not callback.replace(".", "_").isidentifier():
        raise RuntimeError("Unexpected Dukascopy JSONP callback")
    decoded = json.loads(text[first + 1 : last])
    if not isinstance(decoded, list) or any(
        not isinstance(row, dict) for row in decoded
    ):
        raise RuntimeError("Unexpected Dukascopy event payload")
    required = {
        "id",
        "date",
        "country",
        "currency",
        "title",
        "impact",
        "tag",
    }
    if any(not required.issubset(row) for row in decoded):
        raise RuntimeError("Unexpected Dukascopy event schema")
    return decoded


def normalize_events(
    rows: list[dict[str, Any]],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=NORMALIZED_COLUMNS)
    frame = pd.DataFrame(rows)
    frame["event_time_utc"] = pd.to_datetime(
        frame["date"], utc=True, errors="raise"
    )
    exclusive_end = end + pd.Timedelta(days=1)
    frame = frame[
        frame["event_time_utc"].ge(start)
        & frame["event_time_utc"].lt(exclusive_end)
    ].copy()
    frame["event_id"] = frame["id"].astype(str)
    rename = {column: column for column in NORMALIZED_COLUMNS}
    for column in NORMALIZED_COLUMNS:
        if column not in frame:
            frame[column] = None
    normalized = frame[list(rename)].copy()
    for column in NORMALIZED_COLUMNS:
        if column not in ("event_time_utc",):
            normalized[column] = normalized[column].astype("string")
    return normalized


def acquire_payload(
    url: str,
    path: Path,
    *,
    force: bool,
) -> tuple[bytes, dict[str, Any]]:
    from_cache = path.exists() and not force
    payload = path.read_bytes() if from_cache else fetch_bytes(url)
    if not from_cache:
        atomic_write(path, payload)
    return payload, {
        "url": url,
        "path": path.as_posix(),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "from_cache": from_cache,
    }


def _deduplicate(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if frame.empty:
        return frame, 0
    ordered = frame.sort_values(
        ["event_time_utc", "event_id"],
        kind="mergesort",
    ).reset_index(drop=True)
    duplicated = ordered.duplicated("event_id", keep=False)
    for _, group in ordered[duplicated].groupby("event_id", sort=False):
        comparable = group.drop(columns=["event_time_utc"]).fillna("<NA>")
        if len(comparable.drop_duplicates()) != 1:
            raise RuntimeError(
                f"Conflicting duplicate event id {group['event_id'].iloc[0]}"
            )
        if group["event_time_utc"].nunique() != 1:
            raise RuntimeError(
                f"Duplicate event id moved in time "
                f"{group['event_id'].iloc[0]}"
            )
    duplicate_count = int(ordered.duplicated("event_id").sum())
    return (
        ordered.drop_duplicates("event_id", keep="first").reset_index(
            drop=True
        ),
        duplicate_count,
    )


def acquire(
    output_root: Path,
    *,
    force: bool,
    delay_seconds: float,
) -> dict[str, Any]:
    raw_root = output_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []
    duplicate_rows_within_chunks = 0
    windows = quarterly_windows()
    for index, (start, end, key) in enumerate(windows, start=1):
        url = event_url(start, end)
        payload, record = acquire_payload(
            url,
            raw_root / f"{key}.jsonp",
            force=force,
        )
        rows = parse_jsonp(payload)
        frame = normalize_events(rows, start, end)
        duplicate_rows_within_chunks += int(
            frame.duplicated("event_id").sum()
        )
        record.update(
            {
                "window": key,
                "start_date": start.strftime("%Y-%m-%d"),
                "end_date": end.strftime("%Y-%m-%d"),
                "response_rows": len(rows),
                "in_window_rows": int(len(frame)),
            }
        )
        records.append(record)
        frames.append(frame)
        print(
            f"Dukascopy event acquisition {index}/{len(windows)} "
            f"{key}: {len(frame)} rows",
            flush=True,
        )
        if not record["from_cache"]:
            time.sleep(delay_seconds)

    combined = pd.concat(frames, ignore_index=True)
    combined, duplicate_rows_removed = _deduplicate(combined)
    if combined["event_id"].duplicated().any():
        raise RuntimeError("Duplicate normalized Dukascopy event ids")
    if not combined["event_time_utc"].is_monotonic_increasing:
        raise RuntimeError("Dukascopy event source is not time ordered")

    output_root.mkdir(parents=True, exist_ok=True)
    parquet_path = output_root / "DUKASCOPY_ECONOMIC_EVENTS.parquet"
    combined.to_parquet(parquet_path, index=False, compression="zstd")

    raw_chain = hashlib.sha256()
    for record in records:
        raw_chain.update(bytes.fromhex(record["sha256"]))
    currency_counts = {
        str(key): int(value)
        for key, value in combined["currency"].value_counts().items()
    }
    impact_counts = {
        str(key): int(value)
        for key, value in combined["impact"].fillna("<NA>").value_counts().items()
    }
    manifest = {
        "source": "Dukascopy public Economic Calendar widget",
        "documentation": DOCUMENTATION_URL,
        "authentication_required": False,
        "base_url": BASE_URL,
        "coverage": {
            "first_date": FIRST_DATE,
            "last_date": LAST_DATE,
            "first_event_utc": combined["event_time_utc"].min().isoformat(),
            "last_event_utc": combined["event_time_utc"].max().isoformat(),
            "quarterly_requests": len(records),
            "normalized_events": int(len(combined)),
            "duplicate_rows_reported_within_chunks": (
                duplicate_rows_within_chunks
            ),
            "duplicate_rows_removed_overall": duplicate_rows_removed,
            "currency_counts": currency_counts,
            "impact_counts": impact_counts,
        },
        "field_policy": {
            "allowed_for_strategy": [
                "event_id",
                "event_time_utc",
                "currency",
                "title",
                "tag",
            ],
            "prohibited_for_strategy": [
                "impact",
                "actual",
                "actual_norm",
                "forecast",
                "forecast_norm",
                "previous",
                "previous_norm",
                "historical_count",
                "effect",
            ],
            "reason": (
                "The endpoint is a current historical snapshot, not a "
                "point-in-time archive. A known 2024 payroll consensus is "
                "inconsistent with contemporaneous sources."
            ),
        },
        "raw_response_chain_sha256": raw_chain.hexdigest(),
        "normalized_schema": NORMALIZED_COLUMNS,
        "parquet_path": parquet_path.as_posix(),
        "parquet_bytes": parquet_path.stat().st_size,
        "parquet_sha256": sha256_file(parquet_path),
        "raw_responses": [
            {
                key: record[key]
                for key in (
                    "url",
                    "path",
                    "bytes",
                    "sha256",
                    "window",
                    "start_date",
                    "end_date",
                    "response_rows",
                    "in_window_rows",
                )
            }
            for record in records
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
        "downloaded_requests": int(
            sum(not record["from_cache"] for record in records)
        ),
        "cached_requests": int(
            sum(record["from_cache"] for record in records)
        ),
        **{
            key: manifest[key]
            for key in (
                "coverage",
                "raw_response_chain_sha256",
                "parquet_path",
                "parquet_bytes",
                "parquet_sha256",
            )
        },
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
    parser.add_argument("--delay-seconds", type=float, default=0.15)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.delay_seconds < 0:
        raise ValueError("Delay must be nonnegative")
    if args.command == "rebuild":
        expected = len(quarterly_windows())
        actual = len(list((args.root / "raw").glob("*.jsonp")))
        if actual != expected:
            raise RuntimeError(f"Cache incomplete: {actual} != {expected}")
    result = acquire(
        args.root,
        force=args.force,
        delay_seconds=args.delay_seconds,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
