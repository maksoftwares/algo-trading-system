from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "mt5"
    / "Experts"
    / "EurUsdRsiHealthGateProspectiveObserver.mq5"
)
PRESET = (
    ROOT
    / "mt5"
    / "Presets"
    / "EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER.set"
)
LIVE_CONFIG = (
    ROOT
    / "mt5"
    / "Config"
    / "EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER_LIVE_DEMO.ini"
)
FROZEN = (
    ROOT
    / "config"
    / "frozen_rsi_health_gate_prospective_observer_v1.json"
)
RESULT = (
    ROOT
    / "outputs"
    / "rsi_health_gate_prospective_observer_parity"
    / "RESULT.json"
)


def _settings(path: Path) -> dict[str, str]:
    return {
        key: value
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for key, value in [line.split("=", 1)]
    }


def test_source_has_zero_order_capability() -> None:
    source = SOURCE.read_text(encoding="utf-8").lower()
    forbidden = (
        "#include <trade/",
        "ctrade",
        "ordersend",
        "ordersendasync",
        ".buy(",
        ".sell(",
        "positionclose",
        "positionmodify",
    )
    assert all(token not in source for token in forbidden)


def test_source_freezes_exact_rsi_rule_and_health_gate() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "ATR_PERIOD = 14",
        "BANDS_PERIOD = 20",
        "RSI_PERIOD = 14",
        "RSI_OVERSOLD_INCLUSIVE = 30.0",
        "MINIMUM_BODY_FRACTION = 0.4",
        "RECENT_STOP_LOOKBACK_M15_BARS = 6",
        "STOP_ATR_MULTIPLE = 1.4",
        "STOP_FLOOR_PIPS = 3.0",
        "STOP_CEILING_PIPS = 70.0",
        "TARGET_R = 0.8",
        "MAXIMUM_ENTRY_SPREAD_PIPS = 10.0",
        "MAXIMUM_TRADES_PER_UTC_DAY = 20",
        "ADVERSE_SLIPPAGE_PIPS_PER_SIDE = 0.1",
        "HEALTH_LOOKBACK_COMPLETED_TRADES = 30",
        "HEALTH_MINIMUM_PROFIT_FACTOR = 1.05",
        "hour == 1 || hour == 7 || hour == 21",
        "tick.bid <= virtualStop",
        "tick.bid >= virtualTarget",
        "PushHealthOutcome(pnlPips)",
        "healthCount == HEALTH_LOOKBACK_COMPLETED_TRADES",
        "FileSize(handle) <= 2",
    )
    for token in required:
        assert token in source


def test_source_is_restart_safe_and_fail_closed() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "STATE_SCHEMA",
        "CONTRACT_FINGERPRINT",
        'GlobalVariableDel(StateName("SCHEMA"))',
        "GlobalVariablesFlush()",
        "state_schema_mismatch",
        "state_contract_mismatch",
        "state_prospective_floor_mismatch",
        "state_health_ring_incomplete",
        "duplicate_instance_mutex",
        "ACCOUNT_TRADE_MODE_DEMO",
        "InpAllowedAccountLogin",
        "InpAllowedServer",
        "InpResetPersistentState = false",
        "BrokerToUtc(signalBar.time) < prospectiveStart",
        "STATE_RESTORED",
        "STARTUP_LATCH",
    )
    for token in required:
        assert token in source


def test_preset_and_terminal_are_safely_disarmed() -> None:
    settings = _settings(PRESET)
    assert settings["InpTargetSymbol"] == "EURUSD"
    assert settings["InpRequireDemoAccount"] == "true"
    assert settings["InpAllowedAccountLogin"] == "0"
    assert settings["InpAllowedServer"] == ""
    assert settings["InpProspectiveStartUtc"] == "2026.08.01 00:00"
    assert settings["InpResetPersistentState"] == "false"

    config = LIVE_CONFIG.read_text(encoding="utf-8")
    assert "AllowLiveTrading=0" in config
    assert "AllowDllImport=0" in config
    assert "Expert=EurUsdRsiHealthGateProspectiveObserver" in config
    assert (
        "ExpertParameters=EURUSD_RSI_HEALTH_GATE_PROSPECTIVE_OBSERVER.set"
        in config
    )
    assert "Symbol=EURUSD" in config
    assert "Period=M15" in config


def test_compiled_and_replayed_implementation_is_frozen() -> None:
    config = json.loads(FROZEN.read_text(encoding="utf-8"))
    for item in config["implementation"].values():
        path = ROOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    compile_log = (
        ROOT
        / config["implementation"]["compile_log"]["path"]
    ).read_text(encoding="utf-16")
    assert "Result: 0 errors, 0 warnings" in compile_log
    assert config["broker_action_allowed"] is False
    assert config["demo_order_authorized"] is False


def test_mt5_parity_passed_but_did_not_authorize_orders() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["all_parity_checks_passed"] is True
    assert result["entry_parity"]["broker_coverage"] > 0.99
    assert result["raw_virtual"]["trades"] == 632
    assert result["health_admitted"]["trades"] == 344
    assert result["health_admitted"]["profit_factor"] > 1.6
    assert result["concentration_warning"][
        "no_admitted_trades_2025_08_through_2025_12"
    ] is True
    assert result["demo_order_authorized"] is False


def test_parity_audit_has_exact_header_and_zero_execution_events() -> None:
    path = (
        ROOT
        / "outputs"
        / "rsi_health_gate_prospective_observer_parity"
        / "PARITY_AUDIT.csv"
    )
    with path.open("r", encoding="utf-16", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) > 1_000
    assert rows[0]["event"] == "STATE_INITIALIZED"
    assert not any(
        row["event"].startswith(("ORDER_", "DEAL_", "POSITION_"))
        for row in rows
    )
