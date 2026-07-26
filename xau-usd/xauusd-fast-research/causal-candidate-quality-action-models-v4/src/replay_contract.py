from __future__ import annotations

from typing import Any, Mapping

from src.action_models import canonical_json_sha256


VERSIONED_CONFIG_KEYS = {"schema_version", "inputs", "outputs", "replay_contract"}


def experimental_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in config.items() if key not in VERSIONED_CONFIG_KEYS
    }


def assert_method_parity(
    current: Mapping[str, Any], reference: Mapping[str, Any]
) -> str:
    current_contract = experimental_contract(current)
    reference_contract = experimental_contract(reference)
    if current_contract != reference_contract:
        raise ValueError("Action V4 methodology differs from frozen Action V3")
    if current["replay_contract"]["methodology_change_authorized"]:
        raise ValueError("Action V4 methodology change was unexpectedly authorized")
    return canonical_json_sha256(current_contract)


def build_result_comparison(
    current: Mapping[str, Any], reference: Mapping[str, Any]
) -> dict[str, Any]:
    lanes: dict[str, Any] = {}
    metric_paths = {
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

    for lane, current_family in current["families"].items():
        reference_family = reference["families"][lane]
        metrics: dict[str, Any] = {}
        for name, path in metric_paths.items():
            current_value = get(current_family["metrics"], path)
            reference_value = get(reference_family["metrics"], path)
            delta = (
                None
                if current_value is None or reference_value is None
                else float(current_value) - float(reference_value)
            )
            metrics[name] = {
                "v3": reference_value,
                "v4": current_value,
                "delta_v4_minus_v3": delta,
            }
        lanes[lane] = {
            "v3_decision": reference_family["decision"],
            "v4_decision": current_family["decision"],
            "metrics": metrics,
        }
    return {
        "schema_version": "xauusd_action_v4_vs_v3_comparison",
        "comparison_scope": "CORRECTED_DENSITY_FEATURES_ONLY",
        "methodology_equal": True,
        "v3_decision": reference["decision"],
        "v4_decision": current["decision"],
        "lanes": lanes,
    }
