from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest


def _bars(times: list[int], closes: list[float] | None = None) -> pd.DataFrame:
    return pd.DataFrame({"timestamp_ms": times, "close": closes or [100.0 + index for index in range(len(times))]})


def test_common_m5_requires_all_four_instruments(reviewed) -> None:
    core, _, _ = reviewed
    with pytest.raises(ValueError, match="all four"):
        core.synchronize_m5({"XAUUSD": _bars([0]), "XAGUSD": _bars([0])})


def test_common_m5_is_exact_intersection(reviewed) -> None:
    core, _, _ = reviewed
    frames = {symbol: _bars([0, 300_000, 600_000]) for symbol in core.INSTRUMENTS}
    frames["USDJPY"] = _bars([0, 600_000])
    synchronized, missing = core.synchronize_m5(frames)
    assert synchronized.timestamp_ms.tolist() == [0, 600_000]
    assert len(missing) == 1


def test_missing_common_bar_records_instrument(reviewed) -> None:
    core, _, _ = reviewed
    frames = {symbol: _bars([0, 300_000]) for symbol in core.INSTRUMENTS}
    frames["EURUSD"] = _bars([0])
    _, missing = core.synchronize_m5(frames)
    assert missing.iloc[0].missing_instruments == "EURUSD"
    assert missing.iloc[0].exclusion_reason == "MISSING_COMMON_M5_BAR"


def test_synchronization_never_forward_fills(reviewed) -> None:
    core, _, _ = reviewed
    frames = {symbol: _bars([0, 300_000]) for symbol in core.INSTRUMENTS}
    frames["XAGUSD"] = _bars([0])
    synchronized, _ = core.synchronize_m5(frames)
    assert len(synchronized) == 1
    assert synchronized.timestamp_ms.iloc[0] == 0


def test_returns_require_consecutive_five_minutes(reviewed) -> None:
    core, _, _ = reviewed
    synchronized = pd.DataFrame({"timestamp_ms": [0, 300_000, 900_000], **{f"close_{symbol.lower()}": [100.0, 101.0, 102.0] for symbol in core.INSTRUMENTS}})
    result = core.add_log_returns(synchronized)
    assert math.isfinite(result.r_xau.iloc[1])
    assert math.isnan(result.r_xau.iloc[2])


def test_returns_are_log_close_to_close(reviewed) -> None:
    core, _, _ = reviewed
    synchronized = pd.DataFrame({"timestamp_ms": [0, 300_000], **{f"close_{symbol.lower()}": [100.0, 110.0] for symbol in core.INSTRUMENTS}})
    result = core.add_log_returns(synchronized)
    assert result.r_xau.iloc[1] == pytest.approx(math.log(1.1))


def _linear_returns(count: int) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    xag = rng.normal(0, .001, count)
    eur = rng.normal(0, .001, count)
    jpy = rng.normal(0, .001, count)
    xau = .0001 + .4 * xag - .2 * eur + .1 * jpy + rng.normal(0, .00001, count)
    return pd.DataFrame({"timestamp_ms": np.arange(count, dtype=np.int64) * 300_000, "r_xau": xau, "r_xag": xag, "r_eurusd": eur, "r_usdjpy": jpy})


def test_model_rejects_before_minimum_2500(reviewed) -> None:
    core, _, _ = reviewed
    model = core.rolling_causal_ols(_linear_returns(20))
    assert not model.model_valid.any()
    assert set(model.model_rejection_reason) == {"INSUFFICIENT_TRAINING_OBSERVATIONS"}


def test_model_training_ends_at_t_minus_one(reviewed) -> None:
    core, _, _ = reviewed
    model = core.rolling_causal_ols(_linear_returns(2502))
    row = model.iloc[2500]
    assert row.training_observations == 2500
    assert row.training_end == core.iso_ms(model.timestamp_ms.iloc[2499])


def test_model_window_caps_at_exact_3000(reviewed) -> None:
    core, _, _ = reviewed
    model = core.rolling_causal_ols(_linear_returns(3010))
    assert model.iloc[-1].training_observations == 3000


def test_model_includes_intercept(reviewed) -> None:
    core, _, _ = reviewed
    model = core.rolling_causal_ols(_linear_returns(2502))
    assert math.isfinite(float(model.iloc[2500].intercept))
    assert abs(float(model.iloc[2500].intercept)) < .001


def test_rank_deficiency_is_rejected(reviewed) -> None:
    core, _, _ = reviewed
    frame = pd.DataFrame({"timestamp_ms": np.arange(2502) * 300_000, "r_xau": np.ones(2502), "r_xag": np.ones(2502), "r_eurusd": np.ones(2502), "r_usdjpy": np.ones(2502)})
    model = core.rolling_causal_ols(frame)
    assert model.iloc[2500].model_rejection_reason == "RANK_DEFICIENT"


def test_condition_number_limit_is_enforced(reviewed) -> None:
    core, _, _ = reviewed
    model = core.rolling_causal_ols(_linear_returns(2502), condition_limit=1.0)
    assert not bool(model.iloc[2500].model_valid)
    assert model.iloc[2500].model_rejection_reason == "CONDITION_NUMBER_EXCEEDED"


def test_current_residual_excluded_from_prior_distribution(reviewed) -> None:
    core, _, _ = reviewed
    model = core.rolling_causal_ols(_linear_returns(3105))
    row = model[np.isfinite(model.residual_z)].iloc[0]
    prior = model[(model.timestamp_ms < row.timestamp_ms) & model.model_valid].residual.dropna().tail(500)
    assert row.prior_residual_mean == pytest.approx(prior.mean())
    assert row.prior_residual_std == pytest.approx(prior.std(ddof=1))


def test_residual_normalization_needs_500_prior_values(reviewed) -> None:
    core, _, _ = reviewed
    model = core.rolling_causal_ols(_linear_returns(2999))
    assert model.residual_z.notna().sum() == 0


def test_model_prediction_is_finite_when_valid(reviewed) -> None:
    core, _, _ = reviewed
    model = core.rolling_causal_ols(_linear_returns(2510))
    valid = model[model.model_valid]
    assert np.isfinite(valid.predicted_r_xau).all()
    assert np.isfinite(valid.residual).all()


def test_h1_atr_is_wilder_smoothed(reviewed) -> None:
    core, _, _ = reviewed
    bars = pd.DataFrame({"timestamp_ms": np.arange(20) * 3_600_000, "high": np.arange(20) + 2.0, "low": np.arange(20, dtype=float), "close": np.arange(20) + 1.0})
    result = core.wilder_atr(bars, 14)
    assert result.ATR14.iloc[:13].isna().all()
    assert result.ATR14.iloc[13] == pytest.approx(2.0)


def test_prior_percentile_excludes_current_by_contract(reviewed) -> None:
    core, _, _ = reviewed
    prior = [1.0, 2.0, 3.0, 4.0]
    assert core.prior_percentile(prior, 3.0) == 75.0
    assert len(prior) == 4
