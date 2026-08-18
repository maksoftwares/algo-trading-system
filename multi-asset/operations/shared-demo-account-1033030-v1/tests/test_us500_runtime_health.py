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


def audit_row(event: str = "HEARTBEAT", **changes: str) -> dict[str, str]:
    row = {
        "utc_time": "2026.08.10 12:00:00",
        "event": event,
        "detail": "OK" if event == "HEARTBEAT" else "ORDER_MODE_AUTHORIZED",
        "contract_id": MODULE.EXPECTED_CONTRACT,
        "config_sha256": MODULE.EXPECTED_CONFIG,
        "account": MODULE.EXPECTED_ACCOUNT,
        "server": MODULE.EXPECTED_SERVER,
        "symbol": MODULE.EXPECTED_SYMBOL,
        "orders_enabled": "1",
        "broker_allowed": "1",
        "symbol_exposure": "0",
        "own_positions": "0",
        "event_id": "V41-test",
    }
    row.update(changes)
    return row


def armed_audit(**heartbeat_changes: str) -> list[dict[str, str]]:
    return [audit_row(event="INIT"), audit_row(**heartbeat_changes)]


def test_fresh_authorized_heartbeat_is_healthy() -> None:
    report = MODULE.evaluate(
        [health_row()],
        armed_audit(),
        now_utc=datetime(2026, 8, 10, 12, 1, tzinfo=timezone.utc),
    )

    assert report["status"] == "HEALTHY"
    assert report["errors"] == []
    assert report["warnings"] == []


def test_stale_or_disconnected_runtime_fails_without_changing_trading_state() -> None:
    report = MODULE.evaluate(
        [health_row(connected="0")],
        armed_audit(),
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
        rows,
        armed_audit(),
        now_utc=datetime(2026, 8, 10, 12, 1, tzinfo=timezone.utc),
    )

    assert report["status"] == "DEGRADED"
    assert report["errors"] == []
    assert "29494.0ms" in report["warnings"][0]


def test_disarmed_or_failed_ea_state_fails_closed() -> None:
    disarmed = armed_audit(orders_enabled="0")
    disarmed[0]["detail"] = "DISARMED_READY"
    report = MODULE.evaluate(
        [health_row()],
        disarmed,
        now_utc=datetime(2026, 8, 10, 12, 1, tzinfo=timezone.utc),
    )

    assert report["status"] == "FAILED"
    assert any("orders_enabled" in error for error in report["errors"])
    assert any("not order-authorized" in error for error in report["errors"])

    failed = MODULE.evaluate(
        [health_row()],
        armed_audit(detail="INTEGRITY_FAILED"),
        now_utc=datetime(2026, 8, 10, 12, 1, tzinfo=timezone.utc),
    )
    assert failed["status"] == "FAILED"
    assert any("INTEGRITY_FAILED" in error for error in failed["errors"])


def test_tick_and_clock_freshness_fail_during_decision_session() -> None:
    report = MODULE.evaluate(
        [health_row(utc_time="2026.08.10 14:00:00", tick_age_ms="30001", server_lag_seconds="31")],
        armed_audit(utc_time="2026.08.10 14:00:00"),
        now_utc=datetime(2026, 8, 10, 14, 1, tzinfo=timezone.utc),
    )

    assert report["status"] == "FAILED"
    assert report["session_freshness_required"] is True
    assert any("tick is stale" in error for error in report["errors"])
    assert any("clock lag" in error for error in report["errors"])


def test_closed_session_does_not_require_a_fresh_tick() -> None:
    report = MODULE.evaluate(
        [health_row(tick_age_ms="999999")],
        armed_audit(),
        now_utc=datetime(2026, 8, 10, 12, 1, tzinfo=timezone.utc),
    )

    assert report["status"] == "HEALTHY"
    assert report["session_freshness_required"] is False


def test_runtime_verifier_is_read_only() -> None:
    source = (ROOT / "verify_us500_runtime_health.py").read_text(encoding="utf-8")

    assert "OrderSend(" not in source
    assert "order_send(" not in source
    assert "order_send" in source
    assert ".write_" not in source
    assert "FileOpen" not in source
