from __future__ import annotations

import numpy as np
import pandas as pd

from src import retest


def test_completed_bar_indices_require_bar_end_before_entry() -> None:
    opens = pd.to_datetime(
        ["2026-01-01T10:00:00Z", "2026-01-01T10:05:00Z"], utc=True
    )
    entries = pd.to_datetime(
        [
            "2026-01-01T10:04:59Z",
            "2026-01-01T10:05:00Z",
            "2026-01-01T10:09:59Z",
            "2026-01-01T10:10:00Z",
        ],
        utc=True,
    )
    assert retest.completed_bar_indices(opens, entries).tolist() == [-1, 0, 0, 1]


def test_expanding_rank_uses_history_only_after_current_score() -> None:
    history = [1.0, 2.0]
    ranks = retest.expanding_rank(
        np.array([3.0, 0.0]),
        np.array([0.0, 1.0, 2.0, 3.0]),
        history,
        minimum_history=2,
    )
    assert ranks.tolist() == [1.0, 0.0]
    assert history == [1.0, 2.0, 3.0, 0.0]


def test_closed_metrics_treat_zero_factor_as_skipped_trade() -> None:
    meta = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"], utc=True
            ),
            "exit_time": pd.to_datetime(
                ["2026-01-01T01:00:00Z", "2026-01-02T01:00:00Z"], utc=True
            ),
            retest.PNL: [10.0, -5.0],
        }
    )
    metrics, _, yearly = retest.closed_metrics(meta, np.array([1.0, 0.0]))
    assert metrics["trade_rows"] == 1
    assert metrics["net_pnl_usd"] == 10.0
    assert metrics["win_rate"] == 1.0
    assert yearly.loc[0, "delta_pnl_usd"] == 5.0


def test_week_block_bootstrap_is_deterministic() -> None:
    meta = pd.DataFrame(
        {
            "entry_time": pd.date_range(
                "2025-01-01T00:00:00Z", periods=20, freq="7D"
            )
        }
    )
    delta = np.arange(1.0, 21.0)
    first = retest.moving_week_block_bootstrap(
        meta, delta, repetitions=100, block_weeks=4, seed=7
    )
    second = retest.moving_week_block_bootstrap(
        meta, delta, repetitions=100, block_weeks=4, seed=7
    )
    assert first == second
    assert first["observed_delta_usd"] == float(delta.sum())


def test_risk_gates_reject_unexpressible_lot() -> None:
    floating = {
        "maximum_open_positions": 1,
        "maximum_open_core_positions": 1,
        "maximum_open_addon_positions": 0,
        "maximum_known_initial_risk_usd": 10.0,
        "maximum_floating_drawdown_usd": 10.0,
    }
    limits = {
        "maximum_account_positions": 12,
        "maximum_core_positions": 10,
        "maximum_addon_positions": 2,
        "account_initial_risk_usd": 60.0,
        "floating_drawdown_hard_stop_usd": 100.0,
    }
    audit = {
        "lot_values": [0.015],
        "double_rejections": {},
        "accepted_double_missing_risk_rows": 0,
    }
    gates = retest.risk_gates(floating, limits, audit)
    assert not gates["lot_values_broker_expressible"]


def test_broker_policy_never_doubles_missing_initial_risk() -> None:
    meta = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T02:00:00Z"], utc=True
            ),
            "exit_time": pd.to_datetime(
                ["2026-01-01T01:00:00Z", "2026-01-01T03:00:00Z"], utc=True
            ),
            "risk_usd": [np.nan, 10.0],
            "direction": ["LONG", "LONG"],
            "is_core": [True, True],
            "execution_source_id": ["R1_UPTREND", "R1_UPTREND"],
        }
    )
    contract = {
        "sizing": {
            "broker_policy": {
                "skip_below_multiplier": 0.75,
                "double_above_multiplier": 1.25,
            }
        }
    }
    limits = {
        "account_initial_risk_usd": 60.0,
        "directional_initial_risk_usd": 60.0,
        "addon_initial_risk_usd": 45.0,
    }
    factors, audit = retest.broker_factors(
        meta,
        np.array([1.5, 1.5]),
        {"sources": []},
        limits,
        contract,
    )
    assert factors.tolist() == [1.0, 2.0]
    assert audit["accepted_double_missing_risk_rows"] == 0
    assert audit["double_rejections"] == {"MISSING_INITIAL_RISK": 1}


def test_broker_policy_rejects_double_that_breaks_concurrent_risk() -> None:
    meta = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T00:30:00Z"], utc=True
            ),
            "exit_time": pd.to_datetime(
                ["2026-01-01T02:00:00Z", "2026-01-01T01:00:00Z"], utc=True
            ),
            "risk_usd": [20.0, 10.0],
            "direction": ["LONG", "LONG"],
            "is_core": [True, True],
            "execution_source_id": ["R1_UPTREND", "R1_UPTREND"],
        }
    )
    contract = {
        "sizing": {
            "broker_policy": {
                "skip_below_multiplier": 0.75,
                "double_above_multiplier": 1.25,
            }
        }
    }
    limits = {
        "account_initial_risk_usd": 50.0,
        "directional_initial_risk_usd": 50.0,
        "addon_initial_risk_usd": 45.0,
    }
    factors, audit = retest.broker_factors(
        meta,
        np.array([1.5, 1.5]),
        {"sources": []},
        limits,
        contract,
    )
    assert factors.tolist() == [2.0, 1.0]
    assert audit["double_rejections"] == {"ACCOUNT_RISK_LIMIT": 1}


def test_weighted_floating_metrics_reconstruct_open_position_path() -> None:
    bars = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range(
                "2026-01-01T10:00:00Z", periods=3, freq="5min"
            ),
            "bid_low": [99.0, 103.0, 102.0],
            "bid_high": [101.0, 104.0, 103.0],
            "bid_close": [100.0, 103.0, 102.0],
            "ask_low": [99.1, 103.1, 102.1],
            "ask_high": [101.1, 104.1, 103.1],
            "ask_close": [100.1, 103.1, 102.1],
        }
    )
    meta = pd.DataFrame(
        {
            "trade_id": ["T1"],
            "entry_time": pd.to_datetime(["2026-01-01T10:00:00Z"], utc=True),
            "exit_time": pd.to_datetime(["2026-01-01T10:10:00Z"], utc=True),
            "direction": ["LONG"],
            "is_core": [True],
            "entry_price": [100.0],
            "fee_stress_open_cost_usd": [0.0],
            "risk_usd": [5.0],
            retest.PNL: [2.0],
        }
    )
    metrics = retest.weighted_floating_metrics(
        bars, meta, np.array([1.0])
    )
    assert metrics["maximum_floating_drawdown_usd"] == 2.0
    assert metrics["maximum_open_positions"] == 1
    assert metrics["maximum_known_initial_risk_usd"] == 5.0
    assert metrics["final_close_equity_pnl_usd"] == 2.0
