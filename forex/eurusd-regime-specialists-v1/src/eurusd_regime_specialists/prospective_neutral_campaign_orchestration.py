from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .prospective_neutral_macro_crossasset_execution import (
    ACTUAL_SEMANTICS,
    MARKET_SEMANTICS,
    build_signal_ledger,
    evaluate_admission,
    execute_signal,
    verify_neutral_ownership_record,
)
from .research import PACKAGE_ROOT, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_campaign_orchestration_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_CAMPAIGN_ORCHESTRATION_V1_2_PREREG_2026_07_28.sha256.json"
)
HEX_64 = re.compile(r"[0-9a-f]{64}")
TERMINAL_STATUSES = {
    "CASH_NO_TRADE",
    "SKIPPED_POSITION_ALREADY_OPEN",
    "CLOSED",
}


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_prospective_start_and_first_signal") is not True:
        raise RuntimeError("Prospective campaign orchestration is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Prospective orchestration lock mismatch: {relative}")
        checked[relative] = actual
    cfg = load_config()
    for section in (
        "execution_contract",
        "ownership_contract",
        "oracle_evaluation_contract",
    ):
        reference = cfg[section]
        actual = sha256_file(PACKAGE_ROOT / reference["path"])
        if actual != reference["sha256"]:
            raise RuntimeError(f"Prospective orchestration reference drift: {section}")
    superseded = cfg["supersedes"]
    if sha256_file(PACKAGE_ROOT / superseded["lock_path"]) != superseded["lock_sha256"]:
        raise RuntimeError("Superseded orchestration lock drift")
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
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if pd.isna(value):
        return None
    return value


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(_serialize(value), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        _serialize(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _valid_hash(value: Any, label: str) -> str:
    normalized = str(value).lower()
    if HEX_64.fullmatch(normalized) is None:
        raise RuntimeError(f"{label} is not a SHA-256")
    return normalized


def _safe_relative(root: Path, value: Any) -> tuple[str, Path]:
    relative = Path(str(value))
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError("Evidence reference escapes its declared root")
    normalized = relative.as_posix()
    root_resolved = root.resolve()
    resolved = (root / relative).resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise RuntimeError("Evidence reference escapes its declared root")
    return normalized, resolved


def _verified_reference(
    root: Path,
    reference: Mapping[str, Any],
    label: str,
) -> tuple[str, Path, str]:
    if not isinstance(reference, Mapping):
        raise TypeError(f"{label} reference is missing")
    relative, path = _safe_relative(root, reference.get("relative_path"))
    expected = _valid_hash(reference.get("sha256"), f"{label} hash")
    if not path.is_file():
        raise RuntimeError(f"{label} file is missing: {relative}")
    actual = sha256_file(path)
    if actual != expected:
        raise RuntimeError(f"{label} hash drift: {relative}")
    return relative, path, actual


def _read_manifest(path: Path) -> tuple[dict[str, Any], str]:
    payload = path.read_bytes()
    manifest = json.loads(payload)
    if not isinstance(manifest, dict):
        raise TypeError(f"Manifest is not an object: {path}")
    if manifest.get("broker_action_allowed") is not False:
        raise RuntimeError(f"Manifest broker boundary drift: {path}")
    return manifest, _sha256_bytes(payload)


def _read_frame(
    path: Path,
    expected_rows: Any,
    label: str,
) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    if len(frame) != int(expected_rows):
        raise RuntimeError(f"{label} row count drift")
    return frame


def _require_columns(
    frame: pd.DataFrame,
    required: set[str],
    label: str,
) -> None:
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"{label} lacks required columns: {sorted(missing)}")


def load_actual_evidence(
    root: Path,
    *,
    evaluated_at_utc: Any | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    evaluated = (
        None if evaluated_at_utc is None else _utc(evaluated_at_utc)
    )
    manifests = sorted(root.glob("post_release_manifests/*.json"))
    frames: dict[str, pd.DataFrame] = {}
    referenced_forecasts: dict[str, str] = {}
    for manifest_path in manifests:
        manifest, _ = _read_manifest(manifest_path)
        if (
            manifest.get("schema_version")
            != "eurusd_neutral_prospective_actual_snapshot_v1"
        ):
            raise RuntimeError("Unexpected linked-actual manifest schema")
        raw_relative, _, raw_hash = _verified_reference(
            root, manifest.get("raw_snapshot", {}), "actual raw snapshot"
        )
        _verified_reference(
            root,
            manifest.get("capture_metadata", {}),
            "actual capture metadata",
        )
        normalized_relative, normalized_path, _normalized_hash = _verified_reference(
            root,
            manifest.get("normalized_snapshot", {}),
            "actual normalized snapshot",
        )
        if normalized_relative in frames:
            raise RuntimeError("One actual snapshot has multiple manifests")
        frame = _read_frame(
            normalized_path,
            manifest["normalized_snapshot"]["rows"],
            "Actual snapshot",
        )
        if not frame.empty:
            _require_columns(
                frame,
                {
                    "event_time_utc",
                    "forecast_observed_at_utc",
                    "actual_observed_at_utc",
                    "forecast_raw_snapshot_relative_path",
                    "forecast_raw_snapshot_sha256",
                    "actual_raw_snapshot_relative_path",
                    "actual_raw_snapshot_sha256",
                    "capture_semantics",
                },
                "Actual snapshot",
            )
            if not frame["capture_semantics"].eq(ACTUAL_SEMANTICS).all():
                raise RuntimeError("Actual snapshot semantics drift")
            if (
                not frame["actual_raw_snapshot_relative_path"]
                .astype(str)
                .eq(raw_relative)
                .all()
            ):
                raise RuntimeError("Actual raw path linkage drift")
            if (
                not frame["actual_raw_snapshot_sha256"]
                .astype(str)
                .str.lower()
                .eq(raw_hash)
                .all()
            ):
                raise RuntimeError("Actual raw hash linkage drift")
            for row in (
                frame[
                    [
                        "forecast_raw_snapshot_relative_path",
                        "forecast_raw_snapshot_sha256",
                    ]
                ]
                .drop_duplicates()
                .itertuples(index=False)
            ):
                relative, path = _safe_relative(root, row[0])
                expected = _valid_hash(row[1], "Forecast raw snapshot hash")
                if relative in referenced_forecasts:
                    if referenced_forecasts[relative] != expected:
                        raise RuntimeError("Forecast snapshot has conflicting hashes")
                else:
                    if not path.is_file() or sha256_file(path) != expected:
                        raise RuntimeError("Forecast raw snapshot hash drift")
                    referenced_forecasts[relative] = expected
        frames[normalized_relative] = frame
    combined = (
        pd.concat(frames.values(), ignore_index=True) if frames else pd.DataFrame()
    )
    inventory_rows = len(combined)
    if evaluated is not None and not combined.empty:
        forecast_observed = pd.to_datetime(
            combined["forecast_observed_at_utc"], utc=True
        ).dt.as_unit("ns")
        actual_observed = pd.to_datetime(
            combined["actual_observed_at_utc"], utc=True
        ).dt.as_unit("ns")
        combined = combined.loc[
            forecast_observed.le(evaluated) & actual_observed.le(evaluated)
        ].reset_index(drop=True)
    return combined, {
        "actual_manifests": len(manifests),
        "actual_snapshots": len(frames),
        "actual_rows_inventory": inventory_rows,
        "actual_rows": len(combined),
    }


def load_market_evidence(
    root: Path,
    *,
    evaluated_at_utc: Any | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    evaluated = (
        None if evaluated_at_utc is None else _utc(evaluated_at_utc)
    )
    manifests = sorted(root.glob("manifests/*.json"))
    frames: dict[str, pd.DataFrame] = {}
    complete_rows: list[pd.DataFrame] = []
    complete_inventory = 0
    for manifest_path in manifests:
        manifest, manifest_hash = _read_manifest(manifest_path)
        if (
            manifest.get("schema_version")
            != "eurusd_neutral_prospective_event_market_m5_v1"
        ):
            raise RuntimeError("Unexpected event-market manifest schema")
        for row in manifest.get("raw_snapshots", []):
            _verified_reference(
                root,
                {
                    "relative_path": row.get("raw_relative_path"),
                    "sha256": row.get("raw_sha256"),
                },
                "event-market raw snapshot",
            )
            _verified_reference(
                root,
                {
                    "relative_path": row.get("metadata_relative_path"),
                    "sha256": row.get("metadata_sha256"),
                },
                "event-market metadata",
            )
        normalized_relative, normalized_path, normalized_hash = _verified_reference(
            root,
            manifest.get("normalized_snapshot", {}),
            "event-market normalized snapshot",
        )
        if normalized_relative in frames:
            raise RuntimeError("One event-market snapshot has multiple manifests")
        frame = _read_frame(
            normalized_path,
            manifest["normalized_snapshot"]["rows"],
            "Event-market snapshot",
        )
        frames[normalized_relative] = frame
        if manifest.get("coverage") != "COMPLETE":
            if not frame.empty:
                raise RuntimeError(
                    "Incomplete event-market manifest contains a feature"
                )
            continue
        if len(frame) != 1:
            raise RuntimeError("Complete event-market snapshot must have one row")
        _require_columns(
            frame,
            {
                "event_time_utc",
                "market_observed_at_utc",
                "capture_semantics",
            },
            "Event-market snapshot",
        )
        if str(frame["capture_semantics"].iloc[0]) != MARKET_SEMANTICS:
            raise RuntimeError("Event-market semantics drift")
        if _utc(frame["event_time_utc"].iloc[0]) != _utc(manifest["event_time_utc"]):
            raise RuntimeError("Event-market event time linkage drift")
        if _utc(frame["market_observed_at_utc"].iloc[0]) != _utc(
            manifest["market_observed_at_utc"]
        ):
            raise RuntimeError("Event-market observation linkage drift")
        complete_inventory += 1
        if (
            evaluated is not None
            and _utc(manifest["market_observed_at_utc"]) > evaluated
        ):
            continue
        linked = frame.copy()
        linked["market_manifest_sha256"] = manifest_hash
        linked["market_snapshot_sha256"] = normalized_hash
        complete_rows.append(linked)
    combined = (
        pd.concat(complete_rows, ignore_index=True) if complete_rows else pd.DataFrame()
    )
    return combined, {
        "market_manifests": len(manifests),
        "market_snapshots": len(frames),
        "complete_market_rows_inventory": complete_inventory,
        "complete_market_rows": len(combined),
    }


def load_ownership_evidence(
    root: Path,
    *,
    evaluated_at_utc: Any | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    evaluated = (
        None if evaluated_at_utc is None else _utc(evaluated_at_utc)
    )
    manifests = sorted(root.glob("manifests/MANIFEST_*.json"))
    records: dict[str, dict[str, Any]] = {}
    dates: dict[str, str] = {}
    for manifest_path in manifests:
        manifest_payload = manifest_path.read_bytes()
        manifest_hash = _sha256_bytes(manifest_payload)
        expected_name = (
            f"MANIFEST_{str(json.loads(manifest_payload)['eligible_date'])[:10]}_"
            f"{manifest_hash[:16]}.json"
        )
        if manifest_path.name != expected_name:
            raise RuntimeError("Ownership manifest name/hash drift")
        manifest = json.loads(manifest_payload)
        if manifest.get("broker_action_allowed") is not False:
            raise RuntimeError("Ownership broker boundary drift")
        reference = manifest.get("ownership_record", {})
        relative, record_path, record_hash = _verified_reference(
            root, reference, "ownership record"
        )
        if relative in records:
            raise RuntimeError("One ownership record has multiple manifests")
        record = json.loads(record_path.read_bytes())
        verify_neutral_ownership_record(record)
        manifest_date = _utc(manifest["eligible_date"]).strftime("%Y-%m-%d")
        if manifest_date != str(record["eligible_date"]):
            raise RuntimeError("Ownership eligible-date linkage drift")
        if manifest_date in dates:
            raise RuntimeError("Date has multiple ownership records")
        if str(reference.get("ownership_evidence_sha256")) != str(
            record["ownership_evidence_sha256"]
        ):
            raise RuntimeError("Ownership evidence linkage drift")
        if bool(reference.get("is_neutral")) != bool(record["is_neutral"]):
            raise RuntimeError("Ownership status linkage drift")
        expected_record_name = (
            f"{record['eligible_date']}_"
            f"{str(record['ownership_evidence_sha256'])[:16]}.json"
        )
        if record_path.name != expected_record_name:
            raise RuntimeError("Ownership record name/hash drift")
        if record_hash != sha256_file(record_path):
            raise RuntimeError("Ownership record hash drift")
        records[relative] = record
        dates[manifest_date] = relative
    visible_records = [
        record
        for record in records.values()
        if evaluated is None
        or _utc(record["ownership_observed_at_utc"]) <= evaluated
    ]
    combined = pd.DataFrame(visible_records) if visible_records else pd.DataFrame()
    return combined, {
        "ownership_manifests": len(manifests),
        "ownership_records_inventory": len(records),
        "ownership_records": len(visible_records),
        "neutral_owned_dates": (
            int(combined["is_neutral"].astype(bool).sum()) if len(combined) else 0
        ),
    }


def load_oracle_evidence(
    root: Path,
    ownership_root: Path,
    *,
    evaluated_at_utc: Any,
) -> tuple[pd.DataFrame, set[str], dict[str, int]]:
    """Load only immutable oracle dates known by the evaluation timestamp."""
    evaluated = _utc(evaluated_at_utc)
    prospective_start = _utc(load_config()["prospective_start_utc"])
    manifests = sorted(root.glob("manifests/MANIFEST_*.json"))
    labels_by_date: dict[str, pd.DataFrame] = {}
    completed_dates: set[str] = set()
    seen_dates: set[str] = set()
    not_yet_known = 0
    complete = 0
    unavailable = 0
    for manifest_path in manifests:
        manifest, manifest_hash = _read_manifest(manifest_path)
        if manifest.get("schema_version") != "eurusd_neutral_prospective_oracle_day_v1":
            raise RuntimeError("Unexpected prospective oracle manifest schema")
        day = _utc(manifest.get("oracle_date")).floor("D")
        if day != _utc(manifest.get("oracle_date")):
            raise RuntimeError("Oracle manifest date is not UTC midnight")
        if day < prospective_start or day.weekday() >= 5:
            raise RuntimeError("Oracle manifest date is outside the campaign")
        day_string = day.strftime("%Y-%m-%d")
        expected_name = f"MANIFEST_{day_string}_{manifest_hash[:16]}.json"
        if manifest_path.name != expected_name:
            raise RuntimeError("Oracle manifest name/hash drift")
        if day_string in seen_dates:
            raise RuntimeError("Oracle date has multiple manifests")
        seen_dates.add(day_string)
        if manifest.get("historical_pnl_loaded") is not False:
            raise RuntimeError("Oracle manifest historical-PnL boundary drift")

        known = _utc(manifest.get("oracle_label_known_time_utc"))
        earliest = day + pd.Timedelta(hours=36, seconds=60)
        if known < earliest:
            raise RuntimeError("Oracle label predates its safe known time")
        raw_rows = manifest.get("raw_snapshots", [])
        if not isinstance(raw_rows, list) or len(raw_rows) != 36:
            raise RuntimeError("Oracle manifest lacks the frozen 36 hours")
        expected_hours = list(pd.date_range(day, periods=36, freq="h"))
        observed_hours: list[pd.Timestamp] = []
        for row in raw_rows:
            hour = _utc(row.get("hour_utc"))
            observed = _utc(row.get("observed_at_utc"))
            if observed > known:
                raise RuntimeError("Oracle raw evidence postdates label")
            observed_hours.append(hour)
            _, raw_path, raw_hash = _verified_reference(
                root,
                {
                    "relative_path": row.get("raw_relative_path"),
                    "sha256": row.get("raw_sha256"),
                },
                "oracle raw snapshot",
            )
            _, metadata_path, _ = _verified_reference(
                root,
                {
                    "relative_path": row.get("metadata_relative_path"),
                    "sha256": row.get("metadata_sha256"),
                },
                "oracle metadata",
            )
            metadata = json.loads(metadata_path.read_bytes())
            if (
                str(metadata.get("symbol")) != "EURUSD"
                or _utc(metadata.get("hour_utc")) != hour
                or _utc(metadata.get("observed_at_utc")) != observed
                or str(metadata.get("raw_sha256")).lower() != raw_hash
                or metadata.get("broker_action_allowed") is not False
            ):
                raise RuntimeError("Oracle metadata linkage drift")
            if not raw_path.is_file():
                raise RuntimeError("Oracle raw snapshot is missing")
        if observed_hours != expected_hours:
            raise RuntimeError("Oracle hour inventory is not exact and ordered")

        _, market_path, _ = _verified_reference(
            root,
            manifest.get("normalized_market", {}),
            "oracle normalized market",
        )
        market = _read_frame(
            market_path,
            manifest["normalized_market"]["rows"],
            "Oracle normalized market",
        )
        if not market.empty:
            _require_columns(market, {"timestamp_utc"}, "Oracle normalized market")
            market_times = pd.to_datetime(market["timestamp_utc"], utc=True).dt.as_unit(
                "ns"
            )
            if (
                market_times.duplicated().any()
                or not market_times.is_monotonic_increasing
                or market_times.lt(day).any()
                or market_times.ge(day + pd.Timedelta(hours=36)).any()
            ):
                raise RuntimeError("Oracle normalized market time drift")

        _, labels_path, _ = _verified_reference(
            root,
            manifest.get("oracle_labels", {}),
            "oracle labels",
        )
        labels = _read_frame(
            labels_path,
            manifest["oracle_labels"]["rows"],
            "Oracle labels",
        )
        status = str(manifest.get("status"))
        if status == "ORACLE_DATE_COMPLETE":
            complete += 1
            if len(labels) != 4:
                raise RuntimeError("Complete oracle date must have four labels")
        elif status == "ORACLE_DATE_COMPLETE_UNAVAILABLE":
            unavailable += 1
            if not labels.empty:
                raise RuntimeError("Unavailable oracle date cannot contain labels")
        else:
            raise RuntimeError("Unexpected oracle completion status")

        inventory_hash = _valid_hash(
            manifest.get("market_inventory_sha256"),
            "Oracle market inventory hash",
        )
        if not labels.empty:
            _require_columns(
                labels,
                {
                    "oracle_date",
                    "side",
                    "entry_time_utc",
                    "regime",
                    "oracle_label_known_time_utc",
                    "oracle_date_complete",
                    "market_inventory_sha256",
                    "ownership_manifest_sha256",
                },
                "Oracle labels",
            )
            entry_times = pd.to_datetime(labels["entry_time_utc"], utc=True).dt.as_unit(
                "ns"
            )
            label_known = pd.to_datetime(
                labels["oracle_label_known_time_utc"], utc=True
            ).dt.as_unit("ns")
            if (
                not labels["oracle_date"].astype(str).eq(day_string).all()
                or not entry_times.dt.floor("D").eq(day).all()
                or not labels["side"].isin(["LONG", "SHORT"]).all()
                or not label_known.eq(known).all()
                or not labels["oracle_date_complete"].astype(bool).all()
                or not labels["market_inventory_sha256"]
                .astype(str)
                .str.lower()
                .eq(inventory_hash)
                .all()
            ):
                raise RuntimeError("Oracle label linkage drift")
            neutral_rows = int(labels["regime"].eq("NEUTRAL").sum())
            if neutral_rows != int(manifest["oracle_labels"]["neutral_rows"]):
                raise RuntimeError("Oracle Neutral row-count drift")

        context = manifest.get("next_day_context", {})
        if _utc(context.get("eligible_date")) != day + pd.Timedelta(days=1):
            raise RuntimeError("Oracle next-day context date drift")
        context_manifest_relative, context_manifest_path, context_manifest_hash = (
            _verified_reference(
                ownership_root,
                {
                    "relative_path": context.get("ownership_manifest_relative_path"),
                    "sha256": context.get("ownership_manifest_sha256"),
                },
                "oracle ownership manifest",
            )
        )
        context_manifest, _ = _read_manifest(context_manifest_path)
        if _utc(context_manifest.get("eligible_date")) != (day + pd.Timedelta(days=1)):
            raise RuntimeError("Oracle ownership manifest date drift")
        context_record_relative, context_record_path, context_record_hash = (
            _verified_reference(
                ownership_root,
                {
                    "relative_path": context.get("ownership_record_relative_path"),
                    "sha256": context.get("ownership_record_sha256"),
                },
                "oracle ownership record",
            )
        )
        record = json.loads(context_record_path.read_bytes())
        verify_neutral_ownership_record(record)
        manifest_record = context_manifest.get("ownership_record", {})
        if (
            context_manifest_relative
            != str(context.get("ownership_manifest_relative_path")).replace("\\", "/")
            or context_manifest_hash
            != str(context.get("ownership_manifest_sha256")).lower()
            or context_record_relative
            != str(context.get("ownership_record_relative_path")).replace("\\", "/")
            or context_record_hash
            != str(context.get("ownership_record_sha256")).lower()
            or str(manifest_record.get("relative_path")).replace("\\", "/")
            != context_record_relative
            or str(manifest_record.get("sha256")).lower() != context_record_hash
            or str(record.get("ownership_evidence_sha256"))
            != str(context.get("ownership_evidence_sha256"))
        ):
            raise RuntimeError("Oracle ownership context linkage drift")
        if (
            not labels.empty
            and not labels["ownership_manifest_sha256"]
            .astype(str)
            .str.lower()
            .eq(context_manifest_hash)
            .all()
        ):
            raise RuntimeError("Oracle label ownership linkage drift")

        if known > evaluated:
            not_yet_known += 1
            continue
        completed_dates.add(day_string)
        labels_by_date[day_string] = labels

    combined = (
        pd.concat(labels_by_date.values(), ignore_index=True)
        if labels_by_date
        else pd.DataFrame(
            columns=[
                "oracle_date",
                "side",
                "entry_time_utc",
                "regime",
                "oracle_label_known_time_utc",
            ]
        )
    )
    return (
        combined,
        completed_dates,
        {
            "oracle_manifests": len(manifests),
            "oracle_dates_known_as_of": len(completed_dates),
            "oracle_dates_not_yet_known": not_yet_known,
            "oracle_complete_dates": complete,
            "oracle_unavailable_dates": unavailable,
            "oracle_label_rows_known_as_of": len(combined),
            "neutral_oracle_label_rows_known_as_of": (
                int(combined["regime"].eq("NEUTRAL").sum()) if len(combined) else 0
            ),
        },
    )


def load_complete_paths(
    root: Path,
    *,
    evaluated_at_utc: Any | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    evaluated = (
        None if evaluated_at_utc is None else _utc(evaluated_at_utc)
    )
    manifests = sorted(root.glob("manifests/MANIFEST_*.json"))
    complete: dict[str, dict[str, Any]] = {}
    complete_seen: set[str] = set()
    complete_inventory = 0
    incomplete = 0
    incomplete_inventory = 0
    for manifest_path in manifests:
        manifest, manifest_hash = _read_manifest(manifest_path)
        if manifest.get("schema_version") != "eurusd_neutral_prospective_trade_path_v2":
            raise RuntimeError("Unexpected trade-path manifest schema")
        signal_id = _valid_hash(manifest.get("signal_id"), "Trade-path signal ID")
        for row in manifest.get("raw_snapshots", []):
            _verified_reference(
                root,
                {
                    "relative_path": row.get("raw_relative_path"),
                    "sha256": row.get("raw_sha256"),
                },
                "trade-path raw snapshot",
            )
            _verified_reference(
                root,
                {
                    "relative_path": row.get("metadata_relative_path"),
                    "sha256": row.get("metadata_sha256"),
                },
                "trade-path metadata",
            )
        _, normalized_path, normalized_hash = _verified_reference(
            root,
            manifest.get("normalized_snapshot", {}),
            "trade-path normalized snapshot",
        )
        frame = _read_frame(
            normalized_path,
            manifest["normalized_snapshot"]["rows"],
            "Trade-path snapshot",
        )
        market_observed = _utc(manifest["market_observed_at_utc"])
        if manifest.get("status") != "COMPLETE":
            incomplete_inventory += 1
            if evaluated is None or market_observed <= evaluated:
                incomplete += 1
            continue
        if signal_id in complete_seen:
            raise RuntimeError("Signal has multiple complete path manifests")
        complete_seen.add(signal_id)
        complete_inventory += 1
        if (
            int(manifest.get("expected_m5_rows", -1)) != 144
            or len(frame) != 144
            or manifest.get("missing_m5_timestamps")
        ):
            raise RuntimeError("Complete trade path is not continuous")
        _require_columns(
            frame,
            {
                "timestamp_utc",
                "bid_open",
                "bid_high",
                "bid_low",
                "bid_close",
                "ask_open",
                "ask_high",
                "ask_low",
                "ask_close",
            },
            "Trade-path snapshot",
        )
        entry = _utc(manifest["entry_time_utc"])
        deadline = _utc(manifest["deadline_utc"])
        if deadline != entry + pd.Timedelta(hours=12):
            raise RuntimeError("Complete trade path deadline drift")
        if market_observed < deadline + pd.Timedelta(seconds=60):
            raise RuntimeError("Trade path was observed before admissible time")
        expected = pd.date_range(
            entry,
            deadline - pd.Timedelta(minutes=5),
            freq="5min",
        )
        timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True).dt.as_unit("ns")
        if list(timestamps) != list(expected):
            raise RuntimeError("Complete trade path timestamps drift")
        if evaluated is not None and market_observed > evaluated:
            continue
        complete[signal_id] = {
            "frame": frame,
            "entry_time_utc": entry,
            "deadline_utc": deadline,
            "path_observed_at_utc": market_observed,
            "path_evidence_sha256": normalized_hash,
            "path_manifest_sha256": manifest_hash,
        }
    return complete, {
        "path_manifests": len(manifests),
        "complete_paths_inventory": complete_inventory,
        "complete_paths": len(complete),
        "incomplete_paths_inventory": incomplete_inventory,
        "incomplete_paths": incomplete,
    }


def _write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError(f"Refusing to overwrite ledger record: {path}")


def _record_directory(ledger_root: Path, kind: str) -> Path:
    if kind not in {"signals", "trades"}:
        raise ValueError(f"Unsupported ledger kind: {kind}")
    return ledger_root / kind / "records"


def _load_content_records(
    ledger_root: Path,
    kind: str,
) -> dict[str, dict[str, Any]]:
    directory = _record_directory(ledger_root, kind)
    grouped: dict[str, list[Path]] = {}
    for path in sorted(directory.glob("*.json")):
        signal_id = path.name.split("_", 1)[0]
        _valid_hash(signal_id, f"{kind} record signal ID")
        grouped.setdefault(signal_id, []).append(path)
    records: dict[str, dict[str, Any]] = {}
    for signal_id, paths in grouped.items():
        if len(paths) != 1:
            raise RuntimeError(f"Multiple immutable {kind} records for one signal")
        path = paths[0]
        payload = path.read_bytes()
        payload_hash = _sha256_bytes(payload)
        if path.name != f"{signal_id}_{payload_hash[:16]}.json":
            raise RuntimeError(f"{kind} record name/hash drift")
        wrapper = json.loads(payload)
        expected_schema = (
            "eurusd_neutral_prospective_signal_record_v1"
            if kind == "signals"
            else "eurusd_neutral_prospective_trade_record_v1"
        )
        if wrapper.get("schema_version") != expected_schema:
            raise RuntimeError(f"Unexpected {kind} record schema")
        record = wrapper.get("record")
        if not isinstance(record, dict):
            raise TypeError(f"Invalid {kind} record body")
        if str(record.get("signal_id")) != signal_id:
            raise RuntimeError(f"{kind} signal ID linkage drift")
        if record.get("broker_action_allowed") is not False:
            raise RuntimeError(f"{kind} broker boundary drift")
        records[signal_id] = record
    return records


def _record_known_at(kind: str, record: Mapping[str, Any]) -> pd.Timestamp:
    if kind == "signals":
        candidates = [
            record.get("actual_observed_at_utc"),
            record.get("market_observed_at_utc"),
            record.get("ownership_observed_at_utc"),
            record.get("observation_completed_at_utc"),
        ]
        known = [value for value in candidates if value is not None]
        if known:
            return max(_utc(value) for value in known)
        return _utc(record["entry_time_utc"])
    if kind != "trades":
        raise ValueError(f"Unsupported ledger kind: {kind}")
    if str(record.get("status")) == "CLOSED":
        observed = record.get("path_observed_at_utc")
        if observed is not None:
            return _utc(observed)
        return _utc(record["entry_time_utc"]) + pd.Timedelta(
            hours=12,
            seconds=60,
        )
    return _utc(record["entry_time_utc"])


def _visible_content_records(
    records: Mapping[str, dict[str, Any]],
    kind: str,
    evaluated_at_utc: Any | None,
) -> dict[str, dict[str, Any]]:
    if evaluated_at_utc is None:
        return dict(records)
    evaluated = _utc(evaluated_at_utc)
    return {
        signal_id: record
        for signal_id, record in records.items()
        if _record_known_at(kind, record) <= evaluated
    }


def _persist_content_record(
    ledger_root: Path,
    kind: str,
    record: Mapping[str, Any],
) -> tuple[str, str]:
    signal_id = _valid_hash(record.get("signal_id"), f"{kind} signal ID")
    schema = (
        "eurusd_neutral_prospective_signal_record_v1"
        if kind == "signals"
        else "eurusd_neutral_prospective_trade_record_v1"
    )
    payload = _json_bytes(
        {
            "schema_version": schema,
            "record": record,
        }
    )
    payload_hash = _sha256_bytes(payload)
    relative = Path(kind) / "records" / f"{signal_id}_{payload_hash[:16]}.json"
    _write_immutable(ledger_root / relative, payload)
    return relative.as_posix(), payload_hash


def _records_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _canonical_hash(left) == _canonical_hash(right)


def reconcile_signal_records(
    generated: pd.DataFrame,
    ledger_root: Path,
    *,
    persist: bool,
    evaluated_at_utc: Any | None = None,
) -> pd.DataFrame:
    existing = _visible_content_records(
        _load_content_records(ledger_root, "signals"),
        "signals",
        evaluated_at_utc,
    )
    generated_records = (
        generated.to_dict(orient="records") if not generated.empty else []
    )
    by_id: dict[str, dict[str, Any]] = {}
    events: dict[tuple[str, str, str], str] = {}
    for record in generated_records:
        signal_id = _valid_hash(record["signal_id"], "Signal ID")
        if signal_id in by_id:
            raise RuntimeError("Duplicate generated signal ID")
        event_key = (
            str(record["tradingview_event_id"]),
            str(record["tradingview_ticker"]),
            _utc(record["event_time_utc"]).isoformat(),
        )
        previous = events.get(event_key)
        if previous is not None and previous != signal_id:
            raise RuntimeError("Exact event generated multiple signals")
        events[event_key] = signal_id
        by_id[signal_id] = record
    extra = set(existing) - set(by_id)
    if extra:
        raise RuntimeError(
            "Existing signal cannot be reconstructed from current evidence"
        )
    for signal_id, record in by_id.items():
        if signal_id in existing:
            if not _records_equal(existing[signal_id], record):
                raise RuntimeError("Existing immutable signal record drift")
        elif persist:
            _persist_content_record(
                ledger_root, "signals", {**record, "broker_action_allowed": False}
            )
    result = pd.DataFrame(list(by_id.values()))
    if not result.empty:
        result = result.sort_values(["entry_time_utc", "signal_id"]).reset_index(
            drop=True
        )
    return result


def route_operational_signals(
    signals: pd.DataFrame,
    complete_paths: Mapping[str, Mapping[str, Any]],
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    unresolved = False
    if signals.empty:
        return pd.DataFrame(
            columns=[
                "signal_id",
                "status",
                "entry_time_utc",
                "exit_time_utc",
                "side",
                "r",
                "extra_half_pip_stress_r",
                "path_evidence_sha256",
            ]
        )
    ordered = signals.sort_values(["entry_time_utc", "signal_id"]).to_dict(
        orient="records"
    )
    for signal in ordered:
        signal_id = str(signal["signal_id"])
        side = str(signal["side"])
        entry = _utc(signal["entry_time_utc"])
        base = {
            "signal_id": signal_id,
            "event_time_utc": _utc(signal["event_time_utc"]),
            "entry_time_utc": entry,
            "side": side,
            "broker_action_allowed": False,
        }
        if side == "CASH":
            records.append(
                {
                    **base,
                    "status": "CASH_NO_TRADE",
                    "exit_reason": str(signal["reason"]),
                }
            )
            continue
        if unresolved:
            records.append(
                {
                    **base,
                    "status": "BLOCKED_PRIOR_POSITION_OUTCOME_PENDING",
                }
            )
            continue
        if open_until is not None and entry <= open_until:
            records.append(
                {
                    **base,
                    "status": "SKIPPED_POSITION_ALREADY_OPEN",
                    "prior_position_exit_time_utc": open_until,
                }
            )
            continue
        path = complete_paths.get(signal_id)
        if path is None:
            records.append(
                {
                    **base,
                    "status": "PENDING_COMPLETE_PATH_NOT_AVAILABLE",
                }
            )
            unresolved = True
            continue
        if _utc(path["entry_time_utc"]) != entry:
            raise RuntimeError("Complete path entry does not match signal")
        result = execute_signal(
            signal,
            path["frame"],
            path_evidence_sha256=str(path["path_evidence_sha256"]),
        )
        if result["status"] != "CLOSED":
            raise RuntimeError("Validated complete path did not close its signal")
        result["path_manifest_sha256"] = _valid_hash(
            path["path_manifest_sha256"], "Path manifest hash"
        )
        result["path_observed_at_utc"] = _utc(
            path.get(
                "path_observed_at_utc",
                entry + pd.Timedelta(hours=12, seconds=60),
            )
        )
        records.append(result)
        open_until = _utc(result["exit_time_utc"])
    return pd.DataFrame(records)


def reconcile_trade_records(
    routed: pd.DataFrame,
    ledger_root: Path,
    *,
    persist: bool,
    evaluated_at_utc: Any | None = None,
) -> pd.DataFrame:
    existing = _visible_content_records(
        _load_content_records(ledger_root, "trades"),
        "trades",
        evaluated_at_utc,
    )
    expected_terminal = {
        str(row["signal_id"]): row
        for row in routed.to_dict(orient="records")
        if str(row["status"]) in TERMINAL_STATUSES
    }
    extra = set(existing) - set(expected_terminal)
    if extra:
        raise RuntimeError("Existing terminal trade is not reconstructible")
    for signal_id, record in expected_terminal.items():
        if signal_id in existing:
            if not _records_equal(existing[signal_id], record):
                raise RuntimeError("Existing immutable terminal trade record drift")
        elif persist:
            _persist_content_record(ledger_root, "trades", record)
    return routed


def attach_completed_oracle_labels(
    routed: pd.DataFrame,
    oracle: pd.DataFrame,
    completed_dates: set[str],
    *,
    evaluated_at_utc: Any,
) -> pd.DataFrame:
    """Attach nullable evaluation labels only after terminal reconciliation."""
    result = routed.copy()
    result["oracle_same_day_same_side"] = pd.Series(
        pd.array([pd.NA] * len(result), dtype="boolean"),
        index=result.index,
    )
    if result.empty:
        return result
    evaluated = _utc(evaluated_at_utc)
    keys: set[tuple[str, str]] = set()
    if not oracle.empty:
        _require_columns(
            oracle,
            {
                "oracle_date",
                "side",
                "regime",
                "oracle_label_known_time_utc",
            },
            "Oracle evaluation labels",
        )
        known = pd.to_datetime(
            oracle["oracle_label_known_time_utc"], utc=True
        ).dt.as_unit("ns")
        if known.gt(evaluated).any():
            raise ValueError("Oracle label was not known at evaluation time")
        neutral = oracle[oracle["regime"].eq("NEUTRAL")]
        keys = set(
            zip(
                neutral["oracle_date"].astype(str),
                neutral["side"].astype(str),
                strict=True,
            )
        )
    values: list[Any] = [pd.NA] * len(result)
    for position, row in enumerate(result.to_dict(orient="records")):
        if str(row.get("status")) != "CLOSED":
            continue
        day = _utc(row["entry_time_utc"]).strftime("%Y-%m-%d")
        if day in completed_dates:
            values[position] = (day, str(row["side"])) in keys
    result["oracle_same_day_same_side"] = pd.array(values, dtype="boolean")
    return result


def _evidence_inventory_hash(roots: Mapping[str, Path]) -> str:
    digest = hashlib.sha256()
    patterns = {
        "consensus_and_actual": (
            "post_release_raw/*.json",
            "post_release_metadata/*.json",
            "post_release_normalized/*.parquet",
            "post_release_manifests/*.json",
            "raw/*.json",
        ),
        "event_market": (
            "raw/**/*.json",
            "metadata/**/*.json",
            "normalized/*.parquet",
            "manifests/*.json",
        ),
        "neutral_ownership": (
            "records/*.json",
            "manifests/*.json",
        ),
        "trade_path": (
            "raw/**/*.json",
            "metadata/**/*.json",
            "normalized/*.parquet",
            "manifests/*.json",
        ),
        "oracle_evaluation": (
            "raw/**/*.json",
            "metadata/**/*.json",
            "normalized/*.parquet",
            "labels/*.parquet",
            "manifests/*.json",
        ),
    }
    for name, globs in patterns.items():
        root = roots[name]
        paths: set[Path] = set()
        for pattern in globs:
            paths.update(root.glob(pattern))
        for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
            digest.update(name.encode("utf-8"))
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _ledger_inventory_hash(
    ledger_root: Path,
    *,
    evaluated_at_utc: Any | None = None,
) -> str:
    digest = hashlib.sha256()
    for kind in ("signals", "trades"):
        visible = _visible_content_records(
            _load_content_records(ledger_root, kind),
            kind,
            evaluated_at_utc,
        )
        for signal_id in sorted(visible):
            path = next(
                _record_directory(ledger_root, kind).glob(
                    f"{signal_id}_*.json"
                )
            )
            digest.update(path.relative_to(ledger_root).as_posix().encode("utf-8"))
            digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _validate_process_manifests(ledger_root: Path) -> None:
    for path in sorted(ledger_root.glob("manifests/PROCESS_*.json")):
        payload_hash = _sha256_bytes(path.read_bytes())
        if not path.stem.endswith(f"_{payload_hash[:16]}"):
            raise RuntimeError("Process manifest name/hash drift")


def _resolve_roots(
    roots: Mapping[str, Path | str] | None,
) -> dict[str, Path]:
    configured = load_config()["evidence_roots"]
    values = configured if roots is None else roots
    required = {
        "consensus_and_actual",
        "event_market",
        "neutral_ownership",
        "trade_path",
        "oracle_evaluation",
        "ledger",
    }
    if set(values) != required:
        raise ValueError("Campaign orchestration requires all evidence roots")
    return {name: Path(path) for name, path in values.items()}


def process_campaign(
    *,
    evaluated_at_utc: Any,
    roots: Mapping[str, Path | str] | None = None,
    persist: bool,
) -> dict[str, Any]:
    evaluated = _utc(evaluated_at_utc)
    resolved = _resolve_roots(roots)
    _validate_process_manifests(resolved["ledger"])
    actuals, actual_census = load_actual_evidence(
        resolved["consensus_and_actual"],
        evaluated_at_utc=evaluated,
    )
    markets, market_census = load_market_evidence(
        resolved["event_market"],
        evaluated_at_utc=evaluated,
    )
    ownerships, ownership_census = load_ownership_evidence(
        resolved["neutral_ownership"],
        evaluated_at_utc=evaluated,
    )
    paths, path_census = load_complete_paths(
        resolved["trade_path"],
        evaluated_at_utc=evaluated,
    )
    oracle, completed_oracle_dates, oracle_census = load_oracle_evidence(
        resolved["oracle_evaluation"],
        resolved["neutral_ownership"],
        evaluated_at_utc=evaluated,
    )
    generated, signal_census = build_signal_ledger(actuals, markets, ownerships)
    signals = reconcile_signal_records(
        generated,
        resolved["ledger"],
        persist=persist,
        evaluated_at_utc=evaluated,
    )
    routed = route_operational_signals(signals, paths)
    routed = reconcile_trade_records(
        routed,
        resolved["ledger"],
        persist=persist,
        evaluated_at_utc=evaluated,
    )
    evaluated_routed = attach_completed_oracle_labels(
        routed,
        oracle,
        completed_oracle_dates,
        evaluated_at_utc=evaluated,
    )
    admission = evaluate_admission(evaluated_routed, evaluated_at_utc=evaluated)
    status_counts = (
        {str(key): int(value) for key, value in routed["status"].value_counts().items()}
        if len(routed)
        else {}
    )
    pending = [
        str(row["signal_id"])
        for row in routed.to_dict(orient="records")
        if str(row["status"]).startswith("PENDING_")
    ]
    blocked = [
        str(row["signal_id"])
        for row in routed.to_dict(orient="records")
        if str(row["status"]).startswith("BLOCKED_")
    ]
    if admission["status"] == "WAITING_FOR_PROSPECTIVE_START":
        status = admission["status"]
    elif actual_census["actual_rows"] == 0:
        status = "WAITING_FOR_LINKED_POST_RELEASE_ACTUAL"
    elif signal_census["missing_ownership"] or signal_census["missing_market"]:
        status = "WAITING_FOR_COMPLETE_SIGNAL_EVIDENCE"
    elif pending:
        status = "WAITING_FOR_COMPLETE_TRADE_PATH"
    else:
        status = admission["status"]
    evidence_hash = _evidence_inventory_hash(resolved)
    ledger_hash = _ledger_inventory_hash(
        resolved["ledger"],
        evaluated_at_utc=evaluated,
    )
    result = {
        "schema_version": ("eurusd_neutral_prospective_campaign_process_v1_2"),
        "evaluated_at_utc": evaluated,
        "status": status,
        "persisted": bool(persist),
        "historical_pnl_loaded": False,
        "network_request_made": False,
        "broker_action_allowed": False,
        "evidence_census": {
            **actual_census,
            **market_census,
            **ownership_census,
            **path_census,
            **oracle_census,
        },
        "signal_census": signal_census,
        "routed_status_counts": status_counts,
        "pending_signal_ids": pending,
        "blocked_signal_ids": blocked,
        "evidence_inventory_sha256": evidence_hash,
        "ledger_inventory_sha256": ledger_hash,
        "admission": admission,
        "oracle_evaluation": {
            "completed_dates_known_as_of": sorted(completed_oracle_dates),
            "closed_trades_with_known_oracle_date": int(
                evaluated_routed.loc[
                    evaluated_routed["status"].eq("CLOSED"),
                    "oracle_same_day_same_side",
                ]
                .notna()
                .sum()
            )
            if len(evaluated_routed)
            else 0,
            "labels_evaluation_only": True,
            "persisted_signal_or_trade_records_changed": False,
        },
    }
    if persist:
        manifest = {
            **result,
            "persisted_signal_ids": (
                sorted(signals["signal_id"].astype(str).tolist())
                if len(signals)
                else []
            ),
            "terminal_trade_signal_ids": sorted(
                str(row["signal_id"])
                for row in routed.to_dict(orient="records")
                if str(row["status"]) in TERMINAL_STATUSES
            ),
        }
        payload = _json_bytes(manifest)
        payload_hash = _sha256_bytes(payload)
        stem = evaluated.strftime("%Y%m%dT%H%M%SZ")
        relative = Path("manifests") / f"PROCESS_{stem}_{payload_hash[:16]}.json"
        _write_immutable(resolved["ledger"] / relative, payload)
        result["process_manifest_relative_path"] = relative.as_posix()
        result["process_manifest_sha256"] = payload_hash
    return _serialize(result)


__all__ = [
    "CONFIG_PATH",
    "LOCK_PATH",
    "attach_completed_oracle_labels",
    "load_actual_evidence",
    "load_complete_paths",
    "load_config",
    "load_market_evidence",
    "load_oracle_evidence",
    "load_ownership_evidence",
    "process_campaign",
    "reconcile_signal_records",
    "reconcile_trade_records",
    "route_operational_signals",
    "verify_lock",
]
