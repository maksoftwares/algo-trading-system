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
from sklearn.metrics import mean_pinball_loss


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
                f"Locked source drift for {name}: "
                f"expected {source['sha256']}, got {actual}"
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


def benefit_r_target(snapshots: pd.DataFrame) -> np.ndarray:
    benefit = pd.to_numeric(snapshots["benefit_usd"], errors="raise").to_numpy(
        dtype=float
    )
    risk = pd.to_numeric(snapshots["risk_usd"], errors="raise").to_numpy(
        dtype=float
    )
    if (risk <= 0.0).any():
        raise ValueError("Utility target contains non-positive risk")
    target = benefit / risk
    if not np.isfinite(target).all():
        raise ValueError("Utility target contains non-finite values")
    return target


def rank_correlation(actual: np.ndarray, predicted: np.ndarray) -> float:
    left = pd.Series(actual, dtype=float).rank(method="average")
    right = pd.Series(predicted, dtype=float).rank(method="average")
    if left.std(ddof=0) == 0.0 or right.std(ddof=0) == 0.0:
        return 0.0
    value = float(left.corr(right))
    return value if np.isfinite(value) else 0.0


def make_model(config: Mapping[str, Any]) -> HistGradientBoostingRegressor:
    model = config["model"]
    parameters = dict(model["parameters"])
    parameters["loss"] = str(model["loss"])
    parameters["quantile"] = float(model["quantile"])
    return HistGradientBoostingRegressor(**parameters)


def action_mask(
    snapshots: pd.DataFrame,
    predicted_lower_benefit_r: np.ndarray,
    config: Mapping[str, Any],
) -> np.ndarray:
    policy = config["action_policy"]
    score = np.asarray(predicted_lower_benefit_r, dtype=float)
    if len(score) != len(snapshots) or not np.isfinite(score).all():
        raise ValueError("Utility action score is invalid")
    return (
        (score >= float(policy["minimum_predicted_lower_benefit_r"]))
        & (
            snapshots["current_r"].to_numpy(dtype=float)
            <= float(policy["maximum_current_r"])
        )
        & (
            snapshots["max_adverse_r"].to_numpy(dtype=float)
            >= float(policy["minimum_max_adverse_r"])
        )
        & (
            snapshots["recent_15m_r"].to_numpy(dtype=float)
            <= float(policy["maximum_recent_15m_r"])
        )
    )


def annual_utility_predictions(
    training_snapshots: pd.DataFrame,
    target_snapshots: pd.DataFrame,
    config: Mapping[str, Any],
    feature_config: Mapping[str, Any],
    v3: ModuleType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = config["walk_forward"]
    quantile = float(config["model"]["quantile"])
    prediction_frames: list[pd.DataFrame] = []
    logs: list[dict[str, Any]] = []
    for year in settings["target_years"]:
        year = int(year)
        train = v3.annual_training_split(
            training_snapshots, year, float(settings["purge_hours"])
        )
        target = target_snapshots.loc[
            pd.to_datetime(target_snapshots["entry_time"], utc=True).dt.year.eq(year)
        ].copy()
        if len(train) < int(settings["minimum_training_rows"]):
            raise ValueError(f"Insufficient training snapshots for {year}: {len(train)}")
        if target.empty:
            raise ValueError(f"No frozen V1 target snapshots for {year}")
        train_target = benefit_r_target(train)
        target_actual = benefit_r_target(target)
        model = make_model(config)
        model.fit(
            v3.build_feature_matrix(train, feature_config),
            train_target,
            sample_weight=v3.decision_day_equal_weights(train),
        )
        score = model.predict(v3.build_feature_matrix(target, feature_config))
        target["actual_benefit_r"] = target_actual
        target["predicted_lower_benefit_r"] = score
        target["utility_exit_trigger"] = action_mask(target, score, config)
        prediction_frames.append(target)
        first = (
            target.loc[target["utility_exit_trigger"]]
            .sort_values(["source_trade_id", "checkpoint_minutes"], kind="mergesort")
            .drop_duplicates("source_trade_id", keep="first")
        )
        logs.append(
            {
                "target_year": year,
                "training_rows": int(len(train)),
                "training_last_original_exit_time": train[
                    "original_exit_time"
                ].max(),
                "training_target_mean_r": float(train_target.mean()),
                "training_target_q25_r": float(np.quantile(train_target, 0.25)),
                "target_rows": int(len(target)),
                "target_spearman": rank_correlation(target_actual, score),
                "target_pinball_loss": float(
                    mean_pinball_loss(target_actual, score, alpha=quantile)
                ),
                "target_score_mean_r": float(np.mean(score)),
                "target_score_max_r": float(np.max(score)),
                "first_action_trades": int(len(first)),
                "first_action_positive_benefit_share": (
                    float(first["benefit_usd"].gt(0.0).mean())
                    if len(first)
                    else 0.0
                ),
                "first_action_net_benefit_usd": float(first["benefit_usd"].sum()),
                "first_action_worst_benefit_usd": (
                    float(first["benefit_usd"].min()) if len(first) else 0.0
                ),
            }
        )
    predictions = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["entry_time", "source_trade_id", "checkpoint_minutes"],
        kind="mergesort",
    )
    return predictions.reset_index(drop=True), pd.DataFrame(logs)


def apply_first_utility_signal(
    selected_trades: pd.DataFrame,
    predictions: pd.DataFrame,
    v3: ModuleType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    compatible = predictions.copy()
    compatible["exit_trigger"] = compatible["utility_exit_trigger"]
    compatible["exit_probability"] = compatible["predicted_lower_benefit_r"]
    managed, actions = v3.apply_first_exit_signal(selected_trades, compatible)
    managed = managed.rename(
        columns={
            "management_probability": "management_lower_benefit_r",
        }
    )
    actions = actions.rename(
        columns={
            "management_probability": "management_lower_benefit_r",
        }
    )
    return managed, actions
