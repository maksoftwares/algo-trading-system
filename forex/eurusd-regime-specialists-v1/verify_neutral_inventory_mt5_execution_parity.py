from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import build_neutral_inventory_mt5_parity_fixture as fixture
from eurusd_regime_specialists.research import PACKAGE_ROOT, sha256_file

LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_INVENTORY_MT5_EXECUTION_PARITY_"
    "2026_07_29.sha256.json"
)
SOURCE = (
    PACKAGE_ROOT
    / "mt5"
    / "Experts"
    / "EurUsdNeutralInventoryExecutionParity.mq5"
)
EX5 = SOURCE.with_suffix(".ex5")
FIXTURE = (
    PACKAGE_ROOT
    / "mt5"
    / "Files"
    / "EURUSD_NEUTRAL_INVENTORY_EXECUTION_PARITY_INPUT.csv"
)
CONFIG = (
    PACKAGE_ROOT
    / "mt5"
    / "Config"
    / "EURUSD_NEUTRAL_INVENTORY_EXECUTION_PARITY.ini"
)
COMPILE_LOG = (
    PACKAGE_ROOT
    / "mt5"
    / "EURUSD_NEUTRAL_INVENTORY_EXECUTION_PARITY_COMPILE.log"
)


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {
        "compiled_with_zero_errors": True,
        "compiled_with_zero_warnings": True,
        "python_fixture_parity_passed": True,
        "strategy_tester_runtime_parity_verified": False,
        "account_accessed": False,
        "broker_action_allowed": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("MT5 execution-parity lock is incomplete")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"MT5 execution-parity artifact drift: {relative}")
    return lock


def verify_fixture() -> dict[str, int]:
    with FIXTURE.open(encoding="ascii", newline="") as stream:
        committed = list(csv.DictReader(stream))
    expected = fixture.build_fixture_rows()
    if committed != expected:
        raise RuntimeError("MT5 execution-parity fixture drift")
    return {
        "cases": len({row["case_id"] for row in committed}),
        "tick_rows": len(committed),
    }


def verify_source_safety() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "MQLInfoInteger(MQL_TESTER)",
        "PositionsTotal() != 0",
        "broker_action_allowed=false",
        "FIXED_STOP_PIPS = 6.0",
        "FIXED_TARGET_PIPS = 9.0",
        "MAXIMUM_HOLD_SECONDS = 21600",
    )
    if any(value not in source for value in required):
        raise RuntimeError("MT5 execution-parity safety contract drift")
    forbidden = (
        "CTrade",
        "OrderSend",
        ".Buy(",
        ".Sell(",
        "PositionClose",
        "WebRequest",
    )
    if any(value in source for value in forbidden):
        raise RuntimeError("MT5 execution-parity source gained broker capability")


def verify_compile() -> None:
    if not EX5.is_file() or EX5.stat().st_size <= 0:
        raise RuntimeError("MT5 execution-parity EX5 is missing")
    log = COMPILE_LOG.read_text(encoding="utf-16")
    if "Result: 0 errors, 0 warnings" not in log:
        raise RuntimeError("MT5 execution-parity compile did not pass")


def verify_tester_boundary() -> None:
    config = CONFIG.read_text(encoding="utf-8")
    required = (
        "Login=0",
        "Server=\n",
        "UseLocal=1",
        "UseRemote=0",
        "UseCloud=0",
        "Visual=0",
        "ShutdownTerminal=1",
    )
    if any(value not in config for value in required):
        raise RuntimeError("MT5 execution-parity tester boundary drift")


def build_status() -> dict[str, Any]:
    lock = verify_lock()
    counts = verify_fixture()
    verify_source_safety()
    verify_compile()
    verify_tester_boundary()
    return {
        "schema_version": (
            "eurusd_neutral_inventory_mt5_execution_parity_status_v1"
        ),
        "status": (
            "COMPILE_AND_FIXTURE_READY_RUNTIME_PARITY_"
            "BLOCKED_ACCOUNT_BOUNDARY"
        ),
        "fixture_cases": counts["cases"],
        "fixture_tick_rows": counts["tick_rows"],
        "python_fixture_parity_passed": True,
        "compiled_with_zero_errors": True,
        "compiled_with_zero_warnings": True,
        "mq5_sha256": lock["files"][
            "mt5/Experts/EurUsdNeutralInventoryExecutionParity.mq5"
        ],
        "ex5_sha256": lock["files"][
            "mt5/Experts/EurUsdNeutralInventoryExecutionParity.ex5"
        ],
        "strategy_tester_attempted_without_account": True,
        "strategy_tester_runtime_parity_verified": False,
        "tester_blocker": "MT5_TESTER_REQUIRES_ACCOUNT",
        "account_accessed": False,
        "broker_action_allowed": False,
        "controlled_demo_ready": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status",))
    return parser.parse_args()


def main() -> int:
    parse_args()
    print(json.dumps(build_status(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
