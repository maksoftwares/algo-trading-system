from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mt5" / "Experts" / "EurUsdH4ChopControlledDemo.mq5"
SHADOW = (
    ROOT / "mt5" / "Presets" / "EURUSD_H4_CHOP_CONTROLLED_SHADOW_DEMO.set"
)
ORDERING = (
    ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_H4_CHOP_CONTROLLED_ORDERING_DEMO.template.set"
)
EX5 = ROOT / "mt5" / "Experts" / "EurUsdH4ChopControlledDemo.ex5"
COMPILE_LOG = ROOT / "mt5" / "EURUSD_H4_CHOP_CONTROLLED_DEMO_COMPILE.log"
VERIFICATION = (
    ROOT / "outputs" / "h4_chop_controlled_demo" / "VERIFICATION.json"
)


def _settings(path: Path) -> dict[str, str]:
    return {
        key: value
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for key, value in [line.split("=", 1)]
    }


def test_source_contains_independent_fail_closed_guards() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "ACCOUNT_TRADE_MODE_DEMO",
        "InpAllowedAccountLogin",
        "InpAllowedServer",
        "InpDemoArmToken",
        "InpEmergencyStop",
        "InpProspectiveStartUtc",
        "InpMaximumDailyClosedLossUsd",
        "InpMaximumRolling5DayClosedLossUsd",
        "InpMaximumSessionEquityDrawdownUsd",
        "CountSymbolPositions() > 0",
        "fixed_lot_must_equal_0p01",
        "GlobalVariableCheck(mutexName)",
        "position_ownership_reconciliation_failed",
    )
    for token in required:
        assert token in source


def test_shadow_preset_is_multiply_disarmed() -> None:
    settings = _settings(SHADOW)
    assert settings["InpShadowMode"] == "true"
    assert settings["InpEnableDemoOrders"] == "false"
    assert settings["InpEmergencyStop"] == "true"
    assert settings["InpDemoArmToken"] == "DISARMED"
    assert settings["InpAllowedAccountLogin"] == "0"
    assert settings["InpAllowedServer"] == ""
    assert settings["InpFixedLots"] == "0.01"


def test_ordering_template_still_requires_owner_identity_edit() -> None:
    settings = _settings(ORDERING)
    assert settings["InpShadowMode"] == "false"
    assert settings["InpEnableDemoOrders"] == "true"
    assert settings["InpEmergencyStop"] == "false"
    assert settings["InpDemoArmToken"] == "I_ACCEPT_DEMO_001"
    assert settings["InpAllowedAccountLogin"] == "0"
    assert settings["InpAllowedServer"] == "REPLACE_WITH_EXACT_DEMO_SERVER"
    assert settings["InpFixedLots"] == "0.01"


def test_compiled_artifact_and_broker_parity_are_pinned() -> None:
    assert hashlib.sha256(EX5.read_bytes()).hexdigest() == (
        "b922bebb492d07bc17c102eecebfb38a097b3cf851eb4f65fd3a56b0380a2eb8"
    )
    compile_text = COMPILE_LOG.read_text(encoding="utf-16")
    assert "Result: 0 errors, 0 warnings" in compile_text
    result = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    assert result["exact_prior_trade_row_parity"] is True
    assert result["exact_prior_metric_parity"] is True
    assert result["windows"]["FULL"]["trades"] == 62
    assert result["windows"]["FULL"]["net_pnl_usd_001_lot"] == 22.85
    assert result["ordering_demo_armed"] is False
    assert result["broker_action_performed"] is False
