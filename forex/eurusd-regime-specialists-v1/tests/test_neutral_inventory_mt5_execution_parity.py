from __future__ import annotations

import csv
from pathlib import Path

import build_neutral_inventory_mt5_parity_fixture as fixture
import verify_neutral_inventory_mt5_execution_parity as verifier

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "mt5" / "Experts" / "EurUsdNeutralInventoryExecutionParity.mq5"
)
FIXTURE = (
    ROOT
    / "mt5"
    / "Files"
    / "EURUSD_NEUTRAL_INVENTORY_EXECUTION_PARITY_INPUT.csv"
)
CONFIG = (
    ROOT
    / "mt5"
    / "Config"
    / "EURUSD_NEUTRAL_INVENTORY_EXECUTION_PARITY.ini"
)


def test_fixture_covers_closed_and_fail_closed_execution_states() -> None:
    rows = fixture.build_fixture_rows()
    statuses = {row["expected_status"] for row in rows}
    reasons = {row["expected_exit_reason"] for row in rows}
    assert statuses == {
        "CLOSED",
        "NO_TRADE_EXCESS_ENTRY_SPREAD",
        "NO_TRADE_MISSING_ENTRY_TICK",
        "PENDING_MISSING_TIME_EXIT_TICK",
    }
    assert {"STOP", "TARGET", "TIME"}.issubset(reasons)
    assert {row["side"] for row in rows} == {"LONG", "SHORT"}


def test_committed_fixture_matches_python_execution_kernel() -> None:
    with FIXTURE.open(encoding="ascii", newline="") as stream:
        committed = list(csv.DictReader(stream))
    assert committed == fixture.build_fixture_rows()


def test_mql5_kernel_is_tester_only_and_contains_no_order_api() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "MQLInfoInteger(MQL_TESTER)" in text
    assert "PositionsTotal() != 0" in text
    assert "broker_action_allowed=false" in text
    assert "FIXED_STOP_PIPS = 6.0" in text
    assert "FIXED_TARGET_PIPS = 9.0" in text
    assert "MAXIMUM_HOLD_SECONDS = 21600" in text
    for forbidden in (
        "CTrade",
        "OrderSend",
        ".Buy(",
        ".Sell(",
        "PositionClose",
        "WebRequest",
    ):
        assert forbidden not in text


def test_tester_config_has_no_account_or_remote_agent_access() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    assert "Login=0" in text
    assert "Server=\n" in text
    assert "UseLocal=1" in text
    assert "UseRemote=0" in text
    assert "UseCloud=0" in text
    assert "Visual=0" in text
    assert "ShutdownTerminal=1" in text


def test_compiled_kernel_and_fixture_status_are_verified() -> None:
    status = verifier.build_status()
    assert status["fixture_cases"] == 7
    assert status["fixture_tick_rows"] == 18
    assert status["compiled_with_zero_errors"] is True
    assert status["compiled_with_zero_warnings"] is True
    assert status["strategy_tester_runtime_parity_verified"] is False
    assert status["account_accessed"] is False
    assert status["broker_action_allowed"] is False
