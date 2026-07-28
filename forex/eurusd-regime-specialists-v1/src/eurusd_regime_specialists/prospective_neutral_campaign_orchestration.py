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
    / "EURUSD_NEUTRAL_PROSPECTIVE_CAMPAIGN_ORCHESTRATION_PREREG_2026_07_28.sha256.json"
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
    if (
        lock.get("locked_before_prospective_start_and_first_signal")
        is not True
    ):
        raise RuntimeError("Prospective campaign orchestration is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Prospective orchestration lock mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for section in ("execution_contract", "ownership_contract"):
        reference = cfg[section]
        actual = sha256_file(PACKAGE_ROOT / reference["path"])
        if actual != reference["sha256"]:
            raise RuntimeError(
                f"Prospective orchestration reference drift: {section}"
            )
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
        return {
            str(key): _serialize(item) for key, item in value.items()
        }
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
    return (
        json.dumps(_serialize(value), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


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
        raise RuntimeError(
            f"{label} lacks required columns: {sorted(missing)}"
        )


def load_actual_evidence(root: Path) -> tuple[pd.DataFrame, dict[str, int]]:
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
        normalized_relative, normalized_path, _normalized_hash = (
            _verified_reference(
                root,
                manifest.get("normalized_snapshot", {}),
                "actual normalized snapshot",
            )
        )
        if normalized_relative in frames:
            raise RuntimeError(
                "One actual snapshot has multiple manifests"
            )
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
            if not frame["capture_semantics"].eq(
                ACTUAL_SEMANTICS
            ).all():
                raise RuntimeError("Actual snapshot semantics drift")
            if not frame[
                "actual_raw_snapshot_relative_path"
            ].astype(str).eq(raw_relative).all():
                raise RuntimeError("Actual raw path linkage drift")
            if not frame["actual_raw_snapshot_sha256"].astype(
                str
            ).str.lower().eq(raw_hash).all():
                raise RuntimeError("Actual raw hash linkage drift")
            for row in frame[
                [
                    "forecast_raw_snapshot_relative_path",
                    "forecast_raw_snapshot_sha256",
                ]
            ].drop_duplicates().itertuples(index=False):
                relative, path = _safe_relative(root, row[0])
                expected = _valid_hash(
                    row[1], "Forecast raw snapshot hash"
                )
                if relative in referenced_forecasts:
                    if referenced_forecasts[relative] != expected:
                        raise RuntimeError(
                            "Forecast snapshot has conflicting hashes"
                        )
                else:
                    if not path.is_file() or sha256_file(path) != expected:
                        raise RuntimeError(
                            "Forecast raw snapshot hash drift"
                        )
                    referenced_forecasts[relative] = expected
        frames[normalized_relative] = frame
    combined = (
        pd.concat(frames.values(), ignore_index=True)
        if frames
        else pd.DataFrame()
    )
    return combined, {
        "actual_manifests": len(manifests),
        "actual_snapshots": len(frames),
        "actual_rows": len(combined),
    }


def load_market_evidence(root: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    manifests = sorted(root.glob("manifests/*.json"))
    frames: dict[str, pd.DataFrame] = {}
    complete_rows: list[pd.DataFrame] = []
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
        normalized_relative, normalized_path, normalized_hash = (
            _verified_reference(
                root,
                manifest.get("normalized_snapshot", {}),
                "event-market normalized snapshot",
            )
        )
        if normalized_relative in frames:
            raise RuntimeError(
                "One event-market snapshot has multiple manifests"
            )
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
            raise RuntimeError(
                "Complete event-market snapshot must have one row"
            )
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
        if _utc(frame["event_time_utc"].iloc[0]) != _utc(
            manifest["event_time_utc"]
        ):
            raise RuntimeError("Event-market event time linkage drift")
        if _utc(frame["market_observed_at_utc"].iloc[0]) != _utc(
            manifest["market_observed_at_utc"]
        ):
            raise RuntimeError("Event-market observation linkage drift")
        linked = frame.copy()
        linked["market_manifest_sha256"] = manifest_hash
        linked["market_snapshot_sha256"] = normalized_hash
        complete_rows.append(linked)
    combined = (
        pd.concat(complete_rows, ignore_index=True)
        if complete_rows
        else pd.DataFrame()
    )
    return combined, {
        "market_manifests": len(manifests),
        "market_snapshots": len(frames),
        "complete_market_rows": len(combined),
    }


def load_ownership_evidence(
    root: Path,
) -> tuple[pd.DataFrame, dict[str, int]]:
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
        manifest_date = _utc(manifest["eligible_date"]).strftime(
            "%Y-%m-%d"
        )
        if manifest_date != str(record["eligible_date"]):
            raise RuntimeError("Ownership eligible-date linkage drift")
        if manifest_date in dates:
            raise RuntimeError("Date has multiple ownership records")
        if (
            str(reference.get("ownership_evidence_sha256"))
            != str(record["ownership_evidence_sha256"])
        ):
            raise RuntimeError("Ownership evidence linkage drift")
        if bool(reference.get("is_neutral")) != bool(
            record["is_neutral"]
        ):
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
    combined = (
        pd.DataFrame(list(records.values()))
        if records
        else pd.DataFrame()
    )
    return combined, {
        "ownership_manifests": len(manifests),
        "ownership_records": len(records),
        "neutral_owned_dates": (
            int(combined["is_neutral"].astype(bool).sum())
            if len(combined)
            else 0
        ),
    }


def load_complete_paths(
    root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    manifests = sorted(root.glob("manifests/MANIFEST_*.json"))
    complete: dict[str, dict[str, Any]] = {}
    incomplete = 0
    for manifest_path in manifests:
        manifest, manifest_hash = _read_manifest(manifest_path)
        if (
            manifest.get("schema_version")
            != "eurusd_neutral_prospective_trade_path_v2"
        ):
            raise RuntimeError("Unexpected trade-path manifest schema")
        signal_id = _valid_hash(
            manifest.get("signal_id"), "Trade-path signal ID"
        )
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
        if manifest.get("status") != "COMPLETE":
            incomplete += 1
            continue
        if signal_id in complete:
            raise RuntimeError("Signal has multiple complete path manifests")
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
        market_observed = _utc(manifest["market_observed_at_utc"])
        if market_observed < deadline + pd.Timedelta(seconds=60):
            raise RuntimeError("Trade path was observed before admissible time")
        expected = pd.date_range(
            entry,
            deadline - pd.Timedelta(minutes=5),
            freq="5min",
        )
        timestamps = pd.to_datetime(
            frame["timestamp_utc"], utc=True
        ).dt.as_unit("ns")
        if list(timestamps) != list(expected):
            raise RuntimeError("Complete trade path timestamps drift")
        complete[signal_id] = {
            "frame": frame,
            "entry_time_utc": entry,
            "deadline_utc": deadline,
            "path_evidence_sha256": normalized_hash,
            "path_manifest_sha256": manifest_hash,
        }
    return complete, {
        "path_manifests": len(manifests),
        "complete_paths": len(complete),
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
            raise RuntimeError(
                f"Multiple immutable {kind} records for one signal"
            )
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


def _persist_content_record(
    ledger_root: Path,
    kind: str,
    record: Mapping[str, Any],
) -> tuple[str, str]:
    signal_id = _valid_hash(
        record.get("signal_id"), f"{kind} signal ID"
    )
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
    relative = (
        Path(kind)
        / "records"
        / f"{signal_id}_{payload_hash[:16]}.json"
    )
    _write_immutable(ledger_root / relative, payload)
    return relative.as_posix(), payload_hash


def _records_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _canonical_hash(left) == _canonical_hash(right)


def reconcile_signal_records(
    generated: pd.DataFrame,
    ledger_root: Path,
    *,
    persist: bool,
) -> pd.DataFrame:
    existing = _load_content_records(ledger_root, "signals")
    generated_records = (
        generated.to_dict(orient="records")
        if not generated.empty
        else []
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
                raise RuntimeError(
                    "Existing immutable signal record drift"
                )
        elif persist:
            _persist_content_record(
                ledger_root, "signals", {**record, "broker_action_allowed": False}
            )
    result = pd.DataFrame(list(by_id.values()))
    if not result.empty:
        result = result.sort_values(
            ["entry_time_utc", "signal_id"]
        ).reset_index(drop=True)
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
    ordered = signals.sort_values(
        ["entry_time_utc", "signal_id"]
    ).to_dict(orient="records")
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
            path_evidence_sha256=str(
                path["path_evidence_sha256"]
            ),
        )
        if result["status"] != "CLOSED":
            raise RuntimeError(
                "Validated complete path did not close its signal"
            )
        result["path_manifest_sha256"] = _valid_hash(
            path["path_manifest_sha256"], "Path manifest hash"
        )
        records.append(result)
        open_until = _utc(result["exit_time_utc"])
    return pd.DataFrame(records)


def reconcile_trade_records(
    routed: pd.DataFrame,
    ledger_root: Path,
    *,
    persist: bool,
) -> pd.DataFrame:
    existing = _load_content_records(ledger_root, "trades")
    expected_terminal = {
        str(row["signal_id"]): row
        for row in routed.to_dict(orient="records")
        if str(row["status"]) in TERMINAL_STATUSES
    }
    extra = set(existing) - set(expected_terminal)
    if extra:
        raise RuntimeError(
            "Existing terminal trade is not reconstructible"
        )
    for signal_id, record in expected_terminal.items():
        if signal_id in existing:
            if not _records_equal(existing[signal_id], record):
                raise RuntimeError(
                    "Existing immutable terminal trade record drift"
                )
        elif persist:
            _persist_content_record(
                ledger_root, "trades", record
            )
    return routed


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
    }
    for name, globs in patterns.items():
        root = roots[name]
        paths: set[Path] = set()
        for pattern in globs:
            paths.update(root.glob(pattern))
        for path in sorted(
            paths, key=lambda item: item.relative_to(root).as_posix()
        ):
            digest.update(name.encode("utf-8"))
            digest.update(
                path.relative_to(root).as_posix().encode("utf-8")
            )
            digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def _ledger_inventory_hash(ledger_root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(
        [
            *ledger_root.glob("signals/records/*.json"),
            *ledger_root.glob("trades/records/*.json"),
        ],
        key=lambda item: item.relative_to(ledger_root).as_posix(),
    )
    for path in paths:
        digest.update(
            path.relative_to(ledger_root).as_posix().encode("utf-8")
        )
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
        resolved["consensus_and_actual"]
    )
    markets, market_census = load_market_evidence(
        resolved["event_market"]
    )
    ownerships, ownership_census = load_ownership_evidence(
        resolved["neutral_ownership"]
    )
    paths, path_census = load_complete_paths(
        resolved["trade_path"]
    )
    generated, signal_census = build_signal_ledger(
        actuals, markets, ownerships
    )
    signals = reconcile_signal_records(
        generated, resolved["ledger"], persist=persist
    )
    routed = route_operational_signals(signals, paths)
    routed = reconcile_trade_records(
        routed, resolved["ledger"], persist=persist
    )
    admission = evaluate_admission(
        routed, evaluated_at_utc=evaluated
    )
    status_counts = (
        {
            str(key): int(value)
            for key, value in routed["status"].value_counts().items()
        }
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
    elif signal_census["missing_ownership"] or signal_census[
        "missing_market"
    ]:
        status = "WAITING_FOR_COMPLETE_SIGNAL_EVIDENCE"
    elif pending:
        status = "WAITING_FOR_COMPLETE_TRADE_PATH"
    else:
        status = admission["status"]
    evidence_hash = _evidence_inventory_hash(resolved)
    ledger_hash = _ledger_inventory_hash(resolved["ledger"])
    result = {
        "schema_version": (
            "eurusd_neutral_prospective_campaign_process_v1"
        ),
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
        },
        "signal_census": signal_census,
        "routed_status_counts": status_counts,
        "pending_signal_ids": pending,
        "blocked_signal_ids": blocked,
        "evidence_inventory_sha256": evidence_hash,
        "ledger_inventory_sha256": ledger_hash,
        "admission": admission,
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
        relative = (
            Path("manifests")
            / f"PROCESS_{stem}_{payload_hash[:16]}.json"
        )
        _write_immutable(resolved["ledger"] / relative, payload)
        result["process_manifest_relative_path"] = relative.as_posix()
        result["process_manifest_sha256"] = payload_hash
    return _serialize(result)


__all__ = [
    "CONFIG_PATH",
    "LOCK_PATH",
    "load_actual_evidence",
    "load_complete_paths",
    "load_config",
    "load_market_evidence",
    "load_ownership_evidence",
    "process_campaign",
    "reconcile_signal_records",
    "reconcile_trade_records",
    "route_operational_signals",
    "verify_lock",
]
