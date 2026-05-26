from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase1_observer_parity_report_passes_current_sources(tmp_path):
    module = _load_module()

    output = module.generate_phase1_observer_parity_report(
        ROOT,
        tmp_path / "PHASE1_OBSERVER_PARITY_REPORT.md",
    )

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert "Phase 1 Observer Parity Report" in report
    assert any(check.name == "Break window" and check.status == "PASS" for check in output.checks)
    assert any(check.name == "Reward multiple" and check.status == "PASS" for check in output.checks)


def test_phase1_observer_parity_report_fails_missing_phase0(tmp_path):
    module = _load_module()
    phase1_root = tmp_path / "phase1"
    phase0_root = tmp_path / "phase0"
    observer = phase1_root / "mt5" / "Include" / "Phase1" / "Phase1BreakoutRetest.mqh"
    observer.parent.mkdir(parents=True)
    observer.write_text("m_break_window_bars = 20\n", encoding="utf-8")

    output = module.generate_phase1_observer_parity_report(
        phase1_root,
        tmp_path / "PHASE1_OBSERVER_PARITY_REPORT.md",
        phase0_root,
    )

    assert output.status == "FAIL"
    assert any(check.name == "Phase 0 Python strategy" and check.status == "FAIL" for check in output.checks)


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase1_observer_parity_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase1_observer_parity_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase1_observer_parity_report"] = module
    spec.loader.exec_module(module)
    return module
