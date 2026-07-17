from __future__ import annotations

import pandas as pd
import pytest

from data import aggregate_complete_bars
from research import _simulate_trade, attach_regime, evaluate_gate


def _m5(prices: list[tuple[float, float, float, float]]) -> pd.DataFrame:
    starts = pd.date_range("2026-01-05", periods=len(prices), freq="5min", tz="UTC")
    rows = []
    for timestamp, (open_price, high, low, close) in zip(starts, prices):
        row = {
            "bar_start_utc": timestamp,
            "bar_end_utc": timestamp + pd.Timedelta(minutes=5),
            "timestamp_utc": timestamp + pd.Timedelta(minutes=5),
            "tick_count": 10,
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


def test_aggregate_drops_incomplete_bucket() -> None:
    bars = _m5([(100, 101, 99, 100)] * 7).drop(index=1).reset_index(drop=True)
    result = aggregate_complete_bars(bars, 15, "M15")
    assert len(result) == 1
    assert result.iloc[0]["bar_start_utc"] == pd.Timestamp("2026-01-05 00:15:00Z")


def test_regime_attachment_never_uses_future_h4_close() -> None:
    bars = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2026-01-05 03:00Z", "2026-01-05 04:00Z"], utc=True
            )
        }
    )
    h4 = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2026-01-05 00:00Z", "2026-01-05 04:00Z"], utc=True
            ),
            "regime": ["CHOP", "TREND_UP"],
            "atr_h4": [1.0, 2.0],
            "adx_h4": [10.0, 30.0],
            "er_h4": [0.1, 0.5],
            "ema_slope_atr_h4": [0.0, 0.3],
            "range_width_atr_h4": [3.0, 5.0],
            "displacement_atr_h4": [0.2, 2.0],
        }
    )
    result = attach_regime(bars, h4)
    assert result["regime"].tolist() == ["CHOP", "TREND_UP"]


def test_m5_collision_is_stop_first_and_uses_side_prices() -> None:
    bars = _m5([(100.0, 103.0, 98.0, 101.0)])
    signal = pd.Series(
        {
            "direction": "LONG",
            "stop_frozen": 99.0,
            "atr_value": 1.0,
            "minimum_stop_atr": 0.5,
            "maximum_stop_atr": 2.0,
            "target_kind": "R_MULTIPLE",
            "target_value": 1.0,
            "maximum_hold_hours": 1,
        }
    )
    execution = {
        "maximum_entry_spread_r": 0.2,
        "ounces_at_lot_size": 1.0,
        "maximum_research_risk_usd": 50.0,
        "extra_execution_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.0,
        "current_account_risk_usd": 8.0,
    }
    outcome = _simulate_trade(bars, 0, signal, execution)
    assert outcome["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert outcome["net_r"] == pytest.approx(-1.0)
    assert outcome["entry_price"] == pytest.approx(100.1)


def test_gate_requires_winner_removal_robustness() -> None:
    value = {
        "trades": 100,
        "stress_pf": 2.0,
        "average_stress_r": 0.2,
        "positive_active_month_share": 0.6,
        "closed_drawdown_r": 5.0,
        "top_winners_removed_stress_net_r": -0.1,
        "trades_per_source_day": 0.1,
    }
    gate = {
        "minimum_trades": 80,
        "minimum_stress_pf": 1.1,
        "minimum_average_stress_r": 0.02,
        "minimum_positive_active_month_share": 0.5,
        "maximum_closed_drawdown_r": 30.0,
    }
    passed, checks = evaluate_gate(value, gate)
    assert not passed
    assert not checks["top_winners_removed_positive"]
