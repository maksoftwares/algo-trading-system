from __future__ import annotations

import numpy as np
import pytest

from conftest import synthetic_returns
from xau_crossasset_residual.core import rolling_causal_ols


def test_rolling_ols_uses_prior_rows_and_exact_window_boundaries():
    result = rolling_causal_ols(synthetic_returns())
    assert result.iloc[2499].training_observations == 2499 and not result.iloc[2499].model_valid
    assert result.iloc[2500].training_observations == 2500
    assert result.iloc[3000].training_observations == 3000
    assert result.iloc[-1].training_observations == 3000


def test_rolling_ols_includes_intercept_and_excludes_current_residual_from_z_reference():
    result = rolling_causal_ols(synthetic_returns(3200))
    row = result[result.model_valid & np.isfinite(result.residual_z)].iloc[0]
    earlier = result[(result.timestamp_ms < row.timestamp_ms) & result.model_valid].residual.dropna().tail(500)
    assert np.isfinite(row.intercept)
    assert row.prior_residual_mean == pytest.approx(earlier.mean())
    assert row.prior_residual_std == pytest.approx(earlier.std(ddof=1))


def test_rank_deficient_training_matrix_is_rejected():
    frame = synthetic_returns(2502)
    frame[["r_xag", "r_eurusd", "r_usdjpy"]] = 1.0
    assert rolling_causal_ols(frame).iloc[-1].model_rejection_reason == "RANK_DEFICIENT"


def test_condition_number_limit_is_enforced():
    result = rolling_causal_ols(synthetic_returns(2502), condition_limit=1.0)
    assert result.iloc[-1].model_rejection_reason == "CONDITION_NUMBER_EXCEEDED"


def test_current_xau_return_is_not_in_the_training_window():
    frame = synthetic_returns(3101)
    first = rolling_causal_ols(frame)
    changed = frame.copy()
    changed.loc[3100, "r_xau"] += 1.0
    second = rolling_causal_ols(changed)
    assert first.loc[3100, ["intercept", "beta_xag", "beta_eurusd", "beta_usdjpy"]].equals(second.loc[3100, ["intercept", "beta_xag", "beta_eurusd", "beta_usdjpy"]])
    assert first.at[3100, "residual"] != second.at[3100, "residual"]
