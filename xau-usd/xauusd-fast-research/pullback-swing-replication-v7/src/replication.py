from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_ACTION_COLUMNS = {
    "event_id",
    "signal_time",
    "entry_time",
    "exit_time",
    "direction",
    "regime",
    "action_id",
    "h1_adx",
    "dir_return_1h_atr",
    "stress_net_r",
    "risk_usd",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_parquet(path: Path, expected_hash: str, expected_rows: int) -> pd.DataFrame:
    actual_hash = sha256_file(path)
    if actual_hash.lower() != expected_hash.lower():
        raise ValueError(f"Source hash mismatch: {actual_hash}")
    frame = pd.read_parquet(path)
    if len(frame) != expected_rows:
        raise ValueError(f"Source row mismatch: {len(frame)} != {expected_rows}")
    return frame


def select_rule(actions: pd.DataFrame, rule: dict[str, Any]) -> pd.DataFrame:
    missing = REQUIRED_ACTION_COLUMNS.difference(actions.columns)
    if missing:
        raise ValueError(f"Action ledger is missing columns: {sorted(missing)}")
    selected = actions.loc[
        actions["regime"].ne(str(rule["excluded_regime"]))
        & actions["action_id"].eq(str(rule["action_id"]))
        & actions["h1_adx"].gt(float(rule["h1_adx_exclusive_minimum"]))
        & actions["h1_adx"].le(float(rule["h1_adx_inclusive_maximum"]))
        & actions["dir_return_1h_atr"].le(
            float(rule["maximum_directional_return_1h_atr"])
        )
    ].copy()
    for column in ["signal_time", "entry_time", "exit_time"]:
        selected[column] = pd.to_datetime(selected[column], utc=True)
    if selected["event_id"].duplicated().any():
        raise ValueError("Fixed-action rule produced duplicate event IDs")
    selected["portfolio_pnl_usd"] = (
        pd.to_numeric(selected["stress_net_r"], errors="raise")
        * pd.to_numeric(selected["risk_usd"], errors="raise")
    )
    numeric = selected[
        ["h1_adx", "dir_return_1h_atr", "stress_net_r", "risk_usd", "portfolio_pnl_usd"]
    ].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Selected rule contains non-finite values")
    return selected.sort_values(["entry_time", "event_id"], kind="mergesort").reset_index(
        drop=True
    )


def execute_rule(selected: pd.DataFrame, rule: dict[str, Any]) -> pd.DataFrame:
    maximum_open = int(rule["maximum_open_positions"])
    maximum_daily = int(rule["maximum_entries_per_utc_date"])
    active_exits: list[pd.Timestamp] = []
    daily_entries: dict[Any, int] = {}
    accepted: list[int] = []
    for index, trade in selected.iterrows():
        entry_time = trade["entry_time"]
        active_exits = [exit_time for exit_time in active_exits if exit_time > entry_time]
        date = entry_time.date()
        if len(active_exits) >= maximum_open:
            continue
        if daily_entries.get(date, 0) >= maximum_daily:
            continue
        accepted.append(index)
        active_exits.append(trade["exit_time"])
        daily_entries[date] = daily_entries.get(date, 0) + 1
    result = selected.loc[accepted].copy().reset_index(drop=True)
    result["v7_trade_id"] = "V7_" + result["event_id"].astype(str)
    return result


def business_days(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(
        start.tz_localize(None).normalize(),
        (end.tz_localize(None) - pd.Timedelta(nanoseconds=1)).normalize(),
        freq="B",
    )


def profit_factor(values: pd.Series) -> float:
    gain = float(values.loc[values > 0].sum())
    loss = float(-values.loc[values < 0].sum())
    if loss == 0.0:
        return float("inf") if gain > 0.0 else 0.0
    return gain / loss


def closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(([0.0], values.cumsum().to_numpy(dtype=float)))
    return float(np.max(np.maximum.accumulate(equity) - equity))


def metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    top_winners: int,
) -> dict[str, Any]:
    selected = trades.loc[
        (trades["entry_time"] >= start) & (trades["entry_time"] < end)
    ].sort_values(["exit_time", "event_id"], kind="mergesort")
    values = selected["portfolio_pnl_usd"].astype(float)
    weekdays = business_days(start, end)
    month_index = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end.tz_localize(None) - pd.Timedelta(nanoseconds=1)).to_period("M"),
        freq="M",
    )
    monthly = (
        selected.assign(month=selected["exit_time"].dt.tz_localize(None).dt.to_period("M"))
        .groupby("month", sort=True)["portfolio_pnl_usd"]
        .sum()
        .reindex(month_index, fill_value=0.0)
    )
    removed = values.drop(values.nlargest(min(top_winners, len(values))).index)
    return {
        "trades": int(len(selected)),
        "weekdays": int(len(weekdays)),
        "trades_per_weekday": float(len(selected) / len(weekdays)) if len(weekdays) else 0.0,
        "net_usd": float(values.sum()),
        "average_usd": float(values.mean()) if len(values) else 0.0,
        "profit_factor": profit_factor(values),
        "closed_drawdown_usd": closed_drawdown(values),
        "win_rate": float((values > 0).mean()) if len(values) else 0.0,
        "positive_month_share": float((monthly > 0).mean()) if len(monthly) else 0.0,
        "top_winners_removed_net_usd": float(removed.sum()),
    }


def direction_metrics(
    trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> dict[str, dict[str, Any]]:
    selected = trades.loc[
        (trades["entry_time"] >= start) & (trades["entry_time"] < end)
    ]
    result: dict[str, dict[str, Any]] = {}
    for direction in ["LONG", "SHORT"]:
        values = selected.loc[
            selected["direction"].eq(direction), "portfolio_pnl_usd"
        ].astype(float)
        result[direction] = {
            "trades": int(len(values)),
            "net_usd": float(values.sum()),
            "profit_factor": profit_factor(values),
        }
    return result


def month_cluster_bootstrap_lower_bound(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    resamples: int,
    seed: int,
    lower_quantile: float,
) -> float:
    selected = trades.loc[
        (trades["entry_time"] >= start) & (trades["entry_time"] < end)
    ].copy()
    selected["month"] = selected["entry_time"].dt.tz_localize(None).dt.to_period("M")
    clusters = [group["portfolio_pnl_usd"].to_numpy(dtype=float) for _, group in selected.groupby("month", sort=True)]
    if not clusters:
        return 0.0
    rng = np.random.default_rng(seed)
    means = np.empty(resamples, dtype=float)
    for index in range(resamples):
        chosen = rng.integers(0, len(clusters), size=len(clusters))
        sample = np.concatenate([clusters[item] for item in chosen])
        means[index] = sample.mean()
    return float(np.quantile(means, lower_quantile))


def marginal_independence(
    candidate: pd.DataFrame,
    core: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    separation_minutes: int,
) -> dict[str, Any]:
    selected = candidate.loc[
        (candidate["entry_time"] >= start) & (candidate["entry_time"] < end)
    ].copy()
    core_entries = pd.to_datetime(
        core.loc[
            (core["entry_time_utc"] >= start) & (core["entry_time_utc"] < end),
            "entry_time_utc",
        ],
        utc=True,
    ).sort_values()
    width = pd.Timedelta(minutes=separation_minutes)
    independent = []
    for entry in selected["entry_time"]:
        near = ((core_entries - entry).abs() <= width).any()
        independent.append(not bool(near))
    selected["independent_of_core_entry"] = independent
    weekdays = business_days(start, end)
    count = int(selected["independent_of_core_entry"].sum())
    return {
        "candidate_trades": int(len(selected)),
        "independent_candidate_trades": count,
        "near_core_entries": int(len(selected) - count),
        "marginal_independent_trades_per_weekday": float(count / len(weekdays))
        if len(weekdays)
        else 0.0,
    }
