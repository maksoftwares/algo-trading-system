from __future__ import annotations

import pandas as pd

from backtest import _funding_weights, _simulate
from strategies import TREND_ID


def _m5(rows: list[tuple[str, float, float, float, float]]) -> pd.DataFrame:
    records = []
    for stamp, bid_open, bid_high, bid_low, bid_close in rows:
        start = pd.Timestamp(stamp, tz="UTC")
        spread = 0.10
        records.append({
            "bar_start_utc": start,
            "timestamp_utc": start + pd.Timedelta(minutes=5),
            "bid_open": bid_open,
            "bid_high": bid_high,
            "bid_low": bid_low,
            "bid_close": bid_close,
            "ask_open": bid_open + spread,
            "ask_high": bid_high + spread,
            "ask_low": bid_low + spread,
            "ask_close": bid_close + spread,
            "mid_open": bid_open + spread / 2,
            "spread_open_points": 10.0,
            "stress_spread_points": 20.0,
            "regime_at_open": "TREND_UP",
        })
    return pd.DataFrame(records)


def _signal(**overrides: object) -> pd.Series:
    values: dict[str, object] = {
        "direction": "LONG",
        "strategy_id": TREND_ID,
        "stop_frozen": 99.10,
        "atr15": 1.0,
        "min_stop_atr": 0.75,
        "max_stop_atr": 2.0,
        "target_kind": "R_MULTIPLE",
        "target_value": 2.0,
        "minimum_reward_r": 2.0,
        "max_hold_hours": 24,
    }
    values.update(overrides)
    return pd.Series(values)


def _config(**account_overrides: float) -> dict:
    account = {
        "equity_usd": 1000.0,
        "risk_fraction": 0.005,
        "leverage": 100,
        "contract_size_oz": 100.0,
        "volume_min": 0.01,
        "volume_step": 0.01,
        "margin_limit_fraction": 0.20,
        "free_margin_floor_fraction": 0.80,
        "order_calc_margin_rate": 0.005,
    }
    account.update(account_overrides)
    return {
        "account": account,
        "costs": {
            "swap_rollover3days_python_weekday": 4,
            "funding_snapshot_long_pct": 0.0,
            "funding_snapshot_short_pct": 0.0,
            "funding_day_basis": 360,
            "stress_funding_multiplier": 1.25,
            "stress_slippage_r": 0.05,
        },
    }


def test_gap_through_stop_fills_at_worse_open() -> None:
    bars = _m5([
        ("2020-01-01 00:00", 100.00, 100.20, 99.80, 100.00),
        ("2020-01-01 00:05", 98.80, 99.00, 98.50, 98.90),
    ])
    result = _simulate(bars, bars.iloc[0]["bar_start_utc"], _signal(), _config())
    assert result["accepted"] is True
    assert result["exit_reason"] == "GAP_THROUGH_STOP"
    assert result["exit_price"] == 98.80


def test_ambiguous_bar_is_stop_first() -> None:
    bars = _m5([("2020-01-01 00:00", 100.00, 103.00, 98.90, 100.00)])
    result = _simulate(bars, bars.iloc[0]["bar_start_utc"], _signal(), _config())
    assert result["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert result["ambiguous_m5"] is True
    assert result["exit_price"] == 99.10


def test_minimum_contract_stop_loss_and_actual_margin_are_enforced() -> None:
    bars = _m5([("2020-01-01 00:00", 100.00, 100.10, 99.90, 100.00)])
    too_wide = _simulate(
        bars,
        bars.iloc[0]["bar_start_utc"],
        _signal(stop_frozen=94.10, atr15=4.0, min_stop_atr=1.0, max_stop_atr=2.0),
        _config(),
    )
    margin_bound = _simulate(bars, bars.iloc[0]["bar_start_utc"], _signal(), _config(order_calc_margin_rate=0.50))
    assert too_wide["rejection_reason"] == "CONTRACT_GRANULARITY_OR_MARGIN_REJECT"
    assert too_wide["sizing_rejection_category"] == "CONTRACT_GRANULARITY_REJECT"
    assert too_wide["minimum_volume_stop_loss_usd"] > 5.0
    assert margin_bound["rejection_reason"] == "CONTRACT_GRANULARITY_OR_MARGIN_REJECT"
    assert margin_bound["sizing_rejection_category"] == "MARGIN_REJECT"
    assert margin_bound["required_margin_usd"] > 200.0


def test_funding_weight_applies_triple_friday_rollover() -> None:
    thursday = pd.Timestamp("2020-01-02 12:00", tz="UTC")
    saturday = pd.Timestamp("2020-01-04 12:00", tz="UTC")
    assert _funding_weights(thursday, saturday, triple_weekday=4) == 4.0
