from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .market_data_export import _table, _utc_now, _write_json_atomic


DEFAULT_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_CONTRACT_EXPANSION_IMPACT_ESTIMATE_STATUS.json"
STATUS_NOT_SUFFICIENT = "APPROVAL_ALONE_NOT_SUFFICIENT"
STATUS_COULD_HELP = "APPROVAL_COULD_HELP_BUT_REQUIRES_REBUILD"
STATUS_NO_CANDIDATES = "NO_EXPANSION_CANDIDATES"


def generate_contract_expansion_impact_estimate(root: Path, report_json: Path | None = None) -> Path:
    root = root.resolve()
    reports = root / "outputs" / "reports"
    report_json = (report_json or root / DEFAULT_REPORT_JSON).resolve()
    c01 = _read_json(reports / "C02_C01_DATA_AUDIT.json")
    c03 = _read_json(reports / "C03_TRAINING_READINESS_REPORT.json")
    c11 = _read_json(reports / "A3_ML_READINESS_GAP_REPORT.json")
    c34 = _read_json(reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json")
    c36 = _read_json(reports / "A3_ML_CONTRACT_EXPANSION_CONFIG_PROPOSAL_STATUS.json")
    gate_projection = _gate_projection(c01, c03, c11, c34)
    status = _status(c34, gate_projection)
    payload = {
        "status": status,
        "stage": "C37-CONTRACT-EXPANSION-IMPACT-ESTIMATE",
        "created_at_utc": _utc_now(),
        "schema_version": "a3_ml_contract_expansion_impact_estimate_status_v1",
        "dataset_version": c03.get("dataset_version") or c34.get("dataset_version", ""),
        "inputs": {
            "c01_data_audit": str(reports / "C02_C01_DATA_AUDIT.json"),
            "c03_training_readiness": str(reports / "C03_TRAINING_READINESS_REPORT.json"),
            "c11_readiness_gap": str(reports / "A3_ML_READINESS_GAP_REPORT.json"),
            "c34_decision_backfill_audit": str(reports / "A3_ML_DECISION_BACKFILL_AUDIT_STATUS.json"),
            "c36_config_proposal": str(reports / "A3_ML_CONTRACT_EXPANSION_CONFIG_PROPOSAL_STATUS.json"),
        },
        "summary": {
            "c03_status": c03.get("status", "MISSING"),
            "c34_status": c34.get("status", "MISSING"),
            "c36_status": c36.get("status", "MISSING"),
            "candidate_files": c34.get("summary", {}).get("out_of_scope_files_with_would_signals", 0),
            "candidate_would_signal_rows": c34.get("summary", {}).get("out_of_scope_would_signal_rows", 0),
            "candidate_estimated_groups": c34.get("summary", {}).get("out_of_scope_estimated_groups", 0),
            "approval_alone_authorizes_demo_python": False,
        },
        "gate_projection": gate_projection,
        "approval_alone_result": _approval_alone_result(gate_projection),
        "required_follow_up_after_approval": _required_follow_up_after_approval(gate_projection),
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
            "config_write_attempted": False,
            "model_training_authorized": False,
            "python_demo_predictions_authorized": False,
            "broker_action_authorized": False,
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


def render_contract_expansion_impact_estimate_md(payload: dict[str, Any]) -> str:
    gate_rows = [
        {
            "Gate": gate.get("gate", ""),
            "Current": gate.get("current_observed", ""),
            "Projected": gate.get("projected_observed", ""),
            "Pass": str(gate.get("projected_passed", False)).lower(),
            "Why": gate.get("projection_reason", ""),
        }
        for gate in payload.get("gate_projection", [])
    ]
    follow_up = "\n".join(f"- {item}" for item in payload.get("required_follow_up_after_approval", []))
    return "\n".join(
        [
            "# A3 ML Contract Expansion Impact Estimate",
            "",
            f"Overall status: {payload['status']}",
            f"Dataset version: {payload.get('dataset_version', '')}",
            "",
            "## Summary",
            "",
            f"- C03 status: {payload.get('summary', {}).get('c03_status', '')}.",
            f"- Candidate files: {payload.get('summary', {}).get('candidate_files', 0)}.",
            f"- Candidate rows: {payload.get('summary', {}).get('candidate_would_signal_rows', 0)}.",
            f"- Candidate estimated groups: {payload.get('summary', {}).get('candidate_estimated_groups', 0)}.",
            "- Approval alone authorizes demo Python: false.",
            "",
            "## Gate Projection",
            "",
            _table(gate_rows, ["Gate", "Current", "Projected", "Pass", "Why"]) if gate_rows else "No gate projection.",
            "",
            "## Result",
            "",
            payload.get("approval_alone_result", ""),
            "",
            "## Required Follow-Up",
            "",
            follow_up or "- none",
            "",
            "## Boundary",
            "",
            "- MT5 connection attempted: false.",
            "- Data export attempted: false.",
            "- Config write attempted: false.",
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


def _gate_projection(
    c01: dict[str, Any],
    c03: dict[str, Any],
    c11: dict[str, Any],
    c34: dict[str, Any],
) -> list[dict[str, Any]]:
    checks = {check.get("gate"): check for check in c03.get("checks", [])}
    c34_summary = c34.get("summary", {})
    current_groups = _int_observed(checks.get("market_setup_groups", {}))
    extra_groups = int(c34_summary.get("out_of_scope_estimated_groups", 0) or 0)
    current_active = _float_observed(checks.get("active_weeks", {}))
    projected_active = _projected_active_weeks(c11, c34) or current_active
    current_feature_budget = _int_observed(checks.get("feature_budget", {}))
    candidate_trainable_groups = int(
        c01.get("labeled_and_trainable_setup_groups", {}).get("candidate_trainable_groups", 0) or 0
    )
    current_regimes = str(checks.get("at_least_two_regimes", {}).get("observed", ""))
    return [
        _projection(
            checks,
            "dataset_status",
            projected_observed=c01.get("status", checks.get("dataset_status", {}).get("observed", "")),
            projected_passed=c01.get("status") in {"EXPLORATORY_MODEL", "CANDIDATE_MODEL", "MATURE_MODEL"},
            reason="extra families do not change trainable-label status by themselves",
        ),
        _projection(
            checks,
            "market_setup_groups",
            projected_observed=str(current_groups + extra_groups),
            projected_passed=(current_groups + extra_groups) >= 300,
            reason=f"adds C34 estimated out-of-scope groups={extra_groups}",
        ),
        _projection(
            checks,
            "minority_labels",
            projected_observed=checks.get("minority_labels", {}).get("observed", ""),
            projected_passed=bool(checks.get("minority_labels", {}).get("passed", False)),
            reason="current minority-label gate already reflects approved contract only; C34 has no validated labels",
        ),
        _projection(
            checks,
            "active_weeks",
            projected_observed=f"{projected_active:.2f}",
            projected_passed=projected_active >= 8.0,
            reason="C34 candidate dates do not extend active decision span enough",
        ),
        _projection(
            checks,
            "both_directions",
            projected_observed=checks.get("both_directions", {}).get("observed", ""),
            projected_passed=bool(checks.get("both_directions", {}).get("passed", False)),
            reason="current gate already passes; C34 does not reduce coverage",
        ),
        _projection(
            checks,
            "at_least_two_regimes",
            projected_observed=current_regimes,
            projected_passed=bool(checks.get("at_least_two_regimes", {}).get("passed", False)),
            reason="C34 candidates have no proven second-regime C01 feature evidence yet",
        ),
        _projection(
            checks,
            "feature_budget",
            projected_observed=str(current_feature_budget),
            projected_passed=current_feature_budget >= 6,
            reason=f"candidate_trainable_groups={candidate_trainable_groups}; extra rows remain non-trainable until label promotion",
        ),
        _projection(
            checks,
            "slippage_readiness",
            projected_observed=checks.get("slippage_readiness", {}).get("observed", ""),
            projected_passed=bool(checks.get("slippage_readiness", {}).get("passed", False)),
            reason="extra signal rows do not create broker fill/request-price coverage for A2/A3",
        ),
        _projection(
            checks,
            "leakage",
            projected_observed=checks.get("leakage", {}).get("observed", ""),
            projected_passed=bool(checks.get("leakage", {}).get("passed", False)),
            reason="leakage must be rechecked after any approved rebuild",
        ),
    ]


def _projection(
    checks: dict[str, dict[str, Any]],
    gate: str,
    *,
    projected_observed: str,
    projected_passed: bool,
    reason: str,
) -> dict[str, Any]:
    check = checks.get(gate, {})
    return {
        "gate": gate,
        "current_passed": bool(check.get("passed", False)),
        "current_observed": str(check.get("observed", "")),
        "required": str(check.get("required", "")),
        "projected_observed": str(projected_observed),
        "projected_passed": bool(projected_passed),
        "projection_reason": reason,
    }


def _status(c34: dict[str, Any], gate_projection: list[dict[str, Any]]) -> str:
    if int(c34.get("summary", {}).get("out_of_scope_would_signal_rows", 0) or 0) <= 0:
        return STATUS_NO_CANDIDATES
    if all(gate.get("projected_passed") for gate in gate_projection):
        return STATUS_COULD_HELP
    return STATUS_NOT_SUFFICIENT


def _approval_alone_result(gate_projection: list[dict[str, Any]]) -> str:
    failed = [gate["gate"] for gate in gate_projection if not gate.get("projected_passed")]
    if not failed:
        return "Approval may clear the observed gates, but the full pipeline must still be rebuilt and reviewed fail-closed."
    return "Approval alone is not enough for demo Python predictions. Remaining projected blockers: " + ", ".join(failed) + "."


def _required_follow_up_after_approval(gate_projection: list[dict[str, Any]]) -> list[str]:
    failed = {gate["gate"] for gate in gate_projection if not gate.get("projected_passed")}
    actions = [
        "If reviewer approves expansion, run C36 with explicit allowed families and review reference, then rerun C08/C07/C03.",
    ]
    if "active_weeks" in failed:
        actions.append("Collect more active market weeks or approved older data that extends the actual decision-date span.")
    if "feature_budget" in failed or "dataset_status" in failed:
        actions.append("Promote labels/trainability only through reviewed C02/C01 rules; current rows remain diagnostic/non-trainable.")
    if "slippage_readiness" in failed:
        actions.append("Improve A2/A3 broker fill and request-price coverage before official demo Python authorization.")
    if "at_least_two_regimes" in failed:
        actions.append("Collect or approve data that proves at least two non-UNKNOWN regimes in C01.")
    actions.append("Keep broker_action_authorized=false through all rebuilds.")
    return actions


def _next_allowed_stage(status: str) -> str:
    if status == STATUS_NO_CANDIDATES:
        return "No expansion impact can be estimated. Continue live data collection and rerun C34."
    if status == STATUS_COULD_HELP:
        return "Reviewer approval is still required; after approval rerun C36/C08/C07 and keep broker action false."
    return "Do not expect reviewer approval alone to authorize demo Python. Continue collecting data and address remaining C03 blockers."


def _projected_active_weeks(c11: dict[str, Any], c34: dict[str, Any]) -> float:
    times = []
    coverage = c11.get("decision_coverage", {})
    for key in ("min_decision_utc", "max_decision_utc"):
        parsed = _parse_time(coverage.get(key, ""))
        if parsed is not None:
            times.append(parsed)
    for item in c34.get("out_of_scope_candidates", []):
        for key in ("min_signal_utc", "max_signal_utc"):
            parsed = _parse_time(item.get(key, ""))
            if parsed is not None:
                times.append(parsed)
    if len(times) < 2:
        return 0.0
    return max((max(times) - min(times)).total_seconds() / (7 * 24 * 3600), 0.0)


def _int_observed(check: dict[str, Any]) -> int:
    try:
        return int(float(str(check.get("observed", "0")).split(",", 1)[0]))
    except ValueError:
        return 0


def _float_observed(check: dict[str, Any]) -> float:
    try:
        return float(str(check.get("observed", "0")).split(",", 1)[0])
    except ValueError:
        return 0.0


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _write_status(status_json: Path, payload: dict[str, Any]) -> None:
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_json.with_suffix(".md").write_text(render_contract_expansion_impact_estimate_md(payload), encoding="utf-8")


def _update_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    if not pointer_path.exists():
        return
    pointer = _read_json(pointer_path)
    pointer["c37_contract_expansion_impact_estimate_report"] = payload["outputs"]["status_report_json"]
    pointer["c37_contract_expansion_impact_estimate_status"] = payload["status"]
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
