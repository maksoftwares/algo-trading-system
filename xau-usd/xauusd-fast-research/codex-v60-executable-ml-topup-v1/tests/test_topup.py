from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src import topup


def model_contract() -> dict:
    return {
        "population": {"test_entry_years": [2021]},
        "model": {
            "purge_hours": 48,
            "minimum_train_rows": 1,
            "bags": 1,
            "regression_winsor_quantiles": [0.01, 0.99],
            "parameters": {
                "max_depth": 2,
                "max_iter": 2,
                "learning_rate": 0.1,
                "min_samples_leaf": 1,
                "l2_regularization": 1.0,
                "random_state": 0,
            },
        },
        "score_policy": {
            "minimum_oos_history": 100,
            "expected_pnl_weight": 0.5,
            "win_probability_weight": 0.5,
            "minimum_expected_pnl_rank_exclusive": 0.5,
            "minimum_win_probability_rank_exclusive": 0.5,
            "minimum_joint_score_exclusive": 0.8,
        },
    }


def risk_limits(account: float = 60.0) -> dict[str, float]:
    return {
        "account_initial_risk_usd": account,
        "directional_initial_risk_usd": account,
        "addon_initial_risk_usd": 45.0,
    }


def prior_stub() -> SimpleNamespace:
    return SimpleNamespace(
        source_risk_limits=lambda _: {
            "R2_DOWNTREND": 45.0,
            "V7_SWING_HEALTH": 30.0,
        }
    )


def test_build_source_features_adds_only_frozen_source_identity() -> None:
    base = pd.DataFrame({"ret_1h": [0.1, -0.2], "is_long": [1.0, 0.0]})
    meta = pd.DataFrame(
        {
            "execution_source_id": ["R2_DOWNTREND", "V7_SWING_HEALTH"],
            "risk_usd": [10.0, 5.0],
        }
    )
    result = topup.build_source_features(
        base,
        meta,
        ["R2_DOWNTREND", "V7_SWING_HEALTH"],
    )
    assert result.columns.tolist() == [
        "ret_1h",
        "is_long",
        "source__R2_DOWNTREND",
        "source__V7_SWING_HEALTH",
    ]
    assert result["source__R2_DOWNTREND"].tolist() == [1.0, 0.0]


def test_build_source_features_rejects_outcome_column() -> None:
    base = pd.DataFrame({topup.PNL: [1.0]})
    meta = pd.DataFrame(
        {"execution_source_id": ["R2_DOWNTREND"], "risk_usd": [10.0]}
    )
    with pytest.raises(ValueError, match="Outcome or risk columns"):
        topup.build_source_features(base, meta, ["R2_DOWNTREND"])


def test_causal_rank_appends_current_score_only_after_ranking() -> None:
    history = [1.0, 2.0]
    ranks = topup.causal_rank(
        np.array([3.0, 0.0]),
        np.array([0.0, 1.0, 2.0, 3.0]),
        history,
        minimum_history=2,
    )
    assert ranks.tolist() == [1.0, 0.0]
    assert history == [1.0, 2.0, 3.0, 0.0]


def test_walkforward_purges_recent_exit_and_never_scores_missing_risk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meta = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                [
                    "2020-01-01T00:00:00Z",
                    "2020-12-01T00:00:00Z",
                    "2021-01-10T00:00:00Z",
                    "2021-01-11T00:00:00Z",
                ],
                utc=True,
            ),
            "exit_time": pd.to_datetime(
                [
                    "2020-12-20T00:00:00Z",
                    "2020-12-31T00:00:00Z",
                    "2021-01-10T01:00:00Z",
                    "2021-01-11T01:00:00Z",
                ],
                utc=True,
            ),
            "risk_usd": [10.0, 10.0, 10.0, np.nan],
            topup.PNL: [1.0, -1.0, 2.0, -2.0],
        }
    )
    X = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0]})

    def fake_fit(X_train, X_test, pnl, contract, rng):
        assert len(X_train) == 1
        assert pnl.tolist() == [1.0]
        return (
            np.array([0.0]),
            np.ones(len(X_test)),
            np.array([0.5]),
            np.full(len(X_test), 0.9),
        )

    monkeypatch.setattr(topup, "fit_dual_ensemble", fake_fit)
    decisions, annual = topup.walkforward_dual(
        X,
        meta,
        model_contract(),
        seed=0,
    )
    assert annual.loc[0, "training_rows"] == 1
    assert decisions.loc[2, "expected_pnl_score"] == 1.0
    assert pd.isna(decisions.loc[3, "expected_pnl_score"])
    assert not bool(decisions.loc[3, "topup_proposed"])


def test_topup_policy_keeps_missing_risk_trade_at_base_lot() -> None:
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
            "execution_source_id": ["R2_DOWNTREND", "R2_DOWNTREND"],
        }
    )
    factors, audit = topup.topup_factors(
        meta,
        np.array([True, True]),
        {},
        risk_limits(),
        prior_stub(),
    )
    assert factors.tolist() == [1.0, 2.0]
    assert audit["skipped_trade_rows"] == 0
    assert audit["accepted_missing_risk_topups"] == 0
    assert audit["rejections"] == {"MISSING_INITIAL_RISK": 1}


def test_topup_policy_rejects_concurrent_account_risk_breach() -> None:
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
            "execution_source_id": ["R2_DOWNTREND", "R2_DOWNTREND"],
        }
    )
    factors, audit = topup.topup_factors(
        meta,
        np.array([True, True]),
        {},
        risk_limits(account=50.0),
        prior_stub(),
    )
    assert factors.tolist() == [2.0, 1.0]
    assert audit["rejections"] == {"ACCOUNT_RISK_LIMIT": 1}
    assert audit["maximum_known_account_risk_usd"] == 50.0
