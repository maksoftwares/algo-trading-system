from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from src.action_models import prepare_dataset, sha256_file  # noqa: E402
from src.adaptive_models import (  # noqa: E402
    assert_adaptive_v5_parity,
    fit_adaptive_model,
    predict_adaptive_model,
    recency_multipliers,
)
from src.interaction_features import (  # noqa: E402
    ACTION_DESCRIPTOR_COLUMNS,
    add_action_interactions,
    event_feature_columns,
    interaction_feature_columns,
)
from src.two_stage import (  # noqa: E402
    action_choice_accuracy,
    add_two_stage_targets,
    choose_two_stage_action,
)


CONFIG = json.loads(
    (ROOT / "config" / "two_stage_models_v8.json").read_text(encoding="utf-8")
)


def test_base_method_matches_adaptive_v5() -> None:
    path = REPO_ROOT / CONFIG["inputs"]["reference_adaptive_v5_config"]["path"]
    reference = json.loads(path.read_text(encoding="utf-8"))
    assert assert_adaptive_v5_parity(CONFIG, reference)
    assert (
        sha256_file(ROOT / "src" / "action_models.py")
        == CONFIG["adaptation_contract"]["expected_shared_model_code_sha256"]
    )


def test_training_variants_are_small_and_frozen() -> None:
    variants = {row["variant_id"]: row for row in CONFIG["training_variants"]}
    assert list(variants) == [
        "EXPANDING",
        "ROLLING_36M",
        "RECENCY_H12M",
        "REGIME_LOCAL",
    ]
    assert variants["ROLLING_36M"]["lookback_months"] == 36
    assert variants["RECENCY_H12M"]["half_life_months"] == 12
    assert variants["REGIME_LOCAL"]["minimum_regime_action_rows"] == 650
    assert variants["REGIME_LOCAL"]["minimum_regime_events"] == 200


def test_recency_weight_boundaries() -> None:
    boundary = pd.Timestamp("2026-01-01T00:00:00Z")
    times = pd.Series(
        [
            boundary,
            boundary - pd.Timedelta(days=365.25),
            pd.Timestamp("2010-01-01T00:00:00Z"),
        ]
    )
    weights = recency_multipliers(
        times,
        boundary,
        half_life_months=12,
        minimum_weight=0.01,
    )
    assert np.isclose(weights[0], 1.0)
    assert np.isclose(weights[1], 0.5)
    assert np.isclose(weights[2], 0.01)


def test_regime_local_model_uses_sparse_fallback() -> None:
    rows = 12
    frame = pd.DataFrame(
        {
            "x": np.linspace(-1.0, 1.0, rows),
            "target_fit": np.linspace(-0.5, 0.5, rows),
            "structural_weight": np.ones(rows),
            "signal_time": pd.date_range("2024-01-01", periods=rows, tz="UTC"),
            "label_end_time": pd.date_range("2024-01-02", periods=rows, tz="UTC"),
            "event_id": [f"E{index}" for index in range(rows)],
            "regime": ["CHOP"] * 10 + ["COMPRESSION"] * 2,
        }
    )
    config = {
        "calibration_gates": {"minimum_fit_action_rows": 10},
        "ridge_model": CONFIG["ridge_model"],
    }
    variant = {
        "variant_id": "REGIME_LOCAL",
        "kind": "REGIME_LOCAL",
        "minimum_regime_action_rows": 5,
        "minimum_regime_events": 5,
        "fallback": "EXPANDING_GLOBAL",
    }
    model = fit_adaptive_model(
        frame,
        features=["x"],
        config=config,
        variant=variant,
        fit_boundary=pd.Timestamp("2025-01-01T00:00:00Z"),
    )
    assert set(model.regime_models) == {"CHOP"}
    assert model.fit_metadata["regimes"]["COMPRESSION"]["local_model_fitted"] is False
    assert np.isfinite(predict_adaptive_model(model, frame, ["x"])).all()


def test_runtime_authorizations_are_disabled() -> None:
    authorization = CONFIG["authorization"]
    assert authorization["offline_model_fit_authorized"] is True
    assert authorization["offline_threshold_fit_authorized"] is True
    for key in (
        "portfolio_simulation_authorized",
        "python_serving_authorized",
        "ml_shadow_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
    ):
        assert authorization[key] is False


def test_action_interactions_change_slopes_by_horizon() -> None:
    base_features = [
        "market_x",
        *ACTION_DESCRIPTOR_COLUMNS,
    ]
    frame = pd.DataFrame(
        {
            "market_x": [2.0, 2.0, 2.0],
            "action_stop_atr": [1.0, 1.5, 2.0],
            "action_target_r": [1.0, 1.5, 2.0],
            "action_hold_hours": [4.0, 12.0, 36.0],
            "action_fast": [1.0, 0.0, 0.0],
            "action_intraday": [0.0, 1.0, 0.0],
            "action_swing": [0.0, 0.0, 1.0],
        }
    )
    enriched, interactions = add_action_interactions(frame, base_features)
    assert event_feature_columns(base_features) == ["market_x"]
    assert interactions == ["ix_intraday__market_x", "ix_swing__market_x"]
    assert enriched["ix_intraday__market_x"].tolist() == [0.0, 2.0, 0.0]
    assert enriched["ix_swing__market_x"].tolist() == [0.0, 0.0, 2.0]


def test_full_interaction_surface_is_mechanical() -> None:
    v4_config = json.loads(
        (REPO_ROOT / CONFIG["inputs"]["v4_dataset_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    base = v4_config["model_features"]
    assert len(event_feature_columns(base)) == CONFIG["expected"]["event_feature_count"]
    assert len(interaction_feature_columns(base)) == CONFIG["expected"][
        "interaction_feature_count"
    ]


def test_two_stage_targets_separate_event_and_action_quality() -> None:
    frame = pd.DataFrame(
        {
            "event_id": ["E0", "E0", "E1", "E1"],
            "candidate_id": ["E0_A", "E0_B", "E1_A", "E1_B"],
            "action_id": ["A", "B", "A", "B"],
            "stress_net_r": [-1.0, 2.0, -0.5, -0.25],
            "structural_weight": [0.5, 0.5, 0.5, 0.5],
            "event_eval_weight": [1.0, 1.0, 1.0, 1.0],
        }
    )
    result = add_two_stage_targets(frame, CONFIG)
    assert result.loc[result.event_id.eq("E0"), "event_best_stress_r"].eq(2.0).all()
    assert result.loc[result.event_id.eq("E1"), "event_best_stress_r"].eq(-0.25).all()
    assert result.groupby("event_id")["action_advantage_r"].mean().abs().max() < 1e-12
    assert result["event_best_stress_r_positive"].tolist() == [True, True, False, False]


def test_two_stage_action_choice_uses_relative_score() -> None:
    scored = pd.DataFrame(
        {
            "event_id": ["E0", "E0", "E1", "E1"],
            "candidate_id": ["E0_A", "E0_B", "E1_A", "E1_B"],
            "signal_time": pd.to_datetime(
                ["2025-01-01T00:00:00Z"] * 2 + ["2025-01-02T00:00:00Z"] * 2,
                utc=True,
            ),
            "action_advantage_score": [0.1, 0.8, 0.7, 0.2],
            "action_tie_rank": [0, 1, 0, 1],
            "event_score": [0.3, 0.3, -0.1, -0.1],
        }
    )
    chosen = choose_two_stage_action(scored)
    assert chosen["candidate_id"].tolist() == ["E0_B", "E1_A"]
    assert chosen["event_score"].tolist() == [0.3, -0.1]


def test_action_accuracy_accepts_tied_best_actions() -> None:
    scored = pd.DataFrame(
        {
            "event_id": ["E0", "E0"],
            "candidate_id": ["E0_A", "E0_B"],
            "stress_net_r": [1.0, 1.0],
            "event_eval_weight": [1.0, 1.0],
        }
    )
    chosen = scored.iloc[[1]].copy()
    assert action_choice_accuracy(scored, chosen) == 1.0


def test_outputs_when_present() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    predictions_path = output / CONFIG["outputs"]["predictions"]
    if not predictions_path.is_file():
        return
    policies = pd.read_parquet(output / CONFIG["outputs"]["calibration_policies"])
    predictions = pd.read_parquet(predictions_path)
    selected = pd.read_parquet(output / CONFIG["outputs"]["selected_events"])
    assert len(policies) == CONFIG["expected"]["calibration_policy_rows"]
    assert int(policies["chosen"].sum()) == CONFIG["expected"]["chosen_models"]
    assert not predictions["candidate_id"].duplicated().any()
    assert not selected.duplicated(["fold_id", "model_lane", "event_id"]).any()
    assert np.isfinite(predictions["model_score"]).all()
    assert np.isfinite(predictions["event_score"]).all()
    assert np.isfinite(predictions["action_advantage_score"]).all()
    source = pd.read_parquet(REPO_ROOT / CONFIG["inputs"]["v4_action_dataset"]["path"])
    prepared = prepare_dataset(
        source,
        CONFIG,
        json.loads(
            (REPO_ROOT / CONFIG["inputs"]["v4_dataset_config"]["path"]).read_text(
                encoding="utf-8"
            )
        )["model_features"],
    )
    regimes = predictions[["candidate_id"]].merge(
        prepared[["candidate_id", "regime"]],
        on="candidate_id",
        how="left",
        validate="one_to_one",
    )
    assert not regimes["regime"].eq("UNSAFE_SHOCK").any()
