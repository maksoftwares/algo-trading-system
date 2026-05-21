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
