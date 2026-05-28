from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2_scheduler_installer_runs_periodic_checks_only():
    script = (ROOT / "scripts" / "install_phase2_periodic_checks_task.ps1").read_text(encoding="utf-8")

    assert "Register-ScheduledTask" in script
    assert "run_phase1_periodic_checks.py" in script
    assert "--spread-files-dir" in script
    assert "$WhatIfOnly" in script
    assert "terminal64.exe" not in script
    assert "MetaEditor" not in script
    assert "OrderSend" not in script
    assert "CTrade" not in script


def test_operations_prep_documents_scheduler_dry_run_first():
    text = (ROOT / "docs" / "PHASE2_OPERATIONS_PREP.md").read_text(encoding="utf-8")

    assert "install_phase2_periodic_checks_task.ps1" in text
    assert "-WhatIfOnly" in text
    assert "does not start MT5" in text
    assert "does not" in text and "authorize broker execution" in text
