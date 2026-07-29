from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_online_expert_aggregation import (
    select_online_trades,
    verify_lock,
    weighted_expert_score,
)


def _trade(
    expert: str,
    entry: str,
    exit_: str,
    r: float,
    source_row: int,
) -> dict:
    return {
        "expert_id": expert,
        "mechanism": expert,
        "entry_time_utc": pd.Timestamp(entry),
        "exit_time_utc": pd.Timestamp(exit_),
        "side": "LONG" if source_row % 2 == 0 else "SHORT",
        "r": r,
        "extra_half_pip_stress_r": r - 0.05,
        "source_row": source_row,
    }


def _config() -> dict:
    return {
        "evaluation_start_utc": "2023-01-01T00:00:00Z",
        "evaluation_end_utc": "2023-12-31T23:59:59Z",
        "policy": {
            "minimum_lifetime_closed_trades": 1,
            "minimum_effective_closed_trades": 0.1,
            "stress_outcome_column": "extra_half_pip_stress_r",
        },
    }


def test_contract_is_frozen_before_combined_outcome() -> None:
    checked = verify_lock()
    assert "config/frozen_neutral_online_expert_aggregation.json" in checked


def test_score_uses_only_strictly_prior_closed_outcomes() -> None:
    history = pd.DataFrame(
        [
            _trade(
                "A",
                "2022-12-01T00:00:00Z",
                "2022-12-02T00:00:00Z",
                1.5,
                0,
            ),
            _trade(
                "A",
                "2022-12-31T00:00:00Z",
                "2023-01-01T00:00:00Z",
                -1.0,
                1,
            ),
        ]
    )
    score = weighted_expert_score(
        history,
        decision_time_utc="2023-01-01T00:00:00Z",
        half_life_days=126,
        minimum_lifetime_closed_trades=1,
        minimum_effective_closed_trades=0.1,
    )
    assert score["lifetime_closed_trades"] == 1
    assert score["weighted_mean_r"] == 1.5
    assert score["latest_known_exit_utc"] == pd.Timestamp(
        "2022-12-02T00:00:00Z"
    )


def test_selector_enforces_one_trade_per_day_and_no_overlap() -> None:
    rows = [
        _trade(
            "A",
            "2022-12-01T00:00:00Z",
            "2022-12-01T01:00:00Z",
            1.5,
            0,
        ),
        _trade(
            "B",
            "2022-12-01T00:00:00Z",
            "2022-12-01T01:00:00Z",
            -1.0,
            0,
        ),
        _trade(
            "A",
            "2023-01-02T00:00:00Z",
            "2023-01-02T12:00:00Z",
            -1.0,
            1,
        ),
        _trade(
            "B",
            "2023-01-02T00:00:00Z",
            "2023-01-02T01:00:00Z",
            1.5,
            1,
        ),
        _trade(
            "A",
            "2023-01-02T13:00:00Z",
            "2023-01-02T14:00:00Z",
            1.5,
            2,
        ),
        _trade(
            "A",
            "2023-01-03T00:00:00Z",
            "2023-01-03T01:00:00Z",
            1.5,
            3,
        ),
    ]
    selected, decisions = select_online_trades(
        pd.DataFrame(rows),
        config=_config(),
        half_life_days=126,
    )
    assert len(selected) == 2
    assert selected.iloc[0]["expert_id"] == "A"
    assert selected["entry_time_utc"].dt.strftime("%Y-%m-%d").is_unique
    assert "CASH_DAILY_LIMIT" in set(decisions["status"])
