from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ReplayResult:
    candidates: pd.DataFrame
    trades: pd.DataFrame


def wilder_atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous_close = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - previous_close).abs(),
            (frame["mid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result = pd.Series(np.nan, index=frame.index, dtype="float64")
    if len(true_range) < period:
        return result
    seed = true_range.iloc[:period]
    if seed.isna().any():
        return result
    result.iloc[period - 1] = seed.mean()
    for position in range(period, len(true_range)):
        result.iloc[position] = (
            result.iloc[position - 1] * (period - 1) + true_range.iloc[position]
        ) / period
    return result


def add_previous_levels(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    day = result["bar_start_utc"].dt.floor("D")
    daily = result.assign(_day=day).groupby("_day", sort=True).agg(
        prior_high_source=("mid_high", "max"),
        prior_low_source=("mid_low", "min"),
    )
    result["previous_daily_high"] = day.map(daily["prior_high_source"].shift(1))
    result["previous_daily_low"] = day.map(daily["prior_low_source"].shift(1))
    week = day - pd.to_timedelta(result["bar_start_utc"].dt.weekday, unit="D")
    weekly = result.assign(_week=week).groupby("_week", sort=True).agg(
        prior_high_source=("mid_high", "max"),
        prior_low_source=("mid_low", "min"),
    )
    result["previous_weekly_high"] = week.map(weekly["prior_high_source"].shift(1))
    result["previous_weekly_low"] = week.map(weekly["prior_low_source"].shift(1))
    return result


def confirmed_swings(
    frame: pd.DataFrame, kind: str, left: int, right: int
) -> pd.DataFrame:
    price_column = "mid_high" if kind == "HIGH" else "mid_low"
    prices = frame[price_column]
    mask = pd.Series(True, index=frame.index)
    for offset in range(1, left + 1):
        mask &= prices > prices.shift(offset) if kind == "HIGH" else prices < prices.shift(offset)
    for offset in range(1, right + 1):
        mask &= prices > prices.shift(-offset) if kind == "HIGH" else prices < prices.shift(-offset)
    rows: list[dict[str, Any]] = []
    for position in np.flatnonzero(mask.fillna(False).to_numpy()):
        available = position + right
        if available >= len(frame):
            continue
        rows.append(
            {
                "level_price": float(prices.iloc[position]),
                "swing_time_utc": frame["timestamp_utc"].iloc[position],
                "available_time_utc": frame["timestamp_utc"].iloc[available],
            }
        )
    return pd.DataFrame(
        rows,
        columns=("level_price", "swing_time_utc", "available_time_utc"),
    )


def _merge_latest_swing(
    frame: pd.DataFrame, swings: pd.DataFrame, label: str
) -> pd.DataFrame:
    price = f"latest_swing_{label}"
    swing_time = f"latest_swing_{label}_time_utc"
    available_time = f"latest_swing_{label}_available_time_utc"
    if swings.empty:
        frame[price] = np.nan
        frame[swing_time] = pd.NaT
        frame[available_time] = pd.NaT
        return frame
    right = swings.rename(
        columns={
            "level_price": price,
            "swing_time_utc": swing_time,
            "available_time_utc": available_time,
        }
    ).sort_values(available_time)
    return pd.merge_asof(
        frame.sort_values("timestamp_utc"),
        right[[available_time, price, swing_time]],
        left_on="timestamp_utc",
        right_on=available_time,
        direction="backward",
        allow_exact_matches=True,
    ).sort_values("timestamp_utc", kind="mergesort").reset_index(drop=True)


def prepare_features(frame: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    result = add_previous_levels(frame)
    result["atr14"] = wilder_atr(result, int(settings["atr_period"]))
    left = int(settings["swing_left_bars"])
    right = int(settings["swing_right_bars"])
    result = _merge_latest_swing(
        result, confirmed_swings(result, "HIGH", left, right), "high"
    )
    result = _merge_latest_swing(
        result, confirmed_swings(result, "LOW", left, right), "low"
    )
    return result


def _levels(
    arrays: dict[str, np.ndarray], position: int, direction: str, tolerance: float
) -> list[dict[str, Any]]:
    if direction == "LONG":
        raw = [
            ("previous_daily_high", arrays["previous_daily_high"][position], arrays["timestamp"][position]),
            ("previous_weekly_high", arrays["previous_weekly_high"][position], arrays["timestamp"][position]),
            ("latest_swing_high", arrays["latest_swing_high"][position], arrays["latest_swing_high_time"][position]),
        ]
    else:
        raw = [
            ("previous_daily_low", arrays["previous_daily_low"][position], arrays["timestamp"][position]),
            ("previous_weekly_low", arrays["previous_weekly_low"][position], arrays["timestamp"][position]),
            ("latest_swing_low", arrays["latest_swing_low"][position], arrays["latest_swing_low_time"][position]),
        ]
    available = [
        {"level_kind": kind, "level_price": float(price), "level_time": pd.Timestamp(time)}
        for kind, price, time in raw
        if pd.notna(price) and pd.notna(time)
    ]
    kept: list[dict[str, Any]] = []
    for level in sorted(available, key=lambda item: item["level_time"], reverse=True):
        if all(
            abs(level["level_price"] - previous["level_price"]) > tolerance
            for previous in kept
        ):
            kept.append(level)
    return sorted(kept, key=lambda item: item["level_time"])


def generate_candidates(
    frame: pd.DataFrame, settings: dict[str, Any], costs: dict[str, Any]
) -> pd.DataFrame:
    featured = prepare_features(frame, settings)
    arrays = {
        "timestamp": featured["timestamp_utc"].to_numpy(),
        "open": featured["mid_open"].to_numpy(dtype=float),
        "high": featured["mid_high"].to_numpy(dtype=float),
        "low": featured["mid_low"].to_numpy(dtype=float),
        "close": featured["mid_close"].to_numpy(dtype=float),
        "atr": featured["atr14"].to_numpy(dtype=float),
        "previous_daily_high": featured["previous_daily_high"].to_numpy(dtype=float),
        "previous_daily_low": featured["previous_daily_low"].to_numpy(dtype=float),
        "previous_weekly_high": featured["previous_weekly_high"].to_numpy(dtype=float),
        "previous_weekly_low": featured["previous_weekly_low"].to_numpy(dtype=float),
        "latest_swing_high": featured["latest_swing_high"].to_numpy(dtype=float),
        "latest_swing_low": featured["latest_swing_low"].to_numpy(dtype=float),
        "latest_swing_high_time": featured["latest_swing_high_time_utc"].to_numpy(),
        "latest_swing_low_time": featured["latest_swing_low_time_utc"].to_numpy(),
    }
    rows: list[dict[str, Any]] = []
    lookback = int(settings["break_lookback_bars"])
    level_tolerance = 10.0 * float(settings["point_size"])
    for confirmation in range(2, len(featured)):
        direction = ""
        if arrays["close"][confirmation] > arrays["open"][confirmation]:
            direction = "LONG"
        elif arrays["close"][confirmation] < arrays["open"][confirmation]:
            direction = "SHORT"
        if not direction:
            continue
        retest = confirmation - 1
        retest_atr = arrays["atr"][retest]
        if not np.isfinite(retest_atr):
            continue
        entry_trigger = (
            arrays["high"][retest] + float(settings["entry_buffer_price"])
            if direction == "LONG"
            else arrays["low"][retest] - float(settings["entry_buffer_price"])
        )
        stop = (
            arrays["low"][retest] - float(settings["stop_buffer_atr"]) * retest_atr
            if direction == "LONG"
            else arrays["high"][retest] + float(settings["stop_buffer_atr"]) * retest_atr
        )
        planned_risk = entry_trigger - stop if direction == "LONG" else stop - entry_trigger
        if planned_risk < float(settings["minimum_planned_stop_price"]):
            continue
        if planned_risk > float(settings["maximum_research_stop_price"]):
            continue
        estimated_cost_r = (
            float(costs["stress_spread_price"])
            + float(costs["extra_execution_cost_usd"])
        ) / (planned_risk * float(costs["ounces_at_0_01_lot"])) + float(costs["stress_slippage_r"])
        if estimated_cost_r > float(costs["maximum_estimated_cost_r"]):
            continue
        candidates: list[dict[str, Any]] = []
        for break_position in range(max(0, retest - lookback), retest):
            break_atr = arrays["atr"][break_position]
            if not np.isfinite(break_atr):
                continue
            for level in _levels(arrays, break_position, direction, level_tolerance):
                price = level["level_price"]
                if direction == "LONG":
                    if arrays["close"][break_position] < price + float(settings["break_distance_atr"]) * break_atr:
                        continue
                    if arrays["low"][retest] > price + float(settings["retest_tolerance_price"]):
                        continue
                    if arrays["close"][retest] < price:
                        continue
                else:
                    if arrays["close"][break_position] > price - float(settings["break_distance_atr"]) * break_atr:
                        continue
                    if arrays["high"][retest] < price - float(settings["retest_tolerance_price"]):
                        continue
                    if arrays["close"][retest] > price:
                        continue
                candidates.append(
                    {
                        "direction": direction,
                        "level_kind": level["level_kind"],
                        "level_price": price,
                        "level_time": level["level_time"],
                        "break_position": break_position,
                        "break_time": pd.Timestamp(arrays["timestamp"][break_position]),
                    }
                )
        if not candidates:
            continue
        selected = sorted(candidates, key=lambda item: item["level_time"])[0]
        signal_time = featured["timestamp_utc"].iloc[confirmation]
        rows.append(
            {
                "specialist_id": "COST_AWARE_BREAKOUT_RETEST_V2",
                "signal_time": signal_time,
                "direction": direction,
                "entry_trigger": entry_trigger,
                "stop_frozen": stop,
                "planned_risk_price": planned_risk,
                "estimated_cost_r": estimated_cost_r,
                "preferred_cost_r": estimated_cost_r <= float(costs["preferred_estimated_cost_r"]),
                "expires_after_bars": int(settings["pending_expiry_bars"]),
                "maximum_hold_hours": float(settings["maximum_hold_hours"]),
                "target_r": float(settings["target_r"]),
                "retest_time": featured["timestamp_utc"].iloc[retest],
                "confirmation_position": confirmation,
                "retest_position": retest,
                **selected,
            }
        )
    return pd.DataFrame(rows)


def _find_entry(
    m5: pd.DataFrame, signal: pd.Series, costs: dict[str, Any]
) -> tuple[int, float] | None:
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    signal_time = pd.Timestamp(signal["signal_time"])
    start = int(
        np.searchsorted(
            starts, np.datetime64(signal_time.tz_convert(None)), side="left"
        )
    )
    end = min(len(m5), start + int(signal["expires_after_bars"]))
    direction = str(signal["direction"])
    trigger = float(signal["entry_trigger"])
    for position in range(start, end):
        row = m5.iloc[position]
        spread = float(row["ask_open"] - row["bid_open"])
        if spread > float(costs["maximum_native_entry_spread_price"]):
            continue
        if direction == "LONG" and float(row["ask_high"]) >= trigger:
            return position, max(trigger, float(row["ask_open"]))
        if direction == "SHORT" and float(row["bid_low"]) <= trigger:
            return position, min(trigger, float(row["bid_open"]))
    return None


def _simulate(
    m5: pd.DataFrame,
    entry_index: int,
    entry: float,
    signal: pd.Series,
    settings: dict[str, Any],
    costs: dict[str, Any],
) -> dict[str, Any]:
    direction = str(signal["direction"])
    stop = float(signal["stop_frozen"])
    risk = entry - stop if direction == "LONG" else stop - entry
    risk_usd = risk * float(costs["ounces_at_0_01_lot"])
    if risk < float(settings["minimum_planned_stop_price"]):
        return {"accepted": False, "reason": "ACTUAL_RISK_BELOW_MINIMUM"}
    if risk > float(settings["maximum_research_stop_price"]):
        return {"accepted": False, "reason": "ACTUAL_RISK_ABOVE_MAXIMUM"}
    estimated_cost_r = (
        float(costs["stress_spread_price"])
        + float(costs["extra_execution_cost_usd"])
    ) / risk_usd + float(costs["stress_slippage_r"])
    if estimated_cost_r > float(costs["maximum_estimated_cost_r"]):
        return {"accepted": False, "reason": "ACTUAL_ESTIMATED_COST_R_LIMIT"}
    target = (
        entry + float(signal["target_r"]) * risk
        if direction == "LONG"
        else entry - float(signal["target_r"]) * risk
    )
    entry_row = m5.iloc[entry_index]
    deadline = entry_row["bar_start_utc"] + pd.Timedelta(
        hours=float(signal["maximum_hold_hours"])
    )
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    end = min(
        len(m5),
        int(
            np.searchsorted(
                starts, np.datetime64(deadline.tz_convert(None)), side="right"
            )
        )
        + 1,
    )
    exit_index = entry_index
    exit_price = entry
    exit_reason = "END_OF_DATA"
    exit_at_open = False
    ambiguous = False
    for position in range(entry_index, end):
        row = m5.iloc[position]
        if row["bar_start_utc"] >= deadline:
            exit_index, exit_reason, exit_at_open = position, "MAX_HOLD", True
            exit_price = float(
                row["bid_open"] if direction == "LONG" else row["ask_open"]
            )
            break
        if direction == "LONG":
            if float(row["bid_open"]) < stop:
                exit_index, exit_price, exit_reason, exit_at_open = (
                    position,
                    float(row["bid_open"]),
                    "GAP_THROUGH_STOP",
                    True,
                )
                break
            if float(row["bid_open"]) >= target:
                exit_index, exit_price, exit_reason, exit_at_open = (
                    position,
                    target,
                    "TARGET_GAP_FROZEN_TARGET",
                    True,
                )
                break
            stop_hit = float(row["bid_low"]) <= stop
            target_hit = float(row["bid_high"]) >= target
        else:
            if float(row["ask_open"]) > stop:
                exit_index, exit_price, exit_reason, exit_at_open = (
                    position,
                    float(row["ask_open"]),
                    "GAP_THROUGH_STOP",
                    True,
                )
                break
            if float(row["ask_open"]) <= target:
                exit_index, exit_price, exit_reason, exit_at_open = (
                    position,
                    target,
                    "TARGET_GAP_FROZEN_TARGET",
                    True,
                )
                break
            stop_hit = float(row["ask_high"]) >= stop
            target_hit = float(row["ask_low"]) <= target
        if stop_hit:
            exit_index, exit_price = position, stop
            ambiguous = bool(target_hit)
            exit_reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            break
        if target_hit:
            exit_index, exit_price, exit_reason = position, target, "TARGET"
            break
        exit_index = position
        exit_price = float(
            row["bid_close"] if direction == "LONG" else row["ask_close"]
        )
    exit_row = m5.iloc[exit_index]
    exit_time = (
        exit_row["bar_start_utc"] if exit_at_open else exit_row["timestamp_utc"]
    )
    sign = 1.0 if direction == "LONG" else -1.0
    baseline_net_r = sign * (exit_price - entry) / risk
    entry_spread = float(entry_row["ask_open"] - entry_row["bid_open"])
    exit_suffix = "open" if exit_at_open else "close"
    exit_spread = float(
        exit_row[f"ask_{exit_suffix}"] - exit_row[f"bid_{exit_suffix}"]
    )
    entry_mid = entry - 0.5 * entry_spread if direction == "LONG" else entry + 0.5 * entry_spread
    exit_mid = exit_price + 0.5 * exit_spread if direction == "LONG" else exit_price - 0.5 * exit_spread
    gross_mid_r = sign * (exit_mid - entry_mid) / risk
    holding_days = max(
        0.0,
        (exit_time - entry_row["bar_start_utc"]).total_seconds() / 86400.0,
    )
    stress_cost_price = (
        float(costs["stress_spread_price"])
        + float(costs["extra_execution_cost_usd"])
        + holding_days * float(costs["holding_cost_per_24h_usd"])
    )
    stress_net_r = (
        gross_mid_r
        - stress_cost_price / risk_usd
        - float(costs["stress_slippage_r"])
    )
    return {
        "accepted": True,
        "entry_time": entry_row["bar_start_utc"],
        "exit_time": exit_time,
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "risk_price": risk,
        "risk_usd": risk_usd,
        "estimated_cost_r_at_entry": estimated_cost_r,
        "preferred_cost_r": estimated_cost_r
        <= float(costs["preferred_estimated_cost_r"]),
        "baseline_net_r": baseline_net_r,
        "net_r": baseline_net_r,
        "gross_mid_r": gross_mid_r,
        "stress_net_r": stress_net_r,
        "holding_minutes": (
            exit_time - entry_row["bar_start_utc"]
        ).total_seconds()
        / 60.0,
        "exit_reason": exit_reason,
        "ambiguous_m5": ambiguous,
        "current_account_feasible": risk_usd
        <= float(costs["current_account_risk_usd"]),
    }


def replay(
    m5: pd.DataFrame, candidates: pd.DataFrame, config: dict[str, Any]
) -> ReplayResult:
    candidate_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    position_until = pd.Timestamp.min.tz_localize("UTC")
    for _, signal in candidates.sort_values("signal_time", kind="mergesort").iterrows():
        ledger = signal.to_dict()
        if signal["signal_time"] <= position_until:
            ledger.update(
                {"signal_accepted": False, "rejection_reason": "POSITION_OPEN"}
            )
            candidate_rows.append(ledger)
            continue
        entry = _find_entry(m5, signal, config["costs"])
        if entry is None:
            ledger.update(
                {"signal_accepted": False, "rejection_reason": "PENDING_EXPIRED"}
            )
            candidate_rows.append(ledger)
            continue
        entry_index, entry_price = entry
        outcome = _simulate(
            m5,
            entry_index,
            entry_price,
            signal,
            config["strategy"],
            config["costs"],
        )
        if not outcome["accepted"]:
            ledger.update(
                {"signal_accepted": False, "rejection_reason": outcome["reason"]}
            )
            candidate_rows.append(ledger)
            continue
        ledger.update(
            {
                "signal_accepted": True,
                "rejection_reason": "",
                "entry_time": outcome["entry_time"],
            }
        )
        candidate_rows.append(ledger)
        trade = dict(ledger)
        trade.update({key: value for key, value in outcome.items() if key != "accepted"})
        trade_rows.append(trade)
        position_until = outcome["exit_time"]
    return ReplayResult(pd.DataFrame(candidate_rows), pd.DataFrame(trade_rows))


def profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None if positive == 0 else float("inf")
    return positive / negative


def closed_drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def metrics(
    trades: pd.DataFrame, source_days: int, top_winners: int
) -> dict[str, Any]:
    values = trades["stress_net_r"].astype(float) if not trades.empty else pd.Series(dtype=float)
    monthly = (
        trades.assign(month=trades["entry_time"].dt.tz_localize(None).dt.to_period("M"))
        .groupby("month", sort=True)["stress_net_r"]
        .sum()
        if not trades.empty
        else pd.Series(dtype=float)
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
        "preferred_cost_share": float(trades["preferred_cost_r"].mean()) if not trades.empty else 0.0,
        "current_account_feasible_share": float(trades["current_account_feasible"].mean()) if not trades.empty else 0.0,
        "median_holding_minutes": float(trades["holding_minutes"].median()) if not trades.empty else 0.0,
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


def stage_audit(
    trades: pd.DataFrame, m5: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    audit: dict[str, Any] = {}
    eligible = True
    for stage, (start_text, end_text) in config["windows"].items():
        start, end = pd.Timestamp(start_text), pd.Timestamp(end_text)
        subset = (
            trades.loc[(trades["entry_time"] >= start) & (trades["entry_time"] < end)]
            if not trades.empty
            else trades
        )
        source_days = int(
            m5.loc[
                (m5["bar_start_utc"] >= start) & (m5["bar_start_utc"] < end),
                "bar_start_utc",
            ].dt.date.nunique()
        )
        gate = config["gates"][stage]
        value = metrics(subset, source_days, int(gate["top_winners_removed"]))
        passed, checks = evaluate_gate(value, gate)
        decision_eligible = bool(eligible)
        promoted = bool(eligible and passed)
        audit[stage] = {
            "decision_eligible": decision_eligible,
            "raw_gate_pass": passed,
            "promoted": promoted,
            "checks": checks,
            "metrics": value,
        }
        rows.append(
            {
                "stage": stage,
                "decision_eligible": decision_eligible,
                "raw_gate_pass": passed,
                "promoted": promoted,
                **value,
            }
        )
        eligible = promoted
    return pd.DataFrame(rows), audit
