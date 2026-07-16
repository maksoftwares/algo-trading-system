from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ml.a3_meta_v1.dukascopy_confirmed_event_specialists import BAR_WIDTH_MS
from ml.a3_meta_v1.dukascopy_event_census import (
    _barrier_label,
    _classification,
    _entry,
    _horizon_label,
    _volatility_expansion_events,
    policy_metrics,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/ml/a3_ml_dukascopy_event_census_v1.json"
BASE_MS = int(pd.Timestamp("2017-01-02T00:00:00Z").timestamp() * 1000)


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _row(index: int, **overrides: float | int | str) -> dict:
    timestamp_ms = BASE_MS + index * BAR_WIDTH_MS
    row = {
        "timestamp_ms": timestamp_ms,
        "date_utc": "2017-01-02",
        "hour_utc": 6,
        "bid_open": 99.95,
        "bid_high": 100.45,
        "bid_low": 99.55,
        "bid_close": 100.15,
        "ask_open": 100.05,
        "ask_high": 100.55,
        "ask_low": 99.65,
        "ask_close": 100.25,
        "mid_open": 100.0,
        "mid_high": 100.5,
        "mid_low": 99.6,
        "mid_close": 100.2,
        "atr": 1.0,
        "atr_ratio": 0.8,
        "body_fraction": 0.5,
        "tick_imbalance_5m": 0.1,
        "quote_intensity_ratio": 1.5,
        "tick_spread_last": 0.1,
        "session_utc": "LONDON",
        "volatility_bin": "NORMAL",
        "trend_sign": 1,
        "ema_fast": 100.0,
    }
    row.update(overrides)
    return row


def _event() -> dict:
    decision_ms = BASE_MS + BAR_WIDTH_MS
    return {
        "event_id": "event-1",
        "family_id": "trend_pullback_resumption_v1",
        "profile_id": "FIXED",
        "split": "train",
        "direction": "LONG",
        "signal_index": 0,
        "decision_timestamp_ms": decision_ms,
        "decision_time_utc": "2017-01-02T00:05:00.000Z",
        "session_utc": "ASIA",
        "volatility_bin": "NORMAL",
        "trend_alignment": "ALIGNED",
        "atr": 1.0,
    }


def test_contract_is_research_only_and_context_cannot_promote() -> None:
    contract = _contract()
    validate_contract(contract)
    assert contract["research_controls"]["diagnostic_context_promotion_authorized"] is False
    assert contract["authorization"]["python_demo_predictions_authorized"] is False
    assert contract["authorization"]["ea_consumption_authorized"] is False
    assert contract["authorization"]["broker_action_authorized"] is False


def test_long_labels_enter_at_ask_and_mark_at_bid() -> None:
    contract = _contract()
    contract["forward_labels"]["extra_execution_cost_usd"] = 0.0
    contract["forward_labels"]["holding_cost_per_24h_usd"] = 0.0
    rows = [_row(0)] + [
        _row(index, bid_close=100.0 + index, ask_close=100.1 + index)
        for index in range(1, 7)
    ]
    frame = pd.DataFrame(rows)
    event = _event()
    entry = _entry(event, frame, 1, contract)
    assert entry is not None
    assert entry["price"] == 100.05
    label = _horizon_label(event, frame, 1, entry, 30, contract)
    assert label["status"] == "RESOLVED"
    assert label["entry_price"] == 100.05
    assert label["exit_price"] == 106.0


def test_same_bar_barrier_collision_is_stop_first() -> None:
    contract = _contract()
    contract["forward_labels"]["extra_execution_cost_usd"] = 0.0
    contract["forward_labels"]["holding_cost_per_24h_usd"] = 0.0
    frame = pd.DataFrame(
        [
            _row(0),
            _row(1, bid_open=100.0, ask_open=100.1, bid_low=99.0, bid_high=102.0),
        ]
    )
    event = _event()
    entry = _entry(event, frame, 1, contract)
    assert entry is not None
    label = _barrier_label(
        event,
        frame,
        1,
        entry,
        {"profile_id": "test", "stop_atr": 0.5, "target_atr": 0.75, "maximum_horizon_minutes": 5},
        contract,
    )
    assert label["exit_reason"] == "STOP"
    assert label["exit_price"] == 99.6


def test_stop_gap_uses_worse_executable_open() -> None:
    contract = _contract()
    contract["forward_labels"]["extra_execution_cost_usd"] = 0.0
    contract["forward_labels"]["holding_cost_per_24h_usd"] = 0.0
    frame = pd.DataFrame(
        [
            _row(0),
            _row(1, bid_open=100.0, ask_open=100.1, bid_low=99.9, bid_high=100.2),
            _row(2, bid_open=99.0, ask_open=99.1, bid_low=98.8, bid_high=99.3),
        ]
    )
    event = _event()
    entry = _entry(event, frame, 1, contract)
    assert entry is not None
    label = _barrier_label(
        event,
        frame,
        1,
        entry,
        {"profile_id": "test", "stop_atr": 0.5, "target_atr": 0.75, "maximum_horizon_minutes": 10},
        contract,
    )
    assert label["exit_reason"] == "STOP"
    assert label["exit_price"] == 99.0
    assert label["gross_r"] == pytest.approx(-2.2)


def test_volatility_expansion_rejects_gap_before_signal_bar() -> None:
    contract = _contract()
    family = next(
        row
        for row in contract["event_families"]
        if row["family_id"] == "volatility_expansion_break_v1"
    )
    rows = [
        _row(
            index,
            mid_open=100.0,
            mid_high=100.4,
            mid_low=99.6,
            mid_close=100.0,
        )
        for index in range(12)
    ]
    rows.append(
        _row(
            13,
            mid_open=100.0,
            mid_high=101.2,
            mid_low=99.9,
            mid_close=101.1,
            body_fraction=0.8,
        )
    )
    assert _volatility_expansion_events(pd.DataFrame(rows), family, contract) == []


def test_policy_drawdown_includes_losses_before_first_equity_peak() -> None:
    rows = [
        {
            "event_id": str(index),
            "exit_time_utc": f"2017-01-0{index + 1}T00:00:00Z",
            "stress_net_r": value,
            "stress_net_pnl_usd": value,
        }
        for index, value in enumerate((-1.0, -1.0, 3.0, -2.0))
    ]
    metrics = policy_metrics(rows, 4)
    assert metrics["max_closed_drawdown_r"] == 2.0


def test_chronological_firewall_cannot_be_rescued_by_later_windows() -> None:
    quality = {"quality": True}
    assert (
        _classification(quality, [], ["candidate"], ["candidate"], ["candidate"])
        == "EVENT_CENSUS_NO_TRAIN_SURVIVOR"
    )
    assert (
        _classification(quality, ["candidate"], [], ["candidate"], ["candidate"])
        == "EVENT_CENSUS_NO_VALIDATION_SURVIVOR"
    )
