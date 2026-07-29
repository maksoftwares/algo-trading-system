from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from eurusd_regime_specialists.neutral_specialist_agreement_execution import (
    _quarantine_overlap,
    attach_oracle_matches,
    load_eurusd_m5,
    payoff_metrics,
    remove_top_winners,
    simulate_one,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_neutral_specialist_meta_selector.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_SPECIALIST_META_SELECTOR_PREREG_"
    "2026_07_29.sha256.json"
)
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_specialist_meta_selector"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("frozen_before_combined_canonical_outcomes") is not True
        or lock.get("oracle_decision_use_allowed") is not False
        or lock.get("parameter_search_allowed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Specialist meta-selector lock is incomplete")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Specialist meta-selector drift: {relative}")
        checked[relative] = actual
    return {**lock, "checked_files": checked}


def _utc_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, utc=True, errors="raise")


def load_signal_candidates(config: dict[str, Any]) -> pd.DataFrame:
    source = config["signal_source"]
    census_lock_path = PACKAGE_ROOT / source["census_result_lock_path"]
    if sha256_file(census_lock_path) != source["census_result_lock_sha256"]:
        raise RuntimeError("Signal census result lock drift")
    census_lock = json.loads(census_lock_path.read_text(encoding="utf-8"))
    if census_lock["status"] != source["required_census_status"]:
        raise RuntimeError("Signal census status does not permit research")
    path = PACKAGE_ROOT / source["path"]
    if sha256_file(path) != source["sha256"]:
        raise RuntimeError("Signal-only source drift")
    allowed = list(source["columns_allowed"])
    signals = pd.read_csv(path, usecols=allowed)
    if len(signals) != int(source["rows"]):
        raise RuntimeError("Signal-only source row-count drift")
    signals["entry_time_utc"] = _utc_series(signals["entry_time_utc"])
    experts = list(config["experts"])
    if (
        not signals["side"].isin(["LONG", "SHORT"]).all()
        or set(signals["expert_id"]) != set(experts)
    ):
        raise RuntimeError("Signal-only source domain drift")

    grouped = (
        signals.groupby(["entry_time_utc", "side"], sort=True)["expert_id"]
        .agg(lambda values: tuple(sorted(set(values))))
        .reset_index(name="expert_ids")
    )
    side_counts = grouped.groupby("entry_time_utc")["side"].transform("nunique")
    grouped["opposite_side_present"] = side_counts.gt(1)
    grouped["distinct_experts"] = grouped["expert_ids"].map(len)
    grouped["expert_combination"] = grouped["expert_ids"].map("|".join)
    grouped["eligible_date"] = grouped["entry_time_utc"].dt.strftime("%Y-%m-%d")
    for expert in experts:
        grouped[f"expert__{expert}"] = grouped["expert_ids"].map(
            lambda values, name=expert: int(name in values)
        )
    grouped = grouped.sort_values(
        ["entry_time_utc", "side", "expert_combination"]
    ).reset_index(drop=True)
    grouped.insert(0, "candidate_id", np.arange(len(grouped), dtype=np.int64))
    if len(grouped) != int(source["expected_collapsed_clock_side_candidates"]):
        raise RuntimeError("Collapsed candidate-count drift")
    return grouped


def label_canonical_candidates(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    execution_config = {
        "execution": config["canonical_execution"],
        "quarantine": config["quarantine"],
    }
    for _, candidate in candidates.iterrows():
        base = candidate.to_dict()
        entry = pd.Timestamp(candidate["entry_time_utc"])
        if _quarantine_overlap(entry, execution_config):
            records.append({**base, "status": "CASH_QUARANTINED_PATH"})
            continue
        result = simulate_one(
            candidate, m5, config["canonical_execution"]
        )
        records.append({**base, **result})
    labeled = pd.DataFrame(records).sort_values("candidate_id").reset_index(
        drop=True
    )
    if len(labeled) != len(candidates):
        raise RuntimeError("Canonical labeling lost candidates")
    return labeled


def feature_columns(config: dict[str, Any]) -> list[str]:
    return [
        *(f"expert__{expert}" for expert in config["experts"]),
        "side_long",
        "distinct_experts",
        "opposite_side_present",
        "minute_sin",
        "minute_cos",
        "weekday_sin",
        "weekday_cos",
    ]


def build_features(
    candidates: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    result = candidates[
        [f"expert__{expert}" for expert in config["experts"]]
    ].astype(float)
    times = _utc_series(candidates["entry_time_utc"])
    minute_of_day = times.dt.hour * 60 + times.dt.minute
    result["side_long"] = candidates["side"].eq("LONG").astype(float)
    result["distinct_experts"] = candidates["distinct_experts"].astype(float)
    result["opposite_side_present"] = candidates[
        "opposite_side_present"
    ].astype(float)
    result["minute_sin"] = np.sin(2.0 * math.pi * minute_of_day / 1440.0)
    result["minute_cos"] = np.cos(2.0 * math.pi * minute_of_day / 1440.0)
    result["weekday_sin"] = np.sin(
        2.0 * math.pi * times.dt.dayofweek / 7.0
    )
    result["weekday_cos"] = np.cos(
        2.0 * math.pi * times.dt.dayofweek / 7.0
    )
    return result[feature_columns(config)]


def fit_monthly_model(
    labeled: pd.DataFrame,
    *,
    month_boundary: pd.Timestamp,
    config: dict[str, Any],
) -> tuple[StandardScaler, LogisticRegression, dict[str, Any]]:
    boundary = pd.Timestamp(month_boundary)
    if boundary.tzinfo is None:
        raise ValueError("Month boundary must be timezone-aware")
    boundary = boundary.tz_convert("UTC")
    closed = labeled["status"].eq("CLOSED")
    training = labeled[
        closed
        & labeled["entry_time_utc"].lt(boundary)
        & labeled["exit_time_utc"].lt(boundary)
    ].copy()
    minimum = int(config["model"]["minimum_training_candidates"])
    if len(training) < minimum:
        raise RuntimeError("Insufficient strictly prior training candidates")
    labels = training["r"].gt(0.0).astype(int)
    if labels.nunique() != 2:
        raise RuntimeError("Training labels contain only one class")
    features = build_features(training, config)
    scaler = StandardScaler()
    standardized = scaler.fit_transform(features)
    model = LogisticRegression(
        C=float(config["model"]["c"]),
        solver=str(config["model"]["solver"]),
        max_iter=int(config["model"]["maximum_iterations"]),
        random_state=int(config["model"]["random_state"]),
        class_weight=config["model"]["class_weight"],
    )
    model.fit(standardized, labels)
    latest_exit = training["exit_time_utc"].max()
    if not latest_exit < boundary:
        raise RuntimeError("Training chronology violation")
    metadata = {
        "month_boundary_utc": boundary,
        "training_candidates": len(training),
        "training_wins": int(labels.sum()),
        "training_win_rate": float(labels.mean()),
        "latest_training_exit_utc": latest_exit,
        "intercept": float(model.intercept_[0]),
        "coefficients": {
            name: float(value)
            for name, value in zip(feature_columns(config), model.coef_[0])
        },
    }
    return scaler, model, metadata


def select_chronological_trades(
    candidates: pd.DataFrame,
    labeled: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    start = pd.Timestamp(config["routing"]["evaluation_start_utc"])
    end = pd.Timestamp(config["routing"]["evaluation_end_utc"])
    evaluation = candidates[
        candidates["entry_time_utc"].between(start, end, inclusive="both")
    ].copy()
    label_index = labeled.set_index("candidate_id", drop=False)
    selected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    models: list[dict[str, Any]] = []
    open_until = pd.Timestamp.min.tz_localize("UTC")
    traded_dates: set[str] = set()
    threshold = float(
        config["model"]["selection_probability_minimum_inclusive"]
    )

    for period, month in evaluation.groupby(
        evaluation["entry_time_utc"].dt.to_period("M"), sort=True
    ):
        boundary = pd.Timestamp(period.start_time, tz="UTC")
        scaler, model, metadata = fit_monthly_model(
            labeled, month_boundary=boundary, config=config
        )
        models.append(metadata)
        for entry_time, clock in month.groupby("entry_time_utc", sort=True):
            date_key = entry_time.strftime("%Y-%m-%d")
            base = {
                "entry_time_utc": entry_time,
                "eligible_date": date_key,
                "month_boundary_utc": boundary,
                "candidate_sides": len(clock),
                "training_candidates": metadata["training_candidates"],
                "latest_training_exit_utc": metadata[
                    "latest_training_exit_utc"
                ],
            }
            if date_key in traded_dates:
                decisions.append({**base, "status": "CASH_DAILY_LIMIT"})
                continue
            if entry_time < open_until:
                decisions.append(
                    {
                        **base,
                        "status": "CASH_PRIOR_POSITION_OPEN",
                        "prior_position_exit_utc": open_until,
                    }
                )
                continue
            probabilities = model.predict_proba(
                scaler.transform(build_features(clock, config))
            )[:, 1]
            ranked = clock.copy()
            ranked["predicted_win_probability"] = probabilities
            ranked = ranked.sort_values(
                [
                    "predicted_win_probability",
                    "distinct_experts",
                    "expert_combination",
                    "side",
                    "candidate_id",
                ],
                ascending=[False, False, True, True, True],
            )
            chosen = ranked.iloc[0]
            probability = float(chosen["predicted_win_probability"])
            if probability < threshold:
                decisions.append(
                    {
                        **base,
                        "status": "CASH_BELOW_FIXED_PROBABILITY",
                        "best_probability": probability,
                    }
                )
                continue
            outcome = label_index.loc[int(chosen["candidate_id"])]
            if outcome["status"] != "CLOSED":
                decisions.append(
                    {
                        **base,
                        "status": f"CASH_{outcome['status']}",
                        "selected_candidate_id": int(chosen["candidate_id"]),
                        "best_probability": probability,
                    }
                )
                continue
            record = outcome.to_dict()
            record.update(
                {
                    "predicted_win_probability": probability,
                    "model_month_boundary_utc": boundary,
                    "model_training_candidates": metadata[
                        "training_candidates"
                    ],
                    "model_latest_training_exit_utc": metadata[
                        "latest_training_exit_utc"
                    ],
                }
            )
            selected.append(record)
            traded_dates.add(date_key)
            open_until = pd.Timestamp(outcome["exit_time_utc"])
            decisions.append(
                {
                    **base,
                    "status": "SELECTED",
                    "selected_candidate_id": int(chosen["candidate_id"]),
                    "selected_side": chosen["side"],
                    "selected_expert_combination": chosen[
                        "expert_combination"
                    ],
                    "best_probability": probability,
                    "selected_exit_time_utc": open_until,
                }
            )
    selected_frame = pd.DataFrame(selected)
    decisions_frame = pd.DataFrame(decisions)
    models_frame = pd.DataFrame(models)
    if not selected_frame.empty:
        selected_frame = selected_frame.sort_values(
            ["entry_time_utc", "candidate_id"]
        ).reset_index(drop=True)
    return selected_frame, decisions_frame, models_frame


def _period(frame: pd.DataFrame, bounds: list[str]) -> pd.DataFrame:
    start, end = (pd.Timestamp(value) for value in bounds)
    return frame[
        frame["entry_time_utc"].between(start, end, inclusive="both")
    ]


def summarize(
    trades: pd.DataFrame,
    oracle_summary: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    overall = payoff_metrics(trades)
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(remove_top_winners(trades))
    windows = {
        name: payoff_metrics(_period(trades, bounds))
        for name, bounds in config["reporting_windows"].items()
    }
    sides = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    gates = config["research_gates"]
    gate_results = {
        "minimum_selected_trades": overall["trades"]
        >= int(gates["minimum_selected_trades"]),
        "win_rate": float(gates["minimum_win_rate"])
        <= overall["win_rate"]
        <= float(gates["maximum_win_rate"]),
        "realized_payoff_ratio": float(
            gates["minimum_realized_payoff_ratio"]
        )
        <= overall["realized_payoff_ratio"]
        <= float(gates["maximum_realized_payoff_ratio"]),
        "profit_factor": overall["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "each_full_year_profit_factor": all(
            windows[name]["profit_factor"]
            > float(gates["minimum_each_full_year_profit_factor_exclusive"])
            for name in ("OOS_2023", "OOS_2024", "OOS_2025")
        ),
        "latest_six_month_capacity": windows["LATEST_SIX_MONTHS"]["trades"]
        >= int(gates["minimum_latest_six_month_trades"]),
        "latest_six_month_profit_factor": windows["LATEST_SIX_MONTHS"][
            "profit_factor"
        ]
        > float(gates["minimum_latest_six_month_profit_factor_exclusive"]),
        "both_sides": all(
            sides[side]["trades"] >= int(gates["minimum_trades_each_side"])
            and sides[side]["profit_factor"]
            > float(gates["minimum_profit_factor_each_side_exclusive"])
            for side in ("LONG", "SHORT")
        ),
        "maximum_drawdown": overall["max_drawdown_r"]
        <= float(gates["maximum_drawdown_r"]),
        "extra_half_pip_profit_factor": stressed["profit_factor"]
        > float(gates["minimum_extra_half_pip_profit_factor_exclusive"]),
        "top_5pct_winners_removed_profit_factor": top_removed["profit_factor"]
        > float(
            gates["minimum_top_5pct_winners_removed_profit_factor_exclusive"]
        ),
        "oracle_precision": oracle_summary["same_side_precision_15m"]
        >= float(gates["minimum_same_side_oracle_precision_15m"]),
    }
    return {
        "overall": overall,
        "extra_half_pip": stressed,
        "top_5pct_winners_removed": top_removed,
        "windows": windows,
        "by_side": sides,
        "oracle_resemblance": oracle_summary,
        "gate_results": gate_results,
        "all_research_gates_passed": all(gate_results.values()),
    }


def run() -> dict[str, Any]:
    verify_lock()
    config = load_config()
    candidates = load_signal_candidates(config)
    m5 = load_eurusd_m5(config)
    labeled = label_canonical_candidates(candidates, m5, config)
    trades, decisions, models = select_chronological_trades(
        candidates, labeled, config
    )
    oracle_matches, oracle_summary = attach_oracle_matches(trades, config)
    summary = summarize(trades, oracle_summary, config)
    result = {
        "schema_version": "eurusd_neutral_specialist_meta_selector_result_v1",
        "frozen_at_utc": config["frozen_at_utc"],
        "status": (
            "RESEARCH_PASS_PROSPECTIVE_PREREGISTRATION_REQUIRED"
            if summary["all_research_gates_passed"]
            else "REJECTED_EXACT_META_SELECTOR"
        ),
        "signal_candidates": len(candidates),
        "canonical_closed_labels": int(labeled["status"].eq("CLOSED").sum()),
        "monthly_models": len(models),
        "selected_trades": len(trades),
        "summary": summary,
        "retrospective_causal_not_pristine_oos": True,
        "historical_pass_can_authorize_demo": False,
        "broker_action_allowed": False,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    csv_kwargs = {"index": False, "date_format": "%Y-%m-%dT%H:%M:%S.%fZ"}
    candidate_output = candidates.drop(columns=["expert_ids"])
    candidate_output.to_csv(OUTPUT_ROOT / "SIGNAL_CANDIDATES.csv", **csv_kwargs)
    labeled.drop(columns=["expert_ids"]).to_csv(
        OUTPUT_ROOT / "CANONICAL_LABELS.csv", **csv_kwargs
    )
    decisions.to_csv(OUTPUT_ROOT / "DECISIONS.csv", **csv_kwargs)
    models.assign(
        coefficients=models["coefficients"].map(
            lambda value: json.dumps(value, sort_keys=True)
        )
    ).to_csv(OUTPUT_ROOT / "MONTHLY_MODELS.csv", **csv_kwargs)
    trades.drop(columns=["expert_ids"]).to_csv(
        OUTPUT_ROOT / "SELECTED_TRADES.csv", **csv_kwargs
    )
    oracle_matches.to_csv(OUTPUT_ROOT / "ORACLE_MATCHES.csv", **csv_kwargs)
    (OUTPUT_ROOT / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return result
