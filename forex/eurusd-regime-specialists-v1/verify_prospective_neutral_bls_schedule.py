from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.research import sha256_file
from plan_prospective_neutral_operations import (
    load_calendar_watchlist,
)
from plan_prospective_neutral_operations import (
    load_config as load_operations_config,
)
from plan_prospective_neutral_operations import (
    verify_lock as verify_operations_lock,
)

CONFIG_PATH = (
    ROOT / "config" / "frozen_prospective_neutral_bls_schedule_v1.json"
)
LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_BLS_SCHEDULE_PREREG_"
    "2026_07_28.sha256.json"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_bls_schedule_status_v1"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("BLS schedule verification is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"BLS schedule lock mismatch: {relative}")
        checked[relative] = actual
    cfg = load_config()
    planner = cfg["operations_planner_contract"]
    if sha256_file(ROOT / planner["path"]) != planner["sha256"]:
        raise RuntimeError("BLS schedule operations-planner drift")
    verify_operations_lock()
    verify_official_evidence(cfg)
    return checked


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return timestamp.tz_convert("UTC").as_unit("ns")


def _serialize(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def _official_canonical_payload(config: dict[str, Any]) -> dict[str, Any]:
    official = config["official_evidence"]
    return {
        "eastern": str(official["timezone_statement"]),
        "modified": f"Last Modified Date: {official['page_last_modified']}",
        "rows": official["rows"],
        "title": str(official["page_title"]),
        "url": str(official["url"]),
    }


def verify_official_evidence(config: dict[str, Any]) -> str:
    official = config["official_evidence"]
    payload = json.dumps(
        _official_canonical_payload(config),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    actual = hashlib.sha256(payload).hexdigest()
    if actual != official["canonical_extracted_payload_sha256"]:
        raise RuntimeError("Frozen browser-observed BLS evidence drift")
    if (
        official.get("raw_html_archived") is not False
        or int(official.get("scripted_http_status", 0)) != 403
        or "Eastern Time" not in str(official.get("timezone_statement"))
    ):
        raise RuntimeError("BLS access provenance is incomplete")
    return actual


def official_schedule(config: dict[str, Any]) -> list[dict[str, Any]]:
    official = config["official_evidence"]
    mapping = config["target_mapping"]
    timezone = ZoneInfo(str(official["timezone"]))
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in official["rows"]:
        if not isinstance(row, list) or len(row) != 3:
            raise RuntimeError("Official BLS schedule row is malformed")
        date_text, time_text, release_text = map(str, row)
        names = [name for name in mapping if release_text.startswith(name)]
        if len(names) != 1:
            raise RuntimeError("Official BLS release cannot be mapped uniquely")
        name = names[0]
        if name in seen:
            raise RuntimeError("Official BLS release appears more than once")
        seen.add(name)
        local = datetime.strptime(
            f"{date_text} {time_text}",
            "%A, %B %d, %Y %I:%M %p",
        ).replace(tzinfo=timezone)
        target = mapping[name]
        records.append(
            {
                "official_release": name,
                "official_release_text": release_text,
                "family": str(target["family"]),
                "tradingview_event_id": str(target["tradingview_event_id"]),
                "tradingview_ticker": str(target["tradingview_ticker"]),
                "official_event_time_utc": pd.Timestamp(local).tz_convert(
                    "UTC"
                ),
                "configured_event_time_utc": _utc(
                    target["expected_event_time_utc"]
                ),
            }
        )
    if seen != set(mapping):
        raise RuntimeError("Official BLS schedule does not cover every target")
    for record in records:
        if record["official_event_time_utc"] != record[
            "configured_event_time_utc"
        ]:
            raise RuntimeError("Configured UTC time disagrees with official BLS row")
    return sorted(records, key=lambda item: item["official_event_time_utc"])


def compare_schedule(
    tradingview_events: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    expected = official_schedule(config)
    expected_by_family = {row["family"]: row for row in expected}
    actual_by_family: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    for event in tradingview_events:
        family = str(event["family"])
        if family in actual_by_family:
            reasons.append(f"DUPLICATE_TRADINGVIEW_FAMILY:{family}")
            continue
        actual_by_family[family] = event
    missing = sorted(set(expected_by_family) - set(actual_by_family))
    extra = sorted(set(actual_by_family) - set(expected_by_family))
    reasons.extend(f"MISSING_TRADINGVIEW_FAMILY:{family}" for family in missing)
    reasons.extend(f"EXTRA_TRADINGVIEW_FAMILY:{family}" for family in extra)
    rows: list[dict[str, Any]] = []
    for family in sorted(set(expected_by_family) & set(actual_by_family)):
        expected_row = expected_by_family[family]
        actual = actual_by_family[family]
        checks = {
            "event_id": (
                str(actual["tradingview_event_id"])
                == expected_row["tradingview_event_id"]
            ),
            "ticker": (
                str(actual["tradingview_ticker"])
                == expected_row["tradingview_ticker"]
            ),
            "utc_timestamp": (
                _utc(actual["event_time_utc"])
                == expected_row["official_event_time_utc"]
            ),
        }
        for name, passed in checks.items():
            if not passed:
                reasons.append(f"{family}_{name.upper()}_MISMATCH")
        rows.append(
            {
                **expected_row,
                "tradingview_event_time_utc": _utc(
                    actual["event_time_utc"]
                ),
                "checks": checks,
                "matched": all(checks.values()),
            }
        )
    return {
        "matched": not reasons and len(rows) == len(expected),
        "mismatch_reasons": reasons,
        "rows": rows,
    }


def build_status(*, evaluated_at_utc: Any) -> dict[str, Any]:
    verify_lock()
    evaluated = _utc(evaluated_at_utc)
    config = load_config()
    operations = load_operations_config()
    events, latest_capture, census = load_calendar_watchlist(
        Path(config["tradingview_evidence_root"]),
        operations["target_tickers"],
    )
    comparison = compare_schedule(events, config)
    official_rows = official_schedule(config)
    recheck_hours = float(
        config["verification_policy"][
            "official_page_recheck_required_hours_before_release"
        ]
    )
    first_release = min(
        row["official_event_time_utc"] for row in official_rows
    )
    return _serialize(
        {
            "schema_version": SCHEMA_VERSION,
            "evaluated_at_utc": evaluated,
            "status": (
                "MATCHED_OFFICIAL_BLS_SCHEDULE"
                if comparison["matched"]
                else "BLOCKED_OFFICIAL_SCHEDULE_MISMATCH_NO_TRADE"
            ),
            "official_source_url": config["official_evidence"]["url"],
            "official_source_last_modified": config["official_evidence"][
                "page_last_modified"
            ],
            "official_source_observed_at_utc": _utc(
                config["official_evidence"]["observed_at_utc"]
            ),
            "official_evidence_sha256": config["official_evidence"][
                "canonical_extracted_payload_sha256"
            ],
            "official_raw_html_archived": False,
            "latest_tradingview_calendar_capture_utc": latest_capture,
            "comparison": comparison,
            "calendar_census": census,
            "official_page_recheck_due_at_utc": (
                first_release - pd.Timedelta(hours=recheck_hours)
            ),
            "historical_pnl_loaded": False,
            "network_request_made_by_offline_verifier": False,
            "broker_action_allowed": False,
        }
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["status"])
    parser.add_argument("--as-of")
    return parser


def main() -> None:
    args = _parser().parse_args()
    evaluated = (
        pd.Timestamp.now(tz="UTC")
        if args.as_of is None
        else _utc(args.as_of)
    )
    print(json.dumps(build_status(evaluated_at_utc=evaluated), indent=2))


if __name__ == "__main__":
    main()
