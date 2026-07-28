from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_binance_eurusdt_flow import (
    build_decisions as build_flow_decisions,
    build_flow_signals,
    load_config as load_flow_config,
    load_flow,
    load_parent_points,
)
from .neutral_four_clock_ranker import (
    _direction_metrics,
    _period,
    admission,
    evaluate_oracle,
    purged_training_points,
    route_predictions,
    summarize as summarize_parent,
)
from .neutral_midnight_pairs import aggregate_days, write_json
from .research import PACKAGE_ROOT, active_weekday_fx_days, sha256_file


FAMILY = "N23_NEUTRAL_FLOW_AUGMENTED_PAIRED_RANKER"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_flow_augmented_ranker"
TRAINING_WINDOW = "TRAINING_2020_2021"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_flow_augmented_ranker.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_FLOW_AUGMENTED_RANKER_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_flow_augmented_ranker_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral flow-augmented ranker is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral flow-augmented ranker preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for source_key in (
        "parent_four_clock_contract",
        "parent_flow_contract",
        "paired_trade_source",
        "executed_flow_source",
    ):
        source = cfg[source_key]
        source_path = Path(source["path"])
        if not source_path.is_absolute():
            source_path = PACKAGE_ROOT / source_path
        if sha256_file(source_path) != source["sha256"]:
            raise RuntimeError(
                f"Neutral flow-augmented ranker {source_key} drift"
            )
    return checked


def _window_name(
    timestamp: pd.Timestamp,
    cfg: dict[str, Any],
) -> str:
    train_start, train_end = map(pd.Timestamp, cfg["training_period"])
    if train_start <= timestamp <= train_end:
        return TRAINING_WINDOW
    for name, (start_raw, end_raw) in cfg[
        "evaluation_windows"
    ].items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def build_campaign_points(
    decisions: pd.DataFrame,
    source_census: dict[str, Any],
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    points = decisions.copy()
    points["window"] = points["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    window_names = [TRAINING_WINDOW, *cfg["evaluation_windows"].keys()]
    points = (
        points[points["window"].isin(window_names)]
        .sort_values("entry_time_utc")
        .reset_index(drop=True)
    )
    expected = int(cfg["strategy"]["required_trades_per_eligible_day"])
    daily = points.groupby("eligible_date").size()
    by_window: dict[str, Any] = {}
    for name in window_names:
        subset = points[points["window"].eq(name)]
        by_window[name] = {
            "eligible_days": int(subset["eligible_date"].nunique()),
            "decision_points": int(len(subset)),
            "forced_trade_candidates": int(len(subset)),
        }
    eligible_days = int(points["eligible_date"].nunique())
    exact_days = int((daily == expected).sum())
    census = {
        "source_flow_complete_days": int(
            source_census["eligible_complete_days"]
        ),
        "source_flow_decision_points": int(
            source_census["paired_decision_points"]
        ),
        "eligible_complete_days": eligible_days,
        "paired_decision_points": int(len(points)),
        "forced_trade_candidates": int(len(points)),
        "days_exactly_four_candidates": exact_days,
        "eligible_day_exact_four_coverage": (
            exact_days / eligible_days if eligible_days else 0.0
        ),
        "by_window": by_window,
    }
    if enforce_frozen_census and census != cfg["outcome_blind_census"]:
        raise RuntimeError(
            "Flow-augmented ranker census drift: "
            f"actual={census!r} frozen={cfg['outcome_blind_census']!r}"
        )
    return points, census


def load_campaign_points(
    cfg: dict[str, Any],
    *,
    include_outcomes: bool,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    flow_cfg = load_flow_config()
    parent = load_parent_points(include_outcomes=include_outcomes)
    flow = load_flow(flow_cfg)
    signals = build_flow_signals(flow, flow_cfg)
    decisions, source_census = build_flow_decisions(
        parent,
        signals,
        flow_cfg,
        enforce_frozen_census=True,
    )
    return build_campaign_points(
        decisions,
        source_census,
        cfg,
        enforce_frozen_census=enforce_frozen_census,
    )


def fit_ranker(
    training: pd.DataFrame,
    inference: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[np.ndarray, pd.DataFrame]:
    minimum = int(cfg["model"]["minimum_training_one_winner_pairs"])
    if len(training) < minimum:
        raise RuntimeError(
            "Insufficient purged one-winner pairs: "
            f"{len(training)} < {minimum}"
        )
    columns = list(cfg["features"]["model_columns"])
    scaler = StandardScaler()
    train_x = scaler.fit_transform(training[columns])
    labels = training["preferred_long"].astype(int)
    if labels.nunique() != 2:
        raise RuntimeError("Paired ranker training requires both classes")
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
    probabilities = model.predict_proba(
        scaler.transform(inference[columns])
    )[:, 1]
    coefficients = pd.DataFrame(
        {
            "feature": columns,
            "coefficient": model.coef_[0],
            "training_mean": scaler.mean_,
            "training_scale": scaler.scale_,
        }
    ).sort_values("coefficient", ascending=False)
    return probabilities, coefficients


def evaluate_windows(
    points: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    all_trades: list[pd.DataFrame] = []
    all_predictions: list[pd.DataFrame] = []
    all_coefficients: list[pd.DataFrame] = []
    window_results: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg[
        "evaluation_windows"
    ].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        training = purged_training_points(points, start)
        inference = _period(points, start, end).copy()
        probabilities, coefficients = fit_ranker(
            training, inference, cfg
        )
        trades, predicted = route_predictions(
            inference, probabilities, cfg
        )
        trades["family"] = FAMILY
        trades["evaluation_window"] = name
        predicted["evaluation_window"] = name
        coefficients["evaluation_window"] = name
        daily = aggregate_days(trades)
        ticket_metrics = payoff_metrics(trades)
        active_days = active_weekday_fx_days(m5, start, end)
        ticket_metrics["active_weekdays"] = active_days
        ticket_metrics["trades_per_active_weekday"] = (
            len(trades) / active_days if active_days else 0.0
        )
        ticket_metrics["eligible_neutral_days"] = int(
            trades["eligible_date"].nunique()
        )
        ticket_metrics["trades_per_eligible_neutral_day"] = (
            len(trades)
            / ticket_metrics["eligible_neutral_days"]
            if ticket_metrics["eligible_neutral_days"]
            else 0.0
        )
        window_results[name] = {
            "training_one_winner_pairs": int(len(training)),
            "training_long_class_rate": float(
                training["preferred_long"].mean()
            ),
            "tickets": ticket_metrics,
            "daily_portfolio": payoff_metrics(daily),
            "direction_selection": _direction_metrics(predicted),
        }
        all_trades.append(trades)
        all_predictions.append(predicted)
        all_coefficients.append(coefficients)
    return (
        pd.concat(all_trades, ignore_index=True),
        pd.concat(all_predictions, ignore_index=True),
        pd.concat(all_coefficients, ignore_index=True),
        window_results,
    )


def _parent_compatible_census(
    census: dict[str, Any],
) -> dict[str, Any]:
    compatible = copy.deepcopy(census)
    compatible["by_window"] = {
        "TRAINING_2019_2020": compatible["by_window"].pop(
            TRAINING_WINDOW
        ),
        **compatible["by_window"],
    }
    return compatible


def run_census() -> dict[str, Any]:
    cfg = load_config()
    _, census = load_campaign_points(
        cfg,
        include_outcomes=False,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_flow_augmented_ranker() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    points, census = load_campaign_points(
        cfg,
        include_outcomes=True,
        enforce_frozen_census=True,
    )
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    trades, predictions, coefficients, windows = evaluate_windows(
        points, m5, cfg
    )
    strategy = summarize_parent(
        trades,
        predictions,
        windows,
        m5,
        cfg,
        _parent_compatible_census(census),
    )
    oracle, matches = evaluate_oracle(trades, cfg)
    admitted, checks = admission(strategy, oracle, cfg)
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    prospective_points = points[
        points["entry_time_utc"] >= prospective_start
    ]
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_FLOW_AUGMENTED_PAIRED_RANKER_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "executed_flow_source": cfg["executed_flow_source"],
        "causality": {
            "paired_features": (
                "sixteen frozen LONG-minus-SHORT decision-time contrasts"
            ),
            "executed_flow_features": (
                "prior three fully completed EURUSDT M5 bars' taker "
                "imbalance and return"
            ),
            "model_features": cfg["features"]["model_columns"],
            "label_purge": (
                "both entry and paired label-known time strictly before "
                "each inference window"
            ),
            "direction": (
                "fixed 0.5 paired probability; no feature, interaction, "
                "threshold, or hyperparameter search"
            ),
            "future_information_in_inference": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "outcome_blind_census": census,
        "strategy": {
            "admitted": admitted,
            "admission_checks": checks,
            **strategy,
        },
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": cfg["prospective"]["start_utc"],
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": int(len(prospective_points)),
            "status": (
                "WAITING_FOR_POST_LOCK_MARKET_DATA"
                if prospective_points.empty
                else "POST_LOCK_POINTS_AVAILABLE"
            ),
        },
        "verdict": (
            "The frozen flow-augmented paired ranker passed all historical "
            "gates; only post-lock rows may confirm it."
            if admitted
            else "The frozen flow-augmented paired ranker failed one or "
            "more gates and is closed without repair."
        ),
    }
    artifacts = {
        "TRADES": trades,
        "PREDICTIONS": predictions,
        "COEFFICIENTS": coefficients,
        "ORACLE_MATCHES": matches,
    }
    return result, artifacts


__all__ = [
    "FAMILY",
    "OUTPUT_ROOT",
    "TRAINING_WINDOW",
    "build_campaign_points",
    "fit_ranker",
    "load_campaign_points",
    "load_config",
    "purged_training_points",
    "run_census",
    "run_neutral_flow_augmented_ranker",
    "verify_lock",
    "write_json",
]
