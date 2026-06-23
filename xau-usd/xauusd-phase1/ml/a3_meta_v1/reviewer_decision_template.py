from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic
from .reviewer_decision_intake import DECISION_SCHEMA_VERSION


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_REVIEWER_DECISION_TEMPLATE_STATUS.json"
DEFAULT_TEMPLATE_JSON = Path("outputs") / "reports" / "A3_ML_REVIEWER_DECISION_TEMPLATE.json"
SCHEMA_VERSION = "a3_ml_reviewer_decision_template_status_v1"
STATUS_READY = "TEMPLATE_READY_FOR_REVIEWER_EDIT"


def generate_reviewer_decision_template(
    root: Path,
    report_json: Path | None = None,
    *,
    template_json: Path | None = None,
) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    template_json = (template_json or root / DEFAULT_TEMPLATE_JSON).resolve()
    c41 = _read_json(reports / "A3_ML_REVIEWER_DECISION_PACKET_STATUS.json")
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    template = _template(c41, pointer)
    template_json.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(template_json, template)
    payload = {
        "status": STATUS_READY,
        "stage": "C44-REVIEWER-DECISION-TEMPLATE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", c41.get("dataset_version", "")),
        "template_valid_without_reviewer_edit": False,
        "reviewer_must_fill": [
            "review_reference",
            "label_promotion.approved",
            "contract_expansion.approved",
            "contract_expansion.allowed_families if approved=true",
            "reviewer_notes fields",
        ],
        "evidence_digest": _evidence_digest(c41),
        "candidate_families": c41.get("contract_expansion_evidence", {}).get("candidate_families", []),
        "allowed_label_status_options": c41.get("label_promotion_evidence", {}).get("allowed_label_statuses", []),
        "commands": _commands(root, template_json),
        "authorization": {
            "template_authorizes_training": False,
            "template_authorizes_python_demo_predictions": False,
            "template_authorizes_ea_consumption": False,
            "template_authorizes_broker_action": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "config_write_attempted": False,
            "terminal_runtime_change_authorized": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
            "reviewer_decision_template_json": str(template_json),
        },
        "next_allowed_stage": "Send C41 plus this template to the reviewer; after they edit it, validate with C42 and apply with C43 only if final.",
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_reviewer_decision_template_md(payload: dict[str, Any]) -> str:
    digest = payload.get("evidence_digest", {})
    family_rows = [
        {
            "Family": item.get("family", ""),
            "Rows": item.get("would_signal_rows", 0),
            "Groups": item.get("estimated_groups", 0),
            "Files": item.get("files", 0),
        }
        for item in payload.get("candidate_families", [])
    ]
    must_fill = "\n".join(f"- {item}" for item in payload.get("reviewer_must_fill", []))
    command_lines = "\n".join(f"- {key}: `{value}`" for key, value in payload.get("commands", {}).items())
    return "\n".join(
        [
            "# A3 ML Reviewer Decision Template",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            f"Template valid without reviewer edit: {str(payload.get('template_valid_without_reviewer_edit', False)).lower()}",
            "",
            "## Evidence Digest",
            "",
            f"- C03 readiness: {digest.get('c03_status', '')}.",
            f"- C05 training: {digest.get('c05_status', '')}.",
            f"- C23 launch controller: {digest.get('c23_status', '')}.",
            f"- C40 work order: {digest.get('c40_status', '')}.",
            f"- Mature labels: {digest.get('mature_labels', 0)}.",
            f"- Positive/negative labels: {digest.get('positive_labels', 0)} / {digest.get('negative_labels', 0)}.",
            f"- Out-of-scope rows/groups: {digest.get('out_of_scope_would_signal_rows', 0)} / {digest.get('out_of_scope_estimated_groups', 0)}.",
            f"- Approval-alone result: {digest.get('approval_alone_result', '')}",
            "",
            "## Candidate Families",
            "",
            _table(family_rows, ["Family", "Rows", "Groups", "Files"]) if family_rows else "No candidate families.",
            "",
            "## Reviewer Must Fill",
            "",
            must_fill or "- none",
            "",
            "## Commands",
            "",
            command_lines,
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Config write attempted: false.",
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


def _template(c41: dict[str, Any], pointer: dict[str, Any]) -> dict[str, Any]:
    label = c41.get("label_promotion_evidence", {})
    contract = c41.get("contract_expansion_evidence", {})
    return {
        "schema_version": DECISION_SCHEMA_VERSION,
        "review_reference": "",
        "dataset_version_reviewed": pointer.get("dataset_version", c41.get("dataset_version", "")),
        "review_source_packet": c41.get("outputs", {}).get("status_report_json", ""),
        "label_promotion": {
            "approved": False,
            "allowed_label_statuses": list(label.get("allowed_label_statuses", [])),
            "minimum_mature_labels": int(label.get("minimum_mature_labels", 300) or 300),
            "minimum_minority_labels": int(label.get("minimum_minority_labels", 90) or 90),
            "require_slippage_adequate": bool(label.get("require_slippage_adequate", True)),
            "reviewer_notes": "",
        },
        "contract_expansion": {
            "approved": False,
            "allowed_families": [],
            "candidate_families_to_consider": [
                item.get("family", "") for item in contract.get("candidate_families", []) if item.get("family")
            ],
            "model_scope": "REVIEWER_TO_CHOOSE_GLOBAL_WITH_FAMILY_FEATURE_OR_PER_FAMILY",
            "reviewer_notes": "",
        },
        "demo_prediction_conditions": {
            "requires_c03_c05_c04_c06_c10_c23_pass": True,
            "a2_a3_slippage_deficits_must_close_before_ea_consumption": True,
            "broker_action_authorized": False,
            "reviewer_notes": "",
        },
        "post_decision_required_commands": [
            "python scripts/c42_process_reviewer_decision.py --root . --decision-json outputs/reports/A3_ML_REVIEWER_DECISION_TEMPLATE.json",
            "python scripts/c43_run_demo_readiness_cycle.py --root . --decision-json outputs/reports/A3_ML_REVIEWER_DECISION_TEMPLATE.json --apply-reviewer-configs",
            "python scripts/c43_run_demo_readiness_cycle.py --root . --refresh-live-readonly",
        ],
    }


def _evidence_digest(c41: dict[str, Any]) -> dict[str, Any]:
    readiness = c41.get("readiness_summary", {})
    label = c41.get("label_promotion_evidence", {})
    contract = c41.get("contract_expansion_evidence", {})
    return {
        "c03_status": readiness.get("c03_status", ""),
        "c05_status": readiness.get("c05_status", ""),
        "c23_status": readiness.get("c23_status", ""),
        "c40_status": readiness.get("c40_status", ""),
        "active_weeks_observed": readiness.get("active_weeks_observed", ""),
        "market_setup_groups_observed": readiness.get("market_setup_groups_observed", ""),
        "mature_labels": label.get("mature_labels", 0),
        "positive_labels": label.get("positive_labels", 0),
        "negative_labels": label.get("negative_labels", 0),
        "slippage_status": label.get("slippage_status", ""),
        "out_of_scope_would_signal_rows": contract.get("out_of_scope_would_signal_rows", 0),
        "out_of_scope_estimated_groups": contract.get("out_of_scope_estimated_groups", 0),
        "approval_alone_result": contract.get("approval_alone_result", ""),
    }


def _commands(root: Path, template_json: Path) -> dict[str, str]:
    python = _quote(sys.executable)
    root_arg = _quote(str(root))
    template_arg = _quote(str(template_json))
    c42 = _quote(str(root / "scripts" / "c42_process_reviewer_decision.py"))
    c43 = _quote(str(root / "scripts" / "c43_run_demo_readiness_cycle.py"))
    return {
        "validate_after_reviewer_edit": f"{python} {c42} --root {root_arg} --decision-json {template_arg}",
        "apply_after_final_review": f"{python} {c43} --root {root_arg} --decision-json {template_arg} --apply-reviewer-configs",
        "refresh_after_apply": f"{python} {c43} --root {root_arg} --refresh-live-readonly",
    }


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_reviewer_decision_template_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c44_reviewer_decision_template_report"] = payload["outputs"]["status_report_json"]
    pointer["c44_reviewer_decision_template_status"] = payload["status"]
    pointer["c44_reviewer_decision_template_json"] = payload["outputs"]["reviewer_decision_template_json"]
    pointer["python_demo_predictions_authorized"] = False
    pointer["ea_consumption_authorized"] = False
    pointer["broker_action_authorized"] = False
    _write_json_atomic(pointer_path, pointer)


def _read_json(path_or_text: str | Path) -> dict[str, Any]:
    if not path_or_text:
        return {}
    path = Path(path_or_text)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
