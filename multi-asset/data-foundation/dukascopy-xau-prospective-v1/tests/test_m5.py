from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.m5 import aggregate_ticks


@dataclass
class Tick:
    timestamp_ms: int
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float


def test_aggregate_ticks_preserves_bid_ask_and_microstructure() -> None:
    result = aggregate_ticks(
        [
            Tick(0, 99.0, 101.0, 3.0, 1.0),
            Tick(60_000, 100.0, 102.0, 1.0, 3.0),
            Tick(300_000, 101.0, 103.0, 1.0, 1.0),
        ]
    )
    assert len(result) == 2
    first = result.iloc[0]
    assert first["bid_open"] == 99.0
    assert first["bid_close"] == 100.0
    assert first["ask_high"] == 102.0
    assert first["xau_tick_count"] == 2
    assert first["tick_signed_move"] == 1.0
    assert first["tick_move_count"] == 1
    assert first["tick_book_imbalance_mean"] == pytest.approx(0.0)
    assert first["tick_microprice_edge_mean"] == pytest.approx(0.0)
