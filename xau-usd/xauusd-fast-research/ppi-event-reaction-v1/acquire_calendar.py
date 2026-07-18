from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "ppi_event_reaction_v1.json"
LINK_PATTERN = re.compile(
    r"\[(?P<reference>[A-Za-z]+ \d{4}) Producer Price Index\]"
    r"\((?P<url>https://www\.bls\.gov/news\.release/archives/"
    r"ppi_(?P<release>\d{8})\.htm)\)"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_text(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _write_json(path: Path, payload: dict) -> None:
    _write_text(
        path,
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )


def parse_archive(
    text: str, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    rows = []
    for match in LINK_PATTERN.finditer(text):
        release_date = pd.to_datetime(
            match.group("release"), format="%m%d%Y", errors="raise"
        ).date()
        local = pd.Timestamp(
            f"{release_date.isoformat()} 08:30:00", tz="America/New_York"
        )
        event_time = local.tz_convert("UTC")
        if not (start <= event_time < end):
            continue
        rows.append(
            {
                "event_id": f"PPI_{release_date.isoformat()}",
                "event_type": "PPI",
                "event_time_utc": event_time,
                "event_date": release_date.isoformat(),
                "reference": match.group("reference"),
                "source_kind": "BLS_OFFICIAL_ARCHIVE_INDEX",
                "source_url": match.group("url"),
                "release_time_rule": "08:30 America/New_York",
            }
        )
    if not rows:
        raise ValueError("No official PPI release links were parsed")
    frame = pd.DataFrame(rows).sort_values("event_time_utc", kind="mergesort")
    if frame["event_id"].duplicated().any() or frame["source_url"].duplicated().any():
        raise ValueError("Duplicate official PPI release found")
    if not frame["source_url"].str.fullmatch(
        r"https://www\.bls\.gov/news\.release/archives/ppi_\d{8}\.htm"
    ).all():
        raise ValueError("Non-BLS PPI source URL found")
    return frame.reset_index(drop=True)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock = output / config["outputs"]["contract_lock"]
    if lock.exists():
        raise RuntimeError("Refusing calendar acquisition after contract lock")
    request = Request(
        config["source"]["free_text_transport_url"],
        headers={"User-Agent": "xauusd-research-read-only/1.0"},
    )
    with urlopen(request, timeout=60) as response:
        raw = response.read().decode("utf-8")
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    calendar = parse_archive(raw, start, end)
    expected = int(config["source"]["expected_calendar_rows"])
    if len(calendar) != expected:
        raise ValueError(f"Expected {expected} PPI events, found {len(calendar)}")
    output.mkdir(parents=True, exist_ok=True)
    raw_path = output / config["outputs"]["raw_archive_index"]
    calendar_path = output / config["outputs"]["calendar"]
    manifest_path = output / config["outputs"]["calendar_manifest"]
    _write_text(raw_path, raw)
    temporary_calendar = calendar_path.with_suffix(".csv.part")
    calendar.to_csv(temporary_calendar, index=False, lineterminator="\n")
    os.replace(temporary_calendar, calendar_path)
    manifest = {
        "schema_version": "xauusd_ppi_event_calendar_manifest_v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "official_archive_url": config["source"]["official_archive_url"],
        "free_text_transport_url": config["source"]["free_text_transport_url"],
        "transport_role": "read-only rendering of the official BLS index",
        "raw_archive_sha256": _sha256(raw_path),
        "calendar_sha256": _sha256(calendar_path),
        "calendar_rows": int(len(calendar)),
        "first_event_utc": calendar["event_time_utc"].min().isoformat(),
        "last_event_utc": calendar["event_time_utc"].max().isoformat(),
        "direct_bls_source_urls": int(calendar["source_url"].nunique()),
        "contains_price_outcomes": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    _write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
