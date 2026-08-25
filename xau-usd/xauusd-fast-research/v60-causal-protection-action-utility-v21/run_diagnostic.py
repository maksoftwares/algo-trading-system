from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "diagnostic.json"
OUTPUTS = ROOT / "outputs"
sys.path.insert(0, str(ROOT))

from src.scenario import (
    CATEGORICAL_FEATURES,
    FORBIDDEN_MODEL_FIELDS,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    observational_challenger_class,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_config(path: Path = CONFIG) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    for name, item in config["inputs"].items():
        actual = sha256_file(resolve(str(item["path"])))
        if actual != str(item["sha256"]):
            raise ValueError(f"Input identity changed: {name}: {actual}")
    if set(MODEL_FEATURES).intersection(FORBIDDEN_MODEL_FIELDS):
        raise ValueError("Forbidden field entered the fixed model feature list")
    return config


def feature_map(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if frame["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger has duplicate trade IDs")
    return {str(row["trade_id"]): row for row in frame.to_dict("records")}


def close_path(scenario: Any) -> list[dict[str, Any]]:
    return [
        {
            "trade_id": str(row["trade_id"]),
            "source_id": str(row["source_id"]),
            "timestamp_utc": str(row["timestamp_utc"]),
            "reason": str(row["reason"]),
            "pnl_usd": float(row["pnl_usd"]),
            "counted_by_v60": bool(row["counted_by_v60"]),
        }
        for row in scenario.event_rows
        if row["event"] == "POSITION_CLOSED"
    ]


def reference_metric_parity(
    observed: Mapping[str, Any], frozen: Mapping[str, Any]
) -> dict[str, bool]:
    keys = (
        "trades_closed",
        "net_pnl_usd",
        "profit_factor",
        "win_rate",
        "maximum_lifetime_closed_drawdown_usd",
        "maximum_lifetime_equity_drawdown_usd",
        "open_positions_at_end",
        "flat_suspended_deadlock",
        "floating_peak_deadlock",
    )
    result: dict[str, bool] = {}
    for key in keys:
        left = observed[key]
        right = frozen[key]
        if isinstance(left, (int, float)) and not isinstance(left, bool):
            result[key] = bool(
                math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-9)
            )
        else:
            result[key] = left == right
    return result


def make_preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, list(NUMERIC_FEATURES)),
            ("categorical", categorical, list(CATEGORICAL_FEATURES)),
        ],
        remainder="drop",
    )


def fit_predict_folds(
    snapshots: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    predictions: list[pd.DataFrame] = []
    metrics: list[dict[str, Any]] = []
    for fold in config["folds"]:
        train_end = int(fold["train_year_end"])
        evaluation_year = int(fold["evaluation_year"])
        train = snapshots.loc[snapshots["action_year"].le(train_end)].copy()
        test = snapshots.loc[snapshots["action_year"].eq(evaluation_year)].copy()
        if train.empty or test.empty:
            raise ValueError(f"Empty fixed fold: {fold['fold']}")
        if set(train["action_id"]).intersection(set(test["action_id"])):
            raise ValueError(f"Protection action crossed fold boundary: {fold['fold']}")
        preprocessor = make_preprocessor()
        x_train = preprocessor.fit_transform(train[list(MODEL_FEATURES)])
        x_test = preprocessor.transform(test[list(MODEL_FEATURES)])
        model = Ridge(
            alpha=float(config["model"]["alpha"]),
            fit_intercept=bool(config["model"]["fit_intercept"]),
        )
        train_weight = train["action_sample_weight"].to_numpy(dtype=float)
        model.fit(
            x_train,
            train["keep_open_utility_r"].to_numpy(dtype=float),
            sample_weight=train_weight,
        )
        predicted = model.predict(x_test)
        test["fold"] = str(fold["fold"])
        test["predicted_keep_open_utility_r"] = predicted
        test["nominated_skip"] = predicted > float(
            config["model"]["prediction_threshold_exclusive"]
        )
        predictions.append(test)
        weight = test["action_sample_weight"].to_numpy(dtype=float)
        actual = test["keep_open_utility_r"].to_numpy(dtype=float)
        predicted_rank = pd.Series(predicted).rank(method="average")
        actual_rank = pd.Series(actual).rank(method="average")
        rank_correlation = predicted_rank.corr(actual_rank)
        metrics.append(
            {
                "fold": str(fold["fold"]),
                "train_year_end": train_end,
                "evaluation_year": evaluation_year,
                "train_rows": len(train),
                "train_actions": int(train["action_id"].nunique()),
                "evaluation_rows": len(test),
                "evaluation_actions": int(test["action_id"].nunique()),
                "nominated_rows": int(test["nominated_skip"].sum()),
                "nominated_actions": int(
                    test.loc[test["nominated_skip"], "action_id"].nunique()
                ),
                "weighted_mae": float(
                    mean_absolute_error(actual, predicted, sample_weight=weight)
                ),
                "weighted_r2": float(r2_score(actual, predicted, sample_weight=weight)),
                "rank_correlation": (
                    None if pd.isna(rank_correlation) else float(rank_correlation)
                ),
            }
        )
    return pd.concat(predictions, ignore_index=True), pd.DataFrame(metrics)


def action_utility_table(predictions: pd.DataFrame) -> pd.DataFrame:
    selected = predictions.loc[predictions["nominated_skip"]].copy()
    rows: list[dict[str, Any]] = []
    for (fold, year, action_id), group in selected.groupby(
        ["fold", "action_year", "action_id"], sort=True
    ):
        weight = group["action_sample_weight"].to_numpy(dtype=float)
        utility = group["keep_open_utility_r"].to_numpy(dtype=float)
        rows.append(
            {
                "fold": str(fold),
                "action_year": int(year),
                "action_id": str(action_id),
                "nominated_rows": len(group),
                "positions_in_action": int(group["positions_in_action"].iloc[0]),
                "nominated_weight": float(weight.sum()),
                "action_mean_nominated_utility_r": float(
                    np.average(utility, weights=weight)
                ),
            }
        )
    return pd.DataFrame(rows)


def cluster_bootstrap(
    actions: pd.DataFrame, *, seed: int, resamples: int, percentile: float
) -> dict[str, Any]:
    if actions.empty:
        return {
            "seed": seed,
            "resamples": resamples,
            "percentile": percentile,
            "mean_utility_r": None,
            "percentile_utility_r": None,
        }
    rng = np.random.default_rng(seed)
    total_actions = len(actions)
    sampled_sum = np.zeros(resamples, dtype=float)
    for _, group in actions.groupby("action_year", sort=True):
        values = group["action_mean_nominated_utility_r"].to_numpy(dtype=float)
        indices = rng.integers(0, len(values), size=(resamples, len(values)))
        sampled_sum += values[indices].sum(axis=1)
    sampled_mean = sampled_sum / total_actions
    return {
        "seed": int(seed),
        "resamples": int(resamples),
        "percentile": float(percentile),
        "mean_utility_r": float(actions["action_mean_nominated_utility_r"].mean()),
        "percentile_utility_r": float(np.percentile(sampled_mean, percentile)),
    }


def markdown(result: Mapping[str, Any]) -> str:
    lines = [
        f"# {result['report_title']} Result",
        "",
        f"Decision: **{result['decision']}**",
        "",
        "Read-only exposed diagnostic. No broker or deployment action is authorized.",
        "",
        "## Parity",
        "",
        f"- Reference Dynamic V6 trades: `{result['reference_v6']['trades_closed']}`",
        f"- Observed giveback rows: `{result['snapshot_audit']['rows']}`",
        f"- Distinct protection actions: `{result['snapshot_audit']['actions']}`",
        f"- Exact event path: `{'PASS' if result['parity']['full_event_rows_exact'] else 'FAIL'}`",
        f"- Exact close path: `{'PASS' if result['parity']['close_path_exact'] else 'FAIL'}`",
        f"- Exact V6 metrics: `{'PASS' if result['parity']['all_metric_identity'] else 'FAIL'}`",
        "",
        "## Out-of-time diagnostic",
        "",
        f"- Nominated rows: `{result['diagnostic']['nominated_rows']}`",
        f"- Nominated actions: `{result['diagnostic']['nominated_actions']}`",
        f"- Positive utility folds: `{result['diagnostic']['positive_utility_folds']}/4`",
        f"- Combined action utility R: `{result['diagnostic']['combined_action_utility_r']:.6f}`",
        f"- Cluster-bootstrap 10th percentile: `{result['diagnostic']['bootstrap']['percentile_utility_r']}`",
        "",
        "## Gates",
        "",
    ]
    lines.extend(
        f"- `{name}`: {'PASS' if value else 'FAIL'}"
        for name, value in result["gates"].items()
    )
    lines.extend(
        [
            "",
            "A pass only nominates a separately preregistered path-dependent replay. It does not prove portfolio P/L improvement and cannot authorize deployment.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = load_config()
    v17 = json.loads(resolve(config["inputs"]["v17_result"]["path"]).read_text())
    if v17["decision"] != "DIAGNOSTIC_SUPPORTS_TARGETED_PROTECTION_RESEARCH":
        raise ValueError("V17 no longer supports this fixed diagnostic")
    v6_config = json.loads(
        resolve(config["inputs"]["v6_config"]["path"]).read_text(encoding="utf-8")
    )
    v6_result = json.loads(
        resolve(config["inputs"]["v6_result"]["path"]).read_text(encoding="utf-8")
    )
    evaluator = load_module(
        "v21_shared_evaluator", resolve(config["inputs"]["shared_evaluator"]["path"])
    )
    v6_scenario = load_module(
        "v21_v6_scenario", resolve(config["inputs"]["v6_scenario"]["path"])
    )
    features = pd.read_parquet(
        resolve(v6_config["inputs"]["causal_feature_ledger"]["path"])
    )
    features_by_trade = feature_map(features)
    base = json.loads(
        resolve(v6_config["inputs"]["base_challenger_config"]["path"]).read_text()
    )

    with tempfile.TemporaryDirectory(prefix="v60-protection-utility-v21-") as temporary:
        replay_config = deepcopy(base)
        for name, value in v6_config.get("v2_policy_overrides", {}).items():
            if name not in replay_config["policy"]:
                raise ValueError(f"Unknown V2 policy override: {name}")
            replay_config["policy"][name] = value
        replay_path = Path(temporary) / "challenger.json"
        replay_path.write_text(json.dumps(replay_config), encoding="utf-8")
        replay = load_module(
            "v21_tick_replay",
            resolve(replay_config["inputs"]["replay_source"]["path"]),
        )
        contract = replay.load_json(
            resolve(replay_config["inputs"]["replay_contract"]["path"])
        )
        deployed = replay.load_json(
            resolve(replay_config["inputs"]["deployed_config"]["path"])
        )
        deployed = replay.apply_portfolio_protection(contract, deployed)
        deployed = replay.apply_runtime_risk_mode(
            deployed,
            bool(
                contract["evaluation"].get(
                    "required_equity_fraction_limits_enabled", False
                )
            ),
        )
        candidates, population = replay.load_candidates(contract, deployed)
        cache_meta = replay.prepare_quote_cache(
            contract, candidates, population, force=False
        )
        quotes = replay.load_quote_cache(cache_meta)
        spec = next(
            item
            for item in replay.scenario_specs(contract)
            if item.scenario_id == "deployed__full_runtime"
        )
        rank_map = evaluator.load_rank_map(
            resolve(replay_config["inputs"]["causal_rank_ledger"]["path"])
        )
        reference_type = v6_scenario.combined_challenger_class(
            replay, evaluator, features_by_trade, v6_config["anti_chase"]
        )
        print("Running frozen Dynamic V6 reference replay...", flush=True)
        reference = reference_type(
            spec,
            deployed,
            contract,
            candidates,
            rank_map=rank_map,
            policy=replay_config["policy"],
        )
        reference_metrics = reference.simulate(quotes)
        sink: list[Any] = []
        observed_type = observational_challenger_class(
            replay,
            evaluator,
            v6_scenario,
            features_by_trade,
            v6_config["anti_chase"],
            sink,
        )
        print("Running observational Dynamic V6 parity replay...", flush=True)
        observed = observed_type(
            spec,
            deployed,
            contract,
            candidates,
            rank_map=rank_map,
            policy=replay_config["policy"],
        )
        observed_metrics = observed.simulate(quotes)
        if sink != [observed]:
            raise ValueError("Observational instance capture failed")

    reference_closes = close_path(reference)
    observed_closes = close_path(observed)
    frozen_metric_identity = reference_metric_parity(
        reference_metrics, v6_result["challenger"]
    )
    parity = {
        "simulation_result_exact": reference_metrics == observed_metrics,
        "full_event_rows_exact": reference.event_rows == observed.event_rows,
        "close_path_exact": reference_closes == observed_closes,
        "veto_audit_exact": reference.veto_audit == observed.veto_audit,
        "frozen_v6_metric_identity": frozen_metric_identity,
        "all_metric_identity": bool(all(frozen_metric_identity.values())),
        "no_open_positions": int(observed_metrics["open_positions_at_end"]) == 0,
        "no_flat_deadlock": not bool(observed_metrics["flat_suspended_deadlock"]),
        "no_floating_deadlock": not bool(observed_metrics["floating_peak_deadlock"]),
    }
    parity_pass = bool(
        all(
            value for key, value in parity.items() if key != "frozen_v6_metric_identity"
        )
        and all(frozen_metric_identity.values())
    )
    snapshots = pd.DataFrame(observed.protection_action_snapshots)
    if snapshots.empty:
        raise ValueError("Observational replay captured no protection actions")
    if snapshots["trade_id"].duplicated().any():
        raise ValueError("A trade appeared in more than one protection action")
    if len(snapshots) != int(observed_metrics["profit_giveback_closes"]):
        raise ValueError("Snapshot rows do not equal frozen giveback close count")
    if not parity_pass:
        raise ValueError("Observational replay failed exact Dynamic V6 parity")

    predictions, fold_metrics = fit_predict_folds(snapshots, config)
    actions = action_utility_table(predictions)
    acceptance = config["acceptance"]
    bootstrap = cluster_bootstrap(
        actions,
        seed=int(acceptance["bootstrap_seed"]),
        resamples=int(acceptance["bootstrap_resamples"]),
        percentile=float(acceptance["bootstrap_percentile"]),
    )
    annual_utility = {
        int(year): float(group["action_mean_nominated_utility_r"].sum())
        for year, group in actions.groupby("action_year", sort=True)
    }
    positive_folds = sum(value > 0.0 for value in annual_utility.values())
    combined_utility = float(actions["action_mean_nominated_utility_r"].sum())
    positive_actions = actions.loc[
        actions["action_mean_nominated_utility_r"].gt(0.0),
        "action_mean_nominated_utility_r",
    ]
    positive_total = float(positive_actions.sum())
    maximum_positive_share = (
        float(positive_actions.max() / positive_total)
        if positive_total > 0.0 and len(positive_actions)
        else None
    )
    actions_per_fold = actions.groupby("fold")["action_id"].nunique().to_dict()
    gates = {
        "exact_dynamic_v6_behavioral_parity": parity_pass,
        "causal_feature_contract": not bool(
            set(MODEL_FEATURES).intersection(FORBIDDEN_MODEL_FIELDS)
        ),
        "all_four_fixed_evaluation_years": set(predictions["action_year"].astype(int))
        == {2023, 2024, 2025, 2026},
        "minimum_nominated_rows": int(predictions["nominated_skip"].sum())
        >= int(acceptance["minimum_nominated_rows"]),
        "minimum_nominated_actions": len(actions)
        >= int(acceptance["minimum_nominated_actions"]),
        "minimum_actions_every_fold": all(
            int(actions_per_fold.get(str(fold["fold"]), 0))
            >= int(acceptance["minimum_nominated_actions_per_fold"])
            for fold in config["folds"]
        ),
        "positive_utility_in_three_of_four_folds": positive_folds
        >= int(acceptance["minimum_positive_utility_folds"]),
        "nonnegative_2025_utility": annual_utility.get(2025, float("-inf")) >= 0.0,
        "nonnegative_2026_utility": annual_utility.get(2026, float("-inf")) >= 0.0,
        "combined_utility_positive": combined_utility > 0.0,
        "single_action_concentration_below_limit": maximum_positive_share is not None
        and maximum_positive_share
        < float(acceptance["maximum_single_action_positive_utility_share_exclusive"]),
        "cluster_bootstrap_tenth_percentile_positive": bootstrap["percentile_utility_r"]
        is not None
        and float(bootstrap["percentile_utility_r"]) > 0.0,
    }
    passed = bool(all(gates.values()))
    result = {
        "schema_version": config["schema_version"] + "_result",
        "report_title": config["report_title"],
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "decision": (
            "DIAGNOSTIC_NOMINATES_PATH_DEPENDENT_V22"
            if passed
            else "NO_STABLE_PROTECTION_UTILITY_KEEP_V6"
        ),
        "authorization": config["authorization"],
        "deployment_authorized": False,
        "broker_action_authorized": False,
        "evidence_status": config["evidence_status"],
        "input_sha256": {
            name: str(item["sha256"]) for name, item in config["inputs"].items()
        },
        "implementation_sha256": {
            "runner": sha256_file(Path(__file__)),
            "scenario": sha256_file(ROOT / "src" / "scenario.py"),
        },
        "reference_v6": reference_metrics,
        "parity": parity,
        "parity_hashes": {
            "reference_events": canonical_sha256(reference.event_rows),
            "observed_events": canonical_sha256(observed.event_rows),
            "reference_closes": canonical_sha256(reference_closes),
            "observed_closes": canonical_sha256(observed_closes),
            "reference_veto_audit": canonical_sha256(reference.veto_audit),
            "observed_veto_audit": canonical_sha256(observed.veto_audit),
        },
        "snapshot_audit": {
            "rows": len(snapshots),
            "actions": int(snapshots["action_id"].nunique()),
            "years": {
                str(year): {
                    "rows": len(group),
                    "actions": int(group["action_id"].nunique()),
                }
                for year, group in snapshots.groupby("action_year", sort=True)
            },
            "giveback_close_rows": int(observed_metrics["profit_giveback_closes"]),
        },
        "model": config["model"],
        "features": {
            "categorical": list(CATEGORICAL_FEATURES),
            "numeric": list(NUMERIC_FEATURES),
            "forbidden": sorted(FORBIDDEN_MODEL_FIELDS),
        },
        "folds": fold_metrics.to_dict("records"),
        "diagnostic": {
            "nominated_rows": int(predictions["nominated_skip"].sum()),
            "nominated_actions": len(actions),
            "actions_per_fold": {
                str(key): int(value) for key, value in actions_per_fold.items()
            },
            "annual_action_utility_r": {
                str(year): value for year, value in annual_utility.items()
            },
            "positive_utility_folds": int(positive_folds),
            "combined_action_utility_r": combined_utility,
            "maximum_single_positive_action_share": maximum_positive_share,
            "bootstrap": bootstrap,
        },
        "gates": gates,
        "limitations": [
            "All protection outcomes were exposed before V21 was nominated.",
            "Annual folds are pseudo-out-of-time and do not undo research multiplicity.",
            "Source endpoints are labels only and ignore path-dependent replacement capacity.",
            "A pass only nominates V22; clean Capital.com prospective evidence remains mandatory.",
            "V60 remains the only broker-action policy.",
        ],
    }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    snapshots.to_csv(OUTPUTS / "ACTION_SNAPSHOTS.csv", index=False)
    predictions.to_csv(OUTPUTS / "OOT_PREDICTIONS.csv", index=False)
    fold_metrics.to_csv(OUTPUTS / "FOLD_METRICS.csv", index=False)
    actions.to_csv(OUTPUTS / "ACTION_UTILITY.csv", index=False)
    (OUTPUTS / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (OUTPUTS / "RESULT.md").write_text(markdown(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "snapshot_audit": result["snapshot_audit"],
                "diagnostic": result["diagnostic"],
                "failed_gates": [name for name, value in gates.items() if not value],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
