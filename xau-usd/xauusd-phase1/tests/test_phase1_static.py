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
    assert "InpObserveBreakoutRetest = true" in text
    assert "g_logger.WriteDecision" in text
    assert "g_logger.WriteStartup" in text
    assert "g_logger.WriteShutdown" in text
    assert "EventSetTimer(1)" in text
    assert "CPhase1ServerTimeValidator" in text
    assert "CPhase1MagicNumberAllocator" in text
    assert "CPhase1ExpertLifecycleManager" in text


def test_safe_preset_keeps_shell_in_dry_run_observation_mode():
    text = (ROOT / "mt5" / "Presets" / "Phase1DryRunShell.safe.set").read_text(encoding="utf-8")

    assert "InpDryRunOnly=true" in text
    assert "InpObserveBreakoutRetest=true" in text
    assert "InpDecisionLogFileName=decision_log.csv" in text
    assert "InpStartupLogFileName=startup_log.csv" in text
    assert "InpShutdownLogFileName=shutdown_log.csv" in text
    assert "InpRunId=phase1-dry-run-v0.5" in text


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
    assert "`breakout_retest` is the only approved future expert" in text


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
        "magic_namespace_ok",
        "server_time_status",
        "atr14_points",
        "compression_state",
        "br_stage",
        "br_direction",
        "br_would_signal",
        "br_reason_code",
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
