from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from strategies import COMPRESSION_ID, FAILED_AUCTION_ID, TREND_ID


@dataclass(frozen=True)
class BacktestResult:
    signals: pd.DataFrame
    trades: pd.DataFrame


def _point_size(row: pd.Series) -> float:
    spread_points = float(row.get("spread_open_points", np.nan))
    spread_price = float(row["ask_open"] - row["bid_open"])
    return spread_price / spread_points if np.isfinite(spread_points) and spread_points > 0 else 0.01


def _funding_weights(entry: pd.Timestamp, exit_time: pd.Timestamp, triple_weekday: int = 4) -> float:
    if exit_time <= entry:
        return 0.0
    cursor = entry.normalize() + pd.Timedelta(days=1)
    weight = 0.0
    while cursor <= exit_time:
        weight += 3.0 if cursor.weekday() == triple_weekday else 1.0
        cursor += pd.Timedelta(days=1)
    return weight


def _ownership_exit(strategy_id: str, direction: str, regime: str) -> bool:
    if strategy_id == TREND_ID:
        return regime != ("TREND_UP" if direction == "LONG" else "TREND_DOWN")
    if strategy_id == FAILED_AUCTION_ID:
        return regime != "BALANCED_RANGE"
    if strategy_id == COMPRESSION_ID:
        return regime == "UNSAFE_SHOCK"
    raise ValueError(f"Unknown strategy: {strategy_id}")


def _simulate(
    m5: pd.DataFrame,
    entry_time: pd.Timestamp,
    signal: pd.Series,
    config: dict[str, Any],
) -> dict[str, Any]:
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    start_index = int(np.searchsorted(starts, np.datetime64(entry_time.tz_convert(None)), side="left"))
    if start_index >= len(m5) or m5.iloc[start_index]["bar_start_utc"] != entry_time:
        return {"accepted": False, "rejection_reason": "MISSING_M5_ENTRY_BAR"}
    direction = str(signal["direction"]); strategy_id = str(signal["strategy_id"])
    entry_row = m5.iloc[start_index]
    entry_exec = float(entry_row["ask_open"] if direction == "LONG" else entry_row["bid_open"])
    entry_mid = float(entry_row["mid_open"])
    stop = float(signal["stop_frozen"])
    risk = entry_exec - stop if direction == "LONG" else stop - entry_exec
    atr_value = float(signal["atr15"])
    stop_atr = risk / atr_value if atr_value > 0 else np.nan
    if not np.isfinite(risk) or risk <= 0 or not np.isfinite(stop_atr):
        return {"accepted": False, "rejection_reason": "INVALID_STOP"}
    if stop_atr < float(signal["min_stop_atr"]) or stop_atr > float(signal["max_stop_atr"]):
        return {"accepted": False, "rejection_reason": "STOP_OUTSIDE_FROZEN_ATR_RANGE", "stop_atr": stop_atr}
    if signal["target_kind"] == "R_MULTIPLE":
        reward_r = float(signal["target_value"])
        target = entry_exec + reward_r * risk if direction == "LONG" else entry_exec - reward_r * risk
    else:
        target = float(signal["target_value"])
        reward_r = (target - entry_exec if direction == "LONG" else entry_exec - target) / risk
    if not np.isfinite(target) or reward_r < float(signal["minimum_reward_r"]):
        return {"accepted": False, "rejection_reason": "MINIMUM_EXPECTED_REWARD_FAILED", "stop_atr": stop_atr, "reward_r": reward_r}

    account = config["account"]
    risk_budget = float(account["equity_usd"]) * float(account["risk_fraction"])
    minimum_loss_usd = risk * float(account["contract_size_oz"]) * float(account["volume_min"])
    requested_volume = risk_budget / (risk * float(account["contract_size_oz"]))
    step = float(account["volume_step"])
    normalized_volume = np.floor(requested_volume / step + 1e-12) * step
    margin_rate = float(account.get("order_calc_margin_rate", 1.0 / float(account["leverage"])))
    margin_usd = entry_exec * float(account["contract_size_oz"]) * max(normalized_volume, float(account["volume_min"])) * margin_rate
    contract_granularity_failed = minimum_loss_usd > risk_budget + 1e-9 or normalized_volume < float(account["volume_min"])
    margin_failed = (
        margin_usd > float(account["equity_usd"]) * float(account["margin_limit_fraction"])
        or float(account["equity_usd"]) - margin_usd < float(account["equity_usd"]) * float(account["free_margin_floor_fraction"])
    )
    expressible = not contract_granularity_failed and not margin_failed
    sizing = {
        "risk_budget_usd": risk_budget, "minimum_volume_stop_loss_usd": minimum_loss_usd,
        "requested_volume": requested_volume, "normalized_volume": normalized_volume,
        "required_margin_usd": margin_usd, "risk_expressible": bool(expressible),
    }
    if not expressible:
        category = "CONTRACT_GRANULARITY_REJECT" if contract_granularity_failed else "MARGIN_REJECT" if margin_failed else "OTHER_SIZING_REJECT"
        return {
            "accepted": False, "rejection_reason": "CONTRACT_GRANULARITY_OR_MARGIN_REJECT",
            "sizing_rejection_category": category, "stop_atr": stop_atr, "reward_r": reward_r, **sizing,
        }

    deadline = entry_time + pd.Timedelta(hours=float(signal["max_hold_hours"]))
    exit_index = start_index; exit_reason = "END_OF_DATA"; exit_exec = entry_exec; exit_at_open = False
    favourable = adverse = 0.0; ambiguous = False
    for index in range(start_index, len(m5)):
        row = m5.iloc[index]
        if row["bar_start_utc"] >= deadline:
            exit_index, exit_reason, exit_at_open = index, "MAX_HOLD", True
            exit_exec = float(row["bid_open"] if direction == "LONG" else row["ask_open"])
            break
        if index > start_index and _ownership_exit(strategy_id, direction, str(row["regime_at_open"])):
            exit_index, exit_reason, exit_at_open = index, "REGIME_OWNERSHIP_EXIT", True
            exit_exec = float(row["bid_open"] if direction == "LONG" else row["ask_open"])
            break
        if direction == "LONG":
            open_favourable = max(0.0, float(row["bid_open"]) - entry_exec)
            open_adverse = max(0.0, entry_exec - float(row["bid_open"]))
            if float(row["bid_open"]) < stop:
                exit_index, exit_reason, exit_exec, exit_at_open = index, "GAP_THROUGH_STOP", float(row["bid_open"]), True
                favourable, adverse = max(favourable, open_favourable), max(adverse, open_adverse)
                break
            if float(row["bid_open"]) >= target:
                exit_index, exit_reason, exit_exec, exit_at_open = index, "TARGET_GAP_FROZEN_TARGET", target, True
                favourable, adverse = max(favourable, target - entry_exec), max(adverse, open_adverse)
                break
            stop_hit, target_hit = float(row["bid_low"]) <= stop, float(row["bid_high"]) >= target
        else:
            open_favourable = max(0.0, entry_exec - float(row["ask_open"]))
            open_adverse = max(0.0, float(row["ask_open"]) - entry_exec)
            if float(row["ask_open"]) > stop:
                exit_index, exit_reason, exit_exec, exit_at_open = index, "GAP_THROUGH_STOP", float(row["ask_open"]), True
                favourable, adverse = max(favourable, open_favourable), max(adverse, open_adverse)
                break
            if float(row["ask_open"]) <= target:
                exit_index, exit_reason, exit_exec, exit_at_open = index, "TARGET_GAP_FROZEN_TARGET", target, True
                favourable, adverse = max(favourable, entry_exec - target), max(adverse, open_adverse)
                break
            stop_hit, target_hit = float(row["ask_high"]) >= stop, float(row["ask_low"]) <= target
        if stop_hit:
            exit_index, exit_exec = index, stop
            ambiguous = bool(target_hit); exit_reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            favourable, adverse = max(favourable, open_favourable), max(adverse, risk)
            break
        if target_hit:
            exit_index, exit_exec, exit_reason = index, target, "TARGET"
            favourable, adverse = max(favourable, reward_r * risk), max(adverse, open_adverse)
            break
        if direction == "LONG":
            favourable = max(favourable, float(row["bid_high"]) - entry_exec); adverse = max(adverse, entry_exec - float(row["bid_low"]))
        else:
            favourable = max(favourable, entry_exec - float(row["ask_low"])); adverse = max(adverse, float(row["ask_high"]) - entry_exec)
        exit_index = index
        exit_exec = float(row["bid_close"] if direction == "LONG" else row["ask_close"])

    exit_row = m5.iloc[exit_index]
    exit_time = exit_row["bar_start_utc"] if exit_at_open else exit_row["timestamp_utc"]
    point = _point_size(exit_row)
    exit_spread = float((exit_row["ask_open"] - exit_row["bid_open"]) if exit_at_open else (exit_row["ask_close"] - exit_row["bid_close"]))
    exit_mid = exit_exec + 0.5 * exit_spread if direction == "LONG" else exit_exec - 0.5 * exit_spread
    sign = 1.0 if direction == "LONG" else -1.0
    gross_mid_r = sign * (exit_mid - entry_mid) / risk
    entry_spread = float(entry_row["ask_open"] - entry_row["bid_open"])
    spread_cost_r = (0.5 * entry_spread + 0.5 * exit_spread) / risk
    weights = _funding_weights(entry_time, exit_time, int(config["costs"]["swap_rollover3days_python_weekday"]))
    rate_pct = float(config["costs"]["funding_snapshot_long_pct"] if direction == "LONG" else config["costs"]["funding_snapshot_short_pct"])
    funding_cost_r = -(rate_pct / 100.0) * entry_mid / float(config["costs"]["funding_day_basis"]) * weights / risk
    baseline_net_r = gross_mid_r - spread_cost_r - funding_cost_r
    stress_entry = float(entry_row["stress_spread_points"]) * point
    stress_exit = float(exit_row["stress_spread_points"]) * point
    stress_spread_cost_r = (0.5 * stress_entry + 0.5 * stress_exit) / risk
    multiplier = float(config["costs"]["stress_funding_multiplier"])
    stress_funding_r = funding_cost_r * multiplier if funding_cost_r >= 0 else funding_cost_r / multiplier
    stress_net_r = gross_mid_r - stress_spread_cost_r - stress_funding_r - float(config["costs"]["stress_slippage_r"])
    return {
        "accepted": True, "entry_time": entry_time, "exit_time": exit_time, "entry_price": entry_exec,
        "exit_price": exit_exec, "stop": stop, "target": target, "initial_risk_price": risk,
        "stop_atr": stop_atr, "expected_reward_r": reward_r, "exit_reason": exit_reason,
        "gross_mid_r": gross_mid_r, "spread_cost_r": spread_cost_r, "funding_cost_r": funding_cost_r,
        "net_r": baseline_net_r, "stress_spread_cost_r": stress_spread_cost_r,
        "stress_funding_cost_r": stress_funding_r, "stress_net_r": stress_net_r,
        "mfe_r": favourable / risk, "mae_r": adverse / risk,
        "holding_minutes": float((exit_time - entry_time).total_seconds() / 60.0),
        "holding_overrun_minutes": max(0.0, float((exit_time - deadline).total_seconds() / 60.0)),
        "ambiguous_m5": ambiguous, "funding_weights": weights, **sizing,
    }


def run_portfolio(m15: pd.DataFrame, m5: pd.DataFrame, candidates: pd.DataFrame, config: dict[str, Any]) -> BacktestResult:
    signal_rows: list[dict[str, Any]] = []; trade_rows: list[dict[str, Any]] = []
    if candidates.empty:
        return BacktestResult(pd.DataFrame(), pd.DataFrame())
    m15_starts = m15["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    position_until = pd.Timestamp.min.tz_localize("UTC")
    cooldowns: dict[tuple[str, str], pd.Timestamp] = {}
    consumed_setups: set[str] = set()
    for _, signal in candidates.sort_values(["signal_time", "strategy_id", "direction"], kind="mergesort").iterrows():
        entry_index = int(np.searchsorted(m15_starts, np.datetime64(signal["signal_time"].tz_convert(None)), side="left"))
        entry_time = m15.iloc[entry_index]["bar_start_utc"] if entry_index < len(m15) else None
        key = (str(signal["strategy_id"]), str(signal["direction"]))
        ledger = {
            "strategy_id": signal["strategy_id"], "direction": signal["direction"], "signal_time": signal["signal_time"],
            "setup_key": signal["setup_key"], "regime": signal["regime"], "regime_episode_id": int(signal["regime_episode_id"]),
            "h1_structure_time": signal["h1_structure_time"], "atr15": signal["atr15"],
            "h1_box_high": signal["h1_box_high"], "h1_box_low": signal["h1_box_low"], "h1_box_mid": signal["h1_box_mid"],
        }
        reason = ""
        if entry_time is None:
            reason = "NO_NEXT_M15_BAR"
        elif entry_time <= position_until:
            reason = "PORTFOLIO_POSITION_ALREADY_OPEN"
        elif signal["signal_time"] < cooldowns.get(key, pd.Timestamp.min.tz_localize("UTC")):
            reason = "FAMILY_DIRECTION_COOLDOWN"
        elif str(signal["setup_key"]) in consumed_setups:
            reason = "DUPLICATE_SETUP_EPISODE"
        if reason:
            ledger.update({"signal_accepted": False, "rejection_reason": reason}); signal_rows.append(ledger); continue
        outcome = _simulate(m5, entry_time, signal, config)
        if not outcome["accepted"]:
            ledger.update({"signal_accepted": False, "rejection_reason": outcome["rejection_reason"], **{k: v for k, v in outcome.items() if k not in {"accepted", "rejection_reason"}}})
            signal_rows.append(ledger); consumed_setups.add(str(signal["setup_key"])); continue
        ledger.update({"signal_accepted": True, "rejection_reason": "", "entry_time": outcome["entry_time"], "entry_price": outcome["entry_price"]})
        signal_rows.append(ledger)
        trade = dict(ledger); trade.update({k: v for k, v in outcome.items() if k != "accepted"}); trade_rows.append(trade)
        position_until = outcome["exit_time"]
        cooldowns[key] = outcome["exit_time"] + pd.Timedelta(hours=float(signal["cooldown_hours"]))
        consumed_setups.add(str(signal["setup_key"]))
    signals = pd.DataFrame(signal_rows).sort_values(["signal_time", "strategy_id", "direction"], kind="mergesort").reset_index(drop=True)
    trades = pd.DataFrame(trade_rows)
    if not trades.empty:
        trades = trades.sort_values(["entry_time", "strategy_id", "direction"], kind="mergesort").reset_index(drop=True)
    return BacktestResult(signals, trades)
