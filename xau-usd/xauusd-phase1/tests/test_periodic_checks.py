from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from scripts.run_phase1_periodic_checks import PeriodicCheckOutput


def test_periodic_check_output_shape(tmp_path: Path):
    output = PeriodicCheckOutput(
        status="PASS",
        status_summary_path=tmp_path / "summary.json",
        external_health_path=tmp_path / "health.json",
        soak_history_rows=3,
        acceptance_status="PENDING",
        phase2_readiness_status="PENDING",
        phase2_demo_preflight_status="PENDING",
        phase2_owner_action_status="WAITING_AND_OWNER_ACTION_REQUIRED",
        phase2_vps_bootstrap_status="WAITING_AND_VPS_BOOTSTRAP_PENDING",
        vps_first_day_status="PENDING",
        review_index_status="PENDING",
    )

    assert output.status == "PASS"
    assert output.soak_history_rows == 3


def test_periodic_imports_do_not_shadow_csv_datetime():
    assert csv.excel.delimiter == ","
    assert datetime(2026, 5, 22).year == 2026


def test_periodic_checks_support_separate_spread_log_directory():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "--spread-files-dir" in script
    assert "input_dir=spread_files_dir" in script
    assert "SPREAD_LOG_FRESHNESS_SCHEMA_WARNING.md" in script


def test_periodic_checks_break_phase1_phase2_report_cycle():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "include_phase2_readiness=False" in script


def test_periodic_checks_generate_observer_parity_before_phase2_readiness():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "generate_phase1_observer_parity_report" in script
    assert script.index("generate_phase1_observer_parity_report") < script.index("generate_phase2_readiness_report")


def test_periodic_checks_regenerate_single_status_page():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "generate_project_status_page" in script
    assert "status.html" in script


def test_periodic_checks_generate_demo_countdown_after_phase2_readiness():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "generate_phase2_demo_countdown_report" in script
    assert script.index("phase2_readiness = generate_phase2_readiness_report") < script.index(
        "generate_phase2_demo_countdown_report(root=root)"
    )


def test_periodic_checks_generate_demo_preflight_after_countdown():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "generate_phase2_demo_preflight_report" in script
    assert script.index("generate_phase2_demo_countdown_report(root=root)") < script.index(
        "phase2_preflight = generate_phase2_demo_preflight_report(root=root)"
    )


def test_periodic_checks_generate_owner_action_packet_after_preflight():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "generate_phase2_owner_action_packet" in script
    assert script.index("phase2_preflight = generate_phase2_demo_preflight_report(root=root)") < script.index(
        "owner_action_packet = generate_phase2_owner_action_packet(root=root)"
    )


def test_periodic_checks_generate_vps_bootstrap_after_owner_action_packet():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "generate_phase2_vps_bootstrap_packet" in script
    assert script.index("owner_action_packet = generate_phase2_owner_action_packet(root=root)") < script.index(
        "vps_bootstrap_packet = generate_phase2_vps_bootstrap_packet(root=root)"
    )


def test_periodic_checks_generate_vps_first_day_before_phase2_readiness():
    script = Path("scripts/run_phase1_periodic_checks.py").read_text(encoding="utf-8")

    assert "generate_phase2_vps_first_day_verification" in script
    assert script.index("generate_phase2_vps_first_day_verification") < script.index(
        "phase2_readiness = generate_phase2_readiness_report"
    )
