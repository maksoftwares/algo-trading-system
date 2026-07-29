from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_prospective_neutral_swfx_sentiment_source_census_v1.json"
)
CAPTURE_PREREG_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_SOURCE_CENSUS_"
    "PREREG_2026_07_29.sha256.json"
)
CAPTURE_IMPLEMENTATION_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_SOURCE_CENSUS_"
    "IMPLEMENTATION_2026_07_29.sha256.json"
)
VALIDATION_PREREG_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_VALIDATION_"
    "PREREG_2026_07_29.sha256.json"
)
VALIDATION_IMPLEMENTATION_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_VALIDATION_"
    "IMPLEMENTATION_2026_07_29.sha256.json"
)
DEFAULT_EVIDENCE_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-swfx-sentiment-source-census-v1"
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def verify_validation_locks() -> dict[str, Any]:
    capture_prereg = json.loads(
        CAPTURE_PREREG_LOCK_PATH.read_text(encoding="utf-8")
    )
    capture_implementation = json.loads(
        CAPTURE_IMPLEMENTATION_LOCK_PATH.read_text(encoding="utf-8")
    )
    validation_prereg = json.loads(
        VALIDATION_PREREG_LOCK_PATH.read_text(encoding="utf-8")
    )
    validation_implementation = json.loads(
        VALIDATION_IMPLEMENTATION_LOCK_PATH.read_text(encoding="utf-8")
    )
    if (
        validation_prereg.get("locked_before_first_census_capture") is not True
        or validation_prereg.get("source_only_no_strategy") is not True
        or validation_implementation.get("locked_before_first_census_capture")
        is not True
        or validation_implementation.get("network_request_allowed") is not False
        or validation_implementation.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("SWFX validation was not locked in time")
    for lock in (
        capture_prereg,
        capture_implementation,
        validation_prereg,
        validation_implementation,
    ):
        for relative, expected in lock["files"].items():
            if _sha256_file(ROOT / relative) != expected:
                raise RuntimeError(f"SWFX validation lock drift: {relative}")
    for reference in validation_prereg["capture_contracts"]:
        if _sha256_file(ROOT / reference["path"]) != reference["sha256"]:
            raise RuntimeError("SWFX validation capture-contract drift")
    prereg_reference = validation_implementation["validation_preregistration"]
    if (
        _sha256_file(ROOT / prereg_reference["path"])
        != prereg_reference["sha256"]
    ):
        raise RuntimeError("SWFX validation preregistration-link drift")
    return {
        "config": json.loads(CONFIG_PATH.read_text(encoding="utf-8")),
        "validation_implementation": validation_implementation,
    }


def _scheduled_slot(value: datetime, config: dict[str, Any]) -> bool:
    return (
        value.weekday() < 5
        and value.second == 0
        and value.microsecond == 0
        and value.minute
        in config["capture_schedule"]["minutes_each_hour_utc"]
    )


def _expected_slots(
    start: datetime, evaluated: datetime, config: dict[str, Any]
) -> list[datetime]:
    lateness = int(
        config["capture_schedule"]["maximum_start_lateness_seconds"]
    )
    result: list[datetime] = []
    day = start.date()
    while day <= evaluated.date():
        if day.weekday() < 5:
            for hour in range(24):
                for minute in config["capture_schedule"][
                    "minutes_each_hour_utc"
                ]:
                    slot = datetime(
                        day.year,
                        day.month,
                        day.day,
                        hour,
                        minute,
                        tzinfo=timezone.utc,
                    )
                    if (
                        slot >= start
                        and slot + timedelta(seconds=lateness) <= evaluated
                    ):
                        result.append(slot)
        day += timedelta(days=1)
    return result


def _parse_raw(payload: bytes) -> list[dict[str, Any]]:
    text = payload.decode("utf-8-sig")
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        raise ValueError("Independent SWFX replay found no JSON array")
    rows = json.loads(text[start : end + 1])
    if not isinstance(rows, list) or not all(
        isinstance(row, dict) for row in rows
    ):
        raise ValueError("Independent SWFX replay body is not object rows")
    return rows


def _normalize_raw(
    rows: list[dict[str, Any]], config: dict[str, Any]
) -> dict[str, Any]:
    source = config["source"]
    matches = [
        row for row in rows if row.get("name") == source["instrument_name"]
    ]
    if len(matches) != 1:
        raise ValueError("Independent SWFX replay requires one EUR/USD row")
    selected = matches[0]
    result: dict[str, Any] = {"name": source["instrument_name"]}
    for field in source["required_fields"]:
        try:
            value = float(selected[field])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Independent SWFX replay nonnumeric field: {field}"
            ) from exc
        if not math.isfinite(value):
            raise ValueError(
                f"Independent SWFX replay nonfinite field: {field}"
            )
        result[field] = value
    tolerance = float(source["long_short_sum_tolerance"])
    for horizon in ("last", "sixhours", "oneday", "fivedays"):
        if abs(result[f"{horizon}_long"] + result[f"{horizon}_short"]) > (
            tolerance
        ):
            raise ValueError(
                f"Independent SWFX replay antipodal failure: {horizon}"
            )
    return result


def _verify_boundaries(record: dict[str, Any]) -> None:
    for field in (
        "eurusd_prices_loaded",
        "eurusd_returns_loaded",
        "eurusd_pnl_loaded",
        "oracle_rows_loaded",
        "signal_generated",
        "trade_created",
        "broker_action_allowed",
    ):
        if record.get(field) is not False:
            raise RuntimeError(f"SWFX source-only boundary failed: {field}")


def _replay_manifest(
    path: Path,
    evidence_root: Path,
    config: dict[str, Any],
    *,
    evaluated_at_utc: datetime,
) -> dict[str, Any]:
    payload = path.read_bytes()
    digest = _sha256_bytes(payload)
    if path.name != (
        f"CAPTURE_{path.name[8:24]}_{digest[:16]}.json"
    ):
        raise RuntimeError("SWFX manifest filename/hash mismatch")
    manifest = json.loads(payload)
    slot = _utc(manifest["scheduled_at_utc"])
    start = _utc(config["prospective_start_utc"])
    if slot < start or not _scheduled_slot(slot, config):
        raise RuntimeError("SWFX manifest has an invalid scheduled slot")
    if _utc(manifest["capture_invoked_at_utc"]) > evaluated_at_utc:
        return {
            "status": "EXCLUDED_AFTER_VALIDATION_AS_OF",
            "scheduled_at_utc": slot,
            "manifest_sha256": digest,
        }
    _verify_boundaries(manifest)
    status = str(manifest["status"])
    if status not in ("VALID_SOURCE_CAPTURE", "SOURCE_CAPTURE_FAILED"):
        raise RuntimeError("SWFX immutable manifest has an invalid status")
    raw_reference = manifest.get("raw")
    replayed_row: dict[str, Any] | None = None
    raw_hash: str | None = None
    if raw_reference is not None:
        raw_path = evidence_root / raw_reference["relative_path"]
        raw = raw_path.read_bytes()
        raw_hash = _sha256_bytes(raw)
        if (
            raw_hash != raw_reference["sha256"]
            or len(raw) != int(raw_reference["bytes"])
        ):
            raise RuntimeError("SWFX raw bytes/hash drift")
        rows = _parse_raw(raw)
        replayed_row = _normalize_raw(rows, config)
    if status == "VALID_SOURCE_CAPTURE":
        if replayed_row is None or raw_hash is None:
            raise RuntimeError("Valid SWFX capture lacks replayable raw evidence")
        request = manifest["request"]
        if int(request["http_status"]) != 200:
            raise RuntimeError("Valid SWFX capture lacks HTTP 200")
        request_started = _utc(request["request_started_at_utc"])
        response_completed = _utc(request["response_completed_at_utc"])
        lateness = (request_started - slot).total_seconds()
        maximum_lateness = int(
            config["capture_schedule"]["maximum_start_lateness_seconds"]
        )
        if lateness < 0 or lateness > maximum_lateness:
            raise RuntimeError("SWFX request violates the frozen clock")
        if response_completed < request_started:
            raise RuntimeError("SWFX response completed before request start")
        normalized_reference = manifest["normalized"]
        normalized_path = (
            evidence_root / normalized_reference["relative_path"]
        )
        normalized_payload = normalized_path.read_bytes()
        if (
            _sha256_bytes(normalized_payload)
            != normalized_reference["sha256"]
        ):
            raise RuntimeError("SWFX normalized evidence hash drift")
        normalized = json.loads(normalized_payload)
        _verify_boundaries(normalized)
        if (
            _utc(normalized["scheduled_at_utc"]) != slot
            or normalized["raw_sha256"] != raw_hash
            or normalized["provider_settlement_timestamp_utc"] is not None
            or normalized["eurusd"] != replayed_row
            or int(normalized["jsonp_row_count"]) != len(rows)
            or normalized_reference["eurusd_value_sha256"]
            != _sha256_bytes(_json_bytes(replayed_row))
        ):
            raise RuntimeError("SWFX normalized values failed raw replay")
    return {
        "status": status,
        "scheduled_at_utc": slot,
        "manifest_sha256": digest,
        "raw_sha256": raw_hash,
        "eurusd": replayed_row,
    }


def build_validation_status(
    evidence_root: Path = DEFAULT_EVIDENCE_ROOT,
    *,
    evaluated_at_utc: Any | None = None,
) -> dict[str, Any]:
    locked = verify_validation_locks()
    config = locked["config"]
    evaluated = (
        datetime.now(timezone.utc)
        if evaluated_at_utc is None
        else _utc(evaluated_at_utc)
    )
    start = _utc(config["prospective_start_utc"])
    expected = _expected_slots(start, evaluated, config)
    expected_keys = {slot.isoformat() for slot in expected}
    replayed: list[dict[str, Any]] = []
    seen: set[str] = set()
    excluded = 0
    for path in sorted(
        (evidence_root / "manifests").glob("CAPTURE_*.json")
    ):
        row = _replay_manifest(
            path,
            evidence_root,
            config,
            evaluated_at_utc=evaluated,
        )
        if row["status"] == "EXCLUDED_AFTER_VALIDATION_AS_OF":
            excluded += 1
            continue
        key = row["scheduled_at_utc"].isoformat()
        if key in seen:
            raise RuntimeError("Duplicate SWFX immutable manifest slot")
        seen.add(key)
        replayed.append(row)
    valid = [
        row for row in replayed if row["status"] == "VALID_SOURCE_CAPTURE"
    ]
    valid_expected = {
        row["scheduled_at_utc"].isoformat()
        for row in valid
        if row["scheduled_at_utc"].isoformat() in expected_keys
    }
    covered_expected = seen & expected_keys
    distinct_states = {
        _sha256_bytes(_json_bytes(row["eurusd"])) for row in valid
    }
    valid_days = {
        row["scheduled_at_utc"].date().isoformat() for row in valid
    }
    expected_days = {slot.date().isoformat() for slot in expected}
    consecutive = 0
    maximum_consecutive = 0
    for slot in expected:
        if slot.isoformat() in valid_expected:
            consecutive = 0
        else:
            consecutive += 1
            maximum_consecutive = max(maximum_consecutive, consecutive)
    comparison_dates: set[str] = set()
    replayed_hashes = {row["manifest_sha256"] for row in replayed}
    for path in sorted((evidence_root / "comparisons").glob("*.json")):
        comparison = json.loads(path.read_text(encoding="utf-8"))
        _verify_boundaries(comparison)
        if (
            comparison.get("official_source")
            not in ("DUKASCOPY_VISIBLE_WIDGET", "DUKASCOPY_JFOREX")
            or comparison.get("schema_semantics_match") is not True
            or comparison.get("capture_manifest_sha256") not in replayed_hashes
        ):
            raise RuntimeError("SWFX comparison evidence failed validation")
        comparison_dates.add(
            _utc(comparison["observed_at_utc"]).date().isoformat()
        )
    expected_count = len(expected)
    coverage_ratio = (
        len(covered_expected) / expected_count if expected_count else 0.0
    )
    valid_ratio = (
        len(valid_expected) / expected_count if expected_count else 0.0
    )
    elapsed_days = max(0, (evaluated.date() - start.date()).days)
    gates = config["census_gates"]
    evaluation_allowed = (
        elapsed_days >= int(gates["minimum_elapsed_calendar_days"])
        and len(expected_days)
        >= int(gates["minimum_distinct_utc_weekdays"])
    )
    gate_results = {
        "minimum_valid_captures": len(valid)
        >= int(gates["minimum_valid_captures"]),
        "minimum_schedule_coverage_ratio": coverage_ratio
        >= float(gates["minimum_schedule_coverage_ratio"]),
        "minimum_valid_capture_ratio": valid_ratio
        >= float(gates["minimum_valid_capture_ratio"]),
        "minimum_days_with_valid_capture": len(valid_days)
        >= int(gates["minimum_days_with_valid_capture"]),
        "minimum_distinct_eurusd_states": len(distinct_states)
        >= int(gates["minimum_distinct_eurusd_states"]),
        "maximum_consecutive_failed_scheduled_captures": maximum_consecutive
        <= int(gates["maximum_consecutive_failed_scheduled_captures"]),
        "minimum_manual_official_widget_comparisons": len(comparison_dates)
        >= int(gates["minimum_manual_official_widget_comparisons"]),
    }
    admitted = evaluation_allowed and all(gate_results.values())
    return {
        "schema_version": (
            "eurusd_neutral_prospective_swfx_validation_status_v1"
        ),
        "evaluated_at_utc": evaluated.isoformat(),
        "prospective_start_utc": start.isoformat(),
        "status": (
            "SOURCE_ADMITTED_FOR_SEPARATE_STRATEGY_DESIGN"
            if admitted
            else (
                "SOURCE_REJECTED_BY_FROZEN_GATES"
                if evaluation_allowed
                else "ACCUMULATING_PROSPECTIVE_SOURCE_EVIDENCE"
            )
        ),
        "expected_scheduled_captures_due": expected_count,
        "immutable_manifests_replayed": len(replayed),
        "manifests_excluded_after_validation_as_of": excluded,
        "valid_source_captures": len(valid),
        "failed_source_captures": len(replayed) - len(valid),
        "schedule_coverage_ratio": coverage_ratio,
        "valid_capture_ratio": valid_ratio,
        "days_with_valid_capture": len(valid_days),
        "distinct_eurusd_states": len(distinct_states),
        "maximum_consecutive_failed_scheduled_captures": maximum_consecutive,
        "manual_official_widget_comparison_occasions": len(comparison_dates),
        "gate_results": gate_results,
        "census_evaluation_allowed": evaluation_allowed,
        "source_admitted": admitted,
        "evidence_inventory_sha256": _sha256_bytes(
            _json_bytes(
                [
                    {
                        "scheduled_at_utc": row[
                            "scheduled_at_utc"
                        ].isoformat(),
                        "manifest_sha256": row["manifest_sha256"],
                        "raw_sha256": row["raw_sha256"],
                        "status": row["status"],
                    }
                    for row in replayed
                ]
            )
        ),
        "network_request_made": False,
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "signal_generated": False,
        "trade_created": False,
        "broker_action_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status",))
    parser.add_argument(
        "--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT
    )
    parser.add_argument("--evaluated-at-utc")
    args = parser.parse_args()
    result = build_validation_status(
        args.evidence_root,
        evaluated_at_utc=args.evaluated_at_utc,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
