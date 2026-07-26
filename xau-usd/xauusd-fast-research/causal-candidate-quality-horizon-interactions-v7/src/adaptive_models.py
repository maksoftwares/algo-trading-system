from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from src.action_models import build_model, canonical_json_sha256


REFERENCE_KEYS = (
    "lane_ownership",
    "exclusions",
    "target",
    "action_tie_order",
    "retention_quantiles",
    "calibration_gates",
    "acceptance_gates",
    "bootstrap",
    "authorization",
    "historical_outcomes_already_exposed",
)
EXPECTED_REFERENCE_KEYS = (
    "action_rows",
    "event_rows",
    "structural_episodes",
    "folds",
)


@dataclass
class AdaptiveModel:
    variant_id: str
    global_model: Any
    regime_models: dict[str, Any]
    fit_metadata: dict[str, Any]


def base_method_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **{key: config[key] for key in REFERENCE_KEYS},
        "expected": {key: config["expected"][key] for key in EXPECTED_REFERENCE_KEYS},
    }


def assert_adaptive_v5_parity(
    config: Mapping[str, Any], reference: Mapping[str, Any]
) -> str:
    current_contract = base_method_contract(config)
    reference_contract = base_method_contract(reference)
    if current_contract != reference_contract:
        raise ValueError("Horizon V7 changed an unauthorized Adaptive V5 method field")
    if config["ridge_model"] != reference["ridge_model"]:
        raise ValueError("Horizon V7 ridge model differs from Adaptive V5")
    if config["training_variants"] != reference["training_variants"]:
        raise ValueError("Horizon V7 training variants differ from Adaptive V5")
    return canonical_json_sha256(
        {
            "base_method": current_contract,
            "ridge_model": config["ridge_model"],
            "training_variants": config["training_variants"],
        }
    )


def recency_multipliers(
    label_end_time: pd.Series,
    fit_boundary: pd.Timestamp,
    *,
    half_life_months: int,
    minimum_weight: float,
) -> np.ndarray:
    boundary = pd.Timestamp(fit_boundary)
    ages = (
        boundary - pd.to_datetime(label_end_time, utc=True)
    ).dt.total_seconds().to_numpy(dtype=float) / 86_400.0
    if np.any(ages < 0.0):
        raise ValueError("Recency weighting encountered a post-boundary label")
    half_life_days = float(half_life_months) * 30.4375
    return np.maximum(np.power(0.5, ages / half_life_days), float(minimum_weight))


def _fit_weighted_ridge(
    frame: pd.DataFrame,
    *,
    features: Sequence[str],
    model_spec: Mapping[str, Any],
    weights: np.ndarray,
) -> Any:
    model = build_model(model_spec)
    model.fit(
        frame[list(features)],
        frame["target_fit"].to_numpy(dtype=float),
        model__sample_weight=np.asarray(weights, dtype=float),
    )
    return model


def fit_adaptive_model(
    frame: pd.DataFrame,
    *,
    features: Sequence[str],
    config: Mapping[str, Any],
    variant: Mapping[str, Any],
    fit_boundary: pd.Timestamp,
) -> AdaptiveModel:
    variant_id = str(variant["variant_id"])
    kind = str(variant["kind"])
    fit = frame.copy()
    if kind == "ROLLING":
        start = pd.Timestamp(fit_boundary) - pd.DateOffset(
            months=int(variant["lookback_months"])
        )
        fit = fit.loc[fit["signal_time"].ge(start)].copy()
    minimum_rows = int(config["calibration_gates"]["minimum_fit_action_rows"])
    if len(fit) < minimum_rows:
        raise ValueError(f"{variant_id} has only {len(fit)} fit rows")

    weights = fit["structural_weight"].to_numpy(dtype=float)
    if kind == "RECENCY_WEIGHTED":
        multipliers = recency_multipliers(
            fit["label_end_time"],
            fit_boundary,
            half_life_months=int(variant["half_life_months"]),
            minimum_weight=float(variant["minimum_recency_weight"]),
        )
        adjusted = weights * multipliers
        if variant["normalize_weight_sum"]:
            adjusted *= float(weights.sum() / adjusted.sum())
        weights = adjusted

    model_spec = config["ridge_model"]
    global_model = _fit_weighted_ridge(
        fit, features=features, model_spec=model_spec, weights=weights
    )
    regime_models: dict[str, Any] = {}
    regime_metadata: dict[str, Any] = {}
    if kind == "REGIME_LOCAL":
        minimum_regime_rows = int(variant["minimum_regime_action_rows"])
        minimum_regime_events = int(variant["minimum_regime_events"])
        for regime, group in fit.groupby("regime", sort=True):
            events = int(group["event_id"].nunique())
            eligible = (
                len(group) >= minimum_regime_rows and events >= minimum_regime_events
            )
            regime_metadata[str(regime)] = {
                "action_rows": int(len(group)),
                "events": events,
                "local_model_fitted": bool(eligible),
            }
            if eligible:
                regime_models[str(regime)] = _fit_weighted_ridge(
                    group,
                    features=features,
                    model_spec=model_spec,
                    weights=group["structural_weight"].to_numpy(dtype=float),
                )
    return AdaptiveModel(
        variant_id=variant_id,
        global_model=global_model,
        regime_models=regime_models,
        fit_metadata={
            "fit_action_rows": int(len(fit)),
            "fit_events": int(fit["event_id"].nunique()),
            "fit_weight_sum": float(weights.sum()),
            "regimes": regime_metadata,
        },
    )


def predict_adaptive_model(
    model: AdaptiveModel, frame: pd.DataFrame, features: Sequence[str]
) -> np.ndarray:
    scores = np.asarray(model.global_model.predict(frame[list(features)]), dtype=float)
    for regime, local_model in model.regime_models.items():
        mask = frame["regime"].eq(regime).to_numpy()
        if mask.any():
            scores[mask] = np.asarray(
                local_model.predict(frame.loc[mask, list(features)]), dtype=float
            )
    return scores


def build_result_comparison(
    current: Mapping[str, Any], reference: Mapping[str, Any]
) -> dict[str, Any]:
    paths = {
        "selected_events": ("selected", "events"),
        "selected_fraction": ("selected_fraction",),
        "selected_mean_stress_r": ("selected", "weighted_mean_stress_r"),
        "selected_profit_factor": ("selected", "weighted_profit_factor"),
        "selected_max_drawdown_r": ("selected", "weighted_max_drawdown_r"),
        "weighted_test_auc": ("weighted_test_auc",),
        "common_event_action_uplift_r": (
            "comparison",
            "common_event_action_uplift_r",
        ),
        "latest_fold_mean_stress_r": (
            "latest_fold",
            "selected_weighted_mean_stress_r",
        ),
        "latest_fold_profit_factor": (
            "latest_fold",
            "selected_weighted_profit_factor",
        ),
    }

    def get(value: Mapping[str, Any], path: tuple[str, ...]) -> Any:
        result: Any = value
        for key in path:
            result = result[key]
        return result

    lanes: dict[str, Any] = {}
    for lane, current_family in current["families"].items():
        reference_family = reference["families"][lane]
        metrics: dict[str, Any] = {}
        for name, path in paths.items():
            current_value = get(current_family["metrics"], path)
            reference_value = get(reference_family["metrics"], path)
            metrics[name] = {
                "adaptive_v5": reference_value,
                "horizon_v7": current_value,
                "delta_v7_minus_v5": (
                    None
                    if current_value is None or reference_value is None
                    else float(current_value) - float(reference_value)
                ),
            }
        lanes[lane] = {
            "adaptive_v5_decision": reference_family["decision"],
            "horizon_v7_decision": current_family["decision"],
            "metrics": metrics,
        }
    return {
        "schema_version": "xauusd_horizon_v7_vs_adaptive_v5",
        "adaptive_v5_decision": reference["decision"],
        "horizon_v7_decision": current["decision"],
        "lanes": lanes,
    }
