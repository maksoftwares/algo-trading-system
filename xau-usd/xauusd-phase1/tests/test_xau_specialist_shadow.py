from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ml" / "specialist_shadow_v1.py"


def _load_module():
    name = "specialist_shadow_v1_test"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_shadow_source_has_no_execution_surface() -> None:
    module_text = MODULE_PATH.read_text(encoding="utf-8")
    runner_text = (ROOT / "scripts" / "run_xau_specialist_shadow.py").read_text(
        encoding="utf-8"
    )
    forbidden = ("order_send", "order_check", "login(", "TRADE_ACTION_", "CTrade")
    for token in forbidden:
        assert token not in module_text
        assert token not in runner_text
    assert '"trade_permission": False' in module_text
    assert '"broker_action_allowed": False' in module_text
    assert '"python_execution_authorized": False' in module_text


def test_rates_conversion_excludes_incomplete_bars() -> None:
    module = _load_module()
    rates = [
        {"time": 1_704_067_200, "open": 2000, "high": 2002, "low": 1999, "close": 2001, "spread": 20},
        {"time": 1_704_067_500, "open": 2001, "high": 2003, "low": 2000, "close": 2002, "spread": 30},
    ]
    completed = pd.Timestamp("2024-01-01T00:05:00Z")

    frame = module.mt5_rates_to_m5(rates, point_size=0.01, completed_through=completed)

    assert len(frame) == 1
    assert frame.iloc[0]["bid_open"] == 2000
    assert frame.iloc[0]["ask_open"] == 2000.2
    assert frame.iloc[0]["timestamp_utc"] == completed


def test_market_history_freshness_accepts_weekend_gap() -> None:
    module = _load_module()
    frame = pd.DataFrame(
        {"bar_end_utc": [pd.Timestamp("2026-07-17T21:00:00Z")]}
    )

    age = module.assert_market_history_fresh(
        frame,
        now_utc=pd.Timestamp("2026-07-19T22:40:00Z"),
    )

    assert age == 49 + (40 / 60)


def test_market_history_freshness_rejects_genuinely_stale_feed() -> None:
    module = _load_module()
    frame = pd.DataFrame(
        {"bar_end_utc": [pd.Timestamp("2026-07-15T21:00:00Z")]}
    )

    try:
        module.assert_market_history_fresh(
            frame,
            now_utc=pd.Timestamp("2026-07-19T22:40:00Z"),
        )
    except ValueError as exc:
        assert "stale" in str(exc)
    else:
        raise AssertionError("Stale market history was accepted")


def test_candidate_id_and_jsonl_are_idempotent(tmp_path: Path) -> None:
    module = _load_module()
    stamp = pd.Timestamp("2026-07-17T12:00:00Z")
    first = module.deterministic_id("candidate", module.SPECIALIST_ID, stamp, "abc")
    second = module.deterministic_id("candidate", module.SPECIALIST_ID, stamp, "abc")
    path = tmp_path / "candidates.jsonl"
    record = {"candidate_id": first, "value": 1}

    assert first == second
    assert module.append_jsonl_once(path, record, "candidate_id") is True
    assert module.append_jsonl_once(path, record, "candidate_id") is False
    assert len(module.read_jsonl(path)) == 1


def _candidate(module):
    return {
        "candidate_id": "candidate-1",
        "specialist_id": module.SPECIALIST_ID,
        "signal_time_utc": "2026-07-17T12:00:00Z",
        "contract_hash": "abc",
        "maximum_entry_gap_minutes": 10,
        "maximum_spread_price": 0.75,
        "maximum_spread_r": 0.15,
        "stop_distance": 4.0,
        "target_r": 2.0,
        "ticket_cost_usd": 0.30,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
    }


def test_tick_outcome_uses_ask_entry_bid_exit_and_cost_stress() -> None:
    module = _load_module()
    ticks = pd.DataFrame(
        [
            {"timestamp_utc": pd.Timestamp("2026-07-17T12:00:01Z"), "bid": 100.0, "ask": 100.3},
            {"timestamp_utc": pd.Timestamp("2026-07-17T12:05:00Z"), "bid": 104.0, "ask": 104.3},
            {"timestamp_utc": pd.Timestamp("2026-07-17T12:10:00Z"), "bid": 108.3, "ask": 108.6},
        ]
    )

    result = module.resolve_candidate(
        _candidate(module), ticks, now_utc=datetime(2026, 7, 17, 12, 11, tzinfo=timezone.utc)
    )

    assert result["status"] == "CLOSED"
    assert result["entry_price"] == 100.3
    assert result["exit_reason"] == "TARGET"
    assert result["gross_r"] == 2.0
    assert result["stress_net_r"] < 1.88


def test_tick_outcome_rejects_missing_entry_after_deadline() -> None:
    module = _load_module()
    empty = pd.DataFrame(columns=["timestamp_utc", "bid", "ask"])

    result = module.resolve_candidate(
        _candidate(module),
        empty,
        now_utc=datetime(2026, 7, 17, 12, 11, tzinfo=timezone.utc),
    )

    assert result["status"] == "REJECTED"
    assert result["rejection_reason"] == "NO_ENTRY_TICK"


def test_empty_candidate_ledger_does_not_scan_tick_history(tmp_path: Path) -> None:
    module = _load_module()

    def fail_if_called(_path: Path) -> pd.DataFrame:
        raise AssertionError("Tick history should not be read without candidates")

    module.read_prospective_ticks = fail_if_called

    result = module.resolve_all_candidates(
        tmp_path / "missing_candidates.jsonl",
        tmp_path / "ticks",
        now_utc=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )

    assert result == []
