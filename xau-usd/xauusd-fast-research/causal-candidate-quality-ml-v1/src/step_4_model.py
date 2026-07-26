from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class FittedProbabilityModel:
    estimator: Pipeline
    calibrator: LogisticRegression
    feature_names: list[str]
    inner_base_rows: int
    inner_calibrator_rows: int
    inner_purged_rows: int

    def predict_proba(self, frame: pd.DataFrame, clip: float) -> np.ndarray:
        raw = self.estimator.predict_proba(frame[self.feature_names])[:, 1]
        logits = probability_logit(raw, clip)
        return self.calibrator.predict_proba(logits.reshape(-1, 1))[:, 1]


def feature_names_for_blocks(
    step2b: Mapping[str, Any], block_ids: Sequence[str]
) -> list[str]:
    requested = set(block_ids)
    blocks = step2b["feature_contract"]["ordered_blocks"]
    available = {str(block["block_id"]) for block in blocks}
    missing = requested - available
    if missing:
        raise ValueError(f"Unknown feature blocks: {sorted(missing)}")
    return [
        str(name)
        for block in blocks
        if str(block["block_id"]) in requested
        for name in block["features"]
    ]


def eligibility_mask(frame: pd.DataFrame, rule: str) -> pd.Series:
    if rule == "RESOLVED_CANONICAL":
        return frame["label_status"].str.startswith("RESOLVED_")
    if rule == "XAU_FEATURE_STATUS_PASS":
        return frame["xau_feature_status"].eq("PASS")
    if rule == "XAU_AND_CROSSASSET_STATUS_PASS":
        return frame["xau_feature_status"].eq("PASS") & frame[
            "crossasset_feature_status"
        ].eq("PASS")
    raise ValueError(f"Unknown eligibility rule: {rule}")


def probability_logit(probability: np.ndarray, clip: float) -> np.ndarray:
    clipped = np.clip(np.asarray(probability, dtype=float), clip, 1.0 - clip)
    return np.log(clipped / (1.0 - clipped))


def chronological_calibration_split(
    frame: pd.DataFrame, trailing_fraction: float
) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    episodes = (
        frame.groupby("structural_episode_id", as_index=False)
        .agg(decision_time=("decision_time", "min"))
        .sort_values(["decision_time", "structural_episode_id"], kind="stable")
        .reset_index(drop=True)
    )
    cut = max(
        1,
        min(len(episodes) - 1, int(np.floor(len(episodes) * (1 - trailing_fraction)))),
    )
    calibrator_ids = set(episodes.loc[cut:, "structural_episode_id"].astype(str))
    calibrator = frame.loc[
        frame["structural_episode_id"].astype(str).isin(calibrator_ids)
    ].copy()
    calibrator_start = calibrator["decision_time"].min()
    earlier = frame.loc[
        ~frame["structural_episode_id"].astype(str).isin(calibrator_ids)
    ].copy()
    episode_ends = earlier.groupby("structural_episode_id")["label_end_time"].max()
    base_ids = set(
        episode_ends.loc[episode_ends.lt(calibrator_start)].index.astype(str)
    )
    base = earlier.loc[
        earlier["structural_episode_id"].astype(str).isin(base_ids)
    ].copy()
    return base, calibrator, len(earlier) - len(base)


def _preprocessor(
    feature_names: Sequence[str],
    categorical: Sequence[str],
    *,
    scale_numeric: bool,
) -> ColumnTransformer:
    category_names = [name for name in categorical if name in feature_names]
    numeric_names = [name for name in feature_names if name not in category_names]
    numeric_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median"))
    ]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    category_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", Pipeline(numeric_steps), numeric_names),
            ("categorical", category_pipeline, category_names),
        ],
        remainder="drop",
        sparse_threshold=0.0,
    )


def build_estimator(
    spec: Mapping[str, Any],
    feature_names: Sequence[str],
    categorical: Sequence[str],
) -> Pipeline:
    kind = str(spec["estimator"])
    parameters = dict(spec["parameters"])
    if kind == "HIST_GRADIENT_BOOSTING_CLASSIFIER":
        estimator = HistGradientBoostingClassifier(**parameters)
        scale_numeric = False
    elif kind == "LOGISTIC_REGRESSION":
        estimator = LogisticRegression(**parameters)
        scale_numeric = True
    else:
        raise ValueError(f"Unknown estimator: {kind}")
    return Pipeline(
        [
            (
                "preprocess",
                _preprocessor(feature_names, categorical, scale_numeric=scale_numeric),
            ),
            ("model", estimator),
        ]
    )


def _validate_fit_frame(frame: pd.DataFrame, feature_names: Sequence[str]) -> None:
    missing = sorted(set(feature_names) - set(frame.columns))
    if missing:
        raise ValueError(f"Model frame lacks features: {missing}")
    numeric = frame[list(feature_names)].select_dtypes(include=[np.number])
    if np.isinf(numeric.to_numpy(dtype=float)).any():
        raise ValueError("Model frame contains infinite features")
    if frame["stress_net_r_positive"].nunique() != 2:
        raise ValueError("Model frame does not contain both target classes")


def fit_probability_model(
    outer_fit: pd.DataFrame,
    *,
    spec: Mapping[str, Any],
    feature_names: list[str],
    categorical: Sequence[str],
    calibration: Mapping[str, Any],
) -> FittedProbabilityModel:
    ordered = outer_fit.sort_values(
        ["decision_time", "candidate_id"], kind="stable"
    ).reset_index(drop=True)
    _validate_fit_frame(ordered, feature_names)
    base, calibrator_frame, purged = chronological_calibration_split(
        ordered, float(calibration["trailing_episode_fraction"])
    )
    if len(base) < int(calibration["minimum_base_fit_rows"]):
        raise ValueError(f"Inner base fit has only {len(base)} rows")
    if len(calibrator_frame) < int(calibration["minimum_calibrator_rows"]):
        raise ValueError(f"Inner calibrator has only {len(calibrator_frame)} rows")
    _validate_fit_frame(base, feature_names)
    _validate_fit_frame(calibrator_frame, feature_names)

    temporary = build_estimator(spec, feature_names, categorical)
    temporary.fit(
        base[feature_names],
        base["stress_net_r_positive"].astype(int),
        model__sample_weight=base["structural_weight"].to_numpy(dtype=float),
    )
    clip = float(calibration["clip_probability"])
    raw = temporary.predict_proba(calibrator_frame[feature_names])[:, 1]
    logits = probability_logit(raw, clip).reshape(-1, 1)
    platt = LogisticRegression(
        C=float(calibration["platt_c"]),
        solver="lbfgs",
        max_iter=int(calibration["platt_max_iter"]),
        random_state=int(spec["parameters"]["random_state"]),
    )
    platt.fit(
        logits,
        calibrator_frame["stress_net_r_positive"].astype(int),
        sample_weight=calibrator_frame["structural_weight"].to_numpy(dtype=float),
    )

    final = build_estimator(spec, feature_names, categorical)
    final.fit(
        ordered[feature_names],
        ordered["stress_net_r_positive"].astype(int),
        model__sample_weight=ordered["structural_weight"].to_numpy(dtype=float),
    )
    return FittedProbabilityModel(
        estimator=final,
        calibrator=platt,
        feature_names=feature_names,
        inner_base_rows=len(base),
        inner_calibrator_rows=len(calibrator_frame),
        inner_purged_rows=purged,
    )
