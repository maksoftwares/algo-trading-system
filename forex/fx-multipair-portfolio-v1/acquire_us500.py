"""Acquire USA500.IDX-USD hourly tick files from Dukascopy.

The instrument screen picked US500 (74.0x range/cost) over BTCUSD (16.0x), so
this builds its history. Dukascopy publishes ticks from 2012-01-16; this pulls
2016-01 onward, matching the FX foundation's window so the two are comparable.

Storage mirrors the existing Dukascopy foundations — ``raw/<SYMBOL>/year=YYYY/
month=MM/YYYYMMDDHH.json.gz`` — so the same decoder reads all of them.

Politeness: bounded concurrency, one retry, and empty hours are stored as empty
payloads rather than retried forever (an index is closed most of the weekend).
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import random
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from pathlib import Path

SYMBOL = "US500"
SOURCE_CODE = "USA500.IDX-USD"
ORIGIN = "https://jetta.dukascopy.com/v1"
STORAGE = Path(r"D:\AlgoTradingData\C_DRIVE\DukascopyIndexFoundationV1")
TIMEOUT = 45
MAX_ATTEMPTS = 6
BACKOFF_BASE = 2.0
USER_AGENT = "us500-research/1.0"


def hour_url(moment: datetime) -> str:
    return f"{ORIGIN}/ticks/{SOURCE_CODE}/{moment.year}/{moment.month}/{moment.day}/{moment.hour}"


def hour_path(moment: datetime) -> Path:
    return (
        STORAGE
        / "raw"
        / SYMBOL
        / f"year={moment.year:04d}"
        / f"month={moment.month:02d}"
        / f"{moment:%Y%m%d%H}.json.gz"
    )


def fetch(moment: datetime) -> tuple[datetime, str, int]:
    path = hour_path(moment)
    if path.is_file() and path.stat().st_size > 0:
        return moment, "CACHED", path.stat().st_size
    request = urllib.request.Request(hour_url(moment), headers={"User-Agent": USER_AGENT})
    # The endpoint rate-limits aggressively; 429 is retried with exponential
    # backoff and jitter rather than dropped, otherwise whole months go missing.
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                raw = response.read()
            payload = json.loads(raw)
            if not isinstance(payload, dict) or "times" not in payload:
                return moment, "BAD_PAYLOAD", 0
            path.parent.mkdir(parents=True, exist_ok=True)
            blob = gzip.compress(raw, compresslevel=6)
            path.write_bytes(blob)
            return moment, ("EMPTY" if not payload["times"] else "OK"), len(blob)
        except urllib.error.HTTPError as error:
            if error.code == 400:
                return moment, "NO_DATA", 0
            if error.code != 429 and attempt >= 3:
                return moment, f"HTTP_{error.code}", 0
            if attempt == MAX_ATTEMPTS:
                return moment, f"HTTP_{error.code}", 0
        except Exception:
            if attempt == MAX_ATTEMPTS:
                return moment, "ERROR", 0
        time.sleep(min(BACKOFF_BASE * (2 ** (attempt - 1)), 20.0) + random.random())
    return moment, "ERROR", 0


def hours(start: datetime, end: datetime):
    moment = start
    while moment < end:
        yield moment
        moment += timedelta(hours=1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire US500 Dukascopy ticks")
    parser.add_argument("--start", default="2016-01")
    parser.add_argument("--end", default="2026-07")  # exclusive
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m").replace(tzinfo=UTC)
    end = datetime.strptime(args.end, "%Y-%m").replace(tzinfo=UTC)
    todo = list(hours(start, end))
    print(f"{SYMBOL} <- {SOURCE_CODE}: {len(todo):,} hours, {args.workers} workers", flush=True)

    counts: dict[str, int] = {}
    began = time.time()
    done = total_bytes = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(fetch, moment) for moment in todo]
        for future in as_completed(futures):
            _, status, size = future.result()
            counts[status] = counts.get(status, 0) + 1
            total_bytes += size
            done += 1
            if done % 2000 == 0 or done == len(todo):
                rate = done / max(time.time() - began, 1e-9)
                print(
                    f"  {done:,}/{len(todo):,} ({rate:.0f}/s, "
                    f"{(len(todo) - done) / max(rate, 1e-9) / 60:.0f} min left) "
                    f"{total_bytes / 1e6:.0f} MB  {counts}",
                    flush=True,
                )

    manifest = {
        "schema_version": "dukascopy_index_us500_v1",
        "symbol": SYMBOL,
        "source_code": SOURCE_CODE,
        "window": {"start": args.start, "end_exclusive": args.end},
        "hours_requested": len(todo),
        "status_counts": counts,
        "stored_bytes": total_bytes,
        "completed_utc": datetime.now(UTC).isoformat(),
    }
    manifest_path = STORAGE / "metadata" / f"{SYMBOL}_ACQUISITION.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\n{counts}")
    print(f"elapsed {(time.time() - began) / 60:.1f} min, {total_bytes / 1e6:.0f} MB")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
