from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge


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


@dataclass
class SpecialistExpectedR:
    features: tuple[str, ...]
    medians: np.ndarray
    means: np.ndarray
    scales: np.ndarray
    estimator: Ridge

    @classmethod
    def fit(
        cls,
        frame: pd.DataFrame,
        *,
        alpha: float,
        target_clip: tuple[float, float],
    ) -> "SpecialistExpectedR":
        missing = sorted(
            set((*AUXILIARY_SCORES, "stress_net_r", "structural_weight"))
            - set(frame.columns)
        )
        if missing:
            raise ValueError(f"Specialist fit frame is missing columns: {missing}")
        values = frame[list(AUXILIARY_SCORES)].to_numpy(dtype=float)
        medians = np.nanmedian(values, axis=0)
        if np.isnan(medians).any():
            raise ValueError("A specialist score is entirely missing")
        filled = np.where(np.isnan(values), medians, values)
        means = filled.mean(axis=0)
        scales = filled.std(axis=0, ddof=1)
        scales = np.where(scales > 0.0, scales, 1.0)
        design = (filled - means) / scales
        estimator = Ridge(alpha=float(alpha), fit_intercept=True)
        estimator.fit(
            design,
            frame["stress_net_r"]
            .clip(float(target_clip[0]), float(target_clip[1]))
            .to_numpy(dtype=float),
            sample_weight=frame["structural_weight"].to_numpy(dtype=float),
        )
        return cls(
            features=AUXILIARY_SCORES,
            medians=medians,
            means=means,
            scales=scales,
            estimator=estimator,
        )

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        values = frame[list(self.features)].to_numpy(dtype=float)
        filled = np.where(np.isnan(values), self.medians, values)
        result = self.estimator.predict((filled - self.means) / self.scales)
        if not np.isfinite(result).all():
            raise ValueError("Specialist predictions are not finite")
        return np.asarray(result, dtype=float)


def apply_v57_confirmation(
    frame: pd.DataFrame,
    *,
    specialist_id: str,
    threshold: float | None,
    fallback_retain_all: bool,
) -> pd.DataFrame:
    missing = sorted(
        {"family_id", "b123_selected", "v57_model_score"} - set(frame.columns)
    )
    if missing:
        raise ValueError(f"V17 frame is missing columns: {missing}")
    result = frame.copy()
    is_v57 = result["family_id"].eq(specialist_id)
    if threshold is None:
        v57_selected = pd.Series(
            bool(fallback_retain_all), index=result.index, dtype=bool
        )
    else:
        v57_selected = result["b123_selected"].astype(bool) | result[
            "v57_model_score"
        ].ge(float(threshold))
    result["v17_selected"] = result["b123_selected"].astype(bool)
    result.loc[is_v57, "v17_selected"] = v57_selected.loc[is_v57]
    result["v17_veto"] = ~result["v17_selected"]
    result["v57_re_admitted"] = (
        is_v57
        & ~result["b123_selected"].astype(bool)
        & result["v17_selected"]
    )
    if not result.loc[~is_v57, "v17_selected"].equals(
        result.loc[~is_v57, "b123_selected"].astype(bool)
    ):
        raise ValueError("V17 changed a non-V57 B123 decision")
    if not result.loc[
        is_v57 & result["b123_selected"].astype(bool), "v17_selected"
    ].all():
        raise ValueError("V17 vetoed a B123-retained V57 candidate")
    return result
