from __future__ import annotations

import pandas as pd

from src.router import causal_state_health, eligible_actions, qualified_event_keys


def _actions(outcomes: list[float]) -> pd.DataFrame:
    signal = pd.date_range("2020-01-01", periods=len(outcomes), freq="2h", tz="UTC")
    return pd.DataFrame(
        {
            "signal_time": signal,
            "entry_time": signal,
            "exit_time": signal + pd.Timedelta(hours=1),
            "event_id": [f"E{index}" for index in range(len(outcomes))],
            "action_id": "A",
            "direction": "LONG",
            "mechanism": "BREAK",
            "regime": "TREND_UP",
            "h4adx": "HIGH",
            "stress_net_r": outcomes,
            "risk_usd": 5.0,
            "pnl_usd": [value * 5.0 for value in outcomes],
            "trade_id": [f"T{index}" for index in range(len(outcomes))],
            "current_account_feasible": True,
        }
    )


def test_causal_health_uses_only_outcomes_completed_before_signal() -> None:
    frame = _actions([1.0, -1.0, 2.0, -2.0])
    health = causal_state_health(frame, ["action_id", "direction"], 1, 2)
    assert health.loc[0, "long_count"] == 0
    assert health.loc[1, "long_count"] == 1
    assert health.loc[2, "long_net"] == 0.0
    assert health.loc[3, "long_net"] == 1.0


def test_eligible_actions_excludes_existing_qualified_event() -> None:
    frame = _actions([1.0, 1.0, 1.0, 1.0])
    health = causal_state_health(frame, ["action_id", "direction"], 1, 2)
    existing = pd.DataFrame(
        {"signal_time": [frame.loc[2, "signal_time"]], "direction": ["LONG"]}
    )
    selected = eligible_actions(
        health, qualified_event_keys(existing), 30.0, 1, 2, 1.0
    )
    assert frame.loc[2, "event_id"] not in set(selected["event_id"])
    assert frame.loc[3, "event_id"] in set(selected["event_id"])


def test_health_threshold_cannot_see_current_trade_outcome() -> None:
    frame = _actions([1.0, 1.0, -100.0])
    health = causal_state_health(frame, ["action_id", "direction"], 1, 2)
    selected = eligible_actions(
        health, pd.MultiIndex.from_arrays([[], []]), 30.0, 1, 2, 1.0
    )
    assert frame.loc[2, "event_id"] in set(selected["event_id"])
