from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_session(hour: int, sessions: Sequence[Mapping[str, Any]]) -> str:
    for spec in sessions:
        if int(spec["start_hour_inclusive"]) <= hour < int(spec["end_hour_exclusive"]):
            return str(spec["name"])
    raise ValueError(f"UTC hour is outside the locked session map: {hour}")


def validate_feature_contract(
    frame: pd.DataFrame, config: Mapping[str, Any]
) -> list[str]:
    features = list(config["features"])
    if len(features) != len(set(features)):
        raise ValueError("Feature contract contains duplicates")
    missing = sorted(set(features).difference(frame.columns))
    if missing:
        raise ValueError(f"Feature contract columns are missing: {missing}")
    forbidden = set(config["forbidden_features"])
    overlap = sorted(forbidden.intersection(features))
    if overlap:
        raise ValueError(f"Feature contract includes forbidden columns: {overlap}")
    if any(feature.startswith(("gc_", "comex_")) for feature in features):
        raise ValueError("COMEX features are prohibited")
    for feature in features:
        if not pd.api.types.is_numeric_dtype(frame[feature]):
            raise ValueError(f"Diagnostic feature is not numeric: {feature}")
    return features


def prepare_population(
    dataset: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    expected = config["expected"]
    if len(dataset) != int(expected["canonical_rows"]):
        raise ValueError("Canonical row count changed")
    if dataset["candidate_id"].duplicated().any():
        raise ValueError("Canonical candidate IDs are duplicated")
    winners = int(dataset["stress_net_r_positive"].sum())
    if winners != int(expected["stressed_winners"]):
        raise ValueError("Canonical winner count changed")
    if len(dataset) - winners != int(expected["stressed_failures"]):
        raise ValueError("Canonical failure count changed")
    accepted = int(dataset["historical_portfolio_accepted"].sum())
    if accepted != int(expected["historically_accepted"]):
        raise ValueError("Historical acceptance count changed")

    families = set(config["population"]["families"])
    observed = set(dataset["family_id"].unique())
    if observed != families:
        raise ValueError(
            f"Canonical family set changed: expected={sorted(families)} "
            f"observed={sorted(observed)}"
        )
    result = dataset.loc[
        dataset["xau_feature_status"].eq(
            config["population"]["required_xau_feature_status"]
        )
        & dataset["label_status"].str.startswith("RESOLVED_")
    ].copy()
    result["decision_time"] = pd.to_datetime(
        result["decision_time"], utc=True, errors="raise"
    )
    result["calendar_year"] = result["decision_time"].dt.year.astype(int)
    sessions = config["matching"]["sessions"]
    result["utc_session"] = result["decision_time"].dt.hour.map(
        lambda value: utc_session(int(value), sessions)
    )
    result["outcome"] = np.where(result["stress_net_r_positive"], "WINNER", "FAILURE")
    return result.sort_values(
        ["decision_time", "family_id", "candidate_id"], kind="stable"
    ).reset_index(drop=True)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.average(values, weights=weights))


def _weighted_variance(values: np.ndarray, weights: np.ndarray, mean: float) -> float:
    return float(np.average(np.square(values - mean), weights=weights))


def weighted_smd(frame: pd.DataFrame, feature: str) -> dict[str, float | int | None]:
    local = frame.loc[
        frame[feature].notna()
        & np.isfinite(frame[feature].to_numpy(dtype=float, na_value=np.nan))
    ].copy()
    winners = local.loc[local["stress_net_r_positive"]]
    failures = local.loc[~local["stress_net_r_positive"]]
    result: dict[str, float | int | None] = {
        "valid_rows": int(len(local)),
        "winner_rows": int(len(winners)),
        "failure_rows": int(len(failures)),
        "winner_mean": None,
        "failure_mean": None,
        "pooled_standard_deviation": None,
        "weighted_smd": None,
    }
    if winners.empty or failures.empty:
        return result
    winner_values = winners[feature].to_numpy(dtype=float)
    failure_values = failures[feature].to_numpy(dtype=float)
    winner_weights = winners["structural_weight"].to_numpy(dtype=float)
    failure_weights = failures["structural_weight"].to_numpy(dtype=float)
    winner_mean = _weighted_mean(winner_values, winner_weights)
    failure_mean = _weighted_mean(failure_values, failure_weights)
    winner_variance = _weighted_variance(winner_values, winner_weights, winner_mean)
    failure_variance = _weighted_variance(failure_values, failure_weights, failure_mean)
    pooled = float(np.sqrt((winner_variance + failure_variance) / 2.0))
    smd = (winner_mean - failure_mean) / pooled if pooled > 1e-12 else 0.0
    result.update(
        {
            "winner_mean": winner_mean,
            "failure_mean": failure_mean,
            "pooled_standard_deviation": pooled,
            "weighted_smd": float(smd),
        }
    )
    return result


def _portfolio_metrics(frame: pd.DataFrame) -> dict[str, float | int | None]:
    weights = frame["structural_weight"].to_numpy(dtype=float)
    outcomes = frame["stress_net_r"].to_numpy(dtype=float)
    weighted = outcomes * weights
    gains = float(weighted[weighted > 0].sum())
    losses = float(-weighted[weighted < 0].sum())
    return {
        "rows": int(len(frame)),
        "structural_episodes": int(frame["structural_episode_id"].nunique()),
        "winners": int(frame["stress_net_r_positive"].sum()),
        "failures": int((~frame["stress_net_r_positive"]).sum()),
        "weighted_mean_stress_r": (
            float(weighted.sum() / weights.sum()) if weights.sum() else None
        ),
        "weighted_profit_factor": (float(gains / losses) if losses > 0 else None),
    }


def build_family_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family_id, local in frame.groupby("family_id", sort=True, observed=True):
        rows.append(
            {
                "family_id": family_id,
                **_portfolio_metrics(local),
                "historically_accepted": int(
                    local["historical_portfolio_accepted"].sum()
                ),
                "start_time": local["decision_time"].min(),
                "end_time": local["decision_time"].max(),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("family_id", kind="stable")
        .reset_index(drop=True)
    )


def build_cohort_summary(
    frame: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    population = config["population"]
    accepted = frame["historical_portfolio_accepted"]
    cohorts = {
        "ALL_CAUSAL_FEATURE_PASS": frame,
        "V59_CORE_ACCEPTED": frame.loc[
            accepted & frame["family_id"].isin(population["v59_core_families"])
        ],
        "V59_ADDON_ACCEPTED": frame.loc[
            accepted & frame["family_id"].isin(population["v59_addon_families"])
        ],
        "HISTORICALLY_REJECTED": frame.loc[~accepted],
    }
    rows = [
        {"cohort_id": name, **_portfolio_metrics(local)}
        for name, local in cohorts.items()
    ]
    result = pd.DataFrame(rows)
    expected = config["expected"]
    observed_core = int(
        result.loc[result["cohort_id"].eq("V59_CORE_ACCEPTED"), "rows"].iloc[0]
    )
    observed_addon = int(
        result.loc[result["cohort_id"].eq("V59_ADDON_ACCEPTED"), "rows"].iloc[0]
    )
    # Feature-PASS rows can be fewer than accepted V59 rows. Reconcile against
    # the complete canonical population separately in run_diagnostic.
    result["canonical_expected_rows"] = result["cohort_id"].map(
        {
            "V59_CORE_ACCEPTED": int(expected["v59_core_accepted"]),
            "V59_ADDON_ACCEPTED": int(expected["v59_addon_accepted"]),
        }
    )
    result["feature_pass_rows_missing"] = (
        result["canonical_expected_rows"] - result["rows"]
    )
    if observed_core <= 0 or observed_addon <= 0:
        raise ValueError("V59 feature-PASS cohorts are empty")
    return result


def _representative_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.sort_values(
            [
                "family_id",
                "direction",
                "structural_episode_id",
                "structural_weight",
                "candidate_id",
            ],
            ascending=[True, True, True, False, True],
            kind="stable",
        )
        .drop_duplicates(
            ["family_id", "direction", "structural_episode_id"], keep="first"
        )
        .reset_index(drop=True)
    )


def _greedy_time_pairs(
    winners: pd.DataFrame, failures: pd.DataFrame
) -> list[tuple[pd.Series, pd.Series, float]]:
    candidates: list[tuple[int, str, str, int, int]] = []
    winner_rows = list(winners.itertuples(index=False))
    failure_rows = list(failures.itertuples(index=False))
    for winner_index, winner in enumerate(winner_rows):
        winner_ns = int(pd.Timestamp(winner.decision_time).value)
        for failure_index, failure in enumerate(failure_rows):
            failure_ns = int(pd.Timestamp(failure.decision_time).value)
            candidates.append(
                (
                    abs(winner_ns - failure_ns),
                    str(winner.candidate_id),
                    str(failure.candidate_id),
                    winner_index,
                    failure_index,
                )
            )
    candidates.sort()
    used_winners: set[int] = set()
    used_failures: set[int] = set()
    pairs: list[tuple[pd.Series, pd.Series, float]] = []
    target = min(len(winner_rows), len(failure_rows))
    winner_columns = list(winners.columns)
    failure_columns = list(failures.columns)
    for distance_ns, _, _, winner_index, failure_index in candidates:
        if winner_index in used_winners or failure_index in used_failures:
            continue
        used_winners.add(winner_index)
        used_failures.add(failure_index)
        pairs.append(
            (
                pd.Series(winner_rows[winner_index]._asdict())[winner_columns],
                pd.Series(failure_rows[failure_index]._asdict())[failure_columns],
                distance_ns / 3_600_000_000_000.0,
            )
        )
        if len(pairs) == target:
            break
    return pairs


def build_matched_pairs(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    representatives = _representative_rows(frame)
    strata = list(config["matching"]["exact_strata"])
    rows: list[dict[str, Any]] = []
    pair_number = 0
    for keys, local in representatives.groupby(
        strata, sort=True, observed=True, dropna=False
    ):
        winners = local.loc[local["stress_net_r_positive"]].sort_values(
            ["decision_time", "candidate_id"], kind="stable"
        )
        failures = local.loc[~local["stress_net_r_positive"]].sort_values(
            ["decision_time", "candidate_id"], kind="stable"
        )
        if winners.empty or failures.empty:
            continue
        key_values = keys if isinstance(keys, tuple) else (keys,)
        stratum = dict(zip(strata, key_values, strict=True))
        for winner, failure, distance_hours in _greedy_time_pairs(winners, failures):
            pair_number += 1
            pair_time = min(winner["decision_time"], failure["decision_time"])
            pair_week = pair_time.normalize() - pd.Timedelta(days=pair_time.weekday())
            rows.append(
                {
                    "pair_id": f"PAIR_{pair_number:06d}",
                    **stratum,
                    "winner_candidate_id": winner["candidate_id"],
                    "failure_candidate_id": failure["candidate_id"],
                    "winner_structural_episode_id": winner["structural_episode_id"],
                    "failure_structural_episode_id": failure["structural_episode_id"],
                    "winner_time": winner["decision_time"],
                    "failure_time": failure["decision_time"],
                    "distance_hours": float(distance_hours),
                    "pair_week": pair_week,
                }
            )
    if not rows:
        raise ValueError("Matched comparison produced no winner/failure pairs")
    result = pd.DataFrame(rows)
    if result["winner_candidate_id"].duplicated().any():
        raise ValueError("A winner was reused across matched pairs")
    if result["failure_candidate_id"].duplicated().any():
        raise ValueError("A failure was reused across matched pairs")
    if (
        result["winner_structural_episode_id"]
        .eq(result["failure_structural_episode_id"])
        .any()
    ):
        raise ValueError("A matched pair uses the same structural episode twice")
    return result.sort_values(
        ["family_id", "winner_time", "pair_id"], kind="stable"
    ).reset_index(drop=True)


def _stable_seed(base_seed: int, family_id: str, feature: str) -> int:
    payload = f"{base_seed}|{family_id}|{feature}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def _block_bootstrap_mean(
    values: np.ndarray,
    blocks: np.ndarray,
    *,
    resamples: int,
    confidence: float,
    seed: int,
) -> tuple[float | None, float | None]:
    unique_blocks = np.unique(blocks)
    if len(unique_blocks) < 2 or len(values) < 2:
        return None, None
    block_sums = np.asarray(
        [values[blocks == block].sum() for block in unique_blocks], dtype=float
    )
    block_counts = np.asarray(
        [(blocks == block).sum() for block in unique_blocks], dtype=float
    )
    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, len(unique_blocks), size=(resamples, len(unique_blocks)))
    estimates = block_sums[sampled].sum(axis=1) / block_counts[sampled].sum(axis=1)
    alpha = (1.0 - confidence) / 2.0
    return (
        float(np.quantile(estimates, alpha)),
        float(np.quantile(estimates, 1.0 - alpha)),
    )


def descriptive_and_matched_diagnostics(
    frame: pd.DataFrame,
    pairs: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    features = list(config["features"])
    lookup = frame.set_index("candidate_id", verify_integrity=True)
    bootstrap = config["bootstrap"]
    recent_start = pd.Timestamp(config["lead_gates"]["recent_start_utc"])
    rows: list[dict[str, Any]] = []
    for family_id in config["population"]["families"]:
        local = frame.loc[frame["family_id"].eq(family_id)]
        local_pairs = pairs.loc[pairs["family_id"].eq(family_id)]
        for feature in features:
            overall = weighted_smd(local, feature)
            recent = weighted_smd(
                local.loc[local["decision_time"].ge(recent_start)], feature
            )
            winner_values = lookup.loc[
                local_pairs["winner_candidate_id"], feature
            ].to_numpy(dtype=float)
            failure_values = lookup.loc[
                local_pairs["failure_candidate_id"], feature
            ].to_numpy(dtype=float)
            valid = np.isfinite(winner_values) & np.isfinite(failure_values)
            raw_difference = winner_values[valid] - failure_values[valid]
            pooled = overall["pooled_standard_deviation"]
            if pooled is not None and float(pooled) > 1e-12:
                standardized = raw_difference / float(pooled)
            else:
                standardized = np.zeros(len(raw_difference), dtype=float)
            blocks = (
                local_pairs.loc[valid, "pair_week"]
                .astype("int64")
                .to_numpy(dtype=np.int64)
            )
            ci_lower, ci_upper = _block_bootstrap_mean(
                standardized,
                blocks,
                resamples=int(bootstrap["resamples"]),
                confidence=float(bootstrap["confidence"]),
                seed=_stable_seed(int(bootstrap["seed"]), str(family_id), str(feature)),
            )
            rows.append(
                {
                    "family_id": family_id,
                    "feature": feature,
                    "family_rows": int(len(local)),
                    "family_winners": int(local["stress_net_r_positive"].sum()),
                    "family_failures": int((~local["stress_net_r_positive"]).sum()),
                    "missing_fraction": float(1.0 - overall["valid_rows"] / len(local)),
                    **{f"overall_{key}": value for key, value in overall.items()},
                    **{f"recent_{key}": value for key, value in recent.items()},
                    "matched_pairs": int(valid.sum()),
                    "matched_mean_standardized_difference": (
                        float(np.mean(standardized)) if len(standardized) else None
                    ),
                    "matched_median_standardized_difference": (
                        float(np.median(standardized)) if len(standardized) else None
                    ),
                    "matched_winner_higher_fraction": (
                        float(np.mean(raw_difference > 0))
                        if len(raw_difference)
                        else None
                    ),
                    "matched_ci_lower": ci_lower,
                    "matched_ci_upper": ci_upper,
                }
            )
    return pd.DataFrame(rows)


def walk_forward_feature_transfer(
    frame: pd.DataFrame,
    splits: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_columns = [
        "fold_id",
        "candidate_id",
        "assignment",
        "resolved_label",
        "dataset_eligible",
    ]
    if splits.duplicated(["fold_id", "candidate_id"]).any():
        raise ValueError("Split assignments contain duplicate fold/candidate rows")
    joined = splits[split_columns].merge(
        frame, on="candidate_id", how="inner", validate="many_to_one"
    )
    joined = joined.loc[joined["resolved_label"] & joined["dataset_eligible"]]
    spec = config["walk_forward"]
    fold_rows: list[dict[str, Any]] = []
    prediction_rows: list[pd.DataFrame] = []
    for family_id in config["population"]["families"]:
        family = joined.loc[joined["family_id"].eq(family_id)]
        for feature in config["features"]:
            for fold_id in spec["folds"]:
                local = family.loc[family["fold_id"].eq(fold_id)]
                fit = local.loc[
                    local["assignment"].eq("FIT") & local[feature].notna()
                ].copy()
                test = local.loc[
                    local["assignment"].eq("TEST") & local[feature].notna()
                ].copy()
                fit_class = fit["stress_net_r_positive"].value_counts()
                test_class = test["stress_net_r_positive"].value_counts()
                eligible = (
                    len(fit) >= int(spec["minimum_fit_rows"])
                    and int(fit_class.get(True, 0))
                    >= int(spec["minimum_fit_rows_per_class"])
                    and int(fit_class.get(False, 0))
                    >= int(spec["minimum_fit_rows_per_class"])
                    and len(test) >= int(spec["minimum_test_rows"])
                    and int(test_class.get(True, 0))
                    >= int(spec["minimum_test_rows_per_class"])
                    and int(test_class.get(False, 0))
                    >= int(spec["minimum_test_rows_per_class"])
                )
                row: dict[str, Any] = {
                    "family_id": family_id,
                    "feature": feature,
                    "fold_id": fold_id,
                    "fit_rows": int(len(fit)),
                    "fit_winners": int(fit_class.get(True, 0)),
                    "fit_failures": int(fit_class.get(False, 0)),
                    "test_rows": int(len(test)),
                    "test_winners": int(test_class.get(True, 0)),
                    "test_failures": int(test_class.get(False, 0)),
                    "eligible": bool(eligible),
                    "fit_direction": None,
                    "test_auc": None,
                }
                if eligible:
                    fit_effect = weighted_smd(fit, feature)
                    smd = float(fit_effect["weighted_smd"] or 0.0)
                    direction = 1.0 if smd >= 0.0 else -1.0
                    fit_values = fit[feature].to_numpy(dtype=float)
                    fit_weights = fit["structural_weight"].to_numpy(dtype=float)
                    location = _weighted_mean(fit_values, fit_weights)
                    variance = _weighted_variance(fit_values, fit_weights, location)
                    scale = float(np.sqrt(variance))
                    if scale <= 1e-12:
                        eligible = False
                        row["eligible"] = False
                    else:
                        test = test.copy()
                        test["signed_score"] = (
                            direction
                            * (test[feature].to_numpy(dtype=float) - location)
                            / scale
                        )
                        auc = roc_auc_score(
                            test["stress_net_r_positive"].astype(int),
                            test["signed_score"],
                            sample_weight=test["structural_weight"],
                        )
                        row["fit_direction"] = (
                            "WINNERS_HIGHER" if direction > 0 else "WINNERS_LOWER"
                        )
                        row["test_auc"] = float(auc)
                        prediction_rows.append(
                            test[
                                [
                                    "candidate_id",
                                    "structural_weight",
                                    "stress_net_r_positive",
                                    "signed_score",
                                ]
                            ].assign(
                                family_id=family_id,
                                feature=feature,
                                fold_id=fold_id,
                            )
                        )
                fold_rows.append(row)
    folds = pd.DataFrame(fold_rows)
    predictions = (
        pd.concat(prediction_rows, ignore_index=True)
        if prediction_rows
        else pd.DataFrame()
    )
    summary_rows: list[dict[str, Any]] = []
    for (family_id, feature), local_folds in folds.groupby(
        ["family_id", "feature"], sort=True, observed=True
    ):
        eligible_folds = local_folds.loc[local_folds["eligible"]]
        local_predictions = predictions.loc[
            predictions["family_id"].eq(family_id) & predictions["feature"].eq(feature)
        ]
        aggregate_auc = None
        if (
            not local_predictions.empty
            and local_predictions["stress_net_r_positive"].nunique() == 2
        ):
            aggregate_auc = float(
                roc_auc_score(
                    local_predictions["stress_net_r_positive"].astype(int),
                    local_predictions["signed_score"],
                    sample_weight=local_predictions["structural_weight"],
                )
            )
        latest_auc = (
            float(eligible_folds.iloc[-1]["test_auc"])
            if not eligible_folds.empty
            else None
        )
        summary_rows.append(
            {
                "family_id": family_id,
                "feature": feature,
                "walk_forward_folds": int(len(eligible_folds)),
                "walk_forward_test_rows": int(len(local_predictions)),
                "walk_forward_auc": aggregate_auc,
                "positive_fold_fraction": (
                    float(eligible_folds["test_auc"].gt(0.5).mean())
                    if not eligible_folds.empty
                    else None
                ),
                "latest_eligible_fold": (
                    str(eligible_folds.iloc[-1]["fold_id"])
                    if not eligible_folds.empty
                    else None
                ),
                "latest_fold_auc": latest_auc,
                "fit_direction_consistency": (
                    float(
                        eligible_folds["fit_direction"]
                        .value_counts(normalize=True)
                        .max()
                    )
                    if not eligible_folds.empty
                    else None
                ),
            }
        )
    return folds, pd.DataFrame(summary_rows)


def apply_lead_gates(
    diagnostics: pd.DataFrame,
    walk_forward: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = diagnostics.merge(
        walk_forward,
        on=["family_id", "feature"],
        how="left",
        validate="one_to_one",
    )
    gates = config["lead_gates"]
    check_rows: list[dict[str, Any]] = []
    statuses: list[str] = []
    for row in merged.itertuples(index=False):
        overall_smd = row.overall_weighted_smd
        recent_smd = row.recent_weighted_smd
        matched_mean = row.matched_mean_standardized_difference
        matched_ci_excludes = (
            row.matched_ci_lower is not None
            and row.matched_ci_upper is not None
            and (float(row.matched_ci_lower) > 0.0 or float(row.matched_ci_upper) < 0.0)
        )
        descriptive_match_agree = (
            overall_smd is not None
            and matched_mean is not None
            and np.sign(float(overall_smd)) == np.sign(float(matched_mean))
            and np.sign(float(overall_smd)) != 0
        )
        recent_available = (
            int(row.recent_winner_rows) >= int(gates["minimum_recent_rows_per_class"])
            and int(row.recent_failure_rows)
            >= int(gates["minimum_recent_rows_per_class"])
            and recent_smd is not None
        )
        recent_agree = (
            recent_available
            and overall_smd is not None
            and np.sign(float(recent_smd)) == np.sign(float(overall_smd))
            and np.sign(float(overall_smd)) != 0
        )
        checks = {
            "family_rows": int(row.family_rows) >= int(gates["minimum_family_rows"]),
            "family_classes": min(int(row.family_winners), int(row.family_failures))
            >= int(gates["minimum_family_rows_per_class"]),
            "feature_coverage": float(row.missing_fraction)
            <= float(gates["maximum_feature_missing_fraction"]),
            "matched_pairs": int(row.matched_pairs)
            >= int(gates["minimum_matched_pairs"]),
            "descriptive_effect": overall_smd is not None
            and abs(float(overall_smd))
            >= float(gates["minimum_absolute_weighted_smd"]),
            "matched_ci": matched_ci_excludes,
            "matched_direction": descriptive_match_agree,
            "walk_forward_folds": int(row.walk_forward_folds or 0)
            >= int(gates["minimum_walk_forward_folds"]),
            "walk_forward_rows": int(row.walk_forward_test_rows or 0)
            >= int(gates["minimum_walk_forward_test_rows"]),
            "walk_forward_auc": row.walk_forward_auc is not None
            and float(row.walk_forward_auc) >= float(gates["minimum_walk_forward_auc"]),
            "positive_fold_fraction": row.positive_fold_fraction is not None
            and float(row.positive_fold_fraction)
            >= float(gates["minimum_positive_fold_fraction"]),
            "latest_fold_auc": row.latest_fold_auc is not None
            and float(row.latest_fold_auc) >= float(gates["minimum_latest_fold_auc"]),
            "recent_direction": recent_agree,
        }
        passed = sum(checks.values())
        if passed == len(checks):
            status = "STABLE_EXPLORATORY_LEAD"
        elif passed >= len(checks) - 2:
            status = "NEAR_LEAD_REQUIRES_MORE_EVIDENCE"
        else:
            status = "NO_STABLE_SEPARATOR"
        statuses.append(status)
        for check, value in checks.items():
            check_rows.append(
                {
                    "family_id": row.family_id,
                    "feature": row.feature,
                    "check": check,
                    "passed": bool(value),
                }
            )
    merged["status"] = statuses
    return merged, pd.DataFrame(check_rows)


def _markdown(
    result: Mapping[str, Any],
    family_summary: pd.DataFrame,
    diagnostics: pd.DataFrame,
) -> str:
    lines = [
        "# Causal Specialist Winner/Loser Diagnostic V1",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Historical outcomes were already exposed. Any lead below is exploratory "
        "and requires prospective confirmation.",
        "",
        "## Specialist Evidence",
        "",
        "| Family | Rows | Winners | Failures | Mean stress R | PF | Matched pairs | Stable leads | Near leads |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    pair_counts = result["matched_pairs_by_family"]
    lead_counts = result["stable_leads_by_family"]
    near_counts = result["near_leads_by_family"]
    for row in family_summary.itertuples(index=False):
        pf = (
            f"{float(row.weighted_profit_factor):.3f}"
            if row.weighted_profit_factor is not None
            else "n/a"
        )
        lines.append(
            f"| {row.family_id} | {row.rows} | {row.winners} | {row.failures} | "
            f"{float(row.weighted_mean_stress_r):.4f} | {pf} | "
            f"{pair_counts.get(row.family_id, 0)} | "
            f"{lead_counts.get(row.family_id, 0)} | "
            f"{near_counts.get(row.family_id, 0)} |"
        )
    ranked = diagnostics.assign(
        status_order=diagnostics["status"].map(
            {
                "STABLE_EXPLORATORY_LEAD": 0,
                "NEAR_LEAD_REQUIRES_MORE_EVIDENCE": 1,
                "NO_STABLE_SEPARATOR": 2,
            }
        )
    ).sort_values(
        [
            "status_order",
            "walk_forward_auc",
            "matched_pairs",
            "family_id",
            "feature",
        ],
        ascending=[True, False, False, True, True],
        kind="stable",
        na_position="last",
    )
    visible = ranked.loc[
        ranked["status"].isin(
            ["STABLE_EXPLORATORY_LEAD", "NEAR_LEAD_REQUIRES_MORE_EVIDENCE"]
        )
    ].head(20)
    lines.extend(
        [
            "",
            "## Best Feature Leads",
            "",
            "| Family | Feature | Status | WF folds | WF rows | WF AUC | SMD | Matched pairs | Matched delta | 95% CI |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    if visible.empty:
        lines.append(
            "| none | none | NO_STABLE_SEPARATOR | 0 | 0 | n/a | n/a | 0 | n/a | n/a |"
        )
    else:
        for row in visible.itertuples(index=False):
            auc = (
                f"{float(row.walk_forward_auc):.4f}"
                if row.walk_forward_auc is not None
                else "n/a"
            )
            ci = (
                f"[{float(row.matched_ci_lower):.3f}, "
                f"{float(row.matched_ci_upper):.3f}]"
                if row.matched_ci_lower is not None and row.matched_ci_upper is not None
                else "n/a"
            )
            lines.append(
                f"| {row.family_id} | {row.feature} | {row.status} | "
                f"{int(row.walk_forward_folds)} | "
                f"{int(row.walk_forward_test_rows)} | {auc} | "
                f"{float(row.overall_weighted_smd):.3f} | "
                f"{int(row.matched_pairs)} | "
                f"{float(row.matched_mean_standardized_difference):.3f} | "
                f"{ci} |"
            )
    lines.extend(
        [
            "",
            "No model, threshold, portfolio, MT5, demo, live, or broker action was "
            "created by this analysis.",
            "",
        ]
    )
    return "\n".join(lines)


def run_diagnostic(
    repo_root: Path,
    package_root: Path,
    config_path: Path,
    output_dir: Path,
    *,
    verify_bound_file: Any,
    stable_parquet: Any,
    write_json: Any,
) -> dict[str, Any]:
    config = load_json(config_path)
    controls = config["controls"]
    required_false = [
        "model_training_authorized",
        "threshold_fitting_authorized",
        "portfolio_simulation_authorized",
        "runtime_change_authorized",
        "ml_shadow_or_execution_authorized",
        "databento_api_access_authorized",
        "new_data_acquisition_authorized",
        "comex_features_authorized",
    ]
    if any(bool(controls[name]) for name in required_false):
        raise ValueError("Diagnostic controls do not fail closed")
    bound = {
        name: verify_bound_file(repo_root, spec, name)
        for name, spec in config["bound_inputs"].items()
    }
    dataset = pd.read_parquet(bound["step_3_dataset"])
    splits = pd.read_parquet(bound["step_3_splits"])
    features = validate_feature_contract(dataset, config)
    frame = prepare_population(dataset, config)

    complete_core = int(
        (
            dataset["historical_portfolio_accepted"]
            & dataset["family_id"].isin(config["population"]["v59_core_families"])
        ).sum()
    )
    complete_addon = int(
        (
            dataset["historical_portfolio_accepted"]
            & dataset["family_id"].isin(config["population"]["v59_addon_families"])
        ).sum()
    )
    if complete_core != int(config["expected"]["v59_core_accepted"]):
        raise ValueError("V59 core acceptance reconciliation changed")
    if complete_addon != int(config["expected"]["v59_addon_accepted"]):
        raise ValueError("V59 add-on acceptance reconciliation changed")

    family_summary = build_family_summary(frame)
    cohort_summary = build_cohort_summary(frame, config)
    pairs = build_matched_pairs(frame, config)
    diagnostics = descriptive_and_matched_diagnostics(frame, pairs, config)
    fold_rows, walk_forward = walk_forward_feature_transfer(frame, splits, config)
    diagnostics, lead_checks = apply_lead_gates(diagnostics, walk_forward, config)
    stable = diagnostics.loc[diagnostics["status"].eq("STABLE_EXPLORATORY_LEAD")]
    near = diagnostics.loc[diagnostics["status"].eq("NEAR_LEAD_REQUIRES_MORE_EVIDENCE")]
    decision = (
        "STABLE_EXPLORATORY_SEPARATOR_LEADS_FOUND_REQUIRES_PROSPECTIVE_CONFIRMATION"
        if not stable.empty
        else "NO_STABLE_UNIVARIATE_SEPARATOR_FOUND"
    )
    matched_counts = pairs.groupby("family_id").size().astype(int).to_dict()
    stable_counts = stable.groupby("family_id").size().astype(int).to_dict()
    near_counts = near.groupby("family_id").size().astype(int).to_dict()
    result: dict[str, Any] = {
        "schema_version": "xauusd_causal_specialist_win_loss_result_v1",
        "decision": decision,
        "canonical_rows": int(len(dataset)),
        "feature_pass_rows": int(len(frame)),
        "features_tested": int(len(features)),
        "families_tested": int(frame["family_id"].nunique()),
        "matched_pairs": int(len(pairs)),
        "matched_pairs_by_family": matched_counts,
        "stable_leads": int(len(stable)),
        "stable_leads_by_family": stable_counts,
        "near_leads": int(len(near)),
        "near_leads_by_family": near_counts,
        "priority_family_leads": stable.loc[
            stable["family_id"].isin(config["population"]["priority_families"]),
            ["family_id", "feature", "walk_forward_auc"],
        ].to_dict(orient="records"),
        "historical_outcomes_already_exposed": True,
        "development_only": True,
        "model_trained": False,
        "threshold_fitted": False,
        "runtime_changed": False,
        "ml_authorized": False,
        "next_action": (
            "PREREGISTER_PROSPECTIVE_FEATURE_CONFIRMATION"
            if not stable.empty
            else "ADD_NEW_CAUSAL_INFORMATION_OR_COLLECT_MORE_SPECIALIST_OUTCOMES"
        ),
    }
    outputs = config["outputs"]
    output_dir.mkdir(parents=True, exist_ok=True)
    stable_parquet(family_summary, output_dir / outputs["family_summary"])
    stable_parquet(cohort_summary, output_dir / outputs["cohort_summary"])
    stable_parquet(pairs, output_dir / outputs["matched_pairs"])
    stable_parquet(
        diagnostics.sort_values(["family_id", "feature"], kind="stable"),
        output_dir / outputs["feature_diagnostics"],
    )
    stable_parquet(
        fold_rows.sort_values(["family_id", "feature", "fold_id"], kind="stable"),
        output_dir / outputs["walk_forward_folds"],
    )
    stable_parquet(
        lead_checks.sort_values(["family_id", "feature", "check"], kind="stable"),
        output_dir / outputs["lead_checks"],
    )
    write_json(output_dir / outputs["result_json"], result)
    (output_dir / outputs["result_markdown"]).write_text(
        _markdown(result, family_summary, diagnostics),
        encoding="utf-8",
    )
    return result
