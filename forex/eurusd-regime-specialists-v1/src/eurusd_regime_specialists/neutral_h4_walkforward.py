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

from .neutral_h4_quiet_state_transfer import (
    PIP,
    PIP_VALUE_USD_001_LOT,
    PRICE_COLUMNS,
    add_h4_regimes,
    aggregate_h1,
    load_m5,
    summarize,
)
from .neutral_macro_pressure_reversal import (
    _effective_ask,
    _json_safe,
    _overlaps_quarantine,
    aggregate_h4,
    attach_macro_and_regime,
    load_macro,
)


SHARED_FEATURES = (
    "range_atr",
    "atr_ratio_126",
    "efficiency_24",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
)
SIGNED_FEATURES = (
    "return_1_atr",
    "return_3_atr",
    "return_6_atr",
    "return_24_atr",
    "body_atr",
    "ema20_distance_atr",
    "ema_slope_6_atr",
    "rsi_centered",
    "prior24_location",
    "macro_pressure_clipped",
    "real_yield_delta_clipped",
    "dollar_delta_clipped",
)
MODEL_FEATURES = SHARED_FEATURES + tuple(f"side_{name}" for name in SIGNED_FEATURES)


def add_features(h4: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    result = h4.copy()
    atr = result["atr"].replace(0.0, np.nan)
    for bars in (1, 3, 6, 24):
        result[f"return_{bars}_atr"] = (
            result["close"] - result["close"].shift(bars)
        ) / atr
    result["body_atr"] = (result["close"] - result["open"]) / atr
    result["range_atr"] = (result["high"] - result["low"]) / atr
    ema20 = result["close"].ewm(span=20, adjust=False, min_periods=20).mean()
    result["ema20_distance_atr"] = (result["close"] - ema20) / atr
    result["ema_slope_6_atr"] = (ema20 - ema20.shift(6)) / atr
    delta = result["close"].diff()
    gains = delta.clip(lower=0.0).rolling(14, min_periods=14).mean()
    losses = -delta.clip(upper=0.0).rolling(14, min_periods=14).mean()
    rs = gains / losses.replace(0.0, np.nan)
    result["rsi_centered"] = ((100.0 - 100.0 / (1.0 + rs)) - 50.0) / 50.0
    prior_high = result["high"].shift(1).rolling(24, min_periods=24).max()
    prior_low = result["low"].shift(1).rolling(24, min_periods=24).min()
    result["prior24_location"] = (
        2.0 * (result["close"] - prior_low) / (prior_high - prior_low) - 1.0
    )
    result["atr_ratio_126"] = atr / atr.shift(1).rolling(126, min_periods=126).median()
    result["efficiency_24"] = (
        (result["close"] - result["close"].shift(24)).abs()
        / result["close"].diff().abs().rolling(24, min_periods=24).sum()
    )
    hour_angle = 2.0 * math.pi * result["timestamp"].dt.hour / 24.0
    weekday_angle = 2.0 * math.pi * result["timestamp"].dt.dayofweek / 5.0
    result["hour_sin"] = np.sin(hour_angle)
    result["hour_cos"] = np.cos(hour_angle)
    result["weekday_sin"] = np.sin(weekday_angle)
    result["weekday_cos"] = np.cos(weekday_angle)
    clipping = config["model"]["macro_feature_clipping"]
    result["macro_pressure_clipped"] = result["macro_pressure_score"].clip(
        -float(clipping["macro_pressure_abs"]),
        float(clipping["macro_pressure_abs"]),
    )
    result["real_yield_delta_clipped"] = result["real_yield_delta_20d"].clip(
        -float(clipping["real_yield_delta_abs"]),
        float(clipping["real_yield_delta_abs"]),
    )
    result["dollar_delta_clipped"] = result["dollar_pct_20d"].clip(
        -float(clipping["dollar_delta_abs_pct"]),
        float(clipping["dollar_delta_abs_pct"]),
    )
    return result


def _execute_side(
    signal_index: int,
    direction: str,
    h4: pd.DataFrame,
    m5: pd.DataFrame,
    arrays: dict[str, np.ndarray],
    time_to_index: dict[pd.Timestamp, int],
    config: dict[str, Any],
) -> dict[str, Any] | None:
    execution = config["execution"]
    model = config["model"]
    entry_h4_index = signal_index + 1
    final_h4_index = entry_h4_index + int(model["maximum_hold_h4_bars"]) - 1
    if final_h4_index >= len(h4):
        return None
    entry_time = pd.Timestamp(h4["timestamp"].iloc[entry_h4_index])
    final_time = pd.Timestamp(h4["timestamp"].iloc[final_h4_index]) + pd.Timedelta(
        hours=3, minutes=55
    )
    entry_index = time_to_index.get(entry_time)
    final_index = time_to_index.get(final_time)
    if entry_index is None or final_index is None:
        return None

    spread_floor = float(execution["minimum_retail_spread_pips"]) * PIP
    slip = float(execution["adverse_slippage_pips_per_side"]) * PIP
    ask_open = _effective_ask(
        arrays["bid_open"][entry_index],
        arrays["ask_open"][entry_index],
        spread_floor,
    )
    spread_pips = (ask_open - arrays["bid_open"][entry_index]) / PIP
    if spread_pips > float(execution["maximum_entry_spread_pips"]):
        return None
    stop_distance = float(model["stop_atr_multiple"]) * float(
        h4["atr"].iloc[signal_index]
    )
    if not math.isfinite(stop_distance) or stop_distance <= 0.0:
        return None
    target_r = float(model["target_r_multiple"])
    if direction == "LONG":
        entry = ask_open + slip
        stop = entry - stop_distance
        target = entry + target_r * stop_distance
        exit_price = arrays["bid_close"][final_index] - slip
    else:
        entry = arrays["bid_open"][entry_index] - slip
        stop = entry + stop_distance
        target = entry - target_r * stop_distance
        exit_price = _effective_ask(
            arrays["bid_close"][final_index],
            arrays["ask_close"][final_index],
            spread_floor,
        ) + slip
    exit_index = final_index
    exit_reason = "TIME"

    for position in range(entry_index, final_index + 1):
        if direction == "LONG":
            bid_open = arrays["bid_open"][position]
            if bid_open <= stop:
                exit_index = position
                exit_price = min(bid_open, stop) - slip
                exit_reason = "STOP_GAP"
                break
            if bid_open >= target:
                exit_index = position
                exit_price = max(bid_open, target) - slip
                exit_reason = "TARGET_GAP"
                break
            if arrays["bid_low"][position] <= stop:
                exit_index = position
                exit_price = stop - slip
                exit_reason = "STOP"
                break
            if arrays["bid_high"][position] >= target:
                exit_index = position
                exit_price = target - slip
                exit_reason = "TARGET"
                break
        else:
            ask_position_open = _effective_ask(
                arrays["bid_open"][position],
                arrays["ask_open"][position],
                spread_floor,
            )
            ask_high = _effective_ask(
                arrays["bid_high"][position],
                arrays["ask_high"][position],
                spread_floor,
            )
            ask_low = _effective_ask(
                arrays["bid_low"][position],
                arrays["ask_low"][position],
                spread_floor,
            )
            if ask_position_open >= stop:
                exit_index = position
                exit_price = max(ask_position_open, stop) + slip
                exit_reason = "STOP_GAP"
                break
            if ask_position_open <= target:
                exit_index = position
                exit_price = min(ask_position_open, target) + slip
                exit_reason = "TARGET_GAP"
                break
            if ask_high >= stop:
                exit_index = position
                exit_price = stop + slip
                exit_reason = "STOP"
                break
            if ask_low <= target:
                exit_index = position
                exit_price = target + slip
                exit_reason = "TARGET"
                break

    exit_time = pd.Timestamp(m5["timestamp"].iloc[exit_index])
    if _overlaps_quarantine(
        entry_time, exit_time + pd.Timedelta(minutes=5), config["source"]
    ):
        return None
    net_pips = (
        (exit_price - entry) / PIP
        if direction == "LONG"
        else (entry - exit_price) / PIP
    )
    stop_pips = stop_distance / PIP
    net_r = net_pips / stop_pips
    return {
        "entry_time_utc": entry_time,
        "exit_time_utc": exit_time,
        "entry_index": entry_index,
        "exit_index": exit_index,
        "entry": entry,
        "stop": stop,
        "target": target,
        "exit": exit_price,
        "entry_spread_pips": spread_pips,
        "stop_pips": stop_pips,
        "net_pips": net_pips,
        "r": net_r,
        "stress_r": net_r
        - float(execution["extra_round_trip_stress_pips"]) / stop_pips,
        "pnl_usd_001_lot": net_pips * PIP_VALUE_USD_001_LOT,
        "exit_reason": exit_reason,
        "target_hit": exit_reason.startswith("TARGET"),
    }


def build_side_candidates(
    h4: pd.DataFrame, m5: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    arrays = {name: m5[name].to_numpy(dtype=float) for name in PRICE_COLUMNS}
    time_to_index = {
        pd.Timestamp(value): index
        for index, value in enumerate(m5["timestamp"].to_numpy())
    }
    neutral = set(config["ownership"]["neutral_regimes"])
    start = pd.Timestamp(config["model"]["candidate_start_utc"])
    records: list[dict[str, Any]] = []
    finite_columns = list(SHARED_FEATURES + SIGNED_FEATURES)
    for signal_index in range(len(h4) - 1):
        row = h4.iloc[signal_index]
        if row["timestamp"] < start or row["regime"] not in neutral:
            continue
        if not all(math.isfinite(float(row[name])) for name in finite_columns):
            continue
        signal_id = f"{pd.Timestamp(row['timestamp']).isoformat()}"
        for direction, side_sign in (("LONG", 1.0), ("SHORT", -1.0)):
            outcome = _execute_side(
                signal_index,
                direction,
                h4,
                m5,
                arrays,
                time_to_index,
                config,
            )
            if outcome is None:
                continue
            record: dict[str, Any] = {
                "signal_id": signal_id,
                "signal_index": signal_index,
                "signal_time_utc": row["timestamp"],
                "signal_regime": row["regime"],
                "direction": direction,
                "side_sign": side_sign,
                "macro_available_utc": row["macro_available_utc"],
            }
            record.update(outcome)
            for name in SHARED_FEATURES:
                record[name] = float(row[name])
            for name in SIGNED_FEATURES:
                record[f"side_{name}"] = side_sign * float(row[name])
            records.append(record)
    return pd.DataFrame(records)


def walkforward_select(
    candidates: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    model_config = config["model"]
    evaluation_start = pd.Timestamp(model_config["evaluation_start_utc"])
    evaluation_end = pd.Timestamp(model_config["evaluation_end_exclusive_utc"])
    months = pd.date_range(evaluation_start, evaluation_end, freq="MS", inclusive="left")
    selected: list[pd.DataFrame] = []
    model_records: list[dict[str, Any]] = []
    for month_start in months:
        month_end = min(month_start + pd.offsets.MonthBegin(1), evaluation_end)
        train_start = month_start - pd.DateOffset(
            years=int(model_config["trailing_training_years"])
        )
        train = candidates[
            (candidates["signal_time_utc"] >= train_start)
            & (candidates["exit_time_utc"] < month_start)
        ]
        score = candidates[
            (candidates["signal_time_utc"] >= month_start)
            & (candidates["signal_time_utc"] < month_end)
        ].copy()
        if (
            len(train) < int(model_config["minimum_training_side_rows"])
            or int(train["target_hit"].sum())
            < int(model_config["minimum_training_targets"])
            or score.empty
        ):
            model_records.append(
                {
                    "month": month_start.strftime("%Y-%m"),
                    "training_rows": len(train),
                    "training_targets": int(train["target_hit"].sum()),
                    "scored_rows": len(score),
                    "selected_signals": 0,
                    "status": "INSUFFICIENT_TRAINING_OR_NO_SCORE_ROWS",
                }
            )
            continue
        scaler = StandardScaler()
        train_x = scaler.fit_transform(train[list(MODEL_FEATURES)])
        classifier = LogisticRegression(
            C=float(model_config["logistic_c"]),
            penalty="l2",
            solver="lbfgs",
            max_iter=int(model_config["maximum_iterations"]),
            random_state=int(model_config["random_state"]),
        )
        classifier.fit(train_x, train["target_hit"].astype(int))
        score["predicted_target_probability"] = classifier.predict_proba(
            scaler.transform(score[list(MODEL_FEATURES)])
        )[:, 1]
        picks: list[pd.Series] = []
        for _, group in score.groupby("signal_id", sort=True):
            ordered = group.sort_values(
                ["predicted_target_probability", "direction"],
                ascending=[False, True],
            )
            best = ordered.iloc[0]
            second_probability = (
                float(ordered.iloc[1]["predicted_target_probability"])
                if len(ordered) > 1
                else 0.0
            )
            if (
                float(best["predicted_target_probability"])
                >= float(model_config["minimum_target_probability"])
                and float(best["predicted_target_probability"]) - second_probability
                >= float(model_config["minimum_side_probability_gap"])
            ):
                pick = best.copy()
                pick["opposite_side_probability"] = second_probability
                picks.append(pick)
        chosen = pd.DataFrame(picks)
        if not chosen.empty:
            selected.append(chosen)
        model_records.append(
            {
                "month": month_start.strftime("%Y-%m"),
                "training_start_utc": train_start.isoformat(),
                "training_cutoff_utc": month_start.isoformat(),
                "training_rows": len(train),
                "training_targets": int(train["target_hit"].sum()),
                "training_target_rate": float(train["target_hit"].mean()),
                "scored_rows": len(score),
                "selected_signals": len(chosen),
                "coefficient_l2_norm": float(np.linalg.norm(classifier.coef_[0])),
                "status": "FIT_PAST_ONLY",
            }
        )
    predictions = (
        pd.concat(selected, ignore_index=True) if selected else pd.DataFrame()
    )
    return predictions, model_records


def enforce_nonoverlap(predictions: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if predictions.empty:
        return predictions, 0
    kept: list[pd.Series] = []
    blocked_until = -1
    rejected = 0
    for _, row in predictions.sort_values("entry_time_utc").iterrows():
        if int(row["entry_index"]) <= blocked_until:
            rejected += 1
            continue
        kept.append(row)
        blocked_until = int(row["exit_index"])
    return pd.DataFrame(kept).reset_index(drop=True), rejected


def window_metrics(
    trades: pd.DataFrame, windows: dict[str, list[str]]
) -> dict[str, dict[str, Any]]:
    result = {}
    for name, (start, end) in windows.items():
        subset = trades[
            (trades["entry_time_utc"] >= pd.Timestamp(start))
            & (trades["entry_time_utc"] < pd.Timestamp(end))
        ] if not trades.empty else trades
        result[name] = summarize(subset)
    return result


def gate_results(
    metrics: dict[str, dict[str, Any]], gates: dict[str, Any]
) -> dict[str, bool]:
    full = metrics["FULL_WALKFORWARD"]
    latest = metrics["LATEST_12_MONTHS"]
    chronological = (
        "OOS_2020_2021",
        "OOS_2022_2023",
        "OOS_2024_2025",
        "OOS_2026_H1",
    )
    return {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "win_rate": float(gates["minimum_win_rate_inclusive"])
        <= full["win_rate"]
        <= float(gates["maximum_win_rate_inclusive"]),
        "payoff": float(gates["minimum_payoff_inclusive"])
        <= full["realized_payoff_ratio"]
        <= float(gates["maximum_payoff_inclusive"]),
        "profit_factor": full["profit_factor"]
        >= float(gates["minimum_profit_factor"]),
        "stressed_profit_factor": full["stress_profit_factor"]
        >= float(gates["minimum_stressed_profit_factor"]),
        "chronological_blocks": all(
            metrics[name]["profit_factor"]
            > float(gates["minimum_each_block_profit_factor_exclusive"])
            for name in chronological
        ),
        "latest_12_month_profit_factor": latest["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "latest_12_month_net_r": latest["net_r"]
        > float(gates["minimum_latest_12_month_net_r_exclusive"]),
        "positive_active_month_share": full["positive_active_month_share"]
        >= float(gates["minimum_positive_active_month_share"]),
        "winner_concentration": full["top_5pct_winners_removed_profit_factor"]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_drawdown_r"]),
    }


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    if tuple(config["model"]["model_features"]) != MODEL_FEATURES:
        raise RuntimeError("Frozen model feature order does not match implementation")
    m5 = load_m5(config["source"])
    macro = load_macro(config)
    h4 = aggregate_h4(m5)
    h1 = aggregate_h1(m5)
    _, regime_states = add_h4_regimes(h1, config["classifier"])
    h4 = attach_macro_and_regime(h4, macro, regime_states)
    h4 = add_features(h4, config)
    side_candidates = build_side_candidates(h4, m5, config)
    predictions, model_records = walkforward_select(side_candidates, config)
    trades, overlap_rejections = enforce_nonoverlap(predictions)
    metrics = window_metrics(trades, config["reporting_windows"])
    gates = gate_results(metrics, config["historical_quality_gates"])
    passed = all(gates.values())

    output_dir.mkdir(parents=True, exist_ok=True)
    side_candidates.to_csv(
        output_dir / "SIDE_CANDIDATES.csv", index=False, lineterminator="\n"
    )
    predictions.to_csv(
        output_dir / "MODEL_SELECTIONS.csv", index=False, lineterminator="\n"
    )
    trades.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    pd.DataFrame(model_records).to_csv(
        output_dir / "MONTHLY_MODELS.csv", index=False, lineterminator="\n"
    )
    result = {
        "schema_version": "eurusd_neutral_h4_walkforward_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": config["source"]["sha256"],
        "source_rows": len(m5),
        "h4_rows": len(h4),
        "side_candidate_rows": len(side_candidates),
        "model_selections_before_overlap": len(predictions),
        "overlap_rejections": overlap_rejections,
        "trades": len(trades),
        "windows": metrics,
        "gate_results": gates,
        "all_historical_quality_gates_passed": passed,
        "retrospective_causal_not_pristine_oos": True,
        "broker_action_allowed": False,
        "status": (
            "HISTORICAL_WALKFORWARD_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if passed
            else "REJECTED_H4_NEUTRAL_WALKFORWARD"
        ),
    }
    (output_dir / "RESULT.json").write_text(
        json.dumps(_json_safe(result), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result
