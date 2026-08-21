from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mt5" / "Experts" / "Account1DailyProfitFloorGuardian.mq5"
CONFIG = (
    ROOT.parent
    / "xauusd-fast-research"
    / "v60-canonical-demo-portfolio-v2"
    / "config"
    / "v60_canonical_demo_portfolio_v2.json"
)


def _guardian_inputs() -> dict[str, str]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    for chart in config["preflight"]["expected_charts"]:
        if chart["id"] == "DAILY_GUARDIAN":
            return chart["inputs"]
    raise AssertionError("DAILY_GUARDIAN chart is absent")


def test_v60_guardian_is_loss_only_and_has_no_minimum_balance_gate() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    inputs = _guardian_inputs()

    assert config["authorization"]["minimum_balance_requirement_enabled"] is False
    assert config["risk"]["equity_fraction_limits_enabled"] is True
    assert inputs["InpDailyProfitFloorEnabled"] == "false"
    assert inputs["InpNextDailyFloorEnabled"] == "false"
    assert inputs["InpHaltEntriesWhenArmed"] == "false"
    assert inputs["InpDailyLossStopEnabled"] == "true"
    assert inputs["InpDailyLossStopAed"] == "-100.0"
    assert inputs["InpDailyLossStopClosePositions"] == "false"
    assert inputs["InpStrategyScopedPnl"] == "true"


def test_v60_guardian_can_only_close_deployed_xau_positions() -> None:
    inputs = _guardian_inputs()
    expected_magics = {
        "961101",
        "961102",
        "961201",
        "961301",
        "961401",
        "967007",
        "968008",
        "962525",
        "965757",
    }

    assert inputs["InpCloseScopeSymbol"] == "XAUUSD"
    assert set(inputs["InpAllowedPositionMagicsCsv"].split(",")) == expected_magics
    source = SOURCE.read_text(encoding="utf-8")
    assert "bool PositionInCloseScope()" in source
    assert "PositionGetInteger(POSITION_MAGIC)" in source
    assert "if(!PositionInCloseScope())" in source


def test_v60_guardian_daily_pnl_is_strategy_scoped() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "input bool InpStrategyScopedPnl = true;" in source
    assert "double StrategyDayPnlAed(bool &valid)" in source
    assert "DEAL_POSITION_ID" in source
    assert "PositionGetDouble(POSITION_PROFIT)" in source
    assert "g_day_start_strategy_open_pnl" in source
    assert "OpenScopedPnlAed(open_pnl_valid) - g_day_start_strategy_open_pnl" in source
    evaluate = source[source.index("void EvaluateFloor()") : source.index("void ReconcileProfitFloorPolicy()")]
    assert "CurrentDayPnlAed(day_pnl_valid)" in evaluate
    assert "ACCOUNT_EQUITY) - g_day_start_equity" not in evaluate


def test_v60_daily_loss_lock_halts_entries_without_forced_liquidation() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "input bool InpDailyLossStopClosePositions = true;" in source
    assert "bool LockedStateRequiresPositionClose()" in source
    assert 'if(ContainsText(g_trigger_reason, "DAILY_LOSS_STOP"))' in source
    assert "return InpDailyLossStopClosePositions;" in source
    locked = source[source.index("if(g_locked)") : source.index("if(InpDailyLossStopEnabled")]
    assert "LockedStateRequiresPositionClose()" in locked
    assert 'WriteEntryHaltFile("keep_entries_halted_today")' in locked
