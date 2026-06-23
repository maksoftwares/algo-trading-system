from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _sha256_file, _table, _utc_now, _write_json_atomic


DEFAULT_CONTRACT = Path("config") / "ml" / "a3_ml_shadow_bridge_contract.json"
DEFAULT_OUTPUT_CSV = Path("outputs") / "reports" / "A3_ML_SHADOW_PREDICTIONS.csv"
DEFAULT_STATUS_JSON = Path("outputs") / "reports" / "A3_ML_SHADOW_BRIDGE_STATUS.json"
SCHEMA_VERSION = "a3_ml_shadow_predictions_v1"


def generate_shadow_bridge_outputs(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_path = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    readiness = _read_json(root / "outputs" / "reports" / "C03_TRAINING_READINESS_REPORT.json")
    pointer = _read_json(root / "outputs" / "reports" / "C02_DATASET_POINTER.json")
    scores_csv = (root / contract.get("input_scores_csv", "")).resolve()
    model_artifact_path = (root / contract.get("model_artifact_json", "outputs/reports/A3_ML_MODEL_ARTIFACT.json")).resolve()
    training_status_path = (root / contract.get("training_status_json", "outputs/reports/A3_ML_TRAINING_STATUS.json")).resolve()
    output_csv = (root / contract.get("output_predictions_csv", str(DEFAULT_OUTPUT_CSV))).resolve()
    status_json = (root / contract.get("status_report_json", str(DEFAULT_STATUS_JSON))).resolve()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0)
    model_artifact = _read_json(model_artifact_path)
    training_status = _read_json(training_status_path)
    model_artifact_present = _model_artifact_valid(model_artifact)
    model_hash = _sha256_file(model_artifact_path) if model_artifact_present else ""
    training_status_valid = _training_status_valid(training_status, model_artifact_path, model_hash)
    ready = readiness.get("status") == "PASS"
    authorized = bool(ready and model_artifact_present and training_status_valid)
    rows = _build_prediction_rows(
        scores=_read_csv(scores_csv),
        readiness=readiness,
        pointer=pointer,
        generated_at=generated_at,
        stale_after_minutes=int(contract.get("stale_after_minutes", 15)),
        model_artifact=model_artifact,
        model_hash=model_hash,
        training_status=training_status,
        authorized=authorized,
    )
    _write_csv(output_csv, rows, _prediction_fields())
    payload = {
        "status": "DISABLED_FAIL_CLOSED" if not authorized else "READY_SHADOW_ONLY",
        "stage": "A3-ML-SHADOW-BRIDGE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "readiness_status": readiness.get("status", "UNKNOWN"),
        "authorization": {
            "training_authorized": bool(readiness.get("authorization", {}).get("training_authorized", False)),
            "python_demo_predictions_authorized": authorized,
            "ea_consumption_authorized": authorized,
            "broker_action_authorized": False,
        },
        "inputs": {
            "contract": str(contract_path),
            "input_scores_csv": str(scores_csv),
            "model_artifact_json": str(model_artifact_path),
            "training_status_json": str(training_status_path),
            "readiness_report": str(root / "outputs" / "reports" / "C03_TRAINING_READINESS_REPORT.json"),
        },
        "outputs": {
            "predictions_csv": str(output_csv),
            "predictions_sha256": _sha256_file(output_csv),
            "rows": len(rows),
        },
        "readiness_failures": _failed_gate_summary(readiness),
        "model_artifact": {
            "present": model_artifact_present,
            "training_status_valid": training_status_valid,
            "model_id": model_artifact.get("model_id", "") if model_artifact_present else "",
            "model_hash": model_hash,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "terminal_runtime_change_authorized": False,
            "ea_file_drop_authorized": False,
            "broker_action_authorized": False,
        },
        "next_allowed_stage": (
            "EA may consume the Python shadow file; broker action remains false."
            if authorized
            else "Generate real TAKE/SKIP shadow scores only after C03 PASS and a locked reviewed model artifact exists."
        ),
    }
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_shadow_bridge_status_md(payload), encoding="utf-8")
    pointer["shadow_bridge_status_report"] = str(status_json)
    pointer["shadow_predictions_csv"] = str(output_csv)
    pointer["python_demo_predictions_authorized"] = authorized
    pointer["ea_consumption_authorized"] = authorized
    pointer["broker_action_authorized"] = False
    _write_json_atomic(root / "outputs" / "reports" / "C02_DATASET_POINTER.json", pointer)
    return status_json


def render_shadow_bridge_status_md(payload: dict[str, Any]) -> str:
    failures = payload.get("readiness_failures", [])
    failure_lines = "\n".join(f"- {item}" for item in failures) if failures else "- none"
    return "\n".join(
        [
            "# A3 ML Shadow Bridge Status",
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
            "## Output",
            "",
            f"- Predictions CSV: {payload['outputs']['predictions_csv']}",
            f"- Rows: {payload['outputs']['rows']}",
            f"- SHA256: {payload['outputs']['predictions_sha256']}",
            "",
            "## Readiness Failures",
            "",
            failure_lines,
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


def _build_prediction_rows(
    *,
    scores: list[dict[str, str]],
    readiness: dict[str, Any],
    pointer: dict[str, Any],
    generated_at: datetime,
    stale_after_minutes: int,
    model_artifact: dict[str, Any],
    model_hash: str,
    training_status: dict[str, Any],
    authorized: bool,
) -> list[dict[str, Any]]:
    failures = _failed_gate_summary(readiness)
    readiness_status = readiness.get("status", "UNKNOWN")
    fail_closed = not authorized
    if readiness_status != "PASS":
        reason = "C03_READINESS_NO_GO: " + ("; ".join(failures) if failures else "no passed readiness report")
    elif fail_closed:
        reason = f"C05_TRAINING_NOT_READY: {training_status.get('status', 'MISSING')}"
    else:
        reason = "MODEL_SHADOW_SCORE"
    expires = generated_at + timedelta(minutes=stale_after_minutes)
    output = []
    for row in scores:
        p_win = _predict_probability(row, model_artifact) if authorized else None
        threshold = _to_float(model_artifact.get("action_policy", {}).get("threshold"), default=0.5)
        action = "ABSTAIN" if fail_closed else ("TAKE" if p_win is not None and p_win >= threshold else "SKIP")
        output.append(
            {
                "schema_version": SCHEMA_VERSION,
                "generated_at_utc": _fmt(generated_at),
                "expires_at_utc": _fmt(expires),
                "dataset_version": pointer.get("dataset_version", ""),
                "readiness_status": readiness_status,
                "account_scope": row.get("account_scope", ""),
                "account_label": row.get("account_label", ""),
                "symbol": row.get("symbol", "XAUUSD"),
                "signal_id": row.get("source_signal_id", "") or row.get("signal_id", ""),
                "exact_signal_id": row.get("exact_signal_id", ""),
                "setup_group_id": row.get("setup_group_id", ""),
                "decision_time_utc": row.get("decision_time_utc", ""),
                "direction": row.get("direction", ""),
                "p_win_raw": _fmt_float(p_win),
                "p_win_calibrated": _fmt_float(p_win),
                "threshold": _fmt_float(threshold) if authorized else "",
                "action": action,
                "reason": reason,
                "model_id": model_artifact.get("model_id", "") if authorized else "",
                "model_hash": model_hash if authorized else "",
                "feature_schema_hash": model_artifact.get("feature_schema_hash", "") if authorized else "",
                "drift_status": "ML_SHADOW_DISABLED" if fail_closed else "OK",
                "python_demo_predictions_authorized": str(authorized).lower(),
                "ea_consumption_authorized": str(authorized).lower(),
                "broker_action_authorized": "false",
            }
        )
    return output


def _failed_gate_summary(readiness: dict[str, Any]) -> list[str]:
    return [
        f"{check.get('gate')} observed {check.get('observed')} required {check.get('required')}"
        for check in readiness.get("checks", [])
        if not check.get("passed")
    ]


def _prediction_fields() -> list[str]:
    return [
        "schema_version",
        "generated_at_utc",
        "expires_at_utc",
        "dataset_version",
        "readiness_status",
        "account_scope",
        "account_label",
        "symbol",
        "signal_id",
        "exact_signal_id",
        "setup_group_id",
        "decision_time_utc",
        "direction",
        "p_win_raw",
        "p_win_calibrated",
        "threshold",
        "action",
        "reason",
        "model_id",
        "model_hash",
        "feature_schema_hash",
        "drift_status",
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ]


def _model_artifact_valid(model_artifact: dict[str, Any]) -> bool:
    return (
        model_artifact.get("schema_version") == "a3_ml_model_artifact_v1"
        and model_artifact.get("status") == "TRAINED_SHADOW_ONLY"
        and bool(model_artifact.get("model_id"))
    )


def _training_status_valid(training_status: dict[str, Any], model_artifact_path: Path, model_hash: str) -> bool:
    if training_status.get("status") != "TRAINED_SHADOW_ONLY":
        return False
    outputs = training_status.get("outputs", {})
    if not model_hash or outputs.get("model_artifact_sha256") != model_hash:
        return False
    reported_path = str(outputs.get("model_artifact_json", ""))
    return not reported_path or Path(reported_path) == model_artifact_path


def _predict_probability(row: dict[str, str], model_artifact: dict[str, Any]) -> float:
    rates = model_artifact.get("rates", {})
    by_account_direction = rates.get("by_account_direction", {})
    account_direction_key = f"{row.get('account_scope', '')}|{row.get('direction', '')}"
    if account_direction_key in by_account_direction:
        return _to_float(by_account_direction[account_direction_key].get("p_win"), default=_global_rate(rates))
    by_direction = rates.get("by_direction", {})
    direction = row.get("direction", "")
    if direction in by_direction:
        return _to_float(by_direction[direction].get("p_win"), default=_global_rate(rates))
    return _global_rate(rates)


def _global_rate(rates: dict[str, Any]) -> float:
    return _to_float(rates.get("global"), default=0.5)


def _to_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fmt_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.10f}"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _fmt(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
