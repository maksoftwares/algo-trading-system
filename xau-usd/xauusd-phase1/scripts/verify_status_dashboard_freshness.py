from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Any


GOVERNANCE_SCHEMA = "a1_xau_governance_status_v1"
GOVERNANCE_NORTH_STAR = (
    "Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month "
    "periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can "
    "eventually support controlled withdrawals from accumulated profits."
)
GOVERNANCE_DOCUMENTS = {
    "master_direction": "xau-usd/xauusd-phase1/docs/A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md",
    "current_research_freeze": "xau-usd/xauusd-phase1/docs/A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md",
    "router_entry_hold_path_audit_prereg": (
        "xau-usd/xauusd-phase1/docs/A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md"
    ),
    "independent_specialist_primary_direction": (
        "xau-usd/xauusd-phase1/docs/A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md"
    ),
}
GOVERNANCE_REQUIRED_STATEMENTS = [
    "R6 = primary independent specialist lane",
    "NP1-A = next action",
    "R1+R2 = research control only",
    "R3 = excluded",
    "R4 = no survivor",
    "router entry/hold audit = deferred control diagnostic",
    "parallel specialist lane = false",
    "all history through 2026-06-30 = DEVELOPMENT_DATA",
    "no demo/live/broker authorization",
]
CURRENT_CONTROL_LEDGER_SHA256 = "47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52"
GOVERNANCE_RULE_ADMISSIBILITY_SOURCES = [
    {
        "source_id": "h4_d1_long_best_box2_atr80",
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule_type": "PREVIOUS_MONTH_PNL_HEALTH_GATE",
        "retained_rule": "Previous-month P/L health gate (enabled; minimum net -$50)",
    },
    {
        "source_id": "r1_h1_pullback_long_v1",
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule_type": "R1_DIRECTIONAL_SESSION_GATE",
        "retained_rule": "R1 directional session 09 <= hour < 15",
    },
    {
        "source_id": "r2_pullback_rejection_short_v1",
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule_type": "R2_DIRECTIONAL_SESSION_GATE",
        "retained_rule": "R2 directional session 05 <= hour < 19",
    },
    {
        "source_id": "r2_continuation_short_v1",
        "admissibility_issue_type": "SOURCE_LOCAL_CONTAINMENT_NOT_ADMISSION_EVIDENCE",
        "retained_rule_type": "R2_DAILY_LOSS_STOP",
        "retained_rule": "R2 $10 daily-loss stop",
    },
]


def verify_status_dashboard_freshness(repo_root: Path, status_path: Path | None = None) -> list[str]:
    repo_root = repo_root.resolve()
    status_path = (status_path or repo_root / "status.html").resolve()
    project_status_json_path = repo_root / "status_summary.json"
    project_status = _read_json(project_status_json_path) if project_status_json_path.exists() else {}
    present_governance_documents = [
        relative_path
        for relative_path in GOVERNANCE_DOCUMENTS.values()
        if (repo_root / relative_path).is_file()
    ]
    if present_governance_documents and project_status.get("schema_version") != GOVERNANCE_SCHEMA:
        actual_schema = project_status.get("schema_version", "MISSING")
        return [
            "A1 governance documents are present but the canonical status is missing or has been "
            f"downgraded from {GOVERNANCE_SCHEMA} (actual schema: {actual_schema})"
        ]
    if project_status.get("schema_version") == GOVERNANCE_SCHEMA:
        return _verify_governance_status_dashboard(repo_root, status_path, project_status)

    phase0_reports = repo_root / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase1_reports = repo_root / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase3_reports = repo_root / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"

    canonical_paths = {
        "phase1_summary": phase1_reports / "PHASE1_STATUS_SUMMARY.json",
        "measured_cost": phase0_reports / "MEASURED_COST_MODEL.md",
        "phase2_demo_countdown": phase1_reports / "PHASE2_DEMO_COUNTDOWN.json",
        "phase2_demo_preflight": phase1_reports / "PHASE2_DEMO_PREFLIGHT.json",
        "phase2_experimental_demo_terminal": phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json",
        "phase2_experimental_demo_attachments": phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json",
        "phase2_demo_next_actions": phase1_reports / "PHASE2_DEMO_NEXT_ACTIONS.json",
        "phase2_owner_packet": phase1_reports / "PHASE2_OWNER_ACTION_PACKET.json",
        "phase2_vps_selection_check": phase1_reports / "PHASE2_VPS_SELECTION_DECISION_CHECK.json",
        "phase2_vps_bootstrap": phase1_reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json",
        "phase2_readiness": phase1_reports / "PHASE2_READINESS_REPORT.md",
        "phase3_status": phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json",
        "phase3_handoff": phase3_reports / "PHASE3_TO_DEMO_HANDOFF.json",
    }
    project_status_summary_path = repo_root / "status_summary.md"
    runtime_chart_inventory_path = phase1_reports / "RUNTIME_CHART_INVENTORY_FORENSIC_2026_06_21.csv"
    a1_momentum_report_path = phase1_reports / "A1_XAU_M5_MOMENTUM_RR2_LONG_ONLY_FORWARD_ATTACHMENT_2026_07_02.json"
    errors = [f"missing status dashboard: {status_path}"] if not status_path.exists() else []
    for label, path in canonical_paths.items():
        if not path.exists():
            errors.append(f"missing canonical report {label}: {path}")
    if errors:
        return errors

    actual = status_path.read_text(encoding="utf-8", errors="replace")

    phase1_summary = _read_json(canonical_paths["phase1_summary"])
    phase3_status = _read_json(canonical_paths["phase3_status"])
    phase2_countdown = _read_json(canonical_paths["phase2_demo_countdown"])
    phase2_preflight = _read_json(canonical_paths["phase2_demo_preflight"])
    phase2_experimental_demo_terminal = _read_json(canonical_paths["phase2_experimental_demo_terminal"])
    phase2_experimental_demo_attachments = _read_json(canonical_paths["phase2_experimental_demo_attachments"])
    phase2_next_actions = _read_json(canonical_paths["phase2_demo_next_actions"])
    phase2_owner_packet = _read_json(canonical_paths["phase2_owner_packet"])
    phase2_vps_selection_check = _read_json(canonical_paths["phase2_vps_selection_check"])
    phase2_bootstrap = _read_json(canonical_paths["phase2_vps_bootstrap"])
    phase3_handoff = _read_json(canonical_paths["phase3_handoff"])
    measured_cost = _parse_measured_cost(canonical_paths["measured_cost"])
    phase2_status = _markdown_status(canonical_paths["phase2_readiness"])
    project_status_summary_md = (
        project_status_summary_path.read_text(encoding="utf-8", errors="replace")
        if project_status_summary_path.exists()
        else ""
    )
    runtime_inventory = _read_runtime_inventory(runtime_chart_inventory_path) if runtime_chart_inventory_path.exists() else []
    a1_momentum_report = _read_json(a1_momentum_report_path) if a1_momentum_report_path.exists() else {}

    runtime = _mapping(phase1_summary.get("runtime"))
    latest = _mapping(runtime.get("latest_row"))
    soak = _mapping(phase1_summary.get("soak"))
    phase3_cost_modes = _mapping(phase3_status.get("cost_mode_comparison"))
    phase3_paper_shadow = _mapping(phase3_status.get("paper_shadow_experiment"))
    phase3_lifecycle = _mapping(phase3_status.get("shadow_lifecycle_experiment"))
    phase3_guard = _mapping(phase3_status.get("lifecycle_guard_experiment"))
    phase3_rehearsal = _mapping(phase3_status.get("demo_rehearsal"))
    bootstrap_source_status = _mapping(phase2_bootstrap.get("source_status"))
    owner_vps_recommendation = _mapping(phase2_owner_packet.get("vps_selection_recommendation"))
    owner_vps_workspace = _mapping(phase2_owner_packet.get("vps_evidence_workspace"))
    owner_vps_workspace_items = _mapping_rows(owner_vps_workspace.get("items"))
    median_net_by_mode = _mapping(phase3_cost_modes.get("median_net_after_proxy_by_mode"))
    suspend_count_by_mode = _mapping(phase3_cost_modes.get("suspend_family_count_by_mode"))
    core_expectations = {
        "decision row count": runtime.get("decision_rows"),
        "latest bar": latest.get("bar_time"),
        "soak observed days": soak.get("observed_days"),
        "soak progress pct": f"{_to_float(soak.get('progress_pct')):.2f}%" if _to_float(soak.get("progress_pct")) is not None else None,
        "measured cost status": measured_cost.get("status"),
        "measured cost observed rows": measured_cost.get("observed_rows"),
        "measured cost observed days": measured_cost.get("observed_days"),
        "demo countdown status": phase2_countdown.get("status"),
        "demo countdown pending gate count": phase2_countdown.get("pending_gate_count"),
        "demo preflight status": phase2_preflight.get("status"),
        "demo preflight implementation authorization": str(
            phase2_preflight.get("paper_mode_implementation_authorized", "")
        ).lower(),
        "experimental demo terminal status": phase2_experimental_demo_terminal.get("status"),
        "experimental demo terminal clean setup ready": str(
            phase2_experimental_demo_terminal.get("clean_demo_setup_ready", "")
        ).lower(),
        "experimental demo terminal observers attached": str(
            phase2_experimental_demo_terminal.get("experimental_observers_attached", "")
        ).lower(),
        "experimental demo terminal observer active count": phase2_experimental_demo_terminal.get(
            "experimental_observer_active_count"
        ),
        "experimental demo terminal server": _mapping(
            phase2_experimental_demo_terminal.get("terminal")
        ).get("latest_authorization_server"),
        "experimental demo attachment status": phase2_experimental_demo_attachments.get("status"),
        "experimental demo attachment count": phase2_experimental_demo_attachments.get("attachment_count"),
        "experimental demo attachment run id": phase2_experimental_demo_attachments.get("run_id"),
        "experimental demo attachment terminal relaunched": str(
            _mapping(phase2_experimental_demo_attachments.get("terminal")).get("terminal_relaunched", "")
        ).lower(),
        "experimental demo attachment broker action allowed": str(
            _mapping(phase2_experimental_demo_attachments.get("ea")).get("broker_action_allowed", "")
        ).lower(),
        "demo next-actions status": phase2_next_actions.get("status"),
        "demo next-actions pending gate count": phase2_next_actions.get("pending_gate_count"),
        "demo next-actions demo authorization": str(phase2_next_actions.get("demo_trading_authorized", "")).lower(),
        "owner packet status": phase2_owner_packet.get("status"),
        "vps selection decision check status": phase2_vps_selection_check.get("status"),
        "vps selection decision next action": phase2_vps_selection_check.get("next_action"),
        "vps evidence workspace status": owner_vps_workspace.get("status"),
        "vps evidence workspace manifest": owner_vps_workspace.get("manifest_path"),
        "owner packet vps recommendation status": owner_vps_recommendation.get("status"),
        "owner packet primary vps trial": owner_vps_recommendation.get("primary_trial"),
        "owner packet backup vps trial": owner_vps_recommendation.get("backup_trial"),
        "owner packet deferred vps option": owner_vps_recommendation.get("defer"),
        "vps bootstrap status": phase2_bootstrap.get("status"),
        "vps bootstrap demo authorization": str(phase2_bootstrap.get("demo_trading_authorized", "")).lower(),
        "vps bootstrap selection status": bootstrap_source_status.get("vps_selection"),
        "vps bootstrap latency status": bootstrap_source_status.get("vps_latency"),
        "vps bootstrap first-day status": bootstrap_source_status.get("vps_first_day_verification"),
        "vps bootstrap owner approval status": bootstrap_source_status.get("project_owner_approval"),
        "demo countdown paper authorization": str(phase2_countdown.get("paper_mode_authorized", "")).lower(),
        "demo countdown broker execution authorization": str(
            phase2_countdown.get("broker_execution_authorized", "")
        ).lower(),
        "demo countdown live trading authorization": str(
            phase2_countdown.get("live_trading_authorized", "")
        ).lower(),
        "phase2 readiness status": phase2_status,
        "phase3 experimental status": phase3_status.get("status"),
        "entry_exit_proxy median net": median_net_by_mode.get("entry_exit_proxy"),
        "p95_fresh_proxy median net": median_net_by_mode.get("p95_fresh_proxy"),
        "stress_2x_p95_proxy median net": median_net_by_mode.get("stress_2x_p95_proxy"),
        "entry_exit_proxy suspend count": suspend_count_by_mode.get("entry_exit_proxy"),
        "p95_fresh_proxy suspend count": suspend_count_by_mode.get("p95_fresh_proxy"),
        "stress_2x_p95_proxy suspend count": suspend_count_by_mode.get("stress_2x_p95_proxy"),
        "paper-shadow status": phase3_paper_shadow.get("status"),
        "paper-shadow would-open count": phase3_paper_shadow.get("would_open_count"),
        "paper-shadow blocked suspend count": phase3_paper_shadow.get("blocked_suspend_count"),
        "shadow lifecycle status": phase3_lifecycle.get("status"),
        "shadow lifecycle synthetic open count": phase3_lifecycle.get("synthetic_open_count"),
        "shadow lifecycle total net R": phase3_lifecycle.get("synthetic_total_net_r"),
        "lifecycle guard status": phase3_guard.get("status"),
        "lifecycle guard open count": phase3_guard.get("guarded_open_count"),
        "lifecycle guard total net R": phase3_guard.get("guarded_total_net_r"),
        "demo rehearsal status": phase3_rehearsal.get("status"),
        "demo rehearsal event count": phase3_rehearsal.get("rehearsal_event_count"),
        "demo rehearsal shadow opens": phase3_rehearsal.get("shadow_open_events"),
        "demo rehearsal blocked events": phase3_rehearsal.get("blocked_events"),
        "demo rehearsal can start real demo": phase3_rehearsal.get("can_start_real_demo"),
        "demo handoff status": phase3_handoff.get("status"),
        "demo handoff can start demo now": phase3_handoff.get("can_start_demo_now"),
        "demo handoff paper-shadow branch": phase3_handoff.get("can_start_real_paper_shadow_branch"),
        "demo handoff demo authorization": phase3_handoff.get("demo_authorized"),
        "demo handoff paper mode authorization": phase3_handoff.get("paper_mode_authorized"),
        "demo handoff broker-action code allowed": phase3_handoff.get("broker_action_code_allowed"),
        "demo handoff mt5 runtime touched": phase3_handoff.get("mt5_runtime_touched"),
    }
    for wait_gate in phase2_countdown.get("wait_gates", []):
        if not isinstance(wait_gate, dict):
            continue
        gate = str(wait_gate.get("gate", ""))
        if gate:
            core_expectations[f"demo wait gate {gate}"] = gate
        if wait_gate.get("remaining") not in {None, ""}:
            core_expectations[f"demo wait gate {gate} remaining"] = wait_gate.get("remaining")
    for target in phase2_next_actions.get("earliest_gate_targets", []):
        if not isinstance(target, dict):
            continue
        gate = str(target.get("gate", ""))
        if gate:
            core_expectations[f"demo earliest target gate {gate}"] = gate
        if target.get("earliest_target_utc"):
            core_expectations[f"demo earliest target utc {gate}"] = target.get("earliest_target_utc")
        if target.get("condition"):
            core_expectations[f"demo earliest target condition {gate}"] = target.get("condition")
    for closure in phase2_next_actions.get("gate_closure_map", []):
        if not isinstance(closure, dict):
            continue
        gate = str(closure.get("gate", ""))
        if gate:
            core_expectations[f"demo gate closure map gate {gate}"] = gate
        for key in (
            "category",
            "owner",
            "why_required",
            "proof_artifact",
            "closure_action",
            "pass_condition",
            "verification_command",
        ):
            if closure.get(key):
                value = closure.get(key)
                if key == "proof_artifact":
                    value = _compact_path(str(value))
                core_expectations[f"demo gate closure map {gate} {key}"] = value
    for check in phase2_vps_selection_check.get("checks", []):
        if not isinstance(check, dict):
            continue
        name = check.get("check")
        if name:
            core_expectations[f"vps selection decision check {name}"] = name
        if check.get("status"):
            core_expectations[f"vps selection decision check {name} status"] = check.get("status")
    for index, item in enumerate(owner_vps_workspace_items, start=1):
        target = item.get("target")
        action = item.get("action")
        if target:
            core_expectations[f"vps evidence workspace item {index} target"] = target
        if action:
            core_expectations[f"vps evidence workspace item {index} action"] = action
    for phase in phase2_bootstrap.get("bootstrap_phases", []):
        if not isinstance(phase, dict):
            continue
        name = phase.get("phase")
        if name:
            core_expectations[f"vps bootstrap phase {name}"] = name
    for action in phase2_next_actions.get("do_now", []):
        if not isinstance(action, dict):
            continue
        step = action.get("step")
        text = action.get("action")
        if step:
            core_expectations[f"demo next-action step {step}"] = step
        if text:
            core_expectations[f"demo next-action text {step}"] = text
    for expert in phase2_experimental_demo_terminal.get("active_experts", []):
        if not isinstance(expert, dict):
            continue
        name = expert.get("expert")
        if name:
            core_expectations[f"experimental demo terminal active expert {name}"] = name
    for attachment in phase2_experimental_demo_attachments.get("attachments", []):
        if not isinstance(attachment, dict):
            continue
        candidate = attachment.get("candidate")
        symbol = attachment.get("symbol")
        if candidate and symbol:
            core_expectations[f"experimental demo attachment {candidate} {symbol}"] = candidate
            core_expectations[f"experimental demo attachment symbol {candidate} {symbol}"] = symbol
    for label, value in core_expectations.items():
        if value is None or value == "":
            continue
        text = html.escape(str(value), quote=True)
        if text not in actual:
            errors.append(f"status.html is missing {label}: {value}")
    observed_days = _to_float(soak.get("observed_days"))
    required_days = _to_float(soak.get("required_days"))
    if observed_days is not None and required_days is not None:
        soak_fragment = f"{observed_days:g} of {required_days:g} trading days"
        if soak_fragment not in actual:
            errors.append(f"status.html is missing soak observed days: {soak.get('observed_days')}")
    vps_check_status = phase2_vps_selection_check.get("status")
    if vps_check_status:
        status_text = html.escape(str(vps_check_status), quote=True)
        fragment = f'VPS decision check</td><td><span class="pill {_status_class(str(vps_check_status))}">{status_text}</span>'
        if fragment not in actual:
            errors.append(f"status.html is missing vps selection decision check status: {vps_check_status}")
    if project_status_summary_md or runtime_inventory:
        _verify_protected_breakout_core_summary(errors, project_status_summary_md, runtime_inventory)
    if a1_momentum_report:
        _verify_a1_momentum_summary(errors, actual, project_status_summary_md, a1_momentum_report)
    return errors


def _verify_governance_status_dashboard(
    repo_root: Path,
    status_path: Path,
    summary: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    markdown_path = repo_root / "status_summary.md"
    if not status_path.exists():
        errors.append(f"missing status dashboard: {status_path}")
    if not markdown_path.exists():
        errors.append(f"missing governance status markdown: {markdown_path}")
    if errors:
        return errors

    current = _mapping(summary.get("current"))
    repo = _mapping(summary.get("repo"))
    control = _mapping(current.get("portfolio_control"))
    metrics = _mapping(control.get("metrics"))
    specialists = _mapping(current.get("specialists"))
    r1 = _mapping(specialists.get("R1"))
    r2 = _mapping(specialists.get("R2"))
    r3 = _mapping(specialists.get("R3"))
    r4 = _mapping(specialists.get("R4"))
    rule_admissibility = _mapping(current.get("rule_admissibility"))
    attribution_repair = _mapping(current.get("attribution_repair"))
    history = _mapping(current.get("historical_evidence"))
    authorization = _mapping(current.get("authorization"))
    authority_map = _mapping(current.get("authority_map"))
    program = _mapping(current.get("independent_specialist_program"))
    next_task = _mapping(current.get("primary_next_task"))
    next_task_alias = _mapping(current.get("next_task"))
    control_diagnostic = _mapping(current.get("control_diagnostic_task"))

    if "commit" in repo:
        errors.append("governance repo provenance must use base_commit, not ambiguous commit")
    if "base_commit" not in repo:
        errors.append("governance repo provenance is missing base_commit")

    expected_values = [
        ("overall status", current.get("overall_status"), "NO_GO_RESEARCH_ONLY"),
        ("north star", current.get("north_star"), GOVERNANCE_NORTH_STAR),
        ("control id", control.get("id"), "current_r1_r2_baseline"),
        ("control status", control.get("status"), "CURRENT_RESEARCH_CONTROL"),
        (
            "control admission status",
            control.get("admission_status"),
            "RESEARCH_CONTROL_NOT_DEPLOYMENT_AUTHORIZED",
        ),
        ("control ledger SHA256", control.get("ledger_sha256"), CURRENT_CONTROL_LEDGER_SHA256),
        ("control trades", metrics.get("trades"), 678),
        ("control win rate", metrics.get("win_rate_pct"), 51.03),
        ("control realized W/L", metrics.get("realized_win_loss"), 2.6082),
        ("control PF", metrics.get("profit_factor"), 2.7182),
        ("control net", metrics.get("net_usd"), 9640.05),
        ("control stressed net", metrics.get("stress_net_minus_0_30_per_ticket_usd"), 9436.65),
        ("control recent-three-month net", metrics.get("recent_three_month_net_usd"), 764.92),
        ("control max closed DD", metrics.get("max_closed_drawdown_usd"), 889.69),
        ("control positive months", metrics.get("positive_months"), 26),
        ("control active weekdays", metrics.get("active_weekdays_pct_approx"), 21.28),
        ("R1 status", r1.get("status"), "RESEARCH_CONTROL_ONLY"),
        ("R1 role", r1.get("role"), "Primary bullish/uptrend profit engine"),
        ("R2 status", r2.get("status"), "RESEARCH_CONTROL_ONLY"),
        ("R2 role", r2.get("role"), "Strict downtrend hedge and secondary profit source"),
        ("R3 standalone status", r3.get("standalone_status"), "EXCLUDED"),
        ("R3 portfolio status", r3.get("portfolio_status"), "KILLED_BY_DD_GATE"),
        ("R4 status", r4.get("status"), "NO_SURVIVOR"),
        ("R4 chop default", r4.get("chop_default"), "NO_TRADE"),
        (
            "rule admissibility status",
            rule_admissibility.get("status"),
            "BLOCKED_LEGACY_RULE_ADMISSIBILITY",
        ),
        (
            "rule admissibility identity scope",
            rule_admissibility.get("identity_scope"),
            "PRESERVES_678_ROW_AUDIT_IDENTITY_ONLY",
        ),
        ("rule admissibility audit rows", rule_admissibility.get("audit_identity_rows"), 678),
        (
            "integrated admission requirement",
            rule_admissibility.get("integrated_admission_requirement"),
            "Independently qualified rule-clean sources or later reviewed governance",
        ),
        (
            "future containment requirement",
            rule_admissibility.get("future_containment_requirement"),
            "SHARED_PREREGISTERED_INTEGRATED_RISK_POLICY",
        ),
        ("rule admissibility failure status", rule_admissibility.get("otherwise"), "NO_GO"),
        (
            "attribution status",
            current.get("attribution_status"),
            "REPAIR_REQUIRED_NATIVE_POSITION_JOIN",
        ),
        ("attribution total rows", attribution_repair.get("total_rows"), 678),
        ("attribution legacy pairing", attribution_repair.get("legacy_pairing_method"), "FIFO_BY_DIRECTION"),
        ("non-native exit-deal rows", attribution_repair.get("non_native_exit_deal_rows"), 388),
        ("non-native individual-P/L rows", attribution_repair.get("non_native_individual_pnl_rows"), 387),
        ("native position count", attribution_repair.get("native_position_count"), 678),
        (
            "attribution repair required before classification",
            attribution_repair.get("required_before_classification"),
            "OUTCOME_BLIND_ENTRY_DEAL_TO_NATIVE_POSITION_ID_JOIN_AND_RECONCILIATION",
        ),
        ("development cutoff", history.get("through"), "2026-06-30"),
        ("development classification", history.get("classification"), "DEVELOPMENT_DATA"),
        ("next task", next_task.get("id"), "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS"),
        ("next task status", next_task.get("status"), "AUTHORIZED_NOT_STARTED"),
        ("EA trading logic change", next_task.get("ea_trading_logic_change"), "NONE"),
        ("primary specialist", program.get("id"), "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1"),
        ("primary specialist status", program.get("status"), "PRIMARY_INDEPENDENT_SPECIALIST_LANE"),
        ("primary next action", program.get("next_action"), "NP1-A"),
        ("deferred control task", control_diagnostic.get("id"), "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1"),
        ("deferred control task status", control_diagnostic.get("status"), "DEFERRED_CONTROL_DIAGNOSTIC"),
        ("authoritative task key", authority_map.get("authoritative_next_task_key"), "primary_next_task"),
        ("compatibility task key", authority_map.get("compatibility_next_task_key"), "control_diagnostic_task"),
    ]
    for label, actual, expected in expected_values:
        if actual != expected:
            errors.append(f"governance status {label} mismatch: actual={actual!r}; expected={expected!r}")

    if current.get("required_current_statements") != GOVERNANCE_REQUIRED_STATEMENTS:
        errors.append("governance required current statements are missing, reordered, or stale")
    if next_task_alias.get("id") != next_task.get("id") or next_task_alias.get("status") != next_task.get("status"):
        errors.append("governance next_task alias does not point to the authoritative primary task")
    if rule_admissibility.get("sources") != GOVERNANCE_RULE_ADMISSIBILITY_SOURCES:
        errors.append("governance rule-admissibility source list is missing, reordered, or stale")
    for label, value in (
        ("untouched holdout", history.get("untouched_holdout")),
        ("demo authorization", authorization.get("demo_authorized")),
        ("live authorization", authorization.get("live_authorized")),
        ("broker action authorization", authorization.get("broker_action_authorized")),
        ("runtime touched", authorization.get("runtime_touched")),
        ("strategy change authorization", next_task.get("strategy_change_authorized")),
        ("parallel specialist authorization", program.get("parallel_specialist_lane_authorized")),
        ("historical R6 P/L authorization", program.get("historical_pnl_authorized")),
        ("control task primary authority", control_diagnostic.get("authoritative_for_primary_program")),
        ("control task blocks R6", control_diagnostic.get("blocks_r6_standalone_discovery")),
        (
            "legacy rules endorsed for integrated admission",
            rule_admissibility.get("rules_endorsed_for_integrated_admission"),
        ),
        (
            "router-audit rule change authorization",
            rule_admissibility.get("router_audit_rule_change_authorized"),
        ),
        (
            "source-local containment reusable for standalone admission",
            rule_admissibility.get("source_local_containment_reusable_for_standalone_admission"),
        ),
        ("FIFO fallback authorization", attribution_repair.get("fifo_fallback_authorized")),
        ("attribution strategy change authorization", attribution_repair.get("strategy_change_authorized")),
    ):
        if value is not False:
            errors.append(f"governance status {label} must be boolean false; actual={value!r}")
    for label, value in (
        ("aggregate exit/P&L multiset exact", attribution_repair.get("aggregate_exit_pnl_multiset_exact")),
        ("source totals exact", attribution_repair.get("source_totals_exact")),
        ("portfolio totals exact", attribution_repair.get("portfolio_totals_exact")),
        ("native positions recoverable", attribution_repair.get("native_positions_recoverable")),
    ):
        if value is not True:
            errors.append(f"governance status {label} must be boolean true; actual={value!r}")

    documents = _mapping(summary.get("source_documents"))
    for key, expected_relative in GOVERNANCE_DOCUMENTS.items():
        document = _mapping(documents.get(key))
        if document.get("path") != expected_relative:
            errors.append(
                f"governance document path mismatch for {key}: "
                f"actual={document.get('path')!r}; expected={expected_relative!r}"
            )
            continue
        source_path = repo_root / expected_relative
        if not source_path.is_file():
            errors.append(f"missing governance source document {key}: {source_path}")
            continue
        actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if document.get("sha256") != actual_hash:
            errors.append(
                f"governance source hash mismatch for {key}: "
                f"status={document.get('sha256')!r}; actual={actual_hash!r}"
            )

    ledger_path = repo_root / str(control.get("ledger", ""))
    if not ledger_path.is_file():
        errors.append(f"missing frozen current-control ledger: {ledger_path}")
    else:
        ledger_bytes = ledger_path.read_bytes()
        checkout_sha256 = hashlib.sha256(ledger_bytes).hexdigest()
        crlf_sha256 = (
            hashlib.sha256(ledger_bytes.replace(b"\n", b"\r\n")).hexdigest()
            if b"\r" not in ledger_bytes
            else ""
        )
        if checkout_sha256 != CURRENT_CONTROL_LEDGER_SHA256 and crlf_sha256 != CURRENT_CONTROL_LEDGER_SHA256:
            errors.append(f"frozen current-control ledger hash mismatch: {ledger_path}")
        if control.get("checkout_sha256") != checkout_sha256:
            errors.append("frozen current-control checkout hash does not match status provenance")
        expected_representation = (
            "exact_frozen_bytes"
            if checkout_sha256 == CURRENT_CONTROL_LEDGER_SHA256
            else "git_lf_checkout_of_frozen_crlf_artifact"
        )
        if control.get("checkout_representation") != expected_representation:
            errors.append("frozen current-control checkout representation is incorrect")

    markdown = markdown_path.read_text(encoding="utf-8", errors="replace")
    dashboard = status_path.read_text(encoding="utf-8", errors="replace")
    required_surface_fragments = [
        GOVERNANCE_NORTH_STAR,
        *GOVERNANCE_REQUIRED_STATEMENTS,
        "current_r1_r2_baseline",
        "PRIMARY_INDEPENDENT_SPECIALIST_LANE",
        "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1",
        "NP1-A",
        "RESEARCH_CONTROL_ONLY",
        "EXCLUDED",
        "DEFERRED_CONTROL_DIAGNOSTIC",
        "primary_next_task",
        "control_diagnostic_task",
        "STANDALONE_SHADOW_ONLY",
        "KILLED_BY_DD_GATE",
        "NO_SURVIVOR",
        "NO_TRADE",
        "BLOCKED_LEGACY_RULE_ADMISSIBILITY",
        "PRESERVES_678_ROW_AUDIT_IDENTITY_ONLY",
        "FORBIDDEN_SELECTION_RULE",
        "SOURCE_LOCAL_CONTAINMENT_NOT_ADMISSION_EVIDENCE",
        "PREVIOUS_MONTH_PNL_HEALTH_GATE",
        "R1_DIRECTIONAL_SESSION_GATE",
        "R2_DIRECTIONAL_SESSION_GATE",
        "R2_DAILY_LOSS_STOP",
        "h4_d1_long_best_box2_atr80",
        "r1_h1_pullback_long_v1",
        "r2_pullback_rejection_short_v1",
        "r2_continuation_short_v1",
        "preserve the 678-row audit identity only",
        "Future containment must be a shared preregistered integrated risk policy.",
        "Integrated admission requires independently qualified rule-clean sources or later reviewed governance.",
        "Otherwise the result is",
        "REPAIR_REQUIRED_NATIVE_POSITION_JOIN",
        "388/678",
        "387/678",
        "source/portfolio totals remain exact",
        "all 678 native positions are recoverable",
        "before any router classification",
        "no strategy change is authorized",
        "2026-06-30",
        "DEVELOPMENT_DATA",
        "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_V1",
        "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS",
    ]
    for name, surface in (("status_summary.md", markdown), ("status.html", dashboard)):
        for fragment in required_surface_fragments:
            if fragment not in surface:
                errors.append(f"{name} is missing governance fragment: {fragment}")
        for stale in (
            "BROKER_ACTION_ENABLED",
            "PASS_ATTACHED",
            "OWNER_AUTHORIZED_DEMO_BROKER_ACTION",
            "event_reaction_v0_exact_mt5",
            "short_hedge_v2_breakdown_retest",
        ):
            if stale in surface:
                errors.append(f"{name} contains stale non-governance status: {stale}")
    for expected_relative in GOVERNANCE_DOCUMENTS.values():
        if expected_relative not in markdown:
            errors.append(f"status_summary.md is missing governance document link: {expected_relative}")
        if f'href="{html.escape(expected_relative, quote=True)}"' not in dashboard:
            errors.append(f"status.html is missing governance document link: {expected_relative}")
    if len(dashboard.encode("utf-8")) > 100_000:
        errors.append("status.html governance surface is not compact (exceeds 100000 UTF-8 bytes)")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_runtime_inventory(path: Path) -> list[dict[str, str]]:
    data = path.read_bytes()
    if b"\x00" in data[:200]:
        text = data.decode("utf-16", errors="replace")
    else:
        text = data.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(text.splitlines()))


def _verify_protected_breakout_core_summary(
    errors: list[str],
    status_summary_md: str,
    runtime_inventory: list[dict[str, str]],
) -> None:
    active_rows = [
        row
        for row in runtime_inventory
        if row.get("expert") == "Phase2ExperimentalDemoExecutor"
        and row.get("symbol") == "XAUUSD"
        and row.get("InpCandidate") == "breakout_retest"
        and row.get("derived_magic") == "920101"
        and row.get("broker_action_state") == "BROKER_ACTION_ENABLED"
        and row.get("InpAllowedAccountLoginsCsv") in {"1025742", "1033030"}
        and row.get("InpTradeSessionStartHour") == "0"
        and row.get("InpTradeSessionEndHour") == "23"
    ]
    if "Source: `runtime_inventory`" not in status_summary_md:
        errors.append("status_summary.md Protected Breakout Core is not sourced from runtime_inventory")
    for row in active_rows:
        expected = (
            f"| `{row.get('lane')} {row.get('chart')}` | `breakout_retest` | "
            f"`{row.get('InpAllowedAccountLoginsCsv')}` | `920101` | "
            f"`{row.get('InpTradeSessionStartHour')}->{row.get('InpTradeSessionEndHour')}` | "
            f"`enabled={row.get('InpSmartTrendFilterEnabled')} shadow={row.get('InpSmartTrendFilterShadowOnly')} "
            f"D1_required={row.get('InpSmartTrendRequireD1')} D1={row.get('InpSmartTrendMinD1Aligned')} "
            f"H1_required={row.get('InpSmartTrendRequireH1')} H1={row.get('InpSmartTrendMinH1Aligned')}` | "
            f"`{row.get('InpDryRunOnly')}` | `{row.get('InpBrokerActionAllowed')}` | `BROKER_ACTION_ENABLED` |"
        )
        if expected not in status_summary_md:
            errors.append(f"status_summary.md missing runtime protected breakout row: {expected}")
    stale_fragment = "| `chart06.chr` | `swing_breakout_retest_v0` |"
    if stale_fragment in status_summary_md:
        errors.append("status_summary.md still lists stale chart06 swing_breakout_retest_v0 as protected core")


def _verify_a1_momentum_summary(
    errors: list[str],
    status_html: str,
    status_summary_md: str,
    report: dict[str, Any],
) -> None:
    ea = report.get("ea", {})
    required_summary_fragments = [
        "## A1 Momentum Continuation Lane",
        f"| Status | `{report.get('status', '')}` |",
        f"| EA | `{ea.get('name', '')}` |",
        f"| Magic | `{ea.get('magic', '')}` |",
        f"| Run ID | `{ea.get('run_id', '')}` |",
        "| Dedicated kill switch | `a1_xau_m5_momentum_rr2_kill_switch.txt` |",
    ]
    for fragment in required_summary_fragments:
        if fragment not in status_summary_md:
            errors.append(f"status_summary.md missing A1 momentum lane fragment: {fragment}")
    report_link = "A1 XAU M5 momentum RR2 long-only attachment"
    if report_link not in status_html:
        errors.append("status.html missing A1 XAU M5 momentum-continuation attachment link")


def _markdown_status(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _parse_measured_cost(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"status": _markdown_status(path)}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("|") or "Observed Rows" not in line or "Observed Days" not in line:
            continue
        if index + 2 >= len(lines):
            continue
        headers = [part.strip() for part in line.strip("|").split("|")]
        values = [part.strip() for part in lines[index + 2].strip("|").split("|")]
        row = dict(zip(headers, values))
        result["observed_rows"] = row.get("Observed Rows", "")
        result["observed_days"] = row.get("Observed Days", "")
        result["required_days"] = row.get("Required Days", "")
        break
    return result


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_rows(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _to_float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _status_class(value: str) -> str:
    upper = value.upper()
    if upper == "FALSE":
        return "pass"
    if "EXPERIMENTAL" in upper:
        return "pending"
    if "PASS" in upper or "ACCEPTED" in upper or "ACTIVE" in upper or "GREEN" in upper:
        return "pass"
    if "FAIL" in upper or "REJECTED" in upper or "BLOCKED" in upper:
        return "fail"
    if "PENDING" in upper or "PROVISIONAL" in upper or "WARN" in upper or "NOT_READY" in upper or "%" in upper or "ORANGE" in upper or "YELLOW" in upper:
        return "pending"
    return "unknown"


def _compact_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    marker = "xau-usd/"
    if marker in normalized:
        return marker + normalized.split(marker, 1)[1]
    return normalized


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description="Verify that status.html matches canonical project reports.")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--status-path", type=Path, default=None)
    args = parser.parse_args(argv)
    errors = verify_status_dashboard_freshness(args.repo_root, args.status_path)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Status dashboard freshness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
