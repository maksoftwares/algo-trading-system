from __future__ import annotations

from phase2x_test_helpers import ROOT


SOURCE = ROOT / "mt5" / "Experts" / "A3MlPredictionObserver.mq5"
PRESET = ROOT / "mt5" / "Presets" / "A3MlPredictionObserver.passive_xauusd.set"


def test_a3_ml_prediction_observer_reads_python_handoff() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "#include <A3MlEaHandoff.mqh>" in text
    assert "A3_ML_EA_HANDOFF.csv" in text
    assert "A3MlEaHandoffReadLatest" in text
    assert "a3_ml_prediction_observer_log.csv" in text
    assert "a3_ml_prediction_observer_startup.csv" in text
    assert "1025742,1033030,1033669" in text


def test_a3_ml_prediction_observer_has_no_broker_action_surface() -> None:
    text = SOURCE.read_text(encoding="utf-8")
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
    assert "EventSetTimer" in text
    assert "AppendCsvRow" in text


def test_a3_ml_prediction_observer_refuses_unsafe_startup_modes() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "if(!InpDryRunOnly)" in text
    assert "return INIT_FAILED;" in text
    assert "server marker mismatch" in text
    assert "account login not whitelisted" in text
    assert "attached symbol does not match InpTargetSymbol" in text


def test_a3_ml_prediction_observer_preset_is_passive_for_all_three_accounts() -> None:
    text = PRESET.read_text(encoding="utf-8")

    assert "InpDryRunOnly=true" in text
    assert "InpTargetSymbol=XAUUSD" in text
    assert "InpExpectedServerMarker=Demo" in text
    assert "InpAllowedAccountLoginsCsv=1025742,1033030,1033669" in text
    assert "InpHandoffFileName=A3_ML_EA_HANDOFF.csv" in text
