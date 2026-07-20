from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


AUTHORITY_FLAGS = {
    "economic_outcomes_calculated_by_v67": False,
    "same_version_tuning_authorized": False,
    "model_training_authorized": False,
    "python_predictions_authorized": False,
    "ea_consumption_authorized": False,
    "demo_authorized": False,
    "live_authorized": False,
    "trade_permission": False,
    "broker_action_allowed": False,
}


def canonical_hash(payload: Mapping[str, Any], field: str) -> str:
    canonical = {key: value for key, value in payload.items() if key != field}
    encoded = json.dumps(
        canonical,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(
        (json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    temporary.replace(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def inventory_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"available": False}
    payload = load_json(path)
    summary: dict[str, Any] = {"available": True}
    for key in (
        "updated_at_utc",
        "candidate_count_all_loaded_forward_data",
        "raw_candidate_count_all_loaded_forward_data",
        "restart_episode_count_all_loaded_forward_data",
        "block_candidate_count_all_loaded_forward_data",
        "eligible_full_weekday_count",
        "eligible_full_weekdays",
        "validation_full_weekdays",
        "confirmation_full_weekdays",
        "decision",
        "status",
    ):
        if key in payload:
            summary[key] = payload[key]
    source_audit = payload.get("source_audit")
    if isinstance(source_audit, Mapping):
        for source_key in ("raw_rows", "unique_rows"):
            if source_key in source_audit:
                summary[f"source_{source_key}"] = source_audit[source_key]
    return summary


def verify_self_hash(payload: Mapping[str, Any], field: str, label: str) -> None:
    expected = payload.get(field)
    if not isinstance(expected, str) or canonical_hash(payload, field) != expected:
        raise ValueError(f"{label} self-hash changed")


def healthy_status(
    *,
    contract_sha256: str,
    child_exit_code: int,
    child_duration_seconds: float,
    v27_state: Mapping[str, Any],
    inventories: Mapping[str, Any],
) -> dict[str, Any]:
    status = {
        "schema_version": "xauusd_capital_forward_handoff_watch_v67_status",
        "updated_at_utc": utc_now(),
        "status": "HANDOFF_HEALTHY",
        "contract_sha256": contract_sha256,
        "child_exit_code": child_exit_code,
        "child_duration_seconds": round(child_duration_seconds, 3),
        "v27_decision": str(v27_state.get("decision", "UNKNOWN")),
        "v27_evidence_kind": str(v27_state["evidence_kind"]),
        "v27_evidence_sha256": str(v27_state["evidence_sha256"]),
        "inventories": dict(inventories),
        **AUTHORITY_FLAGS,
    }
    status["status_sha256"] = canonical_hash(status, "status_sha256")
    return status


def failure_status(contract_sha256: str | None, error: Exception) -> dict[str, Any]:
    status = {
        "schema_version": "xauusd_capital_forward_handoff_watch_v67_status",
        "updated_at_utc": utc_now(),
        "status": "FAILED_CLOSED",
        "contract_sha256": contract_sha256,
        "error": f"{type(error).__name__}: {error}",
        **AUTHORITY_FLAGS,
    }
    status["status_sha256"] = canonical_hash(status, "status_sha256")
    return status
