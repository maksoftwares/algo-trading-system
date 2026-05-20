from __future__ import annotations

import shutil
from pathlib import Path

from phase0.cli import main
from phase0.config import load_project_config
from phase0.hashing import register_hypotheses
from phase0.matrix import run_phase0_matrix
from phase0.reports import generate_all_reports


def test_generate_all_reports_from_synthetic_matrix(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    run_phase0_matrix(config, "all", synthetic_sample=True)

    output = generate_all_reports(config)

    assert len(output.expert_reports) == 3
    assert output.verdict_path.exists()
    verdict = output.verdict_path.read_text(encoding="utf-8")
    assert "| Expert | 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis-match | FINAL |" in verdict
    assert "Stop before Phase 1" in verdict

    report = root / "outputs" / "reports" / "phase0_trend_pullback_results.md"
    text = report.read_text(encoding="utf-8")
    assert "## Hypothesis" in text
    assert "## 9-Cell Matrix Results" in text
    assert "## Hypothesis vs Reality" in text
    assert "| 9-cell | Decile | Adversarial | Multi-symbol | Hypothesis-match | FINAL |" in text
    assert "| sample_size | FAIL |" in text


def test_generate_verdict_cli(project_root, tmp_path, capsys):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    run_phase0_matrix(config, "all", synthetic_sample=True)

    exit_code = main(["--root", str(root), "generate-verdict"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Generated 3 expert report" in captured.out
    assert (root / "outputs" / "reports" / "PHASE0_VERDICT.md").exists()


def _copy_minimal_project(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    shutil.copytree(project_root / "docs", root / "docs")
    (root / "outputs" / "hashes").mkdir(parents=True)
    return root
