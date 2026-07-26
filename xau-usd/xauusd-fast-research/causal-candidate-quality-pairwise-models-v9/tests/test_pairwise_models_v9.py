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
from src.adaptive_models import recency_multipliers  # noqa: E402
from src.interaction_features import (  # noqa: E402
    ACTION_DESCRIPTOR_COLUMNS,
    add_action_interactions,
    event_feature_columns,
    interaction_feature_columns,
)
from src.pairwise import (  # noqa: E402
    action_choice_accuracy,
    add_event_target,
    assert_adaptive_v5_population_parity,
    build_pairwise_rows,
    choose_pairwise_action,
    pairwise_feature_columns,
    pairwise_target_audit,
)


CONFIG = json.loads(
    (ROOT / "config" / "pairwise_models_v9.json").read_text(encoding="utf-8")
)


def test_base_method_matches_adaptive_v5() -> None:
    path = REPO_ROOT / CONFIG["inputs"]["reference_adaptive_v5_config"]["path"]
    reference = json.loads(path.read_text(encoding="utf-8"))
    assert assert_adaptive_v5_population_parity(CONFIG, reference)
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
    base_features = ["market_x", *ACTION_DESCRIPTOR_COLUMNS]
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


def test_full_feature_surfaces_are_mechanical() -> None:
    v4_config = json.loads(
        (REPO_ROOT / CONFIG["inputs"]["v4_dataset_config"]["path"]).read_text(
            encoding="utf-8"
        )
    )
    base = v4_config["model_features"]
    action = [*base, *interaction_feature_columns(base)]
    pair = pairwise_feature_columns(action)
    assert len(event_feature_columns(base)) == CONFIG["expected"][
        "event_feature_count"
    ]
    assert len(action) == CONFIG["expected"]["model_feature_count"]
    assert len(pair) == CONFIG["expected"]["pairwise_feature_count"]


def synthetic_actions() -> pd.DataFrame:
    signal_time = pd.Timestamp("2025-01-01T00:00:00Z")
    rows: list[dict[str, object]] = []
    for event_id, outcomes, weight in (
        ("E0", [-1.0, 2.0, 2.0], 1.0),
        ("E1", [-0.5, -0.25, -0.75], 0.5),
    ):
        for rank, (action, outcome) in enumerate(
            zip(CONFIG["action_tie_order"], outcomes, strict=True)
        ):
            rows.append(
                {
                    "event_id": event_id,
                    "candidate_id": f"{event_id}_{action}",
                    "action_id": action,
                    "action_tie_rank": rank,
                    "stress_net_r": outcome,
                    "structural_weight": weight / 3.0,
                    "event_eval_weight": weight,
                    "structural_episode_id": event_id,
                    "model_lane": "BREAK_AND_RUN",
                    "model_eligible": True,
                    "signal_time": signal_time,
                    "label_end_time": signal_time + pd.Timedelta(hours=rank + 1),
                    "regime": "CHOP",
                    "market_x": 2.0,
                    "action_rank": float(rank),
                }
            )
    return pd.DataFrame(rows)


def test_event_target_and_pair_weights_preserve_event_weight() -> None:
    source = add_event_target(synthetic_actions())
    pair = build_pairwise_rows(
        source,
        action_features=["market_x", "action_rank"],
        action_tie_order=CONFIG["action_tie_order"],
    )
    assert source.loc[source.event_id.eq("E0"), "event_best_stress_r"].eq(2.0).all()
    assert source.loc[source.event_id.eq("E1"), "event_best_stress_r"].eq(-0.25).all()
    assert pair.groupby("event_id")["pair_weight"].sum().to_dict() == {
        "E0": 1.0,
        "E1": 0.5,
    }
    assert int(pair["pair_tied"].sum()) == 1
    assert pairwise_target_audit(source, pair)["tied_pair_rows"] == 1


def test_pairwise_differences_use_frozen_orientation() -> None:
    pair = build_pairwise_rows(
        add_event_target(synthetic_actions()),
        action_features=["market_x", "action_rank"],
        action_tie_order=CONFIG["action_tie_order"],
    )
    assert pair["pw__market_x"].eq(0.0).all()
    assert pair["model_eligible"].all()
    assert pair["pw__action_rank"].lt(0.0).all()
    assert pair["left_action_id"].map(
        {action: rank for rank, action in enumerate(CONFIG["action_tie_order"])}
    ).lt(
        pair["right_action_id"].map(
            {action: rank for rank, action in enumerate(CONFIG["action_tie_order"])}
        )
    ).all()


def test_pairwise_choice_and_tied_best_accuracy() -> None:
    scored = synthetic_actions().assign(
        pairwise_borda_score=[0.1, 0.7, 0.7, 0.8, 0.3, 0.1],
        event_score=[0.6, 0.6, 0.6, 0.4, 0.4, 0.4],
    )
    chosen = choose_pairwise_action(scored)
    assert chosen["candidate_id"].tolist() == [
        "E0_INTRADAY_1P5R_12H",
        "E1_FAST_1R_4H",
    ]
    assert action_choice_accuracy(scored, chosen) == 2.0 / 3.0


def test_outputs_when_present() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    predictions_path = output / CONFIG["outputs"]["predictions"]
    if not predictions_path.is_file():
        return
    policies = pd.read_parquet(output / CONFIG["outputs"]["calibration_policies"])
    predictions = pd.read_parquet(predictions_path)
    pair_predictions = pd.read_parquet(
        output / CONFIG["outputs"]["pair_predictions"]
    )
    selected = pd.read_parquet(output / CONFIG["outputs"]["selected_events"])
    assert len(policies) == CONFIG["expected"]["calibration_policy_rows"]
    assert int(policies["chosen"].sum()) == CONFIG["expected"]["chosen_models"]
    assert not predictions["candidate_id"].duplicated().any()
    assert not pair_predictions["pair_id"].duplicated().any()
    assert not selected.duplicated(["fold_id", "model_lane", "event_id"]).any()
    assert predictions["event_score"].between(0.0, 1.0).all()
    assert predictions["pairwise_borda_score"].between(0.0, 1.0).all()
    assert pair_predictions["left_win_probability"].between(0.0, 1.0).all()
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
