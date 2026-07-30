from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from .h4_chop_anchor_validation import _evaluation_subset, _scenario_summary
from .h4_trend_pullback_continuation import protected_date_overlap
from .neutral_h4_quiet_state_transfer import (
    PIP,
    PIP_VALUE_USD_001_LOT,
    load_m5,
    sha256_file,
)
from .retrospective_overfit import maximum_concurrent_positions


def load_opportunities(path: Path, expected_rows: int) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if len(frame) != int(expected_rows):
        raise RuntimeError("Opportunity ledger row count mismatch")
    for column in ("signal_time_utc", "entry_time_utc", "exit_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame["entry_date"] = frame["entry_time_utc"].dt.strftime("%Y-%m-%d")
    frame["stop_pips"] = frame["risk_distance"].astype(float) / PIP
    frame["pnl_usd_001_lot"] = frame["fixed_0p01_lot_usd"].astype(float)
    frame["stress_r"] = frame["r"].astype(float)
    return frame.sort_values(
        ["entry_time_utc", "owner_priority", "seed_priority"]
    ).reset_index(drop=True)


def build_daily_dataset(
    m5: pd.DataFrame,
    opportunities: pd.DataFrame,
    *,
    start_date: str,
    target_count: int,
) -> tuple[pd.DataFrame, list[str]]:
    market = m5.copy()
    market["date"] = market["timestamp"].dt.strftime("%Y-%m-%d")
    market["mid_open"] = (market["bid_open"] + market["ask_open"]) / 2.0
    market["mid_high"] = (market["bid_high"] + market["ask_high"]) / 2.0
    market["mid_low"] = (market["bid_low"] + market["ask_low"]) / 2.0
    market["mid_close"] = (market["bid_close"] + market["ask_close"]) / 2.0
    market["spread_pips"] = (
        market["ask_open"] - market["bid_open"]
    ) / PIP
    market["m5_change_pips"] = market.groupby("date")["mid_close"].diff() / PIP
    daily_market = market.groupby("date", sort=True).agg(
        market_open=("mid_open", "first"),
        market_high=("mid_high", "max"),
        market_low=("mid_low", "min"),
        market_close=("mid_close", "last"),
        m5_realized_volatility_pips=("m5_change_pips", "std"),
        mean_spread_pips=("spread_pips", "mean"),
        m5_bars=("timestamp", "size"),
    )
    daily_market["daily_range_pips"] = (
        daily_market["market_high"] - daily_market["market_low"]
    ) / PIP
    daily_market["daily_return_pips"] = (
        daily_market["market_close"] - daily_market["market_open"]
    ) / PIP
    daily_market["absolute_daily_return_pips"] = daily_market[
        "daily_return_pips"
    ].abs()
    daily_market.index = pd.to_datetime(daily_market.index)
    daily_market = daily_market[daily_market.index.weekday < 5].copy()

    counts = opportunities.groupby("entry_date").size().rename(
        "opportunity_count"
    )
    counts.index = pd.to_datetime(counts.index)
    owner_counts = (
        opportunities.pivot_table(
            index="entry_date",
            columns="owner",
            values="r",
            aggfunc="size",
            fill_value=0,
        )
        .add_prefix("owner_count_")
    )
    owner_counts.index = pd.to_datetime(owner_counts.index)
    frame = daily_market.join(counts, how="left").join(
        owner_counts, how="left"
    )
    count_columns = ["opportunity_count", *owner_counts.columns.tolist()]
    frame[count_columns] = frame[count_columns].fillna(0.0)
    frame = frame[frame.index >= pd.Timestamp(start_date)].copy()
    frame["target_exact_four"] = frame["opportunity_count"].eq(
        int(target_count)
    ).astype(int)

    features: list[str] = []
    frame["prior_opportunity_count"] = frame["opportunity_count"].shift(1)
    features.append("prior_opportunity_count")
    for window in (5, 20):
        lagged = frame["opportunity_count"].shift(1)
        mean_name = f"opportunity_count_mean_{window}"
        std_name = f"opportunity_count_std_{window}"
        frame[mean_name] = lagged.rolling(window, min_periods=window).mean()
        frame[std_name] = lagged.rolling(window, min_periods=window).std()
        features.extend([mean_name, std_name])
    for column in owner_counts.columns:
        name = f"prior_{column}"
        frame[name] = frame[column].shift(1)
        features.append(name)

    market_features = (
        "daily_range_pips",
        "daily_return_pips",
        "absolute_daily_return_pips",
        "m5_realized_volatility_pips",
        "mean_spread_pips",
    )
    for column in market_features:
        name = f"prior_{column}"
        frame[name] = frame[column].shift(1)
        features.append(name)
    for window in (5, 20):
        for column in ("daily_range_pips", "m5_realized_volatility_pips"):
            name = f"{column}_mean_{window}"
            frame[name] = (
                frame[column]
                .shift(1)
                .rolling(window, min_periods=window)
                .mean()
            )
            features.append(name)

    weekday = frame.index.weekday.to_numpy(dtype=float)
    month = frame.index.month.to_numpy(dtype=float)
    frame["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 5.0)
    frame["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 5.0)
    frame["month_sin"] = np.sin(2.0 * np.pi * (month - 1.0) / 12.0)
    frame["month_cos"] = np.cos(2.0 * np.pi * (month - 1.0) / 12.0)
    features.extend(["weekday_sin", "weekday_cos", "month_sin", "month_cos"])
    frame = frame.dropna(subset=features).copy()
    frame.index.name = "date"
    return frame, features


def make_model(contract: dict[str, Any]) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=int(contract["n_estimators"]),
        max_depth=int(contract["max_depth"]),
        min_samples_leaf=int(contract["min_samples_leaf"]),
        max_features=contract["max_features"],
        class_weight=contract["class_weight"],
        random_state=int(contract["random_state"]),
        n_jobs=int(contract["n_jobs"]),
    )


def predict_window(
    daily: pd.DataFrame,
    features: list[str],
    model_contract: dict[str, Any],
    *,
    training_start: str,
    window: list[str],
) -> pd.DataFrame:
    start, end = map(pd.Timestamp, window)
    training = daily[
        (daily.index >= pd.Timestamp(training_start)) & (daily.index < start)
    ]
    inference = daily[(daily.index >= start) & (daily.index < end)].copy()
    if training["target_exact_four"].nunique() != 2:
        raise RuntimeError("Training data does not contain both target classes")
    model = make_model(model_contract)
    model.fit(training[features], training["target_exact_four"])
    inference["probability_exact_four"] = model.predict_proba(
        inference[features]
    )[:, 1]
    inference["activated"] = inference["probability_exact_four"] >= float(
        model_contract["threshold"]
    )
    inference["training_rows"] = len(training)
    inference["training_positive_rate"] = training[
        "target_exact_four"
    ].mean()
    return inference.reset_index()


def select_causal_trades(
    opportunities: pd.DataFrame,
    decisions: pd.DataFrame,
    maximum_entries_per_date: int,
) -> pd.DataFrame:
    activated = set(
        decisions.loc[decisions["activated"], "date"].dt.strftime("%Y-%m-%d")
    )
    selected = opportunities[
        opportunities["entry_date"].isin(activated)
    ].copy()
    return (
        selected.sort_values(
            ["entry_time_utc", "owner_priority", "seed_priority"]
        )
        .groupby("entry_date", sort=True)
        .head(int(maximum_entries_per_date))
        .reset_index(drop=True)
    )


def apply_stress(trades: pd.DataFrame, extra_pips: float) -> pd.DataFrame:
    result = trades.copy()
    result["r"] = result["r"] - float(extra_pips) / result["stop_pips"]
    result["stress_r"] = result["r"]
    result["pnl_usd_001_lot"] = result["pnl_usd_001_lot"] - (
        float(extra_pips) * PIP_VALUE_USD_001_LOT
    )
    return result


def classification_metrics(decisions: pd.DataFrame) -> dict[str, Any]:
    activated = decisions["activated"]
    positives = decisions["target_exact_four"].eq(1)
    true_positive = int((activated & positives).sum())
    return {
        "weekdays": len(decisions),
        "activated_dates": int(activated.sum()),
        "actual_exact_four_dates": int(positives.sum()),
        "true_positive_dates": true_positive,
        "precision": (
            true_positive / int(activated.sum()) if activated.any() else 0.0
        ),
        "recall": (
            true_positive / int(positives.sum()) if positives.any() else 0.0
        ),
        "base_rate": float(positives.mean()) if len(decisions) else 0.0,
    }


def economic_metrics(
    trades: pd.DataFrame,
    decisions: pd.DataFrame,
    stress_pips: float,
) -> dict[str, Any]:
    summary = _scenario_summary(trades)
    stressed = _scenario_summary(apply_stress(trades, stress_pips))
    summary["trades_per_weekday"] = (
        len(trades) / len(decisions) if len(decisions) else 0.0
    )
    summary["active_date_coverage"] = (
        trades["entry_date"].nunique() / len(decisions)
        if len(decisions)
        else 0.0
    )
    summary["maximum_concurrent_positions"] = maximum_concurrent_positions(
        trades
    )
    return {"base": summary, "stressed": stressed}


def development_checks(
    economics: dict[str, Any],
    classification: dict[str, Any],
    yearly: dict[str, dict[str, Any]],
    gates: dict[str, Any],
) -> dict[str, bool]:
    base = economics["base"]
    return {
        "minimum_activated_dates": classification["activated_dates"]
        >= int(gates["minimum_activated_dates"]),
        "minimum_trades": base["trades"] >= int(gates["minimum_trades"]),
        "minimum_trades_per_weekday": base["trades_per_weekday"]
        >= float(gates["minimum_trades_per_weekday"]),
        "minimum_exact_four_precision": classification["precision"]
        >= float(gates["minimum_exact_four_precision"]),
        "minimum_profit_factor": base["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": economics["stressed"][
            "profit_factor"
        ]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_development_year_profit_factor": all(
            item["economics"]["base"]["profit_factor"]
            > float(
                gates[
                    "minimum_each_development_year_profit_factor_exclusive"
                ]
            )
            for item in yearly.values()
        ),
        "top_5pct_winners_removed_profit_factor": base[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": base["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
    }


def validation_checks(
    economics: dict[str, Any],
    classification: dict[str, Any],
    windows: dict[str, dict[str, Any]],
    overlap: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    base = economics["base"]
    return {
        "minimum_activated_dates": classification["activated_dates"]
        >= int(gates["minimum_activated_dates"]),
        "minimum_trades": base["trades"] >= int(gates["minimum_trades"]),
        "minimum_trades_per_weekday": base["trades_per_weekday"]
        >= float(gates["minimum_trades_per_weekday"]),
        "minimum_exact_four_precision": classification["precision"]
        >= float(gates["minimum_exact_four_precision"]),
        "minimum_profit_factor": base["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "minimum_stressed_profit_factor": economics["stressed"][
            "profit_factor"
        ]
        >= float(gates["minimum_stressed_profit_factor"]),
        "each_validation_window_profit_factor": all(
            windows[name]["economics"]["base"]["profit_factor"]
            > float(
                gates[
                    "minimum_each_validation_window_profit_factor_exclusive"
                ]
            )
            for name in (
                "VALIDATION_2024",
                "VALIDATION_2025",
                "VALIDATION_2026_H1",
            )
        ),
        "latest_12_month_profit_factor": windows["LATEST_12_MONTHS"][
            "economics"
        ]["base"]["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "top_5pct_winners_removed_profit_factor": base[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": base["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
        "minimum_unique_dates_per_broker_weekday": overlap[
            "unique_dates_per_broker_weekday"
        ]
        >= float(gates["minimum_unique_dates_per_broker_weekday"]),
        "maximum_protected_date_overlap_share": overlap[
            "protected_overlap_share"
        ]
        <= float(gates["maximum_protected_date_overlap_share"]),
    }


def window_result(
    opportunities: pd.DataFrame,
    decisions: pd.DataFrame,
    execution: dict[str, Any],
) -> dict[str, Any]:
    trades = select_causal_trades(
        opportunities,
        decisions,
        int(execution["maximum_entries_per_utc_date"]),
    )
    return {
        "classification": classification_metrics(decisions),
        "economics": economic_metrics(
            trades,
            decisions,
            float(execution["extra_round_trip_stress_pips"]),
        ),
        "trades": trades,
    }


def render_report(result: dict[str, Any]) -> str:
    dev = result["development"]
    base = dev["economics"]["base"]
    if result["validation"] is None:
        validation_text = "Locked validation remained unopened."
    else:
        validation = result["validation"]
        val_base = validation["economics"]["base"]
        validation_text = f"""| Trades | Trades/weekday | Activated dates | Exact-four precision | PF | Stressed PF | Admitted |
|---:|---:|---:|---:|---:|---:|---:|
| {val_base["trades"]} | {val_base["trades_per_weekday"]:.3f} | {validation["classification"]["activated_dates"]} | {validation["classification"]["precision"]:.2%} | {val_base["profit_factor"]:.3f} | {validation["economics"]["stressed"]["profit_factor"]:.3f} | {validation["admitted"]} |"""
    return f"""# EURUSD causal opportunity-density day gate result

Status: **{result["status"]}**

Demo-order authorization: **false**

## Development 2022-2023

| Trades | Trades/weekday | Activated dates | Exact-four precision | PF | Stressed PF | Selected |
|---:|---:|---:|---:|---:|---:|---:|
| {base["trades"]} | {base["trades_per_weekday"]:.3f} | {dev["classification"]["activated_dates"]} | {dev["classification"]["precision"]:.2%} | {base["profit_factor"]:.3f} | {dev["economics"]["stressed"]["profit_factor"]:.3f} | {dev["selected"]} |

## Locked validation

{validation_text}

The classifier uses no same-day information at inference. No threshold rescue
or broker action is authorized.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    root = config_path.parent.parent
    anchor_path = root / config["anchor_config"]["path"]
    opportunity_path = root / config["opportunity_ledger"]["path"]
    protected_path = root / config["protected_broker_ledger"]["path"]
    for path, expected in (
        (anchor_path, config["anchor_config"]["sha256"]),
        (opportunity_path, config["opportunity_ledger"]["sha256"]),
        (protected_path, config["protected_broker_ledger"]["sha256"]),
    ):
        if sha256_file(path) != expected:
            raise RuntimeError(f"Source checksum mismatch: {path}")
    anchor = json.loads(anchor_path.read_bytes())
    m5 = load_m5(anchor["source"])
    opportunities = load_opportunities(
        opportunity_path, int(config["opportunity_ledger"]["rows"])
    )
    daily, features = build_daily_dataset(
        m5,
        opportunities,
        start_date=config["walk_forward"]["initial_training_start"],
        target_count=int(config["day_target"]["target_count"]),
    )

    def predictions_for(
        windows: dict[str, list[str]], names: list[str]
    ) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
        pieces = []
        per_window: dict[str, dict[str, Any]] = {}
        for name in names:
            decisions = predict_window(
                daily,
                features,
                config["model"],
                training_start=config["walk_forward"][
                    "initial_training_start"
                ],
                window=windows[name],
            )
            result = window_result(
                opportunities, decisions, config["execution"]
            )
            pieces.append(decisions)
            per_window[name] = {
                "classification": result["classification"],
                "economics": result["economics"],
            }
        return pd.concat(pieces, ignore_index=True), per_window

    dev_windows = config["walk_forward"]["development_windows"]
    dev_decisions, dev_yearly = predictions_for(
        dev_windows, ["DEVELOPMENT_2022", "DEVELOPMENT_2023"]
    )
    dev_result = window_result(
        opportunities, dev_decisions, config["execution"]
    )
    dev_checks = development_checks(
        dev_result["economics"],
        dev_result["classification"],
        dev_yearly,
        config["development_admission"],
    )
    selected = all(dev_checks.values())
    validation: dict[str, Any] | None = None
    validation_decisions = pd.DataFrame()
    validation_trades = pd.DataFrame()

    if selected:
        val_windows = config["walk_forward"]["locked_validation_windows"]
        validation_decisions, val_yearly = predictions_for(
            val_windows,
            ["VALIDATION_2024", "VALIDATION_2025", "VALIDATION_2026_H1"],
        )
        val_result = window_result(
            opportunities, validation_decisions, config["execution"]
        )
        validation_trades = val_result["trades"]
        latest_decisions = validation_decisions[
            (validation_decisions["date"] >= pd.Timestamp("2025-07-01"))
            & (validation_decisions["date"] < pd.Timestamp("2026-07-01"))
        ].copy()
        latest = window_result(
            opportunities, latest_decisions, config["execution"]
        )
        val_yearly["LATEST_12_MONTHS"] = {
            "classification": latest["classification"],
            "economics": latest["economics"],
        }
        protected = pd.read_csv(protected_path)
        overlap = protected_date_overlap(
            _evaluation_subset(
                validation_trades,
                ["2024-07-01T00:00:00Z", "2026-07-01T00:00:00Z"],
            ),
            set(protected["entry_date"].astype(str)),
            broker_weekdays=int(
                config["protected_broker_ledger"]["weekdays"]
            ),
        )
        val_checks = validation_checks(
            val_result["economics"],
            val_result["classification"],
            val_yearly,
            overlap,
            config["locked_validation_admission"],
        )
        validation = {
            "classification": val_result["classification"],
            "economics": val_result["economics"],
            "windows": val_yearly,
            "protected_date_overlap": overlap,
            "checks": val_checks,
            "admitted": all(val_checks.values()),
        }

    if not selected:
        status = "DEVELOPMENT_REJECTED_VALIDATION_UNOPENED"
    elif validation is not None and validation["admitted"]:
        status = "HISTORICAL_CANDIDATE_REQUIRES_FRESH_CONFIRMATION"
    else:
        status = "LOCKED_VALIDATION_REJECTED"
    result = {
        "schema_version": "eurusd_causal_opportunity_density_day_gate_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor["source"]["sha256"],
        "opportunity_ledger_sha256": config["opportunity_ledger"]["sha256"],
        "feature_columns": features,
        "feature_count": len(features),
        "research_boundary": "RETROSPECTIVE_CAUSAL_NOT_PRISTINE_OOS",
        "broker_action_allowed": False,
        "demo_order_authorized": False,
        "development": {
            "classification": dev_result["classification"],
            "economics": dev_result["economics"],
            "windows": dev_yearly,
            "checks": dev_checks,
            "selected": selected,
        },
        "validation": validation,
        "status": status,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.concat(
        [
            dev_decisions.assign(stage="DEVELOPMENT"),
            validation_decisions.assign(stage="VALIDATION"),
        ],
        ignore_index=True,
    ).to_csv(output_dir / "DAY_DECISIONS.csv", index=False)
    pd.concat(
        [
            dev_result["trades"].assign(stage="DEVELOPMENT"),
            validation_trades.assign(stage="VALIDATION"),
        ],
        ignore_index=True,
    ).to_csv(output_dir / "TRADES.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result), encoding="utf-8"
    )
    return result
