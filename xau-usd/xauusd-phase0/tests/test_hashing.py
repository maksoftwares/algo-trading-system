from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from phase0.cli import main
from phase0.config import load_project_config
from phase0.hashing import (
    HashingError,
    hash_manifest_path,
    register_hypotheses,
    validate_hypotheses,
    validate_hypotheses_complete,
)


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


def test_validate_hypotheses_complete_rejects_placeholders(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    _write_placeholder_hypothesis(root / "docs" / "hypothesis_breakout_retest.md")
    config = load_project_config(root)
    register_hypotheses(config)

    with pytest.raises(HashingError, match="placeholder text remains"):
        validate_hypotheses_complete(config)


def test_validate_hypotheses_complete_passes_completed_files(project_root, tmp_path):
    root = _copy_minimal_project(project_root, tmp_path)
    _write_complete_hypotheses(root)
    config = load_project_config(root)
    register_hypotheses(config)

    assert validate_hypotheses_complete(config) is True


def test_validate_hypotheses_complete_cli_fails_placeholders(project_root, tmp_path, capsys):
    root = _copy_minimal_project(project_root, tmp_path)
    _write_placeholder_hypothesis(root / "docs" / "hypothesis_breakout_retest.md")
    config = load_project_config(root)
    register_hypotheses(config)

    with pytest.raises(SystemExit):
        main(["--root", str(root), "validate-hypotheses-complete"])

    captured = capsys.readouterr()
    assert "Hypothesis pre-registration is incomplete" in captured.err


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


def _write_complete_hypotheses(root: Path) -> None:
    for filename, expert_name in (
        ("hypothesis_trend_pullback.md", "Trend Pullback"),
        ("hypothesis_breakout_retest.md", "Breakout-Retest"),
        ("hypothesis_range_mr.md", "Range Mean-Reversion"),
    ):
        (root / "docs" / filename).write_text(
            f"""# Hypothesis: {expert_name} Expert

Expert name: {expert_name}
Hypothesis date: 2026-05-21
Hypothesis version: v1.0
Author / owner: Phase 0 research desk

## Mechanical Definition

The expert has a fixed mechanical signal definition implemented in src/phase0/strategies.
It uses only completed bars, fixed risk controls, and the configured Phase 0 cost model.

## Expected Behavior

Expected trade count per year: 200 +/- 20%

Expected cost-adjusted PF: 1.30 +/- 0.3

Expected losing-month percentage: 35% +/- 10%

Expected worst single month: -8% equity

Expected max consecutive zero months: 1

Expected R-multiple distribution: median near -1R with positive right-tail winners.

## Why This Hypothesis Should Exist

The market behavior is expected to persist because the setup captures repeated liquidity
retests around visible levels while applying adverse-first execution assumptions.

## What Would Falsify It

The hypothesis is falsified by insufficient multi-cell survival, excess drawdown,
unstable deciles, weak multisymbol checks, or excessive adversarial logic gaps.
""",
            encoding="utf-8",
        )


def _write_placeholder_hypothesis(path: Path) -> None:
    path.write_text(
        """# Hypothesis: Breakout-Retest Expert

Expert name: Breakout-Retest
Hypothesis date: TBD
Hypothesis version: v1.0
Author / owner: TBD

## Mechanical Definition

TBD before any result-producing backtest.

## Expected Behavior

Expected trade count per year: TBD +/- 20%

Expected cost-adjusted PF: TBD +/- 0.3

Expected losing-month percentage: TBD +/- 10%

Expected worst single month: TBD

Expected max consecutive zero months: TBD

Expected R-multiple distribution: TBD

## Why This Hypothesis Should Exist

TBD before hash registration.

## What Would Falsify It

TBD before hash registration.
""",
        encoding="utf-8",
    )
