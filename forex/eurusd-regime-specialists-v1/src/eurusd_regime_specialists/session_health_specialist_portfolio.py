from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .h4_chop_anchor_validation import (
    _evaluation_subset,
    _scenario_summary,
    audit_m5,
    circular_block_bootstrap,
)
from .h4_dual_regime_portfolio_diagnostic import (
    apply_weighted_cost,
    circular_calendar_month_bootstrap,
    concurrency_audit,
)
from .h4_session_frequency_expansion import apply_causal_risk_cap
from .neutral_h4_quiet_state_transfer import load_m5, sha256_file
from .rsi_health_gate_historical_transfer import (
    aggregate_m15,
    build_rsi_signals,
    profit_factor,
    simulate_rsi_trades,
)


CHRONOLOGY = (
    "EARLY_2017_2019",
    "MIDDLE_2020_2022H1",
    "LATE_2022H2_2024H1",
    "RECENT_2024H2_2026H1",
)


def session_bucket(
    timestamp: pd.Timestamp, buckets: dict[str, list[int]]
) -> str:
    hour = int(pd.Timestamp(timestamp).hour)
    matches = [
        name for name, hours in buckets.items() if hour in set(map(int, hours))
    ]
    if len(matches) != 1:
        raise RuntimeError(f"UTC hour {hour} maps to {len(matches)} sessions")
    return matches[0]


def causal_session_health_gate(
    trades: pd.DataFrame, contract: dict[str, Any]
) -> pd.DataFrame:
    ordered = trades.sort_values(
        ["entry_time_utc", "exit_time_utc"], kind="stable"
    ).reset_index(drop=True)
    ordered["session_bucket"] = ordered["entry_time_utc"].map(
        lambda value: session_bucket(value, contract["buckets"])
    )
    lookback = int(contract["lookback_completed_shadow_trades_per_bucket"])
    threshold = float(contract["minimum_trailing_profit_factor"])
    ordered["available_completed_session_trades"] = 0
    ordered["trailing_session_profit_factor"] = 0.0
    ordered["session_health_admitted"] = False
    for name in contract["buckets"]:
        bucket_indices = ordered.index[ordered["session_bucket"].eq(name)]
        exits = ordered.loc[bucket_indices].sort_values(
            ["exit_time_utc", "entry_time_utc"], kind="stable"
        )
        exit_times = (
            exits["exit_time_utc"]
            .dt.as_unit("ns")
            .astype("int64")
            .to_numpy(dtype=np.int64)
        )
        exit_pnl = exits["pnl_usd_001_lot"].to_numpy(dtype=float)
        for index in bucket_indices:
            entry = pd.Timestamp(ordered.at[index, "entry_time_utc"])
            available = int(
                np.searchsorted(exit_times, entry.value, side="right")
            )
            window = exit_pnl[:available][-lookback:]
            factor = profit_factor(window)
            ordered.at[index, "available_completed_session_trades"] = available
            ordered.at[index, "trailing_session_profit_factor"] = factor
            ordered.at[index, "session_health_admitted"] = bool(
                len(window) == lookback and factor >= threshold
            )
    return ordered


def _windows(
    trades: pd.DataFrame, reporting: dict[str, list[str]]
) -> dict[str, dict[str, Any]]:
    return {
        name: _scenario_summary(_evaluation_subset(trades, window))
        for name, window in reporting.items()
    }


def _fx_days(
    m5: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> int:
    subset = m5[
        (m5["timestamp"] >= start)
        & (m5["timestamp"] < end)
        & (m5["timestamp"].dt.dayofweek < 5)
    ]
    return int(subset["timestamp"].dt.strftime("%Y-%m-%d").nunique())


def _gate_results(
    windows: dict[str, dict[str, Any]],
    scenarios: dict[str, dict[str, Any]],
    trade_bootstrap: dict[str, Any],
    calendar_bootstrap: dict[str, Any],
    frequency: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    full = windows["FULL_AUDIT"]
    return {
        "minimum_trades_per_fx_day": frequency["trades_per_fx_day"]
        >= float(gates["minimum_trades_per_fx_day"]),
        "minimum_full_profit_factor": full["profit_factor"]
        >= float(gates["minimum_full_profit_factor"]),
        "minimum_extra_0p5pip_profit_factor": scenarios[
            "COST_PLUS_0P5_PIP"
        ]["profit_factor"]
        >= float(gates["minimum_extra_0p5pip_profit_factor"]),
        "minimum_extra_1p0pip_profit_factor": scenarios[
            "COST_PLUS_1P0_PIP"
        ]["profit_factor"]
        >= float(gates["minimum_extra_1p0pip_profit_factor"]),
        "each_chronological_block_profit_factor": all(
            windows[name]["profit_factor"]
            > float(
                gates[
                    "minimum_each_chronological_block_profit_factor_exclusive"
                ]
            )
            for name in CHRONOLOGY
        ),
        "minimum_recent_block_profit_factor": windows[
            "RECENT_2024H2_2026H1"
        ]["profit_factor"]
        >= float(gates["minimum_recent_block_profit_factor"]),
        "minimum_latest_12_month_profit_factor": windows[
            "LATEST_12_MONTHS"
        ]["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "minimum_latest_6_month_net_r": windows["LATEST_6_MONTHS"]["net_r"]
        > float(gates["minimum_latest_6_month_net_r_exclusive"]),
        "win_rate": float(gates["minimum_win_rate"])
        <= full["win_rate"]
        <= float(gates["maximum_win_rate"]),
        "realized_payoff_ratio": float(
            gates["minimum_realized_payoff_ratio"]
        )
        <= full["realized_payoff_ratio"]
        <= float(gates["maximum_realized_payoff_ratio"]),
        "minimum_positive_active_month_share": full[
            "positive_active_month_share"
        ]
        >= float(gates["minimum_positive_active_month_share"]),
        "minimum_top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown_r": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
        "minimum_trade_bootstrap_pf_5pct": trade_bootstrap[
            "profit_factor"
        ]["q05"]
        > float(gates["minimum_trade_bootstrap_pf_5pct_exclusive"]),
        "maximum_trade_bootstrap_probability_pf_lte_1": trade_bootstrap[
            "probability_profit_factor_lte_1"
        ]
        <= float(gates["maximum_trade_bootstrap_probability_pf_lte_1"]),
        "minimum_calendar_bootstrap_pf_5pct": calendar_bootstrap[
            "profit_factor"
        ]["q05"]
        > float(gates["minimum_calendar_bootstrap_pf_5pct_exclusive"]),
        "maximum_calendar_bootstrap_probability_pf_lte_1": calendar_bootstrap[
            "probability_profit_factor_lte_1"
        ]
        <= float(gates["maximum_calendar_bootstrap_probability_pf_lte_1"]),
    }


def _latest_months(trades: pd.DataFrame) -> list[dict[str, Any]]:
    recent = _evaluation_subset(
        trades,
        ["2026-01-01T00:00:00Z", "2026-07-01T00:00:00Z"],
    ).copy()
    recent["month"] = recent["entry_time_utc"].dt.strftime("%Y-%m")
    rows = []
    for month in pd.period_range("2026-01", "2026-06", freq="M").astype(str):
        group = recent[recent["month"].eq(month)]
        rows.append({"month": month, **_scenario_summary(group)})
    return rows


def _render_report(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL_AUDIT"]
    recent = result["windows"]["RECENT_2024H2_2026H1"]
    latest = result["windows"]["LATEST_6_MONTHS"]
    failed = [
        name for name, passed in result["gate_results"].items() if not passed
    ]
    month_rows = "\n".join(
        f"| {row['month']} | {row['trades']} | {row['win_rate']:.2%} | "
        f"{row['realized_payoff_ratio']:.3f} | "
        f"{row['profit_factor']:.3f} | {row['net_r']:+.3f} | "
        f"${row['pnl_usd_001_lot']:+.2f} |"
        for row in result["latest_6_months_by_month"]
    )
    return f"""# EURUSD session-health specialist portfolio result

Status: **{result["status"]}**

| Window | Trades | Trades/FX day | Win rate | Payoff | PF | Net R | 0.01-lot USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full 2017-2026 | {full["trades"]} | {result["frequency"]["trades_per_fx_day"]:.3f} | {full["win_rate"]:.2%} | {full["realized_payoff_ratio"]:.3f} | {full["profit_factor"]:.3f} | {full["net_r"]:+.3f} | ${full["pnl_usd_001_lot"]:+.2f} |
| Recent 2024H2-2026H1 | {recent["trades"]} | - | {recent["win_rate"]:.2%} | {recent["realized_payoff_ratio"]:.3f} | {recent["profit_factor"]:.3f} | {recent["net_r"]:+.3f} | ${recent["pnl_usd_001_lot"]:+.2f} |
| Latest six months | {latest["trades"]} | - | {latest["win_rate"]:.2%} | {latest["realized_payoff_ratio"]:.3f} | {latest["profit_factor"]:.3f} | {latest["net_r"]:+.3f} | ${latest["pnl_usd_001_lot"]:+.2f} |

Full PF after another 0.5 pip round trip: {result["scenarios"]["COST_PLUS_0P5_PIP"]["profit_factor"]:.3f}.
Full PF with the best 5% of winners removed: {full["top_5pct_winners_removed_profit_factor"]:.3f}.

## Latest six months by month

| Month | Trades | Win rate | Payoff | PF | Net R | 0.01-lot USD |
|---|---:|---:|---:|---:|---:|---:|
{month_rows}

Failed frozen gates: {", ".join(failed) if failed else "none"}.

This is adaptive historical research. It does not authorize broker orders.
"""


def run(
    config_path: Path, output_dir: Path
) -> tuple[dict[str, Any], pd.DataFrame]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    root = config_path.parent.parent
    anchor_path = root / config["anchor_config"]["path"]
    h4_path = root / config["h4_core_ledger"]["path"]
    if sha256_file(anchor_path) != config["anchor_config"]["sha256"]:
        raise RuntimeError("Anchor configuration checksum mismatch")
    if sha256_file(h4_path) != config["h4_core_ledger"]["sha256"]:
        raise RuntimeError("H4 core ledger checksum mismatch")
    anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
    m5 = load_m5(anchor["source"])
    data_audit = audit_m5(m5, anchor["source"])

    m15 = aggregate_m15(m5, config["rsi_long_expert"])
    signals = build_rsi_signals(m15, config["rsi_long_expert"])
    raw_rsi = simulate_rsi_trades(
        m5,
        signals,
        config["rsi_long_expert"],
        anchor["source"]["quarantine"],
    )
    gated_rsi = causal_session_health_gate(
        raw_rsi, config["session_health_gate"]
    )
    admitted_rsi = gated_rsi[
        gated_rsi["session_health_admitted"]
    ].copy()
    admitted_rsi["specialist_id"] = (
        "RSI_1P5R_" + admitted_rsi["session_bucket"]
    )
    admitted_rsi["owned_regime"] = admitted_rsi["session_bucket"]
    admitted_rsi["portfolio_sleeve"] = "RSI_SESSION_HEALTH"
    admitted_rsi["portfolio_risk_weight"] = float(
        config["portfolio_risk"]["rsi_risk_weight"]
    )
    admitted_rsi["pnl_usd_001_lot_equivalent"] = admitted_rsi[
        "pnl_usd_001_lot"
    ]
    admitted_rsi["entry_delay_minutes"] = 0

    h4 = pd.read_csv(
        h4_path,
        parse_dates=[
            "signal_time_utc",
            "entry_time_utc",
            "exit_time_utc",
        ],
    )
    if len(h4) != int(config["h4_core_ledger"]["expected_rows"]):
        raise RuntimeError("Unexpected H4 core row count")
    start, end = map(pd.Timestamp, config["evaluation_window"])
    candidates = pd.concat([h4, admitted_rsi], ignore_index=True, sort=False)
    candidates = _evaluation_subset(candidates, config["evaluation_window"])
    portfolio, cap = apply_causal_risk_cap(
        candidates,
        maximum_risk=float(
            config["portfolio_risk"][
                "maximum_concurrent_initial_risk_units"
            ]
        ),
        priority=config["portfolio_risk"]["fixed_priority"],
    )
    windows = _windows(portfolio, config["reporting_windows"])
    scenarios = {
        "COST_PLUS_0P5_PIP": _scenario_summary(
            apply_weighted_cost(portfolio, 0.5)
        ),
        "COST_PLUS_1P0_PIP": _scenario_summary(
            apply_weighted_cost(portfolio, 1.0)
        ),
    }
    bootstrap = config["bootstrap"]
    trade_bootstrap = circular_block_bootstrap(
        portfolio["r"].to_numpy(dtype=float),
        samples=int(bootstrap["samples"]),
        block_trades=int(bootstrap["trade_block_trades"]),
        seed=int(bootstrap["seed"]),
        lower_quantile=float(bootstrap["lower_quantile"]),
    )
    calendar_bootstrap = circular_calendar_month_bootstrap(
        portfolio,
        start=start,
        end=end,
        samples=int(bootstrap["samples"]),
        block_months=int(bootstrap["calendar_block_months"]),
        seed=int(bootstrap["seed"]),
        lower_quantile=float(bootstrap["lower_quantile"]),
    )
    fx_days = _fx_days(m5, start, end)
    frequency = {
        "trades": len(portfolio),
        "fx_days": fx_days,
        "trades_per_fx_day": len(portfolio) / fx_days,
        "active_trade_days": int(
            portfolio["entry_time_utc"].dt.strftime("%Y-%m-%d").nunique()
        ),
    }
    gate_results = _gate_results(
        windows,
        scenarios,
        trade_bootstrap,
        calendar_bootstrap,
        frequency,
        config["admission"],
    )
    result = {
        "schema_version": "eurusd_session_health_specialist_portfolio_result_v1",
        "status": (
            "BACKTEST_GATES_PASSED_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if all(gate_results.values())
            else "REJECTED_SESSION_HEALTH_SPECIALIST_PORTFOLIO"
        ),
        "demo_ready": False,
        "live_ready": False,
        "broker_action_allowed": False,
        "adaptive_historical_development_not_pristine_oos": True,
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "data_audit": data_audit,
        "rsi_census": {
            "signals": len(signals),
            "raw_trades": len(raw_rsi),
            "admitted_trades_before_portfolio_cap": len(admitted_rsi),
            "admitted_by_session": {
                name: int(admitted_rsi["session_bucket"].eq(name).sum())
                for name in config["session_health_gate"]["buckets"]
            },
        },
        "risk_cap": cap,
        "concurrency": concurrency_audit(portfolio),
        "frequency": frequency,
        "windows": windows,
        "scenarios": scenarios,
        "trade_bootstrap": trade_bootstrap,
        "calendar_bootstrap": calendar_bootstrap,
        "latest_6_months_by_month": _latest_months(portfolio),
        "gate_results": gate_results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    signals.to_csv(output_dir / "RSI_SIGNALS.csv", index=False)
    gated_rsi.to_csv(
        output_dir / "RSI_SHADOW_TRADES_WITH_SESSION_GATE.csv", index=False
    )
    portfolio.to_csv(output_dir / "PORTFOLIO_TRADES.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "RESULT.md").write_text(
        _render_report(result), encoding="utf-8", newline="\n"
    )
    return result, portfolio
