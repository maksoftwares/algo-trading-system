from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from phase0.adversarial import ADVERSARIAL_COLUMNS, create_adversarial_packets
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
