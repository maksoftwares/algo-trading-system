from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
import pandas as pd


AUXILIARY_SCORES = (
    "aux_expected_r_linear",
    "aux_expected_r_nonlinear",
    "aux_win_probability",
)


def weighted_quantile(
    values: Sequence[float],
    weights: Sequence[float],
    quantile: float,
) -> float:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    if len(value_array) == 0 or len(value_array) != len(weight_array):
        raise ValueError("Weighted quantile requires equal nonempty arrays")
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("Quantile must be in [0, 1]")
    if not np.isfinite(value_array).all():
        raise ValueError("Weighted quantile values must be finite")
    if (
        not np.isfinite(weight_array).all()
        or np.any(weight_array < 0.0)
        or float(weight_array.sum()) <= 0.0
    ):
        raise ValueError("Weighted quantile requires finite positive weight")
    order = np.argsort(value_array, kind="mergesort")
    cumulative = np.cumsum(weight_array[order])
    index = int(
        np.searchsorted(
            cumulative,
            float(quantile) * float(weight_array.sum()),
            side="left",
        )
    )
    return float(value_array[order[min(index, len(order) - 1)]])


def calibration_thresholds(
    calibration: pd.DataFrame,
    quantile: float,
) -> dict[str, float]:
    missing = sorted(
        set((*AUXILIARY_SCORES, "structural_weight")) - set(calibration.columns)
    )
    if missing:
        raise ValueError(f"Calibration frame is missing columns: {missing}")
    return {
        score: weighted_quantile(
            calibration[score],
            calibration["structural_weight"],
            quantile,
        )
        for score in AUXILIARY_SCORES
    }


def apply_consensus(
    frame: pd.DataFrame,
    thresholds: Mapping[str, float],
    *,
    minimum_low_votes: int,
) -> pd.DataFrame:
    missing = sorted(
        set((*AUXILIARY_SCORES, "b123_selected")) - set(frame.columns)
    )
    if missing:
        raise ValueError(f"Consensus frame is missing columns: {missing}")
    if not 1 <= int(minimum_low_votes) <= len(AUXILIARY_SCORES):
        raise ValueError("Minimum low votes is outside the score count")
    if set(thresholds) != set(AUXILIARY_SCORES):
        raise ValueError("Consensus thresholds do not match auxiliary scores")

    result = frame.copy()
    vote_columns: list[str] = []
    for score in AUXILIARY_SCORES:
        vote = f"{score}_low_vote"
        result[vote] = result[score].le(float(thresholds[score]))
        vote_columns.append(vote)
    result["auxiliary_low_votes"] = result[vote_columns].sum(axis=1).astype(int)
    result["auxiliary_consensus_low"] = result["auxiliary_low_votes"].ge(
        int(minimum_low_votes)
    )
    result["v16_veto"] = (
        ~result["b123_selected"].astype(bool)
        & result["auxiliary_consensus_low"]
    )
    result["selected"] = ~result["v16_veto"]
    if not result.loc[result["b123_selected"].astype(bool), "selected"].all():
        raise ValueError("V16 vetoed a B123-retained candidate")
    return result
