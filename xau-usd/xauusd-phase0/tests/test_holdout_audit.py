from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from phase0.config import load_project_config
from phase0.holdout_audit import audit_true_holdout


def test_holdout_audit_passes_when_results_stop_before_reserved_window(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    _write_result_csv(root, "2025-06-30T23:55:00+00:00")
    config = load_project_config(root)

    output = audit_true_holdout(config)

    assert output.status == "PASS"
    assert output.report_path.exists()
    assert output.manifest_path.exists()
    assert any(check.name == "result_rows_exclude_holdout" and check.status == "PASS" for check in output.checks)


def test_holdout_audit_fails_when_result_rows_reach_reserved_window(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    _write_result_csv(root, "2025-07-01T00:05:00+00:00")
    config = load_project_config(root)

    output = audit_true_holdout(config)

    assert output.status == "FAIL"
    assert any(check.name == "result_rows_exclude_holdout" and check.status == "FAIL" for check in output.checks)


def _copy_project_shell(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    return root


def _write_result_csv(root: Path, exit_time: str) -> None:
    output_dir = root / "outputs" / "matrix_results" / "breakout_retest"
    output_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "expert": "breakout_retest",
                "entry_time_utc": "2025-06-30T23:50:00+00:00",
                "exit_time_utc": exit_time,
                "net_pnl_usd": 10.0,
            }
        ]
    ).to_csv(output_dir / "sample_trades.csv", index=False)
