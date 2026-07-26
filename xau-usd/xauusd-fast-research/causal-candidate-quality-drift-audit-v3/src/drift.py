from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
from sklearn.metrics import roc_auc_score


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(dict(value)), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def resolve_inputs(repo_root: Path, config: Mapping[str, Any]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, spec in config["inputs"].items():
        path = repo_root / str(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != str(spec["sha256"]):
            raise ValueError(f"Input hash mismatch for {name}: {actual}")
        paths[name] = path
    return paths


def require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def assign_model_lane(
    frame: pd.DataFrame, action_config: Mapping[str, Any]
) -> pd.Series:
    ownership = action_config["lane_ownership"]
    result = pd.Series(pd.NA, index=frame.index, dtype="string")
    for lane in reversed(list(ownership["priority"])):
        flag = str(ownership["flag_columns"][lane])
        result.loc[frame[flag].eq(1.0)] = lane
    if result.isna().any():
        raise ValueError("A V3 event has no model-lane owner")
    return result.astype(str)


def session_for_hour(hour: int, sessions: Sequence[Mapping[str, Any]]) -> str:
    for session in sessions:
        if int(session["start_hour"]) <= hour < int(session["end_hour"]):
            return str(session["name"])
    raise ValueError(f"UTC hour {hour} is not covered by the session contract")


def prepare_actions(
    dataset: pd.DataFrame,
    splits: pd.DataFrame,
    v3_config: Mapping[str, Any],
    action_config: Mapping[str, Any],
    audit_config: Mapping[str, Any],
) -> pd.DataFrame:
    features = list(v3_config["model_features"])
    require_columns(
        dataset,
        [
            "candidate_id",
            "event_id",
            "structural_episode_id",
            "signal_time",
            "direction",
            "regime",
            "action_id",
            "stress_net_r",
            "stress_net_r_positive",
            "mfe_r",
            "mae_r",
            "exit_reason",
            "structural_weight",
            "resolved_events_in_structural_episode",
            *features,
            *action_config["lane_ownership"]["flag_columns"].values(),
        ],
        "V3 action dataset",
    )
    if len(dataset) != int(audit_config["expected"]["action_rows"]):
        raise ValueError("V3 action row count changed")
    if len(features) != int(audit_config["expected"]["model_features"]):
        raise ValueError("V3 model feature count changed")
    result = dataset.copy()
    result["signal_time"] = pd.to_datetime(result["signal_time"], utc=True)
    result["model_lane"] = assign_model_lane(result, action_config)
    result = result.loc[
        ~result["regime"].isin(set(action_config["exclusions"]["regimes"]))
    ].copy()
    fold = splits.loc[
        splits["fold_id"].eq(audit_config["target_fold"]) & splits["eligible"]
    ].copy()
    partition_to_period = {
        str(partition): str(period)
        for period, partition in audit_config["periods"].items()
    }
    fold = fold.loc[fold["partition"].isin(partition_to_period)].copy()
    fold["period"] = fold["partition"].map(partition_to_period)
    result = result.merge(
        fold[["structural_episode_id", "period"]],
        on="structural_episode_id",
        how="inner",
        validate="many_to_one",
    )
    result["event_eval_weight"] = 1.0 / result[
        "resolved_events_in_structural_episode"
    ].astype(float)
    tie_order = {
        action: index for index, action in enumerate(action_config["action_tie_order"])
    }
    result["action_tie_rank"] = result["action_id"].map(tie_order)
    if result["action_tie_rank"].isna().any():
        raise ValueError("V3 dataset contains an unlocked action")
    result["session_utc"] = result["signal_time"].dt.hour.map(
        lambda hour: session_for_hour(int(hour), audit_config["sessions_utc"])
    )
    availability = (
        result.sort_values("action_tie_rank", kind="mergesort")
        .groupby(["period", "model_lane", "event_id"], sort=False)["action_id"]
        .agg("|".join)
        .rename("action_availability")
        .reset_index()
    )
    result = result.merge(
        availability,
        on=["period", "model_lane", "event_id"],
        how="left",
        validate="many_to_one",
    )
    numeric = result[features].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("V3 model features contain non-finite values")
    if result["candidate_id"].duplicated().any():
        raise ValueError("Drift source contains duplicate candidate IDs")
    return result


def replay_policy(
    model: Any,
    actions: pd.DataFrame,
    features: Sequence[str],
    threshold: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scored = actions.copy()
    scored["model_score"] = model.predict(scored[list(features)]).astype(float)
    scored = scored.sort_values(
        ["period", "event_id", "model_score", "action_tie_rank"],
        ascending=[True, True, False, True],
        kind="mergesort",
    )
    scored["chosen_action_flag"] = ~scored.duplicated(["period", "event_id"])
    chosen = scored.loc[scored["chosen_action_flag"]].copy()
    chosen["chosen_action"] = chosen["action_id"]
    chosen["selected"] = chosen["model_score"].ge(float(threshold))
    scored = scored.merge(
        chosen[["period", "event_id", "selected"]],
        on=["period", "event_id"],
        how="left",
        validate="many_to_one",
    )
    scored["selected"] &= scored["chosen_action_flag"]
    return scored, chosen


def weighted_quantile(
    values: Sequence[float], weights: Sequence[float], quantiles: Sequence[float]
) -> np.ndarray:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    mask = np.isfinite(value_array) & np.isfinite(weight_array) & (weight_array > 0)
    value_array = value_array[mask]
    weight_array = weight_array[mask]
    if len(value_array) == 0:
        return np.full(len(quantiles), np.nan)
    order = np.argsort(value_array, kind="mergesort")
    value_array = value_array[order]
    weight_array = weight_array[order]
    cumulative = (np.cumsum(weight_array) - 0.5 * weight_array) / weight_array.sum()
    return np.interp(
        np.asarray(quantiles, dtype=float),
        cumulative,
        value_array,
        left=value_array[0],
        right=value_array[-1],
    )


def weighted_mean(values: Sequence[float], weights: Sequence[float]) -> float:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    mask = np.isfinite(value_array) & np.isfinite(weight_array) & (weight_array > 0)
    if not mask.any():
        return math.nan
    return float(np.average(value_array[mask], weights=weight_array[mask]))


def weighted_variance(values: Sequence[float], weights: Sequence[float]) -> float:
    mean = weighted_mean(values, weights)
    if not math.isfinite(mean):
        return math.nan
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    mask = np.isfinite(value_array) & np.isfinite(weight_array) & (weight_array > 0)
    return float(
        np.average((value_array[mask] - mean) ** 2, weights=weight_array[mask])
    )


def profit_factor(values: Sequence[float], weights: Sequence[float]) -> float:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    gains = float(np.sum(np.maximum(value_array, 0.0) * weight_array))
    losses = float(-np.sum(np.minimum(value_array, 0.0) * weight_array))
    if losses == 0.0:
        return math.inf if gains > 0.0 else math.nan
    return gains / losses


def weighted_auc(
    labels: Sequence[bool], scores: Sequence[float], weights: Sequence[float]
) -> float:
    label_array = np.asarray(labels, dtype=int)
    if len(np.unique(label_array)) < 2:
        return math.nan
    return float(
        roc_auc_score(
            label_array,
            np.asarray(scores, dtype=float),
            sample_weight=np.asarray(weights, dtype=float),
        )
    )


def numeric_psi(
    reference: Sequence[float],
    current: Sequence[float],
    reference_weights: Sequence[float],
    current_weights: Sequence[float],
    bins: int,
    epsilon: float,
) -> float:
    quantiles = np.linspace(0.0, 1.0, bins + 1)[1:-1]
    inner = np.unique(weighted_quantile(reference, reference_weights, quantiles))
    inner = inner[np.isfinite(inner)]
    edges = np.concatenate(([-np.inf], inner, [np.inf]))
    reference_hist = np.histogram(
        np.asarray(reference, dtype=float),
        bins=edges,
        weights=np.asarray(reference_weights, dtype=float),
    )[0]
    current_hist = np.histogram(
        np.asarray(current, dtype=float),
        bins=edges,
        weights=np.asarray(current_weights, dtype=float),
    )[0]
    reference_p = reference_hist / reference_hist.sum()
    current_p = current_hist / current_hist.sum()
    reference_p = np.clip(reference_p, epsilon, None)
    current_p = np.clip(current_p, epsilon, None)
    reference_p /= reference_p.sum()
    current_p /= current_p.sum()
    return float(np.sum((current_p - reference_p) * np.log(current_p / reference_p)))


def feature_drift_table(
    actions: pd.DataFrame,
    features: Sequence[str],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    spec = config["numeric_drift"]
    rows: list[dict[str, Any]] = []
    for lane in config["expected"]["lanes"]:
        lane_frame = actions.loc[actions["model_lane"].eq(lane)]
        reference = lane_frame.loc[lane_frame["period"].eq("REFERENCE")]
        current = lane_frame.loc[lane_frame["period"].eq("CURRENT")]
        for feature in features:
            ref_values = reference[feature].to_numpy(dtype=float)
            cur_values = current[feature].to_numpy(dtype=float)
            ref_weights = reference["structural_weight"].to_numpy(dtype=float)
            cur_weights = current["structural_weight"].to_numpy(dtype=float)
            ref_mean = weighted_mean(ref_values, ref_weights)
            cur_mean = weighted_mean(cur_values, cur_weights)
            ref_var = weighted_variance(ref_values, ref_weights)
            cur_var = weighted_variance(cur_values, cur_weights)
            pooled_std = math.sqrt(max((ref_var + cur_var) / 2.0, 0.0))
            if pooled_std > 0.0:
                smd = (cur_mean - ref_mean) / pooled_std
            else:
                smd = (
                    0.0
                    if cur_mean == ref_mean
                    else math.copysign(math.inf, cur_mean - ref_mean)
                )
            psi = numeric_psi(
                ref_values,
                cur_values,
                ref_weights,
                cur_weights,
                bins=int(spec["quantile_bins"]),
                epsilon=float(spec["epsilon"]),
            )
            ref_quartiles = weighted_quantile(
                ref_values, ref_weights, [0.25, 0.5, 0.75]
            )
            cur_median = weighted_quantile(cur_values, cur_weights, [0.5])[0]
            ref_iqr = ref_quartiles[2] - ref_quartiles[0]
            distance = float(
                wasserstein_distance(
                    ref_values,
                    cur_values,
                    u_weights=ref_weights,
                    v_weights=cur_weights,
                )
            )
            normalized_distance = distance / ref_iqr if ref_iqr > 0.0 else math.nan
            if abs(smd) >= float(spec["severe_absolute_smd"]) or psi >= float(
                spec["severe_psi"]
            ):
                severity = "SEVERE"
            elif abs(smd) >= float(spec["moderate_absolute_smd"]) or psi >= float(
                spec["moderate_psi"]
            ):
                severity = "MODERATE"
            else:
                severity = "LOW"
            rows.append(
                {
                    "model_lane": lane,
                    "feature": feature,
                    "reference_rows": len(reference),
                    "current_rows": len(current),
                    "reference_weight": float(ref_weights.sum()),
                    "current_weight": float(cur_weights.sum()),
                    "reference_mean": ref_mean,
                    "current_mean": cur_mean,
                    "reference_median": float(ref_quartiles[1]),
                    "current_median": float(cur_median),
                    "reference_std": math.sqrt(max(ref_var, 0.0)),
                    "current_std": math.sqrt(max(cur_var, 0.0)),
                    "standardized_mean_difference": smd,
                    "absolute_smd": abs(smd),
                    "psi": psi,
                    "wasserstein": distance,
                    "wasserstein_reference_iqr": normalized_distance,
                    "severity": severity,
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["model_lane", "severity", "psi", "absolute_smd"],
        ascending=[True, True, False, False],
        kind="mergesort",
    )


def distribution(
    frame: pd.DataFrame, column: str, weight_column: str
) -> dict[str, float]:
    values = frame[column].fillna("<NA>").astype(str)
    weights = frame[weight_column].astype(float)
    totals = weights.groupby(values).sum()
    if totals.sum() <= 0.0:
        return {}
    return (totals / totals.sum()).to_dict()


def categorical_drift_rows(
    chosen: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    epsilon = float(config["numeric_drift"]["epsilon"])
    spec = config["categorical_drift"]
    rows: list[dict[str, Any]] = []
    for lane in config["expected"]["lanes"]:
        lane_frame = chosen.loc[chosen["model_lane"].eq(lane)]
        reference = lane_frame.loc[lane_frame["period"].eq("REFERENCE")]
        current = lane_frame.loc[lane_frame["period"].eq("CURRENT")]
        for dimension in config["categorical_dimensions"]:
            ref_dist = distribution(reference, dimension, "event_eval_weight")
            cur_dist = distribution(current, dimension, "event_eval_weight")
            categories = sorted(set(ref_dist) | set(cur_dist))
            ref = np.array([ref_dist.get(category, 0.0) for category in categories])
            cur = np.array([cur_dist.get(category, 0.0) for category in categories])
            total_variation = float(0.5 * np.abs(cur - ref).sum())
            middle = 0.5 * (ref + cur)
            js = float(
                0.5
                * sum(
                    p * math.log(p / m) if p > 0.0 and m > 0.0 else 0.0
                    for p, m in zip(ref, middle, strict=True)
                )
                + 0.5
                * sum(
                    p * math.log(p / m) if p > 0.0 and m > 0.0 else 0.0
                    for p, m in zip(cur, middle, strict=True)
                )
            )
            ref_clip = np.clip(ref, epsilon, None)
            cur_clip = np.clip(cur, epsilon, None)
            ref_clip /= ref_clip.sum()
            cur_clip /= cur_clip.sum()
            contributions = (cur_clip - ref_clip) * np.log(cur_clip / ref_clip)
            psi = float(contributions.sum())
            if total_variation >= float(spec["severe_total_variation"]) or psi >= float(
                spec["severe_psi"]
            ):
                severity = "SEVERE"
            elif total_variation >= float(
                spec["moderate_total_variation"]
            ) or psi >= float(spec["moderate_psi"]):
                severity = "MODERATE"
            else:
                severity = "LOW"
            for index, category in enumerate(categories):
                rows.append(
                    {
                        "model_lane": lane,
                        "dimension": dimension,
                        "category": category,
                        "reference_proportion": float(ref[index]),
                        "current_proportion": float(cur[index]),
                        "proportion_delta": float(cur[index] - ref[index]),
                        "psi_contribution": float(contributions[index]),
                        "total_variation": total_variation,
                        "jensen_shannon": js,
                        "psi": psi,
                        "severity": severity,
                    }
                )
    return pd.DataFrame(rows).sort_values(
        ["model_lane", "dimension", "category"], kind="mergesort"
    )


def economic_summary(frame: pd.DataFrame) -> dict[str, Any]:
    weights = frame["event_eval_weight"].to_numpy(dtype=float)
    outcomes = frame["stress_net_r"].to_numpy(dtype=float)
    return {
        "events": int(len(frame)),
        "episodes": int(frame["structural_episode_id"].nunique()),
        "weight_sum": float(weights.sum()),
        "mean_r": weighted_mean(outcomes, weights),
        "profit_factor": profit_factor(outcomes, weights),
        "win_rate": weighted_mean(
            frame["stress_net_r_positive"].astype(float), weights
        ),
        "mean_mfe_r": weighted_mean(frame["mfe_r"], weights),
        "mean_mae_r": weighted_mean(frame["mae_r"], weights),
    }


def score_metrics_table(
    chosen: pd.DataFrame,
    policies: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for lane in config["expected"]["lanes"]:
        lane_frame = chosen.loc[chosen["model_lane"].eq(lane)]
        reference = lane_frame.loc[lane_frame["period"].eq("REFERENCE")]
        current = lane_frame.loc[lane_frame["period"].eq("CURRENT")]
        ref_weights = reference["event_eval_weight"].to_numpy(dtype=float)
        cur_weights = current["event_eval_weight"].to_numpy(dtype=float)
        reference_selected = reference.loc[reference["selected"]]
        current_selected = current.loc[current["selected"]]
        ref_economics = economic_summary(reference_selected)
        cur_economics = economic_summary(current_selected)
        ref_fraction = len(reference_selected) / len(reference)
        cur_fraction = len(current_selected) / len(current)
        ref_weighted_fraction = weighted_mean(
            reference["selected"].astype(float), ref_weights
        )
        cur_weighted_fraction = weighted_mean(
            current["selected"].astype(float), cur_weights
        )
        ref_auc = weighted_auc(
            reference["stress_net_r_positive"], reference["model_score"], ref_weights
        )
        cur_auc = weighted_auc(
            current["stress_net_r_positive"], current["model_score"], cur_weights
        )
        score_psi = numeric_psi(
            reference["model_score"],
            current["model_score"],
            ref_weights,
            cur_weights,
            bins=int(config["numeric_drift"]["quantile_bins"]),
            epsilon=float(config["numeric_drift"]["epsilon"]),
        )
        ref_mean = weighted_mean(reference["model_score"], ref_weights)
        cur_mean = weighted_mean(current["model_score"], cur_weights)
        pooled_std = math.sqrt(
            max(
                (
                    weighted_variance(reference["model_score"], ref_weights)
                    + weighted_variance(current["model_score"], cur_weights)
                )
                / 2.0,
                0.0,
            )
        )
        rows.append(
            {
                "model_lane": lane,
                "model_id": policies[lane]["model_id"],
                "score_threshold": float(policies[lane]["score_threshold"]),
                "reference_events": len(reference),
                "current_events": len(current),
                "reference_selected_events": len(reference_selected),
                "current_selected_events": len(current_selected),
                "reference_selected_fraction": ref_fraction,
                "current_selected_fraction": cur_fraction,
                "selected_fraction_delta": cur_fraction - ref_fraction,
                "reference_weighted_selected_fraction": ref_weighted_fraction,
                "current_weighted_selected_fraction": cur_weighted_fraction,
                "reference_score_mean": ref_mean,
                "current_score_mean": cur_mean,
                "score_smd": (cur_mean - ref_mean) / pooled_std
                if pooled_std > 0.0
                else 0.0,
                "score_psi": score_psi,
                "reference_auc": ref_auc,
                "current_auc": cur_auc,
                "auc_delta": cur_auc - ref_auc,
                **{
                    f"reference_selected_{key}": value
                    for key, value in ref_economics.items()
                },
                **{
                    f"current_selected_{key}": value
                    for key, value in cur_economics.items()
                },
                "selected_mean_r_delta": cur_economics["mean_r"]
                - ref_economics["mean_r"],
                "selected_win_rate_delta": cur_economics["win_rate"]
                - ref_economics["win_rate"],
            }
        )
    return pd.DataFrame(rows).sort_values("model_lane", kind="mergesort")


def score_bin_table(chosen: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    bins = int(config["numeric_drift"]["quantile_bins"])
    for lane in config["expected"]["lanes"]:
        lane_frame = chosen.loc[chosen["model_lane"].eq(lane)].copy()
        reference = lane_frame.loc[lane_frame["period"].eq("REFERENCE")]
        edges = np.unique(
            weighted_quantile(
                reference["model_score"],
                reference["event_eval_weight"],
                np.linspace(0.0, 1.0, bins + 1)[1:-1],
            )
        )
        lane_frame["reference_score_bin"] = (
            np.digitize(
                lane_frame["model_score"].to_numpy(dtype=float), edges, right=True
            )
            + 1
        )
        for (period, score_bin), group in lane_frame.groupby(
            ["period", "reference_score_bin"], sort=True
        ):
            weights = group["event_eval_weight"].to_numpy(dtype=float)
            rows.append(
                {
                    "model_lane": lane,
                    "period": period,
                    "reference_score_bin": int(score_bin),
                    "events": len(group),
                    "weight_sum": float(weights.sum()),
                    "score_mean": weighted_mean(group["model_score"], weights),
                    "mean_r": weighted_mean(group["stress_net_r"], weights),
                    "win_rate": weighted_mean(
                        group["stress_net_r_positive"].astype(float), weights
                    ),
                    "profit_factor": profit_factor(group["stress_net_r"], weights),
                    "selected_fraction": weighted_mean(
                        group["selected"].astype(float), weights
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["model_lane", "period", "reference_score_bin"], kind="mergesort"
    )


def monthly_metrics_table(chosen: pd.DataFrame) -> pd.DataFrame:
    frame = chosen.copy()
    frame["month"] = frame["signal_time"].dt.strftime("%Y-%m")
    rows: list[dict[str, Any]] = []
    for (lane, period, month), group in frame.groupby(
        ["model_lane", "period", "month"], sort=True
    ):
        weights = group["event_eval_weight"].to_numpy(dtype=float)
        selected = group.loc[group["selected"]]
        selected_weights = selected["event_eval_weight"].to_numpy(dtype=float)
        rows.append(
            {
                "model_lane": lane,
                "period": period,
                "month": month,
                "events": len(group),
                "selected_events": len(selected),
                "selected_fraction": weighted_mean(
                    group["selected"].astype(float), weights
                ),
                "auc": weighted_auc(
                    group["stress_net_r_positive"], group["model_score"], weights
                ),
                "selected_mean_r": weighted_mean(
                    selected["stress_net_r"], selected_weights
                ),
                "selected_profit_factor": profit_factor(
                    selected["stress_net_r"], selected_weights
                ),
                "selected_win_rate": weighted_mean(
                    selected["stress_net_r_positive"].astype(float), selected_weights
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["model_lane", "period", "month"], kind="mergesort"
    )


def label_metrics_table(
    actions: pd.DataFrame, chosen: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    def append_group(
        frame: pd.DataFrame,
        lane: str,
        period: str,
        scope: str,
        dimension: str,
        category: str,
        weight_column: str,
    ) -> None:
        weights = frame[weight_column].to_numpy(dtype=float)
        rows.append(
            {
                "model_lane": lane,
                "period": period,
                "scope": scope,
                "dimension": dimension,
                "category": str(category),
                "events": int(frame["event_id"].nunique()),
                "rows": len(frame),
                "weight_sum": float(weights.sum()),
                "mean_r": weighted_mean(frame["stress_net_r"], weights),
                "profit_factor": profit_factor(frame["stress_net_r"], weights),
                "win_rate": weighted_mean(
                    frame["stress_net_r_positive"].astype(float), weights
                ),
                "mean_mfe_r": weighted_mean(frame["mfe_r"], weights),
                "mean_mae_r": weighted_mean(frame["mae_r"], weights),
            }
        )

    for lane in config["expected"]["lanes"]:
        for period in ("REFERENCE", "CURRENT"):
            available = actions.loc[
                actions["model_lane"].eq(lane) & actions["period"].eq(period)
            ]
            for action, group in available.groupby("action_id", sort=True):
                append_group(
                    group,
                    lane,
                    period,
                    "AVAILABLE_ACTION",
                    "action_id",
                    str(action),
                    "structural_weight",
                )
            lane_chosen = chosen.loc[
                chosen["model_lane"].eq(lane) & chosen["period"].eq(period)
            ]
            for scope, scope_frame in (
                ("CHOSEN_ALL", lane_chosen),
                ("SELECTED", lane_chosen.loc[lane_chosen["selected"]]),
            ):
                append_group(
                    scope_frame,
                    lane,
                    period,
                    scope,
                    "ALL",
                    "ALL",
                    "event_eval_weight",
                )
                for dimension in config["decomposition_dimensions"]:
                    for category, group in scope_frame.groupby(dimension, sort=True):
                        append_group(
                            group,
                            lane,
                            period,
                            scope,
                            dimension,
                            str(category),
                            "event_eval_weight",
                        )
                for category, group in scope_frame.groupby("exit_reason", sort=True):
                    append_group(
                        group,
                        lane,
                        period,
                        scope,
                        "exit_reason",
                        str(category),
                        "event_eval_weight",
                    )
    return pd.DataFrame(rows).sort_values(
        ["model_lane", "scope", "dimension", "category", "period"],
        kind="mergesort",
    )


def decomposition_table(
    chosen: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for lane in config["expected"]["lanes"]:
        selected = chosen.loc[chosen["model_lane"].eq(lane) & chosen["selected"]]
        reference = selected.loc[selected["period"].eq("REFERENCE")]
        current = selected.loc[selected["period"].eq("CURRENT")]
        for dimension in config["decomposition_dimensions"]:
            ref_dist = distribution(reference, dimension, "event_eval_weight")
            cur_dist = distribution(current, dimension, "event_eval_weight")
            categories = sorted(set(ref_dist) | set(cur_dist))
            composition_total = 0.0
            within_total = 0.0
            for category in categories:
                ref_group = reference.loc[reference[dimension].astype(str).eq(category)]
                cur_group = current.loc[current[dimension].astype(str).eq(category)]
                ref_mean = weighted_mean(
                    ref_group["stress_net_r"], ref_group["event_eval_weight"]
                )
                cur_mean = weighted_mean(
                    cur_group["stress_net_r"], cur_group["event_eval_weight"]
                )
                if not math.isfinite(ref_mean):
                    ref_mean = cur_mean
                if not math.isfinite(cur_mean):
                    cur_mean = ref_mean
                ref_p = float(ref_dist.get(category, 0.0))
                cur_p = float(cur_dist.get(category, 0.0))
                composition = (cur_p - ref_p) * ref_mean
                within = cur_p * (cur_mean - ref_mean)
                composition_total += composition
                within_total += within
                rows.append(
                    {
                        "model_lane": lane,
                        "dimension": dimension,
                        "category": category,
                        "reference_proportion": ref_p,
                        "current_proportion": cur_p,
                        "reference_mean_r": ref_mean,
                        "current_mean_r": cur_mean,
                        "composition_effect_r": composition,
                        "within_stratum_effect_r": within,
                        "total_effect_r": composition + within,
                    }
                )
            ref_total = weighted_mean(
                reference["stress_net_r"], reference["event_eval_weight"]
            )
            cur_total = weighted_mean(
                current["stress_net_r"], current["event_eval_weight"]
            )
            rows.append(
                {
                    "model_lane": lane,
                    "dimension": dimension,
                    "category": "__TOTAL__",
                    "reference_proportion": 1.0,
                    "current_proportion": 1.0,
                    "reference_mean_r": ref_total,
                    "current_mean_r": cur_total,
                    "composition_effect_r": composition_total,
                    "within_stratum_effect_r": within_total,
                    "total_effect_r": cur_total - ref_total,
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["model_lane", "dimension", "category"], kind="mergesort"
    )


def build_findings(
    feature_metrics: pd.DataFrame,
    categorical_metrics: pd.DataFrame,
    score_metrics: pd.DataFrame,
    decomposition: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    rules = config["failure_rules"]
    lane_findings: dict[str, Any] = {}
    for lane in config["expected"]["lanes"]:
        features = feature_metrics.loc[feature_metrics["model_lane"].eq(lane)]
        severe = features.loc[features["severity"].eq("SEVERE")]
        top_features = features.sort_values(
            ["psi", "absolute_smd"], ascending=False, kind="mergesort"
        ).head(10)
        categories = categorical_metrics.loc[
            categorical_metrics["model_lane"].eq(lane)
        ].drop_duplicates("dimension")
        category_summary = {
            row.dimension: {
                "total_variation": float(row.total_variation),
                "psi": float(row.psi),
                "severity": row.severity,
            }
            for row in categories.itertuples(index=False)
        }
        score = score_metrics.loc[score_metrics["model_lane"].eq(lane)].iloc[0]
        totals = decomposition.loc[
            decomposition["model_lane"].eq(lane)
            & decomposition["category"].eq("__TOTAL__")
        ]
        decomposition_summary = {
            row.dimension: {
                "composition_effect_r": float(row.composition_effect_r),
                "within_stratum_effect_r": float(row.within_stratum_effect_r),
                "total_effect_r": float(row.total_effect_r),
            }
            for row in totals.itertuples(index=False)
        }
        coverage_drift = abs(float(score.selected_fraction_delta)) >= float(
            rules["minimum_absolute_coverage_shift"]
        )
        ranking_collapse = float(score.current_auc) < float(
            rules["ranking_collapse_auc"]
        ) and float(score.reference_auc - score.current_auc) >= float(
            rules["minimum_auc_drop"]
        )
        outcome_collapse = (
            float(score.reference_selected_mean_r) > 0.0
            and float(score.current_selected_mean_r) < 0.0
        ) or (
            float(score.selected_mean_r_delta) <= -float(rules["minimum_mean_r_drop"])
            and float(score.selected_win_rate_delta)
            <= -float(rules["minimum_win_rate_drop"])
        )
        base_edge_absent = float(score.reference_selected_mean_r) <= float(
            rules["base_edge_maximum_reference_mean_r"]
        ) and float(score.current_selected_mean_r) <= float(
            rules["base_edge_maximum_current_mean_r"]
        )
        broad_covariate_drift = len(severe) >= int(
            config["numeric_drift"]["severe_feature_count_for_lane_flag"]
        ) or any(
            category_summary.get(dimension, {}).get("severity") == "SEVERE"
            for dimension in ("regime", "session_utc")
        )
        within_deterioration = any(
            value["within_stratum_effect_r"]
            <= -float(rules["minimum_negative_within_stratum_effect_r"])
            for value in decomposition_summary.values()
        )
        if base_edge_absent:
            diagnosis = "BASE_EDGE_ABSENT"
            v4_disposition = "REDESIGN_MECHANIC_BEFORE_MORE_ML"
        elif ranking_collapse and outcome_collapse:
            diagnosis = "RANKING_AND_OUTCOME_COLLAPSE"
            v4_disposition = "REGIME_CONDITIONED_V4_RESEARCH_ONLY"
        elif outcome_collapse and coverage_drift:
            diagnosis = "COVERAGE_AND_OUTCOME_COLLAPSE"
            v4_disposition = "REGIME_CONDITIONED_V4_RESEARCH_ONLY"
        elif outcome_collapse:
            diagnosis = "OUTCOME_COLLAPSE"
            v4_disposition = "MECHANISM_AND_REGIME_REVIEW_BEFORE_V4"
        else:
            diagnosis = "NO_SINGLE_LOCKED_FAILURE_CLASS"
            v4_disposition = "NO_AUTOMATIC_MODEL_ITERATION"
        lane_findings[lane] = {
            "diagnosis": diagnosis,
            "v4_disposition": v4_disposition,
            "flags": {
                "base_edge_absent": base_edge_absent,
                "broad_covariate_drift": broad_covariate_drift,
                "coverage_drift": coverage_drift,
                "ranking_collapse": ranking_collapse,
                "outcome_collapse": outcome_collapse,
                "within_stratum_deterioration": within_deterioration,
            },
            "severe_feature_count": int(len(severe)),
            "top_drift_features": [
                {
                    "feature": row.feature,
                    "psi": float(row.psi),
                    "absolute_smd": float(row.absolute_smd),
                    "severity": row.severity,
                }
                for row in top_features.itertuples(index=False)
            ],
            "categorical_drift": category_summary,
            "score_and_outcome": {
                "reference_selected_fraction": float(score.reference_selected_fraction),
                "current_selected_fraction": float(score.current_selected_fraction),
                "score_psi": float(score.score_psi),
                "reference_auc": float(score.reference_auc),
                "current_auc": float(score.current_auc),
                "reference_selected_mean_r": float(score.reference_selected_mean_r),
                "current_selected_mean_r": float(score.current_selected_mean_r),
                "reference_selected_profit_factor": float(
                    score.reference_selected_profit_factor
                ),
                "current_selected_profit_factor": float(
                    score.current_selected_profit_factor
                ),
                "selected_win_rate_delta": float(score.selected_win_rate_delta),
            },
            "decomposition": decomposition_summary,
        }
    return {
        "schema_version": config["schema_version"],
        "decision": "F2026_DRIFT_AUDIT_COMPLETE_NO_RUNTIME_AUTHORIZATION",
        "target_fold": config["target_fold"],
        "lanes": lane_findings,
        "historical_outcomes_already_exposed": True,
        "runtime_changed": False,
        "authorization": config["authorization"],
    }
