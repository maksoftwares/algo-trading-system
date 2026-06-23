from __future__ import annotations

import py_compile
from pathlib import Path

from phase2x_test_helpers import ROOT


TEXT_INTEGRITY_PATHS = [
    ROOT / "docs" / "A3_ML_DATA_CONTRACT_V1.md",
    ROOT / "docs" / "A3_ML_META_LABEL_HYPOTHESIS_V1.md",
    ROOT / "docs" / "A3_ML_SHADOW_GOVERNANCE_V1.md",
    ROOT / "docs" / "A3_ML_REPLAY_PROMOTION_POLICY_V1.md",
    ROOT / "docs" / "A3_ML_EXECUTION_LABEL_CONTRACT_V1.md",
    ROOT / "docs" / "A3_ML_COMMIT_1_CONTRACT_MERGE_REPORT.md",
    ROOT / "tests" / "test_a3_ml_contracts.py",
    ROOT / "tests" / "test_a3_ml_shadow_safety.py",
    ROOT / "tests" / "test_a3_ml_fold_diagnostics.py",
    ROOT / "scripts" / "generate_a3_ml_c01_pipeline.py",
    ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5",
    ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoRepairExecutor.mq5",
    ROOT / "mt5" / "Experts" / "A3MlPredictionObserver.mq5",
    ROOT / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh",
    ROOT / "mt5" / "Include" / "A3MlEaHandoff.mqh",
    ROOT / "mt5" / "Include" / "A3MlShadowTap.mqh",
]

PYTHON_SYNTAX_ROOTS = [
    ROOT / "ml" / "a3_meta_v1",
    ROOT / "scripts",
    ROOT / "tests",
]


def test_a3_ml_critical_text_files_are_not_truncated_or_nul_padded() -> None:
    for path in TEXT_INTEGRITY_PATHS:
        data = path.read_bytes()
        assert b"\x00" not in data, f"{path} contains NUL bytes"
        assert data.endswith(b"\n"), f"{path} is missing a final newline"


def test_a3_ml_python_sources_compile() -> None:
    for path in _a3_ml_python_paths():
        py_compile.compile(str(path), doraise=True)


def _a3_ml_python_paths() -> list[Path]:
    paths: set[Path] = set()
    for root in PYTHON_SYNTAX_ROOTS:
        if not root.exists():
            continue
        if root.name == "scripts":
            paths.update(root.glob("c[0-9][0-9]_*.py"))
            paths.add(root / "generate_a3_ml_c01_pipeline.py")
            paths.add(root / "generate_a3_ml_c02_read_only_boundary_report.py")
        elif root.name == "tests":
            paths.update(root.glob("test_a3_ml*.py"))
        else:
            paths.update(root.rglob("*.py"))
    return sorted(path for path in paths if path.exists())
