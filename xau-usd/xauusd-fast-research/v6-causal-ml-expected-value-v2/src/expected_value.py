from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


REPO_ROOT = Path(__file__).resolve().parents[4]
LANE_ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def verify_sources(config: Mapping[str, Any]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, source in config["sources"].items():
        path = resolve_path(source["path"])
        if not path.is_file():
            raise FileNotFoundError(f"Missing locked source {name}: {path}")
        actual = sha256_file(path)
        if actual != source["sha256"]:
            raise ValueError(
                f"Locked source drift for {name}: expected {source['sha256']}, got {actual}"
            )
        observed[name] = actual
    return observed


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def clipped_target(
    stress_net_r: pd.Series | np.ndarray, minimum: float, maximum: float
) -> np.ndarray:
    if not minimum < 0.0 < maximum:
        raise ValueError("Expected-value target bounds must straddle zero")
    values = np.asarray(stress_net_r, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Expected-value target contains non-finite values")
    return np.clip(values, minimum, maximum)


def annual_training_rows(
    corpus: pd.DataFrame, target_year: int, purge_hours: float
) -> pd.DataFrame:
    cutoff = pd.Timestamp(f"{target_year}-01-01", tz="UTC") - pd.Timedelta(
        hours=purge_hours
    )
    return corpus.loc[corpus["exit_time"].lt(cutoff)].copy()


def rank_correlation(actual: np.ndarray, predicted: np.ndarray) -> float:
    left = pd.Series(actual, dtype=float).rank(method="average")
    right = pd.Series(predicted, dtype=float).rank(method="average")
    if left.std(ddof=0) == 0.0 or right.std(ddof=0) == 0.0:
        return 0.0
    value = float(left.corr(right))
    return value if np.isfinite(value) else 0.0


def make_model(config: Mapping[str, Any]) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(**dict(config["model"]["parameters"]))


def annual_expected_value_predictions(
    corpus: pd.DataFrame,
    candidates: pd.DataFrame,
    config: Mapping[str, Any],
    feature_config: Mapping[str, Any],
    v1: ModuleType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = config["walk_forward"]
    model_config = config["model"]
    prediction_frames: list[pd.DataFrame] = []
    logs: list[dict[str, Any]] = []
    corpus = corpus.copy()
    corpus["stress_net_r"] = (
        corpus["fee_stress_pnl_usd"].astype(float)
        / corpus["stop_usd"].astype(float)
    )
    for year in settings["target_years"]:
        train = annual_training_rows(
            corpus, int(year), float(settings["purge_hours"])
        )
        target = candidates.loc[candidates["entry_time"].dt.year.eq(int(year))].copy()
        if len(train) < int(settings["minimum_training_rows"]):
            raise ValueError(f"Insufficient training rows for {year}: {len(train)}")
        if target.empty:
            raise ValueError(f"No frozen V6 candidates for target year {year}")
        train_target = clipped_target(
            train["stress_net_r"],
            float(model_config["target_min_r"]),
            float(model_config["target_max_r"]),
        )
        model = make_model(config)
        model.fit(
            v1.build_feature_matrix(train, feature_config),
            train_target,
            sample_weight=v1.day_equal_sample_weights(train),
        )
        score = model.predict(
            v1.build_feature_matrix(target, feature_config)
        )
        target["ml_expected_utility_r"] = score
        target["ml_selected"] = target["ml_expected_utility_r"].gt(
            float(model_config["selection_threshold_r"])
        )
        prediction_frames.append(target)
        actual = target["stress_net_r"].to_numpy(dtype=float)
        logs.append(
            {
                "target_year": int(year),
                "training_rows": len(train),
                "training_last_exit_time": train["exit_time"].max(),
                "training_target_mean": float(train_target.mean()),
                "training_target_std": float(train_target.std()),
                "target_rows": len(target),
                "target_selected_rows": int(target["ml_selected"].sum()),
                "target_retained_share": float(target["ml_selected"].mean()),
                "target_auc": v1.safe_auc(target["label"], score),
                "target_spearman": rank_correlation(actual, score),
                "target_score_mean": float(np.mean(score)),
                "target_score_min": float(np.min(score)),
                "target_score_max": float(np.max(score)),
            }
        )
    predictions = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    )
    return predictions.reset_index(drop=True), pd.DataFrame(logs)
