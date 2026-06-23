from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_REVIEWER_DECISION_PACKET_STATUS.json"
SCHEMA_VERSION = "a3_ml_reviewer_decision_packet_status_v1"
STATUS_REVIEW_REQUIRED = "REVIEWER_DECISION_REQUIRED"
STATUS_REVIEW_NOT_REQUIRED = "REVIEW_NOT_REQUIRED"
APPROVAL_WARNING = (
    "Reviewer approval alone must not authorize training, Python demo predictions, EA consumption, or broker action. "
    "C03/C05/C04/C06/C10/C23 must pass after any approved rebuild."
)


def generate_reviewer_decision_packet(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    inputs = _inputs(root, reports)
    status = _status(inputs)
    payload = {
        "status": status,
        "stage": "C41-REVIEWER-DECISION-PACKET",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": inputs["pointer"].get("dataset_version", ""),
        "readiness_summary": _readiness_summary(inputs),
        "decision_requests": _decision_requests(inputs),
        "label_promotion_evidence": _label_promotion_evidence(inputs),
        "contract_expansion_evidence": _contract_expansion_evidence(inputs),
        "historical_coverage": _historical_coverage(inputs),
        "approval_alone_not_sufficient_warning": APPROVAL_WARNING,
        "reviewer_prompt": _reviewer_prompt(inputs),
        "authorization": {
            "reviewer_packet_authorizes_training": False,
            "label_promotion_authorized": False,
            "contract_expansion_authorized": False,
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
            "profile_or_chart_file_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "inputs": _input_paths(root, reports),
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_reviewer_decision_packet_md(payload: dict[str, Any]) -> str:
    readiness = payload.get("readiness_summary", {})
    label = payload.get("label_promotion_evidence", {})
    contract = payload.get("contract_expansion_evidence", {})
    history = payload.get("historical_coverage", {})
    request_rows = [
        {
            "Decision": item.get("decision", ""),
            "Current": item.get("current_authorized", False),
            "Requested": item.get("requested", ""),
        }
        for item in payload.get("decision_requests", [])
    ]
    deficit_rows = [
        {
            "Account": row.get("account_label", ""),
            "Status": row.get("slippage_status", ""),
            "Entry Deficit": row.get("entry_fills_deficit", 0),
            "SL Deficit": row.get("sl_exits_deficit", 0),
            "TP Deficit": row.get("tp_exits_deficit", 0),
            "Request Deficit": row.get("request_price_resolved_deficit", 0),
        }
        for row in label.get("slippage_deficits", [])
    ]
    family_rows = [
        {
            "Family": row.get("family", ""),
            "Rows": row.get("would_signal_rows", 0),
            "Groups": row.get("estimated_groups", 0),
            "Files": row.get("files", 0),
        }
        for row in contract.get("candidate_families", [])
    ]
    return "\n".join(
        [
            "# A3 ML Reviewer Decision Packet",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Readiness",
            "",
            f"- C03 readiness: {readiness.get('c03_status', '')}.",
            f"- C05 training: {readiness.get('c05_status', '')}.",
            f"- C23 launch controller: {readiness.get('c23_status', '')}.",
            f"- C40 work order: {readiness.get('c40_status', '')}.",
            f"- Active weeks: {readiness.get('active_weeks_observed', '')} / >=8.",
            f"- Market setup groups: {readiness.get('market_setup_groups_observed', '')} / >=300.",
            f"- Feature budget: {readiness.get('feature_budget_observed', '')} / >=6.",
            f"- Slippage readiness: {readiness.get('slippage_readiness_observed', '')} / ADEQUATE.",
            f"- All accounts collecting: {str(readiness.get('all_accounts_collecting', False)).lower()}.",
            "",
            "## Decisions Needed",
            "",
            _table(request_rows, ["Decision", "Current", "Requested"]) if request_rows else "No decisions requested.",
            "",
            "## Label Promotion Evidence",
            "",
            f"- C38 status: {label.get('c38_status', '')}.",
            f"- Label promotion authorized now: {str(label.get('label_promotion_authorized_now', False)).lower()}.",
            f"- Allowed label statuses: {', '.join(label.get('allowed_label_statuses', []))}.",
            f"- Mature labels: {label.get('mature_labels', 0)}.",
            f"- Positive/negative labels: {label.get('positive_labels', 0)} / {label.get('negative_labels', 0)}.",
            f"- C01 candidate-trainable rows/groups: {label.get('candidate_trainable_rows', 0)} / {label.get('candidate_trainable_groups', 0)}.",
            f"- Require slippage adequate: {str(label.get('require_slippage_adequate', True)).lower()}.",
            "",
            _table(deficit_rows, ["Account", "Status", "Entry Deficit", "SL Deficit", "TP Deficit", "Request Deficit"])
            if deficit_rows
            else "No slippage deficit rows.",
            "",
            "## Contract Expansion Evidence",
            "",
            f"- C35 status: {contract.get('c35_status', '')}.",
            f"- C37 status: {contract.get('c37_status', '')}.",
            f"- Contract expansion authorized now: {str(contract.get('contract_expansion_authorized_now', False)).lower()}.",
            f"- Out-of-scope would-signal rows/groups: {contract.get('out_of_scope_would_signal_rows', 0)} / {contract.get('out_of_scope_estimated_groups', 0)}.",
            f"- Approval alone result: {contract.get('approval_alone_result', '')}",
            "",
            _table(family_rows, ["Family", "Rows", "Groups", "Files"]) if family_rows else "No candidate families.",
            "",
            "## Historical Coverage",
            "",
            f"- C39 status: {history.get('c39_status', '')}.",
            f"- Older compatible current-scope rows: {history.get('older_compatible_current_scope_would_signal_rows', 0)}.",
            f"- Older out-of-scope rows: {history.get('older_out_of_scope_rows', 0)}.",
            "",
            "## Warning",
            "",
            payload["approval_alone_not_sufficient_warning"],
            "",
            "## Reviewer Prompt",
            "",
            "```markdown",
            payload.get("reviewer_prompt", ""),
            "```",
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


def _inputs(root: Path, reports: Path) -> dict[str, dict[str, Any]]:
    config = root / "config" / "ml"
    return {
        "pointer": _read_json(reports / "C02_DATASET_POINTER.json"),
        "c03": _read_json(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c05": _read_json(reports / "A3_ML_TRAINING_STATUS.json"),
        "c23": _read_json(reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json"),
        "c33": _read_json(reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json"),
        "c34": _read_json(reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json"),
        "c35": _read_json(reports / "A3_ML_CONTRACT_EXPANSION_PACKET_STATUS.json"),
        "c37": _read_json(reports / "A3_ML_CONTRACT_EXPANSION_IMPACT_ESTIMATE_STATUS.json"),
        "c38": _read_json(reports / "A3_ML_LABEL_TRAINABILITY_BLOCKER_STATUS.json"),
        "c39": _read_json(reports / "A3_ML_HISTORICAL_DECISION_COVERAGE_STATUS.json"),
        "c40": _read_json(reports / "A3_ML_DEMO_READINESS_WORK_ORDER.json"),
        "label_config": _read_json(config / "a3_ml_label_promotion.json"),
        "contract_config": _read_json(config / "a3_ml_contract_expansion.json"),
    }


def _input_paths(root: Path, reports: Path) -> dict[str, str]:
    config = root / "config" / "ml"
    return {
        "dataset_pointer": str(reports / "C02_DATASET_POINTER.json"),
        "c03_training_readiness": str(reports / "C03_TRAINING_READINESS_REPORT.json"),
        "c05_training_status": str(reports / "A3_ML_TRAINING_STATUS.json"),
        "c23_demo_python_launch_controller": str(reports / "A3_ML_DEMO_PYTHON_LAUNCH_CONTROLLER_STATUS.json"),
        "c34_decision_backfill_audit": str(reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json"),
        "c35_contract_expansion_packet": str(reports / "A3_ML_CONTRACT_EXPANSION_PACKET_STATUS.json"),
        "c37_contract_expansion_impact_estimate": str(
            reports / "A3_ML_CONTRACT_EXPANSION_IMPACT_ESTIMATE_STATUS.json"
        ),
        "c38_label_trainability_blocker": str(reports / "A3_ML_LABEL_TRAINABILITY_BLOCKER_STATUS.json"),
        "c39_historical_decision_coverage": str(reports / "A3_ML_HISTORICAL_DECISION_COVERAGE_STATUS.json"),
        "c40_demo_readiness_work_order": str(reports / "A3_ML_DEMO_READINESS_WORK_ORDER.json"),
        "label_promotion_config": str(config / "a3_ml_label_promotion.json"),
        "contract_expansion_config": str(config / "a3_ml_contract_expansion.json"),
    }


def _status(inputs: dict[str, dict[str, Any]]) -> str:
    c03_ready = inputs["c03"].get("status") == "PASS"
    c40_ready = inputs["c40"].get("status") == "READY_FOR_DEMO_PYTHON_PREDICTIONS"
    if c03_ready and c40_ready:
        return STATUS_REVIEW_NOT_REQUIRED
    return STATUS_REVIEW_REQUIRED


def _readiness_summary(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    c33_health = inputs["c33"].get("collection_health", {})
    return {
        "c03_status": inputs["c03"].get("status", "MISSING"),
        "c05_status": inputs["c05"].get("status", "MISSING"),
        "c23_status": inputs["c23"].get("status", "MISSING"),
        "c40_status": inputs["c40"].get("status", "MISSING"),
        "market_setup_groups_observed": _check_observed(inputs["c03"], "market_setup_groups"),
        "active_weeks_observed": _check_observed(inputs["c03"], "active_weeks"),
        "regime_observed": _check_observed(inputs["c03"], "at_least_two_regimes"),
        "feature_budget_observed": _check_observed(inputs["c03"], "feature_budget"),
        "slippage_readiness_observed": _check_observed(inputs["c03"], "slippage_readiness"),
        "all_accounts_collecting": bool(c33_health.get("all_accounts_collecting", False)),
        "estimated_active_weeks_pass_date_utc": inputs["c40"]
        .get("summary", {})
        .get("estimated_active_weeks_pass_date_utc", ""),
    }


def _decision_requests(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    label_config = inputs["label_config"]
    contract_config = inputs["contract_config"]
    return [
        {
            "decision": "label_promotion",
            "current_authorized": bool(label_config.get("label_promotion_authorized", False)),
            "requested": "approve or reject diagnostic TP/SL label promotion for trainability, including allowed statuses",
            "must_not_authorize_python": True,
        },
        {
            "decision": "slippage_policy",
            "current_authorized": False,
            "requested": "confirm whether require_slippage_adequate stays true before trainable labels and demo predictions",
            "must_not_authorize_python": True,
        },
        {
            "decision": "contract_expansion",
            "current_authorized": bool(contract_config.get("contract_expansion_authorized", False)),
            "requested": "approve or reject versioned expansion beyond breakout_retest and list allowed families",
            "must_not_authorize_python": True,
        },
        {
            "decision": "demo_prediction_conditions",
            "current_authorized": False,
            "requested": "confirm official demo Python predictions require C03/C05/C04/C06/C10/C23 pass after rebuild",
            "must_not_authorize_python": True,
        },
    ]


def _label_promotion_evidence(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary = inputs["c38"].get("summary", {})
    label_config = inputs["label_config"]
    return {
        "c38_status": inputs["c38"].get("status", "MISSING"),
        "label_promotion_authorized_now": bool(label_config.get("label_promotion_authorized", False)),
        "review_reference": label_config.get("review_reference", ""),
        "allowed_label_statuses": list(label_config.get("allowed_label_statuses", [])),
        "minimum_mature_labels": label_config.get("minimum_mature_labels", 0),
        "minimum_minority_labels": label_config.get("minimum_minority_labels", 0),
        "require_slippage_adequate": bool(label_config.get("require_slippage_adequate", True)),
        "mature_labels": summary.get("c02_mature_labels", 0),
        "positive_labels": summary.get("c02_positive_labels", 0),
        "negative_labels": summary.get("c02_negative_labels", 0),
        "candidate_trainable_rows": summary.get("c01_candidate_trainable_rows", 0),
        "candidate_trainable_groups": summary.get("c01_candidate_trainable_groups", 0),
        "global_feature_budget": summary.get("c01_global_feature_budget", 0),
        "slippage_status": summary.get("slippage_status", "MISSING"),
        "slippage_deficits": inputs["c38"].get("slippage_deficits", []),
        "blockers": inputs["c38"].get("blockers", []),
    }


def _contract_expansion_evidence(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    c34_summary = inputs["c34"].get("summary", {})
    contract_config = inputs["contract_config"]
    c37_summary = inputs["c37"].get("summary", {})
    return {
        "c34_status": inputs["c34"].get("status", "MISSING"),
        "c35_status": inputs["c35"].get("status", "MISSING"),
        "c37_status": inputs["c37"].get("status", "MISSING"),
        "contract_expansion_authorized_now": bool(contract_config.get("contract_expansion_authorized", False)),
        "review_reference": contract_config.get("review_reference", ""),
        "allowed_families_now": list(contract_config.get("allowed_families", [])),
        "current_scope_would_signal_rows": c34_summary.get("current_scope_would_signal_rows", 0),
        "uncataloged_current_scope_files": c34_summary.get("uncataloged_current_scope_files", 0),
        "out_of_scope_would_signal_rows": c34_summary.get("out_of_scope_would_signal_rows", 0),
        "out_of_scope_estimated_groups": c34_summary.get("out_of_scope_estimated_groups", 0),
        "candidate_files": c37_summary.get("candidate_files", 0),
        "candidate_families": inputs["c34"].get("family_summary", []),
        "gate_projection": inputs["c37"].get("gate_projection", []),
        "approval_alone_result": inputs["c37"].get("approval_alone_result", ""),
    }


def _historical_coverage(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary = inputs["c39"].get("summary", {})
    return {
        "c39_status": inputs["c39"].get("status", "MISSING"),
        "older_compatible_current_scope_would_signal_rows": summary.get(
            "older_compatible_current_scope_would_signal_rows", 0
        ),
        "older_out_of_scope_rows": summary.get("older_out_of_scope_rows", 0),
        "scanned_decision_like_files": summary.get("scanned_decision_like_files", 0),
        "current_first_decision_utc": summary.get("current_first_decision_utc", ""),
        "earliest_row_utc": summary.get("earliest_row_utc", ""),
        "latest_row_utc": summary.get("latest_row_utc", ""),
    }


def _reviewer_prompt(inputs: dict[str, dict[str, Any]]) -> str:
    readiness = _readiness_summary(inputs)
    label = _label_promotion_evidence(inputs)
    contract = _contract_expansion_evidence(inputs)
    history = _historical_coverage(inputs)
    family_lines = "\n".join(
        f"- {row.get('family')}: {row.get('would_signal_rows', 0)} rows, "
        f"{row.get('estimated_groups', 0)} groups, {row.get('files', 0)} files"
        for row in contract.get("candidate_families", [])
    ) or "- none"
    deficit_lines = "\n".join(
        f"- {row.get('account_label')}: status={row.get('slippage_status')}, "
        f"entry_deficit={row.get('entry_fills_deficit', 0)}, "
        f"sl_deficit={row.get('sl_exits_deficit', 0)}, "
        f"tp_deficit={row.get('tp_exits_deficit', 0)}, "
        f"request_price_deficit={row.get('request_price_resolved_deficit', 0)}"
        for row in label.get("slippage_deficits", [])
    ) or "- none"
    blockers = "\n".join(f"- {item}" for item in label.get("blockers", [])) or "- none"
    return "\n".join(
        [
            "You are reviewing A3 Python ML readiness for an MT5 demo trading system.",
            "",
            "Review scope:",
            "- Decide label-promotion policy.",
            "- Decide contract-expansion policy.",
            "- Confirm slippage policy and demo-prediction start conditions.",
            "- Do not authorize broker action.",
            "",
            "Current readiness evidence:",
            f"- dataset: {inputs['pointer'].get('dataset_version', '')}",
            f"- C03 readiness: {readiness.get('c03_status')}",
            f"- C05 training: {readiness.get('c05_status')}",
            f"- C23 launch controller: {readiness.get('c23_status')}",
            f"- C40 work order: {readiness.get('c40_status')}",
            f"- active weeks: {readiness.get('active_weeks_observed')} / >=8",
            f"- market setup groups: {readiness.get('market_setup_groups_observed')} / >=300",
            f"- regimes: {readiness.get('regime_observed')} / >=2 non-UNKNOWN regimes",
            f"- feature budget: {readiness.get('feature_budget_observed')} / >=6",
            f"- slippage readiness: {readiness.get('slippage_readiness_observed')} / ADEQUATE",
            f"- all three demo accounts collecting: {readiness.get('all_accounts_collecting')}",
            "",
            "Label promotion evidence:",
            f"- C38 status: {label.get('c38_status')}",
            f"- label promotion currently authorized: {label.get('label_promotion_authorized_now')}",
            f"- allowed statuses in current proposal: {', '.join(label.get('allowed_label_statuses', []))}",
            f"- mature labels: {label.get('mature_labels')}",
            f"- positive/negative labels: {label.get('positive_labels')} / {label.get('negative_labels')}",
            f"- candidate-trainable rows/groups: {label.get('candidate_trainable_rows')} / {label.get('candidate_trainable_groups')}",
            f"- global feature budget: {label.get('global_feature_budget')}",
            f"- require_slippage_adequate: {label.get('require_slippage_adequate')}",
            "",
            "Label blockers:",
            blockers,
            "",
            "Per-account slippage deficits:",
            deficit_lines,
            "",
            "Contract expansion evidence:",
            f"- C34 status: {contract.get('c34_status')}",
            f"- C35 status: {contract.get('c35_status')}",
            f"- C37 status: {contract.get('c37_status')}",
            f"- contract expansion currently authorized: {contract.get('contract_expansion_authorized_now')}",
            f"- out-of-scope would-signal rows/groups: {contract.get('out_of_scope_would_signal_rows')} / {contract.get('out_of_scope_estimated_groups')}",
            f"- C37 approval-alone result: {contract.get('approval_alone_result')}",
            "",
            "Candidate families:",
            family_lines,
            "",
            "Historical coverage:",
            f"- C39 status: {history.get('c39_status')}",
            f"- older compatible current-scope rows: {history.get('older_compatible_current_scope_would_signal_rows')}",
            f"- older out-of-scope rows: {history.get('older_out_of_scope_rows')}",
            "",
            "Please answer with a detailed reviewer decision plan:",
            "1. Approve or reject label promotion. If approved, list exact label_status values and whether require_slippage_adequate remains true.",
            "2. Approve or reject contract expansion. If approved, list exact families and whether models are global-with-family-feature or per-family.",
            "3. List the exact C03/C05/C04/C06/C10/C23 gates that must pass before official Python demo predictions.",
            "4. State whether A2/A3 slippage deficits must close before training and before EA consumption.",
            "5. List config files/scripts/tests that must change if approval is granted.",
            "6. State explicitly that broker_action_authorized remains false.",
            "",
            APPROVAL_WARNING,
        ]
    )


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_REVIEW_NOT_REQUIRED:
        return "Continue through the normal fail-closed C05/C04/C06/C10/C23 demo prediction path."
    return "Send this packet to the reviewer, keep A1/A2/A3 collecting, and do not train or start EA consumption until approved rebuild gates pass."


def _check_observed(c03: dict[str, Any], gate: str) -> str:
    for check in c03.get("checks", []):
        if check.get("gate") == gate:
            return str(check.get("observed", ""))
    return ""


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_reviewer_decision_packet_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c41_reviewer_decision_packet_report"] = payload["outputs"]["status_report_json"]
    pointer["c41_reviewer_decision_packet_status"] = payload["status"]
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
