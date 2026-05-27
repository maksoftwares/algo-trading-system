from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from phase0.config import ProjectConfig
from phase0.reality_check import (
    _block_bootstrap_indices,
    run_family_clustered_reality_check,
    run_reality_check,
)


def test_block_bootstrap_indices_preserve_length():
    rng = np.random.default_rng(123)

    indices = _block_bootstrap_indices(length=10, block_months=3, rng=rng)

    assert len(indices) == 10
    assert indices.min() >= 0
    assert indices.max() < 10


def test_run_reality_check_writes_report(tmp_path: Path):
    matrix_root = tmp_path / "outputs" / "matrix_results"
    for expert, positive in (("breakout_retest", True), ("range_mr", False)):
        expert_dir = matrix_root / expert
        expert_dir.mkdir(parents=True)
        rows = []
        start = pd.Timestamp("2024-01-01T00:00:00Z")
        for month in range(18):
            pnl = 100.0 if positive else -10.0
            rows.append(
                {
                    "entry_time_utc": (start + pd.DateOffset(months=month)).isoformat(),
                    "net_pnl_usd": pnl,
                }
            )
        pd.DataFrame(rows).to_csv(expert_dir / f"cell_1_{expert}_trades.csv", index=False)
    config = ProjectConfig(tmp_path, {}, {}, {}, {}, {})

    output = run_reality_check(
        config,
        approved_expert="breakout_retest",
        iterations=200,
        block_months=2,
        max_pvalue=0.10,
        seed=42,
    )

    assert output.status == "PASS"
    assert output.winner == "breakout_retest"
    assert output.report_path.exists()
    assert output.summary_path.exists()
    assert output.manifest_path.exists()


def test_run_family_clustered_reality_check_excludes_same_family_variants(tmp_path: Path):
    matrix_root = tmp_path / "outputs" / "matrix_results"
    experts = {
        "breakout_retest": 100.0,
        "round_number_retest_v0": 99.0,
        "range_mr": -10.0,
    }
    start = pd.Timestamp("2024-01-01T00:00:00Z")
    for expert, pnl in experts.items():
        expert_dir = matrix_root / expert
        expert_dir.mkdir(parents=True)
        rows = [
            {
                "entry_time_utc": (start + pd.DateOffset(months=month)).isoformat(),
                "net_pnl_usd": pnl,
            }
            for month in range(18)
        ]
        pd.DataFrame(rows).to_csv(expert_dir / f"cell_1_{expert}_trades.csv", index=False)
    config = ProjectConfig(tmp_path, {}, {}, {}, {}, {})

    output = run_family_clustered_reality_check(
        config,
        approved_expert="breakout_retest",
        iterations=200,
        block_months=2,
        max_pvalue=0.10,
        seed=42,
    )

    assert output.status == "PASS_REVIEW_REQUIRED"
    assert output.winner_family == "breakout_retest_family"
    assert output.report_path.exists()
    assert output.assignments_path.exists()
    assert output.manifest_path.exists()

    assignments = pd.read_csv(output.assignments_path)
    round_row = assignments.loc[assignments["expert"] == "round_number_retest_v0"].iloc[0]
    assert round_row["family"] == "breakout_retest_family"
    assert str(round_row["included_in_family_panel"]).lower() == "false"
    assert round_row["role"] == "same_family_excluded_from_pairwise_spa"

    report_text = output.report_path.read_text(encoding="utf-8")
    assert "This report does not modify `PHASE0_REALITY_CHECK.md`." in report_text
    assert "round_number_retest_v0" in report_text
