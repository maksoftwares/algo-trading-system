from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score


REPO_ROOT = Path(__file__).resolve().parents[4]
LANE_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_FEATURE_TOKENS = (
    "exit",
    "return",
    "pnl",
    "label",
    "winner",
    "target",
    "holding",
    "future",
    "rc",
    "rmid",
)


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


def validate_feature_contract(config: Mapping[str, Any]) -> list[str]:
    names = (
        list(config["features"]["numeric"])
        + list(config["features"]["derived"])
        + [f"regime_{value}" for value in config["features"]["regimes"]]
    )
    invalid = [
        name
        for name in names
        if any(token in name.lower() for token in FORBIDDEN_FEATURE_TOKENS)
    ]
    if invalid:
        raise ValueError(f"Outcome-derived feature names are forbidden: {invalid}")
    if len(names) != len(set(names)):
        raise ValueError("Duplicate ML feature names")
    return names


def build_feature_matrix(
    trades: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    expected = {
        "scan_time",
        "long",
        "stop",
        "regime",
        *config["features"]["numeric"],
    }
    expected.discard("log_stop")
    missing = sorted(expected.difference(trades.columns))
    if missing:
        raise ValueError(f"Feature input is missing columns: {missing}")
    frame = pd.DataFrame(index=trades.index)
    for name in config["features"]["numeric"]:
        if name == "log_stop":
            values = np.log1p(pd.to_numeric(trades["stop"], errors="raise"))
        else:
            values = pd.to_numeric(trades[name], errors="raise")
        frame[name] = values.astype(float)
    scan_time = pd.to_datetime(trades["scan_time"], utc=True)
    minute = scan_time.dt.hour * 60 + scan_time.dt.minute
    angle = 2.0 * math.pi * minute / 1440.0
    frame["direction_long"] = trades["long"].astype(bool).astype(float)
    frame["utc_time_sin"] = np.sin(angle)
    frame["utc_time_cos"] = np.cos(angle)
    regimes = trades["regime"].astype(str)
    allowed = set(config["features"]["regimes"])
    unknown = sorted(set(regimes).difference(allowed))
    if unknown:
        raise ValueError(f"Unexpected regime classes: {unknown}")
    for regime in config["features"]["regimes"]:
        frame[f"regime_{regime}"] = regimes.eq(regime).astype(float)
    ordered = validate_feature_contract(config)
    frame = frame.loc[:, ordered]
    values = frame.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("ML feature matrix contains non-finite values")
    return frame


def day_equal_sample_weights(trades: pd.DataFrame) -> np.ndarray:
    days = pd.to_datetime(trades["scan_time"], utc=True).dt.floor("D")
    counts = days.map(days.value_counts()).to_numpy(dtype=float)
    weights = 1.0 / counts
    return weights / weights.mean()


def annual_split(
    corpus: pd.DataFrame, target_year: int, purge_hours: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_start = pd.Timestamp(f"{target_year}-01-01", tz="UTC")
    calibration_start = pd.Timestamp(f"{target_year - 1}-01-01", tz="UTC")
    purge = pd.Timedelta(hours=purge_hours)
    train = corpus.loc[
        corpus["exit_time"].lt(calibration_start - purge)
    ].copy()
    calibration = corpus.loc[
        corpus["entry_time"].ge(calibration_start)
        & corpus["entry_time"].lt(target_start)
        & corpus["exit_time"].lt(target_start - purge)
    ].copy()
    return train, calibration


def make_model(config: Mapping[str, Any]) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(**dict(config["model"]["parameters"]))


def probability_cutoff(
    calibration_probabilities: np.ndarray, retention_fraction: float
) -> float:
    values = np.asarray(calibration_probabilities, dtype=float)
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("Calibration probabilities are empty or non-finite")
    if not 0.0 < retention_fraction < 1.0:
        raise ValueError("Retention fraction must be between zero and one")
    return float(np.quantile(values, 1.0 - retention_fraction))


def safe_auc(labels: pd.Series | np.ndarray, probabilities: np.ndarray) -> float:
    target = np.asarray(labels, dtype=int)
    if len(np.unique(target)) < 2:
        return 0.5
    return float(roc_auc_score(target, probabilities))


def build_training_corpus(
    previous: ModuleType,
    previous_config: Mapping[str, Any],
    feature_config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    modules = previous.load_external_modules(previous_config)
    walk = modules["v6_walkforward"]
    context = modules["specialist"].load_context()
    candidates = walk.enumerate_pool("BOTH", "all", "ALL")
    if candidates is None or candidates.empty:
        raise ValueError("Broad V6 training population is empty")
    candidates = previous.add_capital_outcomes(
        candidates, context, float(modules["engine"].FEE)
    )
    candidates = candidates.loc[
        candidates["rc"].notna() & candidates["cap_exit_t"].notna()
    ].copy()
    candidates["scan_time"] = pd.to_datetime(candidates["dec_time"], utc=True)
    candidates["entry_time"] = pd.to_datetime(candidates["entry_t"], utc=True)
    candidates["exit_time"] = pd.to_datetime(candidates["cap_exit_t"], utc=True)
    candidates["regime"] = np.asarray(context["reg"])[
        candidates["i"].to_numpy(dtype=int)
    ]
    candidates["direction"] = np.where(candidates["long"], "LONG", "SHORT")
    risk = candidates["stop_usd"].to_numpy(dtype=float)
    holding_days = (
        (candidates["exit_time"] - candidates["entry_time"])
        .dt.total_seconds()
        .to_numpy()
        / 86400.0
    )
    stress = previous_config["execution_stress"]
    extra_cost = (
        float(stress["additional_fixed_cost_usd"])
        + float(stress["holding_cost_usd_per_24h"]) * holding_days
        + float(stress["slippage_r"]) * risk
    )
    candidates["fee_stress_pnl_usd"] = (
        candidates["rc"].to_numpy(dtype=float) * risk - extra_cost
    )
    candidates["label"] = candidates["fee_stress_pnl_usd"].gt(0.0).astype(int)
    if candidates.duplicated(["i", "long"]).any():
        raise ValueError("Broad training corpus contains duplicate signal identities")
    build_feature_matrix(candidates, feature_config)
    audit = {
        "rows": len(candidates),
        "first_entry_time": candidates["entry_time"].min().isoformat(),
        "last_entry_time": candidates["entry_time"].max().isoformat(),
        "positive_label_share": float(candidates["label"].mean()),
        "long_rows": int(candidates["long"].sum()),
        "short_rows": int((~candidates["long"]).sum()),
    }
    return candidates.reset_index(drop=True), audit


def attach_candidate_regimes(
    candidates: pd.DataFrame, context: Mapping[str, Any]
) -> pd.DataFrame:
    result = candidates.copy()
    result["scan_time"] = pd.to_datetime(result["scan_time"], utc=True)
    result["entry_time"] = pd.to_datetime(result["entry_time"], utc=True)
    result["exit_time"] = pd.to_datetime(result["exit_time"], utc=True)
    result["regime"] = np.asarray(context["reg"])[result["i"].to_numpy(dtype=int)]
    result["label"] = result["fee_stress_pnl_usd"].gt(0.0).astype(int)
    return result


def annual_walk_forward_predictions(
    corpus: pd.DataFrame,
    candidates: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = config["walk_forward"]
    prediction_frames: list[pd.DataFrame] = []
    logs: list[dict[str, Any]] = []
    for year in settings["target_years"]:
        train, calibration = annual_split(
            corpus, int(year), float(settings["purge_hours"])
        )
        target = candidates.loc[candidates["entry_time"].dt.year.eq(int(year))].copy()
        if len(train) < int(settings["minimum_training_rows"]):
            raise ValueError(f"Insufficient training rows for {year}: {len(train)}")
        if len(calibration) < int(settings["minimum_calibration_rows"]):
            raise ValueError(
                f"Insufficient calibration rows for {year}: {len(calibration)}"
            )
        if target.empty:
            raise ValueError(f"No frozen V6 candidates for target year {year}")
        model = make_model(config)
        train_x = build_feature_matrix(train, config)
        calibration_x = build_feature_matrix(calibration, config)
        target_x = build_feature_matrix(target, config)
        model.fit(
            train_x,
            train["label"].astype(int),
            sample_weight=day_equal_sample_weights(train),
        )
        calibration_probability = model.predict_proba(calibration_x)[:, 1]
        target_probability = model.predict_proba(target_x)[:, 1]
        cutoff = probability_cutoff(
            calibration_probability, float(settings["retention_fraction"])
        )
        target["ml_probability"] = target_probability
        target["ml_cutoff"] = cutoff
        target["ml_selected"] = target["ml_probability"].ge(cutoff)
        prediction_frames.append(target)
        logs.append(
            {
                "target_year": int(year),
                "training_rows": len(train),
                "training_last_exit_time": train["exit_time"].max(),
                "calibration_rows": len(calibration),
                "calibration_start_time": calibration["entry_time"].min(),
                "calibration_last_exit_time": calibration["exit_time"].max(),
                "calibration_auc": safe_auc(
                    calibration["label"], calibration_probability
                ),
                "calibration_brier": float(
                    brier_score_loss(calibration["label"], calibration_probability)
                ),
                "probability_cutoff": cutoff,
                "target_rows": len(target),
                "target_selected_rows": int(target["ml_selected"].sum()),
                "target_retained_share": float(target["ml_selected"].mean()),
                "target_auc": safe_auc(target["label"], target_probability),
                "target_brier": float(
                    brier_score_loss(target["label"], target_probability)
                ),
            }
        )
    predictions = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    )
    return predictions.reset_index(drop=True), pd.DataFrame(logs)


def profit_factor(values: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="raise").astype(float)
    gains = float(numeric[numeric > 0.0].sum())
    losses = float(-numeric[numeric < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = pd.to_numeric(values, errors="raise").astype(float).cumsum()
    if equity.empty:
        return 0.0
    return float((equity.cummax().clip(lower=0.0) - equity).max())


def trade_metrics(frame: pd.DataFrame, top_winners: int) -> dict[str, float]:
    ordered = frame.sort_values(["exit_time", "trade_id"], kind="mergesort")
    values = ordered["fee_stress_pnl_usd"].astype(float)
    removed = values.drop(values.nlargest(min(top_winners, len(values))).index)
    return {
        "trades": int(len(values)),
        "win_rate_pct": 100.0 * float(values.gt(0.0).mean()) if len(values) else 0.0,
        "stress_net_usd": float(values.sum()),
        "stress_profit_factor": profit_factor(values),
        "stress_closed_drawdown_usd": closed_drawdown(values),
        "winner_removed_stress_net_usd": float(removed.sum()),
    }


def window_comparison(
    baseline: pd.DataFrame,
    raw_addon: pd.DataFrame,
    ml_addon: pd.DataFrame,
    windows: Mapping[str, list[str]],
    config: Mapping[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    top = int(config["gates"]["top_winners_removed"])
    for name, bounds in windows.items():
        start, end = map(pd.Timestamp, bounds)

        def select(frame: pd.DataFrame) -> pd.DataFrame:
            return frame.loc[
                frame["entry_time"].ge(start) & frame["entry_time"].lt(end)
            ].copy()

        base = select(baseline)
        raw = select(raw_addon)
        ml = select(ml_addon)
        base_combined = base
        raw_combined = pd.concat([base, raw], ignore_index=True)
        ml_combined = pd.concat([base, ml], ignore_index=True)
        base_m = trade_metrics(base_combined, top)
        raw_m = trade_metrics(raw, top)
        ml_m = trade_metrics(ml, top)
        raw_combined_m = trade_metrics(raw_combined, top)
        ml_combined_m = trade_metrics(ml_combined, top)
        checks = {
            "minimum_ml_accepted_trades": ml_m["trades"]
            >= int(config["gates"]["minimum_ml_accepted_trades_per_window"]),
            "ml_v6_pf_no_worse_than_raw_v6": ml_m["stress_profit_factor"]
            >= raw_m["stress_profit_factor"],
            "ml_v6_drawdown_no_worse_than_raw_v6": ml_m[
                "stress_closed_drawdown_usd"
            ]
            <= raw_m["stress_closed_drawdown_usd"] + 1e-9,
            "ml_v6_winner_removed_positive": ml_m[
                "winner_removed_stress_net_usd"
            ]
            > 0.0,
            "ml_combined_incremental_net_positive": ml_combined_m[
                "stress_net_usd"
            ]
            - base_m["stress_net_usd"]
            > float(config["gates"]["minimum_incremental_stress_net_usd"]),
            "ml_combined_pf_no_worse_than_v60": ml_combined_m[
                "stress_profit_factor"
            ]
            >= base_m["stress_profit_factor"],
            "ml_combined_drawdown_no_worse_than_v60": ml_combined_m[
                "stress_closed_drawdown_usd"
            ]
            <= base_m["stress_closed_drawdown_usd"] + 1e-9,
        }
        row = {
            "window": name,
            **{f"v60_{key}": value for key, value in base_m.items()},
            **{f"raw_v6_{key}": value for key, value in raw_m.items()},
            **{f"ml_v6_{key}": value for key, value in ml_m.items()},
            **{
                f"raw_combined_{key}": value
                for key, value in raw_combined_m.items()
            },
            **{
                f"ml_combined_{key}": value
                for key, value in ml_combined_m.items()
            },
            "checks": checks,
            "passed": all(checks.values()),
        }
        rows.append(row)
    return pd.DataFrame(rows)
