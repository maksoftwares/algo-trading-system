from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_prospective_neutral_swfx_sentiment_source_census_v1.json"
)
PREREG_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_SOURCE_CENSUS_"
    "PREREG_2026_07_29.sha256.json"
)
IMPLEMENTATION_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_SOURCE_CENSUS_"
    "IMPLEMENTATION_2026_07_29.sha256.json"
)
DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-swfx-sentiment-source-census-v1"
)
SCHEMA_VERSION = "eurusd_neutral_swfx_sentiment_source_capture_v1"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite SWFX evidence: {path}")


def utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_and_verify_preregistration() -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    prereg_lock = json.loads(PREREG_LOCK_PATH.read_text(encoding="utf-8"))
    implementation_lock = json.loads(
        IMPLEMENTATION_LOCK_PATH.read_text(encoding="utf-8")
    )
    if (
        prereg_lock.get("locked_before_prospective_start") is not True
        or prereg_lock.get("locked_before_first_census_capture") is not True
        or prereg_lock.get("source_only_no_strategy") is not True
    ):
        raise RuntimeError("SWFX census preregistration was not locked in time")
    for relative, expected in prereg_lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"SWFX census preregistration drift: {relative}")
    if (
        implementation_lock.get("locked_before_first_census_capture") is not True
        or implementation_lock.get("source_only_no_strategy") is not True
    ):
        raise RuntimeError("SWFX census implementation was not locked in time")
    for relative, expected in implementation_lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"SWFX census implementation drift: {relative}")
    audit = config["source_feasibility_audit"]
    if sha256_file(ROOT / audit["path"]) != audit["sha256"]:
        raise RuntimeError("SWFX source-feasibility audit drift")
    boundaries = config["research_boundaries"]
    required_false = (
        "broker_action_allowed",
    )
    required_true = (
        "source_only",
        "historical_backfill_forbidden",
        "eurusd_prices_forbidden",
        "eurusd_returns_forbidden",
        "eurusd_pnl_forbidden",
        "oracle_rows_forbidden",
        "direction_mapping_forbidden",
        "strategy_threshold_forbidden",
        "trade_creation_forbidden",
    )
    if any(boundaries.get(name) is not True for name in required_true) or any(
        boundaries.get(name) is not False for name in required_false
    ):
        raise RuntimeError("SWFX census research boundary is incomplete")
    return config, prereg_lock


def scheduled_slots_for_date(
    value: Any, config: Mapping[str, Any]
) -> list[datetime]:
    day = utc(value).date() if not isinstance(value, date) else value
    if (
        config["capture_schedule"]["utc_weekdays_only"]
        and day.weekday() >= 5
    ):
        return []
    minutes = config["capture_schedule"]["minutes_each_hour_utc"]
    return [
        datetime(
            day.year,
            day.month,
            day.day,
            hour,
            minute,
            tzinfo=timezone.utc,
        )
        for hour in range(24)
        for minute in minutes
    ]


def is_scheduled_slot(value: Any, config: Mapping[str, Any]) -> bool:
    observed = utc(value)
    canonical = observed.replace(second=0, microsecond=0)
    return observed == canonical and canonical in scheduled_slots_for_date(
        canonical.date(), config
    )


def next_scheduled_slot(
    value: Any, config: Mapping[str, Any], *, include_current: bool = False
) -> datetime:
    observed = utc(value)
    start = observed.date()
    for offset in range(8):
        day = start + timedelta(days=offset)
        for slot in scheduled_slots_for_date(day, config):
            if slot > observed or (include_current and slot == observed):
                return slot
    raise RuntimeError("Unable to find the next SWFX census slot")


def parse_jsonp_rows(payload: bytes) -> list[dict[str, Any]]:
    text = payload.decode("utf-8-sig")
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        raise ValueError("SWFX response does not contain a JSON array")
    prefix = text[:start].strip()
    suffix = text[end + 1 :].strip()
    if prefix and not re.fullmatch(r"[A-Za-z_$][\w$.\[\]'\"]*\s*\(\s*", prefix):
        raise ValueError("SWFX JSONP callback prefix is not recognized")
    if suffix not in ("", ")", ");", ";"):
        raise ValueError("SWFX JSONP callback suffix is not recognized")
    rows = json.loads(text[start : end + 1])
    if not isinstance(rows, list) or not all(
        isinstance(row, dict) for row in rows
    ):
        raise ValueError("SWFX JSONP body is not a list of objects")
    return rows


def normalize_eurusd_row(
    rows: list[dict[str, Any]], config: Mapping[str, Any]
) -> dict[str, Any]:
    source = config["source"]
    matches = [
        row for row in rows if row.get("name") == source["instrument_name"]
    ]
    if len(matches) != 1:
        raise ValueError("SWFX response must contain exactly one EUR/USD row")
    selected = matches[0]
    normalized: dict[str, Any] = {"name": source["instrument_name"]}
    for field in source["required_fields"]:
        try:
            number = float(selected[field])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"SWFX field is not numeric: {field}") from exc
        if not math.isfinite(number):
            raise ValueError(f"SWFX field is not finite: {field}")
        normalized[field] = number
    tolerance = float(source["long_short_sum_tolerance"])
    for horizon in ("last", "sixhours", "oneday", "fivedays"):
        if abs(normalized[f"{horizon}_long"] + normalized[f"{horizon}_short"]) > (
            tolerance
        ):
            raise ValueError(f"SWFX long/short pair failed: {horizon}")
    return normalized


def source_url(config: Mapping[str, Any]) -> str:
    query = urllib.parse.urlencode(config["source"]["query"])
    return f"{config['source']['endpoint']}&{query}"


def fetch_source(
    config: Mapping[str, Any], *, timeout_seconds: float
) -> dict[str, Any]:
    url = source_url(config)
    headers = {
        "Accept": "application/javascript, text/javascript, */*; q=0.01",
        "Referer": config["source"]["official_referer"],
        "User-Agent": USER_AGENT,
    }
    request_started = datetime.now(timezone.utc)
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read(
            int(config["source"]["maximum_response_bytes"]) + 1
        )
        response_completed = datetime.now(timezone.utc)
        response_headers = list(response.headers.items())
        status = int(response.status)
        final_url = response.geturl()
    if len(payload) > int(config["source"]["maximum_response_bytes"]):
        raise ValueError("SWFX response exceeds the frozen maximum size")
    return {
        "request_started_at_utc": request_started.isoformat(),
        "response_completed_at_utc": response_completed.isoformat(),
        "request_url": url,
        "final_url": final_url,
        "request_headers": headers,
        "response_headers": response_headers,
        "http_status": status,
        "payload": payload,
    }


def _manifest_matches(
    output_root: Path, scheduled_at: datetime
) -> list[dict[str, Any]]:
    prefix = scheduled_at.strftime("CAPTURE_%Y%m%dT%H%M00Z_")
    matches: list[dict[str, Any]] = []
    for path in sorted((output_root / "manifests").glob(f"{prefix}*.json")):
        payload = path.read_bytes()
        digest = sha256_bytes(payload)
        if path.name != f"{prefix}{digest[:16]}.json":
            raise RuntimeError("SWFX census manifest filename is invalid")
        manifest = json.loads(payload)
        if utc(manifest["scheduled_at_utc"]) != scheduled_at:
            raise RuntimeError("SWFX census manifest scheduled clock drift")
        raw = manifest.get("raw")
        if raw is not None:
            raw_path = output_root / raw["relative_path"]
            if sha256_file(raw_path) != raw["sha256"]:
                raise RuntimeError("SWFX census raw evidence drift")
        normalized = manifest.get("normalized")
        if normalized is not None:
            normalized_path = output_root / normalized["relative_path"]
            if sha256_file(normalized_path) != normalized["sha256"]:
                raise RuntimeError("SWFX census normalized evidence drift")
        matches.append(
            {
                **manifest,
                "manifest_relative_path": path.relative_to(
                    output_root
                ).as_posix(),
                "manifest_sha256": digest,
            }
        )
    if len(matches) > 1:
        raise RuntimeError("Multiple SWFX census manifests exist for one slot")
    return matches


def _write_manifest(
    output_root: Path,
    scheduled_at: datetime,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    payload = _json_bytes(manifest)
    digest = sha256_bytes(payload)
    relative = (
        Path("manifests")
        / f"{scheduled_at:%Y%m%dT%H%M00Z}_{digest[:16]}.json"
    )
    relative = relative.with_name(f"CAPTURE_{relative.name}")
    write_immutable(output_root / relative, payload)
    return {
        **manifest,
        "manifest_relative_path": relative.as_posix(),
        "manifest_sha256": digest,
    }


def capture(
    scheduled_at: Any,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    now_utc: Any | None = None,
    fetcher: Callable[..., dict[str, Any]] = fetch_source,
) -> dict[str, Any]:
    config, prereg_lock = load_and_verify_preregistration()
    slot = utc(scheduled_at)
    if not is_scheduled_slot(slot, config):
        raise ValueError("Requested SWFX census time is not a frozen slot")
    start = utc(config["prospective_start_utc"])
    if slot < start:
        raise ValueError("Requested SWFX census time precedes prospective start")
    existing = _manifest_matches(output_root, slot)
    if existing:
        return existing[0]
    observed = (
        datetime.now(timezone.utc) if now_utc is None else utc(now_utc)
    )
    lateness = (observed - slot).total_seconds()
    if lateness < 0:
        return {
            "schema_version": SCHEMA_VERSION,
            "scheduled_at_utc": slot.isoformat(),
            "status": "WAITING_FOR_SCHEDULED_CLOCK",
            "next_action_utc": slot.isoformat(),
            "network_request_attempted": False,
            "source_only": True,
            "signal_generated": False,
            "trade_created": False,
            "broker_action_allowed": False,
        }
    maximum_lateness = int(
        config["capture_schedule"]["maximum_start_lateness_seconds"]
    )
    if lateness > maximum_lateness:
        return {
            "schema_version": SCHEMA_VERSION,
            "scheduled_at_utc": slot.isoformat(),
            "status": "MISSED_NO_LATE_BACKFILL",
            "observed_at_utc": observed.isoformat(),
            "network_request_attempted": False,
            "source_only": True,
            "signal_generated": False,
            "trade_created": False,
            "broker_action_allowed": False,
        }
    base = {
        "schema_version": SCHEMA_VERSION,
        "scheduled_at_utc": slot.isoformat(),
        "capture_invoked_at_utc": observed.isoformat(),
        "maximum_start_lateness_seconds": maximum_lateness,
        "preregistration_locked_at_utc": prereg_lock["locked_at_utc"],
        "preregistration_lock_sha256": sha256_file(PREREG_LOCK_PATH),
        "implementation_lock_sha256": sha256_file(IMPLEMENTATION_LOCK_PATH),
        "capture_implementation_sha256": sha256_file(Path(__file__)),
        "provider_settlement_timestamp_utc": None,
        "provider_settlement_timestamp_available": False,
        "historical_backfill_used": False,
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "direction_mapping_applied": False,
        "strategy_threshold_applied": False,
        "signal_generated": False,
        "trade_created": False,
        "broker_action_allowed": False,
    }
    fetched_evidence: dict[str, Any] | None = None
    raw_evidence: dict[str, Any] | None = None
    try:
        fetched = fetcher(
            config,
            timeout_seconds=float(
                config["capture_schedule"]["request_timeout_seconds"]
            ),
        )
        payload = fetched.pop("payload")
        fetched_evidence = fetched
        actual_request_start = utc(fetched["request_started_at_utc"])
        if (actual_request_start - slot).total_seconds() > maximum_lateness:
            raise ValueError("SWFX request started after the frozen deadline")
        if int(fetched["http_status"]) != 200:
            raise ValueError("SWFX source did not return HTTP 200")
        if len(payload) > int(config["source"]["maximum_response_bytes"]):
            raise ValueError("SWFX response exceeds the frozen maximum size")
        raw_hash = sha256_bytes(payload)
        raw_relative = (
            Path("raw")
            / f"{slot:%Y-%m-%d}"
            / f"{slot:%Y%m%dT%H%M00Z}_{raw_hash[:16]}.js"
        )
        write_immutable(output_root / raw_relative, payload)
        raw_evidence = {
            "relative_path": raw_relative.as_posix(),
            "bytes": len(payload),
            "sha256": raw_hash,
        }
        rows = parse_jsonp_rows(payload)
        eurusd = normalize_eurusd_row(rows, config)
        normalized_payload = _json_bytes(
            {
                "schema_version": (
                    "eurusd_neutral_swfx_sentiment_normalized_observation_v1"
                ),
                "scheduled_at_utc": slot.isoformat(),
                "provider_settlement_timestamp_utc": None,
                "eurusd": eurusd,
                "raw_sha256": raw_hash,
                "jsonp_row_count": len(rows),
                "source_only": True,
                "eurusd_prices_loaded": False,
                "eurusd_returns_loaded": False,
                "eurusd_pnl_loaded": False,
                "oracle_rows_loaded": False,
                "signal_generated": False,
                "trade_created": False,
                "broker_action_allowed": False,
            }
        )
        normalized_hash = sha256_bytes(normalized_payload)
        normalized_relative = (
            Path("normalized")
            / f"{slot:%Y-%m-%d}"
            / f"{slot:%Y%m%dT%H%M00Z}_{normalized_hash[:16]}.json"
        )
        write_immutable(output_root / normalized_relative, normalized_payload)
        manifest = {
            **base,
            "status": "VALID_SOURCE_CAPTURE",
            "network_request_attempted": True,
            "request": fetched,
            "raw": raw_evidence,
            "normalized": {
                "relative_path": normalized_relative.as_posix(),
                "sha256": normalized_hash,
                "jsonp_row_count": len(rows),
                "eurusd_value_sha256": sha256_bytes(_json_bytes(eurusd)),
            },
        }
    except Exception as exc:  # noqa: BLE001
        manifest = {
            **base,
            "status": "SOURCE_CAPTURE_FAILED",
            "network_request_attempted": True,
            "request": fetched_evidence,
            "raw": raw_evidence,
            "failure": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }
    return _write_manifest(output_root, slot, manifest)


def status(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    config, _ = load_and_verify_preregistration()
    observed = (
        datetime.now(timezone.utc) if now_utc is None else utc(now_utc)
    )
    start = utc(config["prospective_start_utc"])
    next_anchor = (
        observed if observed >= start else start - timedelta(microseconds=1)
    )
    next_slot = next_scheduled_slot(next_anchor, config)
    manifest_paths = sorted((output_root / "manifests").glob("CAPTURE_*.json"))
    manifests: list[dict[str, Any]] = []
    for path in manifest_paths:
        payload = path.read_bytes()
        digest = sha256_bytes(payload)
        if not path.name.endswith(f"_{digest[:16]}.json"):
            raise RuntimeError("SWFX census manifest filename/hash drift")
        manifest = json.loads(payload)
        slot = utc(manifest["scheduled_at_utc"])
        if slot < start or not is_scheduled_slot(slot, config):
            raise RuntimeError("SWFX census manifest is outside the contract")
        verified = _manifest_matches(output_root, slot)
        if len(verified) != 1:
            raise RuntimeError("SWFX census manifest verification failed")
        manifests.append(manifest)
    valid = [
        row for row in manifests if row["status"] == "VALID_SOURCE_CAPTURE"
    ]
    distinct_states = {
        row["normalized"]["eurusd_value_sha256"] for row in valid
    }
    valid_days = {
        utc(row["scheduled_at_utc"]).date().isoformat() for row in valid
    }
    elapsed_days = max(0, (observed.date() - start.date()).days)
    maximum_lateness = int(
        config["capture_schedule"]["maximum_start_lateness_seconds"]
    )
    expected_slots: list[datetime] = []
    if observed >= start:
        day = start.date()
        while day <= observed.date():
            expected_slots.extend(
                slot
                for slot in scheduled_slots_for_date(day, config)
                if slot >= start
                and slot + timedelta(seconds=maximum_lateness) <= observed
            )
            day += timedelta(days=1)
    expected_slot_keys = {slot.isoformat() for slot in expected_slots}
    manifest_by_slot = {
        utc(row["scheduled_at_utc"]).isoformat(): row for row in manifests
    }
    covered = sum(key in manifest_by_slot for key in expected_slot_keys)
    valid_keys = {
        utc(row["scheduled_at_utc"]).isoformat() for row in valid
    }
    expected_weekdays = {slot.date().isoformat() for slot in expected_slots}
    consecutive_failures = 0
    maximum_consecutive_failures = 0
    for slot in expected_slots:
        if slot.isoformat() in valid_keys:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            maximum_consecutive_failures = max(
                maximum_consecutive_failures, consecutive_failures
            )
    comparisons: list[dict[str, Any]] = []
    for path in sorted((output_root / "comparisons").glob("*.json")):
        comparison = json.loads(path.read_text(encoding="utf-8"))
        if (
            comparison.get("official_source")
            not in ("DUKASCOPY_VISIBLE_WIDGET", "DUKASCOPY_JFOREX")
            or comparison.get("schema_semantics_match") is not True
            or comparison.get("eurusd_prices_loaded") is not False
            or comparison.get("eurusd_pnl_loaded") is not False
            or comparison.get("oracle_rows_loaded") is not False
        ):
            raise RuntimeError("SWFX manual comparison is not admissible")
        linked_hash = str(comparison.get("capture_manifest_sha256", ""))
        if linked_hash not in {
            sha256_bytes(path.read_bytes()) for path in manifest_paths
        }:
            raise RuntimeError("SWFX manual comparison lacks a capture link")
        comparisons.append(comparison)
    comparison_occasions = {
        utc(row["observed_at_utc"]).date().isoformat() for row in comparisons
    }
    expected_count = len(expected_slots)
    coverage_ratio = covered / expected_count if expected_count else 0.0
    valid_ratio = len(valid_keys & expected_slot_keys) / expected_count if (
        expected_count
    ) else 0.0
    gates = config["census_gates"]
    evaluation_allowed = (
        elapsed_days >= int(gates["minimum_elapsed_calendar_days"])
        and len(expected_weekdays) >= int(gates["minimum_distinct_utc_weekdays"])
    )
    gate_results = {
        "minimum_valid_captures": (
            len(valid) >= int(gates["minimum_valid_captures"])
        ),
        "minimum_schedule_coverage_ratio": (
            coverage_ratio >= float(gates["minimum_schedule_coverage_ratio"])
        ),
        "minimum_valid_capture_ratio": (
            valid_ratio >= float(gates["minimum_valid_capture_ratio"])
        ),
        "minimum_days_with_valid_capture": (
            len(valid_days) >= int(gates["minimum_days_with_valid_capture"])
        ),
        "minimum_distinct_eurusd_states": (
            len(distinct_states)
            >= int(gates["minimum_distinct_eurusd_states"])
        ),
        "maximum_consecutive_failed_scheduled_captures": (
            maximum_consecutive_failures
            <= int(gates["maximum_consecutive_failed_scheduled_captures"])
        ),
        "minimum_manual_official_widget_comparisons": (
            len(comparison_occasions)
            >= int(gates["minimum_manual_official_widget_comparisons"])
        ),
    }
    admitted = evaluation_allowed and all(gate_results.values())
    if admitted:
        admission_reason = "ALL_FROZEN_SOURCE_GATES_PASSED"
    elif evaluation_allowed:
        admission_reason = "ONE_OR_MORE_FROZEN_SOURCE_GATES_FAILED"
    else:
        admission_reason = "CENSUS_NOT_YET_COMPLETE"
    return {
        "schema_version": "eurusd_neutral_swfx_sentiment_census_status_v1",
        "evaluated_at_utc": observed.isoformat(),
        "prospective_start_utc": start.isoformat(),
        "next_scheduled_capture_utc": next_slot.isoformat(),
        "elapsed_calendar_days": elapsed_days,
        "expected_scheduled_captures_due": expected_count,
        "scheduled_capture_manifests": covered,
        "schedule_coverage_ratio": coverage_ratio,
        "immutable_manifests": len(manifests),
        "valid_source_captures": len(valid),
        "valid_capture_ratio": valid_ratio,
        "failed_source_captures": len(manifests) - len(valid),
        "maximum_consecutive_failed_scheduled_captures": (
            maximum_consecutive_failures
        ),
        "distinct_utc_weekdays_elapsed": len(expected_weekdays),
        "days_with_valid_capture": len(valid_days),
        "distinct_eurusd_states": len(distinct_states),
        "manual_official_widget_comparison_occasions": len(
            comparison_occasions
        ),
        "gate_results": gate_results,
        "census_evaluation_allowed": evaluation_allowed,
        "source_admitted": admitted,
        "source_admission_reason": admission_reason,
        "eurusd_prices_loaded": False,
        "eurusd_returns_loaded": False,
        "eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "signal_generated": False,
        "trade_created": False,
        "broker_action_allowed": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture", "status"))
    parser.add_argument("--scheduled-at")
    parser.add_argument(
        "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "capture":
        if args.scheduled_at is None:
            raise SystemExit("--scheduled-at is required for capture")
        result = capture(args.scheduled_at, args.output_root)
    else:
        result = status(args.output_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
