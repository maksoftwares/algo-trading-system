from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from spot_labels import CompletedM5Atr, SpotLabelError, label_candidates, label_one, load_label_config


@dataclass(frozen=True)
class Tick:
    timestamp_ms: int
    bid: float
    ask: float


class FakeTickStore:
    def __init__(self, ticks: list[Tick]) -> None:
        self.ticks = sorted(ticks, key=lambda tick: tick.timestamp_ms)

    def first_tick_strictly_after(self, timestamp_ms: int, maximum_delay_ms: int) -> Tick | None:
        return next(
            (
                tick
                for tick in self.ticks
                if timestamp_ms < tick.timestamp_ms <= timestamp_ms + maximum_delay_ms
            ),
            None,
        )

    def ticks_between(self, start_timestamp_ms: int, end_timestamp_ms: int):
        return (
            tick
            for tick in self.ticks
            if start_timestamp_ms <= tick.timestamp_ms <= end_timestamp_ms
        )


DECISION = pd.Timestamp("2025-08-01T13:00:00Z")
DECISION_MS = int(DECISION.timestamp() * 1000)


def atr_source(value: float = 2.0) -> CompletedM5Atr:
    return CompletedM5Atr(
        pd.DataFrame(
            {
                "timestamp_ms": [DECISION_MS - 600_000, DECISION_MS],
                "atr": [value, 99.0],
            }
        ),
        bar_width_ms=300_000,
    )


def candidate(direction: str = "LONG", family: str = "flow_continuation") -> dict:
    return {
        "candidate_id": "candidate-1",
        "feature_time_utc": DECISION,
        "family": family,
        "direction": direction,
    }


def test_atr_uses_only_a_bar_completed_before_decision() -> None:
    assert atr_source().at_decision(DECISION_MS) == pytest.approx(2.0)


def test_long_enters_strictly_later_at_ask_and_exits_at_bid() -> None:
    ticks = [
        Tick(DECISION_MS, 90.0, 90.2),
        Tick(DECISION_MS + 100, 100.0, 100.2),
        Tick(DECISION_MS + 500, 101.8, 102.0),
    ]
    result = label_one(
        candidate(),
        atr_source=atr_source(),
        tick_store=FakeTickStore(ticks),
        config=load_label_config(),
    )
    assert result["entry_delay_ms"] == 100
    assert result["entry_price"] == pytest.approx(100.2)
    assert result["exit_price"] == pytest.approx(101.8)
    assert result["exit_reason"] == "TARGET"
    assert result["gross_r"] == pytest.approx(1.6)


def test_gap_through_stop_uses_observed_quote() -> None:
    ticks = [
        Tick(DECISION_MS + 100, 100.0, 100.2),
        Tick(DECISION_MS + 500, 98.5, 98.7),
    ]
    result = label_one(
        candidate(),
        atr_source=atr_source(),
        tick_store=FakeTickStore(ticks),
        config=load_label_config(),
    )
    assert result["planned_stop"] == pytest.approx(99.2)
    assert result["exit_price"] == pytest.approx(98.5)
    assert result["gross_r"] == pytest.approx(-1.7)


def test_short_enters_bid_and_exits_ask() -> None:
    ticks = [
        Tick(DECISION_MS + 100, 100.0, 100.2),
        Tick(DECISION_MS + 500, 98.2, 98.4),
    ]
    result = label_one(
        candidate(direction="SHORT"),
        atr_source=atr_source(),
        tick_store=FakeTickStore(ticks),
        config=load_label_config(),
    )
    assert result["entry_price"] == pytest.approx(100.0)
    assert result["exit_price"] == pytest.approx(98.4)
    assert result["exit_reason"] == "TARGET"


def test_timeout_uses_first_side_correct_quote_at_deadline() -> None:
    deadline = DECISION_MS + 100 + 30 * 60_000
    ticks = [
        Tick(DECISION_MS + 100, 100.0, 100.2),
        Tick(deadline, 100.4, 100.6),
    ]
    result = label_one(
        candidate(),
        atr_source=atr_source(),
        tick_store=FakeTickStore(ticks),
        config=load_label_config(),
    )
    assert result["exit_reason"] == "TIMEOUT"
    assert result["exit_price"] == pytest.approx(100.4)


def test_missing_completed_atr_preserves_split_in_rejection() -> None:
    empty_atr = CompletedM5Atr(
        pd.DataFrame({"timestamp_ms": [DECISION_MS], "atr": [2.0]}),
        bar_width_ms=300_000,
    )
    result = label_one(
        candidate(),
        atr_source=empty_atr,
        tick_store=FakeTickStore([]),
        config=load_label_config(),
    )
    assert result["status"] == "INELIGIBLE"
    assert result["reason"] == "NO_COMPLETED_ATR"
    assert result["split"] == "exam"


def test_duplicate_candidates_are_refused() -> None:
    candidates = pd.DataFrame([candidate(), candidate()])
    with pytest.raises(SpotLabelError, match="duplicate"):
        label_candidates(
            candidates,
            atr_source=atr_source(),
            tick_store=FakeTickStore([]),
            config=load_label_config(),
        )


def test_label_contract_is_research_only_and_causal() -> None:
    controls = load_label_config()["research_controls"]
    assert controls["entry_strictly_after_signal"] is True
    assert controls["atr_from_completed_m5_bar_only"] is True
    assert controls["side_correct_bid_ask_execution"] is True
    assert controls["gap_through_uses_observed_quote"] is True
    assert controls["broker_action_authorized"] is False
