from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contract import load_config, resolve_relative, sha256_file  # noqa: E402
from macro_features import (  # noqa: E402
    _contiguous_log_return,
    align_macro_features,
    model_macro_feature_columns,
)
from router import best_actions, execute_policy, policy_definitions  # noqa: E402


def test_policy_grid_remains_exactly_one_thousand() -> None:
    policies = policy_definitions(load_config())
    assert len(policies) == 1000
    assert len({policy["policy_id"] for policy in policies}) == 1000


def test_macro_feature_set_is_exactly_seventeen_fields() -> None:
    features = model_macro_feature_columns(load_config())
    assert len(features) == 17
    assert len(set(features)) == 17
    assert features[-1] == "macro_feature_age_minutes"


def test_contiguous_return_rejects_a_gap() -> None:
    times = pd.to_datetime(
        ["2025-01-01T00:00Z", "2025-01-01T00:15Z", "2025-01-01T00:45Z"],
        utc=True,
    )
    result = _contiguous_log_return(
        pd.Series([100.0, 101.0, 102.0]), pd.Series(times), 1
    )
    assert np.isnan(result.iloc[0])
    assert np.isfinite(result.iloc[1])
    assert np.isnan(result.iloc[2])


def test_alignment_is_backward_only_and_direction_aligned() -> None:
    config = {
        "macro_features": {
            "horizons": {"H1": 4},
            "scales": {"D2": 192},
            "maximum_feature_age_minutes": 15,
            "required_finite_features": [
                "dxy_pressure_H1_D2",
                "bond_pressure_H1_D2",
            ],
        }
    }
    signal = pd.Timestamp("2025-01-02T10:10Z")
    actions = pd.DataFrame(
        {
            "signal_time": [signal, signal],
            "entry_time": [signal, signal],
            "exit_time": [signal + pd.Timedelta(hours=1)] * 2,
            "event_id": ["E1", "E1"],
            "action_id": ["LONG_FAST", "SHORT_FAST"],
            "direction": ["LONG", "SHORT"],
        }
    )
    macro = pd.DataFrame(
        {
            "macro_feature_time": pd.to_datetime(
                ["2025-01-02T10:00Z", "2025-01-02T10:15Z"], utc=True
            ),
            "dxy_pressure_H1_D2": [2.0, 999.0],
            "bond_pressure_H1_D2": [3.0, 999.0],
        }
    )
    aligned, evidence = align_macro_features(actions, macro, config)
    assert len(aligned) == 2
    assert evidence["maximum_macro_feature_age_minutes"] == 10.0
    assert aligned["macro_feature_time"].eq(pd.Timestamp("2025-01-02T10:00Z")).all()
    long = aligned.loc[aligned["direction"].eq("LONG")].iloc[0]
    short = aligned.loc[aligned["direction"].eq("SHORT")].iloc[0]
    assert long["route_aligned_dxy_pressure_H1_D2"] == 2.0
    assert short["route_aligned_dxy_pressure_H1_D2"] == -2.0
    assert long["route_aligned_bond_pressure_H1_D2"] == 3.0
    assert short["route_aligned_bond_pressure_H1_D2"] == -3.0


def test_optional_macro_field_can_be_missing_without_dropping_action() -> None:
    config = {
        "macro_features": {
            "horizons": {"H1": 4},
            "scales": {"D2": 192, "D10": 960},
            "maximum_feature_age_minutes": 15,
            "required_finite_features": [
                "dxy_pressure_H1_D2",
                "bond_pressure_H1_D2",
            ],
        }
    }
    signal = pd.Timestamp("2025-01-02T10:10Z")
    actions = pd.DataFrame(
        {
            "signal_time": [signal],
            "entry_time": [signal],
            "exit_time": [signal + pd.Timedelta(hours=1)],
            "event_id": ["E1"],
            "action_id": ["LONG_FAST"],
            "direction": ["LONG"],
        }
    )
    macro = pd.DataFrame(
        {
            "macro_feature_time": pd.to_datetime(["2025-01-02T10:00Z"], utc=True),
            "dxy_pressure_H1_D2": [2.0],
            "bond_pressure_H1_D2": [3.0],
            "dxy_pressure_H1_D10": [np.nan],
            "bond_pressure_H1_D10": [np.nan],
        }
    )
    aligned, _ = align_macro_features(actions, macro, config)
    assert len(aligned) == 1
    assert np.isnan(aligned.iloc[0]["dxy_pressure_H1_D10"])


def test_action_without_recent_macro_timestamp_is_retained_with_missing_features() -> (
    None
):
    config = {
        "macro_features": {
            "horizons": {"H1": 4},
            "scales": {"D2": 192},
            "maximum_feature_age_minutes": 15,
            "required_finite_features": [],
        }
    }
    signal = pd.Timestamp("2025-01-02T10:30Z")
    actions = pd.DataFrame(
        {
            "signal_time": [signal],
            "entry_time": [signal],
            "exit_time": [signal + pd.Timedelta(hours=1)],
            "event_id": ["E1"],
            "action_id": ["LONG_FAST"],
            "direction": ["LONG"],
        }
    )
    macro = pd.DataFrame(
        {
            "macro_feature_time": pd.to_datetime(["2025-01-02T10:00Z"], utc=True),
            "dxy_pressure_H1_D2": [2.0],
            "bond_pressure_H1_D2": [3.0],
        }
    )
    aligned, evidence = align_macro_features(actions, macro, config)
    assert len(aligned) == 1
    assert pd.isna(aligned.iloc[0]["macro_feature_time"])
    assert pd.isna(aligned.iloc[0]["dxy_pressure_H1_D2"])
    assert evidence["macro_timestamp_unavailable_rows"] == 1


def test_best_action_can_flip_direction() -> None:
    frame = pd.DataFrame(
        {
            "event_id": ["E1", "E1"],
            "action_id": ["LONG__FAST", "SHORT__SWING"],
            "model_score": [0.1, 0.8],
            "signal_time": pd.to_datetime(
                ["2025-01-02T10:00Z", "2025-01-02T10:00Z"], utc=True
            ),
            "direction": ["LONG", "SHORT"],
        }
    )
    assert best_actions(frame).iloc[0]["direction"] == "SHORT"


def test_execution_respects_daily_cap() -> None:
    times = pd.to_datetime(
        ["2025-01-02T10:00Z", "2025-01-02T11:00Z", "2025-01-02T12:00Z"],
        utc=True,
    )
    scored = pd.DataFrame(
        {
            "event_id": ["E1", "E2", "E3"],
            "score_percentile": [0.9, 0.9, 0.9],
            "model_score": [3.0, 2.0, 1.0],
            "entry_time": times,
            "exit_time": times + pd.Timedelta(minutes=30),
        }
    )
    policy = {
        "score_percentile": 0.5,
        "daily_cap": 2,
        "entry_separation_minutes": 0,
        "maximum_active_expansion": 3,
    }
    assert execute_policy(scored, policy)["event_id"].tolist() == ["E1", "E2"]


def test_locked_external_source_hashes_match() -> None:
    config = load_config()
    for name in (
        "base_actions",
        "base_evidence",
        "baseline_config",
        "baseline_router_source",
        "baseline_result",
        "baseline_evaluation_source",
        "core_ledger",
    ):
        observed = sha256_file(resolve_relative(config["sources"][name]))
        assert observed == config["sources"][f"{name}_sha256"]


def test_authorization_is_research_only() -> None:
    authorization = load_config()["authorization"]
    assert authorization["research_only"] is True
    assert authorization["historical_blocks_contaminated"] is True
    assert all(
        authorization[name] is False
        for name in (
            "same_version_tuning_authorized",
            "python_predictions_authorized",
            "ea_consumption_authorized",
            "demo_authorized",
            "live_authorized",
            "broker_action_authorized",
        )
    )
