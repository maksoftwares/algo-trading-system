from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
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
    result: dict[str, Path] = {}
    for name, spec in config["inputs"].items():
        path = repo_root / str(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != str(spec["sha256"]):
            raise ValueError(f"Input hash mismatch for {name}: {actual}")
        result[name] = path
    return result


def require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def feature_surface(
    step_2b_contract: Mapping[str, Any], config: Mapping[str, Any]
) -> tuple[list[str], list[str]]:
    blocks = {
        str(block["block_id"]): list(block["features"])
        for block in step_2b_contract["feature_contract"]["ordered_blocks"]
    }
    raw: list[str] = []
    for block_id in config["features"]["source_blocks"]:
        raw.extend(blocks[str(block_id)])
    excluded = set(config["features"]["excluded_categorical"])
    family = str(config["features"]["categorical_family"])
    numeric = [column for column in raw if column != family and column not in excluded]
    if len(numeric) != len(set(numeric)):
        raise ValueError("Numeric feature surface contains duplicates")
    return raw, numeric


def prepare_population(
    dataset: pd.DataFrame,
    config: Mapping[str, Any],
    numeric_features: Sequence[str],
) -> pd.DataFrame:
    required = [
        "candidate_id",
        "family_id",
        "decision_time",
        "label_end_time",
        "structural_episode_id",
        "structural_weight",
        "stress_net_r",
        "stress_net_r_positive",
        str(config["population"]["eligibility_column"]),
        *numeric_features,
    ]
    require_columns(dataset, required, "Step 3 canonical dataset")
    if len(dataset) != int(config["population"]["expected_canonical_rows"]):
        raise ValueError("Canonical row count changed")
    if dataset["candidate_id"].duplicated().any():
        raise ValueError("Canonical candidate IDs are duplicated")
    result = dataset.copy()
    for column in ("decision_time", "label_end_time"):
        result[column] = pd.to_datetime(result[column], utc=True)
    result = result.loc[
        result[str(config["population"]["eligibility_column"])].eq(
            str(config["population"]["eligibility_value"])
        )
    ].copy()
    if len(result) != int(config["population"]["expected_xau_feature_pass_rows"]):
        raise ValueError("XAU feature-pass population changed")
    if set(result["family_id"]) != set(config["population"]["families"]):
        raise ValueError("Canonical family surface changed")
    values = result[list(numeric_features)].to_numpy(dtype=float)
    if np.isinf(values).any():
        raise ValueError("Numeric predictors contain infinity")
    return result


def prepare_dataset(
    dataset: pd.DataFrame,
    splits: pd.DataFrame,
    config: Mapping[str, Any],
    numeric_features: Sequence[str],
) -> pd.DataFrame:
    result = prepare_population(dataset, config, numeric_features)
    require_columns(
        splits,
        [
            "fold_id",
            "candidate_id",
            "structural_episode_id",
            "assignment",
            "dataset_eligible",
        ],
        "Step 3 splits",
    )
    joined = result.merge(
        splits[
            [
                "fold_id",
                "candidate_id",
                "structural_episode_id",
                "assignment",
                "dataset_eligible",
            ]
        ],
        on=["candidate_id", "structural_episode_id"],
        how="inner",
        validate="one_to_many",
    )
    return joined.loc[joined["dataset_eligible"].astype(bool)].copy()


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
    if np.any(weight_array < 0.0) or float(weight_array.sum()) <= 0.0:
        raise ValueError("Weighted quantile requires positive total weight")
    order = np.argsort(value_array, kind="mergesort")
    ordered_values = value_array[order]
    cumulative = np.cumsum(weight_array[order])
    index = int(
        np.searchsorted(cumulative, quantile * float(weight_array.sum()), side="left")
    )
    return float(ordered_values[min(index, len(ordered_values) - 1)])


@dataclass
class PartialPoolingExpectedR:
    numeric_features: list[str]
    families: list[str]
    medians: np.ndarray
    means: np.ndarray
    scales: np.ndarray
    interaction_scale: float
    estimator: Ridge

    @classmethod
    def fit(
        cls,
        frame: pd.DataFrame,
        *,
        numeric_features: Sequence[str],
        families: Sequence[str],
        alpha: float,
        interaction_scale: float,
        target_clip: tuple[float, float],
    ) -> "PartialPoolingExpectedR":
        family_list = list(families)
        numeric_list = list(numeric_features)
        numeric = frame[numeric_list].to_numpy(dtype=float)
        medians = np.nanmedian(numeric, axis=0)
        filled = np.where(np.isnan(numeric), medians, numeric)
        means = filled.mean(axis=0)
        scales = filled.std(axis=0, ddof=1)
        scales = np.where(scales > 0.0, scales, 1.0)
        shell = cls(
            numeric_features=numeric_list,
            families=family_list,
            medians=medians,
            means=means,
            scales=scales,
            interaction_scale=float(interaction_scale),
            estimator=Ridge(alpha=float(alpha), fit_intercept=True),
        )
        design = shell.design(frame)
        target = np.clip(
            frame["stress_net_r"].to_numpy(dtype=float),
            float(target_clip[0]),
            float(target_clip[1]),
        )
        shell.estimator.fit(
            design,
            target,
            sample_weight=frame["structural_weight"].to_numpy(dtype=float),
        )
        return shell

    def design(self, frame: pd.DataFrame) -> np.ndarray:
        require_columns(
            frame, [*self.numeric_features, "family_id"], "Expected-R score frame"
        )
        numeric = frame[self.numeric_features].to_numpy(dtype=float)
        filled = np.where(np.isnan(numeric), self.medians, numeric)
        standardized = (filled - self.means) / self.scales
        family = frame["family_id"].astype(str)
        one_hot = np.column_stack(
            [family.eq(value).to_numpy(dtype=float) for value in self.families]
        )
        interactions = np.concatenate(
            [
                standardized * one_hot[:, index : index + 1]
                for index in range(len(self.families))
            ],
            axis=1,
        )
        interactions *= self.interaction_scale
        return np.concatenate([standardized, one_hot, interactions], axis=1)

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return np.asarray(self.estimator.predict(self.design(frame)), dtype=float)


def calibration_thresholds(
    calibration: pd.DataFrame,
    *,
    families: Sequence[str],
    quantile: float,
    minimum_family_rows: int,
) -> tuple[float, dict[str, float], list[dict[str, Any]]]:
    pooled = weighted_quantile(
        calibration["model_score"],
        calibration["structural_weight"],
        quantile,
    )
    thresholds: dict[str, float] = {}
    rows: list[dict[str, Any]] = []
    for family in families:
        group = calibration.loc[calibration["family_id"].eq(family)]
        supported = len(group) >= int(minimum_family_rows)
        threshold = (
            weighted_quantile(
                group["model_score"], group["structural_weight"], quantile
            )
            if supported
            else pooled
        )
        thresholds[str(family)] = float(threshold)
        rows.append(
            {
                "family_id": str(family),
                "calibration_rows": int(len(group)),
                "calibration_weight": float(group["structural_weight"].sum()),
                "threshold": float(threshold),
                "threshold_source": "FAMILY" if supported else "POOLED_FALLBACK",
            }
        )
    return pooled, thresholds, rows


def apply_thresholds(
    frame: pd.DataFrame,
    thresholds: Mapping[str, float],
    pooled_threshold: float,
) -> pd.DataFrame:
    result = frame.copy()
    result["threshold"] = result["family_id"].map(thresholds).fillna(pooled_threshold)
    result["selected"] = result["model_score"].ge(result["threshold"])
    return result


def weighted_profit_factor(values: np.ndarray, weights: np.ndarray) -> float | None:
    positive = float(np.dot(np.clip(values, 0.0, None), weights))
    negative = float(np.dot(np.clip(-values, 0.0, None), weights))
    if negative == 0.0:
        return None if positive == 0.0 else float("inf")
    return positive / negative


def weighted_drawdown(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    episodes = (
        frame.assign(weighted_return=frame["stress_net_r"] * frame["structural_weight"])
        .groupby("structural_episode_id", sort=False)
        .agg(
            decision_time=("decision_time", "min"),
            weighted_return=("weighted_return", "sum"),
        )
        .sort_values("decision_time", kind="mergesort")
    )
    equity = episodes["weighted_return"].cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def business_days(start: pd.Timestamp, end: pd.Timestamp) -> int:
    first = pd.Timestamp(start).tz_localize(None).normalize()
    last = pd.Timestamp(end).tz_localize(None).normalize()
    return int(len(pd.date_range(first, last, freq="B")))


def economic_metrics(
    frame: pd.DataFrame,
    *,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "rows": 0,
            "episodes": 0,
            "weight": 0.0,
            "weighted_mean_r": 0.0,
            "weighted_r_sum": 0.0,
            "weighted_profit_factor": None,
            "weighted_max_drawdown_r": 0.0,
            "weighted_win_rate": 0.0,
            "candidates_per_weekday": 0.0,
        }
    weights = frame["structural_weight"].to_numpy(dtype=float)
    values = frame["stress_net_r"].to_numpy(dtype=float)
    date_start = pd.Timestamp(
        start if start is not None else frame["decision_time"].min()
    )
    date_end = pd.Timestamp(end if end is not None else frame["decision_time"].max())
    return {
        "rows": int(len(frame)),
        "episodes": int(frame["structural_episode_id"].nunique()),
        "weight": float(weights.sum()),
        "weighted_mean_r": float(np.dot(values, weights) / weights.sum()),
        "weighted_r_sum": float(np.dot(values, weights)),
        "weighted_profit_factor": weighted_profit_factor(values, weights),
        "weighted_max_drawdown_r": weighted_drawdown(frame),
        "weighted_win_rate": float(np.average(values > 0.0, weights=weights)),
        "candidates_per_weekday": float(
            len(frame) / business_days(date_start, date_end)
        ),
    }


def comparison_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    ordered = frame.sort_values(
        ["decision_time", "candidate_id"], kind="mergesort"
    ).copy()
    selected = ordered.loc[ordered["selected"]]
    baseline = economic_metrics(ordered)
    retained = economic_metrics(
        selected,
        start=ordered["decision_time"].min(),
        end=ordered["decision_time"].max(),
    )
    weights = ordered["structural_weight"].to_numpy(dtype=float)
    target = ordered["stress_net_r_positive"].astype(int)
    auc = (
        float(roc_auc_score(target, ordered["model_score"], sample_weight=weights))
        if target.nunique() == 2
        else None
    )
    return {
        "baseline": baseline,
        "selected": retained,
        "weighted_score_auc": auc,
        "selected_weight_coverage": float(
            selected["structural_weight"].sum() / ordered["structural_weight"].sum()
        ),
        "selected_mean_lift_r": float(
            retained["weighted_mean_r"] - baseline["weighted_mean_r"]
        ),
        "drawdown_ratio_to_baseline": float(
            retained["weighted_max_drawdown_r"] / baseline["weighted_max_drawdown_r"]
        ),
    }


def weekly_block_bootstrap(
    frame: pd.DataFrame,
    *,
    resamples: int,
    confidence: float,
    seed: int,
) -> dict[str, Any]:
    source = frame.copy()
    source["utc_week"] = source["decision_time"].dt.strftime("%G-W%V")
    groups = [
        group.index.to_numpy() for _, group in source.groupby("utc_week", sort=True)
    ]
    if not groups:
        raise ValueError("Weekly bootstrap has no blocks")
    rng = np.random.default_rng(seed)
    statistics = {
        "selected_weighted_mean_r": [],
        "baseline_weighted_mean_r": [],
        "selected_mean_lift_r": [],
        "selected_profit_factor": [],
        "selected_weight_coverage": [],
    }
    for _ in range(int(resamples)):
        sample = source.loc[
            np.concatenate(
                [groups[index] for index in rng.integers(0, len(groups), len(groups))]
            )
        ]
        metrics = comparison_metrics(sample)
        statistics["selected_weighted_mean_r"].append(
            metrics["selected"]["weighted_mean_r"]
        )
        statistics["baseline_weighted_mean_r"].append(
            metrics["baseline"]["weighted_mean_r"]
        )
        statistics["selected_mean_lift_r"].append(metrics["selected_mean_lift_r"])
        statistics["selected_profit_factor"].append(
            metrics["selected"]["weighted_profit_factor"]
        )
        statistics["selected_weight_coverage"].append(
            metrics["selected_weight_coverage"]
        )
    alpha = (1.0 - confidence) / 2.0
    intervals = {}
    for name, values in statistics.items():
        array = np.asarray(values, dtype=float)
        intervals[name] = {
            "lower": float(np.quantile(array, alpha)),
            "median": float(np.quantile(array, 0.5)),
            "upper": float(np.quantile(array, 1.0 - alpha)),
        }
    return {
        "schema_version": "xauusd_expected_r_v10_weekly_bootstrap",
        "resamples": int(resamples),
        "confidence": float(confidence),
        "seed": int(seed),
        "weekly_blocks": int(len(groups)),
        "intervals": intervals,
    }
