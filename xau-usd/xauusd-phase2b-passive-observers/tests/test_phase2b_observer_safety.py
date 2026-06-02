from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase2b_safety_report_generation_passes(tmp_path):
    audit = _load_audit_module()

    output = audit.generate_safety_report(ROOT, tmp_path)

    assert output.status == "PASS"
    assert "PHASE2B_OBSERVER_SAFETY_AUDIT.md" in str(output.report_path)


def test_phase2b_docs_define_observer_log_schema():
    text = (ROOT / "docs" / "OBSERVER_LOG_SCHEMA.md").read_text(encoding="utf-8")

    assert "candidate_id" in text
    assert "hypothesis_hash" in text
    assert "dry_run" in text
    assert "trade_permission" in text


def _load_audit_module():
    path = ROOT / "scripts" / "audit_phase2b_observer_safety.py"
    spec = importlib.util.spec_from_file_location("audit_phase2b_observer_safety_phase2b", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
