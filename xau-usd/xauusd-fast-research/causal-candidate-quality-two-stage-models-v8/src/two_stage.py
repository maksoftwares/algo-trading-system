from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.adaptive_models import (
    AdaptiveModel,
    fit_adaptive_model,
    predict_adaptive_model,
)


@dataclass
class TwoStageModel:
    variant_id: str
    event_model: AdaptiveModel
    action_model: AdaptiveModel
    fit_metadata: dict[str, Any]


def add_two_stage_targets(
    frame: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    required = {
        "event_id",
        "stress_net_r",
        "action_id",
        "candidate_id",
        "structural_weight",
        "event_eval_weight",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Two-stage target source is missing columns: {missing}")
    result = frame.copy()
    grouped = result.groupby("event_id", sort=False, observed=True)["stress_net_r"]
    result["event_best_stress_r"] = grouped.transform("max")
    result["event_mean_stress_r"] = grouped.transform("mean")
    result["action_advantage_r"] = (
        result["stress_net_r"] - result["event_mean_stress_r"]
    )
    result["event_best_stress_r_positive"] = result["event_best_stress_r"].gt(0.0)
    event_clip = config["target"]
    advantage_clip = config["two_stage_contract"]["action_advantage_clip"]
    result["event_target_fit"] = result["event_best_stress_r"].clip(
        lower=float(event_clip["clip_min_r"]),
        upper=float(event_clip["clip_max_r"]),
    )
    result["action_advantage_target_fit"] = result["action_advantage_r"].clip(
        lower=float(advantage_clip["minimum_r"]),
        upper=float(advantage_clip["maximum_r"]),
    )
    centered = result.groupby("event_id", observed=True)["action_advantage_r"].mean()
    if not np.allclose(centered.to_numpy(dtype=float), 0.0, atol=1e-12, rtol=0.0):
        raise ValueError("Action advantage targets are not centered within event")
    event_groups = result.groupby("event_id", sort=False, observed=True)
    if event_groups["event_eval_weight"].nunique().gt(1).any():
        raise ValueError("Event evaluation weight differs across available actions")
    structural_sum = event_groups["structural_weight"].sum()
    event_weight = event_groups["event_eval_weight"].first()
    if not np.allclose(
        structural_sum.to_numpy(dtype=float),
        event_weight.to_numpy(dtype=float),
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError("Repeated action rows do not preserve event training weight")
    return result


def two_stage_target_audit(frame: pd.DataFrame) -> dict[str, Any]:
    event_groups = frame.groupby("event_id", sort=False, observed=True)
    event_target = frame.sort_values(
        "candidate_id", kind="mergesort"
    ).drop_duplicates("event_id", keep="first")
    weight_error = (
        event_groups["structural_weight"].sum()
        - event_groups["event_eval_weight"].first()
    ).abs()
    return {
        "action_rows": int(len(frame)),
        "events": int(frame["event_id"].nunique()),
        "event_best_positive": int(
            event_target["event_best_stress_r_positive"].sum()
        ),
        "event_best_nonpositive": int(
            (~event_target["event_best_stress_r_positive"]).sum()
        ),
        "action_advantage_mean_r": float(frame["action_advantage_r"].mean()),
        "maximum_absolute_event_centering_error_r": float(
            event_groups["action_advantage_r"].mean().abs().max()
        ),
        "maximum_absolute_event_weight_error": float(weight_error.max()),
        "events_with_inconsistent_evaluation_weight": int(
            event_groups["event_eval_weight"].nunique().gt(1).sum()
        ),
        "available_actions_per_event": {
            str(int(key)): int(value)
            for key, value in event_groups.size().value_counts().sort_index().items()
        },
    }


def fit_two_stage_model(
    frame: pd.DataFrame,
    *,
    event_features: Sequence[str],
    action_features: Sequence[str],
    config: dict[str, Any],
    variant: dict[str, Any],
    fit_boundary: pd.Timestamp,
) -> TwoStageModel:
    event_fit = frame.copy()
    event_fit["target_fit"] = event_fit["event_target_fit"]
    action_fit = frame.copy()
    action_fit["target_fit"] = action_fit["action_advantage_target_fit"]
    event_model = fit_adaptive_model(
        event_fit,
        features=event_features,
        config=config,
        variant=variant,
        fit_boundary=fit_boundary,
    )
    action_model = fit_adaptive_model(
        action_fit,
        features=action_features,
        config=config,
        variant=variant,
        fit_boundary=fit_boundary,
    )
    metadata = {
        "variant_id": str(variant["variant_id"]),
        "event_model": event_model.fit_metadata,
        "action_model": action_model.fit_metadata,
        "fit_action_rows": int(len(frame)),
        "fit_events": int(frame["event_id"].nunique()),
    }
    return TwoStageModel(
        variant_id=str(variant["variant_id"]),
        event_model=event_model,
        action_model=action_model,
        fit_metadata=metadata,
    )


def score_two_stage_model(
    model: TwoStageModel,
    frame: pd.DataFrame,
    *,
    event_features: Sequence[str],
    action_features: Sequence[str],
) -> pd.DataFrame:
    result = frame.copy()
    result["event_score"] = predict_adaptive_model(
        model.event_model, result, event_features
    )
    result["action_advantage_score"] = predict_adaptive_model(
        model.action_model, result, action_features
    )
    spread = result.groupby("event_id", observed=True)["event_score"].agg(
        lambda values: float(values.max() - values.min())
    )
    if spread.gt(1e-12).any():
        raise ValueError("Event-stage scores differ across actions for one event")
    result["model_score"] = result["event_score"]
    return result


def choose_two_stage_action(scored: pd.DataFrame) -> pd.DataFrame:
    return (
        scored.sort_values(
            [
                "event_id",
                "action_advantage_score",
                "action_tie_rank",
                "candidate_id",
            ],
            ascending=[True, False, True, True],
            kind="mergesort",
        )
        .drop_duplicates("event_id", keep="first")
        .sort_values(["signal_time", "event_id"], kind="mergesort")
        .reset_index(drop=True)
    )


def event_tradeability_auc(scored: pd.DataFrame) -> float | None:
    event = scored.sort_values("candidate_id", kind="mergesort").drop_duplicates(
        "event_id", keep="first"
    )
    target = event["event_best_stress_r_positive"].astype(int)
    if target.nunique() < 2:
        return None
    return float(
        roc_auc_score(
            target,
            event["event_score"],
            sample_weight=event["event_eval_weight"],
        )
    )


def chosen_action_outcome_auc(chosen: pd.DataFrame) -> float | None:
    target = chosen["stress_net_r_positive"].astype(int)
    if target.nunique() < 2:
        return None
    return float(
        roc_auc_score(
            target,
            chosen["event_score"],
            sample_weight=chosen["event_eval_weight"],
        )
    )


def action_choice_accuracy(scored: pd.DataFrame, chosen: pd.DataFrame) -> float:
    oracle = (
        scored.groupby("event_id", observed=True)["stress_net_r"]
        .max()
        .rename("oracle_stress_net_r")
        .reset_index()
    )
    comparison = chosen[
        ["event_id", "stress_net_r", "event_eval_weight"]
    ].merge(
        oracle, on="event_id", how="inner", validate="one_to_one"
    )
    correct = np.isclose(
        comparison["stress_net_r"].to_numpy(dtype=float),
        comparison["oracle_stress_net_r"].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
    )
    return float(np.average(correct, weights=comparison["event_eval_weight"]))
