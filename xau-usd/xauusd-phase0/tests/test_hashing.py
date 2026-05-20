from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from phase0.cli import main
from phase0.config import load_project_config
from phase0.hashing import HashingError, hash_manifest_path, register_hypotheses, validate_hypotheses


def test_register_and_validate_hypotheses(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)

    rows = register_hypotheses(config)

    assert len(rows) == 3
    assert hash_manifest_path(config).exists()
    assert validate_hypotheses(config) is True


def test_hash_mismatch_fails(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)

    hypothesis = root / "docs" / "hypothesis_trend_pullback.md"
    hypothesis.write_text(hypothesis.read_text(encoding="utf-8") + "\nChanged after registration.\n")

    with pytest.raises(HashingError, match="changed after registration"):
        validate_hypotheses(config)


def test_hash_cli_registers(project_root, tmp_path, capsys):
    root = _copy_minimal_project(project_root, tmp_path)

    exit_code = main(["--root", str(root), "hash-hypotheses", "--register"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Registered 3 hypothesis hash" in captured.out
    assert (root / "outputs" / "hashes" / "hypothesis_hash_manifest.csv").exists()


def _copy_minimal_project(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    (root / "docs").mkdir(parents=True)
    for name in (
        "hypothesis_trend_pullback.md",
        "hypothesis_breakout_retest.md",
        "hypothesis_range_mr.md",
    ):
        shutil.copy2(project_root / "docs" / name, root / "docs" / name)
    (root / "outputs" / "hashes").mkdir(parents=True)
    return root
