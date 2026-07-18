from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fomc_sources import build_calendar, parse_regular_statement_links  # noqa: E402


CONFIG_PATH = ROOT / "config" / "out_of_era_specialist_replication_v2.json"
USER_AGENT = "algo-trading-system-research/1.0 (+read-only public archive)"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        if int(response.status) != 200:
            raise RuntimeError(f"Official source returned HTTP {response.status}: {url}")
        payload = response.read()
    if len(payload) < 1000:
        raise ValueError(f"Official source is unexpectedly small: {url}")
    return payload


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _storage_root(config: Mapping[str, Any]) -> Path:
    source = config["source"]
    return Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    settings = config["official_fomc"]
    public_root = _storage_root(config) / config["source"]["public_input_root"]
    lock_path = ROOT / "outputs" / "OUT_OF_ERA_SPECIALIST_DEFINITION_LOCK.json"
    if lock_path.exists():
        raise RuntimeError("Official sources cannot change after definition lock")
    public_root.mkdir(parents=True, exist_ok=True)
    source_records: dict[str, dict[str, Any]] = {}
    links = []
    for year in settings["years"]:
        url = str(settings["historical_page_template"]).format(year=int(year))
        payload = _fetch(url)
        path = public_root / "federal-reserve" / f"fomchistorical{int(year)}.html"
        _atomic_bytes(path, payload)
        source_records[f"historical/{int(year)}"] = {
            "url": url,
            "path": str(path.relative_to(public_root)).replace("\\", "/"),
            "bytes": int(path.stat().st_size),
            "sha256": _sha256(path),
        }
        links.extend(parse_regular_statement_links(payload.decode("utf-8-sig")))

    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    calendar = build_calendar(links, settings, start, end)
    expected = int(settings["expected_regular_events"])
    if len(calendar) != expected:
        raise ValueError(f"Expected {expected} regular FOMC events, found {len(calendar)}")

    for row in calendar.itertuples(index=False):
        payload = _fetch(str(row.source_url))
        path = public_root / "federal-reserve" / "statements" / f"monetary{row.date.replace('-', '')}a.html"
        _atomic_bytes(path, payload)
        source_records[f"statement/{row.date}"] = {
            "url": str(row.source_url),
            "path": str(path.relative_to(public_root)).replace("\\", "/"),
            "bytes": int(path.stat().st_size),
            "sha256": _sha256(path),
        }

    timing_url = str(settings["timing_change_url"])
    timing_payload = _fetch(timing_url)
    timing_path = public_root / "federal-reserve" / "monetary20130313a.html"
    _atomic_bytes(timing_path, timing_payload)
    source_records["timing_change"] = {
        "url": timing_url,
        "path": str(timing_path.relative_to(public_root)).replace("\\", "/"),
        "bytes": int(timing_path.stat().st_size),
        "sha256": _sha256(timing_path),
    }

    calendar_path = public_root / "OFFICIAL_FOMC_CALENDAR_2010_2016.csv"
    temporary = calendar_path.with_suffix(".csv.part")
    calendar.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, calendar_path)
    manifest = {
        "schema_version": "xauusd_official_fomc_sources_v2",
        "created_utc": datetime.now(UTC).isoformat(),
        "calendar_rows": int(len(calendar)),
        "calendar_sha256": _sha256(calendar_path),
        "first_event_utc": calendar["event_time_utc"].min().isoformat(),
        "last_event_utc": calendar["event_time_utc"].max().isoformat(),
        "release_rule_counts": {
            str(key): int(value)
            for key, value in calendar["release_time_rule"].value_counts().sort_index().items()
        },
        "sources": dict(sorted(source_records.items())),
        "contains_outcomes": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
    }
    _atomic_json(public_root / "OFFICIAL_FOMC_SOURCE_MANIFEST.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

