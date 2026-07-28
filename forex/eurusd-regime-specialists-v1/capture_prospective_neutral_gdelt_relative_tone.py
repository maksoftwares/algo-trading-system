from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from datetime import time as datetime_time
from pathlib import Path
from typing import Any

from capture_prospective_neutral_ownership import write_immutable
from run_neutral_gdelt_coverage_census import _fetch_archive, sha256_file
from run_neutral_gdelt_relative_tone_design_audit import parse_tone_archive

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = (
    ROOT
    / "config"
    / "frozen_prospective_neutral_gdelt_relative_tone_v1.json"
)
LOCK_PATH = (
    ROOT
    / (
        "EURUSD_NEUTRAL_PROSPECTIVE_GDELT_RELATIVE_TONE_"
        "PREREG_2026_07_28.sha256.json"
    )
)
IMPLEMENTATION_LOCK_PATH = (
    ROOT
    / (
        "EURUSD_NEUTRAL_PROSPECTIVE_GDELT_RELATIVE_TONE_"
        "IMPLEMENTATION_2026_07_28.sha256.json"
    )
)
DEFAULT_OUTPUT_ROOT = Path(
    "D:/AlgoTradingData/prospective/"
    "eurusd-neutral-gdelt-relative-tone-v1/source"
)
SCHEMA_VERSION = "eurusd_neutral_prospective_gdelt_source_capture_v1"


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _entry_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return _utc(value).date()


def load_and_verify_preregistration() -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    implementation_lock = json.loads(
        IMPLEMENTATION_LOCK_PATH.read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_prospective_start_and_first_source_capture")
        is not True
        or lock.get("locked_before_first_signal_and_trade") is not True
    ):
        raise RuntimeError("Prospective GDELT expert was not locked in time")
    for relative, expected in lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"Prospective GDELT lock mismatch: {relative}")
    if (
        implementation_lock.get(
            "locked_before_first_prospective_source_capture"
        )
        is not True
        or implementation_lock.get(
            "locked_before_first_decision_signal_and_trade"
        )
        is not True
    ):
        raise RuntimeError("Prospective GDELT implementation was not locked")
    for relative, expected in implementation_lock["files"].items():
        if sha256_file(ROOT / relative) != expected:
            raise RuntimeError(
                f"Prospective GDELT implementation drift: {relative}"
            )
    strategy_lock = implementation_lock["strategy_preregistration"]
    if sha256_file(ROOT / strategy_lock["path"]) != strategy_lock["sha256"]:
        raise RuntimeError("Prospective GDELT strategy-lock reference drift")
    audit = config["source_design_audit"]
    if sha256_file(Path(audit["path"])) != audit["sha256"]:
        raise RuntimeError("Prospective GDELT source-design audit drift")
    if (
        config.get("historical_backtest_forbidden") is not True
        or config.get("historical_eurusd_pnl_forbidden") is not True
        or config.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Prospective GDELT safety contract is incomplete")
    return config, lock


def source_targets(
    config: dict[str, Any],
    entry_date: Any,
) -> list[dict[str, str]]:
    day = _entry_date(entry_date)
    source_date = day + timedelta(
        days=int(config["source_capture"]["entry_date_source_offset_days"])
    )
    targets: list[dict[str, str]] = []
    for time_text in config["source_capture"]["required_batch_times_utc"]:
        source_time = datetime_time.fromisoformat(time_text)
        timestamp = datetime.combine(
            source_date,
            source_time,
            tzinfo=timezone.utc,
        ).strftime("%Y%m%d%H%M%S")
        targets.append(
            {
                "entry_date_utc": day.isoformat(),
                "batch_timestamp_utc": timestamp,
                "url": config["source_capture"]["url_template"].format(
                    timestamp=timestamp
                ),
            }
        )
    return targets


def capture_window(
    config: dict[str, Any],
    entry_date: Any,
) -> tuple[datetime, datetime]:
    day = _entry_date(entry_date)
    earliest = datetime.combine(
        day,
        datetime_time.fromisoformat(
            config["source_capture"]["earliest_capture_attempt_utc"]
        ),
        tzinfo=timezone.utc,
    )
    deadline = datetime.combine(
        day,
        datetime_time.fromisoformat(
            config["source_capture"]["decision_deadline_utc"]
        ),
        tzinfo=timezone.utc,
    )
    return earliest, deadline


def _validated_manifests(
    output_root: Path,
    entry_date: date,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for path in sorted(
        (output_root / "manifests").glob(
            f"SOURCE_{entry_date.isoformat()}_*.json"
        )
    ):
        payload = path.read_bytes()
        digest = _sha256_bytes(payload)
        if path.name != (
            f"SOURCE_{entry_date.isoformat()}_{digest[:16]}.json"
        ):
            raise RuntimeError("Prospective GDELT manifest name is invalid")
        manifest = json.loads(payload)
        if manifest["entry_date_utc"] != entry_date.isoformat():
            raise RuntimeError("Prospective GDELT manifest date drift")
        normalized = manifest["normalized"]
        normalized_path = output_root / normalized["relative_path"]
        if sha256_file(normalized_path) != normalized["sha256"]:
            raise RuntimeError("Prospective GDELT normalized evidence drift")
        for archive in manifest["archives"]:
            if archive["status"] != "SUCCESS_VALIDATED":
                continue
            archive_path = output_root / archive["relative_path"]
            if sha256_file(archive_path) != archive["sha256"]:
                raise RuntimeError("Prospective GDELT raw archive drift")
        matches.append(
            {
                **manifest,
                "manifest_relative_path": path.relative_to(
                    output_root
                ).as_posix(),
                "manifest_sha256": digest,
            }
        )
    return matches


def status(
    entry_date: Any,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    config, _ = load_and_verify_preregistration()
    day = _entry_date(entry_date)
    observed = (
        datetime.now(timezone.utc)
        if now_utc is None
        else _utc(now_utc)
    )
    earliest, deadline = capture_window(config, day)
    manifests = _validated_manifests(output_root, day)
    complete_on_time = [
        row for row in manifests if row["status"] == "COMPLETE_ON_TIME"
    ]
    selected = min(
        complete_on_time,
        key=lambda row: row["capture_completed_at_utc"],
        default=None,
    )
    if selected is not None:
        state = "COMPLETE_ON_TIME"
        next_action = None
    elif observed < earliest:
        state = "WAITING_FOR_CAPTURE_WINDOW"
        next_action = earliest.isoformat()
    elif observed <= deadline:
        state = "CAPTURE_DUE"
        next_action = observed.isoformat()
    else:
        state = "MISSED_OR_INCOMPLETE_NO_SIGNAL"
        next_action = None
    return {
        "schema_version": SCHEMA_VERSION,
        "evaluated_at_utc": observed.isoformat(),
        "entry_date_utc": day.isoformat(),
        "status": state,
        "capture_window_start_utc": earliest.isoformat(),
        "decision_deadline_utc": deadline.isoformat(),
        "validated_manifests": len(manifests),
        "complete_on_time_manifests": len(complete_on_time),
        "selected_manifest_relative_path": (
            selected["manifest_relative_path"] if selected else None
        ),
        "selected_manifest_sha256": (
            selected["manifest_sha256"] if selected else None
        ),
        "next_action_utc": next_action,
        "historical_eurusd_pnl_loaded": False,
        "signal_generated": False,
        "broker_action_allowed": False,
    }


def capture(
    entry_date: Any,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    now_utc: Any | None = None,
    timeout_seconds: float = 60.0,
    fetcher: Callable[..., dict[str, Any]] = _fetch_archive,
) -> dict[str, Any]:
    config, lock = load_and_verify_preregistration()
    day = _entry_date(entry_date)
    if day.weekday() >= 5:
        raise ValueError("Prospective GDELT expert accepts UTC weekdays only")
    prospective_start = _utc(config["prospective_start_utc"]).date()
    if day < prospective_start:
        raise ValueError("Prospective GDELT entry date precedes frozen start")
    observed = (
        datetime.now(timezone.utc)
        if now_utc is None
        else _utc(now_utc)
    )
    earliest, deadline = capture_window(config, day)
    if observed < earliest:
        return status(day, output_root, now_utc=observed)
    existing = [
        row
        for row in _validated_manifests(output_root, day)
        if row["status"] == "COMPLETE_ON_TIME"
    ]
    if existing:
        return status(day, output_root, now_utc=observed)
    capture_started = observed
    archives: list[dict[str, Any]] = []
    document_rows: list[dict[str, Any]] = []
    network_attempts = 0
    for target in source_targets(config, day):
        relative = (
            Path("raw")
            / day.isoformat()
            / f"{target['batch_timestamp_utc']}.gkg.csv.zip"
        )
        path = output_root / relative
        fetch = fetcher(
            target["url"],
            path,
            timeout_seconds=timeout_seconds,
        )
        network_attempts += int(fetch["network_request_attempts"])
        archive_observed = (
            datetime.now(timezone.utc)
            if now_utc is None
            else observed
        )
        archive_result: dict[str, Any] = {
            **target,
            "relative_path": relative.as_posix(),
            "archive_observed_at_utc": archive_observed.isoformat(),
            "archive_reused": bool(fetch["archive_reused"]),
            "request_attempts": fetch["attempts"],
        }
        if not path.exists():
            archive_result["status"] = "MISSING_ARCHIVE"
        else:
            try:
                rows = parse_tone_archive(
                    path,
                    entry_date_utc=day.isoformat(),
                    batch_timestamp_utc=target["batch_timestamp_utc"],
                )
                archive_result.update(
                    {
                        "status": "SUCCESS_VALIDATED",
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                        "strict_documents": len(rows),
                    }
                )
                document_rows.extend(rows)
            except Exception as exc:  # noqa: BLE001
                archive_result.update(
                    {
                        "status": "FAILED_VALIDATION",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
        archives.append(archive_result)
    capture_completed = (
        datetime.now(timezone.utc) if now_utc is None else observed
    )
    complete = (
        len(archives)
        == len(config["source_capture"]["required_batch_times_utc"])
        and all(
            row["status"] == "SUCCESS_VALIDATED" for row in archives
        )
    )
    on_time = complete and all(
        _utc(row["archive_observed_at_utc"]) <= deadline for row in archives
    )
    if on_time:
        capture_status = "COMPLETE_ON_TIME"
    elif complete:
        capture_status = "COMPLETE_LATE_NO_SIGNAL"
    else:
        capture_status = "INCOMPLETE"
    normalized = {
        "schema_version": (
            "eurusd_neutral_prospective_gdelt_source_documents_v1"
        ),
        "entry_date_utc": day.isoformat(),
        "documents": document_rows,
        "eurusd_prices_loaded": False,
        "oracle_rows_loaded": False,
        "signal_generated": False,
        "broker_action_allowed": False,
    }
    normalized_bytes = _json_bytes(normalized)
    normalized_hash = _sha256_bytes(normalized_bytes)
    normalized_relative = (
        Path("normalized")
        / f"{day.isoformat()}_{normalized_hash[:16]}.json"
    )
    write_immutable(output_root / normalized_relative, normalized_bytes)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "entry_date_utc": day.isoformat(),
        "status": capture_status,
        "capture_started_at_utc": capture_started.isoformat(),
        "capture_completed_at_utc": capture_completed.isoformat(),
        "decision_deadline_utc": deadline.isoformat(),
        "preregistration_lock_sha256": sha256_file(LOCK_PATH),
        "implementation_lock_sha256": sha256_file(
            IMPLEMENTATION_LOCK_PATH
        ),
        "preregistration_locked_at_utc": lock["locked_at_utc"],
        "capture_source_sha256": sha256_file(Path(__file__)),
        "network_request_attempts": network_attempts,
        "archives": archives,
        "normalized": {
            "relative_path": normalized_relative.as_posix(),
            "sha256": normalized_hash,
            "strict_document_occurrences": len(document_rows),
        },
        "historical_eurusd_prices_loaded": False,
        "historical_eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "signal_generated": False,
        "broker_action_allowed": False,
    }
    manifest_bytes = _json_bytes(manifest)
    manifest_hash = _sha256_bytes(manifest_bytes)
    manifest_relative = (
        Path("manifests")
        / f"SOURCE_{day.isoformat()}_{manifest_hash[:16]}.json"
    )
    write_immutable(output_root / manifest_relative, manifest_bytes)
    return {
        **manifest,
        "manifest_relative_path": manifest_relative.as_posix(),
        "manifest_sha256": manifest_hash,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("capture", "status"))
    parser.add_argument("--entry-date", required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
    )
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "capture":
        result = capture(
            args.entry_date,
            args.output_root,
            timeout_seconds=args.timeout_seconds,
        )
    else:
        result = status(args.entry_date, args.output_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
