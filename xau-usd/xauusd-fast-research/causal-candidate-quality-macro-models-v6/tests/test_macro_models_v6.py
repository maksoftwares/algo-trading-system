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
from src.macro_features import MACRO_FEATURE_COLUMNS, enrich_actions  # noqa: E402


CONFIG = json.loads(
    (ROOT / "config" / "macro_models_v6.json").read_text(encoding="utf-8")
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


def test_macro_join_is_backward_and_bounded() -> None:
    actions = pd.DataFrame(
        {
            "candidate_id": ["C0", "C1", "C2", "C3"],
            "event_id": ["E0", "E1", "E2", "E3"],
            "signal_time": pd.to_datetime(
                ["2025-01-01T00:10:00Z", "2025-01-01T00:15:00Z", "2025-01-01T00:20:00Z", "2025-01-01T00:25:00Z"],
                utc=True,
            ),
            "direction_sign": [1.0, 1.0, -1.0, -1.0],
        }
    )
    macro = pd.DataFrame(
        {
            "macro_time": pd.to_datetime(["2025-01-01T00:15:00Z"], utc=True),
            **{
                f"{prefix}_gold_pressure_{horizon}": [value]
                for prefix, value in (("dxy", 2.0), ("bond", 1.0))
                for horizon in ("15m", "1h", "4h")
            },
        }
    )
    enriched, evidence = enrich_actions(actions, macro, tolerance_minutes=10)
    indexed = enriched.set_index("candidate_id")
    assert indexed.loc["C0", list(MACRO_FEATURE_COLUMNS)].isna().all()
    assert indexed.loc["C1", "dir_dxy_gold_pressure_1h"] == 2.0
    assert indexed.loc["C2", "dir_dxy_gold_pressure_1h"] == -2.0
    assert indexed.loc["C3", "dir_macro_consensus_1h"] == -1.5
    assert indexed.loc["C3", "macro_disagreement_1h"] == 1.0
    assert evidence["macro_age_minutes_counts"] == {"0.0": 1, "5.0": 1, "10.0": 1}


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
