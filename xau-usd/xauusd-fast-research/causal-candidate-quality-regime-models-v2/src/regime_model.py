from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from step_4_metrics import economic_metrics, probability_metrics


def build_model(parameters: Mapping[str, Any]) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(**dict(parameters))),
        ]
    )


def fit_model(
    frame: pd.DataFrame,
    *,
    features: Sequence[str],
    parameters: Mapping[str, Any],
) -> Pipeline:
    if frame["stress_net_r_positive"].nunique() < 2:
        raise ValueError("Family fit data does not contain both target classes")
    numeric = frame[list(features)].to_numpy(dtype=float)
    if np.isinf(numeric).any():
        raise ValueError("Regime model features contain infinity")
    model = build_model(parameters)
    model.fit(
        frame[list(features)],
        frame["stress_net_r_positive"].astype(int),
        model__sample_weight=frame["structural_weight"].to_numpy(dtype=float),
    )
    return model


def weighted_prior(frame: pd.DataFrame) -> float:
    weights = frame["structural_weight"].to_numpy(dtype=float)
    target = frame["stress_net_r_positive"].astype(float).to_numpy()
    return float(np.dot(weights, target) / weights.sum())


def predict(model: Pipeline, frame: pd.DataFrame, features: Sequence[str]) -> np.ndarray:
    return model.predict_proba(frame[list(features)])[:, 1]


def safe_probability_metrics(frame: pd.DataFrame) -> dict[str, float | None]:
    if frame["target"].nunique() < 2:
        return {
            "weighted_roc_auc": None,
            "weighted_average_precision": None,
            "weighted_brier": None,
            "weighted_log_loss": None,
            "weighted_ece": None,
        }
    return probability_metrics(frame)


def fold_metric_row(
    test: pd.DataFrame,
    *,
    family_id: str,
    fold_id: str,
    fit_rows: int,
    calibration_rows: int,
    threshold: float,
    fit_prior: float,
    weekdays: int,
) -> dict[str, Any]:
    probability = safe_probability_metrics(test)
    selected = economic_metrics(test, test["selected"], weekdays=weekdays)
    baseline = economic_metrics(
        test, np.ones(len(test), dtype=bool), weekdays=weekdays
    )
    return {
        "family_id": family_id,
        "fold_id": fold_id,
        "fit_rows": fit_rows,
        "calibration_rows": calibration_rows,
        "test_rows": len(test),
        "threshold": threshold,
        "fit_weighted_positive_prior": fit_prior,
        **probability,
        **{f"selected_{key}": value for key, value in selected.items()},
        **{f"baseline_{key}": value for key, value in baseline.items()},
        "selected_minus_baseline_weighted_mean_stress_r": (
            float(selected["weighted_mean_stress_r"])
            - float(baseline["weighted_mean_stress_r"])
        ),
    }
