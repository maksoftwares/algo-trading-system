from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_specialist_meta_selector import (
    build_features,
    feature_columns,
    fit_monthly_model,
    load_config,
    load_signal_candidates,
    verify_lock,
)


def test_contract_is_frozen_before_combined_canonical_outcomes() -> None:
    lock = verify_lock()
    assert lock["frozen_before_combined_canonical_outcomes"] is True
    assert lock["parameter_search_allowed"] is False


def test_signal_manifest_is_outcome_blind_and_keeps_clock_conflicts() -> None:
    config = load_config()
    candidates = load_signal_candidates(config)
    forbidden = {"r", "exit_time_utc", "entry_price", "oracle_match"}
    assert forbidden.isdisjoint(candidates.columns)
    assert len(candidates) == 4698
    assert candidates["opposite_side_present"].sum() == 648
    assert candidates["candidate_id"].is_unique
    assert set(candidates["side"]) == {"LONG", "SHORT"}


def test_feature_contract_is_fixed_and_finite() -> None:
    config = load_config()
    candidates = load_signal_candidates(config).head(20)
    features = build_features(candidates, config)
    assert list(features.columns) == feature_columns(config)
    assert features.notna().all().all()


def test_monthly_fit_uses_only_strictly_prior_closed_labels() -> None:
    config = load_config()
    config["model"]["minimum_training_candidates"] = 6
    candidates = load_signal_candidates(config).head(8).copy()
    candidates["entry_time_utc"] = pd.to_datetime(
        [
            "2022-01-01T00:00:00Z",
            "2022-02-01T00:00:00Z",
            "2022-03-01T00:00:00Z",
            "2022-04-01T00:00:00Z",
            "2022-05-01T00:00:00Z",
            "2022-06-01T00:00:00Z",
            "2022-12-31T23:00:00Z",
            "2023-01-01T00:00:00Z",
        ],
        utc=True,
    )
    candidates["exit_time_utc"] = candidates["entry_time_utc"] + pd.Timedelta(
        hours=1
    )
    candidates["status"] = "CLOSED"
    candidates["r"] = [1.5, -1.0, 1.5, -1.0, 1.5, -1.0, 1.5, -1.0]
    _, _, metadata = fit_monthly_model(
        candidates,
        month_boundary=pd.Timestamp("2023-01-01T00:00:00Z"),
        config=config,
    )
    assert metadata["training_candidates"] == 6
    assert metadata["latest_training_exit_utc"] < pd.Timestamp(
        "2023-01-01T00:00:00Z"
    )
