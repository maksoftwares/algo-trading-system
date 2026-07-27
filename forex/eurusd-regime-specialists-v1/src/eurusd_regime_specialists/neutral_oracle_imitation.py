from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_tick_microstructure import (
    MODEL_FEATURE_COLUMNS,
    build_microstructure_dataset,
    load_tick_microstructure,
)
from .neutral_walkforward import choose_side
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    is_quarantined,
    serialize,
    sha256_file,
)


FAMILY = "N7_NEUTRAL_ORACLE_IMITATION"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_oracle_imitation"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_oracle_imitation.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_ORACLE_IMITATION_PREREG_2026_07_27.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if lock.get("locked_before_oracle_imitation_outcome_pass") is not True:
        raise RuntimeError("Oracle-imitation contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Oracle-imitation preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    return checked


def load_oracle(cfg: dict[str, Any]) -> pd.DataFrame:
    path = PACKAGE_ROOT / cfg["oracle_source"]
    frame = pd.read_csv(path)
    for column in ("entry_time_utc", "exit_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return (
        frame[frame["regime"].eq(cfg["oracle_regime"])]
        .sort_values(["entry_time_utc", "oracle_trade_number"])
        .reset_index(drop=True)
    )


def attach_oracle_labels(
    dataset: pd.DataFrame,
    oracle: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    labeled = dataset.copy()
    positive_keys = pd.MultiIndex.from_frame(
        oracle[["entry_time_utc", "side"]]
    )
    candidate_keys = pd.MultiIndex.from_frame(
        labeled[["entry_time_utc", "side"]]
    )
    labeled["oracle_member"] = candidate_keys.isin(positive_keys).astype(int)
    horizon = float(
        cfg["oracle_label"]["negative_label_known_after_hours"]
    )
    labeled["oracle_label_known_time_utc"] = (
        labeled["entry_time_utc"] + pd.Timedelta(hours=horizon)
    )
    return labeled


def build_dataset(
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], pd.DataFrame]:
    base = load_ensemble_config()
    eurusd, state, manifests = load_inputs(base)
    start = pd.Timestamp(base["data"]["start_utc"])
    end = pd.Timestamp(base["data"]["end_utc"])
    oracle = load_oracle(cfg)
    cache = OUTPUT_ROOT / "LABELED_DATASET.parquet"
    if cache.exists():
        dataset = pd.read_parquet(cache)
        for column in (
            "signal_time_utc",
            "completion_time_utc",
            "entry_time_utc",
            "exit_time_utc",
            "oracle_label_known_time_utc",
        ):
            dataset[column] = pd.to_datetime(dataset[column], utc=True)
    else:
        microstructure, tick_manifest = load_tick_microstructure(
            Path(base["data"]["dukascopy_raw_root"]),
            start,
            end,
            cfg,
        )
        manifests = {**manifests, "EURUSD_TICKS": tick_manifest}
        dataset = attach_oracle_labels(
            build_microstructure_dataset(
                eurusd, state, microstructure, cfg
            ),
            oracle,
            cfg,
        )
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        dataset.to_parquet(cache, index=False, compression="zstd")
    if "EURUSD_TICKS" not in manifests:
        manifest_path = (
            PACKAGE_ROOT
            / "outputs"
            / "cache"
            / "EURUSD_M5_MICROSTRUCTURE_v1.manifest.json"
        )
        manifests = {
            **manifests,
            "EURUSD_TICKS": json.loads(
                manifest_path.read_text(encoding="utf-8")
            ),
        }
    return dataset, oracle, manifests, eurusd


def purged_oracle_training_rows(
    dataset: pd.DataFrame, cutoff: pd.Timestamp
) -> pd.DataFrame:
    return dataset[
        (dataset["entry_time_utc"] < cutoff)
        & (dataset["oracle_label_known_time_utc"] < cutoff)
    ]


def fit_oracle_model(
    training: pd.DataFrame,
    inference: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[np.ndarray, pd.DataFrame]:
    model_cfg = cfg["model"]
    scaler = StandardScaler()
    train_x = scaler.fit_transform(training[MODEL_FEATURE_COLUMNS])
    model = LogisticRegression(
        penalty=model_cfg["penalty"],
        C=float(model_cfg["C"]),
        solver=model_cfg["solver"],
        max_iter=int(model_cfg["max_iter"]),
        class_weight=model_cfg["class_weight"],
        random_state=int(model_cfg["random_state"]),
    )
    model.fit(train_x, training["oracle_member"].astype(int))
    probabilities = model.predict_proba(
        scaler.transform(inference[MODEL_FEATURE_COLUMNS])
    )[:, 1]
    coefficients = pd.DataFrame(
        {
            "feature": MODEL_FEATURE_COLUMNS,
            "coefficient": model.coef_[0],
            "training_mean": scaler.mean_,
            "training_scale": scaler.scale_,
        }
    ).sort_values("coefficient", ascending=False)
    return probabilities, coefficients


def route_concurrent(
    predictions: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    columns = [
        "family",
        "regime",
        "side",
        "signal_time_utc",
        "completion_time_utc",
        "entry_time_utc",
        "exit_time_utc",
        "entry_price",
        "stop_price",
        "target_price",
        "exit_price",
        "exit_reason",
        "predicted_probability",
        "oracle_member",
        "risk_distance",
        "risk_pips",
        "r",
        "extra_half_pip_stress_r",
        "fixed_0p01_lot_usd",
    ]
    if predictions.empty:
        return pd.DataFrame(columns=columns)
    base = load_ensemble_config()
    execution = cfg["execution"]
    maximum_open = int(execution["maximum_concurrent_positions"])
    maximum_daily = int(execution["maximum_trades_per_utc_day"])
    open_exits: list[pd.Timestamp] = []
    daily_count: dict[str, int] = {}
    records: list[dict[str, Any]] = []
    for _, row in predictions.sort_values(
        ["entry_time_utc", "predicted_probability"],
        ascending=[True, False],
    ).iterrows():
        entry_time = row["entry_time_utc"]
        open_exits = [value for value in open_exits if value > entry_time]
        if len(open_exits) >= maximum_open:
            continue
        if is_quarantined(entry_time, "EURUSD", base["quarantine"]):
            continue
        date = entry_time.strftime("%Y-%m-%d")
        if daily_count.get(date, 0) >= maximum_daily:
            continue
        risk = float(row["risk_distance"])
        outcome_r = float(row["outcome_r"])
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "side": row["side"],
                "signal_time_utc": row["signal_time_utc"],
                "completion_time_utc": row["completion_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": row["exit_time_utc"],
                "entry_price": row["entry_price"],
                "stop_price": row["stop_price"],
                "target_price": row["target_price"],
                "exit_price": row["exit_price"],
                "exit_reason": row["exit_reason"],
                "predicted_probability": row[
                    "predicted_probability"
                ],
                "oracle_member": int(row["oracle_member"]),
                "risk_distance": risk,
                "risk_pips": float(row["risk_pips"]),
                "r": outcome_r,
                "extra_half_pip_stress_r": (
                    outcome_r - 0.5 * PIP / risk
                ),
                "fixed_0p01_lot_usd": row[
                    "fixed_0p01_lot_usd"
                ],
            }
        )
        open_exits.append(row["exit_time_utc"])
        daily_count[date] = daily_count.get(date, 0) + 1
    return pd.DataFrame(records, columns=columns)


def _f1(precision: float, recall: float) -> float:
    return (
        2.0 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )


def oracle_match_metrics(
    trades: pd.DataFrame,
    oracle: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    tolerance_minutes: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    actual = oracle[
        (oracle["entry_time_utc"] >= start)
        & (oracle["entry_time_utc"] <= end)
    ].copy()
    predicted = trades[
        (trades["entry_time_utc"] >= start)
        & (trades["entry_time_utc"] <= end)
    ].copy()
    exact_keys = set(
        zip(actual["entry_time_utc"], actual["side"], strict=False)
    )
    exact_matches = int(
        sum(
            (entry, side) in exact_keys
            for entry, side in zip(
                predicted["entry_time_utc"],
                predicted["side"],
                strict=False,
            )
        )
    )
    exact_precision = (
        exact_matches / len(predicted) if len(predicted) else 0.0
    )
    exact_recall = exact_matches / len(actual) if len(actual) else 0.0
    available = actual.reset_index(drop=True)
    unmatched = set(available.index)
    records: list[dict[str, Any]] = []
    tolerance = pd.Timedelta(minutes=tolerance_minutes)
    for trade_index, trade in predicted.sort_values(
        "entry_time_utc"
    ).iterrows():
        candidates = [
            index
            for index in unmatched
            if available.at[index, "side"] == trade["side"]
            and available.at[index, "entry_time_utc"].date()
            == trade["entry_time_utc"].date()
        ]
        if not candidates:
            continue
        chosen = min(
            candidates,
            key=lambda index: abs(
                available.at[index, "entry_time_utc"]
                - trade["entry_time_utc"]
            ),
        )
        difference = abs(
            available.at[chosen, "entry_time_utc"]
            - trade["entry_time_utc"]
        )
        if difference > tolerance:
            continue
        unmatched.remove(chosen)
        records.append(
            {
                "trade_index": trade_index,
                "trade_entry_time_utc": trade["entry_time_utc"],
                "trade_side": trade["side"],
                "oracle_entry_time_utc": available.at[
                    chosen, "entry_time_utc"
                ],
                "oracle_trade_number": available.at[
                    chosen, "oracle_trade_number"
                ],
                "absolute_difference_minutes": (
                    difference.total_seconds() / 60.0
                ),
            }
        )
    tolerant_matches = len(records)
    tolerant_precision = (
        tolerant_matches / len(predicted) if len(predicted) else 0.0
    )
    tolerant_recall = (
        tolerant_matches / len(actual) if len(actual) else 0.0
    )
    metrics = {
        "predicted_trades": int(len(predicted)),
        "oracle_trades": int(len(actual)),
        "exact_matches": exact_matches,
        "exact_precision": exact_precision,
        "exact_recall": exact_recall,
        "exact_f1": _f1(exact_precision, exact_recall),
        "tolerance_minutes": tolerance_minutes,
        "tolerant_matches": tolerant_matches,
        "tolerant_precision": tolerant_precision,
        "tolerant_recall": tolerant_recall,
        "tolerant_f1": _f1(tolerant_precision, tolerant_recall),
    }
    return metrics, pd.DataFrame(records)


def economic_metrics(
    trades: pd.DataFrame,
    eurusd: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    metrics = payoff_metrics(trades)
    active_days = active_weekday_fx_days(eurusd, start, end)
    metrics["active_weekdays"] = active_days
    metrics["trades_per_active_weekday"] = (
        len(trades) / active_days if active_days else 0.0
    )
    metrics["extra_half_pip_stress_net_r"] = (
        float(trades["extra_half_pip_stress_r"].sum())
        if not trades.empty
        else 0.0
    )
    risk_weight = float(
        cfg["execution"]["risk_per_trade_portfolio_r"]
    )
    metrics["portfolio_net_r"] = metrics["net_r"] * risk_weight
    metrics["portfolio_max_drawdown_r"] = (
        metrics["max_drawdown_r"] * risk_weight
    )
    return metrics


def select_development_threshold(
    dataset: pd.DataFrame,
    oracle: pd.DataFrame,
    eurusd: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[float, bool, pd.DataFrame, pd.DataFrame]:
    fit_start, fit_end = map(
        pd.Timestamp, cfg["development"]["fit"]
    )
    selection_start, selection_end = map(
        pd.Timestamp, cfg["development"]["threshold_selection"]
    )
    training = dataset[
        (dataset["entry_time_utc"] >= fit_start)
        & (dataset["entry_time_utc"] <= fit_end)
        & (dataset["oracle_label_known_time_utc"] < selection_start)
    ]
    inference = dataset[
        (dataset["entry_time_utc"] >= selection_start)
        & (dataset["entry_time_utc"] <= selection_end)
    ].copy()
    probabilities, coefficients = fit_oracle_model(
        training, inference, cfg
    )
    inference["predicted_probability"] = probabilities
    rows: list[dict[str, Any]] = []
    minimum = int(
        cfg["development"]["minimum_trades_each_threshold_year"]
    )
    for threshold in cfg["development"]["threshold_grid"]:
        selected = choose_side(inference, float(threshold))
        trades = route_concurrent(selected, cfg)
        imitation, _ = oracle_match_metrics(
            trades,
            oracle,
            selection_start,
            selection_end,
            int(cfg["oracle_matching"]["secondary_tolerance_minutes"]),
        )
        economics = economic_metrics(
            trades, eurusd, selection_start, selection_end, cfg
        )
        year_counts = {
            year: int(
                trades["entry_time_utc"].dt.year.eq(year).sum()
            )
            for year in (2021, 2022)
        }
        rows.append(
            {
                "threshold": float(threshold),
                "eligible_frequency": all(
                    count >= minimum for count in year_counts.values()
                ),
                "trades_2021": year_counts[2021],
                "trades_2022": year_counts[2022],
                **imitation,
                "profit_factor": economics["profit_factor"],
                "net_r": economics["net_r"],
            }
        )
    sweep = pd.DataFrame(rows)
    eligible = sweep[sweep["eligible_frequency"]].copy()
    fallback = eligible.empty
    ranked = sweep if fallback else eligible
    selected_row = ranked.sort_values(
        ["exact_f1", "tolerant_f1", "net_r", "threshold"],
        ascending=[False, False, False, False],
    ).iloc[0]
    qualified = (
        not fallback
        and selected_row["exact_precision"]
        >= float(cfg["development"]["minimum_exact_precision"])
        and selected_row["exact_recall"]
        >= float(cfg["development"]["minimum_exact_recall"])
    )
    sweep["selected"] = sweep["threshold"].eq(
        selected_row["threshold"]
    )
    sweep["fallback_after_frequency_failure"] = fallback
    return (
        float(selected_row["threshold"]),
        bool(qualified),
        sweep,
        coefficients,
    )


def _window_pass(
    metrics: dict[str, Any], cfg: dict[str, Any]
) -> bool:
    gate = cfg["final_admission"]
    return (
        metrics["trades"]
        >= int(gate["minimum_trades_each_walk_forward_window"])
        and float(gate["minimum_win_rate"])
        <= metrics["win_rate"]
        <= float(gate["maximum_win_rate"])
        and float(gate["minimum_realized_payoff_ratio"])
        <= metrics["realized_payoff_ratio"]
        <= float(gate["maximum_realized_payoff_ratio"])
        and metrics["profit_factor"]
        >= float(gate["minimum_profit_factor"])
        and metrics["expectancy_r"]
        > float(gate["minimum_expectancy_r"])
    )


def run_oracle_imitation() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_lock()
    cfg = load_config()
    dataset, oracle, manifests, eurusd = build_dataset(cfg)
    (
        threshold,
        development_qualified,
        threshold_sweep,
        development_coefficients,
    ) = select_development_threshold(dataset, oracle, eurusd, cfg)
    all_trades: list[pd.DataFrame] = []
    all_predictions: list[pd.DataFrame] = []
    all_coefficients = [
        development_coefficients.assign(
            walk_forward_window="DEVELOPMENT_FIT"
        )
    ]
    window_results: dict[str, Any] = {}
    all_matches: list[pd.DataFrame] = []
    for name, (start_raw, end_raw) in cfg[
        "walk_forward_windows"
    ].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        training = purged_oracle_training_rows(dataset, start)
        inference = dataset[
            (dataset["entry_time_utc"] >= start)
            & (dataset["entry_time_utc"] <= end)
        ].copy()
        probabilities, coefficients = fit_oracle_model(
            training, inference, cfg
        )
        inference["predicted_probability"] = probabilities
        selected = choose_side(inference, threshold)
        trades = route_concurrent(selected, cfg)
        trades["walk_forward_window"] = name
        selected["walk_forward_window"] = name
        coefficients["walk_forward_window"] = name
        economics = economic_metrics(
            trades, eurusd, start, end, cfg
        )
        imitation, matches = oracle_match_metrics(
            trades,
            oracle,
            start,
            end,
            int(cfg["oracle_matching"]["secondary_tolerance_minutes"]),
        )
        matches["walk_forward_window"] = name
        window_results[name] = {
            "training_rows": int(len(training)),
            "inference_rows": int(len(inference)),
            "passed": _window_pass(economics, cfg),
            "economics": economics,
            "oracle_imitation": imitation,
        }
        all_trades.append(trades)
        all_predictions.append(selected)
        all_coefficients.append(coefficients)
        all_matches.append(matches)
    trades = pd.concat(all_trades, ignore_index=True)
    predictions = pd.concat(all_predictions, ignore_index=True)
    coefficients = pd.concat(all_coefficients, ignore_index=True)
    matches = pd.concat(all_matches, ignore_index=True)
    oos_start = min(
        pd.Timestamp(values[0])
        for values in cfg["walk_forward_windows"].values()
    )
    oos_end = max(
        pd.Timestamp(values[1])
        for values in cfg["walk_forward_windows"].values()
    )
    overall_economics = economic_metrics(
        trades, eurusd, oos_start, oos_end, cfg
    )
    overall_imitation, _ = oracle_match_metrics(
        trades,
        oracle,
        oos_start,
        oos_end,
        int(cfg["oracle_matching"]["secondary_tolerance_minutes"]),
    )
    membership_breakdown: dict[str, Any] = {}
    for member, name in (
        (1, "exact_oracle_members"),
        (0, "nonmembers"),
    ):
        subset = trades[trades["oracle_member"].eq(member)]
        membership_breakdown[name] = payoff_metrics(subset)
    gate = cfg["final_admission"]
    imitation_pass = (
        overall_imitation["exact_precision"]
        >= float(gate["minimum_exact_match_precision_overall"])
        and overall_imitation["exact_recall"]
        >= float(gate["minimum_exact_match_recall_overall"])
        and overall_imitation["tolerant_precision"]
        >= float(gate["minimum_15m_match_precision_overall"])
    )
    admitted = (
        development_qualified
        and all(value["passed"] for value in window_results.values())
        and imitation_pass
        and overall_economics["extra_half_pip_stress_net_r"] > 0
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_ORACLE_IMITATION_V1"
        ),
        "research_only": True,
        "broker_action_allowed": False,
        "information_status": cfg["information_status"],
        "source_manifests": {
            **manifests,
            "ORACLE": {
                "path": cfg["oracle_source"],
                "sha256": sha256_file(
                    PACKAGE_ROOT / cfg["oracle_source"]
                ),
                "neutral_trades": int(len(oracle)),
            },
        },
        "causality": {
            "features": (
                "Completed EURUSD M5, latest completed cross-asset state, "
                "and tick microstructure through the completed signal bar"
            ),
            "oracle_at_inference": False,
            "oracle_label_purge_hours": cfg["oracle_label"][
                "negative_label_known_after_hours"
            ],
            "future_scores_used_for_routing": False,
        },
        "dataset": {
            "rows": int(len(dataset)),
            "timestamps": int(
                dataset["completion_time_utc"].nunique()
            ),
            "oracle_positive_rows": int(
                dataset["oracle_member"].sum()
            ),
            "oracle_positive_rate": float(
                dataset["oracle_member"].mean()
            ),
            "features": len(MODEL_FEATURE_COLUMNS),
        },
        "development": {
            "selected_threshold": threshold,
            "qualified": development_qualified,
            "thresholds_tested": int(len(threshold_sweep)),
        },
        "walk_forward": {
            "admitted": admitted,
            "windows": window_results,
            "overall_economics": overall_economics,
            "overall_oracle_imitation": overall_imitation,
            "outcomes_by_exact_oracle_membership": (
                membership_breakdown
            ),
            "imitation_gate_passed": imitation_pass,
        },
        "verdict": (
            "The causal oracle-imitation ranker passed every frozen gate; "
            "untouched prospective confirmation is still mandatory."
            if admitted
            else "The causal oracle-imitation hypothesis failed at least "
            "one preregistered development, economic, imitation, or stress "
            "gate and is not an admitted Regime 1 expert."
        ),
    }
    label_census = (
        dataset.assign(year=dataset["entry_time_utc"].dt.year)
        .groupby("year", as_index=False)
        .agg(
            candidate_rows=("oracle_member", "size"),
            oracle_positive_rows=("oracle_member", "sum"),
        )
    )
    label_census["positive_rate"] = (
        label_census["oracle_positive_rows"]
        / label_census["candidate_rows"]
    )
    artifacts = {
        "LABEL_CENSUS": label_census,
        "THRESHOLD_SWEEP": threshold_sweep,
        "SELECTED_PREDICTIONS": predictions,
        "TRADES": trades,
        "ORACLE_MATCHES": matches,
        "MODEL_COEFFICIENTS": coefficients,
    }
    return result, artifacts


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2), encoding="utf-8"
    )
