from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from phase0.config import ProjectConfig
from phase0.reality_check import _block_bootstrap_indices, run_reality_check


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
