from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
FOUNDATION_SRC = REPO_ROOT / "multi-asset" / "data-foundation" / "dukascopy-ticks-v1" / "src"
sys.path.insert(0, str(FOUNDATION_SRC))

from dukascopy_tick_foundation import foundation  # noqa: E402


CONFIG = ROOT / "config" / "xag_xau_eventtime_catchup_v72.json"


def month_range(start: str, end: str) -> list[tuple[int, int]]:
    current = datetime.strptime(start, "%Y-%m").replace(tzinfo=UTC)
    finish = datetime.strptime(end, "%Y-%m").replace(tzinfo=UTC)
    rows: list[tuple[int, int]] = []
    while current <= finish:
        rows.append((current.year, current.month))
        current = datetime(
            current.year + int(current.month == 12),
            1 if current.month == 12 else current.month + 1,
            1,
            tzinfo=UTC,
        )
    return rows


def acquire_instrument_evidence(storage: Path) -> Path:
    url = "https://jetta.dukascopy.com/v1/instruments/XAG-USD"
    if urlparse(url).hostname != "jetta.dukascopy.com":
        raise ValueError("non-official XAG instrument URL")
    body, _, status = foundation.http_fetch(url)
    if status != 200:
        raise RuntimeError(f"XAG instrument endpoint returned {status}")
    metadata = json.loads(body)
    histories = metadata.get("histories", [])
    if (
        metadata.get("code") != "XAG-USD"
        or metadata.get("name") != "XAG/USD"
        or int(metadata.get("priceScale", -1)) != 3
        or not any(row.get("period") == "TICK" for row in histories)
    ):
        raise ValueError("official XAG instrument evidence failed schema validation")
    path = storage / "source-evidence" / "instrument-XAGUSD.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire free official Dukascopy XAG ticks")
    parser.add_argument("--start", default="2024-07")
    parser.add_argument("--end", default="2026-06")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.concurrency <= 4:
        raise ValueError("concurrency must be 1-4")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    storage = Path(
        os.environ.get(
            config["source"]["storage_environment_variable"],
            config["source"]["default_storage_root"],
        )
    ).resolve()
    foundation.INSTRUMENTS["XAGUSD"] = {
        "source_code": "XAG-USD",
        "pip_size": 0.001,
        "price_scale": 3,
    }
    evidence = acquire_instrument_evidence(storage)
    print(f"verified official instrument evidence: {evidence}", flush=True)
    for year, month in month_range(args.start, args.end):
        rows = foundation.acquire_month(
            storage, "XAGUSD", year, month, concurrency=args.concurrency
        )
        manifest = foundation.write_month_acquisition_manifest(
            storage, "XAGUSD", year, month, rows
        )
        foundation.validate_month_acquisition_manifest(
            storage, "XAGUSD", year, month
        )
        frozen = foundation.freeze_raw_month(storage, "XAGUSD", year, month)
        if not bool(frozen["complete"]):
            raise RuntimeError(f"incomplete XAG month {year:04d}-{month:02d}")
        downloaded = sum(row["status"] == "DOWNLOADED_VALID" for row in rows)
        resumed = sum(row["status"] == "RESUMED_VALID" for row in rows)
        print(
            f"XAG {year:04d}-{month:02d}: downloaded={downloaded} "
            f"resumed={resumed} manifest={manifest}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

