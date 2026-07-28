from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_opening_drive import (  # noqa: E402
    build_drive_candidates,
    simulate,
)


def config() -> dict:
    return {
        "strategy": {
            "anchor_hours_utc": [0],
            "observation_window_minutes": 30,
            "minimum_absolute_body_pips": 4.0,
            "minimum_directional_close_location": 0.75,
            "maximum_trades_per_utc_day": 4,
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
        },
        "windows": {
            "test": [
                "2026-01-05T00:00:00Z",
                "2026-01-05T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
    }


def bullish_m5() -> pd.DataFrame:
    index = pd.date_range(
        "2026-01-05T00:00:00Z", periods=10, freq="5min"
    )
    bid_open = [
        1.10000,
        1.10010,
        1.10020,
        1.10030,
        1.10040,
        1.10050,
        1.10062,
        1.10070,
        1.10100,
        1.10120,
    ]
    bid_close = [
        1.10010,
        1.10020,
        1.10030,
        1.10040,
        1.10050,
        1.10060,
        1.10070,
        1.10100,
        1.10120,
        1.10140,
    ]
    frame = pd.DataFrame(
        {
            "timestamp_ms": index.astype("int64") // 1_000_000,
            "bid_open": bid_open,
            "bid_high": [value + 0.00005 for value in bid_close],
            "bid_low": [value - 0.00005 for value in bid_open],
            "bid_close": bid_close,
            "ask_open": [value + 0.00002 for value in bid_open],
            "ask_high": [
                value + 0.00007 for value in bid_close
            ],
            "ask_low": [value - 0.00003 for value in bid_open],
            "ask_close": [
                value + 0.00002 for value in bid_close
            ],
            "tick_count": [100.0] * len(index),
        },
        index=index,
    )
    return frame


def neutral_state() -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [pd.Timestamp("2026-01-04T23:00:00Z")],
        name="timestamp_utc",
    )
    return pd.DataFrame(
        {
            "direction": ["NEUTRAL"],
            "shock": [False],
            "DXY_compressed": [False],
            "EURUSD_compressed": [False],
        },
        index=index,
    )


def test_completed_bullish_opening_drive_selects_long() -> None:
    candidates, census = build_drive_candidates(
        bullish_m5(),
        neutral_state(),
        config(),
        enforce_frozen_census=False,
    )
    assert len(candidates) == 1
    assert candidates.iloc[0]["side"] == "LONG"
    assert candidates.iloc[0]["entry_time_utc"] == pd.Timestamp(
        "2026-01-05T00:30:00Z"
    )
    assert census["trade_candidates"] == 1


def test_entry_bar_does_not_change_completed_drive_signal() -> None:
    frame = bullish_m5()
    frame.loc[
        pd.Timestamp("2026-01-05T00:30:00Z"),
        ["bid_open", "bid_high", "bid_low", "bid_close"],
    ] = [1.0990, 1.0991, 1.0988, 1.0989]
    candidates, _ = build_drive_candidates(
        frame,
        neutral_state(),
        config(),
        enforce_frozen_census=False,
    )
    assert candidates.iloc[0]["side"] == "LONG"


def test_subthreshold_drive_remains_cash() -> None:
    frame = bullish_m5()
    frame.loc[
        frame.index[:6],
        ["bid_open", "bid_high", "bid_low", "bid_close"],
    ] = [1.10000, 1.10015, 1.09995, 1.10010]
    candidates, census = build_drive_candidates(
        frame,
        neutral_state(),
        config(),
        enforce_frozen_census=False,
    )
    assert candidates.iloc[0]["side"] == "CASH"
    assert census["trade_candidates"] == 0


def test_simulation_enters_only_after_observation_completion() -> None:
    frame = bullish_m5()
    candidates, _ = build_drive_candidates(
        frame,
        neutral_state(),
        config(),
        enforce_frozen_census=False,
    )
    trades, diagnostics = simulate(candidates, frame, config())
    assert len(trades) == 1
    assert trades.iloc[0]["entry_time_utc"] == pd.Timestamp(
        "2026-01-05T00:30:00Z"
    )
    assert diagnostics.iloc[0]["status"] == "EXECUTED"
