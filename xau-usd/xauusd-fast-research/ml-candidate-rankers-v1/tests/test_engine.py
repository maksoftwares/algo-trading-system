from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine import _execution_arrays, _label_candidate, _select_trades


def m5(prices: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    starts = pd.date_range("2026-01-05", periods=len(prices), freq="5min", tz="UTC")
    rows = []
    for timestamp, (open_price, high, low, close) in zip(starts, prices):
        row = {
            "bar_start_utc": timestamp,
            "timestamp_utc": timestamp + pd.Timedelta(minutes=5),
        }
        for side, offset in (("bid", -0.1), ("ask", 0.1)):
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


def execution() -> dict:
    return {
        "maximum_entry_gap_minutes": 10,
        "minimum_stop_atr": 0.75,
        "maximum_stop_atr": 3.0,
        "maximum_entry_spread_r": 0.15,
        "ounces_at_lot_size": 1.0,
        "maximum_research_risk_usd": 50.0,
        "extra_execution_cost_usd": 0.30,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
        "current_account_risk_usd": 8.165487,
        "maximum_trades_per_family_utc_day": 2,
        "cooldown_hours": 2,
    }


def test_label_uses_next_ask_and_stop_first() -> None:
    frame = m5([(100, 110, 90, 100), (100, 101, 99, 100)])
    arrays = _execution_arrays(frame)
    candidate = type(
        "Candidate",
        (),
        {
            "signal_time": pd.Timestamp("2026-01-05T00:00:00Z"),
            "direction": "LONG",
            "stop_frozen": 95.0,
            "atr_value": 5.0,
            "target_r": 1.5,
            "maximum_hold_hours": 1,
        },
    )()
    outcome = _label_candidate(arrays, candidate, execution())
    assert outcome is not None
    assert outcome["entry_price"] == pytest.approx(100.1)
    assert outcome["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert outcome["net_r"] == pytest.approx(-1.0)


def test_selection_enforces_daily_cap_and_position_order() -> None:
    entries = pd.date_range("2026-01-05", periods=4, freq="3h", tz="UTC")
    scored = pd.DataFrame(
        {
            "entry_time": entries,
            "exit_time": entries + pd.Timedelta(hours=1),
            "model_score": [0.4, 0.3, 0.2, 0.1],
        }
    )
    selected = _select_trades(scored, 0.0, execution())
    assert len(selected) == 2


def test_execution_arrays_are_timezone_free_for_search() -> None:
    arrays = _execution_arrays(m5([(100, 101, 99, 100)]))
    assert np.issubdtype(arrays["starts"].dtype, np.datetime64)
