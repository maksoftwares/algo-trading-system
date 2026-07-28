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
from .neutral_midnight_pairs import (
    aggregate_days,
    oracle_match_metrics,
    write_json,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N21_NEUTRAL_FOUR_CLOCK_PAIRED_RANKER"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_four_clock_ranker"

IDENTITY_COLUMNS = [
    "side",
    "signal_time_utc",
    "completion_time_utc",
    "entry_time_utc",
]
OUTCOME_COLUMNS = [
    "exit_time_utc",
    "entry_price",
    "stop_price",
    "target_price",
    "exit_price",
    "exit_reason",
    "risk_distance",
    "risk_pips",
    "outcome_r",
    "target_first",
    "fixed_0p01_lot_usd",
    "oracle_member",
]


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_four_clock_ranker.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_FOUR_CLOCK_RANKER_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_four_clock_ranker_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral four-clock ranker is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral four-clock ranker preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for source_key in ("parent_contract", "paired_source"):
        source = cfg[source_key]
        if sha256_file(PACKAGE_ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(
                f"Neutral four-clock ranker {source_key} drift"
            )
    return checked


def _source_path(cfg: dict[str, Any]) -> Path:
    return PACKAGE_ROOT / cfg["paired_source"]["path"]


def load_source(
    cfg: dict[str, Any],
    *,
    include_outcomes: bool,
) -> pd.DataFrame:
    columns = (
        IDENTITY_COLUMNS
        + list(cfg["features"]["contrast_columns"])
        + (OUTCOME_COLUMNS if include_outcomes else [])
    )
    frame = pd.read_parquet(_source_path(cfg), columns=columns)
    for column in (
        "signal_time_utc",
        "completion_time_utc",
        "entry_time_utc",
    ):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    if include_outcomes:
        frame["exit_time_utc"] = pd.to_datetime(
            frame["exit_time_utc"], utc=True
        )
    return frame


def _window_name(
    timestamp: pd.Timestamp,
    cfg: dict[str, Any],
) -> str:
    training_start, training_end = cfg["training_period"]
    if pd.Timestamp(training_start) <= timestamp <= pd.Timestamp(
        training_end
    ):
        return "TRAINING_2019_2020"
    for name, (start_raw, end_raw) in cfg[
        "evaluation_windows"
    ].items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def build_paired_points(
    source: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    include_outcomes: bool,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    strategy = cfg["strategy"]
    minutes = {
        int(value) for value in strategy["entry_minutes_utc"]
    }
    filtered = source[
        source["entry_time_utc"].dt.hour.eq(
            int(strategy["entry_hour_utc"])
        )
        & source["entry_time_utc"].dt.minute.isin(minutes)
        & source["entry_time_utc"].dt.weekday.lt(5)
    ].copy()
    long_rows = filtered[filtered["side"].eq("LONG")].copy()
    short_rows = filtered[filtered["side"].eq("SHORT")].copy()
    shared = [
        "signal_time_utc",
        "completion_time_utc",
        "entry_time_utc",
    ]
    long_rows = long_rows.drop(columns=["side"])
    short_rows = short_rows.drop(columns=["side"])
    paired = long_rows.merge(
        short_rows,
        on=shared,
        how="inner",
        suffixes=("_long", "_short"),
        validate="one_to_one",
    )
    paired["eligible_date"] = paired[
        "entry_time_utc"
    ].dt.strftime("%Y-%m-%d")
    paired["clock_minute"] = paired["entry_time_utc"].dt.minute
    paired["decision_id"] = paired["entry_time_utc"].dt.strftime(
        "%Y-%m-%dT%H%M"
    )
    for column in cfg["features"]["contrast_columns"]:
        paired[f"contrast_{column}"] = (
            paired[f"{column}_long"] - paired[f"{column}_short"]
        )
    expected = int(strategy["required_trades_per_eligible_day"])
    clock_counts = paired.groupby("eligible_date")[
        "clock_minute"
    ].nunique()
    complete_dates = set(clock_counts[clock_counts == expected].index)
    paired = paired[
        paired["eligible_date"].isin(complete_dates)
    ].copy()
    paired["window"] = paired["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    paired = paired.sort_values("entry_time_utc").reset_index(drop=True)
    if include_outcomes:
        paired["long_target_first"] = paired[
            "target_first_long"
        ].astype(bool)
        paired["short_target_first"] = paired[
            "target_first_short"
        ].astype(bool)
        paired["one_winner_label"] = (
            paired["long_target_first"]
            ^ paired["short_target_first"]
        )
        paired["preferred_long"] = paired["long_target_first"]
        paired["pair_label_known_time_utc"] = paired[
            ["exit_time_utc_long", "exit_time_utc_short"]
        ].max(axis=1)
    counts = paired.groupby("eligible_date").size()
    by_window: dict[str, Any] = {}
    for name in [
        "TRAINING_2019_2020",
        *cfg["evaluation_windows"].keys(),
    ]:
        subset = paired[paired["window"].eq(name)]
        by_window[name] = {
            "eligible_days": int(subset["eligible_date"].nunique()),
            "decision_points": int(len(subset)),
            "forced_trade_candidates": int(len(subset)),
        }
    eligible_days = int(paired["eligible_date"].nunique())
    exact_days = int((counts == expected).sum())
    census = {
        "fixed_clock_source_side_rows": int(len(filtered)),
        "paired_decision_points_before_complete_day_filter": int(
            len(long_rows.merge(
                short_rows,
                on=shared,
                how="inner",
                suffixes=("_long", "_short"),
            ))
        ),
        "eligible_complete_days": eligible_days,
        "paired_decision_points": int(len(paired)),
        "forced_trade_candidates": int(len(paired)),
        "days_exactly_four_candidates": exact_days,
        "eligible_day_exact_four_coverage": (
            exact_days / eligible_days if eligible_days else 0.0
        ),
        "by_window": by_window,
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Four-clock ranker census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return paired, census


def contrast_columns(cfg: dict[str, Any]) -> list[str]:
    return [
        f"contrast_{column}"
        for column in cfg["features"]["contrast_columns"]
    ]


def purged_training_points(
    points: pd.DataFrame,
    cutoff: pd.Timestamp,
) -> pd.DataFrame:
    return points[
        points["one_winner_label"]
        & points["entry_time_utc"].lt(cutoff)
        & points["pair_label_known_time_utc"].lt(cutoff)
    ].copy()


def fit_ranker(
    training: pd.DataFrame,
    inference: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[np.ndarray, pd.DataFrame]:
    minimum = int(cfg["model"]["minimum_training_one_winner_pairs"])
    if len(training) < minimum:
        raise RuntimeError(
            "Insufficient purged one-winner pairs: "
            f"{len(training)} < {minimum}"
        )
    columns = contrast_columns(cfg)
    scaler = StandardScaler()
    train_x = scaler.fit_transform(training[columns])
    labels = training["preferred_long"].astype(int)
    if labels.nunique() != 2:
        raise RuntimeError("Paired ranker training requires both classes")
    model_cfg = cfg["model"]
    model = LogisticRegression(
        penalty=model_cfg["penalty"],
        C=float(model_cfg["C"]),
        solver=model_cfg["solver"],
        max_iter=int(model_cfg["max_iter"]),
        class_weight=model_cfg["class_weight"],
        random_state=int(model_cfg["random_state"]),
    )
    model.fit(train_x, labels)
    probabilities = model.predict_proba(
        scaler.transform(inference[columns])
    )[:, 1]
    coefficients = pd.DataFrame(
        {
            "feature": columns,
            "coefficient": model.coef_[0],
            "training_mean": scaler.mean_,
            "training_scale": scaler.scale_,
        }
    ).sort_values("coefficient", ascending=False)
    return probabilities, coefficients


def route_predictions(
    points: pd.DataFrame,
    probabilities: np.ndarray,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(points) != len(probabilities):
        raise ValueError("Prediction count does not match decision points")
    threshold = float(cfg["model"]["decision_probability"])
    ticket_weight = float(
        cfg["execution"]["risk_per_trade_portfolio_r"]
    )
    predicted = points.copy()
    predicted["probability_long"] = probabilities
    predicted["chosen_side"] = np.where(
        probabilities >= threshold, "LONG", "SHORT"
    )
    records: list[dict[str, Any]] = []
    for _, point in predicted.iterrows():
        side = str(point["chosen_side"])
        suffix = "long" if side == "LONG" else "short"
        result_r = float(point[f"outcome_r_{suffix}"])
        risk = float(point[f"risk_distance_{suffix}"])
        stressed = result_r - 0.5 * PIP / risk
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "eligible_date": point["eligible_date"],
                "pair_id": point["decision_id"],
                "trade_id": f"{point['decision_id']}:{side}",
                "side": side,
                "clock_minute": int(point["clock_minute"]),
                "signal_time_utc": point["signal_time_utc"],
                "completion_time_utc": point[
                    "completion_time_utc"
                ],
                "entry_time_utc": point["entry_time_utc"],
                "exit_time_utc": point[f"exit_time_utc_{suffix}"],
                "entry_price": point[f"entry_price_{suffix}"],
                "stop_price": point[f"stop_price_{suffix}"],
                "target_price": point[f"target_price_{suffix}"],
                "exit_price": point[f"exit_price_{suffix}"],
                "exit_reason": point[f"exit_reason_{suffix}"],
                "risk_distance": risk,
                "risk_pips": point[f"risk_pips_{suffix}"],
                "r": result_r,
                "portfolio_r": result_r * ticket_weight,
                "extra_half_pip_stress_r": stressed,
                "extra_half_pip_stress_portfolio_r": (
                    stressed * ticket_weight
                ),
                "fixed_0p01_lot_usd": point[
                    f"fixed_0p01_lot_usd_{suffix}"
                ],
                "target_first": bool(
                    point[f"target_first_{suffix}"]
                ),
                "oracle_member": int(
                    point[f"oracle_member_{suffix}"]
                ),
                "probability_long": point["probability_long"],
                "one_winner_available": bool(
                    point["one_winner_label"]
                ),
                "preferred_side": (
                    "LONG"
                    if bool(point["preferred_long"])
                    else (
                        "SHORT"
                        if bool(point["short_target_first"])
                        else "NONE"
                    )
                ),
            }
        )
    trades = pd.DataFrame(records)
    predicted["chosen_target_first"] = np.where(
        predicted["chosen_side"].eq("LONG"),
        predicted["long_target_first"],
        predicted["short_target_first"],
    )
    predicted["direction_correct_when_available"] = (
        predicted["one_winner_label"]
        & predicted["chosen_target_first"]
    )
    return trades, predicted


def load_oracle(cfg: dict[str, Any]) -> pd.DataFrame:
    frame = pd.read_csv(PACKAGE_ROOT / cfg["oracle_source"])
    for column in ("entry_time_utc", "exit_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return (
        frame[frame["regime"].eq(cfg["oracle_regime"])]
        .sort_values(["entry_time_utc", "oracle_trade_number"])
        .reset_index(drop=True)
    )


def _period(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame[
        frame["entry_time_utc"].between(start, end, inclusive="both")
    ]


def _direction_metrics(predicted: pd.DataFrame) -> dict[str, Any]:
    available = predicted[predicted["one_winner_label"]]
    correct = int(
        available["direction_correct_when_available"].sum()
    )
    return {
        "decision_points": int(len(predicted)),
        "one_winner_points": int(len(available)),
        "no_winner_points": int(
            (~predicted["one_winner_label"]).sum()
        ),
        "correct_side_when_one_winner": correct,
        "conditional_direction_accuracy": (
            correct / len(available) if len(available) else 0.0
        ),
        "unconditional_target_first_rate": (
            float(predicted["chosen_target_first"].mean())
            if len(predicted)
            else 0.0
        ),
        "predicted_long_rate": (
            float(predicted["chosen_side"].eq("LONG").mean())
            if len(predicted)
            else 0.0
        ),
    }


def evaluate_windows(
    points: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    all_trades: list[pd.DataFrame] = []
    all_predictions: list[pd.DataFrame] = []
    all_coefficients: list[pd.DataFrame] = []
    window_results: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg[
        "evaluation_windows"
    ].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        training = purged_training_points(points, start)
        inference = _period(points, start, end).copy()
        probabilities, coefficients = fit_ranker(
            training, inference, cfg
        )
        trades, predicted = route_predictions(
            inference, probabilities, cfg
        )
        trades["evaluation_window"] = name
        predicted["evaluation_window"] = name
        coefficients["evaluation_window"] = name
        daily = aggregate_days(trades)
        ticket_metrics = payoff_metrics(trades)
        daily_metrics = payoff_metrics(daily)
        direction = _direction_metrics(predicted)
        active_days = active_weekday_fx_days(m5, start, end)
        ticket_metrics["active_weekdays"] = active_days
        ticket_metrics["trades_per_active_weekday"] = (
            len(trades) / active_days if active_days else 0.0
        )
        ticket_metrics["eligible_neutral_days"] = int(
            trades["eligible_date"].nunique()
        )
        ticket_metrics["trades_per_eligible_neutral_day"] = (
            len(trades)
            / ticket_metrics["eligible_neutral_days"]
            if ticket_metrics["eligible_neutral_days"]
            else 0.0
        )
        window_results[name] = {
            "training_one_winner_pairs": int(len(training)),
            "training_long_class_rate": float(
                training["preferred_long"].mean()
            ),
            "tickets": ticket_metrics,
            "daily_portfolio": daily_metrics,
            "direction_selection": direction,
        }
        all_trades.append(trades)
        all_predictions.append(predicted)
        all_coefficients.append(coefficients)
    return (
        pd.concat(all_trades, ignore_index=True),
        pd.concat(all_predictions, ignore_index=True),
        pd.concat(all_coefficients, ignore_index=True),
        window_results,
    )


def summarize(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
    window_results: dict[str, Any],
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
) -> dict[str, Any]:
    daily = aggregate_days(trades)
    overall = payoff_metrics(trades)
    daily_overall = payoff_metrics(daily)
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(remove_top_winners(trades))
    direction_overall = _direction_metrics(predictions)
    expected = int(
        cfg["strategy"]["required_trades_per_eligible_day"]
    )
    executed = trades.groupby("eligible_date").size()
    exact_days = int((executed == expected).sum())
    eligible_evaluation_days = sum(
        block["eligible_days"]
        for name, block in census["by_window"].items()
        if name != "TRAINING_2019_2020"
    )
    gate = cfg["admission"]
    window_checks = {
        name: (
            block["tickets"]["trades"]
            >= int(gate["minimum_trades_each_window"])
            and float(gate["minimum_win_rate"])
            <= block["tickets"]["win_rate"]
            <= float(gate["maximum_win_rate"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= block["tickets"]["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and block["tickets"]["profit_factor"]
            >= float(gate["minimum_profit_factor_each_window"])
            and block["tickets"]["expectancy_r"]
            > float(gate["minimum_expectancy_r_each_window"])
            and block["direction_selection"][
                "conditional_direction_accuracy"
            ]
            >= float(
                gate[
                    "minimum_conditional_direction_accuracy_each_window"
                ]
            )
            and block["daily_portfolio"]["profit_factor"]
            >= float(gate["minimum_daily_profit_factor_each_window"])
        )
        for name, block in window_results.items()
    }
    frequency = {
        "eligible_evaluation_days": int(eligible_evaluation_days),
        "executed_days": int(len(executed)),
        "days_exactly_four_executed_trades": exact_days,
        "eligible_day_exact_four_execution_coverage": (
            exact_days / eligible_evaluation_days
            if eligible_evaluation_days
            else 0.0
        ),
        "trades_per_eligible_day": (
            len(trades) / eligible_evaluation_days
            if eligible_evaluation_days
            else 0.0
        ),
    }
    recent_start, recent_end = map(
        pd.Timestamp, cfg["recent_six_months"]
    )
    recent_trades = _period(trades, recent_start, recent_end)
    recent_predictions = _period(
        predictions, recent_start, recent_end
    )
    recent_daily = aggregate_days(recent_trades)
    active_days = active_weekday_fx_days(
        m5, recent_start, recent_end
    )
    recent_eligible = int(
        recent_trades["eligible_date"].nunique()
    )
    return {
        "window_checks": window_checks,
        "overall_tickets": overall,
        "overall_daily_portfolio": daily_overall,
        "overall_direction_selection": direction_overall,
        "windows": window_results,
        "frequency": frequency,
        "robustness": {
            "top_5_percent_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
        },
        "recent_six_months": {
            "tickets": payoff_metrics(recent_trades),
            "daily_portfolio": payoff_metrics(recent_daily),
            "direction_selection": _direction_metrics(
                recent_predictions
            ),
            "active_weekdays": active_days,
            "eligible_neutral_days": recent_eligible,
            "trades_per_active_weekday": (
                len(recent_trades) / active_days
                if active_days
                else 0.0
            ),
            "trades_per_eligible_neutral_day": (
                len(recent_trades) / recent_eligible
                if recent_eligible
                else 0.0
            ),
        },
    }


def evaluate_oracle(
    trades: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    oracle = load_oracle(cfg)
    tolerance = int(
        cfg["oracle_matching"]["secondary_tolerance_minutes"]
    )
    starts = [
        pd.Timestamp(values[0])
        for values in cfg["evaluation_windows"].values()
    ]
    ends = [
        pd.Timestamp(values[1])
        for values in cfg["evaluation_windows"].values()
    ]
    overall, matches = oracle_match_metrics(
        trades, oracle, min(starts), max(ends), tolerance
    )
    by_window: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg[
        "evaluation_windows"
    ].items():
        metrics, _ = oracle_match_metrics(
            trades,
            oracle,
            pd.Timestamp(start_raw),
            pd.Timestamp(end_raw),
            tolerance,
        )
        by_window[name] = metrics
    return {"overall": overall, "windows": by_window}, matches


def admission(
    strategy: dict[str, Any],
    oracle: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[bool, dict[str, bool]]:
    gate = cfg["admission"]
    overall_oracle = oracle["overall"]
    checks = {
        "every_window": all(
            strategy["window_checks"].values()
        ),
        "overall_profit_factor": (
            strategy["overall_tickets"]["profit_factor"]
            >= float(gate["minimum_overall_profit_factor"])
        ),
        "overall_exact_oracle_precision": (
            overall_oracle["exact_precision"]
            >= float(gate["minimum_overall_exact_oracle_precision"])
        ),
        "overall_15m_oracle_precision": (
            overall_oracle["tolerant_precision"]
            >= float(gate["minimum_overall_15m_oracle_precision"])
        ),
        "stressed": (
            strategy["robustness"]["extra_half_pip_round_trip"][
                "net_r"
            ]
            > 0
            and strategy["robustness"][
                "extra_half_pip_round_trip"
            ]["profit_factor"]
            >= float(gate["minimum_stressed_profit_factor"])
        ),
        "top_winners_removed": (
            strategy["robustness"][
                "top_5_percent_winners_removed"
            ]["net_r"]
            > 0
        ),
        "daily_drawdown": (
            strategy["overall_daily_portfolio"][
                "max_drawdown_r"
            ]
            <= float(gate["maximum_daily_portfolio_drawdown_r"])
        ),
        "exact_four_frequency": (
            strategy["frequency"][
                "eligible_day_exact_four_execution_coverage"
            ]
            == 1.0
        ),
    }
    return all(checks.values()), checks


def run_census() -> dict[str, Any]:
    cfg = load_config()
    source = load_source(cfg, include_outcomes=False)
    _, census = build_paired_points(
        source,
        cfg,
        include_outcomes=False,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_four_clock_ranker() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    source = load_source(cfg, include_outcomes=True)
    points, census = build_paired_points(
        source,
        cfg,
        include_outcomes=True,
        enforce_frozen_census=True,
    )
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    trades, predictions, coefficients, windows = evaluate_windows(
        points, m5, cfg
    )
    strategy = summarize(
        trades,
        predictions,
        windows,
        m5,
        cfg,
        census,
    )
    oracle, matches = evaluate_oracle(trades, cfg)
    admitted, checks = admission(strategy, oracle, cfg)
    prospective_start = pd.Timestamp(
        cfg["prospective"]["start_utc"]
    )
    prospective_points = points[
        points["entry_time_utc"] >= prospective_start
    ]
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_FOUR_CLOCK_PAIRED_RANKER_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "causality": {
            "features": (
                "LONG-minus-SHORT contrasts from completed decision-time "
                "rows only"
            ),
            "label_purge": (
                "both entry and paired label-known time strictly before "
                "each inference window"
            ),
            "direction": (
                "fixed 0.5 paired probability; no threshold search or "
                "abstention"
            ),
            "future_information_in_inference": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "outcome_blind_census": census,
        "strategy": {
            "admitted": admitted,
            "admission_checks": checks,
            **strategy,
        },
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": cfg["prospective"]["start_utc"],
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": int(
                len(prospective_points)
            ),
            "status": (
                "WAITING_FOR_POST_LOCK_MARKET_DATA"
                if prospective_points.empty
                else "POST_LOCK_POINTS_AVAILABLE"
            ),
        },
        "verdict": (
            "The fixed paired ranker passed all historical gates; only "
            "post-lock rows may confirm it."
            if admitted
            else "The fixed paired ranker failed one or more frozen "
            "gates and is closed without repair."
        ),
    }
    return result, {
        "PAIRED_POINTS": points,
        "PREDICTIONS": predictions,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "COEFFICIENTS": coefficients,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "build_paired_points",
    "contrast_columns",
    "fit_ranker",
    "load_config",
    "load_source",
    "purged_training_points",
    "route_predictions",
    "run_census",
    "run_neutral_four_clock_ranker",
    "verify_lock",
    "write_json",
]
