from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_CONTRACT = Path("config") / "ml" / "a3_ml_training_contract.json"
DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_TRAINING_STATUS.json"
DEFAULT_MODEL_ARTIFACT = Path("outputs") / "reports" / "A3_ML_MODEL_ARTIFACT.json"
SCHEMA_VERSION = "a3_ml_model_artifact_v1"


def train_or_refuse_model(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_path = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = _read_json(contract_path)
    readiness_path = (root / contract.get("readiness_report_json", "outputs/reports/C03_TRAINING_READINESS_REPORT.json")).resolve()
    data_audit_path = (root / contract.get("data_audit_json", "outputs/reports/C02_C01_DATA_AUDIT.json")).resolve()
    snapshot_path = (root / contract.get("snapshot_csv", "outputs/reports/A3_ML_C01_SNAPSHOT_ROWS.csv")).resolve()
    model_artifact_path = (root / contract.get("model_artifact_json", str(DEFAULT_MODEL_ARTIFACT))).resolve()
    status_json = (root / contract.get("training_status_json", str(DEFAULT_STATUS_JSON))).resolve()
    model_card_md = (root / contract.get("model_card_md", "outputs/reports/A3_ML_MODEL_CARD.md")).resolve()
    pointer_path = root / "outputs" / "reports" / "C02_DATASET_POINTER.json"

    readiness = _read_json(readiness_path)
    data_audit = _read_json(data_audit_path)
    pointer = _read_json(pointer_path)
    refusal_reasons = _refusal_reasons(contract, readiness, data_audit, snapshot_path)
    if refusal_reasons:
        payload = _status_payload(
            status="REFUSED_NOT_READY",
            contract_path=contract_path,
            readiness_path=readiness_path,
            data_audit_path=data_audit_path,
            snapshot_path=snapshot_path,
            model_artifact_path=model_artifact_path,
            model_card_md=model_card_md,
            readiness=readiness,
            data_audit=data_audit,
            pointer=pointer,
            refusal_reasons=refusal_reasons,
            artifact_sha256="",
        )
        _write_status(status_json, model_card_md, payload)
        _update_pointer(pointer_path, pointer, payload, model_artifact_written=False)
        return status_json

    rows = _candidate_training_rows(_read_csv(snapshot_path))
    selected_features = list(data_audit.get("selected_features", []))
    artifact = _build_artifact(
        contract=contract,
        data_audit=data_audit,
        pointer=pointer,
        rows=rows,
        selected_features=selected_features,
    )
    model_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    model_artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    artifact_sha256 = _sha256_file(model_artifact_path)
    payload = _status_payload(
        status="TRAINED_SHADOW_ONLY",
        contract_path=contract_path,
        readiness_path=readiness_path,
        data_audit_path=data_audit_path,
        snapshot_path=snapshot_path,
        model_artifact_path=model_artifact_path,
        model_card_md=model_card_md,
        readiness=readiness,
        data_audit=data_audit,
        pointer=pointer,
        refusal_reasons=[],
        artifact_sha256=artifact_sha256,
    )
    _write_status(status_json, model_card_md, payload)
    _update_pointer(pointer_path, pointer, payload, model_artifact_written=True)
    return status_json


def render_training_status_md(payload: dict[str, Any]) -> str:
    reasons = payload.get("refusal_reasons", [])
    reason_lines = "\n".join(f"- {reason}" for reason in reasons) if reasons else "- none"
    outputs = payload.get("outputs", {})
    return "\n".join(
        [
            "# A3 ML Training Status",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authorization",
            "",
            f"- Training authorized: {str(payload['authorization']['training_authorized']).lower()}",
            f"- Python demo predictions authorized: {str(payload['authorization']['python_demo_predictions_authorized']).lower()}",
            f"- EA consumption authorized: {str(payload['authorization']['ea_consumption_authorized']).lower()}",
            f"- Broker action authorized: {str(payload['authorization']['broker_action_authorized']).lower()}",
            "",
            "## Inputs",
            "",
            f"- Readiness report: {payload['inputs']['readiness_report']}",
            f"- Data audit: {payload['inputs']['data_audit']}",
            f"- Snapshot CSV: {payload['inputs']['snapshot_csv']}",
            "",
            "## Outputs",
            "",
            f"- Model artifact: {outputs.get('model_artifact_json', '')}",
            f"- Artifact SHA256: {outputs.get('model_artifact_sha256', '')}",
            "",
            "## Refusal Reasons",
            "",
            reason_lines,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Terminal runtime change authorized: false.",
            "- EA file drop authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def render_model_card_md(payload: dict[str, Any]) -> str:
    artifact = _read_json(payload["outputs"].get("model_artifact_json", ""))
    rows = [
        {"Metric": key, "Value": str(value)}
        for key, value in artifact.get("training_summary", {}).items()
    ]
    return "\n".join(
        [
            "# A3 ML Model Card",
            "",
            f"Model status: {payload['status']}",
            "",
            "## Artifact",
            "",
            f"- Model artifact: {payload['outputs'].get('model_artifact_json', '')}",
            f"- SHA256: {payload['outputs'].get('model_artifact_sha256', '')}",
            "",
            "## Training Summary",
            "",
            _table(rows, ["Metric", "Value"]) if rows else "No model artifact was written.",
            "",
            "## Boundary",
            "",
            "Shadow scoring only. Broker action remains false.",
            "",
        ]
    )


def _refusal_reasons(
    contract: dict[str, Any],
    readiness: dict[str, Any],
    data_audit: dict[str, Any],
    snapshot_path: Path,
) -> list[str]:
    reasons: list[str] = []
    if readiness.get("status") != "PASS":
        reasons.append(f"C03 readiness is {readiness.get('status', 'MISSING')}, required PASS")
    training_decision = data_audit.get("training_decision", {})
    if not training_decision.get("supervised_training_allowed", False):
        reasons.append(f"C01 supervised training is false: {training_decision.get('reason', 'missing reason')}")
    selected_features = data_audit.get("selected_features", [])
    minimum_features = int(contract.get("minimum_selected_features", 5))
    if len(selected_features) < minimum_features:
        reasons.append(f"selected_features={len(selected_features)}, required >= {minimum_features}")
    if not snapshot_path.exists():
        reasons.append(f"snapshot CSV missing: {snapshot_path}")
        return reasons
    rows = _candidate_training_rows(_read_csv(snapshot_path))
    minimum_rows = int(contract.get("minimum_train_rows", 120))
    if len(rows) < minimum_rows:
        reasons.append(f"candidate training rows={len(rows)}, required >= {minimum_rows}")
    labels = Counter(str(row.get("y_win_expected", "")) for row in rows)
    minority = min(labels.get("0", 0), labels.get("1", 0))
    minimum_minority = int(contract.get("minimum_minority_labels", 60))
    if minority < minimum_minority:
        reasons.append(f"minority labels={minority}, required >= {minimum_minority}")
    return reasons


def _build_artifact(
    *,
    contract: dict[str, Any],
    data_audit: dict[str, Any],
    pointer: dict[str, Any],
    rows: list[dict[str, str]],
    selected_features: list[str],
) -> dict[str, Any]:
    labels = [int(row["y_win_expected"]) for row in rows]
    global_rate = _smooth_rate(sum(labels), len(labels))
    by_direction = _rates(rows, ["direction"])
    by_account_direction = _rates(rows, ["account_scope", "direction"])
    feature_schema_hash = _sha256_text(json.dumps(selected_features, separators=(",", ":"), sort_keys=True))
    dataset_version = pointer.get("dataset_version", data_audit.get("dataset_version", "UNKNOWN_DATASET"))
    model_id = f"a3_m0_base_rate_{dataset_version}_{feature_schema_hash[:8]}"
    threshold = float(contract.get("decision_threshold", 0.5))
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "TRAINED_SHADOW_ONLY",
        "created_at_utc": _utc_now(),
        "model_id": model_id,
        "model_family": contract.get("model_family", "M0_BASE_RATE_FIRST"),
        "dataset_version": dataset_version,
        "feature_schema_hash": feature_schema_hash,
        "selected_features": selected_features,
        "training_summary": {
            "rows": len(rows),
            "positive": sum(labels),
            "negative": len(labels) - sum(labels),
            "minority": min(sum(labels), len(labels) - sum(labels)),
            "global_positive_rate": round(global_rate, 10),
        },
        "rates": {
            "global": round(global_rate, 10),
            "by_direction": by_direction,
            "by_account_direction": by_account_direction,
        },
        "action_policy": {
            "threshold": threshold,
            "take_when": "p_win_calibrated >= threshold",
            "default_action": "SKIP",
            "broker_action_authorized": False,
        },
        "boundary": {
            "shadow_only": True,
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "broker_action_authorized": False,
        },
    }


def _status_payload(
    *,
    status: str,
    contract_path: Path,
    readiness_path: Path,
    data_audit_path: Path,
    snapshot_path: Path,
    model_artifact_path: Path,
    model_card_md: Path,
    readiness: dict[str, Any],
    data_audit: dict[str, Any],
    pointer: dict[str, Any],
    refusal_reasons: list[str],
    artifact_sha256: str,
) -> dict[str, Any]:
    trained = status == "TRAINED_SHADOW_ONLY"
    return {
        "status": status,
        "stage": "C05-MODEL-TRAINING",
        "created_at_utc": _utc_now(),
        "schema_version": "a3_ml_training_status_v1",
        "dataset_version": pointer.get("dataset_version", ""),
        "readiness_status": readiness.get("status", "UNKNOWN"),
        "c01_status": data_audit.get("status", "UNKNOWN"),
        "authorization": {
            "training_authorized": trained,
            "python_demo_predictions_authorized": trained,
            "ea_consumption_authorized": trained,
            "broker_action_authorized": False,
        },
        "inputs": {
            "contract": str(contract_path),
            "readiness_report": str(readiness_path),
            "data_audit": str(data_audit_path),
            "snapshot_csv": str(snapshot_path),
        },
        "outputs": {
            "model_artifact_json": str(model_artifact_path),
            "model_artifact_sha256": artifact_sha256,
            "model_card_md": str(model_card_md),
        },
        "refusal_reasons": refusal_reasons,
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "ea_file_drop_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": (
            "Run C04 shadow bridge to emit Python demo prediction rows."
            if trained
            else "Continue data collection, rerun C01/C02/C03, then rerun C05."
        ),
    }


def _candidate_training_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if str(row.get("candidate_trainable", "")).lower() == "true"
        and row.get("y_win_expected") in {"0", "1"}
    ]


def _rates(rows: list[dict[str, str]], keys: list[str]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups["|".join(str(row.get(key, "")) for key in keys)].append(row)
    output = {}
    for key, group_rows in sorted(groups.items()):
        positive = sum(1 for row in group_rows if row.get("y_win_expected") == "1")
        output[key] = {
            "rows": len(group_rows),
            "positive": positive,
            "negative": len(group_rows) - positive,
            "p_win": round(_smooth_rate(positive, len(group_rows)), 10),
        }
    return output


def _smooth_rate(positive: int, total: int) -> float:
    if total <= 0:
        return 0.5
    return (positive + 0.5) / (total + 1.0)


def _write_status(status_json: Path, model_card_md: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_training_status_md(payload), encoding="utf-8")
    model_card_md.parent.mkdir(parents=True, exist_ok=True)
    model_card_md.write_text(render_model_card_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, pointer: dict[str, Any], payload: dict[str, Any], *, model_artifact_written: bool) -> None:
    if not pointer:
        return
    pointer["c05_training_status_report"] = str(pointer_path.with_name(DEFAULT_STATUS_JSON.name))
    pointer["c05_training_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = bool(payload["authorization"]["python_demo_predictions_authorized"])
    pointer["ea_consumption_authorized"] = bool(payload["authorization"]["ea_consumption_authorized"])
    pointer["broker_action_authorized"] = False
    if model_artifact_written:
        pointer["model_artifact_json"] = payload["outputs"]["model_artifact_json"]
        pointer["model_artifact_sha256"] = payload["outputs"]["model_artifact_sha256"]
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
