from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingRegressor

from src.utility import (
    action_mask,
    apply_first_utility_signal,
    benefit_r_target,
    make_model,
    rank_correlation,
    verify_sources,
)


def test_benefit_target_is_unclipped_and_risk_normalized():
    snapshots = pd.DataFrame(
        {
            "benefit_usd": [4.0, -20.0],
            "risk_usd": [2.0, 4.0],
        }
    )
    np.testing.assert_allclose(benefit_r_target(snapshots), [2.0, -5.0])


def test_benefit_target_rejects_nonpositive_risk():
    snapshots = pd.DataFrame(
        {
            "benefit_usd": [1.0],
            "risk_usd": [0.0],
        }
    )
    with pytest.raises(ValueError, match="non-positive risk"):
        benefit_r_target(snapshots)


def test_action_requires_score_and_every_adverse_guard(config):
    snapshots = pd.DataFrame(
        {
            "current_r": [-0.20, -0.05, -0.20, -0.20, -0.20],
            "max_adverse_r": [0.30, 0.30, 0.20, 0.30, 0.30],
            "recent_15m_r": [-0.01, -0.01, -0.01, 0.01, -0.01],
        }
    )
    scores = np.array([0.10, 0.10, 0.10, 0.10, -0.01])
    assert action_mask(snapshots, scores, config).tolist() == [
        True,
        False,
        False,
        False,
        False,
    ]


def test_model_is_locked_quantile_regressor(config):
    model = make_model(config)
    assert isinstance(model, HistGradientBoostingRegressor)
    assert model.loss == "quantile"
    assert model.quantile == pytest.approx(0.25)


def test_rank_correlation_preserves_order_and_handles_constants():
    assert rank_correlation(np.array([1.0, 2.0, 3.0]), np.array([2.0, 4.0, 6.0])) == pytest.approx(1.0)
    assert rank_correlation(np.ones(3), np.arange(3, dtype=float)) == 0.0


def test_utility_wrapper_renames_probability_semantics():
    class FakeV3:
        @staticmethod
        def apply_first_exit_signal(selected, predictions):
            managed = selected.copy()
            managed["management_probability"] = [0.2]
            actions = pd.DataFrame({"management_probability": [0.2]})
            return managed, actions

    selected = pd.DataFrame({"trade_id": ["T1"]})
    predictions = pd.DataFrame(
        {
            "utility_exit_trigger": [True],
            "predicted_lower_benefit_r": [0.2],
        }
    )
    managed, actions = apply_first_utility_signal(
        selected, predictions, FakeV3()
    )
    assert "management_lower_benefit_r" in managed
    assert "management_probability" not in actions


def test_verify_sources_fails_closed(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("changed", encoding="utf-8")
    config = {
        "sources": {
            "source": {"path": str(source), "sha256": "0" * 64}
        }
    }
    with pytest.raises(ValueError, match="Locked source drift"):
        verify_sources(config)
