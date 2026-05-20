from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from phase0.data_contracts import Trade
from phase0.trades import trades_to_dataframe


@dataclass(frozen=True)
class MetricsSummary:
    trade_count: int
    win_rate: float
    profit_factor: float
    total_pnl_usd: float
    total_return_pct: float
    avg_trade_R: float
    median_trade_R: float
    max_drawdown_usd: float
    max_drawdown_pct: float
    worst_month_usd: float
    best_month_usd: float
    losing_month_pct: float
    max_consecutive_zero_trade_months: int
    max_consecutive_losing_months: int
    largest_single_trade_pct_of_pnl: float
    top5_trades_pct_of_pnl: float


REQUIRED_PER_CELL_METRICS = (
    "cell_id",
    "time_window",
    "tick_source",
    "cost_model",
    "expert",
    "symbol",
    "trade_count",
    "win_rate",
    "profit_factor",
    "total_return_pct",
    "total_pnl_usd",
    "avg_trade_R",
    "median_trade_R",
    "max_drawdown_pct",
    "max_drawdown_usd",
    "worst_month_usd",
    "best_month_usd",
    "losing_month_pct",
    "max_consecutive_zero_trade_months",
    "max_consecutive_losing_months",
    "largest_single_trade_pct_of_pnl",
    "top5_trades_pct_of_pnl",
    "p95_to_best_pf_ratio",
)


def equity_curve_from_trades(trades: list[Trade], starting_equity: float) -> pd.DataFrame:
    rows = [
        {
            "trade_index": 0,
            "timestamp_utc": "",
            "net_pnl_usd": 0.0,
            "equity": starting_equity,
        }
    ]
    equity = starting_equity
    for index, trade in enumerate(trades, start=1):
        equity += trade.net_pnl_usd
        rows.append(
            {
                "trade_index": index,
                "timestamp_utc": trade.exit_time_utc,
                "net_pnl_usd": trade.net_pnl_usd,
                "equity": equity,
            }
        )
    return pd.DataFrame(rows)


def summarize_trades(
    trades: list[Trade],
    starting_equity: float,
    period_start: datetime | str | pd.Timestamp | None = None,
    period_end: datetime | str | pd.Timestamp | None = None,
) -> MetricsSummary:
    monthly = monthly_metrics(trades, period_start, period_end)
    if not trades:
        return MetricsSummary(
            trade_count=0,
            win_rate=0.0,
            profit_factor=0.0,
            total_pnl_usd=0.0,
            total_return_pct=0.0,
            avg_trade_R=0.0,
            median_trade_R=0.0,
            max_drawdown_usd=0.0,
            max_drawdown_pct=0.0,
            worst_month_usd=monthly["worst_month_usd"],
            best_month_usd=monthly["best_month_usd"],
            losing_month_pct=monthly["losing_month_pct"],
            max_consecutive_zero_trade_months=monthly["max_consecutive_zero_trade_months"],
            max_consecutive_losing_months=monthly["max_consecutive_losing_months"],
            largest_single_trade_pct_of_pnl=100.0,
            top5_trades_pct_of_pnl=100.0,
        )

    trades_df = trades_to_dataframe(trades)
    pnl = pd.to_numeric(trades_df["net_pnl_usd"], errors="coerce").fillna(0.0)
    r_values = pd.to_numeric(trades_df["r_multiple"], errors="coerce").fillna(0.0)
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = abs(pnl[pnl < 0].sum())
    profit_factor = float("inf") if gross_loss == 0 and gross_profit > 0 else (
        float(gross_profit / gross_loss) if gross_loss > 0 else 0.0
    )
    equity = equity_curve_from_trades(trades, starting_equity)
    drawdowns = _drawdowns(equity["equity"])
    total_pnl = float(pnl.sum())
    concentration = concentration_metrics(pnl)
    return MetricsSummary(
        trade_count=len(trades),
        win_rate=float((pnl > 0).mean()),
        profit_factor=profit_factor,
        total_pnl_usd=total_pnl,
        total_return_pct=total_pnl / starting_equity * 100.0,
        avg_trade_R=float(r_values.mean()),
        median_trade_R=float(r_values.median()),
        max_drawdown_usd=float(drawdowns["drawdown_usd"].max()),
        max_drawdown_pct=float(drawdowns["drawdown_pct"].max()),
        worst_month_usd=monthly["worst_month_usd"],
        best_month_usd=monthly["best_month_usd"],
        losing_month_pct=monthly["losing_month_pct"],
        max_consecutive_zero_trade_months=monthly["max_consecutive_zero_trade_months"],
        max_consecutive_losing_months=monthly["max_consecutive_losing_months"],
        largest_single_trade_pct_of_pnl=concentration["largest_single_trade_pct_of_pnl"],
        top5_trades_pct_of_pnl=concentration["top5_trades_pct_of_pnl"],
    )


def metrics_row(
    trades: list[Trade],
    starting_equity: float,
    period_start: datetime | str | pd.Timestamp | None = None,
    period_end: datetime | str | pd.Timestamp | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    summary = summarize_trades(trades, starting_equity, period_start, period_end)
    row: dict[str, object] = {
        "trade_count": summary.trade_count,
        "win_rate": summary.win_rate,
        "profit_factor": summary.profit_factor,
        "total_pnl_usd": summary.total_pnl_usd,
        "total_return_pct": summary.total_return_pct,
        "avg_trade_R": summary.avg_trade_R,
        "median_trade_R": summary.median_trade_R,
        "max_drawdown_usd": summary.max_drawdown_usd,
        "max_drawdown_pct": summary.max_drawdown_pct,
        "worst_month_usd": summary.worst_month_usd,
        "best_month_usd": summary.best_month_usd,
        "losing_month_pct": summary.losing_month_pct,
        "max_consecutive_zero_trade_months": summary.max_consecutive_zero_trade_months,
        "max_consecutive_losing_months": summary.max_consecutive_losing_months,
        "largest_single_trade_pct_of_pnl": summary.largest_single_trade_pct_of_pnl,
        "top5_trades_pct_of_pnl": summary.top5_trades_pct_of_pnl,
        "p95_to_best_pf_ratio": pd.NA,
    }
    if extra:
        return {**extra, **row}
    return row


def monthly_metrics(
    trades: list[Trade],
    period_start: datetime | str | pd.Timestamp | None,
    period_end: datetime | str | pd.Timestamp | None,
) -> dict[str, float | int]:
    months = _month_index(trades, period_start, period_end)
    if len(months) == 0:
        return {
            "worst_month_usd": 0.0,
            "best_month_usd": 0.0,
            "losing_month_pct": 0.0,
            "max_consecutive_zero_trade_months": 0,
            "max_consecutive_losing_months": 0,
        }

    monthly_pnl = pd.Series(0.0, index=months)
    monthly_trade_count = pd.Series(0, index=months)
    for trade in trades:
        exit_timestamp = pd.Timestamp(trade.exit_time_utc)
        if exit_timestamp.tzinfo is not None:
            exit_timestamp = exit_timestamp.tz_convert("UTC").tz_localize(None)
        exit_month = exit_timestamp.to_period("M")
        if exit_month in monthly_pnl.index:
            monthly_pnl.loc[exit_month] += float(trade.net_pnl_usd)
            monthly_trade_count.loc[exit_month] += 1

    losing_months = monthly_pnl < 0
    zero_trade_months = monthly_trade_count == 0
    return {
        "worst_month_usd": float(monthly_pnl.min()),
        "best_month_usd": float(monthly_pnl.max()),
        "losing_month_pct": float(losing_months.mean() * 100.0),
        "max_consecutive_zero_trade_months": max_consecutive_true(zero_trade_months.tolist()),
        "max_consecutive_losing_months": max_consecutive_true(losing_months.tolist()),
    }


def concentration_metrics(net_pnl: pd.Series) -> dict[str, float]:
    pnl = pd.to_numeric(net_pnl, errors="coerce").fillna(0.0)
    total_net_profit = float(pnl.sum())
    if total_net_profit <= 0:
        return {
            "largest_single_trade_pct_of_pnl": 100.0,
            "top5_trades_pct_of_pnl": 100.0,
        }

    positive = pnl[pnl > 0].sort_values(ascending=False)
    largest = float(positive.iloc[0]) if len(positive) else 0.0
    top5 = float(positive.head(5).sum()) if len(positive) else 0.0
    return {
        "largest_single_trade_pct_of_pnl": largest / total_net_profit * 100.0,
        "top5_trades_pct_of_pnl": top5 / total_net_profit * 100.0,
    }


def add_cost_sensitivity_ratios(matrix_metrics: pd.DataFrame) -> pd.DataFrame:
    result = matrix_metrics.copy()
    if "p95_to_best_pf_ratio" not in result:
        result["p95_to_best_pf_ratio"] = pd.NA
    pairings = ((1, 3), (4, 6), (7, 9))
    for best_cell, p95_cell in pairings:
        best_rows = result[result["cell_id"].astype(int) == best_cell]
        p95_rows = result[result["cell_id"].astype(int) == p95_cell]
        if best_rows.empty or p95_rows.empty:
            continue
        best_pf = float(best_rows.iloc[0]["profit_factor"])
        p95_pf = float(p95_rows.iloc[0]["profit_factor"])
        if best_pf == float("inf") and p95_pf == float("inf"):
            ratio = float("inf")
        elif best_pf == 0 or best_pf == float("inf"):
            ratio = 0.0
        else:
            ratio = p95_pf / best_pf
        result.loc[result["cell_id"].astype(int) == p95_cell, "p95_to_best_pf_ratio"] = ratio
    return result


def _drawdowns(equity: pd.Series) -> pd.DataFrame:
    running_peak = equity.cummax()
    drawdown_usd = running_peak - equity
    drawdown_pct = drawdown_usd / running_peak.replace(0, pd.NA) * 100.0
    return pd.DataFrame({"drawdown_usd": drawdown_usd, "drawdown_pct": drawdown_pct.fillna(0.0)})


def max_consecutive_true(values: list[bool]) -> int:
    max_run = 0
    current = 0
    for value in values:
        if value:
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return max_run


def _month_index(
    trades: list[Trade],
    period_start: datetime | str | pd.Timestamp | None,
    period_end: datetime | str | pd.Timestamp | None,
) -> pd.PeriodIndex:
    if period_start is None or period_end is None:
        if not trades:
            return pd.PeriodIndex([], freq="M")
        exits = [pd.Timestamp(trade.exit_time_utc) for trade in trades]
        period_start = min(exits)
        period_end = max(exits)

    start = pd.Timestamp(period_start)
    end = pd.Timestamp(period_end)
    if start.tzinfo is not None:
        start = start.tz_convert("UTC").tz_localize(None)
    if end.tzinfo is not None:
        end = end.tz_convert("UTC").tz_localize(None)
    if end < start:
        return pd.PeriodIndex([], freq="M")
    return pd.period_range(start=start.to_period("M"), end=end.to_period("M"), freq="M")
