from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd


def load_v61_router(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("locked_v61_router", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def positive_month_share(
    trades: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> float:
    months = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).to_period("M"),
        freq="M",
    )
    if len(months) == 0:
        return 0.0
    selected = trades.loc[
        trades["entry_time"].ge(start) & trades["entry_time"].lt(end)
    ].copy()
    if selected.empty:
        monthly = pd.Series(0.0, index=months)
    else:
        keys = selected["entry_time"].dt.tz_localize(None).dt.to_period("M")
        monthly = selected.groupby(keys)["pnl_usd"].sum().reindex(months, fill_value=0.0)
    return float(monthly.gt(0.0).mean())


def full_window_metrics(
    router: ModuleType,
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    selected = trades.loc[
        trades["entry_time"].ge(start) & trades["entry_time"].lt(end)
    ].copy()
    pnl = selected["pnl_usd"].astype(float)
    winners = pnl.nlargest(min(5, len(pnl))).index
    return {
        "trades": int(len(selected)),
        "weekdays": int(router.business_days(start, end)),
        "trades_per_weekday": float(
            len(selected) / router.business_days(start, end)
        ),
        "net_usd": float(pnl.sum()),
        "profit_factor": float(router.profit_factor(pnl)),
        "closed_drawdown_usd": float(router.closed_drawdown(selected)),
        "top5_removed_net_usd": float(pnl.drop(winners).sum()),
        "positive_month_share": positive_month_share(selected, start, end),
    }


def evaluate_windows(
    router: ModuleType,
    new_trades: pd.DataFrame,
    combined: pd.DataFrame,
    windows: dict[str, list[str]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for window_name, bounds in windows.items():
        start, end = (pd.Timestamp(value) for value in bounds)
        for portfolio_id, trades in (("NEW", new_trades), ("COMBINED", combined)):
            rows.append(
                {
                    "window": window_name,
                    "portfolio_id": portfolio_id,
                    "window_start_utc": str(start),
                    "cutoff_exclusive_utc": str(end),
                    **full_window_metrics(router, trades, start, end),
                }
            )
    return pd.DataFrame(rows)


def verify_locked_development(
    windows: pd.DataFrame,
    expected: dict[str, float],
    absolute_tolerance: float = 1e-9,
) -> None:
    lookup = windows.set_index(["window", "portfolio_id"])
    mapping = {
        "development_1_new_profit_factor": ("development_1", "NEW", "profit_factor"),
        "development_1_combined_profit_factor": (
            "development_1",
            "COMBINED",
            "profit_factor",
        ),
        "development_1_combined_closed_drawdown_usd": (
            "development_1",
            "COMBINED",
            "closed_drawdown_usd",
        ),
        "development_2_new_trades": ("development_2", "NEW", "trades"),
        "development_2_new_profit_factor": ("development_2", "NEW", "profit_factor"),
        "development_2_combined_trades_per_weekday": (
            "development_2",
            "COMBINED",
            "trades_per_weekday",
        ),
        "development_2_combined_profit_factor": (
            "development_2",
            "COMBINED",
            "profit_factor",
        ),
        "development_2_combined_closed_drawdown_usd": (
            "development_2",
            "COMBINED",
            "closed_drawdown_usd",
        ),
    }
    for key, expected_value in expected.items():
        window_name, portfolio_id, metric = mapping[key]
        actual = float(lookup.loc[(window_name, portfolio_id), metric])
        if not np.isclose(actual, float(expected_value), atol=absolute_tolerance, rtol=0.0):
            raise ValueError(f"Locked development mismatch for {key}: {actual}")


def gate_results(windows: pd.DataFrame, gates: dict[str, Any]) -> list[dict[str, Any]]:
    lookup = windows.set_index(["window", "portfolio_id"])
    results: list[dict[str, Any]] = []
    for window_name in gates["required_windows"]:
        new = lookup.loc[(window_name, "NEW")]
        combined = lookup.loc[(window_name, "COMBINED")]
        checks = {
            "minimum_new_trades": float(new["trades"])
            >= float(gates["minimum_new_trades"]),
            "minimum_new_profit_factor": float(new["profit_factor"])
            >= float(gates["minimum_new_profit_factor"]),
            "minimum_new_net_usd": float(new["net_usd"])
            > float(gates["minimum_new_net_usd"]),
            "minimum_new_top5_removed_net_usd": float(new["top5_removed_net_usd"])
            > float(gates["minimum_new_top5_removed_net_usd"]),
            "minimum_combined_trades_per_weekday": float(
                combined["trades_per_weekday"]
            )
            >= float(gates["minimum_combined_trades_per_weekday"]),
            "minimum_combined_profit_factor": float(combined["profit_factor"])
            >= float(gates["minimum_combined_profit_factor"]),
            "minimum_combined_net_usd": float(combined["net_usd"])
            > float(gates["minimum_combined_net_usd"]),
            "maximum_combined_closed_drawdown_usd": float(
                combined["closed_drawdown_usd"]
            )
            <= float(gates["maximum_combined_closed_drawdown_usd"]),
            "minimum_combined_positive_month_share": float(
                combined["positive_month_share"]
            )
            >= float(gates["minimum_combined_positive_month_share"]),
        }
        results.append(
            {
                "window": window_name,
                "passed": bool(all(checks.values())),
                "checks": checks,
            }
        )
    return results
