from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .ensemble import OWNERS, generate_ensemble_signals, load_ensemble_config, load_inputs
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    is_quarantined,
    remove_top_winners,
    serialize,
    sha256_file,
)


def load_asymmetric_config() -> dict[str, Any]:
    return json.loads(
        (PACKAGE_ROOT / "config" / "frozen_asymmetric_payoff.json").read_text(encoding="utf-8")
    )


def verify_asymmetric_lock() -> dict[str, str]:
    lock = json.loads(
        (PACKAGE_ROOT / "EURUSD_ASYMMETRIC_PAYOFF_PREREG_2026_07_27.sha256.json").read_text(
            encoding="utf-8"
        )
    )
    if lock.get("locked_before_1p5r_outcome_inspection") is not True:
        raise RuntimeError("Asymmetric payoff contract is not locked")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"Asymmetric preregistration mismatch: {relative}")
        checked[relative] = actual
    return checked


def payoff_metrics(trades: pd.DataFrame, value_column: str = "r") -> dict[str, Any]:
    values = (
        trades[value_column].astype(float).to_numpy()
        if not trades.empty
        else np.asarray([], dtype=float)
    )
    wins = values[values > 0]
    losses = values[values < 0]
    average_win = float(wins.mean()) if len(wins) else 0.0
    average_loss = float(-losses.mean()) if len(losses) else 0.0
    payoff = (
        average_win / average_loss
        if average_loss > 0
        else (math.inf if average_win > 0 else 0.0)
    )
    gross_win = float(wins.sum())
    gross_loss = float(-losses.sum())
    profit_factor = (
        gross_win / gross_loss
        if gross_loss > 0
        else (math.inf if gross_win > 0 else 0.0)
    )
    equity = np.concatenate(([0.0], np.cumsum(values)))
    drawdown = np.maximum.accumulate(equity) - equity
    return {
        "trades": int(len(values)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "win_rate": float(len(wins) / len(values)) if len(values) else 0.0,
        "average_win_r": average_win,
        "average_loss_r": average_loss,
        "realized_payoff_ratio": payoff,
        "profit_factor": profit_factor,
        "net_r": float(values.sum()),
        "expectancy_r": float(values.mean()) if len(values) else 0.0,
        "max_drawdown_r": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def walk_timed_long_exit(
    m5: pd.DataFrame,
    start_position: int,
    deadline: pd.Timestamp,
    stop: float,
    target: float,
    slippage: float,
) -> tuple[pd.Timestamp, float, str]:
    end_position = int(m5.index.searchsorted(deadline, side="right")) - 1
    end_position = min(max(end_position, start_position), len(m5) - 1)
    for position in range(start_position, end_position + 1):
        timestamp = m5.index[position]
        bar = m5.iloc[position]
        if float(bar["bid_low"]) <= stop:
            return timestamp, min(float(bar["bid_open"]), stop) - slippage, "STOP"
        if float(bar["bid_high"]) >= target:
            return timestamp, max(float(bar["bid_open"]), target) - slippage, "TARGET"
    return (
        m5.index[end_position],
        float(m5.iloc[end_position]["bid_close"]) - slippage,
        "TIME_12H",
    )


def simulate_asymmetric(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    entry_cfg: dict[str, Any],
    payoff_cfg: dict[str, Any],
) -> pd.DataFrame:
    execution = entry_cfg["execution"]
    priority = {owner: i for i, owner in enumerate(entry_cfg["portfolio"]["priority"])}
    ordered = signals.copy()
    ordered["owner_priority"] = ordered["owner"].map(priority)
    ordered = ordered.sort_values(["completion_time_utc", "owner_priority", "seed_priority"])
    target_r = float(payoff_cfg["exit"]["target_r"])
    hold_hours = int(payoff_cfg["exit"]["maximum_hold_hours"])
    spread_floor = float(payoff_cfg["exit"]["minimum_retail_spread_pips"]) * PIP
    slippage = float(payoff_cfg["exit"]["extra_slippage_pips_per_side"]) * PIP
    records = []
    open_until: pd.Timestamp | None = None
    daily_count: dict[str, int] = {}
    for _, signal in ordered.iterrows():
        position = int(m5.index.searchsorted(signal["completion_time_utc"], side="left"))
        if position >= len(m5):
            continue
        entry_time = m5.index[position]
        if open_until is not None and entry_time <= open_until:
            continue
        if is_quarantined(entry_time, "EURUSD", entry_cfg["quarantine"]):
            continue
        day = entry_time.strftime("%Y-%m-%d")
        if daily_count.get(day, 0) >= int(execution["max_trades_per_utc_day"]):
            continue
        bar = m5.iloc[position]
        entry = max(float(bar["ask_open"]), float(bar["bid_open"]) + spread_floor) + slippage
        minimum = float(signal["stop_floor_pips"]) * PIP
        stop_distance = max(
            float(signal["stop_atr_multiple"]) * float(signal["atr"]), minimum
        )
        stop = min(float(signal["recent_low"]), entry - stop_distance)
        risk = entry - stop
        if risk <= 0 or risk > float(signal["stop_ceiling_pips"]) * PIP:
            continue
        target = entry + target_r * risk
        exit_time, exit_price, reason = walk_timed_long_exit(
            m5,
            position,
            entry_time + pd.Timedelta(hours=hold_hours),
            stop,
            target,
            slippage,
        )
        result_r = (exit_price - entry) / risk
        records.append(
            {
                "specialist": signal["owner"],
                "seed_id": signal["seed_id"],
                "signal_time_utc": signal["signal_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "r": result_r,
                "extra_half_pip_stress_r": result_r - (0.5 * PIP / risk),
                "fixed_0p01_lot_usd": (exit_price - entry) * 1000.0,
            }
        )
        open_until = exit_time
        daily_count[day] = daily_count.get(day, 0) + 1
    return pd.DataFrame(records)


def summarize_specialist(trades: pd.DataFrame, payoff_cfg: dict[str, Any]) -> dict[str, Any]:
    gate = payoff_cfg["specialist_admission"]
    windows = {}
    for name, (start, end) in payoff_cfg["windows"].items():
        frame = (
            trades[
                (trades["entry_time_utc"] >= pd.Timestamp(start))
                & (trades["entry_time_utc"] <= pd.Timestamp(end))
            ]
            if not trades.empty
            else trades
        )
        windows[name] = payoff_metrics(frame)
    overall = payoff_metrics(trades)
    top_removed = payoff_metrics(remove_top_winners(trades))
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    admitted = (
        all(
            block["trades"] >= gate["minimum_trades_each_window"]
            and gate["minimum_win_rate"] <= block["win_rate"] <= gate["maximum_win_rate"]
            and gate["minimum_realized_payoff_ratio"]
            <= block["realized_payoff_ratio"]
            <= gate["maximum_realized_payoff_ratio"]
            and block["profit_factor"] >= gate["minimum_profit_factor"]
            and block["expectancy_r"] > gate["minimum_expectancy_r"]
            for block in windows.values()
        )
        and overall["max_drawdown_r"] <= gate["maximum_drawdown_r_overall"]
        and top_removed["net_r"] > 0
        and stressed["net_r"] > 0
    )
    return {
        "admitted": admitted,
        "status": "ADMITTED_RESEARCH_COMPONENT" if admitted else "REJECTED_STANDALONE",
        "overall": overall,
        "windows": windows,
        "top_5_percent_winners_removed": top_removed,
        "extra_half_pip_round_trip": stressed,
    }


def recent_summary(
    trades: pd.DataFrame, m5: pd.DataFrame, payoff_cfg: dict[str, Any]
) -> dict[str, Any]:
    start, end = map(pd.Timestamp, payoff_cfg["recent_six_months"])
    frame = (
        trades[
            (trades["entry_time_utc"] >= start) & (trades["entry_time_utc"] <= end)
        ]
        if not trades.empty
        else trades
    )
    result = payoff_metrics(frame)
    result["trades_per_active_day"] = len(frame) / active_weekday_fx_days(m5, start, end)
    result["fixed_0p01_lot_usd"] = (
        float(frame["fixed_0p01_lot_usd"].sum()) if not frame.empty else 0.0
    )
    result["monthly"] = {
        month: {
            **payoff_metrics(month_frame),
            "fixed_0p01_lot_usd": float(month_frame["fixed_0p01_lot_usd"].sum()),
        }
        for month, month_frame in (
            frame.groupby(frame["entry_time_utc"].dt.strftime("%Y-%m"))
            if not frame.empty
            else []
        )
    }
    return result


def run_asymmetric() -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    checked = verify_asymmetric_lock()
    entry_cfg = load_ensemble_config()
    payoff_cfg = load_asymmetric_config()
    m5, state, _ = load_inputs(entry_cfg)
    signals = generate_ensemble_signals(m5, state, entry_cfg)
    owned = signals[signals["owner"].isin(OWNERS)]
    trades_by_owner = {
        owner: simulate_asymmetric(
            owned[owned["owner"].eq(owner)], m5, entry_cfg, payoff_cfg
        )
        for owner in OWNERS
    }
    specialists = {
        owner: summarize_specialist(frame, payoff_cfg)
        for owner, frame in trades_by_owner.items()
    }
    admitted = [owner for owner in OWNERS if specialists[owner]["admitted"]]
    portfolio = simulate_asymmetric(
        owned[owned["owner"].isin(admitted)], m5, entry_cfg, payoff_cfg
    )
    portfolio_metrics = payoff_metrics(portfolio)
    start = pd.Timestamp(entry_cfg["data"]["start_utc"])
    end = pd.Timestamp(entry_cfg["data"]["end_utc"])
    frequency = len(portfolio) / active_weekday_fx_days(m5, start, end)
    window_metrics = {}
    for name, (a, b) in payoff_cfg["windows"].items():
        frame = (
            portfolio[
                (portfolio["entry_time_utc"] >= pd.Timestamp(a))
                & (portfolio["entry_time_utc"] <= pd.Timestamp(b))
            ]
            if not portfolio.empty
            else portfolio
        )
        window_metrics[name] = payoff_metrics(frame)
    gate = payoff_cfg["portfolio_admission"]
    portfolio_pass = (
        bool(admitted)
        and frequency >= gate["minimum_actual_trades_per_active_day"]
        and gate["minimum_win_rate"]
        <= portfolio_metrics["win_rate"]
        <= gate["maximum_win_rate"]
        and gate["minimum_realized_payoff_ratio"]
        <= portfolio_metrics["realized_payoff_ratio"]
        <= gate["maximum_realized_payoff_ratio"]
        and portfolio_metrics["profit_factor"] >= gate["minimum_profit_factor"]
        and all(block["net_r"] > 0 for block in window_metrics.values())
    )
    portfolio_result = {
        **portfolio_metrics,
        "actual_trades_per_active_day": frequency,
        "windows": window_metrics,
        "admitted": portfolio_pass,
        "status": "ADAPTIVE_RESEARCH_PASS" if portfolio_pass else "REJECTED",
    }
    all_owner = simulate_asymmetric(owned, m5, entry_cfg, payoff_cfg)
    result = {
        "lock": checked,
        "inherited_capacity_census": {
            "owned_raw_signals": 6035,
            "signals_per_weekday": 3.0885363357215967,
            "passed": True,
        },
        "specialists": specialists,
        "admitted_specialists": admitted,
        "portfolio": portfolio_result,
        "portfolio_recent_six_months": recent_summary(portfolio, m5, payoff_cfg),
        "all_owner_diagnostic": {
            "status": "DIAGNOSTIC_ONLY_NOT_ADMITTED",
            "overall": payoff_metrics(all_owner),
            "recent_six_months": recent_summary(all_owner, m5, payoff_cfg),
        },
    }
    trades_by_owner["PORTFOLIO"] = portfolio
    trades_by_owner["ALL_OWNER_DIAGNOSTIC"] = all_owner
    return result, trades_by_owner


def write_asymmetric(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(serialize(payload), indent=2), encoding="utf-8")
