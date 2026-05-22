from __future__ import annotations

import shutil
from pathlib import Path

from phase0.config import load_project_config
from phase0.mt5_deployment import check_passive_spread_logger_deployment


def test_passive_spread_logger_deployment_pending_until_logs_exist(project_root: Path, tmp_path: Path):
    root = _copy_config(project_root, tmp_path)
    mt5_root = tmp_path / "mt5"
    _write_deployment(mt5_root)
    config = load_project_config(root)

    output = check_passive_spread_logger_deployment(config, mt5_root)

    assert output.status == "PENDING"
    assert output.spread_log_count == 0
    assert "Overall status: PENDING" in output.report_path.read_text(encoding="utf-8")


def test_passive_spread_logger_deployment_passes_with_log_file(project_root: Path, tmp_path: Path):
    root = _copy_config(project_root, tmp_path)
    mt5_root = tmp_path / "mt5"
    _write_deployment(mt5_root)
    files = mt5_root / "MQL5" / "Files"
    files.mkdir(parents=True)
    (files / "spread_log_123_demo_XAUUSD_20260522.csv").write_text("header\n", encoding="utf-8")
    config = load_project_config(root)

    output = check_passive_spread_logger_deployment(config, mt5_root)

    assert output.status == "PASS"
    assert output.spread_log_count == 1


def _write_deployment(mt5_root: Path) -> None:
    expert_dir = mt5_root / "MQL5" / "Experts" / "Phase0"
    preset_dir = mt5_root / "MQL5" / "Presets"
    expert_dir.mkdir(parents=True)
    preset_dir.mkdir(parents=True)
    (expert_dir / "PassiveSpreadLogger_XAUUSD.mq5").write_text("source\n", encoding="utf-8")
    (expert_dir / "PassiveSpreadLogger_XAUUSD.ex5").write_text("binary\n", encoding="utf-8")
    (preset_dir / "PassiveSpreadLogger_XAUUSD.safe.set").write_text("InpUseCommonFiles=false\n", encoding="utf-8")
    (mt5_root / "compile_PassiveSpreadLogger_XAUUSD.log").write_text(
        "Result: 0 errors, 0 warnings\n",
        encoding="utf-8",
    )


def _copy_config(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    return root
