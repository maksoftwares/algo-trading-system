from __future__ import annotations

from pathlib import Path

from phase2x_test_helpers import load_script


def test_canonical_source_fails_if_broker_action_is_injected(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_safety")
    source = tmp_path / "mt5" / "Experts" / "Phase1DryRunShell.mq5"
    source.parent.mkdir(parents=True)
    forbidden = "Order" + "Send"
    source.write_text(f"void OnTick() {{ {forbidden}; }}\n", encoding="utf-8")

    findings = audit.audit_canonical_phase1_sources(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == source
    assert findings[0].term == forbidden


def test_unknown_mql_broker_action_source_fails_closed(tmp_path: Path) -> None:
    audit = load_script("audit_phase1_safety")
    source = tmp_path / "mt5" / "Experts" / "NewUnreviewedExecutor.mq5"
    source.parent.mkdir(parents=True)
    source.write_text("void Send(){ MqlTradeRequest r; r.action = TRADE_ACTION_DEAL; }\n", encoding="utf-8")

    findings = audit.audit_phase1_tree(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == source
    assert findings[0].term == "TRADE_ACTION_DEAL"

