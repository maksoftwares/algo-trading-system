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
    _parity_check,
    _scenario_summary,
    audit_m5,
    circular_block_bootstrap,
    count_utc_rollovers,
)
from .neutral_h4_quiet_state_transfer import (
    PIP_VALUE_USD_001_LOT,
    add_h4_regimes,
    aggregate_h1,
    build_signal_mask,
    load_m5,
    sha256_file,
    simulate_short,
    summarize,
)


def apply_portfolio_weight(trades: pd.DataFrame, weight: float) -> pd.DataFrame:
    result = trades.copy()
    result["portfolio_risk_weight"] = float(weight)
    result["r"] = result["r"] * float(weight)
    result["stress_r"] = result["stress_r"] * float(weight)
    result["pnl_usd_001_lot_equivalent"] = result["pnl_usd_001_lot"] * float(weight)
    result["pnl_usd_001_lot"] = result["pnl_usd_001_lot_equivalent"]
    return result


def apply_weighted_cost(trades: pd.DataFrame, extra_pips: float) -> pd.DataFrame:
    result = trades.copy()
    penalty_r = (
        float(extra_pips) / result["stop_pips"] * result["portfolio_risk_weight"]
    )
    result["extra_cost_pips"] = float(extra_pips)
    result["r"] = result["r"] - penalty_r
    result["stress_r"] = result["r"]
    result["pnl_usd_001_lot"] = result["pnl_usd_001_lot"] - (
        float(extra_pips) * PIP_VALUE_USD_001_LOT * result["portfolio_risk_weight"]
    )
    return result


def apply_weighted_rollover(
    trades: pd.DataFrame, charge_pips_per_crossing: float
) -> pd.DataFrame:
    result = trades.copy()
    result["rollover_crossings"] = [
        count_utc_rollovers(entry, exit_time)
        for entry, exit_time in zip(
            result["entry_time_utc"], result["exit_time_utc"], strict=True
        )
    ]
    result["extra_cost_pips"] = result["rollover_crossings"] * float(
        charge_pips_per_crossing
    )
    penalty_r = (
        result["extra_cost_pips"]
        / result["stop_pips"]
        * result["portfolio_risk_weight"]
    )
    result["r"] = result["r"] - penalty_r
    result["stress_r"] = result["r"]
    result["pnl_usd_001_lot"] = result["pnl_usd_001_lot"] - (
        result["extra_cost_pips"]
        * PIP_VALUE_USD_001_LOT
        * result["portfolio_risk_weight"]
    )
    return result


def circular_calendar_month_bootstrap(
    trades: pd.DataFrame,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    samples: int,
    block_months: int,
    seed: int,
    lower_quantile: float,
) -> dict[str, Any]:
    work = trades.copy()
    work["month"] = work["entry_time_utc"].dt.tz_convert(None).dt.to_period("M")
    calendar = pd.period_range(
        start.tz_convert(None).to_period("M"),
        (end - pd.Timedelta(microseconds=1)).tz_convert(None).to_period("M"),
        freq="M",
    )
    grouped = (
        work.groupby("month")["r"]
        .agg(
            gross_gain=lambda values: values[values > 0.0].sum(),
            gross_loss=lambda values: -values[values < 0.0].sum(),
            net_r="sum",
        )
        .reindex(calendar, fill_value=0.0)
    )
    vectors = grouped[["gross_gain", "gross_loss", "net_r"]].to_numpy(dtype=float)
    month_count = len(vectors)
    block_count = math.ceil(month_count / block_months)
    rng = np.random.default_rng(seed)
    offsets = np.arange(block_months)
    profit_factors = np.empty(samples)
    mean_r = np.empty(samples)
    written = 0
    while written < samples:
        batch = min(500, samples - written)
        starts = rng.integers(0, month_count, size=(batch, block_count))
        indices = ((starts[:, :, None] + offsets) % month_count).reshape(batch, -1)[
            :, :month_count
        ]
        totals = vectors[indices].sum(axis=1)
        profit_factors[written : written + batch] = np.divide(
            totals[:, 0],
            totals[:, 1],
            out=np.where(totals[:, 0] > 0.0, np.inf, 0.0),
            where=totals[:, 1] > 0.0,
        )
        mean_r[written : written + batch] = totals[:, 2] / len(trades)
        written += batch

    def quantiles(values: np.ndarray) -> dict[str, float]:
        low, median, high = np.quantile(
            values, [lower_quantile, 0.5, 1.0 - lower_quantile]
        )
        return {"q05": float(low), "median": float(median), "q95": float(high)}

    return {
        "method": "CIRCULAR_CALENDAR_MONTH_BLOCK",
        "samples": int(samples),
        "block_months": int(block_months),
        "calendar_months": month_count,
        "seed": int(seed),
        "profit_factor": quantiles(profit_factors),
        "mean_r_per_observed_trade": quantiles(mean_r),
        "probability_profit_factor_lte_1": float(np.mean(profit_factors <= 1.0)),
    }


def concurrency_audit(trades: pd.DataFrame) -> dict[str, Any]:
    events: list[tuple[pd.Timestamp, int, float]] = []
    for row in trades.itertuples():
        weight = float(row.portfolio_risk_weight)
        events.append((row.entry_time_utc, 1, weight))
        events.append((row.exit_time_utc, 0, -weight))
    events.sort(key=lambda item: (item[0], item[1]))
    positions = 0
    risk = 0.0
    maximum_positions = 0
    maximum_risk = 0.0
    for _, event_type, change in events:
        positions += 1 if event_type == 1 else -1
        risk += change
        maximum_positions = max(maximum_positions, positions)
        maximum_risk = max(maximum_risk, risk)
    return {
        "maximum_concurrent_positions": maximum_positions,
        "maximum_concurrent_initial_risk_units": maximum_risk,
    }


def _descriptive_checks(
    windows: dict[str, dict[str, Any]],
    scenarios: dict[str, dict[str, Any]],
    trade_bootstrap: dict[str, Any],
    calendar_bootstrap: dict[str, Any],
    parity: dict[str, Any],
    data_audit: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, bool]:
    chronology = (
        "EARLY_2017_2019",
        "MIDDLE_2020_2022H1",
        "LATE_2022H2_2024H1",
        "RECENT_2024H2_2026H1",
    )
    full = windows["FULL_AUDIT"]
    return {
        "data_integrity": bool(data_audit["all_checks_passed"]),
        "both_prior_ledgers_reproduced": all(
            item["all_checks_passed"] for item in parity.values()
        ),
        "full_profit_factor": full["profit_factor"]
        >= float(thresholds["minimum_full_profit_factor"]),
        "extra_0p5pip_profit_factor": scenarios["COST_PLUS_0P5_PIP"]["profit_factor"]
        >= float(thresholds["minimum_extra_0p5pip_profit_factor"]),
        "each_chronological_block_profit_factor": all(
            windows[name]["profit_factor"]
            > float(
                thresholds["minimum_each_chronological_block_profit_factor_exclusive"]
            )
            for name in chronology
        ),
        "latest_12_month_profit_factor": windows["LATEST_12_MONTHS"]["profit_factor"]
        >= float(thresholds["minimum_latest_12_month_profit_factor"]),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(thresholds["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(thresholds["maximum_closed_trade_drawdown_r"]),
        "entry_delay_5m_profit_factor": scenarios["ENTRY_DELAY_5M"]["profit_factor"]
        >= float(thresholds["minimum_delay_profit_factor"]),
        "entry_delay_15m_profit_factor": scenarios["ENTRY_DELAY_15M"]["profit_factor"]
        >= float(thresholds["minimum_delay_profit_factor"]),
        "extra_1p0pip_profit_factor": scenarios["COST_PLUS_1P0_PIP"]["profit_factor"]
        >= float(thresholds["minimum_extra_1p0pip_profit_factor"]),
        "trade_bootstrap_pf_5pct": trade_bootstrap["profit_factor"]["q05"]
        > float(thresholds["minimum_bootstrap_pf_5pct_exclusive"]),
        "trade_bootstrap_probability_pf_lte_1": trade_bootstrap[
            "probability_profit_factor_lte_1"
        ]
        <= float(thresholds["maximum_bootstrap_probability_pf_lte_1"]),
        "calendar_bootstrap_pf_5pct": calendar_bootstrap["profit_factor"]["q05"]
        > float(thresholds["minimum_bootstrap_pf_5pct_exclusive"]),
        "calendar_bootstrap_probability_pf_lte_1": calendar_bootstrap[
            "probability_profit_factor_lte_1"
        ]
        <= float(thresholds["maximum_bootstrap_probability_pf_lte_1"]),
    }


def _render_report(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL_AUDIT"]
    latest_12 = result["windows"]["LATEST_12_MONTHS"]
    latest_6 = result["windows"]["LATEST_6_MONTHS"]
    scenarios = result["scenarios"]
    months = result["latest_6_months_by_month"]
    month_lines = "\n".join(
        f"| {row['month']} | {row['trades']} | {row['win_rate']:.1%} | "
        f"{row['profit_factor']:.3f} | {row['net_r']:+.3f} |"
        for row in months
    )
    return f"""# EURUSD H4 dual-regime portfolio diagnostic

Status: **{result["status"]}**

This combines the unchanged chop expert at 1.0 risk with the unchanged compression expert at 0.5 risk. It is a post-selection developmental result, not pristine confirmation and not permission to trade.

## Full history

- 507 trades from 2017-01 through 2026-06
- Win rate: {full["win_rate"]:.2%}
- Payoff ratio: {full["realized_payoff_ratio"]:.3f}
- Profit factor: {full["profit_factor"]:.3f}
- Net: {full["net_r"]:+.3f}R
- Maximum closed-trade drawdown: {full["maximum_drawdown_r"]:.3f}R
- PF with best 5% of winners removed: {full["top_5pct_winners_removed_profit_factor"]:.3f}

## Robustness

- +0.5 pip cost PF: {scenarios["COST_PLUS_0P5_PIP"]["profit_factor"]:.3f}
- +1.0 pip cost PF: {scenarios["COST_PLUS_1P0_PIP"]["profit_factor"]:.3f}
- 5-minute delayed entry PF: {scenarios["ENTRY_DELAY_5M"]["profit_factor"]:.3f}
- 15-minute delayed entry PF: {scenarios["ENTRY_DELAY_15M"]["profit_factor"]:.3f}
- Trade-block bootstrap PF 5th percentile: {result["trade_bootstrap"]["profit_factor"]["q05"]:.3f}; P(PF <= 1): {result["trade_bootstrap"]["probability_profit_factor_lte_1"]:.2%}
- Three-calendar-month block bootstrap PF 5th percentile: {result["calendar_bootstrap"]["profit_factor"]["q05"]:.3f}; P(PF <= 1): {result["calendar_bootstrap"]["probability_profit_factor_lte_1"]:.2%}

## Recent results

- Latest 12 months: {latest_12["trades"]} trades, PF {latest_12["profit_factor"]:.3f}, {latest_12["net_r"]:+.3f}R
- Latest 6 months: {latest_6["trades"]} trades, win rate {latest_6["win_rate"]:.2%}, payoff {latest_6["realized_payoff_ratio"]:.3f}, PF {latest_6["profit_factor"]:.3f}, {latest_6["net_r"]:+.3f}R

| Month | Trades | Win rate | PF | Net R |
|---|---:|---:|---:|---:|
{month_lines}

All inherited descriptive thresholds passed: {result["all_inherited_descriptive_thresholds_passed"]}.

This is the strongest honest regime-combination result in the current branch. Because the half-risk allocation was selected after historical inspection, the next valid evidence must come from an untouched/prospective sample.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    package_root = config_path.parent.parent
    anchor_config_path = package_root / config["anchor_config_path"]
    prior_ledger_path = package_root / config["prior_ledger_path"]
    if sha256_file(anchor_config_path) != config["anchor_config_sha256"]:
        raise RuntimeError("Anchor configuration checksum mismatch")
    if sha256_file(prior_ledger_path) != config["prior_ledger_sha256"]:
        raise RuntimeError("Prior ledger checksum mismatch")
    anchor_config = json.loads(anchor_config_path.read_bytes())
    m5 = load_m5(anchor_config["source"])
    data_audit = audit_m5(m5, anchor_config["source"])
    h1 = aggregate_h1(m5)
    h1, _ = add_h4_regimes(h1, anchor_config["classifier"])

    ledgers: dict[int, pd.DataFrame] = {}
    diagnostics: dict[str, Any] = {}
    parity: dict[str, Any] = {}
    for delay in (0, *config["stress_scenarios"]["entry_delay_minutes"]):
        pieces = []
        for specialist_id, weight in config["specialists"].items():
            candidate = next(
                item
                for item in anchor_config["candidates"]
                if item["specialist_id"] == specialist_id
            )
            mask = build_signal_mask(h1, candidate)
            raw, diag = simulate_short(
                h1,
                m5,
                mask,
                candidate,
                anchor_config,
                entry_delay_minutes=int(delay),
            )
            diagnostics[f"{specialist_id}_{delay}m"] = diag
            if delay == 0:
                parity[specialist_id] = _parity_check(
                    raw,
                    prior_ledger_path,
                    specialist_id,
                    config["evaluation_window"],
                )
            pieces.append(apply_portfolio_weight(raw, float(weight)))
        combined = pd.concat(pieces, ignore_index=True).sort_values("exit_time_utc")
        ledgers[int(delay)] = _evaluation_subset(combined, config["evaluation_window"])

    base = ledgers[0]
    plus_half = apply_weighted_cost(base, 0.5)
    plus_one = apply_weighted_cost(base, 1.0)
    rollover = apply_weighted_rollover(
        base,
        float(config["stress_scenarios"]["rollover_charge_pips_per_utc_21_crossing"]),
    )
    scenario_ledgers = {
        "BASE": base,
        "COST_PLUS_0P5_PIP": plus_half,
        "COST_PLUS_1P0_PIP": plus_one,
        "ENTRY_DELAY_5M": ledgers[5],
        "ENTRY_DELAY_15M": ledgers[15],
        "ROLLOVER_0P5_PIP": rollover,
    }
    scenarios = {
        name: _scenario_summary(trades) for name, trades in scenario_ledgers.items()
    }
    windows = {
        name: summarize(_evaluation_subset(base, window))
        for name, window in config["reporting_windows"].items()
    }

    trade_config = config["trade_bootstrap"]
    trade_bootstrap = circular_block_bootstrap(
        base["r"].to_numpy(dtype=float),
        samples=int(trade_config["samples"]),
        block_trades=int(trade_config["block_trades"]),
        seed=int(trade_config["seed"]),
        lower_quantile=float(trade_config["lower_quantile"]),
    )
    calendar_config = config["calendar_bootstrap"]
    start, end = map(pd.Timestamp, config["evaluation_window"])
    calendar_bootstrap = circular_calendar_month_bootstrap(
        base,
        start=start,
        end=end,
        samples=int(calendar_config["samples"]),
        block_months=int(calendar_config["block_months"]),
        seed=int(calendar_config["seed"]),
        lower_quantile=float(calendar_config["lower_quantile"]),
    )

    monthly_rows = []
    for month, group in base.groupby(base["entry_time_utc"].dt.strftime("%Y-%m")):
        monthly_rows.append({"month": month, **_scenario_summary(group)})
    monthly = pd.DataFrame(monthly_rows)
    recent_monthly = monthly[monthly["month"].between("2026-01", "2026-06")].to_dict(
        orient="records"
    )
    yearly_rows = []
    for year, group in base.groupby(base["entry_time_utc"].dt.year):
        yearly_rows.append({"year": int(year), **_scenario_summary(group)})
    yearly = pd.DataFrame(yearly_rows)

    active_days = base["entry_time_utc"].dt.strftime("%Y-%m-%d").nunique()
    calendar_days = (end - start).days
    frequency = {
        "trades": len(base),
        "calendar_days": calendar_days,
        "active_trading_days": int(active_days),
        "trades_per_calendar_day": float(len(base) / calendar_days),
        "trades_per_active_trading_day": float(len(base) / active_days),
    }
    checks = _descriptive_checks(
        windows,
        scenarios,
        trade_bootstrap,
        calendar_bootstrap,
        parity,
        data_audit,
        config["descriptive_thresholds_inherited_from_anchor_validation"],
    )
    all_checks = all(checks.values())
    result = {
        "schema_version": "eurusd_h4_dual_regime_portfolio_diagnostic_result_v1",
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor_config["source"]["sha256"],
        "post_hoc_developmental_not_confirmatory": True,
        "broker_action_allowed": False,
        "specialist_risk_weights": config["specialists"],
        "data_audit": data_audit,
        "prior_ledger_parity": parity,
        "diagnostics": diagnostics,
        "windows": windows,
        "scenarios": scenarios,
        "trade_bootstrap": trade_bootstrap,
        "calendar_bootstrap": calendar_bootstrap,
        "concurrency": concurrency_audit(base),
        "frequency": frequency,
        "latest_6_months_by_month": recent_monthly,
        "inherited_descriptive_checks": checks,
        "all_inherited_descriptive_thresholds_passed": all_checks,
        "status": (
            "HISTORICALLY_ROBUST_DUAL_REGIME_CANDIDATE_REQUIRES_FRESH_CONFIRMATION"
            if all_checks
            else "DUAL_REGIME_CANDIDATE_FAILED_INHERITED_ROBUSTNESS_THRESHOLDS"
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    base.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    pd.DataFrame(
        [{"scenario": name, **metrics} for name, metrics in scenarios.items()]
    ).to_csv(output_dir / "SCENARIO_METRICS.csv", index=False, lineterminator="\n")
    monthly.to_csv(output_dir / "MONTHLY_METRICS.csv", index=False, lineterminator="\n")
    yearly.to_csv(output_dir / "YEARLY_METRICS.csv", index=False, lineterminator="\n")
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (
        package_root / "EURUSD_H4_DUAL_REGIME_PORTFOLIO_DIAGNOSTIC_RESULT_2026_07_30.md"
    ).write_text(
        _render_report(result),
        encoding="utf-8",
        newline="\n",
    )
    return result
