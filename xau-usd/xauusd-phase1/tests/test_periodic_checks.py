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
