from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists import (
    neutral_0608_range_breakout_transfer_execution as module,
)


def _execution() -> dict:
    return {
        "maximum_hold_hours": 0,
        "required_final_bar_at_maximum_hold_clock": True,
        "minimum_retail_spread_pips": 0.7,
        "adverse_slippage_pips_per_side": 0.1,
        "entry_price_tolerance": 1e-12,
        "target_r": 1.5,
        "extra_round_trip_stress_pips": 0.5,
    }


def _bar(
    *,
    bid_open: float,
    bid_high: float,
    bid_low: float,
    bid_close: float,
) -> pd.DataFrame:
    timestamp = pd.Timestamp("2026-01-05T08:00:00Z")
    return pd.DataFrame(
        {
            "bid_open": [bid_open],
            "bid_high": [bid_high],
            "bid_low": [bid_low],
            "bid_close": [bid_close],
            "ask_open": [bid_open + 0.00007],
            "ask_high": [bid_high + 0.00007],
            "ask_low": [bid_low + 0.00007],
            "ask_close": [bid_close + 0.00007],
        },
        index=pd.DatetimeIndex([timestamp]),
    )


def _candidate(
    *,
    side: str,
    entry: float,
    stop: float,
) -> pd.Series:
    return pd.Series(
        {
            "family": "FRESH_TEST",
            "signal_time_utc": pd.Timestamp(
                "2026-01-05T07:45:00Z"
            ),
            "entry_time_utc": pd.Timestamp(
                "2026-01-05T08:00:00Z"
            ),
            "side": side,
            "window": "OOS_2026_H1",
            "entry_price_decision_time": entry,
            "stop_price_decision_time": stop,
            "risk_distance": abs(entry - stop),
            "risk_pips": abs(entry - stop) / 0.0001,
        }
    )


def test_same_bar_ambiguity_is_stop_first() -> None:
    m5 = _bar(
        bid_open=1.00000,
        bid_high=1.00040,
        bid_low=0.99980,
        bid_close=1.00010,
    )
    candidate = _candidate(
        side="LONG",
        entry=1.00008,
        stop=0.99990,
    )

    result = module.simulate_one(
        candidate, m5, _execution()
    )

    assert result["status"] == "CLOSED"
    assert result["exit_reason"] == "STOP"
    assert result["r"] < -1.0


def test_target_uses_frozen_one_point_five_r() -> None:
    m5 = _bar(
        bid_open=1.00000,
        bid_high=1.00050,
        bid_low=1.00001,
        bid_close=1.00030,
    )
    candidate = _candidate(
        side="LONG",
        entry=1.00008,
        stop=1.00000,
    )

    result = module.simulate_one(
        candidate, m5, _execution()
    )

    assert result["exit_reason"] == "TARGET"
    assert abs(result["target_price"] - 1.00020) < 1e-12
    assert 1.3 < result["r"] < 1.5


def test_payoff_metrics_keep_breakevens_separate() -> None:
    frame = pd.DataFrame({"r": [1.5, 1.0, -1.0, 0.0]})

    metrics = module.payoff_metrics(frame)

    assert metrics["wins"] == 2
    assert metrics["losses"] == 1
    assert metrics["breakevens"] == 1
    assert metrics["win_rate"] == 0.5
    assert metrics["realized_payoff_ratio"] == 1.25
    assert metrics["profit_factor"] == 2.5


def test_oracle_matching_is_same_side_one_to_one() -> None:
    trades = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                [
                    "2026-01-05T08:00:00Z",
                    "2026-01-05T08:05:00Z",
                ],
                utc=True,
            ),
            "side": ["LONG", "LONG"],
        }
    )
    oracle = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2026-01-05T08:03:00Z"],
                utc=True,
            ),
            "side": ["LONG"],
        }
    )

    matches = module._greedy_one_to_one_matches(
        trades, oracle, 15
    )

    assert len(matches) == 1
    assert 1 in matches


def test_execution_preregistration_lock_verifies() -> None:
    checked = module.verify_lock()

    assert len(checked) >= 8
