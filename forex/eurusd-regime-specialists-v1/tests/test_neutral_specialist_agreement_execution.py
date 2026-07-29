from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_specialist_agreement_execution import (
    simulate_one,
    verify_lock,
)


def _execution() -> dict:
    return {
        "maximum_hold_hours": 1,
        "required_final_bar_at_maximum_hold_clock": True,
        "stop_pips": 4.0,
        "target_pips": 6.0,
        "minimum_retail_spread_pips": 0.7,
        "adverse_slippage_pips_per_side": 0.1,
        "extra_round_trip_stress_pips": 0.5,
    }


def _candidate(side: str = "LONG") -> pd.Series:
    return pd.Series(
        {
            "eligible_date": "2023-01-02",
            "entry_time_utc": pd.Timestamp("2023-01-02T00:00:00Z"),
            "side": side,
            "distinct_experts": 2,
            "expert_combination": "A|B",
        }
    )


def test_execution_contract_is_frozen_before_price_path() -> None:
    lock = verify_lock()
    assert lock["oracle_decision_use_allowed"] is False
    assert lock["broker_action_allowed"] is False


def test_long_same_bar_is_stop_first_with_costs() -> None:
    index = pd.DatetimeIndex(
        [
            pd.Timestamp("2023-01-02T00:00:00Z"),
            pd.Timestamp("2023-01-02T01:00:00Z"),
        ]
    )
    m5 = pd.DataFrame(
        {
            "bid_open": [1.1000, 1.1000],
            "bid_high": [1.1010, 1.1000],
            "bid_low": [1.0990, 1.1000],
            "bid_close": [1.1000, 1.1000],
            "ask_open": [1.1001, 1.1001],
            "ask_high": [1.1011, 1.1001],
            "ask_low": [1.0991, 1.1001],
            "ask_close": [1.1001, 1.1001],
        },
        index=index,
    )
    result = simulate_one(_candidate(), m5, _execution())
    assert result["status"] == "CLOSED"
    assert result["exit_reason"] == "STOP"
    assert abs(result["r"] + 1.025) < 1e-9
    assert abs(result["extra_half_pip_stress_r"] + 1.15) < 1e-9


def test_incomplete_maximum_hold_path_is_cash() -> None:
    index = pd.DatetimeIndex([pd.Timestamp("2023-01-02T00:00:00Z")])
    m5 = pd.DataFrame(
        {
            "bid_open": [1.1000],
            "bid_high": [1.1001],
            "bid_low": [1.0999],
            "bid_close": [1.1000],
            "ask_open": [1.1001],
            "ask_high": [1.1002],
            "ask_low": [1.1000],
            "ask_close": [1.1001],
        },
        index=index,
    )
    result = simulate_one(_candidate(), m5, _execution())
    assert result["status"] == "CASH_INCOMPLETE_MAXIMUM_HOLD_PATH"
