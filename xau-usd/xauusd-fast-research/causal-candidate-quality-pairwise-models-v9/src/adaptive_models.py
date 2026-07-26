from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

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


def base_method_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **{key: config[key] for key in REFERENCE_KEYS},
        "expected": {key: config["expected"][key] for key in EXPECTED_REFERENCE_KEYS},
    }


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
                "pairwise_v9": current_value,
                "delta_v9_minus_v5": (
                    None
                    if current_value is None or reference_value is None
                    else float(current_value) - float(reference_value)
                ),
            }
        lanes[lane] = {
            "adaptive_v5_decision": reference_family["decision"],
            "pairwise_v9_decision": current_family["decision"],
            "metrics": metrics,
        }
    return {
        "schema_version": "xauusd_pairwise_v9_vs_adaptive_v5",
        "adaptive_v5_decision": reference["decision"],
        "pairwise_v9_decision": current["decision"],
        "lanes": lanes,
    }
