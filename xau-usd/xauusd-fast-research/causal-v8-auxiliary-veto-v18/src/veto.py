from __future__ import annotations

from typing import Sequence

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


def apply_v8_veto(
    frame: pd.DataFrame,
    *,
    specialist_id: str,
    threshold: float | None,
) -> pd.DataFrame:
    missing = sorted(
        {"family_id", "b123_selected", "v8_model_score"} - set(frame.columns)
    )
    if missing:
        raise ValueError(f"V18 frame is missing columns: {missing}")
    result = frame.copy()
    is_v8 = result["family_id"].eq(specialist_id)
    baseline = result["b123_selected"].astype(bool)
    if threshold is None:
        v8_selected = baseline
    else:
        score_pass = result["v8_model_score"].isna() | result[
            "v8_model_score"
        ].ge(float(threshold))
        v8_selected = baseline & score_pass
    result["v18_selected"] = baseline
    result.loc[is_v8, "v18_selected"] = v8_selected.loc[is_v8]
    result["v18_veto"] = ~result["v18_selected"]
    result["v8_additional_veto"] = (
        is_v8 & baseline & ~result["v18_selected"]
    )
    if not result.loc[~is_v8, "v18_selected"].equals(
        baseline.loc[~is_v8]
    ):
        raise ValueError("V18 changed a non-V8 B123 decision")
    if (result["v18_selected"] & ~baseline).any():
        raise ValueError("V18 re-admitted a B123-vetoed candidate")
    return result
