from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample_would_signals.csv"


def test_phase3_simulation_filters_unsafe_rows_and_deduplicates_family_events(tmp_path: Path):
    module = _load_script("simulate_phase3_from_would_signals")

    output = module.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")

    assert output.status == "EXPERIMENTAL_COST_SUSPEND_SCENARIO"
    assert output.accepted_events == 7
    assert output.rejected_source_rows == 6
    summary = json.loads(output.summary_path.read_text(encoding="utf-8"))
    assert summary["raw_observer_event_count"] == 7
    assert summary["family_unique_event_count"] == 3
    assert summary["observer_duplicate_count"] == 1
    assert summary["observer_conflict_count"] == 2
    assert summary["primary_stream_allowed_count"] == 3
    assert summary["gross_expectancy_r_source"] == "fixed_notional_phase0_baseline"
    assert summary["baseline_assumed_cost_r"] == 0.3228
    assert summary["baseline_net_expectancy_r"] == 0.1888
    assert "median_net_delta_vs_assumed_baseline_r" in summary
    assert summary["kill_rule_counts"] == {
        "COST_WATCH": 1,
        "NORMAL": 5,
        "SUSPEND_FAMILY": 1,
    }
    with output.ledger_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    roles = {row["source_cluster_id"]: row for row in rows}
    assert roles["WS100"]["family_event_role"] == "PRIMARY_EXECUTION_CANDIDATE"
    assert roles["WS100"]["primary_stream_allowed"] == "true"
    assert roles["WS100"]["gross_expectancy_r_source"] == "fixed_notional_phase0_baseline"
    assert roles["WS100"]["baseline_assumed_cost_r"] == "0.3228"
    assert roles["WS100"]["baseline_net_expectancy_r"] == "0.1888"
    assert roles["WS100"]["proxy_cost_r"] == roles["WS100"]["measured_cost_r_proxy"]
    assert roles["WS100"]["net_after_proxy_from_gross_r"] == roles["WS100"]["net_expectancy_r_after_proxy_cost"]
    assert "net_delta_vs_assumed_baseline_r" in roles["WS100"]
    assert roles["WS101"]["family_event_role"] == "OBSERVER_DUPLICATE"
    assert roles["WS101"]["primary_stream_allowed"] == "false"
    assert roles["WS104"]["family_event_role"] == "OBSERVER_CONFLICT"
    assert roles["WS105"]["family_event_role"] == "OBSERVER_CONFLICT"
    assert roles["WS106"]["family_event_role"] == "OBSERVER_ONLY_NO_PRIMARY"
    assert roles["WS102"]["kill_rule_state"] == "COST_WATCH"
    assert roles["WS103"]["kill_rule_state"] == "SUSPEND_FAMILY"
    assert roles["WS100"]["cost_mode"] == "entry_exit_proxy"
    assert "This report has no authority over Phase 2 readiness." in output.report_path.read_text(encoding="utf-8")


def test_phase3_cost_modes_are_explicit(tmp_path: Path):
    module = _load_script("simulate_phase3_from_would_signals")

    entry_only = module.simulate_phase3_from_would_signals(
        FIXTURE,
        tmp_path / "entry",
        cost_mode="entry_only_proxy",
    )
    stress = module.simulate_phase3_from_would_signals(
        FIXTURE,
        tmp_path / "stress",
        cost_mode="stress_2x_p95_proxy",
    )

    entry_summary = json.loads(entry_only.summary_path.read_text(encoding="utf-8"))
    stress_summary = json.loads(stress.summary_path.read_text(encoding="utf-8"))
    assert entry_summary["cost_mode"] == "entry_only_proxy"
    assert stress_summary["cost_mode"] == "stress_2x_p95_proxy"
    assert stress_summary["kill_rule_counts"]["SUSPEND_FAMILY"] > entry_summary["kill_rule_counts"]["SUSPEND_FAMILY"]


def test_non_primary_observers_cannot_be_primary_stream_allowed(tmp_path: Path):
    module = _load_script("simulate_phase3_from_would_signals")

    output = module.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")

    with output.ledger_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row["observer"] != "breakout_retest":
            assert row["primary_stream_allowed"] == "false"
            assert row["family_event_role"] != "PRIMARY_EXECUTION_CANDIDATE"


def test_p95_proxy_can_suspend_without_mutating_real_phase2_readiness(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulator.simulate_phase3_from_would_signals(
        FIXTURE,
        phase3 / "outputs" / "reports",
        cost_mode="p95_fresh_proxy",
    )
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(json.dumps({"runtime": {"latest_row": {}}}), encoding="utf-8")
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    simulation = json.loads((phase3 / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_SIMULATION.json").read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert simulation["cost_mode"] == "p95_fresh_proxy"
    assert simulation["kill_rule_counts"]["SUSPEND_FAMILY"] > 0
    assert status["real_phase2_readiness"] == "PENDING"
    assert status["authorized_for_deployment"] is False


def test_phase3_cost_mode_comparison_runs_all_modes(tmp_path: Path):
    module = _load_script("generate_phase3_cost_mode_comparison")

    path = module.generate_cost_mode_comparison(FIXTURE, tmp_path / "reports")

    comparison = json.loads(path.read_text(encoding="utf-8"))
    rows = comparison["rows"]
    modes = {row["cost_mode"] for row in rows}
    assert modes == {"entry_only_proxy", "entry_exit_proxy", "p95_fresh_proxy", "stress_2x_p95_proxy"}
    by_mode = {row["cost_mode"]: row for row in rows}
    assert by_mode["stress_2x_p95_proxy"]["suspend_family_count"] >= by_mode["entry_only_proxy"]["suspend_family_count"]
    assert by_mode["entry_exit_proxy"]["gross_expectancy_r_source"] == "fixed_notional_phase0_baseline"
    assert by_mode["entry_exit_proxy"]["baseline_assumed_cost_r"] == 0.3228
    assert "median_net_delta_vs_assumed_baseline_r" in by_mode["entry_exit_proxy"]
    assert (tmp_path / "reports" / "PHASE3_COST_MODE_COMPARISON.md").exists()
    assert (tmp_path / "reports" / "PHASE3_COST_MODE_COMPARISON.csv").exists()


def test_phase3_cost_gate_review_reports_thresholds_buckets_and_kill_states(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    module = _load_script("generate_phase3_cost_gate_review")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")

    path = module.generate_cost_gate_review(simulation.ledger_path, tmp_path / "reports")

    review = json.loads(path.read_text(encoding="utf-8"))
    assert review["status"] == "REVIEW_READY"
    assert review["raw_ledger_rows"] == 7
    assert review["family_unique_events"] == 5
    assert review["review_annotation_options"] == [
        "COST_ISSUE",
        "TIGHT_STOP_ISSUE",
        "TIMING_ISSUE",
        "DUPLICATED_OBSERVER_ISSUE",
        "UNKNOWN",
    ]
    thresholds = {row["threshold_r"]: row for row in review["threshold_rows"]}
    assert thresholds[0.2]["family_unique_events"] >= thresholds[0.35]["family_unique_events"]
    assert len(review["stop_distance_bucket_rows"]) == 4
    assert len(review["spread_regime_bucket_rows"]) == 3
    kill_rows = {row["bucket"]: row for row in review["kill_state_rows"]}
    assert kill_rows["SUSPEND_FAMILY"]["raw_rows"] == 1
    report = (tmp_path / "reports" / "PHASE3_COST_GATE_REVIEW.md").read_text(encoding="utf-8")
    assert "Cost-In-R Gate Prototypes" in report
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def test_phase3_paper_shadow_experiment_models_lifecycle_without_demo_authority(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    module = _load_script("generate_phase3_paper_shadow_experiment")
    repo = tmp_path / "repo"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")

    path = module.generate_paper_shadow_experiment(simulation.ledger_path, tmp_path / "reports", repo)

    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["status"] == "SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS"
    assert summary["real_phase2_readiness"] == "PENDING"
    assert summary["demo_authorized"] is False
    assert summary["mt5_runtime_touched"] is False
    assert summary["broker_action_code_allowed"] is False
    assert summary["source_ledger_rows"] == 7
    assert summary["primary_stream_rows"] == 3
    assert summary["would_open_count"] == 2
    assert summary["would_open_review_count"] == 1
    assert summary["blocked_suspend_count"] == 1
    assert summary["observer_no_exposure_count"] == 4
    rows = list(csv.DictReader((tmp_path / "reports" / "PHASE3_PAPER_SHADOW_LEDGER.csv").open("r", encoding="utf-8")))
    by_cluster = {row["source_cluster_id"]: row for row in rows}
    assert by_cluster["WS100"]["paper_shadow_action"] == "WOULD_PAPER_SHADOW_OPEN"
    assert by_cluster["WS102"]["paper_shadow_action"] == "WOULD_PAPER_SHADOW_OPEN_REVIEW"
    assert by_cluster["WS103"]["paper_shadow_action"] == "BLOCKED_SUSPEND_FAMILY"
    assert by_cluster["WS101"]["paper_shadow_action"] == "NO_EXPOSURE_DUPLICATE_IGNORED"
    assert by_cluster["WS104"]["paper_shadow_action"] == "NO_EXPOSURE_CONFLICT_REVIEW"
    assert by_cluster["WS100"]["demo_authorized"] == "false"
    report = (tmp_path / "reports" / "PHASE3_PAPER_SHADOW_SUMMARY.md").read_text(encoding="utf-8")
    assert "Paper-Shadow Side Experiment" in report
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def test_phase3_shadow_lifecycle_experiment_models_synthetic_closes(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    shadow_module = _load_script("generate_phase3_paper_shadow_experiment")
    lifecycle_module = _load_script("generate_phase3_shadow_lifecycle_experiment")
    repo = tmp_path / "repo"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")
    shadow_module.generate_paper_shadow_experiment(simulation.ledger_path, tmp_path / "reports", repo)

    path = lifecycle_module.generate_shadow_lifecycle_experiment(
        tmp_path / "reports" / "PHASE3_PAPER_SHADOW_LEDGER.csv",
        tmp_path / "reports",
    )

    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["status"] == "SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY"
    assert summary["demo_authorized"] is False
    assert summary["mt5_runtime_touched"] is False
    assert summary["broker_action_code_allowed"] is False
    assert summary["source_shadow_rows"] == 7
    assert summary["synthetic_open_count"] == 2
    assert summary["synthetic_close_count"] == 2
    assert summary["no_exposure_review_only_count"] == 5
    assert "cost_watch_review_exit" in summary["close_reason_counts"]
    rows = list(csv.DictReader((tmp_path / "reports" / "PHASE3_SHADOW_LIFECYCLE_LEDGER.csv").open("r", encoding="utf-8")))
    by_cluster = {row["source_cluster_id"]: row for row in rows}
    assert by_cluster["WS100"]["synthetic_open_state"] == "SYNTHETIC_OPENED"
    assert by_cluster["WS102"]["synthetic_close_reason"] == "cost_watch_review_exit"
    assert by_cluster["WS103"]["lifecycle_stage"] == "NO_EXPOSURE_REVIEW_ONLY"
    assert by_cluster["WS100"]["demo_authorized"] == "false"
    report = (tmp_path / "reports" / "PHASE3_SHADOW_LIFECYCLE_SUMMARY.md").read_text(encoding="utf-8")
    assert "Shadow Lifecycle Side Experiment" in report
    assert "not a backtest and not paper trading" in report
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def test_phase3_lifecycle_guard_blocks_cost_and_risk_exposure(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    shadow_module = _load_script("generate_phase3_paper_shadow_experiment")
    lifecycle_module = _load_script("generate_phase3_shadow_lifecycle_experiment")
    guard_module = _load_script("generate_phase3_lifecycle_guard_experiment")
    repo = tmp_path / "repo"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")
    shadow_module.generate_paper_shadow_experiment(simulation.ledger_path, tmp_path / "reports", repo)
    lifecycle_module.generate_shadow_lifecycle_experiment(
        tmp_path / "reports" / "PHASE3_PAPER_SHADOW_LEDGER.csv",
        tmp_path / "reports",
    )

    path = guard_module.generate_lifecycle_guard_experiment(
        tmp_path / "reports" / "PHASE3_SHADOW_LIFECYCLE_LEDGER.csv",
        tmp_path / "reports",
    )

    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["status"] == "SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY"
    assert summary["demo_authorized"] is False
    assert summary["mt5_runtime_touched"] is False
    assert summary["broker_action_code_allowed"] is False
    assert summary["baseline_open_count"] == 2
    assert summary["guarded_open_count"] == 1
    assert summary["blocked_count"] == 1
    assert summary["guard_block_reason_counts"]["cost_watch_requires_review_before_exposure"] == 1
    assert summary["guarded_total_net_r"] > summary["baseline_total_net_r"]
    rows = list(csv.DictReader((tmp_path / "reports" / "PHASE3_LIFECYCLE_GUARD_LEDGER.csv").open("r", encoding="utf-8")))
    by_cluster = {row["source_cluster_id"]: row for row in rows}
    assert by_cluster["WS100"]["guard_decision"] == "GUARDED_SYNTHETIC_OPEN"
    assert by_cluster["WS102"]["guard_decision"] == "BLOCKED_COST_WATCH"
    assert by_cluster["WS103"]["guard_decision"] == "NO_EXPOSURE_REVIEW_ONLY"
    report = (tmp_path / "reports" / "PHASE3_LIFECYCLE_GUARD_SUMMARY.md").read_text(encoding="utf-8")
    assert "Guarded Lifecycle Side Experiment" in report
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def test_phase3_demo_rehearsal_package_preserves_non_deployment_boundary(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    shadow_module = _load_script("generate_phase3_paper_shadow_experiment")
    lifecycle_module = _load_script("generate_phase3_shadow_lifecycle_experiment")
    guard_module = _load_script("generate_phase3_lifecycle_guard_experiment")
    rehearsal_module = _load_script("generate_phase3_demo_rehearsal_package")
    repo = tmp_path / "repo"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")
    shadow_module.generate_paper_shadow_experiment(simulation.ledger_path, tmp_path / "reports", repo)
    lifecycle_module.generate_shadow_lifecycle_experiment(
        tmp_path / "reports" / "PHASE3_PAPER_SHADOW_LEDGER.csv",
        tmp_path / "reports",
    )
    guard_module.generate_lifecycle_guard_experiment(
        tmp_path / "reports" / "PHASE3_SHADOW_LIFECYCLE_LEDGER.csv",
        tmp_path / "reports",
    )

    path = rehearsal_module.generate_demo_rehearsal_package(
        tmp_path / "reports" / "PHASE3_LIFECYCLE_GUARD_LEDGER.csv",
        tmp_path / "reports" / "PHASE3_LIFECYCLE_GUARD_SUMMARY.json",
        tmp_path / "reports",
        repo,
    )

    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["status"] == "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY"
    assert summary["demo_authorized"] is False
    assert summary["can_start_real_demo"] is False
    assert summary["mt5_runtime_touched"] is False
    assert summary["broker_action_code_allowed"] is False
    assert summary["real_phase2_readiness"] == "PENDING"
    assert summary["shadow_open_events"] == 1
    assert summary["shadow_close_events"] == 1
    assert summary["blocked_events"] == 1
    rows = list(csv.DictReader((tmp_path / "reports" / "PHASE3_DEMO_REHEARSAL_LEDGER.csv").open("r", encoding="utf-8")))
    events_by_cluster = {}
    for row in rows:
        events_by_cluster.setdefault(row["source_cluster_id"], []).append(row["rehearsal_event_type"])
        assert row["demo_authorized"] == "false"
        assert row["can_start_real_demo"] == "false"
    assert events_by_cluster["WS100"] == ["REHEARSAL_SHADOW_OPEN", "REHEARSAL_SHADOW_CLOSE"]
    assert events_by_cluster["WS102"] == ["REHEARSAL_BLOCKED_COST"]
    assert events_by_cluster["WS103"] == ["REHEARSAL_NO_EXPOSURE"]
    report = (tmp_path / "reports" / "PHASE3_DEMO_REHEARSAL_CHECKLIST.md").read_text(encoding="utf-8")
    assert "Demo Rehearsal Checklist" in report
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def test_phase3_to_demo_handoff_preserves_demo_boundary_and_lists_gates(tmp_path: Path):
    module = _load_script("generate_phase3_to_demo_handoff")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    (reports / "PHASE3_EXPERIMENTAL_STATUS.json").write_text(
        json.dumps({"status": "EXPERIMENTAL_COST_SUSPEND_SCENARIO"}),
        encoding="utf-8",
    )
    (reports / "PHASE3_COMPLETION_AUDIT.json").write_text(
        json.dumps({"status": "REPO_SIDE_COMPLETE_WAITING_REAL_GATES", "phase3_repo_complete": True}),
        encoding="utf-8",
    )
    (reports / "PHASE3_DEMO_REHEARSAL_PLAN.json").write_text(
        json.dumps({"can_start_real_demo": False}),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_DEMO_COUNTDOWN.json").write_text(
        json.dumps(
            {
                "wait_gates": [
                    {
                        "gate": "Active-market 72-hour soak",
                        "status": "PENDING",
                        "current": 28.5,
                        "required": 72.0,
                        "remaining": 43.5,
                        "unit": "hours",
                    }
                ],
                "owner_actions_now": [
                    {
                        "gate": "VPS selection",
                        "status": "PENDING",
                        "action": "Select VPS.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE2_OWNER_ACTION_PACKET.json").write_text(
        json.dumps(
            {
                "owner_approval_readiness": {
                    "status": "NOT_READY_TO_SIGN",
                    "pending_objective_gate_count": 1,
                    "pending_objective_gates": [
                        {
                            "gate": "Active-market 72-hour soak",
                            "status": "PENDING",
                            "evidence": "Need more active-market hours.",
                        }
                    ],
                    "signing_rule": "Owner may sign only after every objective gate except Project owner approval is PASS.",
                }
            }
        ),
        encoding="utf-8",
    )

    path = module.generate_phase3_to_demo_handoff(phase3, repo)

    handoff = json.loads(path.read_text(encoding="utf-8"))
    assert handoff["status"] == "READY_FOR_REVIEW_WAITING_REAL_GATES"
    assert handoff["can_start_demo_now"] is False
    assert handoff["demo_authorized"] is False
    assert handoff["broker_action_code_allowed"] is False
    assert handoff["wait_gates"][0]["gate"] == "Active-market 72-hour soak"
    assert handoff["owner_actions"][0]["gate"] == "VPS selection"
    assert handoff["owner_approval_readiness"]["status"] == "NOT_READY_TO_SIGN"
    assert handoff["owner_approval_readiness"]["pending_objective_gate_count"] == 1
    report = (reports / "PHASE3_TO_DEMO_HANDOFF.md").read_text(encoding="utf-8")
    assert "Phase 3 To Demo Handoff" in report
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report
    assert "Owner Approval Readiness" in report
    assert "NOT_READY_TO_SIGN" in report


def test_phase3_status_preserves_real_phase2_pending_and_reports_safety(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    safety_module = _load_script("audit_phase3_experimental_safety")
    suspend_module = _load_script("analyze_phase3_suspend_family")
    suspend_decision_module = _load_script("generate_phase3_suspend_family_decision")
    comparison_module = _load_script("generate_phase3_cost_mode_comparison")
    cost_gate_module = _load_script("generate_phase3_cost_gate_review")
    dedup_module = _load_script("generate_phase3_family_dedup_audit")
    shadow_module = _load_script("generate_phase3_paper_shadow_experiment")
    lifecycle_module = _load_script("generate_phase3_shadow_lifecycle_experiment")
    guard_module = _load_script("generate_phase3_lifecycle_guard_experiment")
    rehearsal_module = _load_script("generate_phase3_demo_rehearsal_package")
    handoff_module = _load_script("generate_phase3_to_demo_handoff")
    manifest_module = _load_script("generate_phase3_experimental_manifest")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, phase3 / "outputs" / "reports")
    safety_module.generate_phase3_safety_report(ROOT, phase3 / "outputs" / "reports")
    suspend_module.analyze_suspend_family(simulation.ledger_path, phase3 / "outputs" / "reports")
    suspend_decision_module.generate_suspend_family_decision(
        phase3 / "outputs" / "reports" / "PHASE3_SUSPEND_FAMILY_ROWS.csv",
        phase3 / "outputs" / "reports",
    )
    comparison_module.generate_cost_mode_comparison(FIXTURE, phase3 / "outputs" / "reports")
    cost_gate_module.generate_cost_gate_review(simulation.ledger_path, phase3 / "outputs" / "reports")
    dedup_module.generate_family_dedup_audit(FIXTURE, phase3 / "outputs" / "reports")
    shadow_module.generate_paper_shadow_experiment(simulation.ledger_path, phase3 / "outputs" / "reports", repo)
    lifecycle_module.generate_shadow_lifecycle_experiment(
        phase3 / "outputs" / "reports" / "PHASE3_PAPER_SHADOW_LEDGER.csv",
        phase3 / "outputs" / "reports",
    )
    guard_module.generate_lifecycle_guard_experiment(
        phase3 / "outputs" / "reports" / "PHASE3_SHADOW_LIFECYCLE_LEDGER.csv",
        phase3 / "outputs" / "reports",
    )
    rehearsal_module.generate_demo_rehearsal_package(
        phase3 / "outputs" / "reports" / "PHASE3_LIFECYCLE_GUARD_LEDGER.csv",
        phase3 / "outputs" / "reports" / "PHASE3_LIFECYCLE_GUARD_SUMMARY.json",
        phase3 / "outputs" / "reports",
        repo,
    )
    manifest_module.generate_phase3_experimental_manifest(phase3, repo)
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "latest_row": {
                        "bar_time": "2026.05.27 19:20:00",
                        "run_id": "phase1-dry-run-v0.7",
                        "dry_run": "true",
                        "trade_permission": "false",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["status"] == "EXPERIMENTAL_COST_SUSPEND_SCENARIO"
    assert status["real_phase2_readiness"] == "PENDING"
    assert status["authorized_for_deployment"] is False
    assert status["broker_action_code_allowed"] is False
    assert status["mt5_runtime_touched"] is False
    assert status["safety"]["status"] == "PASS"
    assert status["suspend_family_review"]["status"] == "REVIEW_READY"
    assert status["suspend_family_review"]["suspend_unique_family_events"] == 1
    assert status["suspend_family_decision"]["status"] == "REVIEW_READY_KEEP_SUSPENDED"
    assert status["suspend_family_decision"]["keep_suspended_primary_rows"] == 1
    assert status["cost_mode_comparison"]["median_net_after_proxy_by_mode"]["entry_exit_proxy"] is not None
    assert status["cost_mode_comparison"]["median_net_after_proxy_by_mode"]["p95_fresh_proxy"] is not None
    assert status["cost_mode_comparison"]["median_net_after_proxy_by_mode"]["stress_2x_p95_proxy"] is not None
    assert status["cost_mode_comparison"]["suspend_family_count_by_mode"]["stress_2x_p95_proxy"] > 0
    assert status["cost_gate_review"]["status"] == "REVIEW_READY"
    assert status["cost_gate_review"]["threshold_count"] == 4
    assert status["paper_shadow_experiment"]["status"] == "SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS"
    assert status["paper_shadow_experiment"]["would_open_count"] == 2
    assert status["paper_shadow_experiment"]["demo_authorized"] is False
    assert status["shadow_lifecycle_experiment"]["status"] == "SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY"
    assert status["shadow_lifecycle_experiment"]["synthetic_open_count"] == 2
    assert status["shadow_lifecycle_experiment"]["demo_authorized"] is False
    assert status["lifecycle_guard_experiment"]["status"] == "SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY"
    assert status["lifecycle_guard_experiment"]["guarded_open_count"] == 1
    assert status["lifecycle_guard_experiment"]["demo_authorized"] is False
    assert status["demo_rehearsal"]["status"] == "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY"
    assert status["demo_rehearsal"]["shadow_open_events"] == 1
    assert status["demo_rehearsal"]["can_start_real_demo"] is False
    assert status["demo_rehearsal"]["demo_authorized"] is False
    assert status["manifest"]["status"] == "PENDING"
    assert status["owner_approval_flow"] == "excluded_from_real_phase2_phase3_approval_flow"
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in (
        phase3 / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_STATUS.md"
    ).read_text(encoding="utf-8")


def test_phase3_status_becomes_boundary_fail_if_safety_fails(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    reports = phase3 / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulator.simulate_phase3_from_would_signals(FIXTURE, reports)
    (reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json").write_text(
        json.dumps({"status": "FAIL", "findings_count": 1}),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(json.dumps({"runtime": {"latest_row": {}}}), encoding="utf-8")
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["status"] == "EXPERIMENTAL_BOUNDARY_FAIL"
    assert status["real_phase2_readiness"] == "PENDING"


def test_phase3_status_cannot_set_authorized_for_deployment_true(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulator.simulate_phase3_from_would_signals(FIXTURE, phase3 / "outputs" / "reports")
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(json.dumps({"runtime": {"latest_row": {}}}), encoding="utf-8")
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PASS\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PASS\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["authorized_for_deployment"] is False
    assert status["broker_action_code_allowed"] is False
    assert status["mt5_runtime_touched"] is False
    assert status["owner_approval_flow"] == "excluded_from_real_phase2_phase3_approval_flow"


def test_phase3_safety_audit_passes_and_report_is_generated(tmp_path: Path):
    module = _load_script("audit_phase3_experimental_safety")

    findings = module.audit_phase3_tree(ROOT)
    output = module.generate_phase3_safety_report(ROOT, tmp_path / "reports")

    assert findings == []
    assert output.status == "PASS"
    assert output.findings_count == 0
    assert output.report_path.exists()
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in output.report_path.read_text(
        encoding="utf-8"
    )


def test_phase3_safety_cli_supports_isolated_output_dir(tmp_path: Path):
    output_dir = tmp_path / "ci_synthetic" / "reports"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_phase3_experimental_safety.py"),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (output_dir / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.md").exists()
    assert (output_dir / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json").exists()


def test_phase3_ci_workflow_keeps_synthetic_reports_isolated():
    workflow = (ROOT.parents[1] / ".github" / "workflows" / "phase3_experimental.yml").read_text(encoding="utf-8")

    assert "outputs/ci_synthetic/reports" in workflow
    assert "outputs/ci_synthetic/safety_boundary" in workflow
    assert "not_real_review_evidence=true" in workflow
    assert "simulate_phase3_from_would_signals.py --input-csv \"$FIXTURE\" --output-dir \"$CI_SYNTH\"" in workflow
    assert "audit_phase3_experimental_safety.py --output-dir \"$CI_SYNTH\"" in workflow
    assert "verify_phase3_experimental_artifacts.py --require-git-tracked --require-clean-release-snapshot" in workflow
    assert "generate_phase3_experimental_manifest.py" not in workflow
    assert "generate_project_status_page.py" not in workflow


def test_phase3_safety_audit_detects_forbidden_broker_action_reference(tmp_path: Path):
    module = _load_script("audit_phase3_experimental_safety")
    root = tmp_path / "xauusd-phase3-experimental"
    root.mkdir()
    forbidden = "Order" + "Send"
    (root / "unsafe.py").write_text(f"def unsafe():\n    return '{forbidden}'\n", encoding="utf-8")

    output = module.generate_phase3_safety_report(root)

    assert output.status == "FAIL"
    assert output.findings_count == 1
    summary = json.loads(output.summary_path.read_text(encoding="utf-8"))
    assert summary["findings"][0]["term"] == forbidden


def test_phase3_source_safety_predicate_rejects_each_unsafe_case():
    module = _load_script("simulate_phase3_from_would_signals")
    rows = _read_csv(FIXTURE)
    by_cluster = {row["cluster_id"]: row for row in rows}

    assert module._source_row_is_safe(by_cluster["WS100"]) is True
    assert module._source_row_is_safe(by_cluster["WS107"]) is False  # dry_run=false
    assert module._source_row_is_safe(by_cluster["WS108"]) is False  # trade_permission=true
    assert module._source_row_is_safe(by_cluster["WS109"]) is False  # execution_state != EXECUTION_OK
    assert module._source_row_is_safe(by_cluster["WS110"]) is False  # risk_state != NORMAL
    assert module._source_row_is_safe(by_cluster["WS111"]) is False  # server_time_status != CLOCK_OK
    assert module._source_row_is_safe(by_cluster["WS112"]) is False  # disallowed observer


def test_phase3_suspend_family_review_summarizes_primary_vs_duplicate_rows(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    suspend_module = _load_script("analyze_phase3_suspend_family")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")

    review_path = suspend_module.analyze_suspend_family(simulation.ledger_path, tmp_path / "reports")

    review = json.loads(review_path.read_text(encoding="utf-8"))
    assert review["status"] == "REVIEW_READY"
    assert review["suspend_raw_rows"] == 1
    assert review["suspend_unique_family_events"] == 1
    assert review["suspend_primary_rows"] == 1
    assert review["suspend_duplicate_rows"] == 0
    assert review["gross_expectancy_r_source"] == "fixed_notional_phase0_baseline"
    assert review["baseline_assumed_cost_r"] == 0.3228
    assert review["baseline_net_expectancy_r"] == 0.1888
    assert "median_suspend_net_delta_vs_assumed_baseline_r" in review
    assert review["diagnosis_counts"] == {"tight_stop_cost_dominates": 1}
    assert review["suggested_annotation_counts"] == {"TIGHT_STOP_ISSUE": 1}
    rows = list(csv.DictReader((tmp_path / "reports" / "PHASE3_SUSPEND_FAMILY_ROWS.csv").open("r", encoding="utf-8")))
    assert rows[0]["suggested_reviewer_annotation"] == "TIGHT_STOP_ISSUE"
    assert "manual_reviewer_annotation" in rows[0]
    report = (tmp_path / "reports" / "PHASE3_SUSPEND_FAMILY_REVIEW.md").read_text(encoding="utf-8")
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def test_phase3_suspend_family_decision_keeps_primary_rows_suspended(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    suspend_module = _load_script("analyze_phase3_suspend_family")
    decision_module = _load_script("generate_phase3_suspend_family_decision")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")
    suspend_module.analyze_suspend_family(simulation.ledger_path, tmp_path / "reports")

    path = decision_module.generate_suspend_family_decision(
        tmp_path / "reports" / "PHASE3_SUSPEND_FAMILY_ROWS.csv",
        tmp_path / "reports",
    )

    decision = json.loads(path.read_text(encoding="utf-8"))
    assert decision["status"] == "REVIEW_READY_KEEP_SUSPENDED"
    assert decision["primary_suspend_rows"] == 1
    assert decision["codex_review_decision_counts"] == {"KEEP_SUSPENDED": 1}
    assert decision["decision_rows"][0]["future_rule"] == "REQUIRE_TIGHT_STOP_COST_BLOCK"
    report = (tmp_path / "reports" / "PHASE3_SUSPEND_FAMILY_DECISION.md").read_text(encoding="utf-8")
    assert "KEEP_SUSPENDED" in report
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def test_phase3_review_bundle_includes_key_docs_and_reports(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    safety_module = _load_script("audit_phase3_experimental_safety")
    suspend_module = _load_script("analyze_phase3_suspend_family")
    decision_module = _load_script("generate_phase3_suspend_family_decision")
    comparison_module = _load_script("generate_phase3_cost_mode_comparison")
    cost_gate_module = _load_script("generate_phase3_cost_gate_review")
    dedup_module = _load_script("generate_phase3_family_dedup_audit")
    shadow_module = _load_script("generate_phase3_paper_shadow_experiment")
    lifecycle_module = _load_script("generate_phase3_shadow_lifecycle_experiment")
    guard_module = _load_script("generate_phase3_lifecycle_guard_experiment")
    rehearsal_module = _load_script("generate_phase3_demo_rehearsal_package")
    handoff_module = _load_script("generate_phase3_to_demo_handoff")
    manifest_module = _load_script("generate_phase3_experimental_manifest")
    status_module = _load_script("generate_phase3_experimental_status")
    completion_module = _load_script("generate_phase3_completion_audit")
    bundle_module = _load_script("generate_phase3_review_bundle")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    (phase3 / "docs").mkdir(parents=True)
    for name in [
        "PHASE3_EXPERIMENTAL_SCOPE.md",
        "PHASE3_EXPERIMENTAL_FREEZE.md",
        "PHASE3_EXECUTION_READINESS_DESIGN.md",
        "PHASE3_PROMOTION_ROLLBACK_CRITERIA.md",
        "PHASE3_OBSERVER_CONFLICT_PLAYBOOK.md",
        "PHASE3_REAL_IMPLEMENTATION_PROMPT.md",
    ]:
        (phase3 / "docs" / name).write_text("This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.\n", encoding="utf-8")
    (phase3 / "README.md").write_text("This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.\n", encoding="utf-8")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, phase3 / "outputs" / "reports")
    safety_module.generate_phase3_safety_report(ROOT, phase3 / "outputs" / "reports")
    suspend_module.analyze_suspend_family(simulation.ledger_path, phase3 / "outputs" / "reports")
    decision_module.generate_suspend_family_decision(phase3 / "outputs" / "reports" / "PHASE3_SUSPEND_FAMILY_ROWS.csv", phase3 / "outputs" / "reports")
    comparison_module.generate_cost_mode_comparison(FIXTURE, phase3 / "outputs" / "reports")
    cost_gate_module.generate_cost_gate_review(simulation.ledger_path, phase3 / "outputs" / "reports")
    dedup_module.generate_family_dedup_audit(FIXTURE, phase3 / "outputs" / "reports")
    shadow_module.generate_paper_shadow_experiment(simulation.ledger_path, phase3 / "outputs" / "reports", repo)
    lifecycle_module.generate_shadow_lifecycle_experiment(
        phase3 / "outputs" / "reports" / "PHASE3_PAPER_SHADOW_LEDGER.csv",
        phase3 / "outputs" / "reports",
    )
    guard_module.generate_lifecycle_guard_experiment(
        phase3 / "outputs" / "reports" / "PHASE3_SHADOW_LIFECYCLE_LEDGER.csv",
        phase3 / "outputs" / "reports",
    )
    rehearsal_module.generate_demo_rehearsal_package(
        phase3 / "outputs" / "reports" / "PHASE3_LIFECYCLE_GUARD_LEDGER.csv",
        phase3 / "outputs" / "reports" / "PHASE3_LIFECYCLE_GUARD_SUMMARY.json",
        phase3 / "outputs" / "reports",
        repo,
    )
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(json.dumps({"runtime": {"latest_row": {}}}), encoding="utf-8")
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_DEMO_COUNTDOWN.json").write_text(
        json.dumps({"wait_gates": [], "owner_actions_now": []}),
        encoding="utf-8",
    )
    manifest_module.generate_phase3_experimental_manifest(phase3, repo)
    status_module.generate_phase3_experimental_status(phase3, repo)
    completion_module.generate_phase3_completion_audit(phase3, repo)
    handoff_module.generate_phase3_to_demo_handoff(phase3, repo)
    manifest_module.generate_phase3_experimental_manifest(phase3, repo)
    status_module.generate_phase3_experimental_status(phase3, repo)
    completion_module.generate_phase3_completion_audit(phase3, repo)
    status_module.generate_phase3_experimental_status(phase3, repo)

    bundle_path = bundle_module.generate_phase3_review_bundle(phase3)

    assert bundle_path.exists()
    latest = phase3 / "outputs" / "review_bundles" / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip"
    latest_manifest = phase3 / "outputs" / "review_bundles" / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST_manifest.json"
    assert latest.exists()
    manifest = json.loads(latest_manifest.read_text(encoding="utf-8"))
    assert manifest["status"] == "PASS"
    assert any(item["path"] == "outputs/reports/PHASE3_SUSPEND_FAMILY_DECISION.md" for item in manifest["files"])
    assert any(item["path"] == "outputs/reports/PHASE3_COMPLETION_AUDIT.md" for item in manifest["files"])
    assert any(item["path"] == "outputs/reports/PHASE3_PAPER_SHADOW_SUMMARY.md" for item in manifest["files"])
    assert any(item["path"] == "outputs/reports/PHASE3_SHADOW_LIFECYCLE_SUMMARY.md" for item in manifest["files"])
    assert any(item["path"] == "outputs/reports/PHASE3_LIFECYCLE_GUARD_SUMMARY.md" for item in manifest["files"])
    assert any(item["path"] == "outputs/reports/PHASE3_DEMO_REHEARSAL_CHECKLIST.md" for item in manifest["files"])
    assert any(item["path"] == "outputs/reports/PHASE3_TO_DEMO_HANDOFF.md" for item in manifest["files"])


def test_phase3_completion_audit_reports_repo_complete_but_demo_blocked(tmp_path: Path):
    module = _load_script("generate_phase3_completion_audit")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    docs = phase3 / "docs"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    bundle_dir = phase3 / "outputs" / "review_bundles"
    reports.mkdir(parents=True)
    docs.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    bundle_dir.mkdir(parents=True)
    for name in [
        "PHASE3_EXPERIMENTAL_SCOPE.md",
        "PHASE3_EXPERIMENTAL_FREEZE.md",
        "PHASE3_EXECUTION_READINESS_DESIGN.md",
        "PHASE3_PROMOTION_ROLLBACK_CRITERIA.md",
        "PHASE3_OBSERVER_CONFLICT_PLAYBOOK.md",
        "PHASE3_REAL_IMPLEMENTATION_PROMPT.md",
    ]:
        (docs / name).write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
    for name in [
        "PHASE3_EXPERIMENTAL_SIMULATION.md",
        "PHASE3_EXPERIMENTAL_SAFETY_REPORT.md",
        "PHASE3_FAMILY_DEDUP_AUDIT.md",
        "PHASE3_COST_MODE_COMPARISON.md",
        "PHASE3_COST_GATE_REVIEW.md",
        "PHASE3_SUSPEND_FAMILY_REVIEW.md",
        "PHASE3_SUSPEND_FAMILY_DECISION.md",
        "PHASE3_PAPER_SHADOW_SUMMARY.md",
        "PHASE3_SHADOW_LIFECYCLE_SUMMARY.md",
        "PHASE3_LIFECYCLE_GUARD_SUMMARY.md",
        "PHASE3_DEMO_REHEARSAL_CHECKLIST.md",
        "PHASE3_TO_DEMO_HANDOFF.md",
        "PHASE3_EXPERIMENTAL_MANIFEST.md",
    ]:
        (reports / name).write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
    (repo / "status.html").write_text("<!doctype html>\n", encoding="utf-8")
    (bundle_dir / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip").write_bytes(b"zip")
    (reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json").write_text(
        json.dumps({"status": "PASS", "findings_count": 0}),
        encoding="utf-8",
    )
    (reports / "PHASE3_EXPERIMENTAL_MANIFEST.json").write_text(
        json.dumps({"status": "PASS", "working_tree_clean": True}),
        encoding="utf-8",
    )
    (reports / "PHASE3_EXPERIMENTAL_STATUS.json").write_text(
        json.dumps(
            {
                "simulation": {"accepted_events": 3, "status": "EXPERIMENTAL_COST_SUSPEND_SCENARIO"},
                "suspend_family_decision": {
                    "status": "REVIEW_READY_KEEP_SUSPENDED",
                    "keep_suspended_primary_rows": 1,
                },
                "family_dedup_audit": {"status": "REVIEW_READY"},
                "cost_mode_comparison": {"status": "REVIEW_READY", "mode_count": 4},
                "cost_gate_review": {"status": "REVIEW_READY", "threshold_count": 4},
                "paper_shadow_experiment": {
                    "status": "SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS",
                    "would_open_count": 2,
                    "demo_authorized": False,
                },
                "shadow_lifecycle_experiment": {
                    "status": "SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY",
                    "synthetic_open_count": 2,
                    "demo_authorized": False,
                },
                "lifecycle_guard_experiment": {
                    "status": "SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY",
                    "guarded_open_count": 1,
                    "demo_authorized": False,
                },
                "demo_rehearsal": {
                    "status": "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY",
                    "rehearsal_event_count": 3,
                    "shadow_open_events": 1,
                    "blocked_events": 1,
                    "demo_authorized": False,
                    "can_start_real_demo": False,
                },
                "demo_handoff": {
                    "status": "READY_FOR_REVIEW_WAITING_REAL_GATES",
                    "phase2_readiness": "PENDING",
                    "can_start_demo_now": False,
                    "demo_authorized": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text(
        "\n".join(
                [
                    "# Phase 2 Readiness Report",
                    "",
                    "Overall status: PENDING",
                    "",
                    "## Gates",
                    "",
                    "| Gate | Status | Evidence |",
                "| --- | --- | --- |",
                "| Active-market 72-hour soak | PENDING | Longest active streak pending. |",
                "| Owner approval | PENDING | No approval file. |",
            ]
        ),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE2_DEMO_COUNTDOWN.json").write_text(
        json.dumps(
            {
                "wait_gates": [
                    {
                        "gate": "Active-market 72-hour soak",
                        "status": "PENDING",
                        "current": 27.92,
                        "required": 72.0,
                        "remaining": 44.08,
                        "unit": "hours",
                    }
                ],
                "owner_actions_now": [
                    {
                        "gate": "Owner approval",
                        "status": "PENDING",
                        "action": "Sign PHASE2_OWNER_APPROVAL.md only after objective gates pass.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    path = module.generate_phase3_completion_audit(phase3, repo)

    audit = json.loads(path.read_text(encoding="utf-8"))
    assert audit["status"] == "REPO_SIDE_COMPLETE_WAITING_REAL_GATES"
    assert audit["phase3_repo_complete"] is True
    assert audit["demo_authorized"] is False
    assert audit["remaining_phase3_repo_items"] == []
    assert audit["external_blockers"][0]["gate"] == "Active-market 72-hour soak"
    assert audit["external_blockers"][0]["current_detail"] == "current=27.92; required=72.0; remaining=44.08; unit=hours"
    assert audit["external_blockers"][1]["gate"] == "Owner approval"
    assert "objective gates pass" in audit["external_blockers"][1]["current_detail"]


def test_phase3_completion_audit_accepts_dirty_manifest_as_wip_snapshot(tmp_path: Path):
    module = _load_script("generate_phase3_completion_audit")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    docs = phase3 / "docs"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    bundle_dir = phase3 / "outputs" / "review_bundles"
    reports.mkdir(parents=True)
    docs.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    bundle_dir.mkdir(parents=True)
    for name in [
        "PHASE3_EXPERIMENTAL_SCOPE.md",
        "PHASE3_EXPERIMENTAL_FREEZE.md",
        "PHASE3_EXECUTION_READINESS_DESIGN.md",
        "PHASE3_PROMOTION_ROLLBACK_CRITERIA.md",
        "PHASE3_OBSERVER_CONFLICT_PLAYBOOK.md",
        "PHASE3_REAL_IMPLEMENTATION_PROMPT.md",
    ]:
        (docs / name).write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
    for name in [
        "PHASE3_EXPERIMENTAL_SIMULATION.md",
        "PHASE3_EXPERIMENTAL_SAFETY_REPORT.md",
        "PHASE3_FAMILY_DEDUP_AUDIT.md",
        "PHASE3_COST_MODE_COMPARISON.md",
        "PHASE3_COST_GATE_REVIEW.md",
        "PHASE3_SUSPEND_FAMILY_REVIEW.md",
        "PHASE3_SUSPEND_FAMILY_DECISION.md",
        "PHASE3_PAPER_SHADOW_SUMMARY.md",
        "PHASE3_SHADOW_LIFECYCLE_SUMMARY.md",
        "PHASE3_LIFECYCLE_GUARD_SUMMARY.md",
        "PHASE3_DEMO_REHEARSAL_CHECKLIST.md",
        "PHASE3_TO_DEMO_HANDOFF.md",
        "PHASE3_EXPERIMENTAL_MANIFEST.md",
    ]:
        (reports / name).write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
    (repo / "status.html").write_text("<!doctype html>\n", encoding="utf-8")
    (bundle_dir / "PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip").write_bytes(b"zip")
    (reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json").write_text(
        json.dumps({"status": "PASS", "findings_count": 0}),
        encoding="utf-8",
    )
    (reports / "PHASE3_EXPERIMENTAL_MANIFEST.json").write_text(
        json.dumps({"status": "DIRTY_WORKTREE", "working_tree_clean": False}),
        encoding="utf-8",
    )
    (reports / "PHASE3_EXPERIMENTAL_STATUS.json").write_text(
        json.dumps(
            {
                "simulation": {"accepted_events": 3, "status": "EXPERIMENTAL_COST_SUSPEND_SCENARIO"},
                "suspend_family_decision": {
                    "status": "REVIEW_READY_KEEP_SUSPENDED",
                    "keep_suspended_primary_rows": 1,
                },
                "family_dedup_audit": {"status": "REVIEW_READY"},
                "cost_mode_comparison": {"status": "REVIEW_READY", "mode_count": 4},
                "cost_gate_review": {"status": "REVIEW_READY", "threshold_count": 4},
                "paper_shadow_experiment": {
                    "status": "SIDE_EXPERIMENT_PAPER_SHADOW_READY_WITH_COST_BLOCKS",
                    "would_open_count": 2,
                    "demo_authorized": False,
                },
                "shadow_lifecycle_experiment": {
                    "status": "SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY",
                    "synthetic_open_count": 2,
                    "demo_authorized": False,
                },
                "lifecycle_guard_experiment": {
                    "status": "SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY",
                    "guarded_open_count": 1,
                    "demo_authorized": False,
                },
                "demo_rehearsal": {
                    "status": "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY",
                    "rehearsal_event_count": 3,
                    "shadow_open_events": 1,
                    "blocked_events": 1,
                    "demo_authorized": False,
                    "can_start_real_demo": False,
                },
                "demo_handoff": {
                    "status": "READY_FOR_REVIEW_WAITING_REAL_GATES",
                    "phase2_readiness": "PENDING",
                    "can_start_demo_now": False,
                    "demo_authorized": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n\n## Gates\n", encoding="utf-8")
    (phase1_reports / "PHASE2_DEMO_COUNTDOWN.json").write_text(json.dumps({}), encoding="utf-8")

    path = module.generate_phase3_completion_audit(phase3, repo)

    audit = json.loads(path.read_text(encoding="utf-8"))
    manifest_row = next(row for row in audit["repo_requirement_rows"] if row["key"] == "manifest")
    assert audit["status"] == "REPO_SIDE_COMPLETE_WITH_WARNINGS_WAITING_REAL_GATES"
    assert audit["phase3_repo_complete"] is True
    assert audit["phase3_release_clean"] is False
    assert manifest_row["status"] == "WARN"
    assert "DIRTY_WORKTREE" in manifest_row["detail"]


def test_phase3_family_dedup_audit_detects_same_bar_distinct_level(tmp_path: Path):
    module = _load_script("generate_phase3_family_dedup_audit")
    input_csv = tmp_path / "distinct.csv"
    _write_rows(
        input_csv,
        [
            _safe_row("DL001", "breakout_retest", "2026.05.27 12:00:00", "LONG", "latest_swing_high", "4500.00"),
            _safe_row("DL002", "swing_breakout_retest_v0", "2026.05.27 12:00:00", "LONG", "previous_weekly_high", "4510.00"),
        ],
    )

    path = module.generate_family_dedup_audit(input_csv, tmp_path / "reports")

    audit = json.loads(path.read_text(encoding="utf-8"))
    assert audit["classification_counts"] == {"SAME_BAR_DISTINCT_LEVEL": 1}
    row = audit["rows"][0]
    assert row["classification"] == "SAME_BAR_DISTINCT_LEVEL"
    assert "level_kind" in row["differing_fields"]
    assert "level_price" in row["differing_fields"]


def test_phase3_family_dedup_audit_detects_true_duplicate_and_direction_conflict(tmp_path: Path):
    module = _load_script("generate_phase3_family_dedup_audit")
    input_csv = tmp_path / "dedup.csv"
    _write_rows(
        input_csv,
        [
            _safe_row("DD001", "breakout_retest", "2026.05.27 12:00:00", "LONG", "latest_swing_high", "4500.00"),
            _safe_row("DD002", "swing_breakout_retest_v0", "2026.05.27 12:00:00", "LONG", "latest_swing_high", "4500.00"),
            _safe_row("DD003", "breakout_retest", "2026.05.27 12:05:00", "LONG", "latest_swing_high", "4510.00"),
            _safe_row("DD004", "swing_breakout_retest_v0", "2026.05.27 12:05:00", "SHORT", "latest_swing_high", "4510.00"),
        ],
    )

    path = module.generate_family_dedup_audit(input_csv, tmp_path / "reports")

    audit = json.loads(path.read_text(encoding="utf-8"))
    assert audit["classification_counts"] == {
        "SAME_BAR_DIRECTION_CONFLICT": 1,
        "TRUE_DUPLICATE": 1,
    }


def test_phase3_manifest_is_pending_when_required_reports_are_missing(tmp_path: Path):
    module = _load_script("generate_phase3_experimental_manifest")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    (reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json").write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    (reports / "PHASE3_EXPERIMENTAL_SIMULATION.json").write_text(json.dumps({"status": "EXPERIMENTAL_ACTIVE"}), encoding="utf-8")

    path = module.generate_phase3_experimental_manifest(phase3, repo)

    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["status"] == "PENDING"
    assert manifest["files"]["phase3_cost_mode_comparison_md"]["exists"] is False
    assert manifest["files"]["script_completion_audit"]["path"].endswith("generate_phase3_completion_audit.py")
    assert manifest["files"]["phase3_completion_audit_md"]["path"].endswith("PHASE3_COMPLETION_AUDIT.md")
    assert manifest["files"]["phase3_status_json"]["path"].endswith("PHASE3_EXPERIMENTAL_STATUS.json")


def test_phase3_manifest_status_marks_dirty_worktree():
    module = _load_script("generate_phase3_experimental_manifest")
    files = {"all_good": {"exists": True}}
    safety = {"status": "PASS"}
    simulation = {"status": "EXPERIMENTAL_ACTIVE"}

    assert module._manifest_status(safety, simulation, files, "") == "PASS"
    assert module._manifest_status(safety, simulation, files, " M changed.py") == "DIRTY_WORKTREE"
    assert module._manifest_status({}, simulation, files, "") == "PENDING"


def test_phase3_fixture_report_generation_is_deterministic_for_csv_outputs(tmp_path: Path):
    comparison = _load_script("generate_phase3_cost_mode_comparison")
    dedup = _load_script("generate_phase3_family_dedup_audit")

    comparison.generate_cost_mode_comparison(FIXTURE, tmp_path / "a")
    comparison.generate_cost_mode_comparison(FIXTURE, tmp_path / "b")
    dedup.generate_family_dedup_audit(FIXTURE, tmp_path / "a")
    dedup.generate_family_dedup_audit(FIXTURE, tmp_path / "b")

    assert (tmp_path / "a" / "PHASE3_COST_MODE_COMPARISON.csv").read_text(encoding="utf-8") == (
        tmp_path / "b" / "PHASE3_COST_MODE_COMPARISON.csv"
    ).read_text(encoding="utf-8")
    assert (tmp_path / "a" / "PHASE3_FAMILY_DEDUP_AUDIT.csv").read_text(encoding="utf-8") == (
        tmp_path / "b" / "PHASE3_FAMILY_DEDUP_AUDIT.csv"
    ).read_text(encoding="utf-8")


def test_phase3_artifact_verifier_requires_reports_and_authority_sentence(tmp_path: Path):
    module = _load_script("verify_phase3_experimental_artifacts")
    phase3 = tmp_path / "repo" / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    for name in module.REQUIRED_ARTIFACTS:
        path = reports / name
        if path.suffix == ".md":
            path.write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
        else:
            path.write_text("event_id\n", encoding="utf-8")
    _write_valid_phase3_verifier_jsons(module, phase3, tmp_path / "repo")

    assert module.verify_phase3_experimental_artifacts(phase3, tmp_path / "repo") == []

    (reports / "PHASE3_EXPERIMENTAL_STATUS.md").write_text("missing authority\n", encoding="utf-8")
    errors = module.verify_phase3_experimental_artifacts(phase3, tmp_path / "repo")
    assert any("missing required Phase 2 authority sentence" in error for error in errors)


def test_phase3_artifact_verifier_can_require_clean_manifest(tmp_path: Path):
    module = _load_script("verify_phase3_experimental_artifacts")
    phase3 = tmp_path / "repo" / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    for name in module.REQUIRED_ARTIFACTS:
        path = reports / name
        if path.suffix == ".md":
            path.write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
        else:
            path.write_text("event_id\n", encoding="utf-8")
    _write_valid_phase3_verifier_jsons(module, phase3, tmp_path / "repo")
    manifest_json = reports / "PHASE3_EXPERIMENTAL_MANIFEST.json"

    assert module.verify_phase3_experimental_artifacts(
        phase3,
        tmp_path / "repo",
        require_clean_manifest=True,
    ) == []

    manifest_json.write_text(
        json.dumps({"status": "DIRTY_WORKTREE", "working_tree_clean": False, "working_tree_short_status": " M x"}),
        encoding="utf-8",
    )
    errors = module.verify_phase3_experimental_artifacts(
        phase3,
        tmp_path / "repo",
        require_clean_release_snapshot=True,
    )
    assert any("status must be PASS" in error for error in errors)


def test_phase3_artifact_verifier_allows_dirty_working_snapshot_with_warned_audit(tmp_path: Path):
    module = _load_script("verify_phase3_experimental_artifacts")
    phase3 = tmp_path / "repo" / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    for name in module.REQUIRED_ARTIFACTS:
        path = reports / name
        if path.suffix == ".md":
            path.write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
        else:
            path.write_text("event_id\n", encoding="utf-8")
    _write_valid_phase3_verifier_jsons(module, phase3, tmp_path / "repo")
    manifest_json = reports / "PHASE3_EXPERIMENTAL_MANIFEST.json"
    clean_manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    manifest_json.write_text(
        json.dumps(
            {
                "status": "DIRTY_WORKTREE",
                "working_tree_clean": False,
                "working_tree_short_status": " M x",
                "files": clean_manifest["files"],
            }
        ),
        encoding="utf-8",
    )
    completion_json = reports / "PHASE3_COMPLETION_AUDIT.json"
    completion_json.write_text(
        json.dumps(
            {
                "repo_requirement_rows": [
                    {
                        "key": "manifest",
                        "status": "WARN",
                        "evidence": str(reports / "PHASE3_EXPERIMENTAL_MANIFEST.md"),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert module.verify_phase3_experimental_artifacts(
        phase3,
        tmp_path / "repo",
        allow_dirty_working_snapshot=True,
    ) == []


def test_phase3_artifact_verifier_detects_status_simulation_mismatch(tmp_path: Path):
    module = _load_script("verify_phase3_experimental_artifacts")
    phase3 = tmp_path / "repo" / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    for name in module.REQUIRED_ARTIFACTS:
        path = reports / name
        if path.suffix == ".md":
            path.write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
        else:
            path.write_text("event_id\n", encoding="utf-8")
    _write_valid_phase3_verifier_jsons(module, phase3, tmp_path / "repo")
    status_json = reports / "PHASE3_EXPERIMENTAL_STATUS.json"
    status = json.loads(status_json.read_text(encoding="utf-8"))
    status["simulation"]["accepted_events"] = 999
    status_json.write_text(json.dumps(status), encoding="utf-8")

    errors = module.verify_phase3_experimental_artifacts(phase3, tmp_path / "repo")

    assert any("status/simulation mismatch for accepted_events" in error for error in errors)


def test_phase3_artifact_verifier_detects_stale_core_report_hash(tmp_path: Path):
    module = _load_script("verify_phase3_experimental_artifacts")
    phase3 = tmp_path / "repo" / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    for name in module.REQUIRED_ARTIFACTS:
        path = reports / name
        if path.suffix == ".md":
            path.write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
        else:
            path.write_text("event_id\n", encoding="utf-8")
    _write_valid_phase3_verifier_jsons(module, phase3, tmp_path / "repo")

    assert module.verify_phase3_experimental_artifacts(phase3, tmp_path / "repo") == []

    (reports / "PHASE3_COST_GATE_REVIEW.md").write_text(
        module.PHASE2_AUTHORITY_SENTENCE + "\nchanged after manifest\n",
        encoding="utf-8",
    )
    errors = module.verify_phase3_experimental_artifacts(phase3, tmp_path / "repo")

    assert any("manifest hash is stale" in error for error in errors)


def test_phase3_artifact_verifier_requires_core_reports_in_manifest(tmp_path: Path):
    module = _load_script("verify_phase3_experimental_artifacts")
    phase3 = tmp_path / "repo" / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    for name in module.REQUIRED_ARTIFACTS:
        path = reports / name
        if path.suffix == ".md":
            path.write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
        else:
            path.write_text("event_id\n", encoding="utf-8")
    _write_valid_phase3_verifier_jsons(module, phase3, tmp_path / "repo")
    manifest_json = reports / "PHASE3_EXPERIMENTAL_MANIFEST.json"
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    manifest["files"] = {
        key: value
        for key, value in manifest["files"].items()
        if Path(value["path"]).name != "PHASE3_EXPERIMENTAL_LEDGER.csv"
    }
    manifest_json.write_text(json.dumps(manifest), encoding="utf-8")

    errors = module.verify_phase3_experimental_artifacts(phase3, tmp_path / "repo")

    assert any("manifest does not hash required Phase 3 artifact: PHASE3_EXPERIMENTAL_LEDGER.csv" in error for error in errors)


def test_phase3_artifact_verifier_detects_stale_real_status_snapshot(tmp_path: Path):
    module = _load_script("verify_phase3_experimental_artifacts")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    reports.mkdir(parents=True)
    phase1_reports.mkdir(parents=True)
    for name in module.REQUIRED_ARTIFACTS:
        path = reports / name
        if path.suffix == ".md":
            path.write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
        else:
            path.write_text("event_id\n", encoding="utf-8")
    _write_valid_phase3_verifier_jsons(module, phase3, repo)
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PASS\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "latest_row": {
                        "bar_time": "2026.05.28 16:25:00",
                        "dry_run": "true",
                        "trade_permission": "false",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    errors = module.verify_phase3_experimental_artifacts(phase3, repo)

    assert any("real_phase1_acceptance is stale" in error for error in errors)
    assert any("latest_phase1_bar is stale" in error for error in errors)


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "cluster_id",
        "observer",
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "bar_time",
        "run_id",
        "symbol",
        "direction",
        "level_kind",
        "level_price",
        "entry_price",
        "stop_loss",
        "take_profit",
        "stop_distance_points",
        "spread_points",
        "risk_state",
        "execution_state",
        "server_time_status",
        "reason_code",
        "trade_permission",
        "dry_run",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _safe_row(
    cluster_id: str,
    observer: str,
    bar_time: str,
    direction: str,
    level_kind: str,
    level_price: str,
) -> dict[str, str]:
    return {
        "cluster_id": cluster_id,
        "observer": observer,
        "timestamp_broker": bar_time,
        "timestamp_utc": "2026.05.27 08:00:00",
        "timestamp_local": "2026.05.27 13:30:00",
        "bar_time": bar_time,
        "run_id": "phase1-dry-run-v0.7",
        "symbol": "XAUUSD",
        "direction": direction,
        "level_kind": level_kind,
        "level_price": level_price,
        "entry_price": "4502.00",
        "stop_loss": "4497.00",
        "take_profit": "4509.50",
        "stop_distance_points": "500.00",
        "spread_points": "30.00",
        "risk_state": "NORMAL",
        "execution_state": "EXECUTION_OK",
        "server_time_status": "CLOCK_OK",
        "reason_code": "DRY_RUN_SIGNAL",
        "trade_permission": "false",
        "dry_run": "true",
    }


def _write_valid_phase3_verifier_jsons(module, phase3: Path, repo: Path) -> None:
    reports = phase3 / "outputs" / "reports"
    simulation = {
        "status": "EXPERIMENTAL_COST_SUSPEND_SCENARIO",
        "accepted_events": 3,
        "raw_observer_event_count": 3,
        "family_unique_event_count": 2,
        "observer_duplicate_count": 1,
        "observer_conflict_count": 0,
        "rejected_source_rows": 0,
        "cost_mode": "entry_exit_proxy",
    }
    status = {
        "status": "EXPERIMENTAL_COST_SUSPEND_SCENARIO",
        "real_phase1_acceptance": "PENDING",
        "real_phase2_readiness": "PENDING",
        "authorized_for_deployment": False,
        "mt5_runtime_touched": False,
        "broker_action_code_allowed": False,
        "latest_phase1_bar": "2026.05.28 15:40:00",
        "latest_phase1_dry_run": "true",
        "latest_phase1_trade_permission": "false",
        "simulation": simulation,
    }
    safety = {"status": "PASS", "findings_count": 0}
    rehearsal = {
        "status": "SIDE_EXPERIMENT_DEMO_REHEARSAL_READY",
        "demo_authorized": False,
        "can_start_real_demo": False,
    }
    handoff = {
        "status": "READY_FOR_REVIEW_WAITING_REAL_GATES",
        "phase2_readiness": "PENDING",
        "can_start_demo_now": False,
        "demo_authorized": False,
        "broker_action_code_allowed": False,
    }
    completion = {
        "repo_requirement_rows": [
            {
                "status": "PASS",
                "evidence": str(reports / "PHASE3_EXPERIMENTAL_STATUS.md"),
            }
        ]
    }
    files = {}
    manifest_tracked_names = [
        *module.REQUIRED_ARTIFACTS,
        *(name for name in module.REQUIRED_JSON_ARTIFACTS if name != "PHASE3_EXPERIMENTAL_MANIFEST.json"),
    ]
    for name in manifest_tracked_names:
        path = reports / name
        if not path.exists():
            path.write_text("{}\n", encoding="utf-8")
        files[name] = {
            "exists": True,
            "path": str(path),
            "sha256": module._sha256(path),
            "bytes": path.stat().st_size,
        }
    manifest = {
        "status": "PASS",
        "working_tree_clean": True,
        "working_tree_short_status": "",
        "files": files,
    }
    (reports / "PHASE3_EXPERIMENTAL_SIMULATION.json").write_text(json.dumps(simulation), encoding="utf-8")
    (reports / "PHASE3_EXPERIMENTAL_STATUS.json").write_text(json.dumps(status), encoding="utf-8")
    (reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json").write_text(json.dumps(safety), encoding="utf-8")
    (reports / "PHASE3_DEMO_REHEARSAL_PLAN.json").write_text(json.dumps(rehearsal), encoding="utf-8")
    (reports / "PHASE3_TO_DEMO_HANDOFF.json").write_text(json.dumps(handoff), encoding="utf-8")
    (reports / "PHASE3_COMPLETION_AUDIT.json").write_text(json.dumps(completion), encoding="utf-8")
    for name in manifest_tracked_names:
        path = reports / name
        files[name]["sha256"] = module._sha256(path)
        files[name]["bytes"] = path.stat().st_size
    (reports / "PHASE3_EXPERIMENTAL_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
