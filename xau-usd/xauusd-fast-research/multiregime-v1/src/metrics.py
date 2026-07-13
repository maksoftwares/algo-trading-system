from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def profit_factor(values: pd.Series) -> float | None:
    wins = float(values.loc[values > 0].sum()) if len(values) else 0.0
    losses = float(-values.loc[values < 0].sum()) if len(values) else 0.0
    return wins / losses if losses > 0 else (999.0 if wins > 0 else None)


def floating_drawdown(trades: pd.DataFrame, net_column: str = "net_r") -> float:
    equity = peak = worst = 0.0
    if trades.empty:
        return 0.0
    for _, trade in trades.sort_values("entry_time", kind="mergesort").iterrows():
        peak = max(peak, equity)
        floating_equity = equity - float(trade["mae_r"])
        worst = max(worst, peak - floating_equity)
        equity += float(trade[net_column])
        worst = max(worst, peak - equity)
        peak = max(peak, equity)
    return float(worst)


def _top_winner_share(values: pd.Series, count: int) -> float:
    wins = values.loc[values > 0]
    gross = float(wins.sum())
    return float(wins.nlargest(count).sum() / gross) if gross > 0 else 0.0


def summary(trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> dict[str, Any]:
    values = trades["net_r"] if len(trades) else pd.Series(dtype=float)
    stress = trades["stress_net_r"] if len(trades) else pd.Series(dtype=float)
    months = pd.period_range(start.tz_localize(None).to_period("M"), (end - pd.Timedelta(seconds=1)).tz_localize(None).to_period("M"), freq="M")
    month_counts = trades.groupby(trades["entry_time"].dt.tz_localize(None).dt.to_period("M")).size() if len(trades) else pd.Series(dtype=int)
    month_counts = month_counts.reindex(months, fill_value=0)
    years = max((end - start).total_seconds() / (365.2425 * 86400), 1e-9)
    latest12 = trades.loc[trades["entry_time"] >= end - pd.DateOffset(months=12)] if len(trades) else trades
    latest6 = trades.loc[trades["entry_time"] >= end - pd.DateOffset(months=6)] if len(trades) else trades
    latest3 = trades.loc[trades["entry_time"] >= end - pd.DateOffset(months=3)] if len(trades) else trades
    gross_positive = float(values.loc[values > 0].sum())
    by_day = trades.groupby(trades["entry_time"].dt.date)["net_r"].sum() if len(trades) else pd.Series(dtype=float)
    positive_days = float(by_day.loc[by_day > 0].sum())
    by_year = trades.groupby(trades["entry_time"].dt.year)["net_r"].sum() if len(trades) else pd.Series(dtype=float)
    positive_years = by_year.loc[by_year > 0]
    return {
        "trades": int(len(trades)), "wins": int((values > 0).sum()), "losses": int((values < 0).sum()),
        "profit_factor": profit_factor(values), "expectancy_r": float(values.mean()) if len(values) else 0.0,
        "net_r": float(values.sum()), "stress_profit_factor": profit_factor(stress),
        "stress_expectancy_r": float(stress.mean()) if len(stress) else 0.0, "stress_net_r": float(stress.sum()),
        "floating_drawdown_r": floating_drawdown(trades), "stress_floating_drawdown_r": floating_drawdown(trades, "stress_net_r"),
        "average_trades_per_year": float(len(trades) / years), "median_trades_per_calendar_month": float(month_counts.median()),
        "latest_12_month_trades": int(len(latest12)), "latest_6_month_trades": int(len(latest6)), "latest_3_month_trades": int(len(latest3)),
        "latest_12_month_profit_factor": profit_factor(latest12["net_r"]) if len(latest12) else None,
        "latest_12_month_expectancy_r": float(latest12["net_r"].mean()) if len(latest12) else 0.0,
        "top_ten_winner_share": _top_winner_share(values, 10),
        "top_three_days_share": float(by_day.nlargest(3).sum() / positive_days) if positive_days > 0 else 0.0,
        "best_year_positive_net_share": float(positive_years.max() / positive_years.sum()) if len(positive_years) else 0.0,
        "gross_positive_r": gross_positive,
    }


def monthly_results(trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    months = pd.period_range(start.tz_localize(None).to_period("M"), (end - pd.Timedelta(seconds=1)).tz_localize(None).to_period("M"), freq="M")
    rows = []
    naive_month = trades["entry_time"].dt.tz_localize(None).dt.to_period("M") if len(trades) else pd.Series(dtype="period[M]")
    for month in months:
        group = trades.loc[naive_month == month] if len(trades) else trades
        rows.append({
            "month": str(month), "trades": int(len(group)), "net_r": float(group["net_r"].sum()) if len(group) else 0.0,
            "profit_factor": profit_factor(group["net_r"]) if len(group) else None,
            "expectancy_r": float(group["net_r"].mean()) if len(group) else 0.0,
            "stress_net_r": float(group["stress_net_r"].sum()) if len(group) else 0.0,
        })
    return pd.DataFrame(rows)


def rolling_results(trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for months in (12, 24):
        window_end = start + pd.DateOffset(months=months)
        while window_end <= end:
            window_start = window_end - pd.DateOffset(months=months)
            group = trades.loc[(trades["entry_time"] >= window_start) & (trades["entry_time"] < window_end)] if len(trades) else trades
            rows.append({
                "window_months": months, "start": window_start, "end_exclusive": window_end,
                "trades": int(len(group)), "net_r": float(group["net_r"].sum()) if len(group) else 0.0,
                "profit_factor": profit_factor(group["net_r"]) if len(group) else None,
                "expectancy_r": float(group["net_r"].mean()) if len(group) else 0.0,
            })
            window_end += pd.DateOffset(months=1)
    return pd.DataFrame(rows)


def standalone_family_gate(metrics: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "trades_gte_200": metrics["trades"] >= 200,
        "pf_gte_1p15": (metrics["profit_factor"] or 0) >= 1.15,
        "expectancy_gte_0p05": metrics["expectancy_r"] >= 0.05,
        "stress_pf_gte_1p03": (metrics["stress_profit_factor"] or 0) >= 1.03,
        "stress_expectancy_positive": metrics["stress_expectancy_r"] > 0,
        "stress_net_positive": metrics["stress_net_r"] > 0,
        "floating_dd_lte_15": metrics["floating_drawdown_r"] <= 15,
        "top_ten_lte_0p40": metrics["top_ten_winner_share"] <= 0.40,
    }
    return {"passed": all(checks.values()), "checks": checks}


def gate_audit(
    family_summaries: dict[str, dict[str, Any]], portfolio: dict[str, Any], rolling: pd.DataFrame,
    trades: pd.DataFrame, signals: pd.DataFrame, coverage_complete: bool,
) -> dict[str, Any]:
    family_gates = {family: standalone_family_gate(metrics) for family, metrics in family_summaries.items()}
    rolling12 = rolling.loc[rolling["window_months"] == 12]
    rolling24 = rolling.loc[rolling["window_months"] == 24]
    positive12 = float((rolling12["net_r"] > 0).mean()) if len(rolling12) else 0.0
    all24 = bool((rolling24["net_r"] > 0).all()) if len(rolling24) else False
    positive_by_family = trades.groupby("strategy_id")["net_r"].sum().clip(lower=0) if len(trades) else pd.Series(dtype=float)
    family_share = float(positive_by_family.max() / positive_by_family.sum()) if positive_by_family.sum() > 0 else 1.0
    portfolio_checks = {
        "trades_gte_1200": portfolio["trades"] >= 1200,
        "average_trades_per_year_gte_120": portfolio["average_trades_per_year"] >= 120,
        "median_month_gte_8": portfolio["median_trades_per_calendar_month"] >= 8,
        "latest12_gte_100": portfolio["latest_12_month_trades"] >= 100,
        "latest6_gte_45": portfolio["latest_6_month_trades"] >= 45,
        "latest3_gte_20": portfolio["latest_3_month_trades"] >= 20,
        "pf_gte_1p30": (portfolio["profit_factor"] or 0) >= 1.30,
        "expectancy_gte_0p10": portfolio["expectancy_r"] >= 0.10,
        "stress_pf_gte_1p12": (portfolio["stress_profit_factor"] or 0) >= 1.12,
        "stress_expectancy_gte_0p04": portfolio["stress_expectancy_r"] >= 0.04,
        "latest12_pf_gte_1p15": (portfolio["latest_12_month_profit_factor"] or 0) >= 1.15,
        "latest12_expectancy_gte_0p05": portfolio["latest_12_month_expectancy_r"] >= 0.05,
        "floating_dd_lte_20": portfolio["floating_drawdown_r"] <= 20,
        "stress_floating_dd_lte_25": portfolio["stress_floating_drawdown_r"] <= 25,
        "positive_rolling12_gte_70pct": positive12 >= 0.70,
        "all_rolling24_positive": all24,
        "top_ten_lte_0p30": portfolio["top_ten_winner_share"] <= 0.30,
        "top_three_days_lte_0p20": portfolio["top_three_days_share"] <= 0.20,
        "best_year_lte_0p35": portfolio["best_year_positive_net_share"] <= 0.35,
        "family_positive_net_share_lte_0p65": family_share <= 0.65,
    }
    sizing_reject = signals.get("rejection_reason", pd.Series(dtype=str)) == "CONTRACT_GRANULARITY_OR_MARGIN_REJECT"
    opportunity_count = int(signals["signal_accepted"].sum() + sizing_reject.sum()) if len(signals) else 0
    granularity_rejects = int(sizing_reject.sum())
    granularity_pct = 100.0 * granularity_rejects / opportunity_count if opportunity_count else 0.0
    return {
        "data_complete": coverage_complete, "family_gates": family_gates,
        "at_least_one_family_passes": any(item["passed"] for item in family_gates.values()),
        "portfolio_checks": portfolio_checks, "portfolio_passed": all(portfolio_checks.values()),
        "positive_rolling_12_month_fraction": positive12, "all_rolling_24_month_positive": all24,
        "maximum_positive_family_share": family_share, "contract_granularity_rejects": granularity_rejects,
        "valid_opportunities": opportunity_count, "contract_granularity_reject_pct": granularity_pct,
        "contract_granularity_adequate": granularity_pct <= 10.0,
    }
