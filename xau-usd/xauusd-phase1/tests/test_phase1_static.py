from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase1_safety_audit_has_no_findings():
    module = _load_safety_module()

    assert module.audit_phase1_tree(ROOT) == []


def test_dry_run_shell_is_locked_to_passive_mode():
    text = (ROOT / "mt5" / "Experts" / "Phase1DryRunShell.mq5").read_text(encoding="utf-8")

    assert "input bool InpDryRunOnly = true;" in text
    assert "InpAllowBreakoutRetest = false" in text
    assert "g_logger.WriteHeartbeat" in text


def test_phase1_docs_record_gate9_boundary():
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "PENDING_MANUAL_REVIEW" in text
    assert "Expert modules | Blocked" in text


def _load_safety_module():
    path = ROOT / "scripts" / "audit_phase1_safety.py"
    spec = importlib.util.spec_from_file_location("audit_phase1_safety", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_phase1_safety"] = module
    spec.loader.exec_module(module)
    return module
