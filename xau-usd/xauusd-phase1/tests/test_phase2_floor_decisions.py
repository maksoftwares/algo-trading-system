from __future__ import annotations

from pathlib import Path

from phase2x_test_helpers import ROOT, load_script


def test_executor_has_family_duplicate_mutex_guard() -> None:
    source = ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5"
    text = source.read_text(encoding="utf-8", errors="replace")

    assert "SameFamilySameDirectionOpenOnCurrentM5Bar" in text
    assert 'guard_reason = "WOULD_DUPLICATE_FAMILY_EVENT";' in text
    assert "magic >= 920100 && magic < 920300" in text
    assert "magic >= 920300 && magic < 920500" in text
    assert "magic >= 920500 && magic < 920600" in text
    assert "PositionGetInteger(POSITION_TIME)" in text
    assert "OrderGetInteger(ORDER_TIME_SETUP)" in text


def test_guardian_stage_a_is_observer_only_and_writes_startup_log() -> None:
    source = ROOT / "mt5" / "Experts" / "AccountEquityGuardianShadow.mq5"
    text = source.read_text(encoding="utf-8", errors="replace")

    assert "InpStartupFileName" in text
    assert "WriteStartupRow" in text
    assert "ATTACHED_GUARDIAN_SHADOW_STAGE_A" in text
    for forbidden in (
        "OrderSend",
        "OrderSendAsync",
        "CTrade",
        "trade.Buy",
        "trade.Sell",
        "PositionOpen",
        "PositionModify",
        "PositionClose",
    ):
        assert forbidden not in text


def test_floor_script_appends_guardian_without_touching_non_usdjpy_charts(tmp_path: Path) -> None:
    module = load_script("apply_phase2_floor_decisions")
    profile = tmp_path / "Default"
    profile.mkdir()
    chart = profile / "chart01.chr"
    chart.write_text(
        "\n".join(
            [
                "<chart>",
                "symbol=XAUUSD",
                "<expert>",
                "name=Phase2ExperimentalDemoExecutor",
                "<inputs>",
                "InpCandidate=breakout_retest",
                "InpBrokerActionAllowed=true",
                "InpDryRunOnly=false",
                "InpFixedLot=0.01",
                "InpEURUSDFixedLot=0.05",
                "InpGBPUSDFixedLot=0.05",
                "</inputs>",
                "</expert>",
                "</chart>",
            ]
        ),
        encoding="utf-8",
    )

    usdjpy = module.disable_usdjpy_broker_action(profile)
    guardian = module.ensure_guardian_chart(profile)
    inventory = module.chart_inventory(profile)

    assert usdjpy["changed_charts"] == []
    assert usdjpy["remaining_usdjpy_broker_action"] == []
    assert Path(guardian).name == "chart02.chr"
    assert len(inventory) == 2
    assert inventory[0].broker_action_allowed == "true"
    assert inventory[1].expert == "AccountEquityGuardianShadow"


def test_floor_script_disables_usdjpy_broker_action(tmp_path: Path) -> None:
    module = load_script("apply_phase2_floor_decisions")
    profile = tmp_path / "Default"
    profile.mkdir()
    chart = profile / "chart01.chr"
    chart.write_text(
        "\n".join(
            [
                "<chart>",
                "symbol=USDJPY",
                "<expert>",
                "name=Phase2ExperimentalDemoExecutor",
                "<inputs>",
                "InpCandidate=breakout_retest",
                "InpBrokerActionAllowed=true",
                "InpDryRunOnly=false",
                "</inputs>",
                "</expert>",
                "</chart>",
            ]
        ),
        encoding="utf-8",
    )

    result = module.disable_usdjpy_broker_action(profile)
    updated = chart.read_text(encoding="utf-8")

    assert result["changed_charts"] == ["chart01.chr"]
    assert result["remaining_usdjpy_broker_action"] == []
    assert "InpBrokerActionAllowed=false" in updated
    assert "InpDryRunOnly=true" in updated
