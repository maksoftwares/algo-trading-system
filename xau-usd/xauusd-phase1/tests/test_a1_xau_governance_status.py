from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DOC_NAMES = (
    "A1_XAU_PROFITABLE_SYSTEM_MASTER_DIRECTION_2026_07_10.md",
    "A1_XAU_CURRENT_RESEARCH_FREEZE_2026_07_10.md",
    "A1_XAU_ROUTER_ENTRY_HOLD_PATH_AUDIT_PREREG_2026_07_10.md",
    "A1_XAU_INDEPENDENT_SPECIALIST_PRIMARY_DIRECTION_2026_07_12.md",
)
LEDGER_RELATIVE = Path(
    "xau-usd/xauusd-phase1/outputs/reports/"
    "A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_"
    "current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv"
)
NORTH_STAR = (
    "Build an automated XAUUSD system that produces positive net returns over rolling 6- and 12-month "
    "periods, survives realistic costs and regime changes, limits portfolio equity drawdown, and can "
    "eventually support controlled withdrawals from accumulated profits."
)
REQUIRED_STATEMENTS = [
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
RULE_ADMISSIBILITY_SOURCES = [
    {
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule": "Previous-month P/L health gate (enabled; minimum net -$50)",
        "retained_rule_type": "PREVIOUS_MONTH_PNL_HEALTH_GATE",
        "source_id": "h4_d1_long_best_box2_atr80",
    },
    {
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule": "R1 directional session 09 <= hour < 15",
        "retained_rule_type": "R1_DIRECTIONAL_SESSION_GATE",
        "source_id": "r1_h1_pullback_long_v1",
    },
    {
        "admissibility_issue_type": "FORBIDDEN_SELECTION_RULE",
        "retained_rule": "R2 directional session 05 <= hour < 19",
        "retained_rule_type": "R2_DIRECTIONAL_SESSION_GATE",
        "source_id": "r2_pullback_rejection_short_v1",
    },
    {
        "admissibility_issue_type": "SOURCE_LOCAL_CONTAINMENT_NOT_ADMISSION_EVIDENCE",
        "retained_rule": "R2 $10 daily-loss stop",
        "retained_rule_type": "R2_DAILY_LOSS_STOP",
        "source_id": "r2_continuation_short_v1",
    },
]


def test_incomplete_governance_document_set_preserves_legacy_schema(tmp_path: Path):
    repo = tmp_path / "repo"
    docs = repo / "xau-usd" / "xauusd-phase1" / "docs"
    docs.mkdir(parents=True)
    for name in DOC_NAMES[:3]:
        (docs / name).write_text(f"# {name}\n", encoding="utf-8")

    module = _load_script("generate_project_status_summary")
    json_path, _ = module.generate_project_status_summary(
        repo,
        now=datetime(2026, 7, 10, 12, 34, 56, tzinfo=timezone.utc),
    )

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["schema_version"] == "project_status_summary_v2"
    assert "current" not in summary
    assert not (repo / "xau-usd" / "xauusd-phase1" / "status_summary.json").exists()


def test_governance_summary_is_single_current_truth_and_writes_phase_local_pointers(tmp_path: Path):
    repo = _governance_repo(tmp_path)
    module = _load_script("generate_project_status_summary")

    json_path, md_path = module.generate_project_status_summary(
        repo,
        now=datetime(2026, 7, 10, 12, 34, 56, tzinfo=timezone.utc),
    )

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    current = summary["current"]
    control = current["portfolio_control"]
    assert summary["schema_version"] == "a1_xau_governance_status_v1"
    assert summary["generated_at_utc"] == "2026-07-10T12:34:56Z"
    assert "base_commit" in summary["repo"]
    assert "commit" not in summary["repo"]
    assert current["north_star"] == NORTH_STAR
    assert current["required_current_statements"] == REQUIRED_STATEMENTS
    assert control["id"] == "current_r1_r2_baseline"
    assert control["status"] == "CURRENT_RESEARCH_CONTROL"
    assert control["ledger_sha256"] == "47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52"
    fixture_ledger = repo / LEDGER_RELATIVE
    assert control["checkout_sha256"] == hashlib.sha256(fixture_ledger.read_bytes()).hexdigest()
    assert control["checkout_representation"] in {
        "exact_frozen_bytes",
        "git_lf_checkout_of_frozen_crlf_artifact",
    }
    assert control["metrics"] == {
        "active_weekdays_pct_approx": 21.28,
        "max_closed_drawdown_usd": 889.69,
        "net_usd": 9640.05,
        "positive_months": 26,
        "profit_factor": 2.7182,
        "realized_win_loss": 2.6082,
        "recent_three_month_net_usd": 764.92,
        "stress_net_minus_0_30_per_ticket_usd": 9436.65,
        "trades": 678,
        "win_rate_pct": 51.03,
    }
    assert current["specialists"]["R1"] == {
        "compatibility_frozen_status": "CURRENT_RESEARCH_CONTROL_COMPONENT",
        "role": "Primary bullish/uptrend profit engine",
        "status": "RESEARCH_CONTROL_ONLY",
    }
    assert current["specialists"]["R2"] == {
        "compatibility_frozen_status": "CURRENT_RESEARCH_CONTROL_COMPONENT",
        "role": "Strict downtrend hedge and secondary profit source",
        "status": "RESEARCH_CONTROL_ONLY",
    }
    assert current["specialists"]["R3"] == {
        "compatibility_frozen_status": "STANDALONE_SHADOW_ONLY",
        "portfolio_status": "KILLED_BY_DD_GATE",
        "standalone_status": "EXCLUDED",
    }
    assert current["specialists"]["R4"] == {"chop_default": "NO_TRADE", "status": "NO_SURVIVOR"}
    assert current["rule_admissibility"] == {
        "audit_identity_rows": 678,
        "identity_scope": "PRESERVES_678_ROW_AUDIT_IDENTITY_ONLY",
        "integrated_admission_requirement": (
            "Independently qualified rule-clean sources or later reviewed governance"
        ),
        "future_containment_requirement": "SHARED_PREREGISTERED_INTEGRATED_RISK_POLICY",
        "otherwise": "NO_GO",
        "router_audit_rule_change_authorized": False,
        "rules_endorsed_for_integrated_admission": False,
        "source_local_containment_reusable_for_standalone_admission": False,
        "sources": RULE_ADMISSIBILITY_SOURCES,
        "status": "BLOCKED_LEGACY_RULE_ADMISSIBILITY",
    }
    assert current["attribution_status"] == "REPAIR_REQUIRED_NATIVE_POSITION_JOIN"
    assert current["attribution_repair"] == {
        "aggregate_exit_pnl_multiset_exact": True,
        "fifo_fallback_authorized": False,
        "legacy_pairing_method": "FIFO_BY_DIRECTION",
        "native_position_count": 678,
        "native_positions_recoverable": True,
        "non_native_exit_deal_rows": 388,
        "non_native_individual_pnl_rows": 387,
        "portfolio_totals_exact": True,
        "required_before_classification": (
            "OUTCOME_BLIND_ENTRY_DEAL_TO_NATIVE_POSITION_ID_JOIN_AND_RECONCILIATION"
        ),
        "source_totals_exact": True,
        "strategy_change_authorized": False,
        "total_rows": 678,
    }
    assert current["historical_evidence"] == {
        "classification": "DEVELOPMENT_DATA",
        "through": "2026-06-30",
        "untouched_holdout": False,
    }
    assert current["authorization"] == {
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "runtime_touched": False,
    }
    assert current["primary_next_task"] == {
        "ea_trading_logic_change": "NONE",
        "id": "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS",
        "status": "AUTHORIZED_NOT_STARTED",
        "strategy_change_authorized": False,
    }
    assert current["next_task"] == {
        **current["primary_next_task"],
        "authority": "ALIAS_OF_PRIMARY_NEXT_TASK",
    }
    assert current["authority_map"] == {
        "authoritative_next_task_key": "primary_next_task",
        "authoritative_statements_key": "required_current_statements",
        "compatibility_next_task_key": "control_diagnostic_task",
        "compatibility_statements_key": "control_diagnostic_compatibility_statements",
    }
    assert current["independent_specialist_program"] == {
        "historical_pnl_authorized": False,
        "id": "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1",
        "next_action": "NP1-A",
        "np1_status": "MANDATORY_PREREQUISITE_WITHIN_R6",
        "parallel_specialist_lane_authorized": False,
        "range_box_status": "BACKLOG_ONLY_IF_R6_CLOSES",
        "status": "PRIMARY_INDEPENDENT_SPECIALIST_LANE",
    }
    assert current["control_diagnostic_task"]["status"] == "DEFERRED_CONTROL_DIAGNOSTIC"

    markdown = md_path.read_text(encoding="utf-8")
    assert NORTH_STAR in markdown
    assert all(statement in markdown for statement in REQUIRED_STATEMENTS)
    assert "BLOCKED_LEGACY_RULE_ADMISSIBILITY" in markdown
    assert all(source["source_id"] in markdown for source in RULE_ADMISSIBILITY_SOURCES)
    assert "preserve the 678-row audit identity only" in markdown
    assert "Future containment must be a shared preregistered integrated risk policy" in markdown
    assert "Integrated admission requires independently qualified rule-clean sources or later reviewed governance" in markdown
    assert "REPAIR_REQUIRED_NATIVE_POSITION_JOIN" in markdown
    assert "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1" in markdown
    assert "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS" in markdown
    assert "DEFERRED_CONTROL_DIAGNOSTIC" in markdown
    assert "388/678" in markdown
    assert "387/678" in markdown
    assert "before any router classification" in markdown
    assert "BROKER_ACTION_ENABLED" not in markdown
    assert "PASS_ATTACHED" not in markdown

    phase1_root = repo / "xau-usd" / "xauusd-phase1"
    pointer = json.loads((phase1_root / "status_summary.json").read_text(encoding="utf-8"))
    assert pointer["schema_version"] == "a1_xau_status_pointer_v1"
    assert pointer["canonical_json"] == "../../status_summary.json"
    assert pointer["canonical_markdown"] == "../../status_summary.md"
    pointer_md = (phase1_root / "status_summary.md").read_text(encoding="utf-8")
    assert "LEGACY_LOCATION_NOT_CANONICAL" in pointer_md
    assert "non-authoritative" in pointer_md


def test_governance_dashboard_is_compact_and_both_verifiers_fail_closed_on_tamper(tmp_path: Path):
    repo = _governance_repo(tmp_path)
    summary_module = _load_script("generate_project_status_summary")
    page_module = _load_script("generate_project_status_page")
    dashboard_verifier = _load_script("verify_status_dashboard_freshness")
    report_verifier = _load_script("verify_status_report_freshness")

    json_path, _ = summary_module.generate_project_status_summary(
        repo,
        now=datetime(2026, 7, 10, 12, 34, 56, tzinfo=timezone.utc),
    )
    output = page_module.generate_project_status_page(repo)
    dashboard = output.output_path.read_text(encoding="utf-8")

    assert output.phase1_status == "RESEARCH_CONTROL"
    assert output.phase2_status == "NO_GO"
    assert len(dashboard.encode("utf-8")) < 100_000
    assert NORTH_STAR in dashboard
    assert all(statement in dashboard for statement in REQUIRED_STATEMENTS)
    assert "BLOCKED_LEGACY_RULE_ADMISSIBILITY" in dashboard
    assert all(source["source_id"] in dashboard for source in RULE_ADMISSIBILITY_SOURCES)
    assert "preserve the 678-row audit identity only" in dashboard
    assert "Future containment must be a shared preregistered integrated risk policy" in dashboard
    assert "Integrated admission requires independently qualified rule-clean sources or later reviewed governance" in dashboard
    assert "REPAIR_REQUIRED_NATIVE_POSITION_JOIN" in dashboard
    assert "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1" in dashboard
    assert "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS" in dashboard
    assert "DEFERRED_CONTROL_DIAGNOSTIC" in dashboard
    assert "388/678" in dashboard
    assert "387/678" in dashboard
    assert "before any router classification" in dashboard
    assert all(name in dashboard for name in DOC_NAMES)
    for stale in (
        "BROKER_ACTION_ENABLED",
        "PASS_ATTACHED",
        "OWNER_AUTHORIZED_DEMO_BROKER_ACTION",
        "event_reaction_v0_exact_mt5",
        "short_hedge_v2_breakdown_retest",
    ):
        assert stale not in dashboard
    assert dashboard_verifier.verify_status_dashboard_freshness(repo, output.output_path) == []
    assert report_verifier.verify_status_report_freshness(repo, output.output_path) == []

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    payload["current"]["rule_admissibility"]["status"] = "PASS"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    dashboard_errors = dashboard_verifier.verify_status_dashboard_freshness(repo, output.output_path)
    report_errors = report_verifier.verify_status_report_freshness(repo, output.output_path)
    assert any("rule admissibility status mismatch" in error for error in dashboard_errors)
    assert any("rule admissibility status mismatch" in error for error in report_errors)

    payload["current"]["rule_admissibility"]["status"] = "BLOCKED_LEGACY_RULE_ADMISSIBILITY"
    payload["current"]["attribution_status"] = "PASS"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    dashboard_errors = dashboard_verifier.verify_status_dashboard_freshness(repo, output.output_path)
    report_errors = report_verifier.verify_status_report_freshness(repo, output.output_path)
    assert any("attribution status mismatch" in error for error in dashboard_errors)
    assert any("attribution status mismatch" in error for error in report_errors)

    payload["current"]["attribution_status"] = "REPAIR_REQUIRED_NATIVE_POSITION_JOIN"
    payload["current"]["authorization"]["broker_action_authorized"] = True
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    dashboard_errors = dashboard_verifier.verify_status_dashboard_freshness(repo, output.output_path)
    report_errors = report_verifier.verify_status_report_freshness(repo, output.output_path)
    assert any("broker action authorization must be boolean false" in error for error in dashboard_errors)
    assert any("broker action authorization must be boolean false" in error for error in report_errors)


@pytest.mark.parametrize(
    ("mutation", "error_type", "message"),
    [
        ("missing", FileNotFoundError, "Frozen current-control ledger is missing"),
        ("tampered", ValueError, "Frozen current-control ledger SHA256 mismatch"),
    ],
)
def test_governance_summary_fails_closed_on_frozen_ledger_drift(
    tmp_path: Path,
    mutation: str,
    error_type: type[Exception],
    message: str,
):
    repo = _governance_repo(tmp_path)
    ledger = repo / LEDGER_RELATIVE
    if mutation == "missing":
        ledger.unlink()
    else:
        ledger.write_bytes(ledger.read_bytes() + b"\ntampered\n")

    module = _load_script("generate_project_status_summary")
    with pytest.raises(error_type, match=message):
        module.generate_project_status_summary(repo)
    assert not (repo / "status_summary.json").exists()
    assert not (repo / "status_summary.md").exists()


def test_checked_in_governance_status_supersedes_primary_task_without_authorizing_runtime():
    summary = json.loads((REPO_ROOT / "status_summary.json").read_text(encoding="utf-8"))
    current = summary["current"]

    assert current["overall_status"] == "NO_GO_RESEARCH_ONLY"
    assert current["independent_specialist_program"]["status"] == (
        "PRIMARY_INDEPENDENT_SPECIALIST_LANE"
    )
    assert current["independent_specialist_program"]["id"] == (
        "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1"
    )
    assert current["independent_specialist_program"]["next_action"] == "NP1-A"
    assert current["independent_specialist_program"]["parallel_specialist_lane_authorized"] is False
    assert current["router_entry_hold_audit"] == {
        "blocks_r6_standalone_discovery": False,
        "required_before_old_control_integration": True,
        "status": "DEFERRED_CONTROL_DIAGNOSTIC",
    }
    assert current["authorization"] == {
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "runtime_touched": False,
    }
    assert current["primary_next_task"]["id"] == (
        "R6-NP1-A_MARKET_ONLY_NATIVE_PARITY_ACQUISITION_LOCKS"
    )
    assert current["primary_next_task"]["ea_trading_logic_change"] == "NONE"
    assert current["primary_next_task"]["strategy_change_authorized"] is False


def _governance_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    docs = repo / "xau-usd" / "xauusd-phase1" / "docs"
    docs.mkdir(parents=True)
    for name in DOC_NAMES:
        (docs / name).write_text(f"# {name}\n\nGovernance test fixture.\n", encoding="utf-8")
    ledger_target = repo / LEDGER_RELATIVE
    ledger_target.parent.mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / LEDGER_RELATIVE, ledger_target)
    return repo


def _load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    module_name = f"test_a1_xau_governance_{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
