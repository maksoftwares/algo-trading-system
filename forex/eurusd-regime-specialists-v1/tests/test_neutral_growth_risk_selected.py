from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_growth_risk_selected import (
    selected_stage_metrics,
)


def _gate() -> dict:
    return {
        "minimum_trades": 4,
        "minimum_win_rate": 0.4,
        "maximum_win_rate": 0.6,
        "minimum_realized_payoff_ratio": 1.25,
        "maximum_realized_payoff_ratio": 1.85,
        "minimum_profit_factor": 1.1,
        "minimum_expectancy_r": 0.0,
        "minimum_each_side_trades": 2,
        "minimum_each_side_profit_factor": 0.9,
        "minimum_each_expert_trades": 2,
        "minimum_each_expert_profit_factor": 0.9,
        "maximum_drawdown_r": 10.0,
    }


def test_selected_gate_requires_both_frozen_experts() -> None:
    trades = pd.DataFrame(
        {
            "r": [1.5, -1.0, 1.5, -1.0],
            "side": ["LONG", "LONG", "SHORT", "SHORT"],
            "expert": [
                "ASIA_HANDOFF_0300",
                "ASIA_HANDOFF_0300",
                "EUROPE_MORNING_0900",
                "EUROPE_MORNING_0900",
            ],
        }
    )
    result = selected_stage_metrics(
        trades,
        _gate(),
        ["ASIA_HANDOFF_0300", "EUROPE_MORNING_0900"],
    )
    assert result["passed"] is True
    missing = trades.copy()
    missing["expert"] = "ASIA_HANDOFF_0300"
    failed = selected_stage_metrics(
        missing,
        _gate(),
        ["ASIA_HANDOFF_0300", "EUROPE_MORNING_0900"],
    )
    assert failed["gate_results"]["expert_trade_capacity"] is False
    assert failed["passed"] is False
