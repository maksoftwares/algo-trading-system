from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor


MOMENTUM = "ML_M15_MOMENTUM_RANKER_V1"
REVERSION = "ML_M15_REVERSION_RANKER_V1"
FAMILIES = (MOMENTUM, REVERSION)
FEATURE_COLUMNS = (
    "dir_return_15m_atr",
    "dir_return_1h_atr",
    "dir_return_4h_atr",
    "dir_return_24h_atr",
    "range_atr",
    "atr_ratio",
    "body_fraction",
    "dir_close_location",
    "efficiency_ratio_16",
    "dir_ema32_distance_atr",
    "quote_intensity_ratio_m15",
    "dir_tick_imbalance_5m",
    "dir_tick_imbalance_15m",
    "m5_quote_intensity_ratio",
    "spread_atr",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
)


@dataclass(frozen=True)
class WalkForwardResult:
    candidates: pd.DataFrame
    selected_trades: pd.DataFrame
    stage_metrics: pd.DataFrame
    diagnostics: pd.DataFrame
    gate_audit: dict[str, Any]
    survivors: list[str]


def wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    previous = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - previous).abs(),
            (frame["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return wilder(true_range, period)


def prepare_m15(m15: pd.DataFrame, m5: pd.DataFrame) -> pd.DataFrame:
    frame = m15.copy()
    frame["atr14"] = atr(frame, 14)
    span = (frame["mid_high"] - frame["mid_low"]).replace(0.0, np.nan)
    frame["body_fraction"] = (frame["mid_close"] - frame["mid_open"]).abs() / span
    frame["close_location"] = (frame["mid_close"] - frame["mid_low"]) / span
    frame["return_1"] = frame["mid_close"] - frame["mid_close"].shift(1)
    frame["return_4"] = frame["mid_close"] - frame["mid_close"].shift(4)
    frame["return_16"] = frame["mid_close"] - frame["mid_close"].shift(16)
    frame["return_96"] = frame["mid_close"] - frame["mid_close"].shift(96)
    movement = frame["mid_close"].diff().abs().rolling(16, min_periods=16).sum()
    frame["efficiency_ratio_16"] = frame["return_16"].abs() / movement.replace(0.0, np.nan)
    frame["ema32"] = frame["mid_close"].ewm(span=32, adjust=False, min_periods=32).mean()
    frame["atr_ratio"] = frame["atr14"] / frame["atr14"].shift(1).rolling(96, min_periods=48).median()
    frame["quote_intensity_ratio_m15"] = frame["tick_count"] / frame["tick_count"].shift(1).rolling(20, min_periods=10).median()
    frame["prior_center32"] = frame["mid_close"].shift(1).rolling(32, min_periods=32).mean()
    frame["prior_scale32"] = frame["mid_close"].shift(1).rolling(32, min_periods=32).std(ddof=0)
    frame["z32"] = (frame["mid_close"] - frame["prior_center32"]) / frame["prior_scale32"].replace(0.0, np.nan)
    micro_columns = [
        "timestamp_utc",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "quote_intensity_ratio",
        "bid_close",
        "ask_close",
    ]
    missing = sorted(set(micro_columns).difference(m5.columns))
    if missing:
        raise ValueError(f"M5 feature cache is missing ML features: {missing}")
    micro = m5[micro_columns].rename(
        columns={
            "quote_intensity_ratio": "m5_quote_intensity_ratio",
            "bid_close": "m5_bid_close",
            "ask_close": "m5_ask_close",
        }
    )
    frame = pd.merge_asof(
        frame.sort_values("timestamp_utc"),
        micro.sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    hour = frame["timestamp_utc"].dt.hour + frame["timestamp_utc"].dt.minute / 60.0
    weekday = frame["timestamp_utc"].dt.weekday
    frame["hour_sin"] = np.sin(2.0 * np.pi * hour / 24.0)
    frame["hour_cos"] = np.cos(2.0 * np.pi * hour / 24.0)
    frame["weekday_sin"] = np.sin(2.0 * np.pi * weekday / 7.0)
    frame["weekday_cos"] = np.cos(2.0 * np.pi * weekday / 7.0)
    frame["spread_atr"] = (frame["m5_ask_close"] - frame["m5_bid_close"]) / frame["atr14"]
    return frame


def _family_candidates(
    frame: pd.DataFrame,
    mask: pd.Series,
    direction: pd.Series,
    family: str,
    stop_atr: float,
    target_r: float,
    maximum_hold_hours: float,
) -> pd.DataFrame:
    selected = frame.loc[mask].copy()
    if selected.empty:
        return pd.DataFrame()
    selected["direction_sign"] = direction.loc[selected.index].astype(int)
    selected["direction"] = np.where(selected["direction_sign"] > 0, "LONG", "SHORT")
    selected["family_id"] = family
    selected["signal_time"] = selected["timestamp_utc"]
    selected["atr_value"] = selected["atr14"]
    selected["stop_frozen"] = selected["mid_close"] - selected["direction_sign"] * stop_atr * selected["atr14"]
    selected["target_r"] = target_r
    selected["maximum_hold_hours"] = maximum_hold_hours
    selected["dir_return_15m_atr"] = selected["direction_sign"] * selected["return_1"] / selected["atr14"]
    selected["dir_return_1h_atr"] = selected["direction_sign"] * selected["return_4"] / selected["atr14"]
    selected["dir_return_4h_atr"] = selected["direction_sign"] * selected["return_16"] / selected["atr14"]
    selected["dir_return_24h_atr"] = selected["direction_sign"] * selected["return_96"] / selected["atr14"]
    selected["range_atr"] = (selected["mid_high"] - selected["mid_low"]) / selected["atr14"]
    selected["dir_close_location"] = np.where(
        selected["direction_sign"] > 0,
        selected["close_location"],
        1.0 - selected["close_location"],
    )
    selected["dir_ema32_distance_atr"] = selected["direction_sign"] * (
        selected["mid_close"] - selected["ema32"]
    ) / selected["atr14"]
    selected["dir_tick_imbalance_5m"] = selected["direction_sign"] * selected["tick_imbalance_5m"]
    selected["dir_tick_imbalance_15m"] = selected["direction_sign"] * selected["tick_imbalance_15m"]
    columns = [
        "family_id", "signal_time", "direction", "direction_sign", "stop_frozen",
        "atr_value", "target_r", "maximum_hold_hours", *FEATURE_COLUMNS,
    ]
    return selected[columns].reset_index(drop=True)


def generate_candidates(
    m15: pd.DataFrame, m5: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    frame = prepare_m15(m15, m5)
    momentum_settings = config["families"][MOMENTUM]
    momentum_direction = np.sign(frame["return_4"]).astype("Int64")
    momentum_mask = (
        np.isfinite(frame["atr14"])
        & (frame["return_4"].abs() / frame["atr14"] >= float(momentum_settings["momentum_atr_min"]))
        & ((frame["mid_close"] - frame["mid_open"]) * momentum_direction > 0)
        & (frame["body_fraction"] >= float(momentum_settings["body_fraction_min"]))
        & (frame["efficiency_ratio_16"] >= float(momentum_settings["efficiency_ratio_min"]))
    )
    reversion_settings = config["families"][REVERSION]
    reversion_direction = -np.sign(frame["z32"]).astype("Int64")
    reversion_mask = (
        np.isfinite(frame["atr14"])
        & (frame["z32"].abs() >= float(reversion_settings["z_min"]))
        & (frame["efficiency_ratio_16"] <= float(reversion_settings["efficiency_ratio_max"]))
    )
    candidates = pd.concat(
        [
            _family_candidates(
                frame, momentum_mask, momentum_direction, MOMENTUM,
                float(momentum_settings["stop_atr"]), float(momentum_settings["target_r"]),
                float(momentum_settings["maximum_hold_hours"]),
            ),
            _family_candidates(
                frame, reversion_mask, reversion_direction, REVERSION,
                float(reversion_settings["stop_atr"]), float(reversion_settings["target_r"]),
                float(reversion_settings["maximum_hold_hours"]),
            ),
        ],
        ignore_index=True,
    )
    finite_features = np.isfinite(candidates[list(FEATURE_COLUMNS)]).all(axis=1)
    return candidates.loc[finite_features].sort_values(
        ["signal_time", "family_id"], kind="mergesort"
    ).reset_index(drop=True)


def _execution_arrays(m5: pd.DataFrame) -> dict[str, Any]:
    return {
        "starts": m5["bar_start_utc"].dt.tz_localize(None).to_numpy(),
        "ends": m5["timestamp_utc"].dt.tz_localize(None).to_numpy(),
        **{
            column: m5[column].to_numpy(dtype=float)
            for column in (
                "bid_open", "bid_high", "bid_low", "bid_close",
                "ask_open", "ask_high", "ask_low", "ask_close",
            )
        },
    }


def _label_candidate(
    arrays: dict[str, Any], row: Any, execution: dict[str, Any]
) -> dict[str, Any] | None:
    signal_time = pd.Timestamp(row.signal_time).tz_localize(None).to_datetime64()
    entry_index = int(np.searchsorted(arrays["starts"], signal_time, side="left"))
    if entry_index >= len(arrays["starts"]):
        return None
    delay_minutes = (arrays["starts"][entry_index] - signal_time) / np.timedelta64(1, "m")
    if delay_minutes < 0 or delay_minutes > float(execution["maximum_entry_gap_minutes"]):
        return None
    direction = str(row.direction)
    entry = float(arrays["ask_open"][entry_index] if direction == "LONG" else arrays["bid_open"][entry_index])
    stop = float(row.stop_frozen)
    risk = entry - stop if direction == "LONG" else stop - entry
    atr_value = float(row.atr_value)
    if not np.isfinite(risk) or risk <= 0 or not np.isfinite(atr_value) or atr_value <= 0:
        return None
    stop_atr = risk / atr_value
    if not float(execution["minimum_stop_atr"]) <= stop_atr <= float(execution["maximum_stop_atr"]):
        return None
    spread = float(arrays["ask_open"][entry_index] - arrays["bid_open"][entry_index])
    if spread / risk > float(execution["maximum_entry_spread_r"]):
        return None
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None
    target = entry + float(row.target_r) * risk if direction == "LONG" else entry - float(row.target_r) * risk
    deadline = arrays["starts"][entry_index] + np.timedelta64(int(float(row.maximum_hold_hours) * 60), "m")
    end_index = min(
        len(arrays["starts"]),
        int(np.searchsorted(arrays["starts"], deadline, side="right")) + 1,
    )
    exit_index = entry_index
    exit_price = entry
    exit_reason = "END_OF_DATA"
    exit_at_open = False
    ambiguous = False
    for position in range(entry_index, end_index):
        if arrays["starts"][position] >= deadline:
            exit_index, exit_reason, exit_at_open = position, "MAX_HOLD", True
            exit_price = float(arrays["bid_open"][position] if direction == "LONG" else arrays["ask_open"][position])
            break
        if direction == "LONG":
            if arrays["bid_open"][position] < stop:
                exit_index, exit_price, exit_reason, exit_at_open = position, float(arrays["bid_open"][position]), "GAP_THROUGH_STOP", True
                break
            if arrays["bid_open"][position] >= target:
                exit_index, exit_price, exit_reason, exit_at_open = position, target, "TARGET_GAP_FROZEN_TARGET", True
                break
            stop_hit = arrays["bid_low"][position] <= stop
            target_hit = arrays["bid_high"][position] >= target
        else:
            if arrays["ask_open"][position] > stop:
                exit_index, exit_price, exit_reason, exit_at_open = position, float(arrays["ask_open"][position]), "GAP_THROUGH_STOP", True
                break
            if arrays["ask_open"][position] <= target:
                exit_index, exit_price, exit_reason, exit_at_open = position, target, "TARGET_GAP_FROZEN_TARGET", True
                break
            stop_hit = arrays["ask_high"][position] >= stop
            target_hit = arrays["ask_low"][position] <= target
        if stop_hit:
            exit_index, exit_price = position, stop
            ambiguous = bool(target_hit)
            exit_reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            break
        if target_hit:
            exit_index, exit_price, exit_reason = position, target, "TARGET"
            break
        exit_index = position
        exit_price = float(arrays["bid_close"][position] if direction == "LONG" else arrays["ask_close"][position])
    exit_time = arrays["starts"][exit_index] if exit_at_open else arrays["ends"][exit_index]
    sign = 1.0 if direction == "LONG" else -1.0
    net_r = sign * (exit_price - entry) / risk
    holding_days = max(0.0, float((exit_time - arrays["starts"][entry_index]) / np.timedelta64(1, "D")))
    extra_cost_r = (
        float(execution["extra_execution_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    stress_net_r = net_r - extra_cost_r - float(execution["stress_slippage_r"])
    return {
        "entry_time": pd.Timestamp(arrays["starts"][entry_index], tz="UTC"),
        "exit_time": pd.Timestamp(exit_time, tz="UTC"),
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "stop_atr": stop_atr,
        "entry_spread_r": spread / risk,
        "net_r": net_r,
        "stress_net_r": stress_net_r,
        "holding_minutes": float((exit_time - arrays["starts"][entry_index]) / np.timedelta64(1, "m")),
        "exit_reason": exit_reason,
        "ambiguous_m5": ambiguous,
        "current_account_feasible": risk_usd <= float(execution["current_account_risk_usd"]),
    }


def label_candidates(
    candidates: pd.DataFrame, m5: pd.DataFrame, execution: dict[str, Any]
) -> pd.DataFrame:
    arrays = _execution_arrays(m5)
    rows: list[dict[str, Any]] = []
    for candidate in candidates.itertuples(index=False):
        outcome = _label_candidate(arrays, candidate, execution)
        if outcome is None:
            continue
        row = candidate._asdict()
        row.update(outcome)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["signal_time", "family_id"], kind="mergesort"
    ).reset_index(drop=True)


def profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None if positive == 0 else float("inf")
    return positive / negative


def closed_drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def metrics(trades: pd.DataFrame, source_days: int, top_winners: int) -> dict[str, Any]:
    values = trades["stress_net_r"].astype(float) if not trades.empty else pd.Series(dtype=float)
    monthly = (
        trades.assign(month=trades["entry_time"].dt.tz_localize(None).dt.to_period("M"))
        .groupby("month", sort=True)["stress_net_r"].sum()
        if not trades.empty else pd.Series(dtype=float)
    )
    removed = values.drop(values.nlargest(min(top_winners, len(values))).index) if len(values) else values
    return {
        "trades": int(len(trades)),
        "source_days": int(source_days),
        "trades_per_source_day": len(trades) / source_days if source_days else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "positive_active_month_share": float((monthly > 0).mean()) if len(monthly) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "current_account_feasible_share": float(trades["current_account_feasible"].mean()) if not trades.empty else 0.0,
    }


def evaluate_gate(value: dict[str, Any], gate: dict[str, Any]) -> tuple[bool, dict[str, bool]]:
    pf = value["stress_pf"]
    checks = {
        "minimum_trades": value["trades"] >= int(gate["minimum_trades"]),
        "minimum_trades_per_source_day": value["trades_per_source_day"] >= float(gate["minimum_trades_per_source_day"]),
        "minimum_stress_pf": pf is not None and pf >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": value["average_stress_r"] >= float(gate["minimum_average_stress_r"]),
        "minimum_positive_active_month_share": value["positive_active_month_share"] >= float(gate["minimum_positive_active_month_share"]),
        "maximum_closed_drawdown_r": value["closed_drawdown_r"] <= float(gate["maximum_closed_drawdown_r"]),
        "top_winners_removed_positive": value["top_winners_removed_stress_net_r"] > 0,
    }
    return all(checks.values()), checks


def _source_days(m5: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(
        m5.loc[
            (m5["bar_start_utc"] >= start) & (m5["bar_start_utc"] < end),
            "bar_start_utc",
        ].dt.date.nunique()
    )


def _select_trades(
    scored: pd.DataFrame, threshold: float, execution: dict[str, Any]
) -> pd.DataFrame:
    eligible = scored.loc[scored["model_score"] >= threshold].sort_values(
        ["entry_time", "model_score"], ascending=[True, False], kind="mergesort"
    )
    selected: list[pd.Series] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for _, trade in eligible.iterrows():
        day = trade["entry_time"].date()
        if trade["entry_time"] < position_until or trade["entry_time"] < cooldown_until:
            continue
        if daily_count.get(day, 0) >= int(execution["maximum_trades_per_family_utc_day"]):
            continue
        selected.append(trade)
        position_until = trade["exit_time"]
        cooldown_until = trade["exit_time"] + pd.Timedelta(hours=float(execution["cooldown_hours"]))
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(selected)


def _model(config: dict[str, Any]) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        learning_rate=float(config["learning_rate"]),
        max_iter=int(config["max_iter"]),
        max_leaf_nodes=int(config["max_leaf_nodes"]),
        min_samples_leaf=int(config["min_samples_leaf"]),
        l2_regularization=float(config["l2_regularization"]),
        random_state=int(config["random_state"]),
    )


def _fit_score_stage(
    family_rows: pd.DataFrame,
    stage_rows: pd.DataFrame,
    stage_start: pd.Timestamp,
    model_config: dict[str, Any],
    execution: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    purge = pd.Timedelta(hours=float(model_config["purge_hours"]))
    history = family_rows.loc[family_rows["exit_time"] < stage_start - purge].sort_values(
        "signal_time", kind="mergesort"
    )
    split_index = int(len(history) * float(model_config["fit_history_share"]))
    if split_index <= 0 or split_index >= len(history):
        return pd.DataFrame(), {"status": "INSUFFICIENT_HISTORY", "history_rows": int(len(history))}
    calibration_start = history.iloc[split_index]["signal_time"]
    fit = history.loc[history["exit_time"] < calibration_start - purge]
    calibration = history.loc[history["signal_time"] >= calibration_start]
    if len(fit) < int(model_config["minimum_fit_rows"]) or len(calibration) < int(model_config["minimum_calibration_rows"]):
        return pd.DataFrame(), {
            "status": "INSUFFICIENT_FIT_OR_CALIBRATION_ROWS",
            "history_rows": int(len(history)),
            "fit_rows": int(len(fit)),
            "calibration_rows": int(len(calibration)),
        }
    estimator = _model(model_config)
    estimator.fit(fit[list(FEATURE_COLUMNS)], fit["stress_net_r"])
    calibration_scores = estimator.predict(calibration[list(FEATURE_COLUMNS)])
    threshold = max(
        0.0,
        float(np.quantile(calibration_scores, float(model_config["calibration_quantile"]))),
    )
    scored = stage_rows.copy()
    scored["model_score"] = estimator.predict(scored[list(FEATURE_COLUMNS)])
    scored["model_threshold"] = threshold
    selected = _select_trades(scored, threshold, execution)
    calibration_correlation = pd.Series(calibration_scores).corr(
        calibration["stress_net_r"].reset_index(drop=True), method="spearman"
    )
    diagnostics = {
        "status": "SCORED",
        "history_rows": int(len(history)),
        "fit_rows": int(len(fit)),
        "calibration_rows": int(len(calibration)),
        "evaluation_candidate_rows": int(len(stage_rows)),
        "threshold": threshold,
        "calibration_score_mean": float(np.mean(calibration_scores)),
        "calibration_spearman": float(calibration_correlation) if np.isfinite(calibration_correlation) else 0.0,
        "selected_rows": int(len(selected)),
        "selected_score_mean": float(selected["model_score"].mean()) if not selected.empty else 0.0,
    }
    return selected, diagnostics


def run_walk_forward(
    labeled: pd.DataFrame, m5: pd.DataFrame, config: dict[str, Any]
) -> WalkForwardResult:
    selected_rows: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {family: {} for family in FAMILIES}
    exam_selected: dict[str, pd.DataFrame] = {}
    for family in FAMILIES:
        family_rows = labeled.loc[labeled["family_id"].eq(family)].copy()
        eligible = True
        for stage in ("train", "validation", "internal_test", "exam"):
            start, end = map(pd.Timestamp, config["windows"][stage])
            evaluation = family_rows.loc[
                (family_rows["entry_time"] >= start) & (family_rows["entry_time"] < end)
            ]
            selected, diagnostic = _fit_score_stage(
                family_rows, evaluation, start, config["model"], config["execution"]
            )
            if not selected.empty:
                selected = selected.copy()
                selected["stage"] = stage
                selected_rows.append(selected)
            if stage == "exam":
                exam_selected[family] = selected
            days = _source_days(m5, start, end)
            gate = config["gates"][stage]
            value = metrics(selected, days, int(gate["top_winners_removed"]))
            raw_pass, checks = evaluate_gate(value, gate)
            decision_eligible = bool(eligible)
            promoted = bool(eligible and raw_pass)
            audit[family][stage] = {
                "decision_eligible": decision_eligible,
                "raw_gate_pass": raw_pass,
                "promoted": promoted,
                "checks": checks,
                "metrics": value,
                "model": diagnostic,
            }
            metric_rows.append(
                {
                    "family_id": family, "stage": stage,
                    "decision_eligible": decision_eligible,
                    "raw_gate_pass": raw_pass, "promoted": promoted, **value,
                }
            )
            diagnostic_rows.append({"family_id": family, "stage": stage, **diagnostic})
            eligible = promoted
        tail_start, tail_end = map(pd.Timestamp, config["windows"]["recent_tail"])
        tail = exam_selected.get(family, pd.DataFrame())
        if not tail.empty:
            tail = tail.loc[(tail["entry_time"] >= tail_start) & (tail["entry_time"] < tail_end)].copy()
            tail["stage"] = "recent_tail"
        days = _source_days(m5, tail_start, tail_end)
        gate = config["gates"]["recent_tail"]
        value = metrics(tail, days, int(gate["top_winners_removed"]))
        raw_pass, checks = evaluate_gate(value, gate)
        decision_eligible = bool(eligible)
        promoted = bool(eligible and raw_pass)
        audit[family]["recent_tail"] = {
            "decision_eligible": decision_eligible,
            "raw_gate_pass": raw_pass,
            "promoted": promoted,
            "checks": checks,
            "metrics": value,
            "model": {"status": "EXAM_MODEL_SUBSET_NO_REFIT"},
        }
        metric_rows.append(
            {
                "family_id": family, "stage": "recent_tail",
                "decision_eligible": decision_eligible,
                "raw_gate_pass": raw_pass, "promoted": promoted, **value,
            }
        )
        diagnostic_rows.append(
            {"family_id": family, "stage": "recent_tail", "status": "EXAM_MODEL_SUBSET_NO_REFIT"}
        )
    survivors = [family for family in FAMILIES if audit[family]["recent_tail"]["promoted"]]
    selected_frame = pd.concat(selected_rows, ignore_index=True) if selected_rows else pd.DataFrame()
    return WalkForwardResult(
        candidates=labeled,
        selected_trades=selected_frame,
        stage_metrics=pd.DataFrame(metric_rows),
        diagnostics=pd.DataFrame(diagnostic_rows),
        gate_audit=audit,
        survivors=survivors,
    )


def independence_audit(
    trades: pd.DataFrame, survivors: list[str], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    all_pass = True
    limits = config["portfolio_gates"]
    threshold = pd.Timedelta(minutes=float(limits["same_opportunity_minutes"]))
    for left_id, right_id in combinations(survivors, 2):
        left = trades.loc[trades["family_id"].eq(left_id)].sort_values("entry_time")
        right = trades.loc[trades["family_id"].eq(right_id)].sort_values("entry_time")
        overlap = 0
        for _, trade in left.iterrows():
            deltas = (
                right.loc[right["direction"].eq(trade["direction"]), "entry_time"]
                - trade["entry_time"]
            ).abs()
            overlap += int(bool(len(deltas) and deltas.min() <= threshold))
        overlap_share = overlap / max(1, min(len(left), len(right)))
        left_daily = left.assign(date=left["entry_time"].dt.date).groupby("date")["stress_net_r"].sum()
        right_daily = right.assign(date=right["entry_time"].dt.date).groupby("date")["stress_net_r"].sum()
        joined = pd.concat([left_daily, right_daily], axis=1, keys=["left", "right"]).fillna(0.0)
        correlation = float(joined["left"].corr(joined["right"])) if len(joined) >= 3 else 0.0
        if not np.isfinite(correlation):
            correlation = 0.0
        passed = (
            overlap_share <= float(limits["maximum_same_direction_overlap_share"])
            and abs(correlation) <= float(limits["maximum_absolute_daily_pnl_correlation"])
        )
        all_pass &= passed
        rows.append(
            {
                "left": left_id, "right": right_id,
                "same_direction_overlap_share": overlap_share,
                "daily_stress_pnl_correlation": correlation,
                "pass": bool(passed),
            }
        )
    return rows, all_pass


def portfolio_exam(
    selected: pd.DataFrame, survivors: list[str], m5: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    start, end = map(pd.Timestamp, config["windows"]["exam"])
    source = selected.loc[
        selected["family_id"].isin(survivors)
        & selected["stage"].eq("exam")
        & (selected["entry_time"] >= start)
        & (selected["entry_time"] < end)
    ].sort_values(["entry_time", "model_score"], ascending=[True, False], kind="mergesort") if not selected.empty else selected
    limits = config["portfolio_gates"]
    accepted: list[pd.Series] = []
    active: list[pd.Timestamp] = []
    daily_counts: dict[Any, int] = {}
    for _, trade in source.iterrows():
        active = [exit_time for exit_time in active if exit_time > trade["entry_time"]]
        day = trade["entry_time"].date()
        if len(active) >= int(limits["maximum_concurrent_trades"]):
            continue
        if daily_counts.get(day, 0) >= int(limits["maximum_trades_per_utc_day"]):
            continue
        accepted.append(trade)
        active.append(trade["exit_time"])
        daily_counts[day] = daily_counts.get(day, 0) + 1
    portfolio = pd.DataFrame(accepted)
    value = metrics(portfolio, _source_days(m5, start, end), 5)
    checks = {
        "minimum_survivors": len(survivors) >= int(limits["minimum_survivors"]),
        "minimum_exam_trades_per_source_day": value["trades_per_source_day"] >= float(limits["minimum_exam_trades_per_source_day"]),
        "minimum_exam_stress_pf": value["stress_pf"] is not None and value["stress_pf"] >= float(limits["minimum_exam_stress_pf"]),
        "minimum_exam_average_stress_r": value["average_stress_r"] >= float(limits["minimum_exam_average_stress_r"]),
        "maximum_exam_closed_drawdown_r": value["closed_drawdown_r"] <= float(limits["maximum_exam_closed_drawdown_r"]),
    }
    independence, independent = independence_audit(source, survivors, config)
    checks["independence"] = independent
    return portfolio, {
        "metrics": value,
        "checks": checks,
        "independence": independence,
        "pass": all(checks.values()),
    }
