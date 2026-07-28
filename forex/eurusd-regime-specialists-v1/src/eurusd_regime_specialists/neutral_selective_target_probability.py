from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .ensemble import load_ensemble_config, load_inputs
from .neutral_binance_eurusdt_flow import evaluate_oracle
from .neutral_four_clock_ranker import route_predictions
from .neutral_midnight_pairs import aggregate_days, write_json
from .neutral_selective_multivenue_agreement import (
    admission,
    load_parent_decisions,
    summarize_selective,
)
from .research import PACKAGE_ROOT, serialize, sha256_file


FAMILY = "N26_NEUTRAL_SELECTIVE_TARGET_PROBABILITY"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_selective_target_probability"
)
TRAINING_WINDOW = "training_2020_2021"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_selective_target_probability.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_SELECTIVE_TARGET_PROBABILITY_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get(
            "locked_before_selective_target_probability_outcome_pass"
        )
        is not True
    ):
        raise RuntimeError(
            "Neutral selective target probability is not locked"
        )
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral selective target-probability lock mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_multivenue_contract"]
    if sha256_file(PACKAGE_ROOT / parent["path"]) != parent["sha256"]:
        raise RuntimeError("Parent multivenue contract drift")
    if (
        sha256_file(PACKAGE_ROOT / parent["lock_path"])
        != parent["lock_sha256"]
    ):
        raise RuntimeError("Parent multivenue lock drift")
    if cfg["pre_evaluation_selection_census"] is None:
        raise RuntimeError("Pre-evaluation selection census is not frozen")
    return checked


def _census_sha256(census: dict[str, Any]) -> str:
    payload = json.dumps(
        serialize(census),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _side_rows(
    points: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    include_labels: bool,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    aligned = list(cfg["features"]["side_aligned_columns"])
    for side, suffix, sign in (
        ("LONG", "long", 1.0),
        ("SHORT", "short", -1.0),
    ):
        frame = pd.DataFrame(
            {
                "decision_id": points["decision_id"].to_numpy(),
                "entry_time_utc": points["entry_time_utc"].to_numpy(),
                "side": side,
            }
        )
        for feature in aligned:
            frame[feature] = points[
                f"{feature}_{suffix}"
            ].to_numpy()
        kraken = points[
            "kraken_reported_side_imbalance_15m"
        ].astype(float)
        binance = points["binance_taker_imbalance_15m"].astype(float)
        frame["aligned_kraken_side_imbalance"] = (
            sign * kraken.to_numpy()
        )
        frame["aligned_binance_taker_imbalance"] = (
            sign * binance.to_numpy()
        )
        frame["kraken_imbalance_magnitude"] = (
            kraken.abs().to_numpy()
        )
        frame["binance_imbalance_magnitude"] = (
            binance.abs().to_numpy()
        )
        if include_labels:
            frame["target_first"] = points[
                f"target_first_{suffix}"
            ].astype(bool).to_numpy()
            frame["label_known_time_utc"] = points[
                f"exit_time_utc_{suffix}"
            ].to_numpy()
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def _model_columns(cfg: dict[str, Any]) -> list[str]:
    columns = [
        *cfg["features"]["side_aligned_columns"],
        *cfg["features"]["derived_flow_columns"],
    ]
    if len(columns) != int(cfg["features"]["model_column_count"]):
        raise RuntimeError("Frozen target-probability feature count drift")
    return columns


def fit_and_score(
    points: pd.DataFrame,
    inference: pd.DataFrame,
    cutoff: pd.Timestamp,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    candidates = points[
        points["entry_time_utc"].lt(cutoff)
    ].copy()
    training = _side_rows(
        candidates, cfg, include_labels=True
    )
    training["label_known_time_utc"] = pd.to_datetime(
        training["label_known_time_utc"], utc=True
    )
    training = training[
        training["label_known_time_utc"].lt(cutoff)
    ].copy()
    minimum = int(cfg["model"]["minimum_training_side_rows"])
    if len(training) < minimum:
        raise RuntimeError(
            f"Insufficient purged side rows: {len(training)} < {minimum}"
        )
    columns = _model_columns(cfg)
    scaler = StandardScaler()
    train_x = scaler.fit_transform(training[columns])
    labels = training["target_first"].astype(int)
    if labels.nunique() != 2:
        raise RuntimeError("Target-probability fit requires both classes")
    model_cfg = cfg["model"]
    model = LogisticRegression(
        penalty=model_cfg["penalty"],
        C=float(model_cfg["C"]),
        solver=model_cfg["solver"],
        max_iter=int(model_cfg["max_iter"]),
        class_weight=model_cfg["class_weight"],
        random_state=int(model_cfg["random_state"]),
    )
    model.fit(train_x, labels)

    scoring = _side_rows(
        inference, cfg, include_labels=False
    )
    scoring["target_probability"] = model.predict_proba(
        scaler.transform(scoring[columns])
    )[:, 1]
    pivot = scoring.pivot(
        index="decision_id",
        columns="side",
        values="target_probability",
    ).rename(
        columns={
            "LONG": "model_probability_long",
            "SHORT": "model_probability_short",
        }
    )
    scored = inference.merge(
        pivot,
        left_on="decision_id",
        right_index=True,
        how="left",
        validate="one_to_one",
    )
    scored["model_selected_side"] = np.where(
        scored["model_probability_long"].ge(
            scored["model_probability_short"]
        ),
        "LONG",
        "SHORT",
    )
    scored["model_selection_probability"] = scored[
        ["model_probability_long", "model_probability_short"]
    ].max(axis=1)
    scored["model_probability_margin"] = (
        scored["model_probability_long"]
        - scored["model_probability_short"]
    ).abs()
    threshold = float(
        cfg["model"]["selection_probability_threshold"]
    )
    selected = scored[
        scored["model_selection_probability"].ge(threshold)
    ].copy()
    selected["flow_side"] = selected["model_selected_side"]

    coefficients = pd.DataFrame(
        {
            "feature": columns,
            "coefficient": model.coef_[0],
            "training_mean": scaler.mean_,
            "training_scale": scaler.scale_,
        }
    ).sort_values("coefficient", ascending=False)
    fit_metadata = {
        "cutoff_utc": cutoff,
        "training_side_rows": int(len(training)),
        "training_decision_points": int(
            training["decision_id"].nunique()
        ),
        "training_positive_side_rows": int(labels.sum()),
        "training_positive_rate": float(labels.mean()),
        "selected_decisions": int(len(selected)),
        "cash_decisions": int(len(scored) - len(selected)),
        "selection_probability": {
            "minimum": float(
                scored["model_selection_probability"].min()
            ),
            "median": float(
                scored["model_selection_probability"].median()
            ),
            "p90": float(
                scored["model_selection_probability"].quantile(0.90)
            ),
            "p95": float(
                scored["model_selection_probability"].quantile(0.95)
            ),
            "p99": float(
                scored["model_selection_probability"].quantile(0.99)
            ),
            "maximum": float(
                scored["model_selection_probability"].max()
            ),
        },
    }
    return selected, coefficients, {
        "scored": scored,
        "fit_metadata": fit_metadata,
    }


def _distribution(
    selected: pd.DataFrame,
    source_dates: pd.Index,
) -> dict[str, int]:
    counts = selected.groupby("eligible_date").size().reindex(
        source_dates, fill_value=0
    )
    return {
        str(value): int((counts == value).sum())
        for value in range(5)
    }


def _selection_block(
    source: pd.DataFrame,
    selected: pd.DataFrame,
) -> dict[str, Any]:
    source_dates = pd.Index(
        sorted(source["eligible_date"].astype(str).unique())
    )
    source_days = int(len(source_dates))
    active_days = int(selected["eligible_date"].nunique())
    trades = int(len(selected))
    return {
        "source_eligible_days": source_days,
        "source_decision_points": int(len(source)),
        "selected_candidates": trades,
        "active_candidate_days": active_days,
        "no_trade_days": source_days - active_days,
        "predicted_long_rate": (
            float(
                selected["model_selected_side"].eq("LONG").mean()
            )
            if trades
            else 0.0
        ),
        "trades_per_source_eligible_day": (
            trades / source_days if source_days else 0.0
        ),
        "trades_per_active_candidate_day": (
            trades / active_days if active_days else 0.0
        ),
        "candidate_count_distribution": _distribution(
            selected, source_dates
        ),
    }


def select_evaluation_points(
    points: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    selected_frames: list[pd.DataFrame] = []
    scored_frames: list[pd.DataFrame] = []
    coefficient_frames: list[pd.DataFrame] = []
    by_window: dict[str, Any] = {}
    fit_metadata: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg["windows"].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        inference = points[
            points["entry_time_utc"].between(
                start, end, inclusive="both"
            )
        ].copy()
        selected, coefficients, details = fit_and_score(
            points, inference, start, cfg
        )
        selected["window"] = name
        scored = details["scored"]
        scored["window"] = name
        coefficients["window"] = name
        by_window[name] = _selection_block(inference, selected)
        fit_metadata[name] = details["fit_metadata"]
        selected_frames.append(selected)
        scored_frames.append(scored)
        coefficient_frames.append(coefficients)
    selected_all = pd.concat(selected_frames, ignore_index=True)
    scored_all = pd.concat(scored_frames, ignore_index=True)
    coefficients_all = pd.concat(
        coefficient_frames, ignore_index=True
    )
    evaluation = points[
        points["entry_time_utc"].between(
            min(pd.Timestamp(v[0]) for v in cfg["windows"].values()),
            max(pd.Timestamp(v[1]) for v in cfg["windows"].values()),
            inclusive="both",
        )
    ]
    overall = _selection_block(evaluation, selected_all)
    overall_probability = {
        "minimum": float(
            scored_all["model_selection_probability"].min()
        ),
        "median": float(
            scored_all["model_selection_probability"].median()
        ),
        "p90": float(
            scored_all["model_selection_probability"].quantile(0.90)
        ),
        "p95": float(
            scored_all["model_selection_probability"].quantile(0.95)
        ),
        "p99": float(
            scored_all["model_selection_probability"].quantile(0.99)
        ),
        "maximum": float(
            scored_all["model_selection_probability"].max()
        ),
    }
    census = {
        "source_eligible_days": overall["source_eligible_days"],
        "source_decision_points": overall["source_decision_points"],
        "selected_candidates": overall["selected_candidates"],
        "active_candidate_days": overall["active_candidate_days"],
        "no_trade_days": overall["no_trade_days"],
        "predicted_long_rate": overall["predicted_long_rate"],
        "trades_per_source_eligible_day": overall[
            "trades_per_source_eligible_day"
        ],
        "trades_per_active_candidate_day": overall[
            "trades_per_active_candidate_day"
        ],
        "candidate_count_distribution": overall[
            "candidate_count_distribution"
        ],
        "selection_probability": overall_probability,
        "by_window": by_window,
        "fit_metadata": fit_metadata,
    }
    return (
        selected_all,
        scored_all,
        coefficients_all,
        census,
    )


def _summary_census(census: dict[str, Any]) -> dict[str, Any]:
    compatible = {
        **census,
        "agreement_candidates": census["selected_candidates"],
    }
    compatible["by_window"] = {
        name: {
            **block,
            "agreement_candidates": block["selected_candidates"],
        }
        for name, block in census["by_window"].items()
    }
    return compatible


def execute(
    selected: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    router_probabilities = np.where(
        selected["model_selected_side"].eq("LONG"), 1.0, 0.0
    )
    trades, predictions = route_predictions(
        selected, router_probabilities, cfg
    )
    trades["family"] = FAMILY
    predictions["family"] = FAMILY
    columns = [
        "model_probability_long",
        "model_probability_short",
        "model_selection_probability",
        "model_probability_margin",
        "model_selected_side",
    ]
    for column in columns:
        trades[column] = selected[column].to_numpy()
        predictions[column] = selected[column].to_numpy()
    return trades, predictions


def run_census() -> dict[str, Any]:
    cfg = load_config()
    points = load_parent_decisions(include_outcomes=True)
    _, _, _, census = select_evaluation_points(points, cfg)
    return census


def run_neutral_selective_target_probability() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    points = load_parent_decisions(include_outcomes=True)
    selected, scores, coefficients, census = (
        select_evaluation_points(points, cfg)
    )
    frozen_census = cfg["pre_evaluation_selection_census"]
    if _census_sha256(census) != frozen_census["sha256"]:
        raise RuntimeError(
            "Target-probability selection census drift: "
            f"actual_sha256={_census_sha256(census)!r} "
            f"frozen_sha256={frozen_census['sha256']!r}"
        )
    if selected.empty:
        safe_score_columns = [
            "decision_id",
            "eligible_date",
            "clock_minute",
            "entry_time_utc",
            "window",
            "model_probability_long",
            "model_probability_short",
            "model_selected_side",
            "model_selection_probability",
            "model_probability_margin",
        ]
        result = {
            "campaign_id": cfg["campaign_id"],
            "status": (
                "REJECTED_PRE_EVALUATION_NO_TARGET_PROBABILITY_SIGNALS"
            ),
            "information_status": cfg["information_status"],
            "parent_multivenue_contract": cfg[
                "parent_multivenue_contract"
            ],
            "causality": {
                "model": (
                    "shared side-stacked L2 logistic target-first "
                    "probability"
                ),
                "features": _model_columns(cfg),
                "selection_threshold": cfg["model"][
                    "selection_probability_threshold"
                ],
                "training_purge": (
                    "side entry and side exit strictly before each "
                    "evaluation-window start"
                ),
                "current_window_outcome_in_fit": False,
                "threshold_feature_or_hyperparameter_search": False,
                "trade_outcomes_routed": False,
                "oracle_evaluated": False,
            },
            "outcome_blind_source_census": cfg[
                "outcome_blind_source_census"
            ],
            "pre_evaluation_selection_census": census,
            "strategy": {
                "admitted": False,
                "selection_threshold": cfg["model"][
                    "selection_probability_threshold"
                ],
                "selected_trades": 0,
                "cash_decisions": int(len(scores)),
                "frequency_gate_relaxed": True,
                "economic_evaluation": (
                    "NOT_RUN_BECAUSE_NO_DECISION_CLEARED_THE_FROZEN_"
                    "PROBABILITY_HURDLE"
                ),
            },
            "prospective": {
                "start_utc": cfg["prospective"]["start_utc"],
                "status": "CANCELLED_BY_PRE_EVALUATION_NO_TRADE_GATE",
                "available_points_after_start": 0,
            },
            "verdict": (
                "No evaluation decision cleared the frozen 0.45 "
                "target-probability hurdle. The model remains CASH and "
                "the threshold will not be lowered after the screen."
            ),
        }
        return result, {
            "MODEL_SCORES_OUTCOME_BLIND": scores[safe_score_columns],
            "COEFFICIENTS": coefficients,
        }
    trades, predictions = execute(selected, cfg)
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    strategy = summarize_selective(
        trades,
        predictions,
        m5,
        cfg,
        _summary_census(census),
    )
    oracle, matches = evaluate_oracle(trades, cfg)
    admitted, checks = admission(strategy, oracle, cfg)
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    prospective_points = selected[
        selected["entry_time_utc"] >= prospective_start
    ]
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_SELECTIVE_TARGET_PROBABILITY_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "parent_multivenue_contract": cfg[
            "parent_multivenue_contract"
        ],
        "causality": {
            "model": (
                "shared side-stacked L2 logistic target-first "
                "probability"
            ),
            "features": _model_columns(cfg),
            "selection_threshold": cfg["model"][
                "selection_probability_threshold"
            ],
            "training_purge": (
                "side entry and side exit strictly before each "
                "evaluation-window start"
            ),
            "current_window_outcome_in_fit": False,
            "threshold_feature_or_hyperparameter_search": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "outcome_blind_source_census": cfg[
            "outcome_blind_source_census"
        ],
        "pre_evaluation_selection_census": census,
        "strategy": {
            "admitted": admitted,
            "admission_checks": checks,
            **strategy,
        },
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": cfg["prospective"]["start_utc"],
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": int(
                len(prospective_points)
            ),
            "status": (
                "WAITING_FOR_POST_LOCK_MARKET_DATA"
                if prospective_points.empty
                else "POST_LOCK_POINTS_AVAILABLE"
            ),
        },
        "verdict": (
            "The frozen selective probability rule passed every "
            "historical gate; only post-lock rows may confirm it."
            if admitted
            else "The frozen selective probability rule failed one or "
            "more gates and is closed without repair."
        ),
    }
    return result, {
        "MODEL_SCORES": scores,
        "SELECTED_DECISIONS": selected,
        "COEFFICIENTS": coefficients,
        "PREDICTIONS": predictions,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "FAMILY",
    "OUTPUT_ROOT",
    "_side_rows",
    "execute",
    "fit_and_score",
    "load_config",
    "run_census",
    "run_neutral_selective_target_probability",
    "select_evaluation_points",
    "verify_lock",
    "write_json",
]
