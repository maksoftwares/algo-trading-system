from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def profit_factor(values: pd.Series) -> float:
    values = values.astype(float)
    gain = float(values.loc[values > 0.0].sum())
    loss = float(-values.loc[values < 0.0].sum())
    if loss == 0.0:
        return math.inf if gain > 0.0 else 0.0
    return gain / loss


def stage_metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    top_winners: int,
) -> dict[str, Any]:
    selected = trades.loc[
        (trades["entry_time"] >= start) & (trades["entry_time"] < end)
    ].sort_values(["exit_time", "event_id"], kind="mergesort")
    values = selected["portfolio_usd"].astype(float)
    weekdays = len(
        pd.date_range(
            start.tz_localize(None).normalize(),
            (end.tz_localize(None) - pd.Timedelta(nanoseconds=1)).normalize(),
            freq="B",
        )
    )
    equity = np.concatenate(([0.0], values.cumsum().to_numpy(dtype=float)))
    removed = values.drop(values.nlargest(min(top_winners, len(values))).index)
    return {
        "trades": int(len(selected)),
        "frequency": float(len(selected) / weekdays) if weekdays else 0.0,
        "net_usd": float(values.sum()),
        "average_usd": float(values.mean()) if len(values) else 0.0,
        "pf": profit_factor(values),
        "drawdown_usd": float(np.max(np.maximum.accumulate(equity) - equity)),
        "top_removed_usd": float(removed.sum()),
    }


def positive_month_share(
    trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> float:
    months = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end.tz_localize(None) - pd.Timedelta(nanoseconds=1)).to_period("M"),
        freq="M",
    )
    selected = trades.loc[
        (trades["entry_time"] >= start) & (trades["entry_time"] < end)
    ].copy()
    if selected.empty:
        return 0.0
    selected["month"] = selected["entry_time"].dt.tz_localize(None).dt.to_period("M")
    monthly = (
        selected.groupby("month", sort=True)["portfolio_usd"]
        .sum()
        .reindex(months, fill_value=0.0)
    )
    return float(monthly.gt(0.0).mean())


def core_ledger(core: pd.DataFrame, weight: float) -> pd.DataFrame:
    result = pd.DataFrame(
        {
            "event_id": "CORE_" + core["trade_id"].astype(str),
            "entry_time": pd.to_datetime(core["entry_time_utc"], utc=True),
            "exit_time": pd.to_datetime(core["exit_time_utc"], utc=True),
            "raw_usd": core["pnl_usd_0p01_equiv"].astype(float),
            "risk_weight": float(weight),
            "source_type": "CORE",
        }
    )
    result["portfolio_usd"] = result["raw_usd"] * result["risk_weight"]
    return result


def expansion_ledger(expansion: pd.DataFrame, weight: float) -> pd.DataFrame:
    result = expansion.copy()
    result["raw_usd"] = result["stress_usd"].astype(float)
    result["risk_weight"] = float(weight)
    result["portfolio_usd"] = result["raw_usd"] * result["risk_weight"]
    result["source_type"] = "EXPANSION"
    return result


def evaluate_stage(
    expansion: pd.DataFrame,
    core: pd.DataFrame,
    stage: str,
    config: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    start, end = map(pd.Timestamp, config["windows"][stage])
    top = int(config["gates"]["common"]["top_winners_removed"])
    expansion_metrics = stage_metrics(expansion, start, end, top)
    core_metrics = stage_metrics(core, start, end, top)
    columns = [
        "event_id",
        "entry_time",
        "exit_time",
        "raw_usd",
        "risk_weight",
        "portfolio_usd",
        "source_type",
    ]
    combined = pd.concat([core[columns], expansion[columns]], ignore_index=True)
    combined_metrics = stage_metrics(combined, start, end, top)
    month_share = positive_month_share(expansion, start, end)
    expansion_metrics["positive_month_share"] = month_share
    common = config["gates"]["common"]
    stage_gate = config["gates"][stage]
    checks = {
        "minimum_frequency": combined_metrics["frequency"]
        >= float(stage_gate["minimum_frequency"]),
        "maximum_frequency": combined_metrics["frequency"]
        <= float(stage_gate["maximum_frequency"]),
        "minimum_expansion_pf": expansion_metrics["pf"]
        >= float(common["minimum_expansion_pf"]),
        "positive_expansion_net": expansion_metrics["net_usd"] > 0.0,
        "positive_expansion_average": expansion_metrics["average_usd"] > 0.0,
        "minimum_expansion_positive_month_share": month_share
        >= float(stage_gate["minimum_expansion_positive_month_share"]),
        "minimum_combined_pf": combined_metrics["pf"]
        >= float(common["minimum_combined_pf"]),
        "combined_net_not_below_core": combined_metrics["net_usd"]
        >= core_metrics["net_usd"] - 1e-10,
        "maximum_drawdown_ratio": combined_metrics["drawdown_usd"]
        <= core_metrics["drawdown_usd"]
        * float(common["maximum_drawdown_ratio_to_core"]),
        "expansion_top_winners_removed_positive": expansion_metrics["top_removed_usd"]
        > 0.0,
        "top_winners_removed_positive": combined_metrics["top_removed_usd"] > 0.0,
    }
    stage_combined = combined.loc[
        (combined["entry_time"] >= start) & (combined["entry_time"] < end)
    ].copy()
    stage_combined["stage"] = stage
    return (
        {
            "stage": stage,
            "gate_pass": bool(all(checks.values())),
            "checks": checks,
            "expansion": expansion_metrics,
            "core": core_metrics,
            "combined": combined_metrics,
        },
        stage_combined,
    )
