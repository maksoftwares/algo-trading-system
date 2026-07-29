from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .neutral_h4_quiet_state_transfer import (
    PIP_VALUE_USD_001_LOT,
    PRICE_COLUMNS,
    add_h4_regimes,
    aggregate_h1,
    build_signal_mask,
    load_m5,
    profit_factor,
    sha256_file,
    simulate_short,
    summarize,
)


def audit_m5(frame: pd.DataFrame, source: dict[str, Any]) -> dict[str, Any]:
    timestamps = frame["timestamp"]
    expected_start = pd.Timestamp(source["start_utc"])
    expected_last = pd.Timestamp(source["end_exclusive_utc"]) - pd.Timedelta(minutes=5)
    deltas = timestamps.diff().dropna()
    finite = np.isfinite(frame[list(PRICE_COLUMNS)].to_numpy(dtype=float)).all()
    aligned = (
        timestamps.dt.second.eq(0)
        & timestamps.dt.microsecond.eq(0)
        & timestamps.dt.minute.mod(5).eq(0)
    ).all()
    delta_ns = deltas.astype("timedelta64[ns]").astype(np.int64)
    five_minutes_ns = int(pd.Timedelta(minutes=5).value)
    gap_multiples = bool((delta_ns % five_minutes_ns == 0).all())
    ohlc_valid: dict[str, bool] = {}
    for side in ("bid", "ask"):
        high = frame[f"{side}_high"]
        low = frame[f"{side}_low"]
        ohlc_valid[side] = bool(
            (high >= low).all()
            and (high >= frame[f"{side}_open"]).all()
            and (high >= frame[f"{side}_close"]).all()
            and (low <= frame[f"{side}_open"]).all()
            and (low <= frame[f"{side}_close"]).all()
        )
    ask_not_below_bid = bool(
        all(
            (frame[f"ask_{field}"] >= frame[f"bid_{field}"]).all()
            for field in ("open", "high", "low", "close")
        )
    )
    checks = {
        "expected_start": bool(timestamps.iloc[0] == expected_start),
        "expected_last_bar": bool(timestamps.iloc[-1] == expected_last),
        "expected_rows": bool(len(frame) == int(source["expected_rows"])),
        "unique_chronological_timestamps": bool(
            timestamps.is_monotonic_increasing and not timestamps.duplicated().any()
        ),
        "five_minute_timestamp_alignment": bool(aligned),
        "all_gaps_are_five_minute_multiples": gap_multiples,
        "finite_prices": bool(finite),
        "bid_ohlc_envelope": ohlc_valid["bid"],
        "ask_ohlc_envelope": ohlc_valid["ask"],
        "ask_not_below_bid_all_fields": ask_not_below_bid,
    }
    return {
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "rows": len(frame),
        "first_timestamp_utc": timestamps.iloc[0].isoformat(),
        "last_timestamp_utc": timestamps.iloc[-1].isoformat(),
        "gaps_larger_than_5_minutes": int((deltas > pd.Timedelta(minutes=5)).sum()),
        "largest_gap_hours": float(deltas.max() / pd.Timedelta(hours=1)),
    }


def _evaluation_subset(
    trades: pd.DataFrame, window: list[str] | tuple[str, str]
) -> pd.DataFrame:
    start, end = map(pd.Timestamp, window)
    return trades[
        (trades["entry_time_utc"] >= start) & (trades["entry_time_utc"] < end)
    ].copy()


def _scenario_summary(trades: pd.DataFrame) -> dict[str, Any]:
    work = trades.copy()
    work["stress_r"] = work["r"]
    result = summarize(work)
    result.pop("stress_profit_factor", None)
    result.pop("stress_net_r", None)
    return result


def apply_round_trip_cost(trades: pd.DataFrame, extra_pips: float) -> pd.DataFrame:
    result = trades.copy()
    result["extra_cost_pips"] = float(extra_pips)
    result["r"] = result["r"] - float(extra_pips) / result["stop_pips"]
    result["net_pips"] = result["net_pips"] - float(extra_pips)
    result["pnl_usd_001_lot"] = result["net_pips"] * PIP_VALUE_USD_001_LOT
    result["stress_r"] = result["r"]
    return result


def count_utc_rollovers(entry: pd.Timestamp, exit_time: pd.Timestamp) -> int:
    days = pd.date_range(
        entry.floor("D") - pd.Timedelta(days=1),
        exit_time.ceil("D") + pd.Timedelta(days=1),
        freq="D",
        tz="UTC",
    )
    rollovers = days + pd.Timedelta(hours=21)
    return int(((rollovers > entry) & (rollovers <= exit_time)).sum())


def apply_rollover_charge(
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
    result["r"] = result["r"] - result["extra_cost_pips"] / result["stop_pips"]
    result["net_pips"] = result["net_pips"] - result["extra_cost_pips"]
    result["pnl_usd_001_lot"] = result["net_pips"] * PIP_VALUE_USD_001_LOT
    result["stress_r"] = result["r"]
    return result


def circular_block_bootstrap(
    values: np.ndarray,
    *,
    samples: int,
    block_trades: int,
    seed: int,
    lower_quantile: float,
) -> dict[str, float | int | str]:
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) == 0:
        raise ValueError("Bootstrap requires a non-empty one-dimensional return vector")
    rng = np.random.default_rng(seed)
    n = len(values)
    blocks = math.ceil(n / block_trades)
    profit_factors = np.empty(samples, dtype=float)
    means = np.empty(samples, dtype=float)
    drawdowns = np.empty(samples, dtype=float)
    batch_size = 500
    offsets = np.arange(block_trades)
    written = 0
    while written < samples:
        batch = min(batch_size, samples - written)
        starts = rng.integers(0, n, size=(batch, blocks))
        indices = ((starts[:, :, None] + offsets) % n).reshape(batch, -1)[:, :n]
        sampled = values[indices]
        gains = np.where(sampled > 0.0, sampled, 0.0).sum(axis=1)
        losses = -np.where(sampled < 0.0, sampled, 0.0).sum(axis=1)
        profit_factors[written : written + batch] = np.divide(
            gains,
            losses,
            out=np.full(batch, np.inf),
            where=losses > 0.0,
        )
        means[written : written + batch] = sampled.mean(axis=1)
        equity = sampled.cumsum(axis=1)
        peaks = np.maximum.accumulate(np.maximum(equity, 0.0), axis=1)
        drawdowns[written : written + batch] = (peaks - equity).max(axis=1)
        written += batch

    def quantiles(vector: np.ndarray) -> dict[str, float]:
        low, median, high = np.quantile(
            vector, [lower_quantile, 0.5, 1.0 - lower_quantile]
        )
        return {"q05": float(low), "median": float(median), "q95": float(high)}

    return {
        "method": "CIRCULAR_MOVING_BLOCK",
        "samples": int(samples),
        "block_trades": int(block_trades),
        "seed": int(seed),
        "profit_factor": quantiles(profit_factors),
        "mean_r": quantiles(means),
        "maximum_drawdown_r": quantiles(drawdowns),
        "probability_profit_factor_lte_1": float(np.mean(profit_factors <= 1.0)),
        "probability_mean_r_lte_0": float(np.mean(means <= 0.0)),
    }


def rolling_windows(trades: pd.DataFrame, widths: list[int]) -> pd.DataFrame:
    ordered = trades.sort_values("exit_time_utc").reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for width in widths:
        for end in range(width, len(ordered) + 1):
            window = ordered.iloc[end - width : end]
            values = window["r"].to_numpy(dtype=float)
            rows.append(
                {
                    "window_trades": width,
                    "start_entry_time_utc": window["entry_time_utc"].iloc[0],
                    "end_exit_time_utc": window["exit_time_utc"].iloc[-1],
                    "profit_factor": profit_factor(values),
                    "net_r": float(values.sum()),
                }
            )
    return pd.DataFrame(rows)


def _parity_check(
    regenerated: pd.DataFrame,
    prior_ledger_path: Path,
    specialist_id: str,
    evaluation_window: list[str],
) -> dict[str, Any]:
    prior = pd.read_csv(prior_ledger_path)
    for column in ("signal_time_utc", "entry_time_utc", "exit_time_utc"):
        prior[column] = pd.to_datetime(prior[column], utc=True)
    prior = prior[prior["specialist_id"].eq(specialist_id)]
    prior = _evaluation_subset(prior, evaluation_window).reset_index(drop=True)
    current = _evaluation_subset(regenerated, evaluation_window).reset_index(drop=True)
    time_columns = ("signal_time_utc", "entry_time_utc", "exit_time_utc")
    numeric_columns = (
        "entry",
        "stop",
        "target",
        "exit",
        "entry_spread_pips",
        "stop_pips",
        "net_pips",
        "r",
        "stress_r",
        "pnl_usd_001_lot",
    )
    checks = {
        "row_count": len(current) == len(prior),
        "timestamps": all(
            current[c]
            .astype("datetime64[ns, UTC]")
            .equals(prior[c].astype("datetime64[ns, UTC]"))
            for c in time_columns
        ),
        "numeric_values": all(
            np.allclose(
                current[c].to_numpy(dtype=float),
                prior[c].to_numpy(dtype=float),
                rtol=0.0,
                atol=1e-12,
                equal_nan=True,
            )
            for c in numeric_columns
        ),
        "exit_reasons": current["exit_reason"].equals(prior["exit_reason"]),
    }
    return {
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "regenerated_rows": len(current),
        "prior_rows": len(prior),
    }


def evaluate_gates(
    base_windows: dict[str, dict[str, Any]],
    scenarios: dict[str, dict[str, Any]],
    bootstrap: dict[str, Any],
    parity: dict[str, Any],
    data_audit: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    full = base_windows["FULL_AUDIT"]
    latest = base_windows["LATEST_12_MONTHS"]
    chronology = (
        "EARLY_2017_2019",
        "MIDDLE_2020_2022H1",
        "LATE_2022H2_2024H1",
        "RECENT_2024H2_2026H1",
    )
    return {
        "data_integrity": bool(data_audit["all_checks_passed"]),
        "prior_ledger_parity": bool(parity["all_checks_passed"]),
        "minimum_full_trades": full["trades"] >= int(gates["minimum_full_trades"]),
        "full_profit_factor": full["profit_factor"]
        >= float(gates["minimum_full_profit_factor"]),
        "extra_0p5pip_profit_factor": scenarios["COST_PLUS_0P5_PIP"]["profit_factor"]
        >= float(gates["minimum_extra_0p5pip_profit_factor"]),
        "each_chronological_block_profit_factor": all(
            base_windows[name]["profit_factor"]
            > float(gates["minimum_each_chronological_block_profit_factor_exclusive"])
            for name in chronology
        ),
        "latest_12_month_profit_factor": latest["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "latest_12_month_net_r": latest["net_r"]
        > float(gates["minimum_latest_12_month_net_r_exclusive"]),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
        "positive_active_month_share": full["positive_active_month_share"]
        >= float(gates["minimum_positive_active_month_share"]),
        "entry_delay_5m_profit_factor": scenarios["ENTRY_DELAY_5M"]["profit_factor"]
        >= float(gates["minimum_5m_delay_profit_factor"]),
        "entry_delay_15m_profit_factor": scenarios["ENTRY_DELAY_15M"]["profit_factor"]
        >= float(gates["minimum_15m_delay_profit_factor"]),
        "extra_1p0pip_profit_factor": scenarios["COST_PLUS_1P0_PIP"]["profit_factor"]
        >= float(gates["minimum_extra_1p0pip_profit_factor"]),
        "rollover_stress_profit_factor": scenarios["ROLLOVER_0P5_PIP"]["profit_factor"]
        >= float(gates["minimum_rollover_stress_profit_factor"]),
        "bootstrap_base_pf_5pct": bootstrap["BASE"]["profit_factor"]["q05"]
        > float(gates["minimum_bootstrap_base_pf_5pct_exclusive"]),
        "bootstrap_base_mean_r_5pct": bootstrap["BASE"]["mean_r"]["q05"]
        > float(gates["minimum_bootstrap_base_mean_r_5pct_exclusive"]),
        "bootstrap_probability_pf_lte_1": bootstrap["BASE"][
            "probability_profit_factor_lte_1"
        ]
        <= float(gates["maximum_bootstrap_probability_pf_lte_1"]),
    }


def _render_report(result: dict[str, Any]) -> str:
    full = result["base_windows"]["FULL_AUDIT"]
    latest_12 = result["base_windows"]["LATEST_12_MONTHS"]
    latest_6 = result["base_windows"]["LATEST_6_MONTHS"]
    scenarios = result["scenarios"]
    failed = [name for name, passed in result["gate_results"].items() if not passed]
    failure_text = ", ".join(failed) if failed else "none"
    return f"""# EURUSD H4 chop anchor validation result

Status: **{result["status"]}**

This is a retrospective causal validation, not a pristine out-of-sample test and not permission to trade a broker account.

## Unchanged full-history anchor

- Trades: {full["trades"]}
- Win rate: {full["win_rate"]:.2%}
- Realized payoff: {full["realized_payoff_ratio"]:.3f}
- Profit factor: {full["profit_factor"]:.3f}
- Net: {full["net_r"]:.3f}R
- Maximum closed-trade drawdown: {full["maximum_drawdown_r"]:.3f}R
- PF after removing the best 5% of winners: {full["top_5pct_winners_removed_profit_factor"]:.3f}

## Recent periods

- Latest 12 months: {latest_12["trades"]} trades, PF {latest_12["profit_factor"]:.3f}, {latest_12["net_r"]:+.3f}R
- Latest 6 months: {latest_6["trades"]} trades, PF {latest_6["profit_factor"]:.3f}, {latest_6["net_r"]:+.3f}R

## Execution degradation

- +0.5 pip round trip: PF {scenarios["COST_PLUS_0P5_PIP"]["profit_factor"]:.3f}
- +1.0 pip round trip: PF {scenarios["COST_PLUS_1P0_PIP"]["profit_factor"]:.3f}
- 5-minute delayed entry: PF {scenarios["ENTRY_DELAY_5M"]["profit_factor"]:.3f}
- 15-minute delayed entry: PF {scenarios["ENTRY_DELAY_15M"]["profit_factor"]:.3f}
- 0.5 pip per 21:00 UTC rollover crossing: PF {scenarios["ROLLOVER_0P5_PIP"]["profit_factor"]:.3f}

## Sampling uncertainty

- Five-trade circular block bootstrap PF 5th percentile: {result["bootstrap"]["BASE"]["profit_factor"]["q05"]:.3f}
- Mean R/trade 5th percentile: {result["bootstrap"]["BASE"]["mean_r"]["q05"]:.4f}
- Estimated probability PF <= 1: {result["bootstrap"]["BASE"]["probability_profit_factor_lte_1"]:.2%}

Failed frozen gates: {failure_text}.

The historical PnL is real within this replay. Validation status depends on the frozen robustness and uncertainty gates; no failed gate is hidden or retuned.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    package_root = config_path.parent.parent
    anchor_config_path = package_root / config["anchor"]["config_path"]
    prior_ledger_path = package_root / config["anchor"]["prior_ledger_path"]
    if sha256_file(anchor_config_path) != config["anchor"]["config_sha256"]:
        raise RuntimeError("Anchor configuration checksum mismatch")
    if sha256_file(prior_ledger_path) != config["anchor"]["prior_ledger_sha256"]:
        raise RuntimeError("Prior anchor ledger checksum mismatch")
    anchor_config = json.loads(anchor_config_path.read_bytes())
    candidate = next(
        item
        for item in anchor_config["candidates"]
        if item["specialist_id"] == config["anchor"]["specialist_id"]
    )

    m5 = load_m5(anchor_config["source"])
    data_audit = audit_m5(m5, anchor_config["source"])
    h1 = aggregate_h1(m5)
    h1, h4 = add_h4_regimes(h1, anchor_config["classifier"])
    mask = build_signal_mask(h1, candidate)
    base_all, base_diagnostics = simulate_short(h1, m5, mask, candidate, anchor_config)
    base = _evaluation_subset(base_all, config["evaluation_window"])
    parity = _parity_check(
        base_all,
        prior_ledger_path,
        candidate["specialist_id"],
        config["evaluation_window"],
    )

    delayed: dict[int, tuple[pd.DataFrame, dict[str, int]]] = {}
    for delay in config["stress_scenarios"]["entry_delay_minutes"]:
        trades, diagnostics = simulate_short(
            h1,
            m5,
            mask,
            candidate,
            anchor_config,
            entry_delay_minutes=int(delay),
        )
        delayed[int(delay)] = (
            _evaluation_subset(trades, config["evaluation_window"]),
            diagnostics,
        )

    plus_half = apply_round_trip_cost(base, 0.5)
    plus_one = apply_round_trip_cost(base, 1.0)
    rollover = apply_rollover_charge(
        base,
        float(config["stress_scenarios"]["rollover_charge_pips_per_utc_21_crossing"]),
    )
    scenario_trades = {
        "BASE": base,
        "COST_PLUS_0P5_PIP": plus_half,
        "COST_PLUS_1P0_PIP": plus_one,
        "ENTRY_DELAY_5M": delayed[5][0],
        "ENTRY_DELAY_15M": delayed[15][0],
        "ROLLOVER_0P5_PIP": rollover,
    }
    scenarios = {
        name: _scenario_summary(trades) for name, trades in scenario_trades.items()
    }
    scenarios["ROLLOVER_0P5_PIP"]["charged_trade_count"] = int(
        (rollover["rollover_crossings"] > 0).sum()
    )
    scenarios["ROLLOVER_0P5_PIP"]["total_rollover_crossings"] = int(
        rollover["rollover_crossings"].sum()
    )

    base_windows = {
        name: summarize(_evaluation_subset(base, window))
        for name, window in config["chronological_blocks"].items()
    }
    rolling = rolling_windows(base, [int(x) for x in config["rolling_trade_windows"]])
    rolling_minima = {}
    for width, group in rolling.groupby("window_trades"):
        min_pf = group.loc[group["profit_factor"].idxmin()]
        min_net = group.loc[group["net_r"].idxmin()]
        rolling_minima[str(width)] = {
            "minimum_profit_factor": float(min_pf["profit_factor"]),
            "minimum_profit_factor_start_utc": pd.Timestamp(
                min_pf["start_entry_time_utc"]
            ).isoformat(),
            "minimum_profit_factor_end_utc": pd.Timestamp(
                min_pf["end_exit_time_utc"]
            ).isoformat(),
            "minimum_net_r": float(min_net["net_r"]),
            "minimum_net_r_start_utc": pd.Timestamp(
                min_net["start_entry_time_utc"]
            ).isoformat(),
            "minimum_net_r_end_utc": pd.Timestamp(
                min_net["end_exit_time_utc"]
            ).isoformat(),
        }

    yearly_rows = []
    for year, group in base.groupby(base["entry_time_utc"].dt.year):
        yearly_rows.append({"year": int(year), **_scenario_summary(group)})
    yearly = pd.DataFrame(yearly_rows)

    bootstrap_config = config["bootstrap"]
    bootstrap = {
        name: circular_block_bootstrap(
            trades["r"].to_numpy(dtype=float),
            samples=int(bootstrap_config["samples"]),
            block_trades=int(bootstrap_config["block_trades"]),
            seed=int(bootstrap_config["seed"]),
            lower_quantile=float(bootstrap_config["lower_quantile"]),
        )
        for name, trades in {
            "BASE": base,
            "COST_PLUS_0P5_PIP": plus_half,
        }.items()
    }
    gate_results = evaluate_gates(
        base_windows,
        scenarios,
        bootstrap,
        parity,
        data_audit,
        config["historical_validation_gates"],
    )
    passed = all(gate_results.values())
    result = {
        "schema_version": "eurusd_h4_chop_anchor_validation_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "anchor_config_sha256": config["anchor"]["config_sha256"],
        "source_sha256": anchor_config["source"]["sha256"],
        "strategy_parameters": candidate,
        "strategy_parameters_unchanged": True,
        "retrospective_causal_not_pristine_oos": True,
        "broker_action_allowed": False,
        "data_audit": data_audit,
        "prior_ledger_parity": parity,
        "base_diagnostics": base_diagnostics,
        "delay_diagnostics": {
            f"{delay}m": diagnostics for delay, (_, diagnostics) in delayed.items()
        },
        "h1_rows": len(h1),
        "h4_complete_rows": len(h4),
        "base_windows": base_windows,
        "scenarios": scenarios,
        "rolling_minima": rolling_minima,
        "bootstrap": bootstrap,
        "gate_results": gate_results,
        "all_historical_validation_gates_passed": passed,
        "status": (
            "HISTORICAL_ANCHOR_VALIDATED_PROSPECTIVE_CONFIRMATION_REQUIRED"
            if passed
            else "POSITIVE_HISTORICAL_ANCHOR_NOT_STATISTICALLY_VALIDATED"
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    base.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    pd.DataFrame(
        [{"scenario": name, **metrics} for name, metrics in scenarios.items()]
    ).to_csv(output_dir / "SCENARIO_METRICS.csv", index=False, lineterminator="\n")
    rolling.to_csv(output_dir / "ROLLING_WINDOWS.csv", index=False, lineterminator="\n")
    yearly.to_csv(output_dir / "YEARLY_METRICS.csv", index=False, lineterminator="\n")
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (package_root / "EURUSD_H4_CHOP_ANCHOR_VALIDATION_RESULT_2026_07_30.md").write_text(
        _render_report(result),
        encoding="utf-8",
        newline="\n",
    )
    return result
