from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_CONTRACT_EXPANSION_PACKET_STATUS.json"
SCHEMA_VERSION = "a3_ml_contract_expansion_packet_status_v1"


def generate_contract_expansion_packet(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    pointer = _read_json(reports / "C02_DATASET_POINTER.json")
    c03 = _read_json(reports / "C03_TRAINING_READINESS_REPORT.json")
    c11 = _read_json(reports / "A3_ML_READINESS_GAP_REPORT.json")
    c34 = _read_json(reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json")
    c33 = _read_json(reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json")
    status = _status(c03, c34)
    summary = _summary(pointer, c03, c11, c34, c33)
    payload = {
        "status": status,
        "stage": "C35-CONTRACT-EXPANSION-PACKET",
        "created_at_utc": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "dataset_version": pointer.get("dataset_version", ""),
        "locked_contract": {
            "symbol": "XAUUSD",
            "family_scope": "breakout_retest_only",
            "source": str(root / "docs" / "A3_ML_DATA_CONTRACT_V1.md"),
            "expansion_authorized": False,
        },
        "summary": summary,
        "candidate_families": c34.get("family_summary", []),
        "review_questions": _review_questions(),
        "required_changes_if_approved": _required_changes_if_approved(),
        "reviewer_prompt": _reviewer_prompt(summary, c34),
        "authorization": {
            "contract_expansion_authorized": False,
            "training_authorized": False,
            "python_demo_predictions_authorized": False,
            "ea_consumption_authorized": False,
            "broker_action_authorized": False,
        },
        "boundary": {
            "mt5_connection_attempted": False,
            "data_export_attempted": False,
            "terminal_runtime_change_authorized": False,
            "profile_or_chart_file_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "broker_action_authorized": False,
        },
        "inputs": {
            "c03_training_readiness": str(reports / "C03_TRAINING_READINESS_REPORT.json"),
            "c11_readiness_gap": str(reports / "A3_ML_READINESS_GAP_REPORT.json"),
            "c33_demo_shadow_collection_health": str(reports / "A3_ML_DEMO_SHADOW_COLLECTION_HEALTH_STATUS.json"),
            "c34_decision_backfill_audit": str(reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json"),
            "data_contract": str(root / "docs" / "A3_ML_DATA_CONTRACT_V1.md"),
            "shadow_governance": str(root / "docs" / "A3_ML_SHADOW_GOVERNANCE_V1.md"),
        },
        "outputs": {
            "status_report_json": str(report_json),
            "status_report_md": str(report_json.with_suffix(".md")),
        },
        "next_allowed_stage": _next_allowed_stage(status),
    }
    _write_status(report_json, payload)
    _update_pointer(reports / "C02_DATASET_POINTER.json", payload)
    return report_json


def render_contract_expansion_packet_md(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    family_rows = [
        {
            "Family": item.get("family", ""),
            "Rows": str(item.get("would_signal_rows", 0)),
            "Groups": str(item.get("estimated_groups", 0)),
            "Files": str(item.get("files", 0)),
            "Min": item.get("min_signal_utc", ""),
            "Max": item.get("max_signal_utc", ""),
        }
        for item in payload.get("candidate_families", [])
    ]
    questions = "\n".join(f"{index}. {item}" for index, item in enumerate(payload.get("review_questions", []), start=1))
    changes = "\n".join(f"- {item}" for item in payload.get("required_changes_if_approved", []))
    return "\n".join(
        [
            "# A3 ML Contract Expansion Packet",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Current Lock",
            "",
            "- Symbol: XAUUSD.",
            "- Family scope: breakout_retest only.",
            "- Contract expansion authorized: false.",
            "- Python demo predictions authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Evidence Summary",
            "",
            f"- C03 readiness: {summary.get('c03_status', '')}.",
            f"- Active weeks: {summary.get('active_weeks_observed', '')} / >=8.",
            f"- Market setup groups: {summary.get('market_setup_groups_observed', '')} / >=300.",
            f"- Current-scope uncataloged files: {summary.get('uncataloged_current_scope_files', 0)}.",
            f"- Out-of-scope would-signal rows: {summary.get('out_of_scope_would_signal_rows', 0)}.",
            f"- Out-of-scope estimated groups: {summary.get('out_of_scope_estimated_groups', 0)}.",
            f"- All demo accounts collecting: {str(summary.get('all_accounts_collecting', False)).lower()}.",
            "",
            "## Candidate Families",
            "",
            _table(family_rows, ["Family", "Rows", "Groups", "Files", "Min", "Max"]) if family_rows else "No candidate families.",
            "",
            "## Reviewer Questions",
            "",
            questions or "No reviewer questions.",
            "",
            "## Required Changes If Approved",
            "",
            changes or "- none",
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
            "- Terminal runtime change authorized: false.",
            "- Model training authorized: false.",
            "- Python demo predictions authorized: false.",
            "- Broker action authorized: false.",
            "",
            "## Next",
            "",
            payload["next_allowed_stage"],
            "",
        ]
    )


def _summary(
    pointer: dict[str, Any],
    c03: dict[str, Any],
    c11: dict[str, Any],
    c34: dict[str, Any],
    c33: dict[str, Any],
) -> dict[str, Any]:
    c34_summary = c34.get("summary", {})
    collection = c33.get("collection_health", {})
    return {
        "dataset_version": pointer.get("dataset_version", ""),
        "c03_status": c03.get("status", "MISSING"),
        "market_setup_groups_observed": _check_observed(c03, "market_setup_groups"),
        "active_weeks_observed": _check_observed(c03, "active_weeks"),
        "feature_budget_observed": _check_observed(c03, "feature_budget"),
        "slippage_readiness_observed": _check_observed(c03, "slippage_readiness"),
        "readiness_gap_status": c11.get("status", "MISSING"),
        "remaining_active_weeks": _remaining_active_weeks(c11),
        "c34_status": c34.get("status", "MISSING"),
        "current_scope_would_signal_rows": c34_summary.get("current_scope_would_signal_rows", 0),
        "uncataloged_current_scope_files": c34_summary.get("uncataloged_current_scope_files", 0),
        "out_of_scope_would_signal_rows": c34_summary.get("out_of_scope_would_signal_rows", 0),
        "out_of_scope_estimated_groups": c34_summary.get("out_of_scope_estimated_groups", 0),
        "all_accounts_collecting": bool(collection.get("all_accounts_collecting", False)),
        "observer_prediction_rows": collection.get("total_observer_prediction_rows", 0),
        "broker_shadow_tap_rows": collection.get("total_broker_shadow_tap_rows", 0),
    }


def _status(c03: dict[str, Any], c34: dict[str, Any]) -> str:
    if c03.get("status") == "PASS":
        return "NO_EXPANSION_REQUIRED_C03_PASS"
    c34_summary = c34.get("summary", {})
    if int(c34_summary.get("uncataloged_current_scope_files", 0) or 0) > 0:
        return "CURRENT_SCOPE_IMPORT_REVIEW_REQUIRED"
    if int(c34_summary.get("out_of_scope_would_signal_rows", 0) or 0) > 0:
        return "CONTRACT_EXPANSION_REVIEW_REQUIRED"
    return "WAITING_FOR_MORE_CURRENT_SCOPE_DATA"


def _review_questions() -> list[str]:
    return [
        "Should A3 ML Data Contract V1 be versioned to allow multi-family XAUUSD rows beyond breakout_retest?",
        "If yes, which families are approved: round_number_retest, session_extreme_retest, rdguard, rdstruct, or a smaller subset?",
        "Should family be a model feature in one global model, or should each approved family receive its own model/gates?",
        "Should market_setup_group_id include family to avoid cross-family dedupe?",
        "Can the existing 288-bar diagnostic label horizon be reused for every approved family, or does any family need a new label contract?",
        "What minimum per-family rows/groups/minority labels must pass before any Python demo prediction authorization?",
        "Should C03 slippage readiness stay per account, or become per account plus per family?",
    ]


def _required_changes_if_approved() -> list[str]:
    return [
        "Create a versioned A3 ML data contract addendum that explicitly changes family scope.",
        "Add allowed_families configuration and tests; keep default locked to breakout_retest until approval is present.",
        "Update C02 normalization to preserve family and include only approved families.",
        "Update signal grouping so setup groups cannot merge different families unless the reviewer explicitly approves it.",
        "Update C03 readiness gates for global and per-family row/group/minority/regime/slippage checks.",
        "Update C05/C04/C06/C23 so model artifacts, shadow predictions, and EA handoff include model scope/family hashes.",
        "Regenerate C08, C03, C05, C04, C06, C23, C33 and keep broker_action_authorized=false.",
    ]


def _reviewer_prompt(summary: dict[str, Any], c34: dict[str, Any]) -> str:
    families = c34.get("family_summary", [])
    family_lines = "\n".join(
        f"- {item.get('family')}: {item.get('would_signal_rows')} rows, {item.get('estimated_groups')} estimated groups, "
        f"{item.get('min_signal_utc')} to {item.get('max_signal_utc')}"
        for item in families
    ) or "- none"
    return "\n".join(
        [
            "You are reviewing an A3 Python ML contract-expansion proposal for an MT5 demo trading system.",
            "",
            "Current locked contract:",
            "- XAUUSD only",
            "- accounts 1025742, 1033030, 1033669",
            "- breakout_retest only",
            "- broker_action_authorized must remain false",
            "",
            "Current readiness:",
            f"- C03 status: {summary.get('c03_status')}",
            f"- active weeks: {summary.get('active_weeks_observed')} / >=8",
            f"- market setup groups: {summary.get('market_setup_groups_observed')} / >=300",
            f"- feature budget: {summary.get('feature_budget_observed')} / >=6",
            f"- slippage readiness: {summary.get('slippage_readiness_observed')} / ADEQUATE",
            f"- all three demo accounts collecting: {summary.get('all_accounts_collecting')}",
            "",
            "Backfill audit:",
            f"- uncataloged current-scope files: {summary.get('uncataloged_current_scope_files')}",
            f"- current-scope would-signal rows: {summary.get('current_scope_would_signal_rows')}",
            f"- out-of-scope would-signal rows: {summary.get('out_of_scope_would_signal_rows')}",
            f"- out-of-scope estimated groups: {summary.get('out_of_scope_estimated_groups')}",
            "",
            "Out-of-scope families found:",
            family_lines,
            "",
            "Please decide whether to approve a versioned contract expansion. If approved, specify:",
            "1. allowed families",
            "2. whether to use one global model with family as a feature or separate per-family models",
            "3. family-aware C03 gate thresholds",
            "4. whether 288-bar diagnostic labels are valid for each family",
            "5. slippage readiness requirements",
            "6. exact conditions before Python demo predictions may be authorized",
            "",
            "If not approved, say so clearly and require continued live collection under the current breakout_retest-only contract.",
        ]
    )


def _next_allowed_stage(status: str) -> str:
    if status == "CONTRACT_EXPANSION_REVIEW_REQUIRED":
        return "Send this packet to the reviewer. Do not import out-of-scope rows or authorize Python demo predictions without an approved versioned contract expansion."
    if status == "CURRENT_SCOPE_IMPORT_REVIEW_REQUIRED":
        return "Review uncataloged current-scope files before changing C02 catalogs, then rerun C08/C03."
    if status == "NO_EXPANSION_REQUIRED_C03_PASS":
        return "C03 already passes; continue through C05/C04/C06/C23 using the locked contract."
    return "Continue live current-scope data collection and rerun C08/C23 after market data advances."


def _check_observed(c03: dict[str, Any], gate: str) -> str:
    for check in c03.get("checks", []):
        if check.get("gate") == gate:
            return str(check.get("observed", ""))
    return ""


def _remaining_active_weeks(c11: dict[str, Any]) -> str:
    value = c11.get("backfill_assessment", {}).get("remaining_active_weeks", "")
    if value != "":
        return str(value)
    for gap in c11.get("gate_gaps", []):
        if gap.get("gate") == "active_weeks":
            return str(gap.get("gap_text") or gap.get("gap_value") or "")
    return ""


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_contract_expansion_packet_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c35_contract_expansion_packet_report"] = payload["outputs"]["status_report_json"]
    pointer["c35_contract_expansion_packet_status"] = payload["status"]
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
