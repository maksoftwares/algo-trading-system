from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "mt5" / "Experts" / "EurUsdM15RegimePortfolioControlledDemo.mq5"
)
SHADOW = (
    ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_M15_REGIME_PORTFOLIO_SHADOW_DEMO.set"
)
ORDERING = (
    ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_M15_REGIME_PORTFOLIO_ORDERING_DEMO.template.set"
)
TRANSFER = ROOT / "config" / "frozen_m15_regime_portfolio_mt5_transfer_v1.json"
EX5 = (
    ROOT / "mt5" / "Experts" / "EurUsdM15RegimePortfolioControlledDemo.ex5"
)
COMPILE_LOG = ROOT / "mt5" / "EURUSD_M15_REGIME_PORTFOLIO_COMPILE.log"
LIVE_CONFIG = (
    ROOT
    / "mt5"
    / "Config"
    / "EURUSD_M15_REGIME_PORTFOLIO_LIVE_DEMO_SHADOW.ini"
)
RESULT = ROOT / "outputs" / "m15_regime_portfolio_mt5_transfer" / "RESULT.json"


def _settings(path: Path) -> dict[str, str]:
    return {
        key: value
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for key, value in [line.split("=", 1)]
    }


def test_source_preserves_selected_m15_rule_and_two_regime_allocation() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "_Period != PERIOD_M15",
        "CHOP_BODY_MINIMUM = 0.35",
        "COMPRESSION_BODY_MINIMUM = 0.55",
        "STOP_ATR_MULTIPLE = 1.75",
        "CHOP_TARGET_R = 1.25",
        "COMPRESSION_TARGET_R = 2.0",
        "referenceBars != 24",
        "signalParts.hour < 6 || signalParts.hour > 9",
        "ClassifyRegime(signalOpen)",
        "InpMaximumHoldM15Bars = 48",
    )
    for token in required:
        assert token in source


def test_source_has_independent_fail_closed_demo_guards() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "ACCOUNT_TRADE_MODE_DEMO",
        "InpAllowedAccountLogin",
        "InpAllowedServer",
        "InpDemoArmToken",
        "InpEmergencyStop",
        "InpProspectiveStartUtc",
        "foreign_eurusd_position_mutex",
        "specialist_position_mutex",
        "executable_2_to_1_risk_allocation_required",
        "hedging_account_required",
        "InpMaximumDailyClosedLossUsd",
        "InpMaximumRolling5DayClosedLossUsd",
        "InpMaximumSessionEquityDrawdownUsd",
        "duplicate_instance_mutex",
        "STARTUP_LATCH",
    )
    for token in required:
        assert token in source


def test_shadow_preset_is_multiply_disarmed() -> None:
    settings = _settings(SHADOW)
    assert settings["InpShadowMode"] == "true"
    assert settings["InpEnableDemoOrders"] == "false"
    assert settings["InpEmergencyStop"] == "true"
    assert settings["InpTesterOrdersEnabled"] == "false"
    assert settings["InpDemoArmToken"] == "DISARMED"
    assert settings["InpAllowedAccountLogin"] == "0"
    assert settings["InpAllowedServer"] == ""
    assert settings["InpChopLots"] == "0.02"
    assert settings["InpCompressionLots"] == "0.01"


def test_ordering_template_requires_owner_identity_edit() -> None:
    settings = _settings(ORDERING)
    assert settings["InpShadowMode"] == "false"
    assert settings["InpEnableDemoOrders"] == "true"
    assert settings["InpEmergencyStop"] == "false"
    assert settings["InpDemoArmToken"] == "I_ACCEPT_DEMO_001"
    assert settings["InpAllowedAccountLogin"] == "0"
    assert settings["InpAllowedServer"] == "REPLACE_WITH_EXACT_DEMO_SERVER"


def test_transfer_was_frozen_as_one_shot_and_cannot_authorize_orders() -> None:
    config = json.loads(TRANSFER.read_text(encoding="utf-8"))
    assert config["source_candidate"]["selected_level"] == "M15_FIRST_BREAK"
    assert config["frozen_rule"]["tester_lots"] == {
        "chop": 0.02,
        "compression": 0.01,
    }
    assert all(config["selection_forbidden_after_result"].values())
    assert config["historical_pass_can_authorize_demo_orders"] is False
    assert config["prospective_shadow_confirmation_required"] is True
    assert config["broker_action_allowed"] is False


def test_compiled_implementation_is_pinned_before_transfer_outcome() -> None:
    config = json.loads(TRANSFER.read_text(encoding="utf-8"))
    hashes = config["implementation_hashes"]
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == hashes["source_mq5"]
    assert hashlib.sha256(EX5.read_bytes()).hexdigest() == hashes["compiled_ex5"]
    assert (
        "Result: 0 errors, 0 warnings"
        in COMPILE_LOG.read_text(encoding="utf-16")
    )


def test_live_startup_config_globally_disables_trading_and_dlls() -> None:
    text = LIVE_CONFIG.read_text(encoding="utf-8")
    assert "AllowLiveTrading=0" in text
    assert "AllowDllImport=0" in text
    assert "Expert=EurUsdM15RegimePortfolioControlledDemo" in text
    assert "ExpertParameters=EURUSD_M15_REGIME_PORTFOLIO_SHADOW_DEMO.set" in text
    assert "Symbol=EURUSD" in text
    assert "Period=M15" in text


def test_frozen_broker_transfer_passed_but_orders_remain_unauthorized() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["status"] == "BROKER_TRANSFER_PASSED_PROSPECTIVE_SHADOW_ONLY"
    assert result["all_transfer_gates_passed"] is True
    assert result["windows"]["FULL"]["trades"] == 106
    assert result["windows"]["FULL"]["profit_factor"] == 1.4105024656803944
    assert result["windows"]["FIRST_12_MONTHS"]["profit_factor"] > 1.0
    assert result["windows"]["SECOND_12_MONTHS"]["profit_factor"] > 1.0
    assert result["best_5pct_removed"]["profit_factor"] > 1.0
    assert result["prospective_shadow_authorized"] is True
    assert result["demo_order_authorized"] is False
