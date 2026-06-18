from __future__ import annotations

from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


def test_profit_lock_policy_passes_current_source() -> None:
    audit = load_script("audit_phase1_safety")

    findings = [
        item
        for item in audit.audit_experimental_demo_sources(ROOT)
        if item.path.name == "Account3ProfitLockExitManager.mq5"
    ]

    assert findings == []


def test_profit_lock_fails_if_deal_action_appears(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_safety")
    source = tmp_path / "mt5" / "Experts" / "Account3ProfitLockExitManager.mq5"
    source.parent.mkdir(parents=True)
    text = (ROOT / "mt5" / "Experts" / "Account3ProfitLockExitManager.mq5").read_text(encoding="utf-8")
    source.write_text(text + "\nvoid Bad(){ MqlTradeRequest request; request.action = TRADE_ACTION_DEAL; }\n", encoding="utf-8")

    findings = audit.audit_experimental_demo_sources(tmp_path)

    assert any(item.term == "TRADE_ACTION_DEAL" for item in findings)
    assert any(item.term == "forbidden_guard_present" and item.line == "TRADE_ACTION_DEAL" for item in findings)


def test_profit_lock_fails_if_managed_magic_exclusion_disappears(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_safety")
    source = tmp_path / "mt5" / "Experts" / "Account3ProfitLockExitManager.mq5"
    source.parent.mkdir(parents=True)
    text = (ROOT / "mt5" / "Experts" / "Account3ProfitLockExitManager.mq5").read_text(encoding="utf-8")
    text = text.replace("if(magic == 933300)", "if(false)")
    source.write_text(text, encoding="utf-8")

    findings = audit.audit_experimental_demo_sources(tmp_path)

    assert any(item.term == "required_guard_missing" and "933300" in item.line for item in findings)
