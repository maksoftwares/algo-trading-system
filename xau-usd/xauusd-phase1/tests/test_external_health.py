from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from scripts.check_phase1_external_health import check_external_health


def test_external_health_passes_with_fresh_dry_run_row(tmp_path: Path):
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "decision_log.csv").write_text(
        "timestamp_local,dry_run,trade_permission,server_time_status\n"
        "2026.05.22 03:30:00,true,false,CLOCK_OK\n",
        encoding="utf-8",
    )
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "status": {
                    "log_verification": "PASS",
                    "soak_analysis": "PASS",
                    "runtime_health": "PASS",
                    "would_signal": "PASS",
                    "acceptance": "PENDING",
                }
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "health.json"

    output = check_external_health(
        files_dir=files_dir,
        status_summary=summary,
        output_path=output_path,
        now=datetime(2026, 5, 22, 3, 35, 0),
        max_fresh_minutes=15,
    )

    assert output.status == "PASS"
    assert output_path.exists()


def test_external_health_fails_stale_row(tmp_path: Path):
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "decision_log.csv").write_text(
        "timestamp_local,dry_run,trade_permission,server_time_status\n"
        "2026.05.22 03:00:00,true,false,CLOCK_OK\n",
        encoding="utf-8",
    )
    summary = tmp_path / "summary.json"
    summary.write_text(json.dumps({"status": {"runtime_health": "PASS"}}), encoding="utf-8")

    output = check_external_health(
        files_dir=files_dir,
        status_summary=summary,
        now=datetime(2026, 5, 22, 3, 35, 0),
        max_fresh_minutes=15,
    )

    assert output.status == "FAIL"
