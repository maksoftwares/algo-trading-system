from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from src.forward_residual_mt5_shadow_bridge import (
    CONFIG_PATH,
    process,
    write_outputs,
)

ROOT = CONFIG_PATH.parents[1]
LOCK = (
    ROOT
    / "EURUSD_FORWARD_RESIDUAL_MT5_SHADOW_BRIDGE_LOCK_2026_07_30.sha256.json"
)


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _signal(
    *,
    side: str = "LONG",
    status: str = "PUBLISHED_SIGNAL",
    published: str = "2026-09-01T20:03:00Z",
) -> dict:
    return {
        "decision_id": "EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1|2026-09-01",
        "campaign_id": "EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_V1",
        "decision_date": "2026-09-01",
        "decision_time_utc": "2026-09-01T20:00:00Z",
        "published_at_utc": published,
        "status": status,
        "eligible_side": side if status == "PUBLISHED_SIGNAL" else "CASH",
        "regime": "BROAD_EUR_UP",
        "demo_order_authorized": False,
    }


def _quote(
    *,
    tick_time: str = "2026-09-01T20:03:58Z",
    login: int = 1033669,
    server: str = "Capital.ComMena-Demo",
    bid: float = 1.14513,
    ask: float = 1.14520,
) -> dict:
    return {
        "account_login": login,
        "account_server": server,
        "account_trade_mode": 0,
        "symbol": "EURUSD",
        "tick_time_utc": tick_time,
        "bid": bid,
        "ask": ask,
    }


def test_long_shadow_receipt_uses_real_ask_without_order_call() -> None:
    calls = 0

    def provider() -> dict:
        nonlocal calls
        calls += 1
        return _quote()

    receipts, summary = process(
        [_signal()],
        [],
        datetime(2026, 9, 1, 20, 4, tzinfo=UTC),
        provider,
        _config(),
    )
    assert calls == 1
    assert receipts[0]["status"] == "SHADOW_ENTRY_CAPTURED"
    assert receipts[0]["entry"] == 1.14520
    assert round(receipts[0]["stop"], 5) == 1.14440
    assert round(receipts[0]["target"], 5) == 1.14640
    assert receipts[0]["order_api_called"] is False
    assert receipts[0]["position_mutation_attempted"] is False
    assert summary["shadow_entries_captured"] == 1
    assert summary["order_api_calls"] == 0
    assert summary["demo_order_authorized"] is False


def test_short_shadow_receipt_uses_real_bid() -> None:
    receipts, _ = process(
        [_signal(side="SHORT")],
        [],
        datetime(2026, 9, 1, 20, 4, tzinfo=UTC),
        lambda: _quote(),
        _config(),
    )
    assert receipts[0]["entry"] == 1.14513
    assert round(receipts[0]["stop"], 5) == 1.14593
    assert round(receipts[0]["target"], 5) == 1.14393


def test_cash_signal_is_mirrored_without_opening_mt5() -> None:
    def forbidden_provider() -> dict:
        raise AssertionError("cash decision queried MT5")

    receipts, summary = process(
        [_signal(status="PUBLISHED_CASH")],
        [],
        datetime(2026, 9, 1, 20, 4, tzinfo=UTC),
        forbidden_provider,
        _config(),
    )
    assert receipts[0]["status"] == "CASH_MIRRORED"
    assert receipts[0]["shadow_action"] == "NO_ENTRY"
    assert summary["shadow_entries_captured"] == 0


def test_late_signal_is_cash_without_query_or_recovery() -> None:
    def forbidden_provider() -> dict:
        raise AssertionError("late signal queried MT5")

    receipts, _ = process(
        [_signal()],
        [],
        datetime(2026, 9, 1, 20, 6, tzinfo=UTC),
        forbidden_provider,
        _config(),
    )
    assert receipts[0]["status"] == "CASH_LATE_RECEIPT"
    assert receipts[0]["shadow_action"] == "NO_LATE_ENTRY"


def test_stale_tick_and_wrong_account_fail_closed() -> None:
    for quote, message in (
        (_quote(tick_time="2026-09-01T20:03:30Z"), "stale"),
        (_quote(login=999), "login mismatch"),
    ):
        try:
            process(
                [_signal()],
                [],
                datetime(2026, 9, 1, 20, 4, tzinfo=UTC),
                lambda quote=quote: quote,
                _config(),
            )
        except ValueError as error:
            assert message in str(error)
        else:
            raise AssertionError("invalid MT5 state was accepted")


def test_receipt_ledger_is_append_only(tmp_path) -> None:
    receipts, summary = process(
        [_signal()],
        [],
        datetime(2026, 9, 1, 20, 4, tzinfo=UTC),
        lambda: _quote(),
        _config(),
    )
    write_outputs(receipts, summary, tmp_path)
    mutated = json.loads(json.dumps(receipts))
    mutated[0]["entry"] = 9.9
    try:
        write_outputs(mutated, summary, tmp_path)
    except ValueError as error:
        assert "mutation refused" in str(error)
    else:
        raise AssertionError("MT5 shadow receipt was mutated")


def test_bridge_contract_forbids_every_order_api() -> None:
    config = _config()
    assert config["required_metatrader5_python_version"] == "5.0.6070"
    assert config["demo_order_authorized"] is False
    assert "NO_ORDER_CHECK" in config["prohibitions"]
    assert "NO_ORDER_SEND" in config["prohibitions"]
    assert "NO_POSITION_MUTATION" in config["prohibitions"]


def test_mt5_shadow_bridge_lock_matches_every_frozen_file() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["locked_before_forward_floor"] is True
    assert lock["locked_with_zero_live_signals"] is True
    assert lock["locked_with_zero_mt5_receipts"] is True
    assert lock["historical_backfill_allowed"] is False
    assert lock["demo_order_authorized"] is False
    for relative, expected in lock["files"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
