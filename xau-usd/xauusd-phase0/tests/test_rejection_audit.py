from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from phase0.cli import main
from phase0.config import ProjectConfig
from phase0.rejection_audit import generate_rejection_gate_audit


def test_generate_rejection_gate_audit_classifies_frequency_and_edge(tmp_path: Path):
    _write_candidate(tmp_path, "breakout_retest", trade_count=100, profit_factor=1.6)
    _write_candidate(tmp_path, "low_frequency_candidate", trade_count=10, profit_factor=1.6)
    _write_candidate(tmp_path, "negative_expectancy_candidate", trade_count=100, profit_factor=0.8)
    config = ProjectConfig(tmp_path, {"gates": _gates()}, {}, {}, {}, {})

    output = generate_rejection_gate_audit(config)

    assert output.audited_candidates == 3
    assert output.rejected_candidates == 2
    assert output.sample_size_failure_candidates == 1
    assert output.edge_expectancy_failure_candidates == 1
    summary = pd.read_csv(output.summary_path)
    by_candidate = summary.set_index("candidate")
    assert by_candidate.loc["low_frequency_candidate", "frequency_bias_diagnosis"] == "FREQUENCY_FAILURE"
    assert by_candidate.loc["negative_expectancy_candidate", "frequency_bias_diagnosis"] == "EDGE_EXPECTANCY_FAILURE"
    assert "Review #3 V3" in output.report_path.read_text(encoding="utf-8")


def test_generate_rejection_gate_audit_cli(project_root: Path, tmp_path: Path, capsys):
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    _write_candidate(root, "breakout_retest", trade_count=100, profit_factor=1.6)
    _write_candidate(root, "candidate_a", trade_count=5, profit_factor=0.9)

    exit_code = main(["--root", str(root), "generate-rejection-gate-audit"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Rejected-candidate gate audit generated" in captured.out
    assert (root / "outputs" / "reports" / "PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md").exists()


def _write_candidate(root: Path, expert: str, trade_count: int, profit_factor: float) -> None:
    expert_dir = root / "outputs" / "matrix_results" / expert
    expert_dir.mkdir(parents=True)
    for cell_id in range(1, 10):
        pd.DataFrame(
            [
                {
                    "expert": expert,
                    "cell_id": cell_id,
                    "profit_factor": profit_factor,
                    "trade_count": trade_count,
                    "max_drawdown_pct": 5.0,
                    "total_return_pct": 10.0,
                    "largest_single_trade_pct_of_pnl": 5.0,
                    "top5_trades_pct_of_pnl": 20.0,
                    "max_consecutive_zero_trade_months": 0,
                }
            ]
        ).to_csv(expert_dir / f"cell_{cell_id}_{expert}.csv", index=False)


def _gates() -> dict[str, float | int]:
    return {
        "total_cells": 9,
        "min_cells_pf_pass": 7,
        "min_pf_per_passing_cell": 1.30,
        "min_trades_every_cell": 40,
        "max_drawdown_pct_every_cell": 30.0,
        "min_total_return_pct_every_cell": -25.0,
        "max_largest_trade_pnl_share_pct": 10.0,
        "max_top5_trades_pnl_share_pct": 40.0,
        "max_consecutive_zero_trade_months": 3,
        "min_p95_to_best_pf_ratio": 0.50,
    }
