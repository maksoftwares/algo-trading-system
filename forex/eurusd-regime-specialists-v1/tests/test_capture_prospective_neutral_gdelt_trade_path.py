from __future__ import annotations

import pandas as pd

from capture_prospective_neutral_gdelt_relative_tone import (
    load_and_verify_preregistration,
)
from capture_prospective_neutral_gdelt_trade_path import (
    execute_ticks,
    path_capture_ready,
    required_path_hours,
)


def _decision(side: str) -> dict[str, str]:
    return {
        "entry_date_utc": "2026-07-29",
        "side": side,
    }


def _ticks(prices: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        prices,
        columns=["timestamp_utc", "bid", "ask"],
    )


def test_path_clock_is_exactly_four_hours_plus_lag() -> None:
    assert len(required_path_hours("2026-07-29T00:20:00Z")) == 5
    assert not path_capture_ready(
        "2026-07-29T00:20:00Z",
        "2026-07-29T04:20:59Z",
    )
    assert path_capture_ready(
        "2026-07-29T00:20:00Z",
        "2026-07-29T04:21:00Z",
    )


def test_long_target_uses_bid_and_adverse_slippage() -> None:
    config, _ = load_and_verify_preregistration()
    ticks = _ticks(
        [
            ("2026-07-29T00:20:00Z", 1.10000, 1.10010),
            ("2026-07-29T01:00:00Z", 1.10080, 1.10090),
        ]
    )
    result = execute_ticks(_decision("LONG"), ticks, config)
    assert result["status"] == "CLOSED"
    assert result["exit_reason"] == "TARGET"
    assert result["entry_fill"] == 1.10011
    assert result["exit_fill"] == 1.10079
    assert result["r"] > 1.35


def test_short_stop_uses_ask_and_adverse_slippage() -> None:
    config, _ = load_and_verify_preregistration()
    ticks = _ticks(
        [
            ("2026-07-29T00:20:00Z", 1.10000, 1.10010),
            ("2026-07-29T00:30:00Z", 1.10040, 1.10050),
        ]
    )
    result = execute_ticks(_decision("SHORT"), ticks, config)
    assert result["status"] == "CLOSED"
    assert result["exit_reason"] == "STOP"
    assert result["r"] < -1.0


def test_excess_spread_and_time_exit_are_deterministic() -> None:
    config, _ = load_and_verify_preregistration()
    wide = _ticks(
        [("2026-07-29T00:20:00Z", 1.10000, 1.10020)]
    )
    rejected = execute_ticks(_decision("LONG"), wide, config)
    assert rejected["status"] == "NO_TRADE_EXCESS_ENTRY_SPREAD"
    quiet = _ticks(
        [
            ("2026-07-29T00:20:00Z", 1.10000, 1.10005),
            ("2026-07-29T04:20:00Z", 1.10010, 1.10015),
        ]
    )
    timed = execute_ticks(_decision("LONG"), quiet, config)
    assert timed["status"] == "CLOSED"
    assert timed["exit_reason"] == "TIME"
    assert timed["effective_spread_pips"] == 0.7
