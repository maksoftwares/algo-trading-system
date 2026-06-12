from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "Phase2ShadowFixObserver.mq5"


def test_shadow_fix_observer_v2_blocks_round_retest_clone_family():
    text = EA.read_text(encoding="utf-8")

    assert 'InpShadowPolicyVersion = "shadow_fix_policy_20260612_v2"' in text
    assert 'candidate == "symbol_normalized_round_retest_v0"' in text
    assert 'candidate == "round_number_retest_v0"' in text
    assert "BLOCK_WEAK_EA_ROUND_RETEST_CLONE_FAMILY" in text
    assert "BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND" not in text


def test_shadow_fix_observer_remains_read_only():
    text = EA.read_text(encoding="utf-8")

    forbidden_terms = [
        "OrderSend",
        "OrderSendAsync",
        "CTrade",
        "trade.Buy",
        "trade.Sell",
        "PositionOpen",
        "PositionModify",
        "PositionClose",
        "TRADE_ACTION",
        "MqlTradeRequest",
        "ORDER_TYPE_BUY",
        "ORDER_TYPE_SELL",
    ]
    for term in forbidden_terms:
        assert term not in text
