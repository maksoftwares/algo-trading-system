from __future__ import annotations

from phase2x_test_helpers import ROOT


def test_shadow_contract_keeps_a3_paused_and_shadow_only() -> None:
    text = (ROOT / "docs" / "A3_ML_SHADOW_GOVERNANCE_V1.md").read_text(encoding="utf-8")
    for token in (
        "A3 account 1033669 remains paused",
        "A3 lanes 933200, 933300, and 933400 remain paused",
        "Profit-lock remains DRY_RUN_DISARMED",
        "No broker action",
        "No MT5 runtime change is allowed",
    ):
        assert token in text


def test_shadow_contract_blocks_broker_write_surfaces() -> None:
    text = (ROOT / "docs" / "A3_ML_SHADOW_GOVERNANCE_V1.md").read_text(encoding="utf-8")
    for token in ("broker write functions", "OrderSend", "CTrade", "TRADE_ACTION_*", "position modification"):
        assert token in text
    assert "Read-only MT5 use is allowed only" in text


def test_meta_hypothesis_does_not_authorize_execution_outputs() -> None:
    text = (ROOT / "docs" / "A3_ML_META_LABEL_HYPOTHESIS_V1.md").read_text(encoding="utf-8")
    for token in (
        "Python must never output or control",
        "BUY or SELL",
        "entry price",
        "stop loss",
        "take profit",
        "broker order",
        "account reactivation",
    ):
        assert token in text
