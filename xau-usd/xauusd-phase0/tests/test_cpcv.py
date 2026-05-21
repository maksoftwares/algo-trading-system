from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from phase0.config import ProjectConfig
from phase0.cpcv import _assign_chronological_folds, _profit_factor, run_cpcv_validation


def test_assign_chronological_folds_covers_requested_folds():
    folds = _assign_chronological_folds(row_count=12, folds=6)

    assert folds == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]


def test_profit_factor_handles_zero_loss_cases():
    assert math.isinf(_profit_factor(10.0, 0.0))
    assert _profit_factor(0.0, 0.0) == 0.0
    assert _profit_factor(9.0, 3.0) == 3.0


def test_run_cpcv_validation_writes_report(tmp_path: Path):
    expert_dir = tmp_path / "outputs" / "matrix_results" / "breakout_retest"
    expert_dir.mkdir(parents=True)
    summary_path = expert_dir / "cell_1_breakout_retest_capital_com_median.csv"
    trades_path = expert_dir / "cell_1_breakout_retest_capital_com_median_trades.csv"
    summary_path.write_text(
        "expert,broker,cost_model,symbol,cell_id\n"
        "breakout_retest,capital_com,median,XAUUSD,1\n",
        encoding="utf-8",
    )
    rows = []
    start = pd.Timestamp("2024-01-01T00:00:00Z")
    for index in range(60):
        pnl = 2.0 if index % 3 else -1.0
        rows.append(
            {
                "entry_time_utc": (start + pd.Timedelta(hours=index)).isoformat(),
                "exit_time_utc": (start + pd.Timedelta(hours=index, minutes=30)).isoformat(),
                "net_pnl_usd": pnl,
            }
        )
    pd.DataFrame(rows).to_csv(trades_path, index=False)
    config = ProjectConfig(tmp_path, {}, {}, {}, {}, {})

    output = run_cpcv_validation(
        config,
        expert="breakout_retest",
        folds=5,
        test_fold_count=1,
        purge_days=0.0,
        min_oos_profit_factor=1.0,
        min_median_oos_profit_factor=1.0,
        min_oos_trades=5,
    )

    assert output.status == "PASS"
    assert output.report_path.exists()
    assert output.paths_path.exists()
    assert output.manifest_path.exists()
