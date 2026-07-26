from __future__ import annotations

from dataclasses import dataclass

from src.m5 import aggregate_ticks, combine_symbols
from src.snapshot import hour_range, parse_utc


@dataclass
class Tick:
    timestamp_ms: int
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float


def test_hour_range_is_end_exclusive() -> None:
    hours = hour_range(
        parse_utc("2026-07-01T00:00:00Z"),
        parse_utc("2026-07-01T02:00:00Z"),
    )
    assert len(hours) == 2


def test_macro_bar_geometry_and_outer_union() -> None:
    ticks = [
        Tick(1_800_000, 100.0, 100.2, 10.0, 20.0),
        Tick(1_860_000, 101.0, 101.2, 30.0, 40.0),
    ]
    dollar = aggregate_ticks(ticks, "DOLLARIDXUSD")
    bond = aggregate_ticks([], "USTBONDTRUSD")
    combined = combine_symbols({"DOLLARIDXUSD": dollar, "USTBONDTRUSD": bond})
    assert len(combined) == 1
    assert combined.iloc[0]["dollaridxusd_mid_close"] == 101.1
    assert combined.iloc[0]["dollaridxusd_mid_volume"] == 50.0
    assert bool(combined.iloc[0]["dollaridxusd_available"])
    assert not bool(combined.iloc[0]["ustbondtrusd_available"])
