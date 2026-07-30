from __future__ import annotations

import copy
import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "src" / "m15_regime_forward_adjudicator.py"
CONFIG = ROOT / "config" / "frozen_m15_regime_forward_adjudication_v1.json"


def _module():
    spec = importlib.util.spec_from_file_location("m15_forward", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _signal(module):
    return module.Signal(
        signal_id="2026.08.03 06:15:00|CHOP|26073061",
        entry_time=datetime(2026, 8, 3, 6, 15, tzinfo=UTC),
        regime="CHOP",
        lots=0.02,
        entry=1.1000,
        stop=1.1010,
        target=1.0980,
    )


def _bar(module, timestamp, *, first=1.1001, high=1.1005, low=1.0990, last=1.1000):
    return module.Bar(
        interval_open=timestamp,
        status="OK",
        first_ask=first,
        ask_high=high,
        ask_low=low,
        last_ask=last,
    )


def test_target_resolves_from_exact_forward_ask_bar() -> None:
    module = _module()
    signal = _signal(module)
    bar = _bar(
        module,
        signal.entry_time,
        high=1.1005,
        low=1.0979,
    )
    record = module.resolve_signal(signal, {signal.entry_time: bar}, _config())
    assert record is not None
    assert record["status"] == "RESOLVED"
    assert record["exit_reason"] == "TARGET"
    assert record["exit"] == signal.target
    assert record["pnl_usd"] > 0.0


def test_same_bar_collision_is_stop_first() -> None:
    module = _module()
    signal = _signal(module)
    bar = _bar(
        module,
        signal.entry_time,
        high=1.1011,
        low=1.0979,
    )
    record = module.resolve_signal(signal, {signal.entry_time: bar}, _config())
    assert record is not None
    assert record["exit_reason"] == "STOP"
    assert record["exit"] == signal.stop
    assert record["pnl_usd"] < 0.0


def test_incomplete_future_path_remains_pending_without_ledger_row() -> None:
    module = _module()
    signal = _signal(module)
    bar = _bar(module, signal.entry_time)
    assert (
        module.resolve_signal(signal, {signal.entry_time: bar}, _config())
        is None
    )


def test_missing_observed_interval_becomes_terminal_invalid() -> None:
    module = _module()
    signal = _signal(module)
    later = signal.entry_time + timedelta(minutes=10)
    bars = {
        signal.entry_time: _bar(module, signal.entry_time),
        later: _bar(module, later),
    }
    record = module.resolve_signal(signal, bars, _config())
    assert record is not None
    assert record["status"] == "INVALID"
    assert "MISSING_INTERVAL" in record["invalid_reason"]


def test_pre_floor_signal_is_refused(tmp_path: Path) -> None:
    module = _module()
    fields = list(module.AUDIT_FIELDS)
    signal = {
        name: ""
        for name in fields
    }
    signal.update(
        {
            "recorded_at_broker": "2026.07.31 06:15:00",
            "recorded_at_utc": "2026.07.31 06:15:00",
            "run_id": "EURUSD_M15_REGIME_FORWARD_V1",
            "event": "SIGNAL",
            "detail": "M15_FIRST_BREAK",
            "account": "1033669",
            "server": "Capital.ComMena-Demo",
            "symbol": "EURUSD",
            "magic": "26073061",
            "regime": "CHOP",
            "side": "SHORT",
            "lots": "0.02",
            "entry": "1.1000",
            "stop": "1.1010",
            "target": "1.0980",
            "shadow": "true",
            "orders_enabled": "false",
            "emergency_stop": "true",
        }
    )
    blocked = signal.copy()
    blocked["event"] = "ORDER_BLOCKED"
    blocked["detail"] = "shadow_or_orders_disabled"
    path = tmp_path / "audit.csv"
    path.write_text(
        ",".join(signal[name] for name in fields)
        + "\n"
        + ",".join(blocked[name] for name in fields)
        + "\n",
        encoding="utf-16",
    )
    try:
        module.load_signals(path, _config())
    except ValueError as error:
        assert "pre-floor" in str(error)
    else:
        raise AssertionError("pre-floor M15 signal was accepted")


def test_nonprospective_feature_scope_is_refused(tmp_path: Path) -> None:
    module = _module()
    path = tmp_path / "features.csv"
    path.write_text(
        "evidence_scope,interval_open_configured_utc,source_symbol,"
        "source_status,valid_two_sided_quote_count,first_ask,ask_high,"
        "ask_low,last_ask\n"
        "TESTER_SMOKE_NOT_FORWARD,2026.08.03 06:15:00,EURUSD,OK,10,"
        "1.1,1.1,1.1,1.1\n",
        encoding="utf-8",
    )
    try:
        module.load_eurusd_bars(path, _config())
    except ValueError as error:
        assert "non-prospective" in str(error)
    else:
        raise AssertionError("tester feature row was accepted")


def test_outcome_ledger_is_append_only() -> None:
    module = _module()
    existing = [{"signal_id": "a", "status": "RESOLVED", "pnl_usd": 1.0}]
    module.validate_append_only(existing, existing + [{"signal_id": "b"}])
    mutated = copy.deepcopy(existing)
    mutated[0]["pnl_usd"] = -1.0
    try:
        module.validate_append_only(existing, mutated)
    except ValueError as error:
        assert "mutation refused" in str(error)
    else:
        raise AssertionError("prior M15 outcome mutation was accepted")


def test_admission_never_authorizes_orders() -> None:
    module = _module()
    metrics = module.admission_metrics([], 0, _config())
    assert metrics["status"] == "WAITING_MINIMUM_EVIDENCE"
    assert metrics["demo_order_authorized"] is False
    assert metrics["checks"]["mt5_signal_parity"] is False
    assert metrics["checks"]["shadow_soak"] is False


def test_process_withholds_later_terminal_outcome_until_older_pending() -> None:
    module = _module()
    first = _signal(module)
    second = module.Signal(
        signal_id="2026.08.03 08:00:00|COMPRESSION|26073061",
        entry_time=datetime(2026, 8, 3, 8, 0, tzinfo=UTC),
        regime="COMPRESSION",
        lots=0.01,
        entry=1.1000,
        stop=1.1020,
        target=1.0995,
    )
    bars = {}
    current = first.entry_time
    while current <= second.entry_time:
        bars[current] = _bar(module, current)
        current += timedelta(minutes=5)
    bars[second.entry_time] = _bar(
        module,
        second.entry_time,
        low=1.0994,
    )
    records, summary = module.process(
        [first, second],
        bars,
        _config(),
    )
    assert records == []
    assert summary["terminal_outcomes"] == 0
    assert summary["pending_signals"] == 2
    assert summary["unresolved_signals"] == 1
    assert summary["causally_withheld_signals"] == 1
    assert (
        summary["earliest_pending_signal_entry_time_utc"]
        == first.entry_time.isoformat()
    )
