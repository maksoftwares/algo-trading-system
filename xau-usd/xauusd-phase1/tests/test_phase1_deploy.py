from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_deploy_phase1_mt5_copies_expected_tree(tmp_path):
    module = _load_deploy_module()
    project = tmp_path / "project"
    portable = tmp_path / "portable"
    data_root = tmp_path / "mapped" / "MQL5"
    _write_project_shell(project)

    output = module.deploy_phase1_mt5(project, portable, data_root)

    assert output.compile_status == "SKIPPED"
    assert output.deployed_count == 9
    assert (portable / "MQL5" / "Experts" / "Phase1DryRunShell.mq5").exists()
    assert (portable / "MQL5" / "Include" / "Phase1" / "Phase1Types.mqh").exists()
    assert (portable / "MQL5" / "Presets" / "Phase1DryRunShell.safe.set").exists()
    assert (portable / "Config" / "phase1_dry_run_startup.ini").exists()
    assert (data_root / "Experts" / "Phase1DryRunShell.mq5").exists()
    assert (data_root / "Include" / "Phase1" / "Phase1Logger.mqh").exists()


def _load_deploy_module():
    path = ROOT / "scripts" / "deploy_phase1_mt5.py"
    spec = importlib.util.spec_from_file_location("deploy_phase1_mt5", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["deploy_phase1_mt5"] = module
    spec.loader.exec_module(module)
    return module


def _write_project_shell(project: Path) -> None:
    (project / "mt5" / "Experts").mkdir(parents=True)
    (project / "mt5" / "Include" / "Phase1").mkdir(parents=True)
    (project / "mt5" / "Presets").mkdir(parents=True)
    (project / "mt5" / "Config").mkdir(parents=True)
    (project / "mt5" / "Experts" / "Phase1DryRunShell.mq5").write_text("#property strict\n", encoding="utf-8")
    (project / "mt5" / "Include" / "Phase1" / "Phase1Types.mqh").write_text("#define TYPES\n", encoding="utf-8")
    (project / "mt5" / "Include" / "Phase1" / "Phase1Logger.mqh").write_text("#define LOGGER\n", encoding="utf-8")
    (project / "mt5" / "Presets" / "Phase1DryRunShell.safe.set").write_text("InpDryRunOnly=true\n", encoding="utf-8")
    (project / "mt5" / "Config" / "phase1_dry_run_startup.ini").write_text("[StartUp]\n", encoding="utf-8")
