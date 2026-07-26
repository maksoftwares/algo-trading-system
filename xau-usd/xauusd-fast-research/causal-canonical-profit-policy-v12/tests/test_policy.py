from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from policy import (  # noqa: E402
    apply_profit_threshold,
    choose_profit_threshold,
    economics,
    weighted_quantile,
)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": ["a", "b", "c", "d"],
            "decision_time": pd.to_datetime(
                [
                    "2025-01-01T00:00:00Z",
                    "2025-01-02T00:00:00Z",
                    "2025-01-03T00:00:00Z",
                    "2025-01-06T00:00:00Z",
                ],
                utc=True,
            ),
            "structural_episode_id": ["a", "b", "c", "d"],
            "structural_weight": [1.0, 1.0, 1.0, 1.0],
            "stress_net_r": [-1.0, -1.0, 2.0, 2.0],
            "initial_risk_usd_0p01": [10.0, 10.0, 10.0, 10.0],
            "model_score": [-2.0, -1.0, 1.0, 2.0],
        }
    )


def policy(minimum_improvement: float = 1.0) -> dict:
    return {
        "weighted_quantile_grid": [0.0, 0.75],
        "minimum_selected_weight_coverage": 0.2,
        "minimum_profit_improvement_usd": minimum_improvement,
        "require_mean_not_worse": True,
        "require_profit_factor_not_worse": True,
        "require_drawdown_not_worse": True,
        "fallback_quantile": 0.0,
    }


def test_weighted_quantile_uses_weights() -> None:
    assert weighted_quantile([0.0, 1.0], [3.0, 1.0], 0.5) == 0.0


def test_profit_policy_rejects_losing_tail() -> None:
    chosen, grid = choose_profit_threshold(sample_frame(), policy())
    assert chosen["quantile"] == 0.75
    assert chosen["profit_improvement_usd"] == 20.0
    assert len(grid) == 2


def test_profit_policy_falls_back_when_improvement_is_too_small() -> None:
    chosen, _ = choose_profit_threshold(sample_frame(), policy(100.0))
    assert chosen["quantile"] == 0.0
    assert chosen["selection_reason"].startswith("RETAIN_ALL")
    future = sample_frame().copy()
    future.loc[0, "model_score"] = chosen["threshold"] - 100.0
    applied = apply_profit_threshold(future, chosen, 0.0)
    assert applied["selected"].all()


def test_economics_reports_normalized_usd() -> None:
    metrics = economics(sample_frame())
    assert metrics["weighted_r_sum"] == 2.0
    assert metrics["normalized_weighted_usd_sum"] == 20.0
