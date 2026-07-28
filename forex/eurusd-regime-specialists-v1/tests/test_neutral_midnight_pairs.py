from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_midnight_pairs import (  # noqa: E402
    aggregate_days,
    aggregate_pairs,
    build_candidates,
    simulate,
)


def config() -> dict:
    return {
        "strategy": {
            "anchor_hour_utc": 0,
            "pair_offsets_minutes": [0, 5],
            "sides_each_pair": ["LONG", "SHORT"],
            "required_trades_per_eligible_day": 4,
        },
        "neutral_ownership": {
            "requires_direction": "NEUTRAL",
        },
        "execution": {
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
            "risk_pips": 4.0,
            "target_r": 1.5,
            "maximum_hold_hours": 12,
            "risk_per_ticket_portfolio_r": 0.25,
        },
        "windows": {
            "test": [
                "2026-01-05T00:00:00Z",
                "2026-01-05T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def m5_frame() -> pd.DataFrame:
    index = pd.date_range(
        "2026-01-05T00:00:00Z",
        periods=146,
        freq="5min",
    )
    bid_open = [1.1000] * len(index)
    bid_high = [1.1001] * len(index)
    bid_low = [1.0999] * len(index)
    bid_close = [1.1000] * len(index)
    bid_high[1] = 1.1008
    bid_close[1] = 1.1007
    frame = pd.DataFrame(
        {
            "timestamp_ms": index.astype("int64") // 1_000_000,
            "bid_open": bid_open,
            "bid_high": bid_high,
            "bid_low": bid_low,
            "bid_close": bid_close,
            "ask_open": [value + 0.00007 for value in bid_open],
            "ask_high": [value + 0.00007 for value in bid_high],
            "ask_low": [value + 0.00007 for value in bid_low],
            "ask_close": [value + 0.00007 for value in bid_close],
            "tick_count": [100.0] * len(index),
        },
        index=index,
    )
    return frame


def neutral_state(direction: str = "NEUTRAL") -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [pd.Timestamp("2026-01-04T23:00:00Z")],
        name="timestamp_utc",
    )
    return pd.DataFrame(
        {
            "direction": [direction],
            "shock": [False],
            "DXY_compressed": [False],
            "EURUSD_compressed": [False],
        },
        index=index,
    )


def test_neutral_day_creates_two_dual_side_pairs() -> None:
    candidates, days, census = build_candidates(
        m5_frame(),
        neutral_state(),
        config(),
        enforce_frozen_census=False,
    )
    assert len(days) == 1
    assert len(candidates) == 4
    assert candidates["pair_id"].nunique() == 2
    assert set(candidates["side"]) == {"LONG", "SHORT"}
    assert census["eligible_day_exact_four_coverage"] == 1.0


def test_non_neutral_day_creates_no_tickets() -> None:
    candidates, _, census = build_candidates(
        m5_frame(),
        neutral_state("USD_UP"),
        config(),
        enforce_frozen_census=False,
    )
    assert candidates.empty
    assert census["eligible_days"] == 0


def test_both_sides_are_retained_and_accounted_independently() -> None:
    frame = m5_frame()
    candidates, _, _ = build_candidates(
        frame,
        neutral_state(),
        config(),
        enforce_frozen_census=False,
    )
    trades, diagnostics = simulate(candidates, frame, config())
    assert len(trades) == 4
    assert len(diagnostics) == 4
    assert diagnostics["status"].eq("EXECUTED").all()
    assert (
        trades.groupby("pair_id")["side"].nunique().eq(2).all()
    )


def test_pair_and_daily_portfolio_aggregation() -> None:
    frame = m5_frame()
    candidates, _, _ = build_candidates(
        frame,
        neutral_state(),
        config(),
        enforce_frozen_census=False,
    )
    trades, _ = simulate(candidates, frame, config())
    pairs = aggregate_pairs(trades)
    days = aggregate_days(trades)
    assert len(pairs) == 2
    assert pairs["tickets"].eq(2).all()
    assert len(days) == 1
    assert days.iloc[0]["tickets"] == 4
    assert days.iloc[0]["pairs"] == 2
    assert abs(
        days.iloc[0]["r"] - trades["portfolio_r"].sum()
    ) < 1e-12
