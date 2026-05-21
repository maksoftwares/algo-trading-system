from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from phase0.adversarial import ADVERSARIAL_COLUMNS, create_adversarial_packets, score_adversarial_review
from phase0.cli import main
from phase0.config import load_project_config
from phase0.deciles import DECILE_COLUMNS, run_decile_tests
from phase0.hashing import register_hypotheses
from phase0.matrix import run_phase0_matrix
from phase0.multisymbol import MULTISYMBOL_SUMMARY_COLUMNS, run_multisymbol_checks


def test_run_decile_tests_synthetic_writes_schema(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)

    outputs = run_decile_tests(config, "trend_pullback", synthetic_sample=True)

    assert len(outputs) == 1
    frame = pd.read_csv(outputs[0].results_path)
    assert list(frame.columns) == list(DECILE_COLUMNS)
    assert frame["decile_id"].tolist() == list(range(1, 11))


def test_run_multisymbol_checks_synthetic_writes_schema(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)

    outputs = run_multisymbol_checks(config, "breakout_retest", synthetic_sample=True)

    assert len(outputs) == 1
    summary = pd.read_csv(outputs[0].summary_path)
    assert list(summary.columns) == list(MULTISYMBOL_SUMMARY_COLUMNS)
    assert summary["symbol"].tolist() == ["EURUSD", "USDJPY"]
    assert all(path.exists() for path in outputs[0].trades_paths)


def test_create_adversarial_packets_writes_schema(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    run_phase0_matrix(config, "range_mr", synthetic_sample=True)

    outputs = create_adversarial_packets(config, "range_mr")

    assert len(outputs) == 1
    frame = pd.read_csv(outputs[0].review_path)
    assert list(frame.columns) == list(ADVERSARIAL_COLUMNS)


def test_score_adversarial_review_writes_score(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    output_dir = root / "outputs" / "adversarial_review"
    output_dir.mkdir(parents=True)
    rows = [
        _adversarial_row("breakout_retest-cell1-1", "LOGIC_GAP"),
        _adversarial_row("breakout_retest-cell1-2", "VALID_LOSS"),
    ]
    pd.DataFrame(rows, columns=ADVERSARIAL_COLUMNS).to_csv(
        output_dir / "breakout_retest_losing_trades_review.csv",
        index=False,
    )

    outputs = score_adversarial_review(config, "breakout_retest")

    assert len(outputs) == 1
    assert outputs[0].status == "FAIL"
    assert outputs[0].logic_gap_failures_pct == 50.0
    assert outputs[0].score_path.exists()


def test_run_deciles_cli(project_root, tmp_path, capsys):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)

    exit_code = main(
        [
            "--root",
            str(root),
            "run-deciles",
            "--expert",
            "trend_pullback",
            "--synthetic-sample",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Decile tests complete: 1 expert result file" in captured.out


def _copy_minimal_project(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    shutil.copytree(project_root / "docs", root / "docs")
    (root / "outputs" / "hashes").mkdir(parents=True)
    return root


def _adversarial_row(trade_id: str, failure_class: str) -> dict[str, object]:
    row = {column: "" for column in ADVERSARIAL_COLUMNS}
    row.update(
        {
            "trade_id": trade_id,
            "expert": "breakout_retest",
            "cell_id": 1,
            "symbol": "XAUUSD",
            "broker": "capital_com",
            "cost_model": "median",
            "entry_time_utc": "2016-01-04T10:00:00+00:00",
            "exit_time_utc": "2016-01-04T10:10:00+00:00",
            "direction": "LONG",
            "net_pnl": -10.0,
            "r_multiple": -1.0,
            "manual_failure_class": failure_class,
            "manual_notes": "reviewed",
            "reviewer": "tester",
            "reviewed_at_utc": "2026-05-21T00:00:00+00:00",
        }
    )
    return row
