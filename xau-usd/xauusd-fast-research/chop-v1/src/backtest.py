from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BacktestResult:
    signals: pd.DataFrame
    trades: pd.DataFrame


def ambiguous_outcome(stop_hit: bool, target_hit: bool) -> tuple[str | None, bool]:
    if stop_hit:
        return "STOP", bool(target_hit)
    if target_hit:
        return "TARGET", False
    return None, False


def cost_r(cost_price: float, initial_risk_price: float) -> float:
    if not np.isfinite(initial_risk_price) or initial_risk_price <= 0:
        raise ValueError("Initial risk must be finite and positive")
    return float(cost_price / initial_risk_price)


def _point_size(row: pd.Series) -> float:
    points = float(row.get("spread_open_points", np.nan))
    spread = float(row["ask_open"] - row["bid_open"])
    return spread / points if np.isfinite(points) and points > 0 and spread > 0 else 0.01


def _exit_prices(row: pd.Series, direction: str, exit_exec: float, at_open: bool = False) -> tuple[float, float, float]:
    suffix = "open" if at_open else "close"
    spread = max(0.0, float(row[f"ask_{suffix}"] - row[f"bid_{suffix}"]))
    mid = exit_exec + spread / 2.0 if direction == "LONG" else exit_exec - spread / 2.0
    return mid, spread, _point_size(row)


def _simulate_trade(
    bars: pd.DataFrame,
    entry_index: int,
    signal: pd.Series,
    stress_slippage_r: float,
    execution_bars: pd.DataFrame | None = None,
) -> dict[str, Any]:
    direction = str(signal["direction"])
    entry_row = bars.iloc[entry_index]
    entry_exec = float(entry_row["ask_open"] if direction == "LONG" else entry_row["bid_open"])
    entry_mid = float(entry_row["mid_open"])
    atr_value = float(signal["atr"])
    if signal["stop_kind"] == "ENTRY_ATR":
        distance = float(signal["stop_value"]) * atr_value
        stop = entry_exec - distance if direction == "LONG" else entry_exec + distance
    else:
        stop = float(signal["stop_value"])
        distance = entry_exec - stop if direction == "LONG" else stop - entry_exec
    target = float(signal["target_frozen"])
    reward = target - entry_exec if direction == "LONG" else entry_exec - target
    rejection = ""
    if not np.isfinite(distance) or distance <= 0 or not np.isfinite(target):
        rejection = "INVALID_STOP_OR_TARGET"
    elif reward < distance:
        rejection = "EXPECTED_REWARD_BELOW_1R"
    elif signal["strategy_id"] == "CHOP_IMPULSE_EXHAUSTION_REVERSION_V1" and not (
        float(signal["min_stop_atr"]) * atr_value <= distance <= float(signal["max_stop_atr"]) * atr_value
    ):
        rejection = "IMPULSE_STOP_OUTSIDE_0P5_TO_2_ATR"
    if rejection:
        return {"accepted": False, "rejection_reason": rejection}

    path = bars if execution_bars is None else execution_bars
    if execution_bars is None:
        execution_index = entry_index
    else:
        starts = path["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
        execution_index = int(np.searchsorted(starts, np.datetime64(entry_row["bar_start_utc"].tz_convert(None)), side="left"))
        if execution_index >= len(path):
            return {"accepted": False, "rejection_reason": "NO_EXECUTION_SUBBAR"}
    deadline = entry_row["bar_start_utc"] + pd.Timedelta(hours=float(signal["max_hold_hours"]))
    exit_index = execution_index
    exit_reason = "END_OF_DATA"
    ambiguous = False
    exit_exec = float(path.iloc[-1]["bid_close"] if direction == "LONG" else path.iloc[-1]["ask_close"])
    exit_at_open = False
    favourable = adverse = 0.0
    for index in range(execution_index, len(path)):
        row = path.iloc[index]
        if row["bar_start_utc"] >= deadline:
            exit_index = index
            exit_reason = "MAX_HOLD"
            exit_exec = float(row["bid_open"] if direction == "LONG" else row["ask_open"])
            exit_at_open = True
            break
        if index > execution_index and not bool(row["chop_active_at_open"]):
            exit_index = index
            exit_reason = "REGIME_EXIT"
            exit_exec = float(row["bid_open"] if direction == "LONG" else row["ask_open"])
            exit_at_open = True
            break
        if direction == "LONG":
            open_favourable = max(0.0, float(row["bid_open"]) - entry_exec)
            open_adverse = max(0.0, entry_exec - float(row["bid_open"]))
            if float(row["bid_open"]) < stop:
                favourable, adverse = max(favourable, open_favourable), max(adverse, open_adverse)
                exit_index, exit_reason, exit_exec, exit_at_open = index, "GAP_THROUGH_STOP", float(row["bid_open"]), True
                break
            stop_hit, target_hit = float(row["bid_low"]) <= stop, float(row["bid_high"]) >= target
        else:
            open_favourable = max(0.0, entry_exec - float(row["ask_open"]))
            open_adverse = max(0.0, float(row["ask_open"]) - entry_exec)
            if float(row["ask_open"]) > stop:
                favourable, adverse = max(favourable, open_favourable), max(adverse, open_adverse)
                exit_index, exit_reason, exit_exec, exit_at_open = index, "GAP_THROUGH_STOP", float(row["ask_open"]), True
                break
            stop_hit, target_hit = float(row["ask_high"]) >= stop, float(row["ask_low"]) <= target
        outcome, ambiguous_here = ambiguous_outcome(stop_hit, target_hit)
        if outcome:
            exit_index, ambiguous = index, ambiguous_here
            exit_reason = "AMBIGUOUS_BAR_STOP_FIRST" if ambiguous_here else outcome
            exit_exec = stop if outcome == "STOP" else target
            if outcome == "STOP":
                favourable = max(favourable, open_favourable)
                adverse = max(adverse, distance)
            else:
                favourable = max(favourable, reward)
                adverse = max(adverse, open_adverse)
            break
        if direction == "LONG":
            favourable = max(favourable, float(row["bid_high"]) - entry_exec)
            adverse = max(adverse, entry_exec - float(row["bid_low"]))
        else:
            favourable = max(favourable, entry_exec - float(row["ask_low"]))
            adverse = max(adverse, float(row["ask_high"]) - entry_exec)

    exit_row = path.iloc[exit_index]
    exit_mid, exit_spread, point_size = _exit_prices(exit_row, direction, exit_exec, exit_at_open)
    sign = 1.0 if direction == "LONG" else -1.0
    gross_r = sign * (exit_mid - entry_mid) / distance
    entry_spread = max(0.0, float(entry_row["ask_open"] - entry_row["bid_open"]))
    baseline_cost_price = 0.5 * entry_spread + 0.5 * exit_spread
    baseline_cost_r = cost_r(baseline_cost_price, distance)
    net_r = gross_r - baseline_cost_r
    stress_entry = float(entry_row.get("spread_p95_points", 0.0)) * point_size
    stress_exit = float(exit_row.get("spread_p95_points", 0.0)) * point_size
    stress_cost_r = cost_r(0.5 * stress_entry + 0.5 * stress_exit, distance) + stress_slippage_r
    stress_net_r = gross_r - stress_cost_r
    entry_time = entry_row["bar_start_utc"]
    exit_time = exit_row["bar_start_utc"] if exit_at_open else exit_row["timestamp_utc"]
    return {
        "accepted": True, "entry_index": entry_index, "exit_index": exit_index,
        "entry_time": entry_time, "exit_time": exit_time, "entry_price": entry_exec,
        "stop": stop, "target": target, "initial_risk": distance, "exit_price": exit_exec,
        "exit_reason": exit_reason, "gross_r": gross_r, "cost_r": baseline_cost_r,
        "net_r": net_r, "stress_cost_r": stress_cost_r, "stress_net_r": stress_net_r,
        "mfe_r": favourable / distance, "mae_r": adverse / distance,
        "holding_minutes": float((exit_time - entry_time).total_seconds() / 60.0),
        "scheduled_max_hold_time": deadline,
        "holding_overrun_minutes": max(0.0, float((exit_time - deadline).total_seconds() / 60.0)),
        "execution_timeframe": str(exit_row.get("timeframe", "")),
        "ambiguous_bar": ambiguous,
        "rollover_crossed": bool(entry_time.date() != exit_time.date()),
    }


def run_cell(
    bars: pd.DataFrame,
    candidates: pd.DataFrame,
    timeframe: str,
    cooldown_hours: int,
    stress_slippage_r: float,
    execution_bars: pd.DataFrame | None = None,
) -> BacktestResult:
    timestamps = bars["timestamp_utc"].to_numpy(dtype="datetime64[ns]")
    signal_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    for strategy_id, strategy_signals in candidates.groupby("strategy_id", sort=True):
        position_until = pd.Timestamp.min.tz_localize("UTC")
        cooldown_until: dict[str, pd.Timestamp] = {"LONG": pd.Timestamp.min.tz_localize("UTC"), "SHORT": pd.Timestamp.min.tz_localize("UTC")}
        for _, signal in strategy_signals.sort_values("signal_time", kind="mergesort").iterrows():
            signal_index = int(np.searchsorted(timestamps, np.datetime64(signal["signal_time"].tz_convert(None)), side="left"))
            ledger = {
                "strategy_id": strategy_id, "timeframe": timeframe, "direction": signal["direction"],
                "chop_episode_id": int(signal["chop_episode_id"]), "setup_episode_id": int(signal["setup_episode_id"]),
                "setup_start_time": signal.get("setup_start_time"), "signal_time": signal["signal_time"], "regime_active": bool(signal["chop_active"]),
                "h4_adx": signal["adx14_h4"], "h4_efficiency_ratio": signal["er24"],
                "h4_displacement_atr": signal["displacement_atr24"], "h4_range_width_atr": signal["range_width_atr24"],
                "volatility_subtype": signal["volatility_subtype"], "range_width_subtype": signal["range_width_subtype"],
                "drift_subtype": signal["drift_subtype"], "atr": signal["atr"],
                "raw_z": signal["raw_z"], "raw_center": signal["raw_center"], "raw_scale": signal["raw_scale"],
            }
            reason = ""
            direction = str(signal["direction"])
            entry_index = signal_index + 1
            prospective_entry_time = bars.iloc[entry_index]["bar_start_utc"] if entry_index < len(bars) else None
            if not bool(signal["signal_accepted_pre_execution"]):
                reason = str(signal["rejection_reason"])
            elif not bool(signal["chop_active"]):
                reason = "REGIME_INACTIVE"
            elif entry_index >= len(bars):
                reason = "NO_NEXT_BAR"
            elif prospective_entry_time <= position_until:
                reason = "POSITION_ALREADY_OPEN"
            elif signal["signal_time"] < cooldown_until[direction]:
                reason = "DIRECTION_COOLDOWN_ACTIVE"
            elif not bool(bars.iloc[entry_index]["chop_active_at_open"]):
                reason = "REGIME_INACTIVE_AT_ENTRY"
            if reason:
                ledger.update({"signal_accepted": False, "rejection_reason": reason})
                signal_rows.append(ledger)
                continue
            outcome = _simulate_trade(bars, entry_index, signal, stress_slippage_r, execution_bars)
            if not outcome["accepted"]:
                ledger.update({"signal_accepted": False, "rejection_reason": outcome["rejection_reason"]})
                signal_rows.append(ledger)
                continue
            ledger.update({
                "signal_accepted": True, "rejection_reason": "", "entry_time": outcome["entry_time"],
                "entry_price": outcome["entry_price"], "stop": outcome["stop"], "target": outcome["target"],
                "initial_risk": outcome["initial_risk"], "spread": float(bars.iloc[entry_index]["ask_open"] - bars.iloc[entry_index]["bid_open"]),
                "cost_price": outcome["cost_r"] * outcome["initial_risk"], "cost_r": outcome["cost_r"],
                "entry_delay_minutes": float((outcome["entry_time"] - signal["setup_start_time"]).total_seconds() / 60.0),
            })
            signal_rows.append(ledger)
            trade = dict(ledger)
            trade.update({key: value for key, value in outcome.items() if key not in {"accepted", "entry_index", "exit_index"}})
            trade_rows.append(trade)
            position_until = outcome["exit_time"]
            cooldown_until[direction] = outcome["exit_time"] + pd.Timedelta(hours=cooldown_hours)
    signals = pd.DataFrame(signal_rows).sort_values(["signal_time", "strategy_id", "direction"], kind="mergesort").reset_index(drop=True)
    trades = pd.DataFrame(trade_rows)
    if not trades.empty:
        trades = trades.sort_values(["entry_time", "strategy_id", "direction"], kind="mergesort").reset_index(drop=True)
    return BacktestResult(signals=signals, trades=trades)


def assert_no_outside_regime(trades: pd.DataFrame) -> None:
    if not trades.empty and not trades["regime_active"].all():
        raise AssertionError("A trade opened outside the active H4 chop regime")
