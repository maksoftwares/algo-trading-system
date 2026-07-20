from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
from urllib.parse import urlparse

import httpx


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
FOUNDATION_SRC = (
    REPO_ROOT
    / "multi-asset"
    / "data-foundation"
    / "dukascopy-ticks-v1"
    / "src"
)
sys.path.insert(0, str(FOUNDATION_SRC))

from dukascopy_tick_foundation import foundation  # noqa: E402


CONFIG = ROOT / "config" / "fx_breadth_overreaction_fade_v81.json"


def month_range(start: str, end: str) -> list[tuple[int, int]]:
    current = datetime.strptime(start, "%Y-%m").replace(tzinfo=UTC)
    finish = datetime.strptime(end, "%Y-%m").replace(tzinfo=UTC)
    if current > finish:
        raise ValueError("V81 acquisition start follows end")
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
    url = "https://jetta.dukascopy.com/v1/instruments/GBP-USD"
    if urlparse(url).hostname != "jetta.dukascopy.com":
        raise ValueError("V81 received a non-official GBP instrument URL")
    body, _, status = foundation.http_fetch(url)
    if status != 200:
        raise RuntimeError(f"GBP instrument endpoint returned {status}")
    metadata = json.loads(body)
    histories = metadata.get("histories", [])
    if (
        metadata.get("code") != "GBP-USD"
        or metadata.get("name") != "GBP/USD"
        or int(metadata.get("priceScale", -1)) != 5
        or not any(row.get("period") == "TICK" for row in histories)
    ):
        raise ValueError("official GBP instrument evidence failed validation")
    path = storage / "source-evidence" / "instrument-GBPUSD.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire free official Dukascopy GBPUSD ticks for V81"
    )
    parser.add_argument("--start", default="2018-07")
    parser.add_argument("--end", default="2024-06")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--inter-month-cooldown-seconds", type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.concurrency <= 4:
        raise ValueError("V81 acquisition concurrency must be 1-4")
    if not 0 <= args.inter_month_cooldown_seconds <= 900:
        raise ValueError("V81 inter-month cooldown must be between 0 and 900 seconds")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    foundation.INSTRUMENTS["GBPUSD"] = {
        "source_code": "GBP-USD",
        "pip_size": 0.0001,
        "price_scale": 5,
    }
    evidence = acquire_instrument_evidence(storage)
    print(f"verified official instrument evidence: {evidence}", flush=True)
    limits = httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )
    headers = {
        "User-Agent": "xauusd-fx-breadth-v81/1.0",
        "Accept": "application/json",
    }
    months = month_range(str(args.start), str(args.end))
    for index, (year, month) in enumerate(months):
        with httpx.Client(
            headers=headers, limits=limits, follow_redirects=True
        ) as client:

            def fetch(
                url: str, timeout_seconds: int
            ) -> tuple[bytes, dict[str, str], int]:
                foundation.validate_official_url(url)
                try:
                    response = client.get(url, timeout=min(timeout_seconds, 30))
                except httpx.HTTPError as exc:
                    raise urllib.error.URLError(str(exc)) from exc
                return (
                    response.content,
                    {key.lower(): value for key, value in response.headers.items()},
                    int(response.status_code),
                )

            rows = foundation.acquire_month(
                storage,
                "GBPUSD",
                year,
                month,
                concurrency=args.concurrency,
                fetcher=fetch,
            )
        manifest = foundation.write_month_acquisition_manifest(
            storage, "GBPUSD", year, month, rows
        )
        foundation.validate_month_acquisition_manifest(
            storage, "GBPUSD", year, month
        )
        frozen = foundation.freeze_raw_month(storage, "GBPUSD", year, month)
        if not bool(frozen["complete"]):
            raise RuntimeError(
                f"incomplete GBPUSD month {year:04d}-{month:02d}"
            )
        downloaded = sum(row["status"] == "DOWNLOADED_VALID" for row in rows)
        resumed = sum(row["status"] == "RESUMED_VALID" for row in rows)
        print(
            f"GBPUSD {year:04d}-{month:02d}: downloaded={downloaded} "
            f"resumed={resumed} manifest={manifest}",
            flush=True,
        )
        if index < len(months) - 1 and args.inter_month_cooldown_seconds:
            print(
                "GBPUSD acquisition cooldown: "
                f"{args.inter_month_cooldown_seconds}s",
                flush=True,
            )
            time.sleep(args.inter_month_cooldown_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
