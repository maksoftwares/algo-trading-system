from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "Account3ProfitLockExitManager.mq5"
PRESET = ROOT / "mt5" / "Presets" / "Account3ProfitLockExitManager.safe_xauusd.set"
ATTACH_SCRIPT = ROOT / "scripts" / "attach_a3_profit_lock_exit_manager.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def test_profit_lock_manager_safe_defaults_and_scope_locks():
    text = _text(EA)

    assert 'input bool InpDryRunOnly = true;' in text
    assert 'input bool InpManageActionAllowed = false;' in text
    assert 'input string InpTargetSymbol = "XAUUSD";' in text
    assert 'input string InpExpectedServerMarker = "Demo";' in text
    assert 'input string InpAllowedAccountLoginsCsv = "1033669";' in text
    assert 'input string InpManagedMagicsCsv = "933200,933400";' in text
    assert 'input string InpExecutionKillSwitchFileName = "A3_EXECUTION_KILL.txt";' in text
    assert 'input string InpFullStopFileName = "A3_FULL_STOP.txt";' in text
    assert "FullStopActive()" in text
    assert "ExecutionKillSwitchActive()" in text
    assert "EXECUTION_KILL_WOULD_BLOCK_SLTP" in text
    assert 'CsvContainsTextToken(InpManagedMagicsCsv, "933300")' in text
    assert "if(magic == 933300)" in text


def test_profit_lock_manager_sl_only_no_entries_or_closes():
    text = _text(EA)

    assert "TRADE_ACTION_SLTP" in text
    assert "request.tp = tp;" in text
    assert "request.position = ticket;" in text
    for forbidden in (
        "TRADE_ACTION_DEAL",
        "PositionClose",
        "PositionClosePartial",
        "OrderDelete",
        "Buy(",
        "Sell(",
    ):
        assert forbidden not in text


def test_profit_lock_manager_never_widens_and_uses_original_risk_state():
    text = _text(EA)

    assert "A3PL_INITIAL_SL" in text
    assert "GlobalVariableSet(name, current_sl)" in text
    assert "desired_sl > current_sl" in text
    assert "desired_sl < current_sl" in text
    assert "open_price + (lock_r * risk_price)" in text
    assert "open_price - (lock_r * risk_price)" in text
    assert "StopRespectsBrokerDistance" in text


def test_profit_lock_safe_preset_is_non_executing_and_excludes_improved_lane():
    values = _values(PRESET)

    assert values["InpDryRunOnly"] == "true"
    assert values["InpManageActionAllowed"] == "false"
    assert values["InpAllowedAccountLoginsCsv"] == "1033669"
    assert values["InpExecutionKillSwitchFileName"] == "A3_EXECUTION_KILL.txt"
    assert values["InpFullStopFileName"] == "A3_FULL_STOP.txt"
    assert values["InpManagedMagicsCsv"] == "933200,933400"
    assert "933300" not in values["InpManagedMagicsCsv"]
    assert values["InpPrimaryRungEnabled"] == "true"
    assert values["InpPrimaryTriggerR"] == "1.25"
    assert values["InpPrimaryLockR"] == "0.80"
    assert values["InpSecondaryRungEnabled"] == "false"
    assert values["InpTertiaryRungEnabled"] == "false"


def test_profit_lock_attach_script_requires_gate_and_arms_only_manager():
    text = _text(ATTACH_SCRIPT)

    assert "load_gate_payload" in text
    assert "Profit-lock replay gate is not PASS" in text
    assert '"InpDryRunOnly": "false"' in text
    assert '"InpManageActionAllowed": "true"' in text
    assert '"InpExecutionKillSwitchFileName": "A3_EXECUTION_KILL.txt"' in text
    assert '"InpFullStopFileName": "A3_FULL_STOP.txt"' in text
    assert '"InpManagedMagicsCsv": MANAGED_MAGICS' in text
    assert 'EXCLUDED_MAGIC = "933300"' in text
    assert "TRADE_ACTION_DEAL" not in text
