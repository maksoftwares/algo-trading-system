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
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
LANE_ROOT = Path(__file__).resolve().parents[1]
ARM_KEYS = (
    "A_COMPETING_UTILITY",
    "B_REGIME_COMPETING",
    "C_SEQUENCE_QUANTILE",
    "D_UNANIMOUS_ENSEMBLE",
)
ARM_PREFIXES = {
    "A_COMPETING_UTILITY": "arm_a",
    "B_REGIME_COMPETING": "arm_b",
    "C_SEQUENCE_QUANTILE": "arm_c",
    "D_UNANIMOUS_ENSEMBLE": "arm_d",
}


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


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sequence_feature_names(config: Mapping[str, Any]) -> list[str]:
    steps = int(config["arms"]["C_SEQUENCE_QUANTILE"]["sequence_steps"])
    return [
        *[f"path_return_step_{step:02d}" for step in range(1, steps + 1)],
        *[f"path_active_step_{step:02d}" for step in range(1, steps + 1)],
    ]


def attach_path_sequence_features(
    snapshots: pd.DataFrame,
    context: Mapping[str, Any],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    required = {
        "entry_time",
        "decision_time",
        "checkpoint_minutes",
        "entry_price",
        "risk_usd",
        "long",
    }
    missing = sorted(required.difference(snapshots.columns))
    if missing:
        raise ValueError(f"Sequence snapshots are missing columns: {missing}")
    settings = config["arms"]["C_SEQUENCE_QUANTILE"]
    steps = int(settings["sequence_steps"])
    bar_minutes = int(settings["bar_minutes"])
    if steps <= 0 or bar_minutes <= 0:
        raise ValueError("Sequence dimensions must be positive")

    cap = context["cap"]
    cap_t = np.asarray(context["cap_t"], dtype="datetime64[ns]")
    bid_close = cap["bid_close"].to_numpy(dtype=float)
    ask_close = cap["ask_close"].to_numpy(dtype=float)
    entry_np = (
        pd.to_datetime(snapshots["entry_time"], utc=True)
        .dt.tz_localize(None)
        .to_numpy(dtype="datetime64[ns]")
    )
    decision_np = (
        (
            pd.to_datetime(snapshots["decision_time"], utc=True)
            - pd.Timedelta(minutes=bar_minutes)
        )
        .dt.tz_localize(None)
        .to_numpy(dtype="datetime64[ns]")
    )
    entry_index = np.searchsorted(cap_t, entry_np)
    decision_index = np.searchsorted(cap_t, decision_np)
    safe_entry = np.clip(entry_index, 0, len(cap_t) - 1)
    safe_decision = np.clip(decision_index, 0, len(cap_t) - 1)
    if (
        (entry_index >= len(cap_t)).any()
        or (decision_index >= len(cap_t)).any()
        or (cap_t[safe_entry] != entry_np).any()
        or (cap_t[safe_decision] != decision_np).any()
    ):
        raise ValueError("Sequence timestamps do not align to frozen M5 bars")
    if (decision_index < entry_index).any():
        raise ValueError("Sequence decision precedes trade entry")

    long = snapshots["long"].astype(bool).to_numpy()
    sign = np.where(long, 1.0, -1.0)
    entry_price = pd.to_numeric(
        snapshots["entry_price"], errors="raise"
    ).to_numpy(dtype=float)
    risk = pd.to_numeric(snapshots["risk_usd"], errors="raise").to_numpy(
        dtype=float
    )
    if (risk <= 0.0).any():
        raise ValueError("Sequence snapshots contain non-positive risk")
    rows = len(snapshots)
    returns = np.zeros((rows, steps), dtype=np.float32)
    active = np.zeros((rows, steps), dtype=np.float32)

    for position in range(steps):
        index = decision_index - (steps - 1 - position)
        valid = index >= entry_index
        take = np.flatnonzero(valid)
        if not len(take):
            continue
        selected_index = index[take]
        current_mark = np.where(
            long[take],
            bid_close[selected_index],
            ask_close[selected_index],
        )
        first_bar = selected_index == entry_index[take]
        previous_index = np.maximum(selected_index - 1, 0)
        previous_mark = np.where(
            long[take],
            bid_close[previous_index],
            ask_close[previous_index],
        )
        previous_mark = np.where(first_bar, entry_price[take], previous_mark)
        returns[take, position] = (
            sign[take] * (current_mark - previous_mark) / risk[take]
        ).astype(np.float32)
        active[take, position] = 1.0

    expected_active = np.minimum(
        steps,
        pd.to_numeric(
            snapshots["checkpoint_minutes"], errors="raise"
        ).to_numpy(dtype=int)
        // bar_minutes,
    )
    observed_active = active.sum(axis=1).astype(int)
    if not np.array_equal(expected_active, observed_active):
        raise ValueError("Sequence activity masks do not match checkpoints")
    values = np.concatenate([returns, active], axis=1)
    if not np.isfinite(values).all():
        raise ValueError("Sequence features contain non-finite values")
    sequence = pd.DataFrame(
        values,
        columns=sequence_feature_names(config),
        index=snapshots.index,
    )
    return pd.concat([snapshots.copy(), sequence], axis=1)


def build_base_feature_matrix(
    snapshots: pd.DataFrame,
    v5_config: Mapping[str, Any],
    v3_config: Mapping[str, Any],
    v3: ModuleType,
    v5: ModuleType,
) -> pd.DataFrame:
    return v5.build_feature_matrix(snapshots, v3_config, v3, v5_config)


def build_sequence_feature_matrix(
    snapshots: pd.DataFrame,
    config: Mapping[str, Any],
    v5_config: Mapping[str, Any],
    v3_config: Mapping[str, Any],
    v3: ModuleType,
    v5: ModuleType,
) -> pd.DataFrame:
    base = build_base_feature_matrix(snapshots, v5_config, v3_config, v3, v5)
    names = sequence_feature_names(config)
    missing = sorted(set(names).difference(snapshots.columns))
    if missing:
        raise ValueError(f"Sequence feature columns are missing: {missing}")
    sequence = snapshots.loc[:, names].astype(float)
    frame = pd.concat([base, sequence], axis=1)
    if frame.columns.duplicated().any():
        raise ValueError("Duplicate sequence model feature names")
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("Sequence model matrix contains non-finite values")
    return frame


def make_classifier(config: Mapping[str, Any]) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(**dict(config["model_parameters"]))


def make_quantile_regressor(
    config: Mapping[str, Any], quantile: float
) -> HistGradientBoostingRegressor:
    parameters = dict(config["model_parameters"])
    parameters["loss"] = "quantile"
    parameters["quantile"] = float(quantile)
    return HistGradientBoostingRegressor(**parameters)


def competing_utility(
    probability: np.ndarray,
    benefit_magnitude: np.ndarray,
    sacrifice_magnitude: np.ndarray,
) -> np.ndarray:
    probability = np.asarray(probability, dtype=float)
    benefit = np.maximum(0.0, np.asarray(benefit_magnitude, dtype=float))
    sacrifice = np.maximum(0.0, np.asarray(sacrifice_magnitude, dtype=float))
    if not (
        len(probability) == len(benefit) == len(sacrifice)
        and np.isfinite(probability).all()
        and np.isfinite(benefit).all()
        and np.isfinite(sacrifice).all()
        and ((probability >= 0.0) & (probability <= 1.0)).all()
    ):
        raise ValueError("Invalid competing-outcome predictions")
    return probability * benefit - (1.0 - probability) * sacrifice


def fit_predict_hurdle(
    train_x: pd.DataFrame,
    train_target: np.ndarray,
    train_weight: np.ndarray,
    target_x: pd.DataFrame,
    settings: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, np.ndarray]:
    target = np.asarray(train_target, dtype=float)
    weights = np.asarray(train_weight, dtype=float)
    beneficial = target > 0.0
    harmful = target < 0.0
    minimum = int(settings["minimum_conditional_rows"])
    if beneficial.sum() < minimum or harmful.sum() < minimum:
        raise ValueError(
            "Insufficient conditional rows for competing-outcome model: "
            f"{beneficial.sum()} beneficial, {harmful.sum()} harmful"
        )
    classifier = make_classifier(config)
    classifier.fit(train_x, beneficial.astype(int), sample_weight=weights)
    benefit_model = make_quantile_regressor(
        config, float(settings["benefit_quantile"])
    )
    benefit_model.fit(
        train_x.loc[beneficial],
        target[beneficial],
        sample_weight=weights[beneficial],
    )
    sacrifice_model = make_quantile_regressor(
        config, float(settings["sacrifice_quantile"])
    )
    sacrifice_model.fit(
        train_x.loc[harmful],
        -target[harmful],
        sample_weight=weights[harmful],
    )
    probability = classifier.predict_proba(target_x)[:, 1]
    benefit = benefit_model.predict(target_x)
    sacrifice = sacrifice_model.predict(target_x)
    return {
        "probability": probability,
        "benefit_magnitude": np.maximum(0.0, benefit),
        "sacrifice_magnitude": np.maximum(0.0, sacrifice),
        "score": competing_utility(probability, benefit, sacrifice),
    }


def fit_predict_regime_hurdle(
    train: pd.DataFrame,
    target: pd.DataFrame,
    train_x: pd.DataFrame,
    train_target: np.ndarray,
    train_weight: np.ndarray,
    target_x: pd.DataFrame,
    settings: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    group_column = str(settings["group_column"])
    if group_column not in train or group_column not in target:
        raise ValueError(f"Missing regime group column: {group_column}")
    groups = sorted(target[group_column].astype(str).unique())
    output = {
        "probability": np.full(len(target), np.nan, dtype=float),
        "benefit_magnitude": np.full(len(target), np.nan, dtype=float),
        "sacrifice_magnitude": np.full(len(target), np.nan, dtype=float),
        "score": np.full(len(target), np.nan, dtype=float),
    }
    counts: dict[str, int] = {}
    train_group = train[group_column].astype(str).to_numpy()
    target_group = target[group_column].astype(str).to_numpy()
    for group in groups:
        train_mask = train_group == group
        target_mask = target_group == group
        rows = int(train_mask.sum())
        counts[group] = rows
        if rows < int(settings["minimum_group_training_rows"]):
            raise ValueError(f"Insufficient {group} training rows: {rows}")
        prediction = fit_predict_hurdle(
            train_x.loc[train_mask],
            train_target[train_mask],
            train_weight[train_mask],
            target_x.loc[target_mask],
            settings,
            config,
        )
        for name, values in prediction.items():
            output[name][target_mask] = values
    if any(not np.isfinite(values).all() for values in output.values()):
        raise ValueError("Regime competing model left unscored target rows")
    return output, counts


def apply_action_policy(
    snapshots: pd.DataFrame,
    score: np.ndarray,
    config: Mapping[str, Any],
) -> np.ndarray:
    policy = config["action_policy"]
    values = np.asarray(score, dtype=float)
    if len(values) != len(snapshots) or not np.isfinite(values).all():
        raise ValueError("Invalid action-policy score")
    return (
        (values >= float(policy["minimum_predicted_lower_benefit_r"]))
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


def unanimous_trigger(
    triggers: list[np.ndarray],
    minimum_agreeing_members: int,
) -> np.ndarray:
    if not triggers:
        raise ValueError("Ensemble requires at least one member")
    arrays = [np.asarray(values, dtype=bool) for values in triggers]
    lengths = {len(values) for values in arrays}
    minimum = int(minimum_agreeing_members)
    if len(lengths) != 1 or minimum <= 0 or minimum > len(arrays):
        raise ValueError("Invalid ensemble trigger contract")
    return np.stack(arrays, axis=1).sum(axis=1) >= minimum


def _append_arm_log(
    logs: list[dict[str, Any]],
    target: pd.DataFrame,
    target_actual: np.ndarray,
    arm: str,
    year: int,
    training_rows: int,
    score: np.ndarray,
    trigger: np.ndarray,
    v4: ModuleType,
    detail: Mapping[str, Any] | None = None,
) -> None:
    first = (
        target.loc[trigger]
        .assign(_score=np.asarray(score, dtype=float)[trigger])
        .sort_values(["source_trade_id", "checkpoint_minutes"], kind="mergesort")
        .drop_duplicates("source_trade_id", keep="first")
    )
    row: dict[str, Any] = {
        "arm": arm,
        "target_year": int(year),
        "training_rows": int(training_rows),
        "target_rows": int(len(target)),
        "target_spearman": v4.rank_correlation(target_actual, score),
        "target_mae_r": float(
            np.mean(np.abs(np.asarray(score, dtype=float) - target_actual))
        ),
        "target_score_mean_r": float(np.mean(score)),
        "target_score_max_r": float(np.max(score)),
        "first_action_trades": int(len(first)),
        "first_action_positive_benefit_share": (
            float(first["benefit_usd"].gt(0.0).mean()) if len(first) else 0.0
        ),
        "first_action_net_benefit_usd": float(first["benefit_usd"].sum()),
        "first_action_worst_benefit_usd": (
            float(first["benefit_usd"].min()) if len(first) else 0.0
        ),
    }
    if detail:
        row["model_detail"] = json.dumps(detail, sort_keys=True)
    else:
        row["model_detail"] = "{}"
    logs.append(row)


def annual_four_arm_predictions(
    training_snapshots: pd.DataFrame,
    target_snapshots: pd.DataFrame,
    config: Mapping[str, Any],
    v5_config: Mapping[str, Any],
    v3_config: Mapping[str, Any],
    v3: ModuleType,
    v4: ModuleType,
    v5: ModuleType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = config["walk_forward"]
    prediction_frames: list[pd.DataFrame] = []
    logs: list[dict[str, Any]] = []
    for raw_year in settings["target_years"]:
        year = int(raw_year)
        train = v3.annual_training_split(
            training_snapshots, year, float(settings["purge_hours"])
        )
        target = target_snapshots.loc[
            pd.to_datetime(target_snapshots["entry_time"], utc=True).dt.year.eq(year)
        ].copy()
        if len(train) < int(settings["minimum_training_rows"]):
            raise ValueError(f"Insufficient annual training rows for {year}")
        if target.empty:
            raise ValueError(f"No target snapshots for {year}")
        train_target = v4.benefit_r_target(train)
        target_actual = v4.benefit_r_target(target)
        train_weight = v3.decision_day_equal_weights(train)
        train_base = build_base_feature_matrix(
            train, v5_config, v3_config, v3, v5
        )
        target_base = build_base_feature_matrix(
            target, v5_config, v3_config, v3, v5
        )

        arm_a = fit_predict_hurdle(
            train_base,
            train_target,
            train_weight,
            target_base,
            config["arms"]["A_COMPETING_UTILITY"],
            config,
        )
        arm_a_trigger = apply_action_policy(target, arm_a["score"], config)

        arm_b, regime_counts = fit_predict_regime_hurdle(
            train,
            target,
            train_base,
            train_target,
            train_weight,
            target_base,
            config["arms"]["B_REGIME_COMPETING"],
            config,
        )
        arm_b_trigger = apply_action_policy(target, arm_b["score"], config)

        train_sequence = build_sequence_feature_matrix(
            train, config, v5_config, v3_config, v3, v5
        )
        target_sequence = build_sequence_feature_matrix(
            target, config, v5_config, v3_config, v3, v5
        )
        arm_c_model = make_quantile_regressor(
            config, float(config["arms"]["C_SEQUENCE_QUANTILE"]["quantile"])
        )
        arm_c_model.fit(
            train_sequence,
            train_target,
            sample_weight=train_weight,
        )
        arm_c_score = arm_c_model.predict(target_sequence)
        arm_c_trigger = apply_action_policy(target, arm_c_score, config)

        arm_d_score = np.minimum.reduce(
            [arm_a["score"], arm_b["score"], arm_c_score]
        )
        arm_d_trigger = unanimous_trigger(
            [arm_a_trigger, arm_b_trigger, arm_c_trigger],
            int(
                config["arms"]["D_UNANIMOUS_ENSEMBLE"][
                    "minimum_agreeing_members"
                ]
            ),
        )

        target["actual_benefit_r"] = target_actual
        for prefix, prediction, trigger in (
            ("arm_a", arm_a, arm_a_trigger),
            ("arm_b", arm_b, arm_b_trigger),
        ):
            target[f"{prefix}_probability"] = prediction["probability"]
            target[f"{prefix}_benefit_magnitude_r"] = prediction[
                "benefit_magnitude"
            ]
            target[f"{prefix}_sacrifice_magnitude_r"] = prediction[
                "sacrifice_magnitude"
            ]
            target[f"{prefix}_score_r"] = prediction["score"]
            target[f"{prefix}_trigger"] = trigger
        target["arm_c_score_r"] = arm_c_score
        target["arm_c_trigger"] = arm_c_trigger
        target["arm_d_score_r"] = arm_d_score
        target["arm_d_trigger"] = arm_d_trigger
        prediction_frames.append(target)

        _append_arm_log(
            logs,
            target,
            target_actual,
            "A_COMPETING_UTILITY",
            year,
            len(train),
            arm_a["score"],
            arm_a_trigger,
            v4,
        )
        _append_arm_log(
            logs,
            target,
            target_actual,
            "B_REGIME_COMPETING",
            year,
            len(train),
            arm_b["score"],
            arm_b_trigger,
            v4,
            {"regime_training_rows": regime_counts},
        )
        _append_arm_log(
            logs,
            target,
            target_actual,
            "C_SEQUENCE_QUANTILE",
            year,
            len(train),
            arm_c_score,
            arm_c_trigger,
            v4,
        )
        _append_arm_log(
            logs,
            target,
            target_actual,
            "D_UNANIMOUS_ENSEMBLE",
            year,
            len(train),
            arm_d_score,
            arm_d_trigger,
            v4,
        )
    predictions = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["entry_time", "source_trade_id", "checkpoint_minutes"],
        kind="mergesort",
    )
    return predictions.reset_index(drop=True), pd.DataFrame(logs)


def arm_score_column(arm: str) -> str:
    return f"{ARM_PREFIXES[arm]}_score_r"


def arm_trigger_column(arm: str) -> str:
    return f"{ARM_PREFIXES[arm]}_trigger"


def apply_arm_first_signal(
    selected_trades: pd.DataFrame,
    predictions: pd.DataFrame,
    arm: str,
    v3: ModuleType,
    v4: ModuleType,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    compatible = predictions.copy()
    compatible["utility_exit_trigger"] = compatible[arm_trigger_column(arm)]
    compatible["predicted_lower_benefit_r"] = compatible[arm_score_column(arm)]
    return v4.apply_first_utility_signal(selected_trades, compatible, v3)
