from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_confirmed_event_specialists import (
    BAR_WIDTH_MS,
    _aggregate_ohlc_arrays,
    _classification,
    _compression_retest_candidates,
    _make_candidate,
    _replay_candidate,
    _session_sweep_candidates,
    _shock_failure_candidates,
    portfolio_select,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "config/ml/a3_ml_dukascopy_confirmed_event_specialists_v1.json"
)
BASE_MS = int(pd.Timestamp("2017-01-02T00:00:00Z").timestamp() * 1000)


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _row(index: int, **overrides: float | int | str) -> dict:
    timestamp_ms = BASE_MS + index * BAR_WIDTH_MS
    hour = (index // 12) % 24
    base = {
        "timestamp_ms": timestamp_ms,
        "date_utc": "2017-01-02",
        "hour_utc": hour,
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
        "close_location": 0.7,
        "price_efficiency_5m": 0.7,
        "tick_imbalance_5m": 0.1,
        "tick_imbalance_15m": 0.1,
        "quote_intensity_ratio": 1.5,
        "tick_spread_last": 0.1,
        "xau_tick_count": 100,
    }
    base.update(overrides)
    return base


def test_contract_is_research_only_and_has_a_strict_firewall() -> None:
    contract = _contract()
    validate_contract(contract)
    assert contract["research_controls"]["parameter_grid_search_authorized"] is False
    assert contract["research_controls"]["claims_untouched_holdout"] is False
    assert contract["authorization"]["python_demo_predictions_authorized"] is False
    assert contract["authorization"]["broker_action_authorized"] is False


def test_tick_ohlc_aggregation_does_not_cross_completed_m5_buckets() -> None:
    timestamp = np.array([1_000, 299_000, 301_000, 302_000], dtype=np.int64)
    bid = np.array([100.0, 101.0, 200.0, 199.0])
    ask = bid + 0.2
    result = _aggregate_ohlc_arrays(timestamp, bid, ask)
    assert result["timestamp_ms"].tolist() == [0, BAR_WIDTH_MS]
    assert result.loc[0, "bid_open"] == 100.0
    assert result.loc[0, "bid_close"] == 101.0
    assert result.loc[1, "bid_open"] == 200.0
    assert result.loc[1, "bid_low"] == 199.0


def test_candidate_rejects_stop_beyond_fixed_risk_or_atr_ceiling() -> None:
    contract = _contract()
    family = contract["families"][0]
    row = _row(100)
    candidate = _make_candidate(
        row=row,
        family=family,
        profile_id="TEST",
        direction="LONG",
        event_id="too-wide",
        structural_extreme=90.0,
        reference_level=99.0,
        contract=contract,
    )
    assert candidate is None


def test_exact_replay_enters_long_at_ask_and_exits_at_bid() -> None:
    contract = _contract()
    decision_ms = BASE_MS + 1_000
    ticks = (
        SimpleNamespace(timestamp_ms=decision_ms, bid=100.0, ask=100.05),
        SimpleNamespace(timestamp_ms=decision_ms + 1_000, bid=101.0, ask=101.05),
    )

    class Store:
        def first_tick_at_or_after(self, timestamp_ms: int, maximum_delay_ms: int):
            assert timestamp_ms == decision_ms
            assert maximum_delay_ms == 5 * 60_000
            return ticks[0]

        def load_hour(self, hour_timestamp_ms: int):
            return ticks

    hour_ms = decision_ms - decision_ms % (60 * 60_000)
    h1 = {
        hour_ms: {
            "bid_low": 99.9,
            "bid_high": 101.1,
            "ask_low": 100.1,
            "ask_high": 101.3,
        }
    }
    label = _replay_candidate(
        {
            "candidate_id": "quote-side-test",
            "decision_timestamp_ms": decision_ms,
            "direction": "LONG",
            "stop_distance": 0.5,
            "reward_r": 1.5,
            "maximum_hold_hours": 1,
        },
        h1,
        Store(),
        contract,
    )
    assert label["status"] == "RESOLVED"
    assert label["entry_price"] == 100.05
    assert label["exit_price"] == 101.0
    assert label["exit_reason"] == "TARGET"


def test_session_sweep_requires_reclaim_and_aligned_tick_confirmation() -> None:
    contract = _contract()
    family = contract["families"][0]
    reference = [
        _row(
            index,
            hour_utc=index // 12,
            mid_high=100.5,
            mid_low=100.0,
            mid_open=100.2,
            mid_close=100.3,
        )
        for index in range(72)
    ]
    signal = _row(
        72,
        hour_utc=6,
        mid_open=100.0,
        mid_high=100.4,
        mid_low=99.7,
        mid_close=100.2,
        bid_low=99.6,
        ask_close=100.3,
        tick_imbalance_5m=0.1,
        tick_imbalance_15m=0.1,
    )
    rows = _session_sweep_candidates(pd.DataFrame([*reference, signal]), family, contract)
    assert len(rows) == 1
    assert rows[0]["direction"] == "LONG"
    assert rows[0]["decision_timestamp_ms"] == signal["timestamp_ms"] + BAR_WIDTH_MS


def test_compression_entry_occurs_only_after_a_separate_retest_bar() -> None:
    contract = _contract()
    family = contract["families"][1]
    history = [
        _row(
            index + 72,
            hour_utc=6 + index // 12,
            mid_open=100.0,
            mid_high=100.4,
            mid_low=99.6,
            mid_close=100.0,
        )
        for index in range(12)
    ]
    breakout = _row(
        84,
        hour_utc=7,
        mid_open=100.0,
        mid_high=101.3,
        mid_low=99.9,
        mid_close=101.2,
        body_fraction=0.85,
    )
    retest = _row(
        85,
        hour_utc=7,
        mid_open=101.0,
        mid_high=101.1,
        mid_low=100.45,
        mid_close=100.7,
        bid_low=100.35,
        ask_close=100.75,
        tick_imbalance_5m=0.1,
        tick_spread_last=0.05,
    )
    rows = _compression_retest_candidates(
        pd.DataFrame([*history, breakout, retest]), family, contract
    )
    assert len(rows) == 1
    assert rows[0]["direction"] == "LONG"
    assert rows[0]["decision_timestamp_ms"] == retest["timestamp_ms"] + BAR_WIDTH_MS
    assert rows[0]["decision_timestamp_ms"] > breakout["timestamp_ms"] + BAR_WIDTH_MS


def test_shock_strategy_waits_for_a_later_failure_reclaim() -> None:
    contract = _contract()
    family = contract["families"][2]
    impulse = [
        _row(72, hour_utc=6, mid_open=100.0, mid_close=100.7, mid_high=100.8),
        _row(73, hour_utc=6, mid_open=100.7, mid_close=101.4, mid_high=101.5),
        _row(74, hour_utc=6, mid_open=101.4, mid_close=102.1, mid_high=102.2),
    ]
    confirmation = _row(
        75,
        hour_utc=6,
        mid_open=102.0,
        mid_high=102.1,
        mid_low=100.7,
        mid_close=100.9,
        ask_high=102.2,
        bid_close=100.85,
        tick_imbalance_5m=-0.1,
    )
    rows = _shock_failure_candidates(
        pd.DataFrame([*impulse, confirmation]), family, contract
    )
    assert len(rows) == 1
    assert rows[0]["direction"] == "SHORT"
    assert rows[0]["decision_timestamp_ms"] == confirmation["timestamp_ms"] + BAR_WIDTH_MS


def test_firewall_cannot_promote_exam_results_after_an_earlier_failure() -> None:
    passed = {"gate": True}
    assert (
        _classification(passed, [], ["family"], ["family"], ["family"], passed)
        == "NO_TRAIN_FAMILY_SURVIVOR"
    )
    assert (
        _classification(
            passed, ["family"], [], ["family"], ["family"], passed
        )
        == "NO_VALIDATION_FAMILY_SURVIVOR"
    )


def test_portfolio_selection_honors_concurrency_and_daily_limits() -> None:
    contract = _contract()
    contract["portfolio_gates"]["maximum_concurrent_trades"] = 1
    contract["portfolio_gates"]["maximum_trades_per_utc_day"] = 1
    base = {
        "entry_timestamp_ms": 1_000,
        "exit_timestamp_ms": 10_000,
        "entry_time_utc": "2025-01-01T00:00:01.000Z",
        "candidate_id": "a",
        "family_id": contract["families"][0]["family_id"],
    }
    rows = [base, {**base, "candidate_id": "b", "entry_timestamp_ms": 2_000}]
    assert [row["candidate_id"] for row in portfolio_select(rows, contract)] == ["a"]
