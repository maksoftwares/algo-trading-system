from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contract_expansion_config_proposal import generate_contract_expansion_config_proposal
from .contract_scope import KNOWN_EXPANSION_FAMILIES, normalize_family_name
from .label_promotion_scope import DEFAULT_ALLOWED_LABEL_STATUSES, KNOWN_TRAINABLE_LABEL_STATUSES
from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_REVIEWER_DECISION_INTAKE_STATUS.json"
LABEL_CONFIG = Path("config") / "ml" / "a3_ml_label_promotion.json"
CONTRACT_CONFIG = Path("config") / "ml" / "a3_ml_contract_expansion.json"
SCHEMA_VERSION = "a3_ml_reviewer_decision_intake_status_v1"
DECISION_SCHEMA_VERSION = "a3_ml_reviewer_decision_v1"
STATUS_WAITING = "WAITING_FOR_REVIEWER_DECISION"
STATUS_INVALID = "INVALID_REVIEWER_DECISION"
STATUS_READY = "VALID_REVIEW_READY_TO_APPLY"
STATUS_APPLIED = "APPLIED_REVIEWER_CONFIGS_FAIL_CLOSED"


def process_reviewer_decision(
    root: Path,
    decision_json: Path | None = None,
    report_json: Path | None = None,
    *,
    apply_configs: bool = False,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    decision_path = decision_json.resolve() if decision_json else None
    decision = _read_json(decision_path) if decision_path and decision_path.exists() else {}
    missing_decision = not decision
    errors = [] if missing_decision else _validation_errors(decision)
    status = _status(missing_decision, errors, apply_configs)
    write_result = _write_configs_if_allowed(root, decision, status, apply_configs)
    payload = {
        "status": status,
        "stage": "C42-REVIEWER-DECISION-INTAKE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": _read_json(reports / "C02_DATASET_POINTER.json").get("dataset_version", ""),
        "decision_json": str(decision_path) if decision_path else "",
        "apply_configs_requested": bool(apply_configs),
        "decision_summary": _decision_summary(decision),
        "validation_errors": errors,
        "config_write_result": write_result,
        "required_decision_schema": _required_decision_schema(),
        "authorization": {
            "reviewer_decision_valid": status in {STATUS_READY, STATUS_APPLIED},
            "label_config_written": bool(write_result.get("label_config_written", False)),
            "contract_config_written": bool(write_result.get("contract_config_written", False)),
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_change_authorized": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "label_config_json": str(root / LABEL_CONFIG),
            "contract_config_json": str(root / CONTRACT_CONFIG),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_reviewer_decision_intake_md(payload: dict[str, Any]) -> str:
    summary = payload.get("decision_summary", {})
    errors = "\n".join(f"- {item}" for item in payload.get("validation_errors", [])) or "- none"
    schema_rows = [{"Field": key, "Requirement": value} for key, value in payload.get("required_decision_schema", {}).items()]
    return "\n".join(
        [
            "# A3 ML Reviewer Decision Intake",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Decision JSON: {payload.get('decision_json', '') or 'not provided'}",
            f"Apply configs requested: {str(payload.get('apply_configs_requested', False)).lower()}",
            "",
            "## Decision Summary",
            "",
            f"- Review reference: {summary.get('review_reference', '') or 'missing'}.",
            f"- Label promotion approved: {str(summary.get('label_promotion_approved', False)).lower()}.",
            f"- Contract expansion approved: {str(summary.get('contract_expansion_approved', False)).lower()}.",
            f"- Allowed label statuses: {', '.join(summary.get('allowed_label_statuses', [])) or 'none'}.",
            f"- Allowed families: {', '.join(summary.get('allowed_families', [])) or 'none'}.",
            f"- Requires C03/C05/C04/C06/C10/C23 pass: {str(summary.get('requires_full_gate_pass', False)).lower()}.",
            f"- Broker action authorized by decision: {str(summary.get('broker_action_authorized_by_decision', False)).lower()}.",
            "",
            "## Validation Errors",
            "",
            errors,
            "",
            "## Config Writes",
            "",
            f"- Label config written: {str(payload.get('config_write_result', {}).get('label_config_written', False)).lower()}.",
            f"- Contract config written: {str(payload.get('config_write_result', {}).get('contract_config_written', False)).lower()}.",
            f"- C36 report: {payload.get('config_write_result', {}).get('c36_report', '') or 'not run'}.",
            "",
            "## Required Schema",
            "",
            _table(schema_rows, ["Field", "Requirement"]),
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- EA consumption authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _validation_errors(decision: dict[str, Any]) -> list[str]:
    errors = []
    if decision.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"schema_version must be {DECISION_SCHEMA_VERSION}")
    review_reference = str(decision.get("review_reference", "")).strip()
    if not review_reference:
        errors.append("review_reference is required")
    label = decision.get("label_promotion", {})
    if not isinstance(label, dict):
        errors.append("label_promotion must be an object")
        label = {}
    contract = decision.get("contract_expansion", {})
    if not isinstance(contract, dict):
        errors.append("contract_expansion must be an object")
        contract = {}
    demo = decision.get("demo_prediction_conditions", {})
    if not isinstance(demo, dict):
        errors.append("demo_prediction_conditions must be an object")
        demo = {}
    if bool(label.get("approved", False)):
        statuses = label.get("allowed_label_statuses", [])
        if not isinstance(statuses, list) or not statuses:
            errors.append("approved label_promotion requires non-empty allowed_label_statuses")
        else:
            for value in statuses:
                status = str(value or "").strip().upper()
                if status not in KNOWN_TRAINABLE_LABEL_STATUSES:
                    errors.append(f"unknown label_status: {value}")
        for key in ("minimum_mature_labels", "minimum_minority_labels"):
            if int(label.get(key, 0) or 0) <= 0:
                errors.append(f"approved label_promotion requires positive {key}")
    if bool(contract.get("approved", False)):
        families = contract.get("allowed_families", [])
        if not isinstance(families, list) or not families:
            errors.append("approved contract_expansion requires non-empty allowed_families")
        else:
            for value in families:
                family = normalize_family_name(value)
                if family not in KNOWN_EXPANSION_FAMILIES:
                    errors.append(f"unknown expansion family: {value}")
    if demo.get("requires_c03_c05_c04_c06_c10_c23_pass") is not True:
        errors.append("demo_prediction_conditions.requires_c03_c05_c04_c06_c10_c23_pass must be true")
    if bool(demo.get("broker_action_authorized", False)):
        errors.append("demo_prediction_conditions.broker_action_authorized must be false")
    return errors


def _status(missing_decision: bool, errors: list[str], apply_configs: bool) -> str:
    if missing_decision:
        return STATUS_WAITING
    if errors:
        return STATUS_INVALID
    if apply_configs:
        return STATUS_APPLIED
    return STATUS_READY


def _write_configs_if_allowed(
    root: Path,
    decision: dict[str, Any],
    status: str,
    apply_configs: bool,
) -> dict[str, Any]:
    result = {
        "label_config_written": False,
        "contract_config_written": False,
        "c36_report": "",
    }
    if status != STATUS_APPLIED or not apply_configs:
        return result
    review_reference = str(decision.get("review_reference", "")).strip()
    label = decision.get("label_promotion", {})
    if bool(label.get("approved", False)):
        label_config = _label_config(decision)
        path = root / LABEL_CONFIG
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json_atomic(path, label_config)
        result["label_config_written"] = True
    contract = decision.get("contract_expansion", {})
    if bool(contract.get("approved", False)):
        output = generate_contract_expansion_config_proposal(
            root,
            allowed_families=_normalize_families(contract.get("allowed_families", [])),
            review_reference=review_reference,
            authorize=True,
            write_config=True,
            config_json=root / CONTRACT_CONFIG,
        )
        result["contract_config_written"] = True
        result["c36_report"] = str(output)
    return result


def _label_config(decision: dict[str, Any]) -> dict[str, Any]:
    label = decision.get("label_promotion", {})
    return {
        "schema_version": "a3_ml_label_promotion_v1",
        "label_promotion_authorized": True,
        "review_reference": str(decision.get("review_reference", "")).strip(),
        "allowed_label_statuses": _normalize_statuses(label.get("allowed_label_statuses", [])),
        "minimum_mature_labels": int(label.get("minimum_mature_labels", 300) or 300),
        "minimum_minority_labels": int(label.get("minimum_minority_labels", 90) or 90),
        "require_slippage_adequate": bool(label.get("require_slippage_adequate", True)),
    }


def _decision_summary(decision: dict[str, Any]) -> dict[str, Any]:
    label = decision.get("label_promotion", {}) if isinstance(decision.get("label_promotion", {}), dict) else {}
    contract = decision.get("contract_expansion", {}) if isinstance(decision.get("contract_expansion", {}), dict) else {}
    demo = (
        decision.get("demo_prediction_conditions", {})
        if isinstance(decision.get("demo_prediction_conditions", {}), dict)
        else {}
    )
    return {
        "review_reference": str(decision.get("review_reference", "")).strip(),
        "label_promotion_approved": bool(label.get("approved", False)),
        "contract_expansion_approved": bool(contract.get("approved", False)),
        "allowed_label_statuses": _normalize_statuses(label.get("allowed_label_statuses", DEFAULT_ALLOWED_LABEL_STATUSES)),
        "allowed_families": _normalize_families(contract.get("allowed_families", [])),
        "requires_full_gate_pass": demo.get("requires_c03_c05_c04_c06_c10_c23_pass") is True,
        "broker_action_authorized_by_decision": bool(demo.get("broker_action_authorized", False)),
    }


def _required_decision_schema() -> dict[str, str]:
    return {
        "schema_version": DECISION_SCHEMA_VERSION,
        "review_reference": "non-empty reviewer note, ticket, or report id",
        "label_promotion.approved": "boolean",
        "label_promotion.allowed_label_statuses": "required non-empty list when approved=true",
        "label_promotion.require_slippage_adequate": "boolean, normally true unless reviewer explicitly overrides",
        "contract_expansion.approved": "boolean",
        "contract_expansion.allowed_families": "required non-empty list when approved=true",
        "demo_prediction_conditions.requires_c03_c05_c04_c06_c10_c23_pass": "must be true",
        "demo_prediction_conditions.broker_action_authorized": "must be false",
    }


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_WAITING:
        return "Send C41 to the reviewer and rerun C42 with --decision-json after a decision is received."
    if status == STATUS_INVALID:
        return "Fix the reviewer decision JSON. No configs were written and all model/EA authorization remains false."
    if status == STATUS_READY:
        return "Decision is valid. Rerun C42 with --apply-configs only after operator confirms the reviewer decision is final."
    return "Configs were written fail-closed. Rerun C08/C07/C03/C05/C04/C06/C10/C23; Python and EA remain unauthorized until gates pass."


def _normalize_statuses(values: Any) -> list[str]:
    if not isinstance(values, list | tuple):
        return []
    output = []
    seen = set()
    for value in values:
        status = str(value or "").strip().upper()
        if status and status not in seen:
            output.append(status)
            seen.add(status)
    return output


def _normalize_families(values: Any) -> list[str]:
    if not isinstance(values, list | tuple):
        return []
    output = []
    seen = set()
    for value in values:
        family = normalize_family_name(value)
        if family and family not in seen:
            output.append(family)
            seen.add(family)
    return output


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_reviewer_decision_intake_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c42_reviewer_decision_intake_report"] = payload["outputs"]["status_report_json"]
    pointer["c42_reviewer_decision_intake_status"] = payload["status"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path | None) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
