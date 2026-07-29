from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "PROSPECTIVE_SERVING_V3.json"
LOCK_PATH = ROOT / "config" / "IMPLEMENTATION_LOCK.json"
OUTPUTS = ROOT / "outputs"
PNL = "fee_stress_pnl_usd"
BAR_WIDTH = pd.Timedelta(minutes=5)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_input(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_config(*, verify_lock: bool = True) -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for source in config["inputs"].values():
        path = resolve_input(str(source["path"]))
        actual = sha256_file(path)
        if actual != str(source["sha256"]):
            raise ValueError(f"Input identity changed: {path}: {actual}")
    if verify_lock:
        verify_implementation_lock()
    return config


def verify_implementation_lock() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if not bool(lock["locked_before_result"]):
        raise ValueError("Implementation was not locked before its result")
    for relative, expected in lock["files"].items():
        path = ROOT / relative
        if sha256_file(path) != expected:
            raise ValueError(f"Implementation identity changed: {path}")


def causal_rank(value: float, reference: np.ndarray) -> float:
    finite = np.sort(np.asarray(reference, dtype=float))
    if len(finite) == 0 or not np.isfinite(finite).all():
        raise ValueError("Rank reference is empty or non-finite")
    return float(np.searchsorted(finite, float(value), side="right") / len(finite))


def _load_research_population(
    config: Mapping[str, Any],
) -> tuple[ModuleType, dict[str, Any], pd.DataFrame, pd.DataFrame]:
    prior = load_module(
        "portable_v3_prior",
        resolve_input(str(config["inputs"]["causal_retest_source"]["path"])),
    )
    contract = json.loads(
        resolve_input(
            str(config["inputs"]["causal_retest_contract"]["path"])
        ).read_text(encoding="utf-8")
    )
    feature_module = prior.load_module("portable_v3_features", prior.FEATURES_PATH)
    cooldown_module = prior.load_module("portable_v3_cooldown", prior.COOLDOWN_PATH)
    ledger, _ = prior.load_current_population(contract, cooldown_module)
    full_X, meta, _ = prior.build_corrected_features(ledger, feature_module)
    X = full_X[list(config["feature_columns"])].copy()
    if X.isna().any().any() or not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError("Training feature matrix is not finite")
    return prior, contract, X, meta


def recreate_serving_bundle(
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], pd.DataFrame]:
    prior, contract, X, meta = _load_research_population(config)
    model_config = contract["model"]
    scores = np.full(len(X), np.nan)
    ranks = np.full(len(X), np.nan)
    history: list[float] = []
    rng = np.random.default_rng(int(config["model"]["primary_seed"]))
    purge = pd.Timedelta(hours=int(model_config["purge_hours"]))
    parameters = dict(model_config["parameters"])
    target_year = int(config["model"]["serving_year"])
    serving_models: list[HistGradientBoostingRegressor] = []
    target_train_reference: np.ndarray | None = None
    target_cutoff: pd.Timestamp | None = None

    for year in contract["population"]["test_entry_years"]:
        cutoff = pd.Timestamp(f"{year}-01-01", tz="UTC") - purge
        train = meta["exit_time"].lt(cutoff).to_numpy()
        test = meta["entry_time"].dt.year.eq(year).to_numpy()
        if (
            int(train.sum()) < int(model_config["minimum_train_rows"])
            or int(test.sum()) < 5
        ):
            continue
        X_train = X.loc[train]
        X_test = X.loc[test]
        pnl = meta.loc[train, PNL].to_numpy(dtype=float)
        target = np.clip(
            pnl,
            np.quantile(pnl, model_config["winsor_quantiles"][0]),
            np.quantile(pnl, model_config["winsor_quantiles"][1]),
        )
        test_score = np.zeros(int(test.sum()), dtype=float)
        train_score = np.zeros(int(train.sum()), dtype=float)
        annual_models: list[HistGradientBoostingRegressor] = []
        for _ in range(int(model_config["bags"])):
            sample = rng.integers(0, len(X_train), len(X_train))
            model = HistGradientBoostingRegressor(**parameters).fit(
                X_train.iloc[sample], target[sample]
            )
            test_score += model.predict(X_test)
            train_score += model.predict(X_train)
            annual_models.append(model)
        test_score /= int(model_config["bags"])
        train_score /= int(model_config["bags"])
        rank = prior.expanding_rank(
            test_score,
            train_score,
            history,
            int(contract["sizing"]["minimum_oos_history"]),
        )
        scores[test] = test_score
        ranks[test] = rank
        if int(year) == target_year:
            serving_models = annual_models
            target_train_reference = train_score
            target_cutoff = cutoff

    if len(serving_models) != int(config["model"]["bags"]):
        raise ValueError("The frozen serving ensemble was not reconstructed")
    if target_train_reference is None or target_cutoff is None:
        raise ValueError("The frozen serving-year training reference is unavailable")

    recreated = meta[["trade_id", "entry_time"]].copy()
    recreated["score"] = scores
    recreated["rank"] = ranks
    recreated = recreated.loc[recreated["score"].notna()].reset_index(drop=True)
    stored = pd.read_parquet(
        resolve_input(str(config["inputs"]["v2_decisions"]["path"])),
        columns=["trade_id", "entry_time", "score", "rank"],
    )
    stored["entry_time"] = pd.to_datetime(stored["entry_time"], utc=True)
    target_stored = stored.loc[
        stored["entry_time"].dt.year.eq(target_year)
    ].copy()
    check = target_stored.merge(
        recreated,
        on=["trade_id", "entry_time"],
        how="inner",
        suffixes=("_stored", "_recreated"),
        validate="one_to_one",
    )
    if len(check) != len(target_stored):
        raise ValueError("Stored serving-year rows did not reproduce one-to-one")
    score_error = np.abs(check["score_stored"] - check["score_recreated"])
    rank_error = np.abs(check["rank_stored"] - check["rank_recreated"])
    historical_reference = (
        stored.sort_values(["entry_time", "trade_id"], kind="mergesort")["score"]
        .to_numpy(dtype=float)
    )
    bundle = {
        "schema_version": "codex_v60_portable_mature_topup_serving_bundle_v3",
        "models": serving_models,
        "feature_columns": list(config["feature_columns"]),
        "historical_oos_score_reference": historical_reference,
        "training_score_reference": target_train_reference,
        "rank_threshold_exclusive": float(
            config["model"]["rank_threshold_exclusive"]
        ),
        "serving_year": target_year,
        "training_cutoff_utc": target_cutoff.isoformat(),
        "training_last_exit_utc": meta.loc[
            meta["exit_time"].lt(target_cutoff), "exit_time"
        ].max().isoformat(),
        "training_rows": int(meta["exit_time"].lt(target_cutoff).sum()),
        "expected_account_login": 1033030,
        "expected_symbol": "XAUUSD",
        "failure_policy": "BASELINE_ONLY",
    }
    audit = {
        "schema_version": "codex_v60_portable_mature_topup_bundle_build_v3",
        "serving_year_rows": int(len(target_stored)),
        "models": int(len(serving_models)),
        "training_rows": int(bundle["training_rows"]),
        "training_cutoff_utc": bundle["training_cutoff_utc"],
        "training_last_exit_utc": bundle["training_last_exit_utc"],
        "stored_score_maximum_absolute_error": float(score_error.max()),
        "stored_rank_maximum_absolute_error": float(rank_error.max()),
        "historical_oos_reference_rows": int(len(historical_reference)),
    }
    return bundle, audit, check


def ensemble_score(bundle: Mapping[str, Any], features: pd.DataFrame) -> np.ndarray:
    columns = list(bundle["feature_columns"])
    if list(features.columns) != columns:
        features = features[columns]
    values = features.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Serving features are not finite")
    models = list(bundle["models"])
    if not models:
        raise ValueError("Serving ensemble is empty")
    score = np.zeros(len(features), dtype=float)
    for model in models:
        score += model.predict(features)
    return score / len(models)


def market_feature_frame(bars: pd.DataFrame) -> pd.DataFrame:
    required = {"bar_start_utc", "mid_high", "mid_low", "mid_close"}
    if not required.issubset(bars.columns):
        raise ValueError(f"Missing bar columns: {sorted(required - set(bars.columns))}")
    frame = bars.copy()
    frame["bar_start_utc"] = pd.to_datetime(frame["bar_start_utc"], utc=True)
    frame = frame.sort_values("bar_start_utc", kind="mergesort")
    frame = frame.drop_duplicates("bar_start_utc", keep="last").reset_index(drop=True)
    close = frame["mid_close"].to_numpy(dtype=float)
    high = frame["mid_high"].to_numpy(dtype=float)
    low = frame["mid_low"].to_numpy(dtype=float)
    previous = np.r_[close[0], close[:-1]]
    true_range = np.maximum.reduce(
        [high - low, np.abs(high - previous), np.abs(low - previous)]
    )
    atr = pd.Series(true_range).rolling(144, min_periods=50).mean()
    ema = pd.Series(close).ewm(span=144, adjust=False).mean()
    atr_median = atr.rolling(2016, min_periods=500).median().shift(1)
    close_series = pd.Series(close)
    change = close_series.diff()
    safe_atr = atr.where(atr > 0.0)
    result = pd.DataFrame(
        {
            "bar_start_utc": frame["bar_start_utc"],
            "decision_time_utc": frame["bar_start_utc"] + BAR_WIDTH,
            "atr_ratio": atr / atr_median.where(atr_median > 0.0),
            "rv_1h": change.rolling(12, min_periods=3).std(ddof=0) / safe_atr,
            "rv_24h": change.rolling(288, min_periods=3).std(ddof=0) / safe_atr,
            "slope_atr": (ema - ema.shift(288)) / safe_atr,
            "ret_1h": (close_series - close_series.shift(12)) / safe_atr,
            "ret_4h": (close_series - close_series.shift(48)) / safe_atr,
            "ret_24h": (close_series - close_series.shift(288)) / safe_atr,
            "dist_hi_24h": (
                pd.Series(high).rolling(288, min_periods=20).max() - close_series
            )
            / safe_atr,
            "dist_lo_24h": (
                close_series - pd.Series(low).rolling(288, min_periods=20).min()
            )
            / safe_atr,
        }
    )
    result["hour"] = result["decision_time_utc"].dt.hour.astype(float)
    result["dow"] = result["decision_time_utc"].dt.dayofweek.astype(float)
    result["_history_ok"] = np.arange(len(result)) >= 2016
    return result


def load_dukascopy_bars(config: Mapping[str, Any]) -> pd.DataFrame:
    columns = ["timestamp_ms", "mid_high", "mid_low", "mid_close"]
    historical = pd.read_parquet(
        resolve_input(str(config["inputs"]["dukascopy_historical_m5"]["path"])),
        columns=columns,
    )
    prospective = pd.read_parquet(
        resolve_input(str(config["inputs"]["dukascopy_prospective_m5"]["path"])),
        columns=columns,
    )
    frame = pd.concat([historical, prospective], ignore_index=True)
    frame["bar_start_utc"] = pd.to_datetime(
        frame.pop("timestamp_ms"), unit="ms", utc=True
    )
    return frame


def load_capital_bars(config: Mapping[str, Any]) -> pd.DataFrame:
    frame = pd.read_parquet(
        resolve_input(str(config["inputs"]["capital_mt5_snapshot"]["path"]))
    )
    point = float(config["capital_symbol_point"])
    spread = frame["spread"].astype(float) * point
    result = pd.DataFrame({"bar_start_utc": frame["bar_start_utc"]})
    for field in ("high", "low", "close"):
        result[f"mid_{field}"] = frame[field].astype(float) + spread / 2.0
    return result


def score_candidate(
    bundle: Mapping[str, Any],
    feature_bars: pd.DataFrame,
    decision_time: pd.Timestamp,
    *,
    is_long: bool,
    is_core: bool,
    maximum_bar_age: pd.Timedelta = pd.Timedelta(minutes=10),
) -> dict[str, Any]:
    now = pd.Timestamp(decision_time)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")
    eligible = feature_bars.loc[
        feature_bars["decision_time_utc"].le(now) & feature_bars["_history_ok"]
    ]
    if eligible.empty:
        return {"topup": False, "reason": "NO_COMPLETED_FEATURE_BAR"}
    row = eligible.iloc[-1]
    age = now - pd.Timestamp(row["decision_time_utc"])
    if age < pd.Timedelta(0) or age > maximum_bar_age:
        return {"topup": False, "reason": "STALE_COMPLETED_FEATURE_BAR"}
    values = {
        key: float(row[key])
        for key in bundle["feature_columns"]
        if key not in {"is_long", "is_core"}
    }
    values["is_long"] = float(bool(is_long))
    values["is_core"] = float(bool(is_core))
    features = pd.DataFrame([values], columns=bundle["feature_columns"])
    try:
        score = float(ensemble_score(bundle, features)[0])
        rank = causal_rank(score, bundle["historical_oos_score_reference"])
    except (ValueError, TypeError, FloatingPointError) as exc:
        return {"topup": False, "reason": "MODEL_SCORING_FAILED", "detail": str(exc)}
    return {
        "topup": bool(rank > float(bundle["rank_threshold_exclusive"])),
        "reason": "SCORE_COMPLETE",
        "score": score,
        "rank": rank,
        "feature_bar_end_utc": pd.Timestamp(
            row["decision_time_utc"]
        ).isoformat(),
    }


def save_bundle(bundle: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(dict(bundle), path, compress=3)


def load_bundle(path: Path) -> dict[str, Any]:
    bundle = joblib.load(path)
    if bundle.get("schema_version") != (
        "codex_v60_portable_mature_topup_serving_bundle_v3"
    ):
        raise ValueError("Unexpected serving bundle schema")
    return bundle


def run_parity(
    config: Mapping[str, Any],
    bundle: Mapping[str, Any],
    build_audit: Mapping[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    start = pd.Timestamp(config["parity_window"]["start_utc"])
    end = pd.Timestamp(config["parity_window"]["end_utc_exclusive"])
    duka = market_feature_frame(load_dukascopy_bars(config))
    capital = market_feature_frame(load_capital_bars(config))
    base_columns = [
        column
        for column in config["feature_columns"]
        if column not in {"is_long", "is_core"}
    ]
    duka = duka.loc[
        duka["bar_start_utc"].ge(start)
        & duka["bar_start_utc"].lt(end)
        & duka["_history_ok"]
    ][["bar_start_utc", *base_columns]]
    capital = capital.loc[
        capital["bar_start_utc"].ge(start)
        & capital["bar_start_utc"].lt(end)
        & capital["_history_ok"]
    ][["bar_start_utc", *base_columns]]
    common = duka.merge(
        capital,
        on="bar_start_utc",
        how="inner",
        suffixes=("_duka", "_capital"),
        validate="one_to_one",
    )
    finite = np.isfinite(
        common.drop(columns=["bar_start_utc"]).to_numpy(dtype=float)
    ).all(axis=1)
    common = common.loc[finite].reset_index(drop=True)
    rows: list[pd.DataFrame] = []
    reference = np.asarray(bundle["historical_oos_score_reference"], dtype=float)
    for context in config["parity_window"]["contexts"]:
        duka_X = pd.DataFrame(
            {
                column: (
                    common[f"{column}_duka"]
                    if column not in {"is_long", "is_core"}
                    else float(context[column])
                )
                for column in config["feature_columns"]
            }
        )
        capital_X = pd.DataFrame(
            {
                column: (
                    common[f"{column}_capital"]
                    if column not in {"is_long", "is_core"}
                    else float(context[column])
                )
                for column in config["feature_columns"]
            }
        )
        duka_score = ensemble_score(bundle, duka_X)
        capital_score = ensemble_score(bundle, capital_X)
        frozen = np.sort(reference)
        duka_rank = np.searchsorted(frozen, duka_score, side="right") / len(frozen)
        capital_rank = (
            np.searchsorted(frozen, capital_score, side="right") / len(frozen)
        )
        rows.append(
            pd.DataFrame(
                {
                    "bar_start_utc": common["bar_start_utc"],
                    "direction": str(context["direction"]),
                    "is_core": bool(context["is_core"]),
                    "duka_score": duka_score,
                    "capital_score": capital_score,
                    "duka_rank": duka_rank,
                    "capital_rank": capital_rank,
                    "duka_topup": duka_rank
                    > float(bundle["rank_threshold_exclusive"]),
                    "capital_topup": capital_rank
                    > float(bundle["rank_threshold_exclusive"]),
                }
            )
        )
    parity = pd.concat(rows, ignore_index=True)
    duka_positive = parity["duka_topup"]
    capital_positive = parity["capital_topup"]
    both = duka_positive & capital_positive
    union = duka_positive | capital_positive
    score_spearman = float(
        parity["duka_score"].corr(parity["capital_score"], method="spearman")
    )
    rank_spearman = float(
        parity["duka_rank"].corr(parity["capital_rank"], method="spearman")
    )
    mean_rank_difference = float(
        np.abs(parity["duka_rank"] - parity["capital_rank"]).mean()
    )
    jaccard = float(both.sum() / union.sum()) if union.any() else 0.0
    precision = (
        float(both.sum() / capital_positive.sum())
        if capital_positive.any()
        else 0.0
    )
    recall = float(both.sum() / duka_positive.sum()) if duka_positive.any() else 0.0
    metrics = {
        "common_completed_bars": int(len(common)),
        "context_rows": int(len(parity)),
        "score_spearman": score_spearman,
        "rank_spearman": rank_spearman,
        "mean_absolute_rank_difference": mean_rank_difference,
        "top_quintile_jaccard": jaccard,
        "capital_precision": precision,
        "capital_recall": recall,
        "dukascopy_topups": int(duka_positive.sum()),
        "capital_topups": int(capital_positive.sum()),
        "agreed_topups": int(both.sum()),
    }
    gate_config = config["gates"]
    gates = {
        "stored_scores_reproduce": float(
            build_audit["stored_score_maximum_absolute_error"]
        )
        <= float(gate_config["maximum_stored_score_error"]),
        "stored_ranks_reproduce": float(
            build_audit["stored_rank_maximum_absolute_error"]
        )
        <= float(gate_config["maximum_stored_rank_error"]),
        "enough_common_bars": len(common)
        >= int(gate_config["minimum_common_bars"]),
        "enough_context_rows": len(parity)
        >= int(gate_config["minimum_context_rows"]),
        "score_spearman": score_spearman
        >= float(gate_config["minimum_score_spearman"]),
        "rank_spearman": rank_spearman
        >= float(gate_config["minimum_rank_spearman"]),
        "mean_rank_difference": mean_rank_difference
        <= float(gate_config["maximum_mean_absolute_rank_difference"]),
        "top_quintile_jaccard": jaccard
        >= float(gate_config["minimum_top_quintile_jaccard"]),
        "capital_precision": precision
        >= float(gate_config["minimum_capital_precision"]),
        "capital_recall": recall >= float(gate_config["minimum_capital_recall"]),
        "all_scored_values_finite": bool(
            np.isfinite(
                parity[
                    ["duka_score", "capital_score", "duka_rank", "capital_rank"]
                ].to_numpy(dtype=float)
            ).all()
        ),
    }
    decision = (
        "PASS_PROSPECTIVE_DEMO_INTEGRATION_NOMINATED"
        if all(gates.values())
        else "FAIL_KEEP_ML_BROKER_ACTION_DISABLED"
    )
    result = {
        "schema_version": "codex_v60_portable_mature_topup_parity_result_v3",
        "decision": decision,
        "outcome_labels_used": False,
        "build_audit": dict(build_audit),
        "metrics": metrics,
        "gates": gates,
        "authorization": dict(config["authorization"]),
    }
    return result, parity
