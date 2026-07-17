from __future__ import annotations

import pandas as pd
import pytest

from engine import _find_entry, _simulate, add_previous_levels, confirmed_swings


def bars(prices: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    starts = pd.date_range("2026-01-04 23:50Z", periods=len(prices), freq="5min")
    rows = []
    for timestamp, (open_price, high, low, close) in zip(starts, prices):
        row = {
            "bar_start_utc": timestamp,
            "bar_end_utc": timestamp + pd.Timedelta(minutes=5),
            "timestamp_utc": timestamp + pd.Timedelta(minutes=5),
        }
        for side, offset in (("mid", 0.0), ("bid", -0.1), ("ask", 0.1)):
            row.update(
                {
                    f"{side}_open": open_price + offset,
                    f"{side}_high": high + offset,
                    f"{side}_low": low + offset,
                    f"{side}_close": close + offset,
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def test_previous_day_uses_bar_start_membership() -> None:
    frame = bars([(100, 101, 99, 100)] * 4)
    result = add_previous_levels(frame)
    assert pd.isna(result.loc[1, "previous_daily_high"])
    assert result.loc[2, "previous_daily_high"] == pytest.approx(101.0)


def test_swing_is_available_only_after_right_bars() -> None:
    frame = bars(
        [
            (1, 1, 0, 1),
            (2, 2, 1, 2),
            (3, 5, 2, 3),
            (3, 4, 2, 3),
            (2, 3, 1, 2),
        ]
    )
    result = confirmed_swings(frame, "HIGH", left=2, right=2)
    assert len(result) == 1
    assert result.iloc[0]["swing_time_utc"] == frame.iloc[2]["timestamp_utc"]
    assert result.iloc[0]["available_time_utc"] == frame.iloc[4]["timestamp_utc"]


def test_pending_long_uses_ask_trigger() -> None:
    frame = bars([(100, 101, 99, 100), (100, 101, 99, 100)])
    signal = pd.Series(
        {
            "signal_time": frame.iloc[0]["timestamp_utc"],
            "direction": "LONG",
            "entry_trigger": 101.05,
            "expires_after_bars": 1,
        }
    )
    entry = _find_entry(frame, signal, {"maximum_native_entry_spread_price": 0.75})
    assert entry is not None
    assert entry[0] == 1
    assert entry[1] == pytest.approx(101.05)


def test_ambiguous_bar_is_stop_first() -> None:
    frame = bars([(100, 110, 90, 100)])
    signal = pd.Series(
        {
            "direction": "LONG",
            "stop_frozen": 95.0,
            "target_r": 1.5,
            "maximum_hold_hours": 1,
        }
    )
    settings = {"minimum_planned_stop_price": 3.75, "maximum_research_stop_price": 50.0}
    costs = {
        "ounces_at_0_01_lot": 1.0,
        "stress_spread_price": 0.75,
        "extra_execution_cost_usd": 0.30,
        "stress_slippage_r": 0.05,
        "maximum_estimated_cost_r": 0.30,
        "preferred_estimated_cost_r": 0.20,
        "holding_cost_per_24h_usd": 0.35,
        "current_account_risk_usd": 8.165487,
    }
    outcome = _simulate(frame, 0, 100.1, signal, settings, costs)
    assert outcome["accepted"]
    assert outcome["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert outcome["baseline_net_r"] == pytest.approx(-1.0)
