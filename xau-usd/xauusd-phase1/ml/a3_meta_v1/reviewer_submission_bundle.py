from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_REVIEWER_SUBMISSION_BUNDLE_STATUS.json"
SCHEMA_VERSION = "a3_ml_reviewer_submission_bundle_status_v1"
STATUS_READY = "READY_TO_SEND_TO_REVIEWER"
STATUS_MISSING = "MISSING_REVIEWER_ARTIFACTS"


def generate_reviewer_submission_bundle(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    c41_path = reports / "A3_ML_REVIEWER_DECISION_PACKET_STATUS.json"
    c44_status_path = reports / "A3_ML_REVIEWER_DECISION_TEMPLATE_STATUS.json"
    c44_template_path = reports / "A3_ML_REVIEWER_DECISION_TEMPLATE.json"
    c46_path = reports / "A3_ML_READINESS_PROGRESS_TRACKER_STATUS.json"
    c47_path = reports / "A3_ML_GATE_CLOSURE_PLAN_STATUS.json"
    c48_path = reports / "A3_ML_LATEST_DATASET_REPAIR_STATUS.json"
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c41 = _read_json(c41_path)
    c44 = _read_json(c44_status_path)
    c46 = _read_json(c46_path)
    c47 = _read_json(c47_path)
    c48 = _read_json(c48_path)
    template = _read_json(c44_template_path)
    artifacts = _artifacts(c41_path, c44_status_path, c44_template_path, c46_path, c47_path, c48_path)
    status = STATUS_READY if all(item["exists"] for item in artifacts) else STATUS_MISSING
    supporting_statuses = _supporting_statuses(c46, c47, c48)
    payload = {
        "status": status,
        "stage": "C45-REVIEWER-SUBMISSION-BUNDLE",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", c41.get("dataset_version", "")),
        "artifact_manifest": artifacts,
        "readiness_summary": c41.get("readiness_summary", {}),
        "supporting_statuses": supporting_statuses,
        "reviewer_submission_text": _submission_text(c41, c44_template_path, supporting_statuses),
        "reviewer_decision_template": template,
        "commands_after_reviewer_returns": _commands(root, c44_template_path),
        "authorization": {
            "bundle_authorizes_training": False,
            "bundle_authorizes_python_demo_predictions": False,
            "bundle_authorizes_ea_consumption": False,
            "bundle_authorizes_broker_action": False,
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
            "review_packet_json": str(c41_path),
            "review_packet_md": str(c41_path.with_suffix(".md")),
            "reviewer_template_json": str(c44_template_path),
            "reviewer_template_status_json": str(c44_status_path),
            "reviewer_template_status_md": str(c44_status_path.with_suffix(".md")),
            "progress_tracker_json": str(c46_path),
            "gate_closure_plan_json": str(c47_path),
            "latest_dataset_repair_json": str(c48_path),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_reviewer_submission_bundle_md(payload: dict[str, Any]) -> str:
    readiness = payload.get("readiness_summary", {})
    supporting = payload.get("supporting_statuses", {})
    artifacts = [
        {
            "Artifact": item.get("name", ""),
            "Exists": str(item.get("exists", False)).lower(),
            "Path": item.get("path", ""),
        }
        for item in payload.get("artifact_manifest", [])
    ]
    commands = "\n".join(
        f"- {key}: `{value}`" for key, value in payload.get("commands_after_reviewer_returns", {}).items()
    )
    return "\n".join(
        [
            "# A3 ML Reviewer Submission Bundle",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Current Readiness",
            "",
            f"- C03 readiness: {readiness.get('c03_status', '')}.",
            f"- C05 training: {readiness.get('c05_status', '')}.",
            f"- C23 launch controller: {readiness.get('c23_status', '')}.",
            f"- C40 work order: {readiness.get('c40_status', '')}.",
            f"- Active weeks: {readiness.get('active_weeks_observed', '')} / >=8.",
            f"- Market setup groups: {readiness.get('market_setup_groups_observed', '')} / >=300.",
            f"- Feature budget: {readiness.get('feature_budget_observed', '')} / >=6.",
            f"- Slippage readiness: {readiness.get('slippage_readiness_observed', '')} / ADEQUATE.",
            f"- C46 progress tracker: {supporting.get('c46_status', '')}.",
            f"- C47 gate closure plan: {supporting.get('c47_status', '')}.",
            f"- C48 latest dataset repair: {supporting.get('c48_status', '')}.",
            f"- Dataset completeness warnings: {supporting.get('c46_completeness_warnings_count', 0)}.",
            f"- Dataset regression warnings: {supporting.get('c46_regression_warnings_count', 0)}.",
            "",
            "## Attachments",
            "",
            _table(artifacts, ["Artifact", "Exists", "Path"]),
            "",
            "## Message To Reviewer",
            "",
            "```markdown",
            payload.get("reviewer_submission_text", ""),
            "```",
            "",
            "## Commands After Reviewer Returns",
            "",
            commands,
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


def _artifacts(
    c41_path: Path,
    c44_status_path: Path,
    c44_template_path: Path,
    c46_path: Path,
    c47_path: Path,
    c48_path: Path,
) -> list[dict[str, Any]]:
    return [
        {"name": "C41 reviewer decision packet JSON", "path": str(c41_path), "exists": c41_path.exists()},
        {"name": "C41 reviewer decision packet Markdown", "path": str(c41_path.with_suffix(".md")), "exists": c41_path.with_suffix(".md").exists()},
        {"name": "C44 reviewer decision template JSON", "path": str(c44_template_path), "exists": c44_template_path.exists()},
        {"name": "C44 reviewer decision template status", "path": str(c44_status_path), "exists": c44_status_path.exists()},
        {"name": "C44 reviewer decision template Markdown", "path": str(c44_status_path.with_suffix(".md")), "exists": c44_status_path.with_suffix(".md").exists()},
        {"name": "C46 readiness progress tracker JSON", "path": str(c46_path), "exists": c46_path.exists()},
        {"name": "C46 readiness progress tracker Markdown", "path": str(c46_path.with_suffix(".md")), "exists": c46_path.with_suffix(".md").exists()},
        {"name": "C47 gate closure plan JSON", "path": str(c47_path), "exists": c47_path.exists()},
        {"name": "C47 gate closure plan Markdown", "path": str(c47_path.with_suffix(".md")), "exists": c47_path.with_suffix(".md").exists()},
        {"name": "C48 latest dataset repair JSON", "path": str(c48_path), "exists": c48_path.exists()},
        {"name": "C48 latest dataset repair Markdown", "path": str(c48_path.with_suffix(".md")), "exists": c48_path.with_suffix(".md").exists()},
    ]


def _supporting_statuses(c46: dict[str, Any], c47: dict[str, Any], c48: dict[str, Any]) -> dict[str, Any]:
    return {
        "c46_status": c46.get("status", "MISSING"),
        "c46_completeness_warnings_count": len(c46.get("completeness_warnings", [])),
        "c46_regression_warnings_count": len(c46.get("regression_warnings", [])),
        "c47_status": c47.get("status", "MISSING"),
        "c48_status": c48.get("status", "MISSING"),
        "c48_repair_attempted": bool(c48.get("repair_attempted", False)),
    }


def _submission_text(c41: dict[str, Any], template_path: Path, supporting: dict[str, Any]) -> str:
    readiness = c41.get("readiness_summary", {})
    label = c41.get("label_promotion_evidence", {})
    contract = c41.get("contract_expansion_evidence", {})
    families = ", ".join(item.get("family", "") for item in contract.get("candidate_families", []) if item.get("family"))
    return "\n".join(
        [
            "Please review the attached A3 ML decision packet and fill the attached reviewer decision template JSON.",
            "",
            "Current state:",
            f"- Dataset: {c41.get('dataset_version', '')}",
            f"- C03: {readiness.get('c03_status', '')}",
            f"- C05: {readiness.get('c05_status', '')}",
            f"- C23: {readiness.get('c23_status', '')}",
            f"- Active weeks: {readiness.get('active_weeks_observed', '')} / >=8",
            f"- Market setup groups: {readiness.get('market_setup_groups_observed', '')} / >=300",
            f"- Feature budget: {readiness.get('feature_budget_observed', '')} / >=6",
            f"- Slippage readiness: {readiness.get('slippage_readiness_observed', '')} / ADEQUATE",
            f"- C46 progress tracker: {supporting.get('c46_status', '')}",
            f"- C46 completeness/regression warnings: {supporting.get('c46_completeness_warnings_count', 0)} / {supporting.get('c46_regression_warnings_count', 0)}",
            f"- C47 gate closure plan: {supporting.get('c47_status', '')}",
            f"- C48 latest dataset repair: {supporting.get('c48_status', '')}; repair attempted={str(supporting.get('c48_repair_attempted', False)).lower()}",
            f"- Mature labels: {label.get('mature_labels', 0)}",
            f"- Out-of-scope candidate rows/groups: {contract.get('out_of_scope_would_signal_rows', 0)} / {contract.get('out_of_scope_estimated_groups', 0)}",
            f"- Candidate families: {families or 'none'}",
            "",
            "Please fill:",
            f"- {template_path}",
            "",
            "Required decisions:",
            "1. Approve or reject label promotion and list allowed label statuses if approved.",
            "2. Confirm whether require_slippage_adequate stays true.",
            "3. Approve or reject contract expansion and list allowed families if approved.",
            "4. Confirm whether model scope is global-with-family-feature or per-family.",
            "5. Confirm C03/C05/C04/C06/C10/C23 must pass before official Python demo predictions.",
            "6. Confirm broker_action_authorized remains false.",
            "",
            "Reviewer approval alone must not authorize training, Python demo predictions, EA consumption, or broker action.",
        ]
    )


def _commands(root: Path, template_path: Path) -> dict[str, str]:
    python = "python"
    root_arg = _quote(str(root))
    template_arg = _quote(str(template_path))
    return {
        "validate_reviewer_template": f"{python} scripts/c42_process_reviewer_decision.py --root {root_arg} --decision-json {template_arg}",
        "apply_final_reviewer_template": f"{python} scripts/c43_run_demo_readiness_cycle.py --root {root_arg} --decision-json {template_arg} --apply-reviewer-configs",
        "refresh_after_apply": f"{python} scripts/c43_run_demo_readiness_cycle.py --root {root_arg} --refresh-live-readonly",
    }


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_READY:
        return "Send this bundle to the reviewer. After the template is edited, validate with C42 and apply with C43 only if final."
    return "Generate C41 and C44 first, then rerun C45."


def _quote(value: str) -> str:
    return f'"{value}"' if " " in value else value


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_reviewer_submission_bundle_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c45_reviewer_submission_bundle_report"] = payload["outputs"]["status_report_json"]
    pointer["c45_reviewer_submission_bundle_status"] = payload["status"]
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
