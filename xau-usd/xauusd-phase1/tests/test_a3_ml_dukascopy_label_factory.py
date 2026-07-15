from __future__ import annotations

import copy
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_label_factory import (  # noqa: E402
    HOUR_MS,
    Candidate,
    LabelFactoryError,
    generate_h1_pullback_candidates,
    replay_candidates,
    _validate_candidates,
)


def _contract() -> dict:
    payload = json.loads(
        (ROOT / "config" / "ml" / "a3_ml_dukascopy_label_factory.json").read_text(
            encoding="utf-8"
        )
    )
    payload["candidate_family"]["minimum_stop_price"] = 0.1
    payload["candidate_family"]["maximum_stop_price"] = 100.0
    payload["execution"]["maximum_hold_hours"] = 1
    payload["execution"]["maximum_timeout_exit_grace_hours"] = 2
    payload["execution"]["extra_execution_cost_usd"] = 0.0
    payload["execution"]["holding_cost_per_24h_usd"] = 0.0
    return payload


def _candidate(direction: str = "LONG", *, decision_ms: int = HOUR_MS) -> Candidate:
    return Candidate(
        candidate_id=f"candidate-{direction.lower()}",
        family_id="test_family",
        symbol="XAUUSD",
        split="train",
        direction=direction,
        signal_bar_start_utc="1970-01-01T00:00:00.000Z",
        decision_time_utc="1970-01-01T01:00:00.000Z",
        decision_timestamp_ms=decision_ms,
        signal_open=99.5,
        signal_high=100.5,
        signal_low=99.0,
        signal_close=100.0,
        ema_fast=99.8,
        ema_slow=99.0,
        ema_fast_slope_atr=0.1,
        atr=1.0,
        body_fraction=0.5,
        close_location=0.7,
        touch_distance_atr=0.0,
        stop_distance=1.0,
        stop_distance_atr=1.0,
        reward_r=2.0,
        signal_tick_count=100,
    )


def _tick(timestamp_ms: int, bid: float, ask: float) -> SimpleNamespace:
    return SimpleNamespace(timestamp_ms=timestamp_ms, bid=bid, ask=ask)


class FakeTickStore:
    def __init__(self, hours: dict[int, list[SimpleNamespace]]) -> None:
        self.hours = hours

    def load_hour(self, hour_timestamp_ms: int):
        return tuple(self.hours.get(hour_timestamp_ms, []))

    def first_tick_at_or_after(self, timestamp_ms: int, maximum_delay_ms: int):
        end = timestamp_ms + maximum_delay_ms
        for hour in sorted(self.hours):
            for tick in self.hours[hour]:
                if timestamp_ms <= tick.timestamp_ms <= end:
                    return tick
        return None


def _bar(hour_ms: int, *, bid_low: float, bid_high: float, ask_low: float, ask_high: float) -> dict:
    return {
        "timestamp_ms": hour_ms,
        "bid_low": bid_low,
        "bid_high": bid_high,
        "ask_low": ask_low,
        "ask_high": ask_high,
    }


def test_long_enters_ask_and_targets_on_bid() -> None:
    candidate = _candidate("LONG")
    store = FakeTickStore(
        {
            HOUR_MS: [
                _tick(HOUR_MS, 100.0, 100.2),
                _tick(HOUR_MS + 10_000, 102.3, 102.5),
            ]
        }
    )
    labels = replay_candidates(
        [candidate],
        [_bar(HOUR_MS, bid_low=100.0, bid_high=102.3, ask_low=100.2, ask_high=102.5)],
        store,
        _contract(),
    )
    label = labels[0]
    assert label.status == "RESOLVED"
    assert label.entry_price == pytest.approx(100.2)
    assert label.exit_price == pytest.approx(102.3)
    assert label.exit_reason == "TARGET"
    assert label.gross_pnl_usd == pytest.approx(2.1)


def test_short_enters_bid_and_targets_on_ask() -> None:
    candidate = _candidate("SHORT")
    store = FakeTickStore(
        {
            HOUR_MS: [
                _tick(HOUR_MS, 100.0, 100.2),
                _tick(HOUR_MS + 10_000, 97.7, 97.9),
            ]
        }
    )
    labels = replay_candidates(
        [candidate],
        [_bar(HOUR_MS, bid_low=97.7, bid_high=100.0, ask_low=97.9, ask_high=100.2)],
        store,
        _contract(),
    )
    label = labels[0]
    assert label.entry_price == pytest.approx(100.0)
    assert label.exit_price == pytest.approx(97.9)
    assert label.exit_reason == "TARGET"
    assert label.gross_pnl_usd == pytest.approx(2.1)


def test_tick_order_resolves_stop_before_later_same_hour_target() -> None:
    candidate = _candidate("LONG")
    store = FakeTickStore(
        {
            HOUR_MS: [
                _tick(HOUR_MS, 100.0, 100.2),
                _tick(HOUR_MS + 5_000, 99.1, 99.3),
                _tick(HOUR_MS + 10_000, 102.4, 102.6),
            ]
        }
    )
    label = replay_candidates(
        [candidate],
        [_bar(HOUR_MS, bid_low=99.1, bid_high=102.4, ask_low=99.3, ask_high=102.6)],
        store,
        _contract(),
    )[0]
    assert label.exit_reason == "STOP"
    assert label.exit_price == pytest.approx(99.1)


def test_timeout_uses_first_side_correct_quote_at_deadline() -> None:
    candidate = _candidate("LONG")
    store = FakeTickStore(
        {
            HOUR_MS: [_tick(HOUR_MS, 100.0, 100.2)],
            2 * HOUR_MS: [_tick(2 * HOUR_MS, 100.5, 100.7)],
        }
    )
    bars = [
        _bar(HOUR_MS, bid_low=100.0, bid_high=100.4, ask_low=100.2, ask_high=100.6),
        _bar(2 * HOUR_MS, bid_low=100.5, bid_high=100.5, ask_low=100.7, ask_high=100.7),
    ]
    label = replay_candidates([candidate], bars, store, _contract())[0]
    assert label.exit_reason == "TIMEOUT"
    assert label.exit_time_utc == "1970-01-01T02:00:00.000Z"
    assert label.exit_price == pytest.approx(100.5)


def test_no_quote_in_entry_window_is_ineligible_not_corrupt() -> None:
    candidate = _candidate("LONG")
    label = replay_candidates([candidate], [], FakeTickStore({}), _contract())[0]
    assert label.status == "INELIGIBLE"
    assert label.exit_reason == "NO_QUOTE_WITHIN_ENTRY_WINDOW"
    assert label.label_profitable_after_stress is None


def test_future_bar_changes_do_not_change_earlier_candidates() -> None:
    contract = _contract()
    bars = []
    for index in range(140):
        close = 100.0 + 0.03 * index
        bars.append(
            {
                "timestamp_ms": index * HOUR_MS,
                "bid_open": close - 0.4,
                "bid_high": close + 0.1,
                "bid_low": close - 0.5,
                "bid_close": close,
                "ask_open": close - 0.2,
                "ask_high": close + 0.3,
                "ask_low": close - 0.3,
                "ask_close": close + 0.2,
                "tick_count": 50,
            }
        )
    baseline = generate_h1_pullback_candidates(bars, contract)
    mutated = copy.deepcopy(bars)
    for row in mutated[120:]:
        row["bid_open"] += 1000.0
        row["bid_high"] += 1000.0
        row["bid_low"] += 1000.0
        row["bid_close"] += 1000.0
    changed = generate_h1_pullback_candidates(mutated, contract)
    cutoff = 120 * HOUR_MS
    baseline_ids = [row.candidate_id for row in baseline if row.decision_timestamp_ms <= cutoff]
    changed_ids = [row.candidate_id for row in changed if row.decision_timestamp_ms <= cutoff]
    assert baseline_ids
    assert changed_ids == baseline_ids


def test_duplicate_candidate_identity_is_rejected() -> None:
    candidate = _candidate("LONG")
    duplicate = replace(candidate)
    with pytest.raises(LabelFactoryError, match="duplicate candidate IDs"):
        _validate_candidates([candidate, duplicate])
