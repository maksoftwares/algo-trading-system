from __future__ import annotations

from phase2x_test_helpers import ROOT


INCLUDE = ROOT / "mt5" / "Include" / "A3MlEaHandoff.mqh"
SHADOW_TAP = ROOT / "mt5" / "Include" / "A3MlShadowTap.mqh"
BROKER_EXECUTOR_SOURCES = [
    ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5",
    ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoRepairExecutor.mq5",
    ROOT / "mt5" / "Include" / "A3BreakoutExecutorBase.mqh",
]


def test_a3_ml_mql_handoff_reader_has_expected_surface() -> None:
    text = INCLUDE.read_text(encoding="utf-8")

    assert "#define A3_ML_EA_HANDOFF_DEFAULT_FILE \"A3_ML_EA_HANDOFF.csv\"" in text
    assert "struct A3MlEaHandoffDecision" in text
    assert "A3MlEaHandoffReadLatest" in text
    assert "A3MlEaHandoffFieldsForLog" in text
    assert "broker_action_authorized" in text
    assert "A3MlEaHandoffNotExpired" in text
    assert "ABSTAIN" in text


def test_a3_ml_mql_handoff_reader_is_passive_read_only() -> None:
    text = INCLUDE.read_text(encoding="utf-8")

    forbidden = (
        "OrderSend",
        "OrderSendAsync",
        "CTrade",
        "TRADE_ACTION_",
        "PositionClose",
        "FILE_WRITE",
    )
    for token in forbidden:
        assert token not in text
    assert "FILE_READ" in text
    assert "FileOpen" in text


def test_a3_ml_shadow_tap_is_passive_log_only() -> None:
    text = SHADOW_TAP.read_text(encoding="utf-8")

    forbidden = (
        "OrderSend",
        "OrderSendAsync",
        "CTrade",
        "MqlTradeRequest",
        "MqlTradeResult",
        "TRADE_ACTION_",
        "PositionClose",
        "PositionModify",
        "OrderDelete",
    )
    for token in forbidden:
        assert token not in text
    assert "A3MlEaHandoffReadLatest" in text
    assert "FILE_WRITE" in text
    assert "A3MlShadowTapAppendCsvRow" in text


def test_broker_executors_only_use_ml_shadow_tap_not_direct_handoff_reader() -> None:
    for path in BROKER_EXECUTOR_SOURCES:
        text = path.read_text(encoding="utf-8")
        assert "A3MlShadowTapWriteRow" in text
        assert "A3MlEaHandoffReadLatest" not in text
        assert "A3MlEaHandoffDecision" not in text


def test_a3_ml_mql_handoff_reader_fails_closed_on_expiry() -> None:
    text = INCLUDE.read_text(encoding="utf-8")

    assert "A3MlEaHandoffParseUtc" in text
    assert "TimeGMT() <= expires_at" in text
    assert "if(!A3MlEaHandoffNotExpired(decision.expires_at_utc))" in text
    assert "return false;" in text[text.index("if(!A3MlEaHandoffNotExpired(decision.expires_at_utc))") :]
