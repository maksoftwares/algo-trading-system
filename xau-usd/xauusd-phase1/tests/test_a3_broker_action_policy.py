from __future__ import annotations

from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


def test_a3_base_policy_passes_current_source() -> None:
    audit = load_script("audit_phase1_safety")

    findings = [
        item
        for item in audit.audit_experimental_demo_sources(ROOT)
        if item.path.name == "A3BreakoutExecutorBase.mqh"
    ]

    assert findings == []


def test_a3_base_fails_if_demo_scope_guard_disappears(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_safety")
    source = tmp_path / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh"
    source.parent.mkdir(parents=True)
    text = (ROOT / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh").read_text(encoding="utf-8")
    text = text.replace('input string InpExpectedServerMarker = "Demo";', 'input string InpExpectedServerMarker = "";')
    source.write_text(text, encoding="utf-8")

    findings = audit.audit_experimental_demo_sources(tmp_path)

    assert any(item.term == "required_guard_missing" and "InpExpectedServerMarker" in item.line for item in findings)


def test_a3_base_fails_if_unapproved_action_type_is_added(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_safety")
    source = tmp_path / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh"
    source.parent.mkdir(parents=True)
    text = (ROOT / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh").read_text(encoding="utf-8")
    source.write_text(text + "\nvoid Bad(){ CTrade t; }\n", encoding="utf-8")

    findings = audit.audit_experimental_demo_sources(tmp_path)

    assert any(item.term == "CTrade" for item in findings)
