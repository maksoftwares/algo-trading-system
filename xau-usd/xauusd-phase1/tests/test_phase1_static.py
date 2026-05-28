from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase1_safety_audit_has_no_findings():
    module = _load_safety_module()

    assert module.audit_phase1_tree(ROOT) == []


def test_phase1_log_verifier_script_exists():
    text = (ROOT / "scripts" / "verify_phase1_logs.py").read_text(encoding="utf-8")

    assert "verify_phase1_logs" in text
    assert "decision_duplicate_headers" in text
    assert "trade_permission_locked" in text


def test_phase1_bundle_generator_script_exists():
    text = (ROOT / "scripts" / "generate_phase1_bundle.py").read_text(encoding="utf-8")

    assert "generate_phase1_bundle" in text
    assert "phase1_bundle_manifest.json" in text
    assert "PHASE1_DRY_RUN_BUNDLE" in text
    assert "acceptance_status" in text


def test_phase1_deploy_script_exists():
    text = (ROOT / "scripts" / "deploy_phase1_mt5.py").read_text(encoding="utf-8")

    assert "deploy_phase1_mt5" in text
    assert "MetaEditor64.exe" in text
    assert "Phase1DryRunShell.mq5" in text


def test_phase1_acceptance_report_script_exists():
    text = (ROOT / "scripts" / "generate_phase1_acceptance_report.py").read_text(encoding="utf-8")

    assert "generate_phase1_acceptance_report" in text
    assert "PHASE1_ACCEPTANCE_REPORT" in text
    assert "Source safety audit" in text
    assert "Would-signal evidence" in text
    assert "Runtime freshness" in text
    assert "Five trading day soak" in text


def test_phase1_would_signal_report_script_exists():
    text = (ROOT / "scripts" / "generate_phase1_would_signal_report.py").read_text(encoding="utf-8")

    assert "generate_phase1_would_signal_report" in text
    assert "PHASE1_WOULD_SIGNAL_REPORT" in text
    assert "would_signal_permission_lock" in text


def test_dry_run_shell_is_locked_to_passive_mode():
    text = (ROOT / "mt5" / "Experts" / "Phase1DryRunShell.mq5").read_text(encoding="utf-8")

    assert "input bool InpDryRunOnly = true;" in text
    assert 'input string InpRunId = "phase1-dry-run-v0.7";' in text
    assert 'input string InpBreakoutRetestFamilyCostState = "COST_REVALIDATION_PENDING";' in text
    assert "InpObserveBreakoutRetest = true" in text
    assert "g_logger.WriteDecision" in text
    assert "g_logger.WriteStartup" in text
    assert "g_logger.WriteShutdown" in text
    assert "EventSetTimer(1)" in text
    assert "CPhase1ServerTimeValidator" in text
    assert "CPhase1MagicNumberAllocator" in text
    assert "CPhase1ExpertLifecycleManager" in text
    assert "return INIT_FAILED;" in text
    assert "Phase1NormalizeSignalFromObservers" in text
    assert "Phase1FillSignalFromObservation" in text
    assert "Phase1IsBreakoutRetestFamily" in text
    assert "signal.entry_price = observation.entry_price" in text
    assert "signal.stop_loss = observation.stop_loss" in text
    assert "signal.take_profit = observation.take_profit" in text


def test_safe_preset_keeps_shell_in_dry_run_observation_mode():
    text = (ROOT / "mt5" / "Presets" / "Phase1DryRunShell.safe.set").read_text(encoding="utf-8")

    assert "InpDryRunOnly=true" in text
    assert "InpObserveBreakoutRetest=true" in text
    assert "InpObserveSwingBreakoutRetest=true" in text
    assert "InpDecisionLogFileName=decision_log.csv" in text
    assert "InpStartupLogFileName=startup_log.csv" in text
    assert "InpShutdownLogFileName=shutdown_log.csv" in text
    assert "InpRunId=phase1-dry-run-v0.7" in text
    assert "InpBreakoutRetestFamilyCostState=COST_REVALIDATION_PENDING" in text


def test_risk_test_presets_stay_dry_run_only():
    preset_dir = ROOT / "mt5" / "Presets"
    expected = {
        "Phase1DryRunShell.test_daily_lock.set": "InpSimulatedDailyPnlPct=-2.5",
        "Phase1DryRunShell.test_weekly_lock.set": "InpSimulatedWeeklyPnlPct=-5.5",
        "Phase1DryRunShell.test_monthly_lock.set": "InpSimulatedMonthlyPnlPct=-10.5",
        "Phase1DryRunShell.test_manual_lock.set": "InpManualRiskLock=true",
    }

    for name, needle in expected.items():
        text = (preset_dir / name).read_text(encoding="utf-8")
        assert "InpDryRunOnly=true" in text
        assert "InpDecisionLogFileName=decision_log.csv" in text
        assert needle in text


def test_phase1_docs_record_gate9_boundary():
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Phase 1 dry-run authorization is now satisfied" in text
    assert "Expert modules | Dry-run contracts only" in text
    assert "`swing_breakout_retest_v0` is approved as a same-family future expert candidate" in text


def test_phase1_spec_keeps_first_build_observation_only():
    text = (ROOT / "docs" / "PHASE1_MASTER_EA_DRY_RUN_SPEC.md").read_text(encoding="utf-8")

    assert "decision_log.csv" in text
    assert "Safety audit finds no broker-action API usage" in text
    assert "No expert is active beyond the approved dry-run scope" in text


def test_phase1_decision_logger_has_required_columns():
    text = (ROOT / "mt5" / "Include" / "Phase1" / "Phase1Logger.mqh").read_text(encoding="utf-8")

    for column in (
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "session",
        "decision_schema_version",
        "decision_schema_hash",
        "regime",
        "risk_state",
        "requested_risk_pct",
        "simulated_daily_pnl_pct",
        "simulated_weekly_pnl_pct",
        "simulated_monthly_pnl_pct",
        "manual_risk_lock",
        "risk_ok",
        "execution_state",
        "news_state",
        "expert_lifecycle_state",
        "br_lifecycle_state",
        "sbr_lifecycle_state",
        "magic_namespace_ok",
        "server_time_status",
        "atr14_points",
        "compression_state",
        "br_stage",
        "br_direction",
        "br_would_signal",
        "br_reason_code",
        "sbr_stage",
        "sbr_direction",
        "sbr_would_signal",
        "sbr_reason_code",
        "allowed_expert",
        "would_have_allowed_experts",
        "trade_permission",
        "block_reason",
        "dry_run",
    ):
        assert f'"{column}"' in text


def test_phase1_startup_and_shutdown_loggers_exist():
    text = (ROOT / "mt5" / "Include" / "Phase1" / "Phase1Logger.mqh").read_text(encoding="utf-8")

    assert "bool WriteStartup" in text
    assert "bool WriteShutdown" in text
    assert "EnsureDecisionLogSchema" in text
    assert "decision_schema_rotation_performed" in text
    assert "decision_schema_archive_path" in text


def test_phase1_magic_validation_has_reserved_range_and_collision_checks():
    text = (ROOT / "mt5" / "Include" / "Phase1" / "Phase1Magic.mqh").read_text(encoding="utf-8")
    registry = (ROOT / "docs" / "MAGIC_NUMBER_EXTERNAL_REGISTRY.md").read_text(encoding="utf-8")

    assert "ReservedRangeMin" in text
    assert "ReservedRangeMax" in text
    assert "ValidateReservedRange" in text
    assert "ValidateExternalCollisions" in text
    assert "PositionsTotal" in text
    assert "OrdersTotal" in text
    assert "910000-910999" in registry
    assert "V61" in registry
    assert "V77" in registry
    assert "V80" in registry
    assert "V85" in registry
    assert "account isolation" in registry


def test_breakout_retest_lifecycle_has_family_cost_pending_and_suspension_states():
    types = (ROOT / "mt5" / "Include" / "Phase1" / "Phase1Types.mqh").read_text(encoding="utf-8")
    lifecycle = (ROOT / "mt5" / "Include" / "Phase1" / "Phase1Lifecycle.mqh").read_text(encoding="utf-8")

    assert "PHASE1_EXPERT_COST_REVALIDATION_PENDING" in types
    assert 'return "COST_REVALIDATION_PENDING"' in types
    assert "PHASE1_EXPERT_COST_SUSPENDED" in types
    assert 'return "COST_SUSPENDED"' in types
    assert "IsBreakoutRetestFamilyBlockedByCost" in lifecycle
    assert "ParseBreakoutRetestFamilyCostState" in lifecycle


def test_phase1_safety_audit_ignores_docs():
    text = (ROOT / "scripts" / "audit_phase1_safety.py").read_text(encoding="utf-8")

    assert "SOURCE_PARTS" in text
    assert '".md"' not in text
    assert '"docs"' in text


def test_phase1_observer_parity_report_script_exists():
    text = (ROOT / "scripts" / "generate_phase1_observer_parity_report.py").read_text(encoding="utf-8")

    assert "generate_phase1_observer_parity_report" in text
    assert "PHASE1_OBSERVER_PARITY_REPORT" in text
    assert "breakout_retest" in text


def test_static_docs_do_not_pin_runtime_snapshots():
    text = (ROOT / "docs" / "PHASE2_AUTHORIZATION_CHECKLIST.md").read_text(encoding="utf-8")

    assert "## Current State Source" in text
    assert "| Decision rows | 56 |" not in text
    assert "| Latest bar | 2026." not in text
    assert "| Soak progress | 8.26%" not in text


def test_phase2_authorization_checklist_uses_owner_accepted_family_d2_method():
    text = (ROOT / "docs" / "PHASE2_AUTHORIZATION_CHECKLIST.md").read_text(encoding="utf-8")

    assert "| D2 Reality Check / SPA-style bootstrap | PASS | Active readiness method is owner-accepted `D2_FAMILY_CLUSTERED_V0`" in text
    assert "Candidate-level D2 remains preserved audit evidence, not the active readiness blocker." in text
    assert "| D2 Reality Check / SPA-style bootstrap | FAIL |" not in text
    assert "same-family variants as diversification" not in text


def test_phase2_authorization_checklist_references_gap_classification_review():
    text = (ROOT / "docs" / "PHASE2_AUTHORIZATION_CHECKLIST.md").read_text(encoding="utf-8")

    assert "PHASE1_GAP_CLASSIFICATION_REVIEW.md" in text
    assert "expected broker maintenance gaps pause" in text


def test_review_12_records_phase3_freeze_and_demo_gate_boundary():
    text = (ROOT.parents[1] / "docs" / "REVIEW_12_PHASE3_FREEZE_AND_DEMO_GATE_RESPONSE.md").read_text(
        encoding="utf-8"
    )

    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in text
    assert "Phase 3 is now a design evidence package, not an active expansion lane." in text
    assert "outputs/ci_synthetic/" in text
    assert "Phase 3-to-Phase 2 leakage protection" in text
    assert "Broker-action code" in text


def test_phase1_ci_verifies_phase2_transition_artifacts_and_dashboard():
    workflow = (ROOT.parents[1] / ".github" / "workflows" / "phase1.yml").read_text(encoding="utf-8")

    assert "Verify Phase 2 transition artifacts and dashboard freshness" in workflow
    assert "generate_phase2_demo_preflight_report.py --root ." in workflow
    assert "generate_phase2_owner_action_packet.py --root ." in workflow
    assert "verify_status_dashboard_freshness.py --repo-root ../.. --status-path ../../status.html" in workflow


def test_phase1_risk_gate_has_simulated_lock_states():
    text = (ROOT / "mt5" / "Include" / "Phase1" / "Phase1Risk.mqh").read_text(encoding="utf-8")

    assert "PHASE1_RISK_LOCKED_DAILY" in text
    assert "PHASE1_RISK_LOCKED_WEEKLY" in text
    assert "PHASE1_RISK_LOCKED_MONTHLY" in text
    assert "PHASE1_RISK_MANUAL_LOCK" in text


def test_phase1_module_slice_exists():
    for relative_path in (
        "mt5/Include/Phase1/Phase1MarketData.mqh",
        "mt5/Include/Phase1/Phase1Session.mqh",
        "mt5/Include/Phase1/Phase1Execution.mqh",
        "mt5/Include/Phase1/Phase1News.mqh",
        "mt5/Include/Phase1/Phase1Dashboard.mqh",
        "mt5/Include/Phase1/Phase1FeatureEngine.mqh",
        "mt5/Include/Phase1/Phase1ServerTime.mqh",
        "mt5/Include/Phase1/Phase1Magic.mqh",
        "mt5/Include/Phase1/Phase1Lifecycle.mqh",
        "mt5/Include/Phase1/Phase1BreakoutRetest.mqh",
    ):
        assert (ROOT / relative_path).exists()


def _load_safety_module():
    path = ROOT / "scripts" / "audit_phase1_safety.py"
    spec = importlib.util.spec_from_file_location("audit_phase1_safety", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_phase1_safety"] = module
    spec.loader.exec_module(module)
    return module
