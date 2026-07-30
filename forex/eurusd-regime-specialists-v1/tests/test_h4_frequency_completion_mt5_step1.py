from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (
    ROOT
    / "mt5"
    / "Experts"
    / "EurUsdH4FrequencyCompletionControlledDemo.mq5"
)
SHADOW = (
    ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_FREQUENCY_COMPLETION_SHADOW_DEMO.set"
)
ORDERING = (
    ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_FREQUENCY_COMPLETION_ORDERING_DEMO.template.set"
)


def test_ea_defaults_and_both_presets_are_fail_closed() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for expected in (
        "input bool InpShadowMode = true;",
        "input bool InpEnableDemoOrders = false;",
        "input bool InpEmergencyStop = true;",
        "input bool InpTesterOrdersEnabled = false;",
        'input string InpDemoArmToken = "DISARMED";',
        "input double InpLotsPerTrade = 0.01;",
    ):
        assert expected in source
    for path in (SHADOW, ORDERING):
        text = path.read_text(encoding="utf-8")
        assert "InpShadowMode=true" in text
        assert "InpEnableDemoOrders=false" in text
        assert "InpEmergencyStop=true" in text
        assert "InpTesterOrdersEnabled=false" in text
        assert "InpDemoArmToken=DISARMED" in text
        assert "InpLotsPerTrade=0.01" in text


def test_ea_contains_every_frozen_sleeve_and_both_causal_caps() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    sleeves = {
        "BASELINE_CHOP",
        "BASELINE_COMPRESSION",
        "NEXT_CLOSE_CHOP",
        "NEXT_CLOSE_COMPRESSION",
        "RETEST_CHOP",
        "RETEST_COMPRESSION",
        "M15_FOLLOW_3_CHOP",
        "M15_FOLLOW_5_CHOP",
        "M15_FOLLOW_5_COMPRESSION",
        "M15_FOLLOW_7_COMPRESSION",
        "M30_FIRST_BREAK_CHOP",
        "M30_FIRST_BREAK_COMPRESSION",
    }
    assert all(name in source for name in sleeves)
    assert "STAGE_ONE_MAXIMUM_RISK = 2.0" in source
    assert "STAGE_TWO_MAXIMUM_RISK = 2.5" in source
    assert "STAGE1_CAP_REJECTED" in source
    assert "STAGE2_CAP_REJECTED" in source


def test_ea_revalidates_volume_reconciles_positions_and_recovers_state() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for expected in (
        "SYMBOL_VOLUME_MIN",
        "SYMBOL_VOLUME_STEP",
        "frozen_0p01_lot_required",
        "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING",
        "foreign_eurusd_position_mutex",
        "ReconcilePositions",
        "RebuildDailyState",
        "RESTART_RECOVERY_OK",
        "persisted_schema_mismatch",
        "duplicate_instance_mutex",
    ):
        assert expected in source
