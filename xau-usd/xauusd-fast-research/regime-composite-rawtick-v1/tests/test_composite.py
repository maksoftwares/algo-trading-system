from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from composite import (  # noqa: E402
    build_composite_trades,
    execute_candidate,
    first_stop_hit,
)


@dataclass(frozen=True)
class Quote:
    timestamp_ms: int
    bid: float
    ask: float


class Store:
    def __init__(self, times: list[int], bids: list[float], asks: list[float]):
        self.times = np.asarray(times, dtype=np.int64)
        self.bids = np.asarray(bids, dtype=float)
        self.asks = np.asarray(asks, dtype=float)

    def segments(self, start_ms: int, end_ms: int):
        mask = (self.times >= start_ms) & (self.times <= end_ms)
        if mask.any():
            yield self.times[mask], self.bids[mask], self.asks[mask]

    def first_quote_at_or_after(
        self, timestamp_ms: int, maximum_delay_ms: int
    ) -> Quote | None:
        indices = np.flatnonzero(
            (self.times >= timestamp_ms)
            & (self.times <= timestamp_ms + maximum_delay_ms)
        )
        if len(indices) == 0:
            return None
        index = int(indices[0])
        return Quote(
            int(self.times[index]), float(self.bids[index]), float(self.asks[index])
        )


def execution() -> dict[str, float]:
    return {
        "maximum_entry_gap_minutes": 10,
        "maximum_horizon_gap_hours": 96,
        "maximum_entry_spread_r": 0.15,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.3,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
    }


def candidate(direction: int = 1) -> pd.Series:
    return pd.Series(
        {
            "candidate_id": "candidate",
            "composite_id": "composite",
            "origin_attempt": 1,
            "origin_variant_id": "variant",
            "regime_owner": "TEST",
            "mechanic": "TEST",
            "signal_time": pd.Timestamp("2026-01-01T00:00:00Z"),
            "scheduled_entry_time": pd.Timestamp("2026-01-01T01:00:00Z"),
            "direction_sign": direction,
            "signal_atr": 10.0,
            "stop_atr": 1.0,
            "hold_hours": 2.0,
        }
    )


def test_long_stop_uses_bid_and_observed_slippage() -> None:
    store = Store([1, 2], [100.0, 89.0], [100.2, 89.2])
    hit = first_stop_hit(store, 1, 2, 1, 90.0, Quote)
    assert hit is not None
    assert hit[1] == pytest.approx(89.0)
    assert hit[2] == "STOP_SLIPPAGE"


def test_short_stop_uses_ask_and_observed_slippage() -> None:
    store = Store([1, 2], [100.0, 110.5], [100.2, 110.8])
    hit = first_stop_hit(store, 1, 2, -1, 110.0, Quote)
    assert hit is not None
    assert hit[1] == pytest.approx(110.8)
    assert hit[2] == "STOP_SLIPPAGE"


def test_horizon_uses_first_quote_at_or_after_deadline() -> None:
    entry_ms = int(pd.Timestamp("2026-01-01T01:00:00Z").value // 1_000_000)
    deadline_ms = int(pd.Timestamp("2026-01-01T03:00:00Z").value // 1_000_000)
    store = Store(
        [entry_ms, deadline_ms + 2_000],
        [100.0, 102.0],
        [100.2, 102.2],
    )
    outcome, reason = execute_candidate(
        candidate(1), store, Quote, execution()
    )
    assert reason is None
    assert outcome is not None
    assert outcome["entry_price"] == pytest.approx(100.2)
    assert outcome["exit_price"] == pytest.approx(102.0)
    assert outcome["horizon_delay_minutes"] == pytest.approx(2.0 / 60.0)


def test_composite_priority_is_origin_attempt_then_nonoverlap() -> None:
    trades = pd.DataFrame(
        [
            {
                "origin_attempt": 2,
                "entry_time": pd.Timestamp("2026-01-01T01:00:00Z"),
                "exit_time": pd.Timestamp("2026-01-01T03:00:00Z"),
            },
            {
                "origin_attempt": 1,
                "entry_time": pd.Timestamp("2026-01-01T01:00:00Z"),
                "exit_time": pd.Timestamp("2026-01-01T02:00:00Z"),
            },
            {
                "origin_attempt": 2,
                "entry_time": pd.Timestamp("2026-01-01T02:00:00Z"),
                "exit_time": pd.Timestamp("2026-01-01T04:00:00Z"),
            },
        ]
    )
    config = {
        "composites": [
            {
                "attempt_no": 10,
                "composite_id": "C",
                "component_attempts": [1, 2],
            }
        ]
    }
    result = build_composite_trades(trades, config)
    assert result["origin_attempt"].tolist() == [1, 2]
    assert result["attempt_no"].tolist() == [10, 10]
