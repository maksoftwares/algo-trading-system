from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .neutral_h4_quiet_state_transfer import sha256_file


def profit_factor(values: pd.Series | np.ndarray) -> float:
    vector = np.asarray(values, dtype=float)
    gains = float(vector[vector > 0.0].sum())
    losses = float(-vector[vector < 0.0].sum())
    if losses == 0.0:
        return math.inf if gains > 0.0 else 0.0
    return gains / losses


def trading_date(timestamp: pd.Timestamp) -> str:
    adjusted = (
        timestamp + pd.Timedelta(days=1)
        if timestamp.weekday() == 6
        else timestamp
    )
    return adjusted.date().isoformat()


def maximum_concurrency(frame: pd.DataFrame) -> int:
    events: list[tuple[pd.Timestamp, int]] = []
    for row in frame.itertuples():
        events.append((row.entry_time, 1))
        events.append((row.exit_time, -1))
    active = 0
    maximum = 0
    for _, change in sorted(events, key=lambda item: (item[0], item[1])):
        active += change
        maximum = max(maximum, active)
    return maximum


def restore_executable_sizing(
    combined: pd.DataFrame,
    protected: pd.DataFrame,
    *,
    rsi_fixed_lots: float,
) -> pd.DataFrame:
    result = combined.copy()
    protected = protected.copy()
    for column in ("entry_time", "exit_time"):
        protected[column] = pd.to_datetime(
            protected[column],
            format="%Y.%m.%d %H:%M:%S",
            utc=True,
        )
    protected["key"] = (
        protected["entry_time"].astype(str)
        + "|"
        + protected["exit_time"].astype(str)
    )
    if protected["key"].duplicated().any():
        raise RuntimeError("Protected executable keys are not unique")
    executable = protected.set_index("key")[["profit", "volume"]]
    result["key"] = (
        result["entry_time"].astype(str)
        + "|"
        + result["exit_time"].astype(str)
    )
    regime_mask = result["component"].eq("M15_REGIME")
    matched = result.loc[regime_mask, "key"].isin(executable.index)
    if not matched.all() or int(regime_mask.sum()) != len(protected):
        raise RuntimeError("Protected executable ledger does not map exactly")
    result.loc[regime_mask, "pnl_usd"] = result.loc[
        regime_mask, "key"
    ].map(executable["profit"])
    result.loc[regime_mask, "volume"] = result.loc[
        regime_mask, "key"
    ].map(executable["volume"])
    result.loc[~regime_mask, "volume"] = float(rsi_fixed_lots)
    return result.drop(columns="key").sort_values(
        ["entry_time", "component", "exit_time"]
    ).reset_index(drop=True)


def outcome_metrics(
    frame: pd.DataFrame,
    *,
    weekdays: int,
    extra_cost_usd_per_001_lot: float,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "trades": 0,
            "trades_per_weekday": 0.0,
            "weekday_coverage": 0.0,
            "active_trading_dates": 0,
            "win_rate": 0.0,
            "payoff_ratio": 0.0,
            "profit_factor": 0.0,
            "stressed_profit_factor": 0.0,
            "net_pnl_usd": 0.0,
            "stressed_net_pnl_usd": 0.0,
            "maximum_closed_trade_drawdown_usd": 0.0,
            "top_5pct_removed_profit_factor": 0.0,
            "positive_active_month_share": 0.0,
        }
    ordered = frame.sort_values(
        ["exit_time", "component", "entry_time"]
    ).copy()
    pnl = ordered["pnl_usd"].astype(float)
    stress_cost = (
        ordered["volume"].astype(float) / 0.01
    ) * float(extra_cost_usd_per_001_lot)
    stressed = pnl - stress_cost
    winners = pnl[pnl > 0.0]
    losers = pnl[pnl < 0.0]
    payoff = (
        float(winners.mean() / -losers.mean())
        if not winners.empty and not losers.empty
        else 0.0
    )
    equity = pnl.cumsum().to_numpy()
    path = np.concatenate(([0.0], equity))
    drawdown = np.maximum.accumulate(path) - path
    remove_count = max(1, math.ceil(len(ordered) * 0.05))
    removed = ordered.drop(ordered.nlargest(remove_count, "pnl_usd").index)
    dates = {trading_date(value) for value in ordered["entry_time"]}
    monthly = (
        ordered.assign(month=ordered["entry_time"].dt.strftime("%Y-%m"))
        .groupby("month")["pnl_usd"]
        .sum()
    )
    return {
        "trades": len(ordered),
        "trades_per_weekday": len(ordered) / int(weekdays),
        "weekday_coverage": len(dates) / int(weekdays),
        "active_trading_dates": len(dates),
        "win_rate": float((pnl > 0.0).mean()),
        "payoff_ratio": payoff,
        "profit_factor": profit_factor(pnl),
        "stressed_profit_factor": profit_factor(stressed),
        "net_pnl_usd": float(pnl.sum()),
        "stressed_net_pnl_usd": float(stressed.sum()),
        "maximum_closed_trade_drawdown_usd": float(drawdown.max()),
        "top_5pct_removed_profit_factor": profit_factor(
            removed["pnl_usd"]
        ),
        "positive_active_month_share": float((monthly > 0.0).mean()),
    }


def admission_checks(
    full: dict[str, Any],
    first: dict[str, Any],
    second: dict[str, Any],
    concurrency: int,
    gates: dict[str, Any],
) -> dict[str, bool]:
    return {
        "minimum_trades_per_weekday": full["trades_per_weekday"]
        >= float(gates["minimum_trades_per_weekday"]),
        "minimum_weekday_coverage": full["weekday_coverage"]
        >= float(gates["minimum_weekday_coverage"]),
        "minimum_full_profit_factor": full["profit_factor"]
        >= float(gates["minimum_full_profit_factor"]),
        "minimum_full_stressed_profit_factor": full[
            "stressed_profit_factor"
        ]
        >= float(gates["minimum_full_stressed_profit_factor"]),
        "minimum_full_top_5pct_removed_profit_factor": full[
            "top_5pct_removed_profit_factor"
        ]
        >= float(gates["minimum_full_top_5pct_removed_profit_factor"]),
        "minimum_each_half_profit_factor": min(
            first["profit_factor"], second["profit_factor"]
        )
        >= float(gates["minimum_each_half_profit_factor"]),
        "minimum_second_half_profit_factor": second["profit_factor"]
        >= float(gates["minimum_second_half_profit_factor"]),
        "minimum_second_half_stressed_profit_factor": second[
            "stressed_profit_factor"
        ]
        >= float(gates["minimum_second_half_stressed_profit_factor"]),
        "minimum_second_half_top_5pct_removed_profit_factor": second[
            "top_5pct_removed_profit_factor"
        ]
        >= float(gates["minimum_second_half_top_5pct_removed_profit_factor"]),
        "minimum_positive_active_month_share": full[
            "positive_active_month_share"
        ]
        >= float(gates["minimum_positive_active_month_share"]),
        "maximum_closed_trade_drawdown": full[
            "maximum_closed_trade_drawdown_usd"
        ]
        <= float(gates["maximum_closed_trade_drawdown_usd"]),
        "maximum_concurrent_positions": concurrency
        <= int(gates["maximum_concurrent_positions"]),
    }


def render_report(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    full = metrics["full"]
    first = metrics["first_12_months"]
    second = metrics["second_12_months"]
    return f"""# EURUSD executable-sizing frequency portfolio result

Status: **{result["status"]}**

Demo-order authorization: **false**

| Window | Trades | Trades/weekday | Coverage | Win rate | Payoff | PF | Stressed PF | Best-5%-removed PF | Net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full two years | {full["trades"]} | {full["trades_per_weekday"]:.3f} | {full["weekday_coverage"]:.2%} | {full["win_rate"]:.2%} | {full["payoff_ratio"]:.3f} | {full["profit_factor"]:.3f} | {full["stressed_profit_factor"]:.3f} | {full["top_5pct_removed_profit_factor"]:.3f} | ${full["net_pnl_usd"]:.2f} |
| First 12 months | {first["trades"]} | {first["trades_per_weekday"]:.3f} | {first["weekday_coverage"]:.2%} | {first["win_rate"]:.2%} | {first["payoff_ratio"]:.3f} | {first["profit_factor"]:.3f} | {first["stressed_profit_factor"]:.3f} | {first["top_5pct_removed_profit_factor"]:.3f} | ${first["net_pnl_usd"]:.2f} |
| Second 12 months | {second["trades"]} | {second["trades_per_weekday"]:.3f} | {second["weekday_coverage"]:.2%} | {second["win_rate"]:.2%} | {second["payoff_ratio"]:.3f} | {second["profit_factor"]:.3f} | {second["stressed_profit_factor"]:.3f} | {second["top_5pct_removed_profit_factor"]:.3f} | ${second["net_pnl_usd"]:.2f} |

The protected chop/compression sizes are the unchanged broker-tested volumes.
The RSI gate remains retrospectively mined and historically non-transferable,
so a pass can authorize only a disarmed prospective router build.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    root = config_path.parent.parent
    combined_path = root / config["selected_combined_ledger"]["path"]
    protected_path = root / config["protected_executable_ledger"]["path"]
    for path, expected in (
        (combined_path, config["selected_combined_ledger"]["sha256"]),
        (protected_path, config["protected_executable_ledger"]["sha256"]),
    ):
        if sha256_file(path) != expected:
            raise RuntimeError(f"Source checksum mismatch: {path}")
    combined = pd.read_csv(
        combined_path, parse_dates=["entry_time", "exit_time"]
    )
    if len(combined) != int(
        config["selected_combined_ledger"]["expected_rows"]
    ):
        raise RuntimeError("Combined source row count mismatch")
    protected = pd.read_csv(protected_path)
    if len(protected) != int(
        config["protected_executable_ledger"]["expected_rows"]
    ):
        raise RuntimeError("Protected source row count mismatch")
    restored = restore_executable_sizing(
        combined,
        protected,
        rsi_fixed_lots=float(
            config["portfolio_contract"]["rsi_fixed_lots"]
        ),
    )
    split = pd.Timestamp(config["period"]["chronological_split"])
    cost = (
        float(config["stress"]["extra_round_trip_pips"])
        * float(config["stress"]["usd_per_pip_at_0_01_lot"])
    )
    full = outcome_metrics(
        restored,
        weekdays=int(config["period"]["full_weekdays"]),
        extra_cost_usd_per_001_lot=cost,
    )
    first = outcome_metrics(
        restored[restored["entry_time"] < split],
        weekdays=int(config["period"]["half_weekdays"]),
        extra_cost_usd_per_001_lot=cost,
    )
    second = outcome_metrics(
        restored[restored["entry_time"] >= split],
        weekdays=int(config["period"]["half_weekdays"]),
        extra_cost_usd_per_001_lot=cost,
    )
    concurrency = maximum_concurrency(restored)
    checks = admission_checks(
        full,
        first,
        second,
        concurrency,
        config["historical_admission"],
    )
    admitted = all(checks.values())
    status = (
        "HISTORICAL_FORWARD_ONLY_CANDIDATE_BUILD_DISARMED_ROUTER"
        if admitted
        else "EXECUTABLE_SIZING_PORTFOLIO_REJECTED"
    )
    result = {
        "schema_version": "eurusd_executable_sizing_frequency_portfolio_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "combined_ledger_sha256": config["selected_combined_ledger"][
            "sha256"
        ],
        "protected_ledger_sha256": config["protected_executable_ledger"][
            "sha256"
        ],
        "research_boundary": "RETROSPECTIVE_FORWARD_ONLY_NOT_PRISTINE_OOS",
        "broker_action_allowed": False,
        "demo_order_authorized": False,
        "metrics": {
            "full": full,
            "first_12_months": first,
            "second_12_months": second,
            "maximum_concurrent_positions": concurrency,
        },
        "checks": checks,
        "admitted_for_disarmed_router_build": admitted,
        "status": status,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    restored.to_csv(output_dir / "EXECUTABLE_SIZING_TRADES.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "RESULT.md").write_text(
        render_report(result), encoding="utf-8"
    )
    return result
