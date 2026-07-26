from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd


def profit_factor(values: pd.Series | np.ndarray) -> float | None:
    array = np.asarray(values, dtype=float)
    gains = float(array[array > 0.0].sum())
    losses = float(-array[array < 0.0].sum())
    if losses <= 0.0:
        return None
    return gains / losses


def closed_drawdown(
    ledger: pd.DataFrame, *, starting_equity_usd: float
) -> dict[str, Any]:
    if ledger.empty:
        return {
            "maximum_drawdown_usd": 0.0,
            "maximum_drawdown_fraction": 0.0,
            "peak_time_utc": None,
            "trough_time_utc": None,
        }
    events = (
        ledger.groupby("label_end_time", as_index=False, sort=True)["pnl_usd"]
        .sum()
        .sort_values("label_end_time", kind="stable")
    )
    equity = starting_equity_usd + events["pnl_usd"].cumsum().to_numpy(float)
    running_peak = np.maximum.accumulate(
        np.concatenate(([starting_equity_usd], equity))
    )[1:]
    drawdown = running_peak - equity
    index = int(np.argmax(drawdown))
    peak_candidates = np.flatnonzero(equity[: index + 1] >= running_peak[index] - 1e-12)
    peak_time = (
        events["label_end_time"].iloc[int(peak_candidates[-1])].isoformat()
        if len(peak_candidates)
        else None
    )
    return {
        "maximum_drawdown_usd": float(drawdown[index]),
        "maximum_drawdown_fraction": float(drawdown[index] / starting_equity_usd),
        "peak_time_utc": peak_time,
        "trough_time_utc": events["label_end_time"].iloc[index].isoformat(),
    }


def equity_envelope_drawdown(curve: pd.DataFrame) -> dict[str, Any]:
    if curve.empty:
        return {
            "maximum_drawdown_usd": 0.0,
            "maximum_drawdown_fraction_of_peak": 0.0,
            "peak_time_utc": None,
            "trough_time_utc": None,
            "peak_equity_usd": None,
            "trough_equity_usd": None,
        }
    high = curve["high_equity_usd"].to_numpy(float)
    low = curve["low_equity_usd"].to_numpy(float)
    running_peak = -np.inf
    running_peak_index = 0
    maximum = -np.inf
    peak_index = 0
    trough_index = 0
    for index in range(len(curve)):
        if high[index] > running_peak:
            running_peak = high[index]
            running_peak_index = index
        drawdown = running_peak - low[index]
        if drawdown > maximum:
            maximum = drawdown
            peak_index = running_peak_index
            trough_index = index
    peak = float(high[peak_index])
    trough = float(low[trough_index])
    return {
        "maximum_drawdown_usd": float(maximum),
        "maximum_drawdown_fraction_of_peak": float(maximum / peak) if peak > 0 else None,
        "peak_time_utc": curve["timestamp_utc"].iloc[peak_index].isoformat(),
        "trough_time_utc": curve["timestamp_utc"].iloc[trough_index].isoformat(),
        "peak_equity_usd": peak,
        "trough_equity_usd": trough,
        "trough_open_positions": int(curve["open_positions"].iloc[trough_index]),
        "trough_open_initial_risk_usd": float(
            curve["open_initial_risk_usd"].iloc[trough_index]
        ),
        "trough_open_margin_usd": float(curve["open_margin_usd"].iloc[trough_index]),
    }


def _weekdays(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(
        np.busday_count(
            np.datetime64(start.date(), "D"),
            np.datetime64(end.date(), "D"),
        )
    )


def _window_daily_pnl(exits: pd.DataFrame) -> pd.Series:
    if exits.empty:
        return pd.Series(dtype=float)
    dates = exits["label_end_time"].dt.floor("D")
    return exits.groupby(dates)["pnl_usd"].sum().sort_index()


def _month_count(start: pd.Timestamp, end: pd.Timestamp) -> int:
    first = start.tz_convert(None).to_period("M")
    final = (end - pd.Timedelta(microseconds=1)).tz_convert(None).to_period("M")
    return int(final.ordinal - first.ordinal + 1)


def window_metrics(
    ledger: pd.DataFrame,
    curve: pd.DataFrame,
    *,
    policy_id: str,
    windows: Mapping[str, list[str]],
    starting_equity_usd: float,
    top_winners_removed: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for window_id, bounds in windows.items():
        start, end = (pd.Timestamp(value) for value in bounds)
        entries = ledger.loc[
            ledger["entry_time"].ge(start) & ledger["entry_time"].lt(end)
        ].copy()
        exits = ledger.loc[
            ledger["label_end_time"].ge(start) & ledger["label_end_time"].lt(end)
        ].copy()
        local_curve = curve.loc[
            curve["timestamp_utc"].ge(start) & curve["timestamp_utc"].lt(end)
        ].reset_index(drop=True)
        weekdays = _weekdays(start, end)
        daily = _window_daily_pnl(exits)
        monthly = (
            exits.groupby(exits["label_end_time"].dt.tz_convert(None).dt.to_period("M"))[
                "pnl_usd"
            ].sum()
            if len(exits)
            else pd.Series(dtype=float)
        )
        closed = closed_drawdown(exits, starting_equity_usd=starting_equity_usd)
        floating = equity_envelope_drawdown(local_curve)
        winners_removed = exits["pnl_usd"].nlargest(top_winners_removed).sum()
        family_fraction = (
            float(entries["family_id"].value_counts(normalize=True).max())
            if len(entries)
            else 0.0
        )
        rows.append(
            {
                "policy_id": policy_id,
                "window": window_id,
                "window_start_utc": start.isoformat(),
                "cutoff_exclusive_utc": end.isoformat(),
                "weekdays": weekdays,
                "entries": len(entries),
                "exits": len(exits),
                "entries_per_weekday": len(entries) / weekdays if weekdays else 0.0,
                "active_entry_days": int(entries["entry_time"].dt.date.nunique()),
                "active_entry_day_fraction": float(
                    entries["entry_time"].dt.date.nunique() / weekdays
                )
                if weekdays
                else 0.0,
                "net_usd": float(exits["pnl_usd"].sum()),
                "gross_profit_usd": float(exits.loc[exits["pnl_usd"].gt(0), "pnl_usd"].sum()),
                "gross_loss_usd": float(-exits.loc[exits["pnl_usd"].lt(0), "pnl_usd"].sum()),
                "profit_factor": profit_factor(exits["pnl_usd"]),
                "win_rate": float(exits["pnl_usd"].gt(0).mean()) if len(exits) else None,
                "mean_stress_r": float(exits["stress_net_r"].mean()) if len(exits) else None,
                "mean_pnl_usd": float(exits["pnl_usd"].mean()) if len(exits) else None,
                "closed_drawdown_usd": closed["maximum_drawdown_usd"],
                "closed_drawdown_fraction_of_start": closed["maximum_drawdown_fraction"],
                "floating_drawdown_usd": floating["maximum_drawdown_usd"],
                "floating_drawdown_fraction_of_start": float(
                    floating["maximum_drawdown_usd"] / starting_equity_usd
                ),
                "minimum_equity_usd": float(local_curve["low_equity_usd"].min()),
                "maximum_open_positions": int(local_curve["open_positions"].max()),
                "maximum_open_initial_risk_usd": float(
                    local_curve["open_initial_risk_usd"].max()
                ),
                "maximum_open_margin_usd": float(local_curve["open_margin_usd"].max()),
                "positive_active_exit_day_fraction": float(daily.gt(0.0).mean())
                if len(daily)
                else None,
                "positive_weekday_fraction": float(daily.gt(0.0).sum() / weekdays)
                if weekdays
                else 0.0,
                "positive_active_month_fraction": float(monthly.gt(0.0).mean())
                if len(monthly)
                else None,
                "positive_calendar_month_fraction": float(
                    monthly.gt(0.0).sum() / _month_count(start, end)
                ),
                "top_winners_removed": min(top_winners_removed, len(exits)),
                "top_winners_removed_net_usd": float(exits["pnl_usd"].sum() - winners_removed),
                "maximum_single_family_entry_fraction": family_fraction,
            }
        )
    return pd.DataFrame(rows)


def daily_metrics(
    ledger: pd.DataFrame,
    *,
    policy_id: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    starting_equity_usd: float,
) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end - pd.Timedelta(days=1), freq="D", tz="UTC")
    result = pd.DataFrame({"date_utc": dates})
    entry_dates = ledger["entry_time"].dt.floor("D")
    exit_dates = ledger["label_end_time"].dt.floor("D")
    entries = ledger.groupby(entry_dates).size()
    exits = ledger.groupby(exit_dates).size()
    pnl = ledger.groupby(exit_dates)["pnl_usd"].sum()
    result["policy_id"] = policy_id
    result["is_weekday"] = result["date_utc"].dt.weekday.lt(5)
    result["entries"] = result["date_utc"].map(entries).fillna(0).astype(int)
    result["exits"] = result["date_utc"].map(exits).fillna(0).astype(int)
    result["closed_pnl_usd"] = result["date_utc"].map(pnl).fillna(0.0)
    result["closed_balance_usd"] = starting_equity_usd + result["closed_pnl_usd"].cumsum()
    peak = np.maximum.accumulate(
        np.concatenate(([starting_equity_usd], result["closed_balance_usd"].to_numpy(float)))
    )[1:]
    result["closed_drawdown_usd"] = peak - result["closed_balance_usd"]
    return result[
        [
            "policy_id",
            "date_utc",
            "is_weekday",
            "entries",
            "exits",
            "closed_pnl_usd",
            "closed_balance_usd",
            "closed_drawdown_usd",
        ]
    ]


def attribution_metrics(ledger: pd.DataFrame, *, policy_id: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dimension in ("family_id", "broad_mechanic", "direction"):
        for value, group in ledger.groupby(dimension, sort=True):
            rows.append(
                {
                    "policy_id": policy_id,
                    "dimension": dimension,
                    "value": str(value),
                    "trades": len(group),
                    "entry_fraction": len(group) / len(ledger) if len(ledger) else 0.0,
                    "net_usd": float(group["pnl_usd"].sum()),
                    "profit_factor": profit_factor(group["pnl_usd"]),
                    "win_rate": float(group["pnl_usd"].gt(0.0).mean()),
                    "mean_stress_r": float(group["stress_net_r"].mean()),
                    "first_entry_utc": group["entry_time"].min().isoformat(),
                    "last_entry_utc": group["entry_time"].max().isoformat(),
                }
            )
    return pd.DataFrame(rows)


def six_month_stability(
    ledger: pd.DataFrame,
    *,
    policy_id: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    block_start = start
    while block_start < end:
        block_end = min(block_start + pd.DateOffset(months=6), end)
        entries = ledger.loc[
            ledger["entry_time"].ge(block_start) & ledger["entry_time"].lt(block_end)
        ]
        exits = ledger.loc[
            ledger["label_end_time"].ge(block_start)
            & ledger["label_end_time"].lt(block_end)
        ]
        weekdays = _weekdays(block_start, block_end)
        rows.append(
            {
                "policy_id": policy_id,
                "block_start_utc": block_start.isoformat(),
                "block_end_exclusive_utc": block_end.isoformat(),
                "entries": len(entries),
                "entries_per_weekday": len(entries) / weekdays if weekdays else 0.0,
                "exits": len(exits),
                "net_usd": float(exits["pnl_usd"].sum()),
                "profit_factor": profit_factor(exits["pnl_usd"]),
                "positive": bool(exits["pnl_usd"].sum() > 0.0),
            }
        )
        block_start = block_end
    return pd.DataFrame(rows)
