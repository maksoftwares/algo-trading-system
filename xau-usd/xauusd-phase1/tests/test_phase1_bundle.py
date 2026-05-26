from __future__ import annotations

import csv
import importlib.util
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generate_phase1_bundle_includes_manifest_and_runtime_logs(tmp_path):
    module = _load_bundle_module()
    project = tmp_path / "project"
    files_dir = tmp_path / "files"
    project.mkdir()
    files_dir.mkdir()
    _write_project_shell(project)
    _write_phase0_cost_artifacts(project)
    _write_runtime_logs(files_dir)
    compile_log = tmp_path / "compile.log"
    compile_log.write_text("Result: 0 errors, 0 warnings\n", encoding="utf-8")

    output = module.generate_phase1_bundle(
        project,
        files_dir,
        project / "outputs" / "review_bundles",
        compile_log,
        now=datetime(2026, 5, 21, 16, 22),
    )

    assert output.bundle_path.exists()
    assert output.manifest_path.exists()
    assert output.log_status == "PASS"
    with zipfile.ZipFile(output.bundle_path) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("phase1_bundle_manifest.json").decode("utf-8"))
    assert "README.md" in names
    assert "mt5_runtime/decision_log.csv" in names
    assert "mt5_runtime/startup_log.csv" in names
    assert "mt5_runtime/shutdown_log.csv" in names
    assert "mt5_runtime/compile.log" in names
    assert "outputs/reports/PHASE1_WOULD_SIGNAL_REVIEW.csv" in names
    assert "outputs/reports/PHASE1_REVIEW_INDEX.md" in names
    assert "outputs/reports/PHASE1_OBSERVER_PARITY_REPORT.md" in names
    assert "outputs/reports/PHASE2_READINESS_REPORT.md" in names
    assert "outputs/reports/PHASE1_STATUS_SUMMARY.json" in names
    assert "outputs/reports/PHASE1_RUNTIME_HEALTH_REPORT.md" in names
    assert "outputs/reports/PHASE1_SOAK_HISTORY.csv" in names
    assert "outputs/reports/PHASE1_SOAK_HISTORY_REPORT.md" in names
    assert "outputs/reports/PHASE2_PAPER_LEDGER_SCHEMA_REPORT.md" in names
    assert "outputs/reports/PHASE2_PAPER_LEDGER_COLUMNS.csv" in names
    assert manifest["log_verification_status"] == "PASS"
    assert manifest["soak_analysis_status"] == "PASS"
    assert manifest["runtime_health_status"] == "PASS"
    assert manifest["runtime_health_report_path"].endswith("PHASE1_RUNTIME_HEALTH_REPORT.md")
    assert manifest["would_signal_status"] == "WARN"
    assert manifest["would_signal_count"] == 0
    assert manifest["would_signal_cluster_count"] == 0
    assert manifest["would_signal_csv_path"].endswith("PHASE1_WOULD_SIGNAL_REVIEW.csv")
    assert manifest["status_summary_path"].endswith("PHASE1_STATUS_SUMMARY.json")
    assert manifest["soak_history_path"].endswith("PHASE1_SOAK_HISTORY.csv")
    assert manifest["soak_history_rows"] == 1
    assert manifest["soak_history_report_path"].endswith("PHASE1_SOAK_HISTORY_REPORT.md")
    assert manifest["soak_history_report_status"] == "WARN"
    assert manifest["acceptance_status"] == "PENDING"
    assert manifest["review_index_status"] == "PENDING"
    assert manifest["review_index_path"].endswith("PHASE1_REVIEW_INDEX.md")
    assert manifest["observer_parity_status"] == "PASS"
    assert manifest["observer_parity_report_path"].endswith("PHASE1_OBSERVER_PARITY_REPORT.md")
    assert manifest["phase2_readiness_status"] == "PENDING"
    assert manifest["phase2_readiness_path"].endswith("PHASE2_READINESS_REPORT.md")
    assert manifest["included_count"] == output.included_count
    assert output.soak_status == "PASS"
    assert output.runtime_health_status == "PASS"
    assert str(output.runtime_health_report_path).endswith("PHASE1_RUNTIME_HEALTH_REPORT.md")
    assert output.would_signal_status == "WARN"
    assert output.acceptance_status == "PENDING"
    assert output.review_index_status == "PENDING"
    assert str(output.review_index_path).endswith("PHASE1_REVIEW_INDEX.md")
    assert output.phase2_readiness_status == "PENDING"
    assert str(output.phase2_readiness_path).endswith("PHASE2_READINESS_REPORT.md")
    assert output.soak_history_rows == 1
    assert output.soak_history_report_status == "WARN"


def _load_bundle_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase1_bundle.py"
    spec = importlib.util.spec_from_file_location("generate_phase1_bundle", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase1_bundle"] = module
    spec.loader.exec_module(module)
    return module


def _write_project_shell(project: Path) -> None:
    (project / "docs").mkdir()
    (project / "mt5" / "Experts").mkdir(parents=True)
    (project / "mt5" / "Include" / "Phase1").mkdir(parents=True)
    (project / "mt5" / "Presets").mkdir(parents=True)
    (project / "scripts").mkdir()
    (project / "tests").mkdir()
    (project / "README.md").write_text("# Phase 1\n", encoding="utf-8")
    (project / "docs" / "PHASE1_DRY_RUN_SCOPE.md").write_text("scope\n", encoding="utf-8")
    (project / "docs" / "PHASE2_DRY_RUN_TO_PAPER_PREP_SPEC.md").write_text("phase2 prep\n", encoding="utf-8")
    (project / "docs" / "PHASE2_PAPER_LEDGER_SCHEMA.md").write_text(_phase2_schema_doc(), encoding="utf-8")
    (project / "docs" / "PHASE2_COST_MEASUREMENT_PROTOCOL.md").write_text(
        "cost-measurement experiment\nMIN_NET_EXPECTANCY_R_AFTER_MEASURED_COST = +0.15R\n",
        encoding="utf-8",
    )
    (project / "docs" / "PHASE2_SINGLE_EDGE_RISK_PLAN.md").write_text(
        "single-edge same-family +0.15R observer-only\n",
        encoding="utf-8",
    )
    (project / "docs" / "PHASE2_OPERATIONS_PREP.md").write_text(
        "External Health Monitor Spec\nDisaster Recovery Runbook\nCapital Allocation Ladder\n",
        encoding="utf-8",
    )
    (project / "mt5" / "README.md").write_text("mt5\n", encoding="utf-8")
    (project / "mt5" / "Experts" / "Phase1DryRunShell.mq5").write_text("#property strict\n", encoding="utf-8")
    (project / "mt5" / "Include" / "Phase1" / "Phase1Types.mqh").write_text("#define X\n", encoding="utf-8")
    (project / "mt5" / "Include" / "Phase1" / "Phase1BreakoutRetest.mqh").write_text(
        _mql_parity_tokens(),
        encoding="utf-8",
    )
    (project / "mt5" / "Presets" / "Phase1DryRunShell.safe.set").write_text("InpDryRunOnly=true\n", encoding="utf-8")
    (project / "scripts" / "verify_phase1_logs.py").write_text("print('ok')\n", encoding="utf-8")
    (project / "tests" / "test_phase1_static.py").write_text("def test_ok(): assert True\n", encoding="utf-8")


def _phase2_schema_doc() -> str:
    path = ROOT / "scripts" / "generate_phase2_paper_ledger_schema_report.py"
    spec = importlib.util.spec_from_file_location("phase2_schema_for_bundle_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase2_schema_for_bundle_test"] = module
    spec.loader.exec_module(module)
    columns = "\n".join(f"- {name}" for name, *_ in module.REQUIRED_COLUMNS)
    tokens = "\n".join(f"- {token}" for token in module.REQUIRED_TOKENS)
    return f"# Schema\n\n{columns}\n\n## Controls\n\n{tokens}\n"


def _write_phase0_cost_artifacts(project: Path) -> None:
    phase0_root = project.parent / "xauusd-phase0"
    docs = phase0_root / "docs"
    reports = phase0_root / "outputs" / "reports"
    strategy = phase0_root / "src" / "phase0" / "strategies" / "breakout_retest.py"
    docs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    strategy.parent.mkdir(parents=True, exist_ok=True)
    strategy.write_text(_python_parity_tokens(), encoding="utf-8")
    (docs / "COST_REPORTING_POLICY.md").write_text("# Cost policy\n", encoding="utf-8")
    (docs / "PHASE0_INDEPENDENT_VALIDATION.md").write_text(
        "# Independent validation\n\nCanonical fixed-notional monthly R evidence; compounding variants are superseded.\n",
        encoding="utf-8",
    )
    (docs / "DIVERSIFICATION_AVAILABILITY_FINDING.md").write_text(
        "# Diversification\n\nnon-level candidates tested. single-edge same-family operating frame.\n",
        encoding="utf-8",
    )
    (docs / "HYPOTHESIS_LOCKING.md").write_text(
        (
            "# Locking\n\n"
            "normalized top-trade R ratio\n\n"
            "normalized top-5-trade R ratio\n\n"
            "Pepperstone and Dukascopy cross-venue PF must be >= 1.20\n"
        ),
        encoding="utf-8",
    )
    (docs / "CANDIDATE_RESEARCH_BACKLOG.md").write_text(
        "\n".join(
            [
                "# Backlog",
                "",
                "d1_compression_h4_expansion_v0",
                "h4_real_yield_proxy_momentum_v0",
                "d1_multi_day_exhaustion_reversion_v0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (reports / "FIXED_NOTIONAL_REPORT.md").write_text("# Fixed notional\n\nOverall status: PASS\n", encoding="utf-8")
    (reports / "PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md").write_text(
        "# Concentration\n\nOverall status: PASS\n",
        encoding="utf-8",
    )


def _mql_parity_tokens() -> str:
    return "\n".join(
        [
            "m_break_window_bars = 20;",
            "m_break_atr_multiplier = 0.30;",
            "m_retest_tolerance_points = 5.0;",
            "m_stop_atr_multiplier = 0.10;",
            "m_reward_multiple = 1.50;",
            '"previous_daily_high"; "previous_weekly_high"; "latest_swing_high";',
            '"previous_daily_low"; "previous_weekly_low"; "latest_swing_low";',
            "10.0 * point;",
            "candidate.stop_distance_points < best.stop_distance_points;",
            "BREAKOUT_RETEST_LONG_DRY_RUN;",
        ]
    )


def _python_parity_tokens() -> str:
    return "\n".join(
        [
            "retest_position - 20",
            "0.3 * break_atr",
            "5.0 * point_size",
            "0.1 * retest_atr",
            "1.5 * risk_price",
            '"previous_daily_high"; "previous_weekly_high"; "latest_swing_high";',
            '"previous_daily_low"; "previous_weekly_low"; "latest_swing_low";',
            "10.0 * point_size",
            'item["stop_distance"]',
            "BREAKOUT_RETEST_LONG",
        ]
    )


def _write_runtime_logs(files_dir: Path) -> None:
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")


def _write_startup_log(path: Path) -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "symbol",
        "dry_run_only",
        "magic_namespace_ok",
        "server_time_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for minute in (0, 5):
            writer.writerow(
                {
                    "timestamp_broker": f"2026.05.21 12:{minute:02d}:00",
                    "timestamp_utc": f"2026.05.21 12:{minute:02d}:00",
                    "timestamp_local": f"2026.05.21 16:{minute:02d}:00",
                    "run_id": "phase1-dry-run-v0.4",
                    "symbol": "XAUUSD",
                    "dry_run_only": "true",
                    "magic_namespace_ok": "true",
                    "server_time_status": "CLOCK_OK",
                }
            )


def _write_shutdown_log(path: Path) -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "symbol",
        "shutdown_reason",
        "last_m5_bar_time",
        "last_decision_write_time",
        "lifecycle_state",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "timestamp_broker": "2026.05.21 12:10:00",
                "timestamp_utc": "2026.05.21 12:10:00",
                "timestamp_local": "2026.05.21 16:10:00",
                "run_id": "phase1-dry-run-v0.4",
                "symbol": "XAUUSD",
                "shutdown_reason": "9",
                "last_m5_bar_time": "2026.05.21 12:05:00",
                "last_decision_write_time": "2026.05.21 12:05:01",
                "lifecycle_state": "DRY_RUN",
            }
        )


def _write_decision_log(path: Path) -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "lifecycle_state",
        "symbol",
        "bar_time",
        "session",
        "regime",
        "router_version",
        "risk_state",
        "risk_ok",
        "execution_state",
        "news_state",
        "expert_lifecycle_state",
        "br_lifecycle_state",
        "sbr_lifecycle_state",
        "magic_namespace_ok",
        "server_time_status",
        "br_stage",
        "br_direction",
        "br_would_signal",
        "br_reason_code",
        "br_level_found",
        "br_break_found",
        "br_retest_valid",
        "br_confirmation_valid",
        "br_level_kind",
        "br_level_price",
        "br_entry_price",
        "br_stop_loss",
        "br_take_profit",
        "br_stop_distance_points",
        "br_break_shift",
        "sbr_stage",
        "sbr_direction",
        "sbr_would_signal",
        "sbr_reason_code",
        "sbr_level_found",
        "sbr_break_found",
        "sbr_retest_valid",
        "sbr_confirmation_valid",
        "sbr_level_kind",
        "sbr_level_price",
        "sbr_entry_price",
        "sbr_stop_loss",
        "sbr_take_profit",
        "sbr_stop_distance_points",
        "sbr_break_shift",
        "allowed_expert",
        "would_have_allowed_experts",
        "trade_permission",
        "block_reason",
        "dry_run",
    ]
    rows = [
        {
            "timestamp_broker": "2026.05.21 12:00:00",
            "timestamp_utc": "2026.05.21 12:00:00",
            "timestamp_local": "2026.05.21 16:00:00",
            "run_id": "phase1-dry-run-v0.4",
            "lifecycle_state": "DRY_RUN",
            "symbol": "XAUUSD",
            "bar_time": "2026.05.21 12:00:00",
            "session": "LONDON",
            "regime": "BREAKOUT_RETEST",
            "router_version": "phase1_router_v0.4",
            "risk_state": "NORMAL",
            "risk_ok": "true",
            "execution_state": "EXECUTION_OK",
            "news_state": "NO_NEWS_RISK",
            "expert_lifecycle_state": "DRY_RUN_ONLY",
            "magic_namespace_ok": "true",
            "server_time_status": "CLOCK_OK",
            "br_stage": "WAIT_LEVEL_BREAK_RETEST",
            "br_direction": "LONG",
            "br_would_signal": "false",
            "br_reason_code": "no_long_breakout_retest_candidate",
            "allowed_expert": "none",
            "would_have_allowed_experts": "breakout_retest;swing_breakout_retest_v0",
            "trade_permission": "false",
            "block_reason": "phase1_dry_run_only",
            "dry_run": "true",
        },
        {
            "timestamp_broker": "2026.05.21 12:05:00",
            "timestamp_utc": "2026.05.21 12:05:00",
            "timestamp_local": "2026.05.21 16:05:00",
            "run_id": "phase1-dry-run-v0.4-daily-lock-test",
            "lifecycle_state": "DRY_RUN",
            "symbol": "XAUUSD",
            "bar_time": "2026.05.21 12:05:00",
            "session": "LONDON",
            "regime": "BREAKOUT_RETEST",
            "router_version": "phase1_router_v0.4",
            "risk_state": "LOCKED_DAILY_LOSS",
            "risk_ok": "false",
            "execution_state": "EXECUTION_OK",
            "news_state": "NO_NEWS_RISK",
            "expert_lifecycle_state": "DRY_RUN_ONLY",
            "magic_namespace_ok": "true",
            "server_time_status": "CLOCK_OK",
            "br_stage": "WAIT_LEVEL_BREAK_RETEST",
            "br_direction": "LONG",
            "br_would_signal": "false",
            "br_reason_code": "no_long_breakout_retest_candidate",
            "allowed_expert": "none",
            "would_have_allowed_experts": "breakout_retest;swing_breakout_retest_v0",
            "trade_permission": "false",
            "block_reason": "LOCKED_DAILY_LOSS",
            "dry_run": "true",
        },
        {
            "timestamp_broker": "2026.05.21 12:10:00",
            "timestamp_utc": "2026.05.21 12:10:00",
            "timestamp_local": "2026.05.21 16:10:00",
            "run_id": "phase1-dry-run-v0.4-weekly-lock-test",
            "lifecycle_state": "DRY_RUN",
            "symbol": "XAUUSD",
            "bar_time": "2026.05.21 12:10:00",
            "session": "LONDON",
            "regime": "BREAKOUT_RETEST",
            "router_version": "phase1_router_v0.4",
            "risk_state": "LOCKED_WEEKLY_LOSS",
            "risk_ok": "false",
            "execution_state": "EXECUTION_OK",
            "news_state": "NO_NEWS_RISK",
            "expert_lifecycle_state": "DRY_RUN_ONLY",
            "magic_namespace_ok": "true",
            "server_time_status": "CLOCK_OK",
            "br_stage": "WAIT_LEVEL_BREAK_RETEST",
            "br_direction": "LONG",
            "br_would_signal": "false",
            "br_reason_code": "no_long_breakout_retest_candidate",
            "allowed_expert": "none",
            "would_have_allowed_experts": "breakout_retest;swing_breakout_retest_v0",
            "trade_permission": "false",
            "block_reason": "LOCKED_WEEKLY_LOSS",
            "dry_run": "true",
        },
        {
            "timestamp_broker": "2026.05.21 12:15:00",
            "timestamp_utc": "2026.05.21 12:15:00",
            "timestamp_local": "2026.05.21 16:15:00",
            "run_id": "phase1-dry-run-v0.4-monthly-lock-test",
            "lifecycle_state": "DRY_RUN",
            "symbol": "XAUUSD",
            "bar_time": "2026.05.21 12:15:00",
            "session": "LONDON",
            "regime": "BREAKOUT_RETEST",
            "router_version": "phase1_router_v0.4",
            "risk_state": "LOCKED_MONTHLY_LOSS",
            "risk_ok": "false",
            "execution_state": "EXECUTION_OK",
            "news_state": "NO_NEWS_RISK",
            "expert_lifecycle_state": "DRY_RUN_ONLY",
            "magic_namespace_ok": "true",
            "server_time_status": "CLOCK_OK",
            "br_stage": "WAIT_LEVEL_BREAK_RETEST",
            "br_direction": "LONG",
            "br_would_signal": "false",
            "br_reason_code": "no_long_breakout_retest_candidate",
            "allowed_expert": "none",
            "would_have_allowed_experts": "breakout_retest;swing_breakout_retest_v0",
            "trade_permission": "false",
            "block_reason": "LOCKED_MONTHLY_LOSS",
            "dry_run": "true",
        },
        {
            "timestamp_broker": "2026.05.21 12:20:00",
            "timestamp_utc": "2026.05.21 12:20:00",
            "timestamp_local": "2026.05.21 16:20:00",
            "run_id": "phase1-dry-run-v0.4-manual-lock-test",
            "lifecycle_state": "DRY_RUN",
            "symbol": "XAUUSD",
            "bar_time": "2026.05.21 12:20:00",
            "session": "LONDON",
            "regime": "BREAKOUT_RETEST",
            "router_version": "phase1_router_v0.4",
            "risk_state": "MANUAL_LOCK",
            "risk_ok": "false",
            "execution_state": "EXECUTION_OK",
            "news_state": "NO_NEWS_RISK",
            "expert_lifecycle_state": "DRY_RUN_ONLY",
            "magic_namespace_ok": "true",
            "server_time_status": "CLOCK_OK",
            "br_stage": "WAIT_LEVEL_BREAK_RETEST",
            "br_direction": "LONG",
            "br_would_signal": "false",
            "br_reason_code": "no_long_breakout_retest_candidate",
            "allowed_expert": "none",
            "would_have_allowed_experts": "breakout_retest;swing_breakout_retest_v0",
            "trade_permission": "false",
            "block_reason": "MANUAL_LOCK",
            "dry_run": "true",
        },
    ]
    for row in rows:
        row.update(
            {
                "br_level_found": "true",
                "br_lifecycle_state": "DRY_RUN_ONLY",
                "br_break_found": "false",
                "br_retest_valid": "false",
                "br_confirmation_valid": "false",
                "br_level_kind": "D1_HIGH",
                "br_level_price": "4505.00",
                "br_entry_price": "0.00",
                "br_stop_loss": "0.00",
                "br_take_profit": "0.00",
                "br_stop_distance_points": "0.00",
                "br_break_shift": "-1",
                "sbr_stage": "WAIT_LEVEL_BREAK_RETEST",
                "sbr_lifecycle_state": "DRY_RUN_ONLY",
                "sbr_direction": "LONG",
                "sbr_would_signal": "false",
                "sbr_reason_code": "no_long_swing_breakout_retest_candidate",
                "sbr_level_found": "true",
                "sbr_break_found": "false",
                "sbr_retest_valid": "false",
                "sbr_confirmation_valid": "false",
                "sbr_level_kind": "latest_swing_high",
                "sbr_level_price": "4505.00",
                "sbr_entry_price": "0.00",
                "sbr_stop_loss": "0.00",
                "sbr_take_profit": "0.00",
                "sbr_stop_distance_points": "0.00",
                "sbr_break_shift": "-1",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
