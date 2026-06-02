from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE2B_ROOT = ROOT.parent / "xauusd-phase2b-passive-observers"


def test_phase2b_observer_safety_audit_passes(tmp_path):
    audit = _load_audit_module()

    output = audit.generate_safety_report(PHASE2B_ROOT, tmp_path)

    assert output.status == "PASS"
    assert output.findings_count == 0


def test_safety_audit_fails_on_executable_broker_action_term(tmp_path):
    audit = _load_audit_module()
    bad_root = tmp_path / "bad_phase2b"
    bad_source = bad_root / "mt5" / "Experts" / "bad.mq5"
    bad_source.parent.mkdir(parents=True)
    forbidden = "Order" + "Send"
    bad_source.write_text(f"void OnTick() {{ {forbidden}(0); }}\n", encoding="utf-8")

    findings = audit.audit_observer_tree(bad_root)

    assert len(findings) == 1
    assert findings[0].term == forbidden


def test_safety_audit_ignores_comments(tmp_path):
    audit = _load_audit_module()
    root = tmp_path / "comment_only_phase2b"
    source = root / "mt5" / "Experts" / "comment_only.mq5"
    source.parent.mkdir(parents=True)
    forbidden = "Order" + "Send"
    source.write_text(f"// {forbidden} is mentioned in a comment only\nvoid OnTick() {{}}\n", encoding="utf-8")

    assert audit.audit_observer_tree(root) == []


def test_observer_log_schema_contains_required_passive_fields():
    text = (PHASE2B_ROOT / "docs" / "OBSERVER_LOG_SCHEMA.md").read_text(encoding="utf-8")

    for field in ("dry_run", "trade_permission", "broker_action_allowed", "phase2_execution_authorized"):
        assert field in text


def _load_audit_module():
    path = PHASE2B_ROOT / "scripts" / "audit_phase2b_observer_safety.py"
    spec = importlib.util.spec_from_file_location("audit_phase2b_observer_safety", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
