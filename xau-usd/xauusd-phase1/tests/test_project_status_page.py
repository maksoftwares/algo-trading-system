from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_status_page_renders_milestones_and_candidates(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    phase0_reports = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase0_manifests = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "manifests"
    phase0_matrix = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "matrix_results"
    phase0_docs = repo / "xau-usd" / "xauusd-phase0" / "docs"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase3_reports = repo / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"
    phase0_reports.mkdir(parents=True)
    phase0_manifests.mkdir(parents=True)
    phase0_docs.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    phase3_reports.mkdir(parents=True)
    _write_phase1_summary(phase1_reports / "PHASE1_STATUS_SUMMARY.json")
    _write_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md", "PENDING")
    _write_status(phase1_reports / "PHASE2_READINESS_REPORT.md", "PENDING")
    _write_phase2_countdown(phase1_reports / "PHASE2_DEMO_COUNTDOWN.json")
    _write_phase2_preflight(phase1_reports / "PHASE2_DEMO_PREFLIGHT.json")
    _write_phase2_experimental_demo_terminal(phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json")
    _write_phase2_experimental_demo_attachments(phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json")
    _write_phase2_next_actions(phase1_reports / "PHASE2_DEMO_NEXT_ACTIONS.json")
    _write_phase2_owner_packet(phase1_reports / "PHASE2_OWNER_ACTION_PACKET.json")
    _write_phase2_vps_selection_check(phase1_reports / "PHASE2_VPS_SELECTION_DECISION_CHECK.json")
    _write_phase2_bootstrap(phase1_reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json")
    _write_phase3_status(phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json")
    _write_phase3_handoff(phase3_reports / "PHASE3_TO_DEMO_HANDOFF.json")
    (phase0_reports / "PHASE0_VERDICT.md").write_text(
        "| breakout_retest | PASS | PASS | PASS | PASS | PASS | PASS |\n",
        encoding="utf-8",
    )
    _write_fixed_notional(phase0_reports / "FIXED_NOTIONAL_REPORT.md")
    _write_measured_cost(phase0_reports / "MEASURED_COST_MODEL.md")
    _write_status(phase0_reports / "PHASE0_REALITY_CHECK.md", "FAIL")
    _write_family_d2(
        phase0_reports / "PHASE0_REALITY_CHECK_FAMILY_CLUSTERED.md",
        phase0_manifests / "PHASE0_REALITY_CHECK_FAMILY_CLUSTERED_MANIFEST.json",
        reviewer_accepted=True,
    )
    _write_candidate_audit(phase0_reports / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv")
    _write_candidate_backlog(phase0_docs / "CANDIDATE_RESEARCH_BACKLOG.md")
    _write_trade_ledger(
        phase0_matrix / "breakout_retest" / "cell_3_breakout_retest_capital_com_p95_trades.csv",
        [
            ("2024-01-03 10:00:00+00:00", 1.5),
            ("2024-01-07 10:00:00+00:00", -1.0),
            ("2024-02-03 10:00:00+00:00", 0.5),
        ],
    )
    _write_trade_ledger(
        phase0_matrix / "trend_pullback" / "cell_3_trend_pullback_capital_com_p95_trades.csv",
        [("2024-01-04 10:00:00+00:00", -1.0)],
    )

    output = module.generate_project_status_page(repo)

    html = output.output_path.read_text(encoding="utf-8")
    assert output.candidate_count == 3
    assert output.accepted_count == 1
    assert output.rejected_count == 1
    assert "Mission Control" in html
    assert "Phase 3 Experimental Lab" in html
    assert "EXPERIMENTAL_ACTIVE" in html
    assert "Phase 3 experimental status" in html
    assert "breakout_retest" in html
    assert "trend_pullback" in html
    assert "h4_us_session_liquidity_reversal_v0" in html
    assert "HASH_LOCKED_SMOKE_PASS_PENDING_MATRIX" in html
    assert "Five-day soak" in html
    assert "Demo Trading Countdown" in html
    assert "Experimental Demo Terminal" in html
    assert "Experimental Demo Attachments" in html
    assert "ATTACHED_TO_DEMO_TERMINAL" in html
    assert "phase2-experimental-demo-attach-v0.1" in html
    assert "DEMO_TERMINAL_VERIFIED_QUARANTINE_REQUIRED" in html
    assert "GoldMissionEAv5" in html
    assert "Demo Next Actions" in html
    assert "Earliest Gate Targets" in html
    assert "Gate Closure Map" in html
    assert "OWNER_DECISION" in html
    assert "PHASE2_VPS_SELECTION_MATRIX.md" in html
    assert "Decision record has no placeholders" in html
    assert "generate_phase2_vps_selection_decision_check.py" in html
    assert "2026-05-30T12:00:00Z" in html
    assert "Assumes no restart, no code-freeze reset, and no unexpected market-data gaps." in html
    assert "OWNER_ACTION_AND_WAIT_GATES_PENDING" in html
    assert "keep_collectors_running" in html
    assert "Demo Owner Moves" in html
    assert "Owner packet status" in html
    assert "VPS decision check" in html
    assert "VPS evidence workspace" in html
    assert "Prepared VPS Evidence Files" in html
    assert "vps_ntp_sync.txt" in html
    assert "PHASE2_VPS_SELECTION_MATRIX.md status is PENDING; required PASS." in html
    assert "matrix_readiness_gate" in html
    assert "Primary VPS trial" in html
    assert "FXVM Advanced VPS in Dubai, Mumbai, or Singapore" in html
    assert "ForexVPS.net Core in the lowest-latency available region" in html
    assert "VPS Bootstrap" in html
    assert "WAITING_AND_VPS_BOOTSTRAP_PENDING" in html
    assert "Before VPS Purchase" in html
    assert "Phase 2 VPS bootstrap packet" in html
    assert "DEMO_NOT_READY" in html
    assert "Demo preflight" in html
    assert "Phase 2 demo preflight" in html
    assert "Phase 2 experimental demo terminal" in html
    assert "Phase 2 experimental demo attachments" in html
    assert "Paper mode authorized" in html
    assert "Active-market 72-hour soak" in html
    assert "After VPS is provisioned, run scripts/capture_phase2_vps_latency_evidence.ps1" in html
    assert "Candidate-level D2 FAIL preserved; owner-accepted family-clustered D2 PASS; D1/D3/D4 remain closed" in html
    assert "D2 Reality Check/SPA FAIL; D1/D3/D4 remain closed" not in html
    assert "Observer conflicts" in html
    assert "Paper-shadow status" in html
    assert "SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS" in html
    assert "Paper-shadow would-open" in html
    assert "Shadow lifecycle status" in html
    assert "SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY" in html
    assert "Shadow lifecycle total net R" in html
    assert "Lifecycle guard status" in html
    assert "SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY" in html
    assert "Lifecycle guard total net R" in html
    assert "Demo rehearsal status" in html
    assert "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY" in html
    assert "Demo rehearsal can start real demo" in html
    assert "Demo handoff status" in html
    assert "READY_FOR_REVIEW_WAITING_REAL_GATES" in html
    assert "Demo handoff can start now" in html
    assert "Demo handoff demo authorized" in html
    assert "Demo handoff broker-action allowed" in html
    assert "Phase 3 to demo handoff" in html
    assert "Phase 2 demo countdown" in html
    assert "Phase 2 demo next actions" in html
    assert "Phase 3 paper-shadow summary" in html
    assert "Phase 3 paper-shadow ledger" in html
    assert "Phase 3 shadow lifecycle summary" in html
    assert "Phase 3 shadow lifecycle ledger" in html
    assert "Phase 3 lifecycle guard summary" in html
    assert "Phase 3 lifecycle guard ledger" in html
    assert "Phase 3 demo rehearsal checklist" in html
    assert "Phase 3 demo rehearsal ledger" in html
    assert "candidateSearch" in html
    assert "Cost edge consumption" in html
    assert "Cost viability map" in html
    assert "Breakout family lifecycle" in html
    assert "COST_REVALIDATION_PENDING" in html
    assert "$1,000 Account Example" in html
    assert "1% fixed risk per trade" in html
    assert "data-account-status-filter=\"accepted\"" in html
    assert "data-account-status-filter=\"rejected\"" in html
    assert 'data-account-row data-status="accepted"' in html
    assert 'data-account-row data-status="rejected"' in html
    assert "Monthly Returns Ledger" in html
    assert "th.status-col, td.status-col" in html
    assert '<th class="status-col">Status</th>' in html
    assert '<td class="status-col"><span class="pill pass">ACCEPTED</span></td>' in html
    assert "<th class=\"num\">Trades</th>" in html
    assert "<th class=\"num\">Win Rate</th>" in html
    assert "<th class=\"num\">Wins</th>" in html
    assert "<th class=\"num\">Losses</th>" in html
    assert "<th class=\"num\">Net R</th>" in html
    assert "<th class=\"num\">Avg R</th>" in html
    assert "<th class=\"num\">Total PnL</th>" in html
    assert "monthlySearch" in html
    assert "monthlyExpertFilter" in html
    assert "monthlyStatusFilter" in html
    assert html.index("monthlyStatusFilter") < html.index("monthlyExpertFilter")
    assert '<option value="all">All classifications</option>' in html
    assert '<option value="accepted">Accepted EAs</option>' in html
    assert '<option value="pending">Provisional EAs</option>' in html
    assert '<option value="rejected">Rejected EAs</option>' in html
    assert '<option value="breakout_retest" data-status="accepted">breakout_retest (ACCEPTED)</option>' in html
    assert '<option value="trend_pullback" data-status="rejected">trend_pullback (REJECTED)</option>' in html
    assert "monthlyExpertOptions" in html
    assert "updateMonthlyExpertOptions" in html
    assert 'data-expert="breakout_retest"' in html
    assert 'data-status="accepted"' in html
    assert 'data-status="rejected"' in html
    assert "66.67%" in html
    assert "+0.50R" in html
    assert "+0.25R" in html
    assert "+$10.00" in html
    freshness = _load_script("verify_status_dashboard_freshness")
    assert freshness.verify_status_dashboard_freshness(repo, output.output_path) == []


def test_status_dashboard_freshness_validator_detects_canonical_drift(tmp_path: Path):
    module = _load_module()
    freshness = _load_script("verify_status_dashboard_freshness")
    repo = tmp_path / "repo"
    phase0_reports = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase0_docs = repo / "xau-usd" / "xauusd-phase0" / "docs"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase3_reports = repo / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"
    phase0_reports.mkdir(parents=True)
    phase0_docs.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    phase3_reports.mkdir(parents=True)
    _write_phase1_summary(phase1_reports / "PHASE1_STATUS_SUMMARY.json")
    _write_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md", "PENDING")
    _write_status(phase1_reports / "PHASE2_READINESS_REPORT.md", "PENDING")
    _write_phase2_countdown(phase1_reports / "PHASE2_DEMO_COUNTDOWN.json")
    _write_phase2_preflight(phase1_reports / "PHASE2_DEMO_PREFLIGHT.json")
    _write_phase2_experimental_demo_terminal(phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json")
    _write_phase2_experimental_demo_attachments(phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json")
    _write_phase2_next_actions(phase1_reports / "PHASE2_DEMO_NEXT_ACTIONS.json")
    _write_phase2_owner_packet(phase1_reports / "PHASE2_OWNER_ACTION_PACKET.json")
    _write_phase2_vps_selection_check(phase1_reports / "PHASE2_VPS_SELECTION_DECISION_CHECK.json")
    _write_phase2_bootstrap(phase1_reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json")
    _write_phase3_status(phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json")
    _write_phase3_handoff(phase3_reports / "PHASE3_TO_DEMO_HANDOFF.json")
    _write_fixed_notional(phase0_reports / "FIXED_NOTIONAL_REPORT.md")
    _write_measured_cost(phase0_reports / "MEASURED_COST_MODEL.md")
    _write_candidate_audit(phase0_reports / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv")
    _write_candidate_backlog(phase0_docs / "CANDIDATE_RESEARCH_BACKLOG.md")
    output = module.generate_project_status_page(repo)

    assert freshness.verify_status_dashboard_freshness(repo, output.output_path) == []

    _write_phase1_summary(
        phase1_reports / "PHASE1_STATUS_SUMMARY.json",
        soak={"progress_pct": 50.0, "observed_days": 2.5, "required_days": 5},
    )
    _write_phase2_countdown(phase1_reports / "PHASE2_DEMO_COUNTDOWN.json", pending_gate_count=123)
    _write_phase2_preflight(phase1_reports / "PHASE2_DEMO_PREFLIGHT.json", status="RECHECK_REQUIRED")
    _write_phase2_experimental_demo_terminal(
        phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json",
        status="DEMO_TERMINAL_VERIFIED_READY_FOR_SAFE_SETUP",
        clean=True,
        active_expert=False,
    )
    _write_phase2_next_actions(
        phase1_reports / "PHASE2_DEMO_NEXT_ACTIONS.json",
        status="OWNER_ACTION_REQUIRED_AFTER_VPS_SELECTION",
        pending_gate_count=123,
        do_now_action="Pick the final VPS plan.",
    )
    _write_phase2_owner_packet(
        phase1_reports / "PHASE2_OWNER_ACTION_PACKET.json",
        primary_trial="ForexVPS.net Core in London",
    )
    _write_phase2_vps_selection_check(
        phase1_reports / "PHASE2_VPS_SELECTION_DECISION_CHECK.json",
        status="PASS",
        next_action="VPS selection evidence is ready for the broader Phase 2 readiness report.",
    )
    _write_phase2_bootstrap(
        phase1_reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json",
        status="VPS_BOOTSTRAP_ACTION_REQUIRED",
    )
    _write_phase3_handoff(
        phase3_reports / "PHASE3_TO_DEMO_HANDOFF.json",
        status="READY_FOR_OWNER_REVIEW_BEFORE_REAL_BRANCH",
    )
    errors = freshness.verify_status_dashboard_freshness(repo, output.output_path)
    assert any("status.html is missing soak observed days: 2.5" in error for error in errors)
    assert any("status.html is missing soak progress pct: 50.00%" in error for error in errors)
    assert any("status.html is missing demo countdown pending gate count: 123" in error for error in errors)
    assert any("status.html is missing demo preflight status: RECHECK_REQUIRED" in error for error in errors)
    assert any(
        "status.html is missing demo next-actions status: OWNER_ACTION_REQUIRED_AFTER_VPS_SELECTION" in error
        for error in errors
    )
    assert any("status.html is missing demo next-action text keep_collectors_running" in error for error in errors)
    assert any("status.html is missing owner packet primary vps trial: ForexVPS.net Core in London" in error for error in errors)
    assert any("status.html is missing vps selection decision check status: PASS" in error for error in errors)
    assert any(
        "status.html is missing vps selection decision next action: VPS selection evidence is ready" in error
        for error in errors
    )
    assert any("status.html is missing vps bootstrap status: VPS_BOOTSTRAP_ACTION_REQUIRED" in error for error in errors)
    assert any(
        "status.html is missing demo handoff status: READY_FOR_OWNER_REVIEW_BEFORE_REAL_BRANCH" in error
        for error in errors
    )


def test_status_dashboard_freshness_validator_ignores_checkout_mtime_when_content_matches(tmp_path: Path):
    module = _load_module()
    freshness = _load_script("verify_status_dashboard_freshness")
    repo = tmp_path / "repo"
    phase0_reports = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase0_docs = repo / "xau-usd" / "xauusd-phase0" / "docs"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase3_reports = repo / "xau-usd" / "xauusd-phase3-experimental" / "outputs" / "reports"
    phase0_reports.mkdir(parents=True)
    phase0_docs.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    phase3_reports.mkdir(parents=True)
    _write_phase1_summary(phase1_reports / "PHASE1_STATUS_SUMMARY.json")
    _write_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md", "PENDING")
    _write_status(phase1_reports / "PHASE2_READINESS_REPORT.md", "PENDING")
    _write_phase2_countdown(phase1_reports / "PHASE2_DEMO_COUNTDOWN.json")
    _write_phase2_preflight(phase1_reports / "PHASE2_DEMO_PREFLIGHT.json")
    _write_phase2_experimental_demo_terminal(phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json")
    _write_phase2_experimental_demo_attachments(phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_ATTACHMENTS.json")
    _write_phase2_next_actions(phase1_reports / "PHASE2_DEMO_NEXT_ACTIONS.json")
    _write_phase2_owner_packet(phase1_reports / "PHASE2_OWNER_ACTION_PACKET.json")
    _write_phase2_vps_selection_check(phase1_reports / "PHASE2_VPS_SELECTION_DECISION_CHECK.json")
    _write_phase2_bootstrap(phase1_reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json")
    _write_phase3_status(phase3_reports / "PHASE3_EXPERIMENTAL_STATUS.json")
    _write_phase3_handoff(phase3_reports / "PHASE3_TO_DEMO_HANDOFF.json")
    _write_fixed_notional(phase0_reports / "FIXED_NOTIONAL_REPORT.md")
    _write_measured_cost(phase0_reports / "MEASURED_COST_MODEL.md")
    _write_candidate_audit(phase0_reports / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv")
    _write_candidate_backlog(phase0_docs / "CANDIDATE_RESEARCH_BACKLOG.md")
    output = module.generate_project_status_page(repo)
    old_time = 1_800_000_000
    new_time = old_time + 10
    os.utime(output.output_path, (old_time, old_time))
    os.utime(phase1_reports / "PHASE1_STATUS_SUMMARY.json", (new_time, new_time))

    assert freshness.verify_status_dashboard_freshness(repo, output.output_path) == []


def test_project_status_page_keeps_five_day_soak_pending_when_phase1_acceptance_fails(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    phase0_reports = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "reports"
    phase0_matrix = repo / "xau-usd" / "xauusd-phase0" / "outputs" / "matrix_results"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase0_reports.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    _write_phase1_summary(
        phase1_reports / "PHASE1_STATUS_SUMMARY.json",
        acceptance="FAIL",
        soak={"progress_pct": 90.0, "observed_days": 4.5, "required_days": 5},
    )
    _write_status(phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md", "FAIL")
    _write_status(phase1_reports / "PHASE2_READINESS_REPORT.md", "FAIL")
    _write_phase2_countdown(phase1_reports / "PHASE2_DEMO_COUNTDOWN.json")
    _write_phase2_preflight(phase1_reports / "PHASE2_DEMO_PREFLIGHT.json")
    _write_phase2_experimental_demo_terminal(phase1_reports / "PHASE2_EXPERIMENTAL_DEMO_TERMINAL.json")
    _write_phase2_next_actions(phase1_reports / "PHASE2_DEMO_NEXT_ACTIONS.json")
    _write_phase2_bootstrap(phase1_reports / "PHASE2_VPS_BOOTSTRAP_PACKET.json")
    (phase0_reports / "PHASE0_VERDICT.md").write_text(
        "| breakout_retest | PASS | PASS | PASS | PASS | PASS | PASS |\n",
        encoding="utf-8",
    )
    _write_fixed_notional(phase0_reports / "FIXED_NOTIONAL_REPORT.md")
    _write_measured_cost(phase0_reports / "MEASURED_COST_MODEL.md")
    _write_candidate_audit(phase0_reports / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv")
    _write_trade_ledger(
        phase0_matrix / "breakout_retest" / "cell_3_breakout_retest_capital_com_p95_trades.csv",
        [("2024-01-03 10:00:00+00:00", 1.5)],
    )

    output = module.generate_project_status_page(repo)

    html = output.output_path.read_text(encoding="utf-8")
    assert '<div class="name">Five-day soak</div>' in html
    assert "Wall-clock evidence accumulating: 4.5 of 5 trading days (90%)" in html
    assert '<span class="pill pending">PENDING</span>' in html


def test_status_page_freshness_check_fails_when_html_older_than_summary(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    summary_path = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports" / "PHASE1_STATUS_SUMMARY.json"
    status_path = repo / "status.html"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text("{}", encoding="utf-8")
    status_path.write_text("<html></html>", encoding="utf-8")
    old_time = 1_800_000_000
    new_time = old_time + 10
    os.utime(status_path, (old_time, old_time))
    os.utime(summary_path, (new_time, new_time))

    try:
        module.assert_status_page_current(repo, status_path, summary_path)
    except module.StatusPageFreshnessError as exc:
        assert "older than PHASE1_STATUS_SUMMARY" in str(exc)
    else:
        raise AssertionError("Expected stale status page to fail freshness check")


def test_status_page_write_retries_after_transient_replace_failure(tmp_path: Path, monkeypatch):
    module = _load_module()
    output = tmp_path / "status.html"
    calls = {"count": 0}
    original_replace = type(output).replace

    def flaky_replace(self, target):
        if self.name.startswith(".status.html.") and calls["count"] == 0:
            calls["count"] += 1
            raise OSError("transient write lock")
        return original_replace(self, target)

    monkeypatch.setattr(type(output), "replace", flaky_replace)

    module._write_text_with_retries(output, "<html>ok</html>", attempts=2, sleep_seconds=0)

    assert calls["count"] == 1
    assert output.read_text(encoding="utf-8") == "<html>ok</html>"
    assert not list(tmp_path.glob(".status.html.*.tmp"))


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_project_status_page.py"
    spec = importlib.util.spec_from_file_location("generate_project_status_page", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_project_status_page"] = module
    spec.loader.exec_module(module)
    return module


def _load_script(name: str):
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_status(path: Path, status: str) -> None:
    path.write_text(f"# Report\n\nOverall status: {status}\n", encoding="utf-8")


def _write_phase1_summary(
    path: Path,
    acceptance: str = "PENDING",
    soak: dict[str, float] | None = None,
) -> None:
    soak = soak or {"progress_pct": 8.26, "observed_days": 0.4132, "required_days": 5}
    path.write_text(
        json.dumps(
            {
                "status": {
                    "acceptance": acceptance,
                    "log_verification": "PASS",
                    "runtime_health": "PASS",
                    "soak_analysis": "PASS",
                    "would_signal": "PASS",
                },
                "runtime": {
                    "decision_rows": 56,
                    "latest_row": {
                        "bar_time": "2026.05.22 20:55:00",
                        "dry_run": "true",
                        "trade_permission": "false",
                        "server_time_status": "CLOCK_OK",
                        "risk_state": "NORMAL",
                        "block_reason": "phase1_dry_run_only",
                    },
                },
                "soak": soak,
                "would_signal": {"rows": 10, "clusters": 10},
            }
        ),
        encoding="utf-8",
    )


def _write_phase2_countdown(path: Path, pending_gate_count: int = 10) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "DEMO_NOT_READY",
                "phase2_readiness_status": "PENDING",
                "phase1_acceptance_status": "PENDING",
                "measured_cost_status": "PENDING",
                "paper_mode_authorized": False,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
                "pending_gate_count": pending_gate_count,
                "wait_gates": [
                    {
                        "gate": "Active-market 72-hour soak",
                        "status": "PENDING",
                        "current": 25.67,
                        "required": 72.0,
                        "remaining": 46.33,
                        "unit": "hours",
                    },
                    {
                        "gate": "Measured cost model",
                        "status": "PENDING",
                        "current": 2.0,
                        "required": 5.0,
                        "remaining": 3.0,
                        "unit": "fresh_market_days",
                    },
                ],
                "owner_actions_now": [
                    {
                        "gate": "VPS latency evidence",
                        "status": "PENDING",
                        "action": "After VPS is provisioned, run scripts/capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root.",
                    }
                ],
                "forbidden_until_ready": ["paper-mode implementation", "live capital"],
            }
        ),
        encoding="utf-8",
    )


def _write_phase2_preflight(path: Path, status: str = "PENDING") -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
                "paper_mode_implementation_authorized": False,
                "demo_trading_authorized": False,
                "live_trading_authorized": False,
            }
        ),
        encoding="utf-8",
    )


def _write_phase2_experimental_demo_terminal(
    path: Path,
    status: str = "DEMO_TERMINAL_VERIFIED_QUARANTINE_REQUIRED",
    clean: bool = False,
    active_expert: bool = True,
) -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
                "clean_demo_setup_ready": clean,
                "can_start_experimental_demo_setup": clean,
                "can_start_demo_broker_rehearsal": False,
                "canonical_phase2_authorized": False,
                "live_trading_authorized": False,
                "mt5_runtime_touched_by_script": False,
                "terminal": {
                    "latest_authorization_server": "Capital.ComMena-Demo",
                    "latest_authorization_time": "2026-05-29 01:07:59.258000",
                },
                "active_experts": [
                    {
                        "expert": "GoldMissionEAv5",
                        "symbol": "XAUUSD",
                        "timeframe": "M15",
                        "last_seen": "2026-05-29 01:07:47.801000",
                    }
                ]
                if active_expert
                else [],
                "next_actions": [
                    "Detach or disable active chart experts, or open a clean demo-only profile.",
                    "Regenerate this report before demo broker rehearsal.",
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_phase2_experimental_demo_attachments(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "ATTACHED_TO_DEMO_TERMINAL",
                "run_id": "phase2-experimental-demo-attach-v0.1",
                "attachment_count": 2,
                "terminal": {
                    "terminal_relaunched": True,
                    "profile_backup_dir": "C:\\terminal\\_codex_quarantine\\profile_backups\\default_profile",
                },
                "ea": {
                    "compile_log": "C:\\terminal\\MQL5\\Logs\\compile_Phase2ExperimentalDemoObserver.log",
                    "dry_run_only": True,
                    "broker_action_allowed": False,
                },
                "attachments": [
                    {
                        "candidate": "breakout_retest",
                        "status": "ACCEPTED",
                        "symbol": "XAUUSD",
                        "qualification_source": "primary_xau_matrix_or_candidate_status",
                        "observer_supported": True,
                    },
                    {
                        "candidate": "round_number_retest_v0",
                        "status": "PROVISIONAL",
                        "symbol": "USDJPY",
                        "qualification_source": "round_number_retest_v0_multisymbol_summary.csv:PASS",
                        "observer_supported": True,
                    },
                ],
                "observer_limitations": [
                    "breakout_retest uses the native Phase 1 breakout-retest observer.",
                    "round_number_retest_v0 uses the experimental MQL dry-run observer for signal telemetry only.",
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_phase2_next_actions(
    path: Path,
    status: str = "OWNER_ACTION_AND_WAIT_GATES_PENDING",
    pending_gate_count: int = 10,
    do_now_action: str = "Keep Phase 1 dry-run MT5 and passive spread logging running while wait gates mature.",
) -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
                "phase2_readiness_status": "PENDING",
                "phase2_demo_countdown_status": "DEMO_NOT_READY",
                "pending_gate_count": pending_gate_count,
                "demo_trading_authorized": False,
                "broker_execution_authorized": False,
                "do_now": [
                    {
                        "step": "keep_collectors_running",
                        "status": "PENDING",
                        "action": do_now_action,
                    }
                ],
                "after_vps_is_provisioned": [
                    {
                        "step": "capture_vps_latency",
                        "status": "PENDING",
                        "action": "Run capture_phase2_vps_latency_evidence.ps1 from the Phase 1 root after the VPS exists.",
                    }
                ],
                "earliest_gate_targets": [
                    {
                        "gate": "Active-market 72-hour soak",
                        "status": "PENDING",
                        "current": "30.5",
                        "remaining": "41.5",
                        "unit": "hours",
                        "earliest_target_utc": "2026-05-30T12:00:00Z",
                        "condition": "Assumes no restart, no code-freeze reset, and no unexpected market-data gaps.",
                    }
                ],
                "gate_closure_map": [
                    {
                        "gate": "VPS selection",
                        "status": "PENDING",
                        "category": "OWNER_DECISION",
                        "owner": "Project owner",
                        "why_required": (
                            "Proves the paper/demo environment has an explicit owner-approved host, "
                            "region, cost, backup, monitoring, and recovery plan before any remote runtime work begins."
                        ),
                        "proof_artifact": "C:\\repo\\xau-usd\\xauusd-phase1\\docs\\PHASE2_VPS_SELECTION_MATRIX.md",
                        "closure_action": "Owner selects provider/region/plan from PHASE2_VPS_SELECTION_MATRIX.md.",
                        "pass_condition": "Decision record has no placeholders and PHASE2_VPS_SELECTION_DECISION_CHECK.md is PASS.",
                        "verification_command": (
                            "..\\xauusd-phase0\\.venv\\Scripts\\python.exe "
                            "scripts\\generate_phase2_vps_selection_decision_check.py"
                        ),
                    }
                ],
                "owner_signature_sequence": [
                    {
                        "step": "verify_zero_pending_objective_gates",
                        "status": "NOT_READY_TO_SIGN",
                        "action": "Owner may sign only after every objective gate except Project owner approval is PASS.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_phase2_owner_packet(
    path: Path,
    primary_trial: str = "FXVM Advanced VPS in Dubai, Mumbai, or Singapore",
) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "WAITING_AND_OWNER_ACTION_REQUIRED",
                "paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
                "vps_evidence_workspace": {
                    "status": "PREPARED_PENDING_OWNER_VERIFICATION",
                    "manifest_path": "outputs/reports/vps_evidence_workspace_manifest.json",
                    "items": [
                        {
                            "target": "outputs/reports/vps_ntp_sync.txt",
                            "action": "CREATED",
                            "reason": "Pending evidence template is ready to fill.",
                        }
                    ],
                },
                "vps_selection_recommendation": {
                    "status": "PENDING",
                    "primary_trial": primary_trial,
                    "backup_trial": "ForexVPS.net Core in the lowest-latency available region",
                    "defer": "QuantVPS unless broker latency testing favors US/Chicago",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_phase2_vps_selection_check(
    path: Path,
    status: str = "PENDING",
    next_action: str = "PHASE2_VPS_SELECTION_MATRIX.md status is PENDING; required PASS.",
) -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
                "paper_mode_authorized": False,
                "demo_trading_authorized": False,
                "broker_execution_authorized": False,
                "live_trading_authorized": False,
                "next_action": next_action,
                "checks": [
                    {
                        "check": "matrix_readiness_gate",
                        "status": status,
                        "evidence": next_action,
                    },
                    {
                        "check": "owner_acceptance_boundary",
                        "status": "PENDING" if status != "PASS" else "PASS",
                        "evidence": "Owner acceptance field is not filled yet."
                        if status != "PASS"
                        else "Owner acceptance preserves paper-only/no-live/no-broker-execution boundary.",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_phase2_bootstrap(path: Path, status: str = "WAITING_AND_VPS_BOOTSTRAP_PENDING") -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
                "demo_trading_authorized": False,
                "source_status": {
                    "vps_selection": "PENDING",
                    "vps_latency": "PENDING",
                    "vps_first_day_verification": "PENDING",
                    "project_owner_approval": "PENDING",
                },
                "bootstrap_phases": [
                    {"phase": "Before VPS Purchase", "objective": "Choose the VPS without touching MT5."},
                    {"phase": "On VPS First Login", "objective": "Capture environment and latency evidence."},
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_fixed_notional(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Fixed",
                "",
                "Overall status: PASS",
                "",
                "| Cell | Broker | Cost | Trades | Win % | PF | Avg R | Gross R | Cost R | Net R | Cost % | Flag |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| ALL | ALL | ALL | 66759 | 48.22 | 1.3625 | 0.1888 | 0.5115 | 0.3228 | 0.1888 | 63.0938 | ORANGE |",
            ]
        ),
        encoding="utf-8",
    )


def _write_measured_cost(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Measured Cost",
                "",
                "Overall status: PENDING",
                "",
                "| Observed Rows | Required Rows | Observed Days | Required Days | Source Files |",
                "| --- | --- | --- | --- | --- |",
                "| 5759 | 500 | 2 | 5 | 2 |",
            ]
        ),
        encoding="utf-8",
    )


def _write_phase3_status(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "EXPERIMENTAL_ACTIVE",
                "real_phase2_readiness": "PENDING",
                "assumption": "assumes_phase2_pass_for_design_only",
                "authorized_for_deployment": False,
                "mt5_runtime_touched": False,
                "simulation": {
                    "accepted_events": 12,
                    "rejected_source_rows": 1,
                    "median_proxy_cost_r": 0.12,
                    "median_net_after_proxy_cost_r": 0.39,
                },
                "paper_shadow_experiment": {
                    "status": "SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS",
                    "would_open_count": 8,
                    "would_open_review_count": 2,
                    "blocked_suspend_count": 1,
                    "observer_no_exposure_count": 4,
                    "estimated_monthly_shadow_open_count": 24.0,
                    "mean_shadow_open_net_r": 0.22,
                },
                "shadow_lifecycle_experiment": {
                    "status": "SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY",
                    "synthetic_open_count": 8,
                    "synthetic_win_rate_pct": 50.0,
                    "synthetic_total_net_r": 1.25,
                    "synthetic_max_drawdown_r": -2.75,
                    "risk_lock_counts": {"NORMAL": 8},
                },
                "lifecycle_guard_experiment": {
                    "status": "SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY",
                    "guarded_open_count": 4,
                    "guarded_total_net_r": 0.75,
                    "guarded_max_drawdown_r": -1.25,
                    "net_improvement_r": 2.0,
                    "drawdown_improvement_r": 1.5,
                },
                "demo_rehearsal": {
                    "status": "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY",
                    "rehearsal_event_count": 12,
                    "shadow_open_events": 4,
                    "blocked_events": 3,
                    "can_start_real_demo": False,
                },
                "demo_handoff": {
                    "status": "READY_FOR_REVIEW_WAITING_REAL_GATES",
                    "can_start_demo_now": False,
                    "can_start_real_paper_shadow_branch": False,
                },
            }
        ),
        encoding="utf-8",
    )


def _write_phase3_handoff(
    path: Path,
    status: str = "READY_FOR_REVIEW_WAITING_REAL_GATES",
) -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
                "phase3_repo_complete": True,
                "phase1_acceptance": "PENDING",
                "phase2_readiness": "PENDING",
                "can_start_demo_now": False,
                "can_start_real_paper_shadow_branch": False,
                "demo_authorized": False,
                "paper_mode_authorized": False,
                "broker_action_code_allowed": False,
                "mt5_runtime_touched": False,
                "wait_gates": [
                    {
                        "gate": "Active-market 72-hour soak",
                        "status": "PENDING",
                        "current": 25.67,
                        "required": 72.0,
                        "remaining": 46.33,
                        "unit": "hours",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_family_d2(report_path: Path, manifest_path: Path, reviewer_accepted: bool) -> None:
    report_path.write_text("# Family D2\n\nOverall status: PASS\n", encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "method": "D2_FAMILY_CLUSTERED_V0",
                "reviewer_accepted_method": reviewer_accepted,
                "statistical_pass": True,
                "winner_family": "breakout_retest_family",
            }
        ),
        encoding="utf-8",
    )


def _write_candidate_audit(path: Path) -> None:
    fieldnames = [
        "candidate",
        "decision_scope",
        "frequency_bias_diagnosis",
        "complete_cells",
        "pf_passing_cells",
        "total_trades",
        "median_cell_trades",
        "failed_gates",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "candidate": "breakout_retest",
                "decision_scope": "APPROVED_OR_ACTIVE",
                "frequency_bias_diagnosis": "APPROVED_EDGE_FAMILY",
                "complete_cells": "9",
                "pf_passing_cells": "7",
                "total_trades": "66759",
                "median_cell_trades": "7287",
                "failed_gates": "none",
            }
        )
        writer.writerow(
            {
                "candidate": "trend_pullback",
                "decision_scope": "REJECTED_OR_RESEARCH",
                "frequency_bias_diagnosis": "EDGE_EXPECTANCY_FAILURE",
                "complete_cells": "9",
                "pf_passing_cells": "0",
                "total_trades": "27576",
                "median_cell_trades": "3039",
                "failed_gates": "multi_cell_survival;concentration",
            }
        )


def _write_candidate_backlog(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Candidate Research Backlog",
                "",
                "| # | Candidate | Status | Next Action |",
                "| ---: | --- | --- | --- |",
                "| 3 | `h4_us_session_liquidity_reversal_v0` | REGISTERED_SMOKE_PASS_PENDING_MATRIX | First-pass matrix pending. |",
            ]
        ),
        encoding="utf-8",
    )


def _write_trade_ledger(path: Path, rows: list[tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["expert", "exit_time_utc", "r_multiple"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for exit_time, r_multiple in rows:
            writer.writerow({"expert": path.parent.name, "exit_time_utc": exit_time, "r_multiple": r_multiple})
