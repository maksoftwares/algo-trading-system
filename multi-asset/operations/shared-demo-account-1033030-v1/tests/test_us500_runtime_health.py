from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_us500_runtime_health", ROOT / "verify_us500_runtime_health.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def health_row(event: str = "HEARTBEAT_HEALTH", **changes: str) -> dict[str, str]:
    row = {
        "utc_time": "2026.08.10 12:00:00",
        "event": event,
        "contract_id": MODULE.EXPECTED_CONTRACT,
        "config_sha256": MODULE.EXPECTED_CONFIG,
        "account": MODULE.EXPECTED_ACCOUNT,
        "server": MODULE.EXPECTED_SERVER,
        "symbol": MODULE.EXPECTED_SYMBOL,
        "connected": "1",
        "terminal_trade_allowed": "1",
        "mql_trade_allowed": "1",
        "account_trade_allowed": "1",
        "ping_ms": "42.125",
        "tick_age_ms": "250",
        "server_lag_seconds": "0",
        "order_send_ms": "-1.000",
        "event_id": "V41H-test",
    }
    row.update(changes)
    return row


def test_fresh_authorized_heartbeat_is_healthy() -> None:
    report = MODULE.evaluate(
        [health_row()], now_utc=datetime(2026, 8, 10, 12, 1, tzinfo=timezone.utc)
    )

    assert report["status"] == "HEALTHY"
    assert report["errors"] == []
    assert report["warnings"] == []


def test_stale_or_disconnected_runtime_fails_without_changing_trading_state() -> None:
    report = MODULE.evaluate(
        [health_row(connected="0")],
        now_utc=datetime(2026, 8, 10, 12, 3, tzinfo=timezone.utc),
    )

    assert report["status"] == "FAILED"
    assert any("stale" in error for error in report["errors"])
    assert any("connected" in error for error in report["errors"])


def test_slow_order_is_reported_but_not_used_as_an_execution_gate() -> None:
    rows = [
        health_row(),
        health_row(
            event="ORDER_EXECUTION",
            utc_time="2026.08.10 12:00:30",
            order_send_ms="29493.971",
        ),
    ]
    report = MODULE.evaluate(
        rows, now_utc=datetime(2026, 8, 10, 12, 1, tzinfo=timezone.utc)
    )

    assert report["status"] == "DEGRADED"
    assert report["errors"] == []
    assert "29494.0ms" in report["warnings"][0]


def test_runtime_verifier_is_read_only() -> None:
    source = (ROOT / "verify_us500_runtime_health.py").read_text(encoding="utf-8")

    assert "OrderSend(" not in source
    assert "order_send" in source
    assert ".write_" not in source
    assert "FileOpen" not in source
