from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.adaptive_models import base_method_contract, recency_multipliers


@dataclass
class AdaptiveClassifier:
    variant_id: str
    global_model: Pipeline
    regime_models: dict[str, Pipeline]
    fit_metadata: dict[str, Any]


@dataclass
class PairwiseModel:
    variant_id: str
    event_model: AdaptiveClassifier
    action_model: AdaptiveClassifier
    fit_metadata: dict[str, Any]


def assert_adaptive_v5_population_parity(
    config: Mapping[str, Any], reference: Mapping[str, Any]
) -> str:
    current = base_method_contract(config)
    expected = base_method_contract(reference)
    if current != expected:
        raise ValueError("Pairwise V9 changed an unauthorized Adaptive V5 method field")
    if config["training_variants"] != reference["training_variants"]:
        raise ValueError("Pairwise V9 training variants differ from Adaptive V5")
    from src.action_models import canonical_json_sha256

    return canonical_json_sha256(
        {
            "base_method": current,
            "training_variants": config["training_variants"],
        }
    )


def add_event_target(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "event_id",
        "stress_net_r",
        "structural_weight",
        "event_eval_weight",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Pairwise event target source is missing columns: {missing}")
    result = frame.copy()
    groups = result.groupby("event_id", sort=False, observed=True)
    result["event_best_stress_r"] = groups["stress_net_r"].transform("max")
    result["event_best_stress_r_positive"] = result["event_best_stress_r"].gt(0.0)
    if groups["event_eval_weight"].nunique().gt(1).any():
        raise ValueError("Event evaluation weight differs across available actions")
    structural_sum = groups["structural_weight"].sum()
    event_weight = groups["event_eval_weight"].first()
    if not np.allclose(
        structural_sum.to_numpy(dtype=float),
        event_weight.to_numpy(dtype=float),
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError("Repeated event rows do not preserve event training weight")
    return result


def pairwise_feature_columns(action_features: Sequence[str]) -> list[str]:
    return [f"pw__{feature}" for feature in action_features]


def build_pairwise_rows(
    frame: pd.DataFrame,
    *,
    action_features: Sequence[str],
    action_tie_order: Sequence[str],
) -> pd.DataFrame:
    required = {
        "event_id",
        "candidate_id",
        "action_id",
        "stress_net_r",
        "event_eval_weight",
        "structural_episode_id",
        "model_lane",
        "signal_time",
        "label_end_time",
        "regime",
        "model_eligible",
        *action_features,
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Pairwise source is missing columns: {missing}")
    if frame.duplicated(["event_id", "action_id"]).any():
        raise ValueError("Pairwise source has duplicate event/action rows")
    pair_features = pairwise_feature_columns(action_features)
    identity_columns = [
        "structural_episode_id",
        "model_lane",
        "signal_time",
        "regime",
        "model_eligible",
        "event_eval_weight",
    ]
    frames: list[pd.DataFrame] = []
    for left_action, right_action in combinations(action_tie_order, 2):
        left_columns = [
            "event_id",
            "candidate_id",
            "action_id",
            "stress_net_r",
            "label_end_time",
            *identity_columns,
            *action_features,
        ]
        right_columns = [
            "event_id",
            "candidate_id",
            "action_id",
            "stress_net_r",
            "label_end_time",
            *identity_columns,
            *action_features,
        ]
        left = frame.loc[frame["action_id"].eq(left_action), left_columns].rename(
            columns={column: f"left__{column}" for column in left_columns[1:]}
        )
        right = frame.loc[
            frame["action_id"].eq(right_action), right_columns
        ].rename(columns={column: f"right__{column}" for column in right_columns[1:]})
        merged = left.merge(
            right, on="event_id", how="inner", validate="one_to_one", sort=False
        )
        for column in identity_columns:
            left_value = merged[f"left__{column}"]
            right_value = merged[f"right__{column}"]
            if pd.api.types.is_numeric_dtype(left_value):
                equal = np.isclose(
                    left_value.to_numpy(dtype=float),
                    right_value.to_numpy(dtype=float),
                    rtol=0.0,
                    atol=1e-12,
                )
            else:
                equal = left_value.eq(right_value).to_numpy()
            if not bool(np.all(equal)):
                raise ValueError(
                    f"Pairwise event identity differs across actions: {column}"
                )
        left_r = merged["left__stress_net_r"].to_numpy(dtype=float)
        right_r = merged["right__stress_net_r"].to_numpy(dtype=float)
        tied = np.isclose(left_r, right_r, rtol=0.0, atol=1e-12)
        pair = pd.DataFrame(
            {
                "pair_id": (
                    merged["event_id"].astype(str)
                    + f"__{left_action}__VS__{right_action}"
                ),
                "event_id": merged["event_id"],
                "structural_episode_id": merged["left__structural_episode_id"],
                "model_lane": merged["left__model_lane"],
                "signal_time": merged["left__signal_time"],
                "label_end_time": merged[
                    ["left__label_end_time", "right__label_end_time"]
                ].max(axis=1),
                "regime": merged["left__regime"],
                "model_eligible": merged["left__model_eligible"],
                "left_candidate_id": merged["left__candidate_id"],
                "right_candidate_id": merged["right__candidate_id"],
                "left_action_id": merged["left__action_id"],
                "right_action_id": merged["right__action_id"],
                "pair_tied": tied,
                "pair_target": pd.array(
                    np.where(tied, None, left_r > right_r), dtype="boolean"
                ),
                "event_eval_weight": merged["left__event_eval_weight"],
            }
        )
        left_values = merged[
            [f"left__{feature}" for feature in action_features]
        ].to_numpy(dtype=float)
        right_values = merged[
            [f"right__{feature}" for feature in action_features]
        ].to_numpy(dtype=float)
        pair = pd.concat(
            [
                pair,
                pd.DataFrame(
                    left_values - right_values,
                    columns=pair_features,
                    index=pair.index,
                ),
            ],
            axis=1,
        )
        frames.append(pair)
    result = pd.concat(frames, ignore_index=True).copy()
    if result.empty:
        raise ValueError("Pairwise construction produced no comparisons")
    if result["pair_id"].duplicated().any():
        raise ValueError("Pairwise construction produced duplicate pair IDs")
    numeric = result[pair_features].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Pairwise feature differences contain non-finite values")
    result["available_pair_count"] = result.groupby(
        "event_id", observed=True
    )["pair_id"].transform("size")
    result["trainable_pair_count"] = (~result["pair_tied"]).groupby(
        result["event_id"], observed=True
    ).transform("sum")
    result["pair_weight"] = np.where(
        result["pair_tied"],
        0.0,
        result["event_eval_weight"] / result["trainable_pair_count"],
    )
    trainable = result.loc[~result["pair_tied"]]
    weight_sum = trainable.groupby("event_id", observed=True)["pair_weight"].sum()
    expected = trainable.groupby("event_id", observed=True)[
        "event_eval_weight"
    ].first()
    if not np.allclose(
        weight_sum.to_numpy(dtype=float),
        expected.to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError("Trainable pair weights do not preserve event weight")
    return result


def _build_classifier(spec: Mapping[str, Any]) -> Pipeline:
    if spec["kind"] != "LOGISTIC_REGRESSION":
        raise ValueError(f"Unsupported pairwise classifier: {spec['kind']}")
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", LogisticRegression(**dict(spec["parameters"]))),
        ]
    )


def _variant_fit_frame(
    frame: pd.DataFrame,
    *,
    variant: Mapping[str, Any],
    fit_boundary: pd.Timestamp,
) -> pd.DataFrame:
    fit = frame.copy()
    if variant["kind"] == "ROLLING":
        start = pd.Timestamp(fit_boundary) - pd.DateOffset(
            months=int(variant["lookback_months"])
        )
        fit = fit.loc[fit["signal_time"].ge(start)].copy()
    return fit


def _fit_classifier(
    frame: pd.DataFrame,
    *,
    features: Sequence[str],
    target: str,
    weight: str,
    config: Mapping[str, Any],
    variant: Mapping[str, Any],
    fit_boundary: pd.Timestamp,
    minimum_rows: int,
    minimum_events: int,
) -> AdaptiveClassifier:
    variant_id = str(variant["variant_id"])
    fit = _variant_fit_frame(
        frame, variant=variant, fit_boundary=fit_boundary
    )
    if len(fit) < minimum_rows or fit["event_id"].nunique() < minimum_events:
        raise ValueError(
            f"{variant_id} has insufficient classifier rows/events: "
            f"{len(fit)}/{fit['event_id'].nunique()}"
        )
    if fit[target].nunique() < 2:
        raise ValueError(f"{variant_id} classifier target has one class")
    weights = fit[weight].to_numpy(dtype=float)
    if variant["kind"] == "RECENCY_WEIGHTED":
        multipliers = recency_multipliers(
            fit["label_end_time"],
            fit_boundary,
            half_life_months=int(variant["half_life_months"]),
            minimum_weight=float(variant["minimum_recency_weight"]),
        )
        weights = weights * multipliers
        if variant["normalize_weight_sum"]:
            weights *= float(fit[weight].sum() / weights.sum())
    global_model = _build_classifier(config["classifier_model"])
    global_model.fit(
        fit[list(features)], fit[target].astype(int), model__sample_weight=weights
    )
    regime_models: dict[str, Pipeline] = {}
    regime_metadata: dict[str, Any] = {}
    if variant["kind"] == "REGIME_LOCAL":
        for regime, group in fit.groupby("regime", sort=True, observed=True):
            events = int(group["event_id"].nunique())
            eligible = (
                len(group) >= minimum_rows
                and events >= minimum_events
                and group[target].nunique() >= 2
            )
            regime_metadata[str(regime)] = {
                "rows": int(len(group)),
                "events": events,
                "local_model_fitted": bool(eligible),
            }
            if eligible:
                model = _build_classifier(config["classifier_model"])
                model.fit(
                    group[list(features)],
                    group[target].astype(int),
                    model__sample_weight=group[weight].to_numpy(dtype=float),
                )
                regime_models[str(regime)] = model
    return AdaptiveClassifier(
        variant_id=variant_id,
        global_model=global_model,
        regime_models=regime_models,
        fit_metadata={
            "fit_rows": int(len(fit)),
            "fit_events": int(fit["event_id"].nunique()),
            "fit_weight_sum": float(weights.sum()),
            "positive_weight_fraction": float(
                np.average(fit[target].astype(int), weights=weights)
            ),
            "regimes": regime_metadata,
        },
    )


def _predict_classifier(
    model: AdaptiveClassifier, frame: pd.DataFrame, features: Sequence[str]
) -> np.ndarray:
    scores = np.asarray(
        model.global_model.predict_proba(frame[list(features)])[:, 1], dtype=float
    )
    for regime, local_model in model.regime_models.items():
        mask = frame["regime"].eq(regime).to_numpy()
        if mask.any():
            scores[mask] = np.asarray(
                local_model.predict_proba(frame.loc[mask, list(features)])[:, 1],
                dtype=float,
            )
    return scores


def fit_pairwise_model(
    event_frame: pd.DataFrame,
    pair_frame: pd.DataFrame,
    *,
    event_features: Sequence[str],
    pair_features: Sequence[str],
    config: Mapping[str, Any],
    variant: Mapping[str, Any],
    fit_boundary: pd.Timestamp,
) -> PairwiseModel:
    trainable_pairs = pair_frame.loc[~pair_frame["pair_tied"]].copy()
    gates = config["calibration_gates"]
    event_model = _fit_classifier(
        event_frame,
        features=event_features,
        target="event_best_stress_r_positive",
        weight="structural_weight",
        config=config,
        variant=variant,
        fit_boundary=fit_boundary,
        minimum_rows=int(gates["minimum_fit_action_rows"]),
        minimum_events=int(config["pairwise_contract"]["minimum_fit_events"]),
    )
    action_model = _fit_classifier(
        trainable_pairs,
        features=pair_features,
        target="pair_target",
        weight="pair_weight",
        config=config,
        variant=variant,
        fit_boundary=fit_boundary,
        minimum_rows=int(config["pairwise_contract"]["minimum_fit_pair_rows"]),
        minimum_events=int(config["pairwise_contract"]["minimum_fit_events"]),
    )
    return PairwiseModel(
        variant_id=str(variant["variant_id"]),
        event_model=event_model,
        action_model=action_model,
        fit_metadata={
            "variant_id": str(variant["variant_id"]),
            "event_model": event_model.fit_metadata,
            "action_model": action_model.fit_metadata,
        },
    )


def score_pairwise_model(
    model: PairwiseModel,
    event_frame: pd.DataFrame,
    pair_frame: pd.DataFrame,
    *,
    event_features: Sequence[str],
    pair_features: Sequence[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scored = event_frame.copy()
    scored["event_score"] = _predict_classifier(
        model.event_model, scored, event_features
    )
    spread = scored.groupby("event_id", observed=True)["event_score"].agg(
        lambda values: float(values.max() - values.min())
    )
    if spread.gt(1e-12).any():
        raise ValueError("Event-stage probabilities differ across one event's actions")
    scored_pairs = pair_frame.copy()
    scored_pairs["left_win_probability"] = _predict_classifier(
        model.action_model, scored_pairs, pair_features
    )
    contributions = pd.concat(
        [
            scored_pairs[["left_candidate_id", "left_win_probability"]].rename(
                columns={
                    "left_candidate_id": "candidate_id",
                    "left_win_probability": "pair_probability",
                }
            ),
            scored_pairs[["right_candidate_id", "left_win_probability"]]
            .assign(
                pair_probability=lambda value: 1.0
                - value["left_win_probability"]
            )
            .drop(columns="left_win_probability")
            .rename(columns={"right_candidate_id": "candidate_id"}),
        ],
        ignore_index=True,
    )
    borda = contributions.groupby("candidate_id", observed=True)[
        "pair_probability"
    ].mean()
    scored["pairwise_borda_score"] = scored["candidate_id"].map(borda).fillna(0.5)
    scored["action_advantage_score"] = scored["pairwise_borda_score"]
    scored["model_score"] = scored["event_score"]
    return scored, scored_pairs


def choose_pairwise_action(scored: pd.DataFrame) -> pd.DataFrame:
    return (
        scored.sort_values(
            [
                "event_id",
                "pairwise_borda_score",
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


def pairwise_test_auc(scored_pairs: pd.DataFrame) -> float | None:
    trainable = scored_pairs.loc[~scored_pairs["pair_tied"]]
    target = trainable["pair_target"].astype(int)
    if target.nunique() < 2:
        return None
    return float(
        roc_auc_score(
            target,
            trainable["left_win_probability"],
            sample_weight=trainable["pair_weight"],
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
    ].merge(oracle, on="event_id", how="inner", validate="one_to_one")
    correct = np.isclose(
        comparison["stress_net_r"].to_numpy(dtype=float),
        comparison["oracle_stress_net_r"].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
    )
    return float(np.average(correct, weights=comparison["event_eval_weight"]))


def pairwise_target_audit(
    event_frame: pd.DataFrame, pair_frame: pd.DataFrame
) -> dict[str, Any]:
    event_groups = event_frame.groupby("event_id", sort=False, observed=True)
    event_target = event_frame.sort_values(
        "candidate_id", kind="mergesort"
    ).drop_duplicates("event_id", keep="first")
    weight_error = (
        event_groups["structural_weight"].sum()
        - event_groups["event_eval_weight"].first()
    ).abs()
    trainable = pair_frame.loc[~pair_frame["pair_tied"]]
    pair_weight_error = (
        trainable.groupby("event_id", observed=True)["pair_weight"].sum()
        - trainable.groupby("event_id", observed=True)["event_eval_weight"].first()
    ).abs()
    return {
        "action_rows": int(len(event_frame)),
        "events": int(event_frame["event_id"].nunique()),
        "event_best_positive": int(
            event_target["event_best_stress_r_positive"].sum()
        ),
        "event_best_nonpositive": int(
            (~event_target["event_best_stress_r_positive"]).sum()
        ),
        "pair_rows": int(len(pair_frame)),
        "trainable_pair_rows": int(len(trainable)),
        "tied_pair_rows": int(pair_frame["pair_tied"].sum()),
        "left_wins": int(trainable["pair_target"].sum()),
        "right_wins": int((~trainable["pair_target"].astype(bool)).sum()),
        "maximum_absolute_event_weight_error": float(weight_error.max()),
        "maximum_absolute_pair_weight_error": float(pair_weight_error.max()),
        "available_actions_per_event": {
            str(int(key)): int(value)
            for key, value in event_groups.size().value_counts().sort_index().items()
        },
    }
