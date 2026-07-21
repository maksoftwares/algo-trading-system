from __future__ import annotations

import pandas as pd

from src.shared_audit import (
    daily_pnl_correlation,
    prepare_v98_ledger,
    route_v98_candidates,
)


def _candidate(
    policy_id: str,
    entry: str,
    exit_: str,
    risk_usd: float,
    attempt_no: int,
) -> dict[str, object]:
    return {
        "attempt_no": attempt_no,
        "policy_id": policy_id,
        "mechanic": "RISK_SIGN_REVERSAL",
        "signal_time": entry,
        "entry_time": entry,
        "exit_time": exit_,
        "direction": "LONG",
        "entry_price": 2000.0,
        "exit_price": 2001.0,
        "risk_usd": risk_usd,
        "net_r": 0.5,
        "stress_net_r": 0.4,
    }


def test_prepare_v98_ledger_reconciles_stress_cost() -> None:
    result = prepare_v98_ledger(
        pd.DataFrame(
            [
                _candidate(
                    "policy-a",
                    "2025-01-02T10:00:00Z",
                    "2025-01-02T11:00:00Z",
                    10.0,
                    1,
                )
            ]
        )
    )
    assert result.loc[0, "pnl_usd"] == 5.0
    assert result.loc[0, "fee_stress_pnl_usd"] == 4.0
    assert result.loc[0, "fee_stress_open_cost_usd"] == 1.0


def test_router_uses_fixed_priority_and_current_portfolio_limits() -> None:
    baseline = pd.DataFrame(
        {
            "trade_id": ["base-addon"],
            "sleeve_id": ["V25_CHOP"],
            "entry_time": [pd.Timestamp("2025-01-02T09:00:00Z")],
            "exit_time": [pd.Timestamp("2025-01-02T11:00:00Z")],
            "risk_usd": [20.0],
            "fee_stress_pnl_usd": [5.0],
        }
    )
    candidates = pd.DataFrame(
        [
            _candidate(
                "policy-a",
                "2025-01-02T10:00:00Z",
                "2025-01-02T12:00:00Z",
                20.0,
                1,
            ),
            _candidate(
                "policy-b",
                "2025-01-02T10:00:00Z",
                "2025-01-02T12:00:00Z",
                5.0,
                2,
            ),
            _candidate(
                "policy-c",
                "2025-01-02T11:30:00Z",
                "2025-01-02T12:30:00Z",
                30.0,
                3,
            ),
        ]
    )
    limits = {
        "maximum_addon_open_positions": 2,
        "maximum_addon_concurrent_initial_risk_usd": 45.0,
        "maximum_v98_entries_per_utc_date": 2,
        "drawdown_suspend_usd": 225.0,
        "drawdown_resume_usd": 180.0,
    }
    accepted, decisions = route_v98_candidates(baseline, candidates, limits)
    assert accepted["policy_id"].tolist() == ["policy-a"]
    assert decisions["reason"].tolist() == [
        "ACCEPTED",
        "DUPLICATE_V98_ENTRY_TIME",
        "MAXIMUM_ADDON_CONCURRENT_INITIAL_RISK_USD",
    ]


def test_router_does_not_look_ahead_to_a_future_frozen_v59_entry() -> None:
    baseline = pd.DataFrame(
        {
            "trade_id": ["future-addon"],
            "sleeve_id": ["V25_CHOP"],
            "entry_time": [pd.Timestamp("2025-01-02T11:00:00Z")],
            "exit_time": [pd.Timestamp("2025-01-02T13:00:00Z")],
            "risk_usd": [30.0],
            "fee_stress_pnl_usd": [5.0],
        }
    )
    candidates = pd.DataFrame(
        [
            _candidate(
                "policy-a",
                "2025-01-02T10:00:00Z",
                "2025-01-02T12:00:00Z",
                20.0,
                1,
            )
        ]
    )
    limits = {
        "maximum_addon_open_positions": 2,
        "maximum_addon_concurrent_initial_risk_usd": 45.0,
        "maximum_v98_entries_per_utc_date": 2,
        "drawdown_suspend_usd": 225.0,
        "drawdown_resume_usd": 180.0,
    }
    accepted, _ = route_v98_candidates(baseline, candidates, limits)
    assert len(accepted) == 1


def test_router_applies_the_frozen_drawdown_suspend_and_resume_levels() -> None:
    baseline = pd.DataFrame(
        {
            "trade_id": ["loss", "recovery"],
            "sleeve_id": ["V59_BROKER_CORE", "V59_BROKER_CORE"],
            "entry_time": pd.to_datetime(
                ["2025-01-01T09:00:00Z", "2025-01-02T10:30:00Z"]
            ),
            "exit_time": pd.to_datetime(
                ["2025-01-02T09:00:00Z", "2025-01-02T11:00:00Z"]
            ),
            "risk_usd": [10.0, 10.0],
            "fee_stress_pnl_usd": [-230.0, 60.0],
        }
    )
    candidates = pd.DataFrame(
        [
            _candidate(
                "policy-a",
                "2025-01-02T10:00:00Z",
                "2025-01-02T10:30:00Z",
                5.0,
                1,
            ),
            _candidate(
                "policy-a",
                "2025-01-02T12:00:00Z",
                "2025-01-02T12:30:00Z",
                5.0,
                1,
            ),
        ]
    )
    limits = {
        "maximum_addon_open_positions": 2,
        "maximum_addon_concurrent_initial_risk_usd": 45.0,
        "maximum_v98_entries_per_utc_date": 2,
        "drawdown_suspend_usd": 225.0,
        "drawdown_resume_usd": 180.0,
    }
    accepted, decisions = route_v98_candidates(baseline, candidates, limits)
    assert accepted["entry_time"].tolist() == [pd.Timestamp("2025-01-02T12:00:00Z")]
    assert decisions["reason"].tolist() == [
        "ACCOUNT_DRAWDOWN_SUSPENDED",
        "ACCEPTED",
    ]


def test_drawdown_hysteresis_remains_suspended_above_the_resume_level() -> None:
    baseline = pd.DataFrame(
        {
            "trade_id": ["loss", "partial-recovery"],
            "sleeve_id": ["V59_BROKER_CORE", "V59_BROKER_CORE"],
            "entry_time": pd.to_datetime(
                ["2025-01-01T09:00:00Z", "2025-01-02T10:30:00Z"]
            ),
            "exit_time": pd.to_datetime(
                ["2025-01-02T09:00:00Z", "2025-01-02T11:00:00Z"]
            ),
            "risk_usd": [10.0, 10.0],
            "fee_stress_pnl_usd": [-230.0, 30.0],
        }
    )
    candidates = pd.DataFrame(
        [
            _candidate(
                "policy-a",
                "2025-01-02T12:00:00Z",
                "2025-01-02T12:30:00Z",
                5.0,
                1,
            )
        ]
    )
    limits = {
        "maximum_addon_open_positions": 2,
        "maximum_addon_concurrent_initial_risk_usd": 45.0,
        "maximum_v98_entries_per_utc_date": 2,
        "drawdown_suspend_usd": 225.0,
        "drawdown_resume_usd": 180.0,
    }
    accepted, decisions = route_v98_candidates(baseline, candidates, limits)
    assert accepted.empty
    assert decisions.loc[0, "reason"] == "ACCOUNT_DRAWDOWN_SUSPENDED"


def test_daily_correlation_attributes_realized_pnl_to_exit_date() -> None:
    baseline = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                ["2025-01-01T23:00:00Z", "2025-01-02T10:00:00Z"]
            ),
            "exit_time": pd.to_datetime(
                ["2025-01-02T01:00:00Z", "2025-01-03T10:00:00Z"]
            ),
            "fee_stress_pnl_usd": [1.0, -1.0],
        }
    )
    addon = baseline.copy()
    correlation = daily_pnl_correlation(
        baseline,
        addon,
        pd.Timestamp("2025-01-01T00:00:00Z"),
        pd.Timestamp("2025-01-04T00:00:00Z"),
    )
    assert correlation == 1.0
