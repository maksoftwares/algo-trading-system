from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .h4_chop_anchor_validation import (
    _evaluation_subset,
    _scenario_summary,
    audit_m5,
    circular_block_bootstrap,
)
from .h4_confirmation_uniform_risk import scale_uniformly
from .h4_dual_regime_portfolio_diagnostic import (
    apply_portfolio_weight,
    apply_weighted_cost,
    circular_calendar_month_bootstrap,
    concurrency_audit,
)
from .h4_intrahour_frequency_ladder import (
    aggregate_resolution_bars,
    build_resolution_mask,
    simulate_resolution,
)
from .h4_session_frequency_expansion import apply_causal_risk_cap
from .neutral_h4_quiet_state_transfer import (
    add_h4_regimes,
    aggregate_h1,
    load_m5,
    sha256_file,
)
from .session_health_specialist_portfolio import (
    CHRONOLOGY,
    _fx_days,
    _gate_results,
    _latest_months,
    _windows,
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def build_fixed_followthrough_mask(
    bars: pd.DataFrame,
    candidate: dict[str, Any],
    offset_bars: int,
    *,
    resolution_minutes: int = 15,
) -> pd.Series:
    """Select a fixed close after the day's first qualified range break.

    The first break owns the original body threshold. A later horizon must be
    complete, remain in the same causal H4 regime, remain inside the original
    decision window, and still close beyond the same overnight boundary.
    """
    if int(offset_bars) <= 0:
        raise ValueError("Follow-through offset must be positive")
    date = bars["timestamp"].dt.strftime("%Y-%m-%d")
    minute = bars["timestamp"].dt.hour * 60 + bars["timestamp"].dt.minute
    reference = minute.ge(0) & minute.lt(360) & bars["complete_bar"]
    reference_low = (
        bars["mid_low"].where(reference).groupby(date).transform("min")
    )
    reference_count = reference.groupby(date).transform("sum")
    first_break_raw = (
        minute.ge(360)
        & minute.lt(600)
        & reference_count.eq(360 // int(resolution_minutes))
        & bars["complete_bar"]
        & (
            bars["body_fraction"]
            >= float(candidate["body_fraction_minimum"])
        )
        & bars["regime"].eq(candidate["owned_regime"])
        & bars["atr"].notna()
        & (bars["mid_close"] < reference_low)
    ).fillna(False)
    first_break = first_break_raw & first_break_raw.groupby(date).cumsum().eq(1)
    selected = pd.Series(False, index=bars.index)
    for position in first_break.to_numpy().nonzero()[0]:
        confirmation = position + int(offset_bars)
        if confirmation >= len(bars):
            continue
        first_time = pd.Timestamp(bars["timestamp"].iloc[position])
        timestamp = pd.Timestamp(bars["timestamp"].iloc[confirmation])
        if timestamp - first_time != pd.Timedelta(
            minutes=int(resolution_minutes) * int(offset_bars)
        ):
            continue
        if timestamp.strftime("%Y-%m-%d") != first_time.strftime("%Y-%m-%d"):
            continue
        if timestamp.hour * 60 + timestamp.minute >= 600:
            continue
        if (
            not bool(bars["complete_bar"].iloc[confirmation])
            or bars["regime"].iloc[confirmation]
            != candidate["owned_regime"]
            or not math.isfinite(float(bars["atr"].iloc[confirmation]))
        ):
            continue
        if float(bars["mid_close"].iloc[confirmation]) < float(
            reference_low.iloc[position]
        ):
            selected.iloc[confirmation] = True
    return selected


def component_audit(
    trades: pd.DataFrame,
    reporting_windows: dict[str, list[str]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    windows = _windows(trades, reporting_windows)
    stressed = _scenario_summary(apply_weighted_cost(trades, 0.5))
    full = windows["FULL_AUDIT"]
    checks = {
        "minimum_trades": full["trades"]
        >= int(contract["minimum_trades"]),
        "full_profit_factor": full["profit_factor"]
        > float(contract["minimum_full_profit_factor_exclusive"]),
        "stressed_profit_factor": stressed["profit_factor"]
        > float(contract["minimum_stressed_profit_factor_exclusive"]),
        "each_chronological_block_profit_factor": all(
            windows[name]["profit_factor"]
            > float(
                contract[
                    "minimum_each_chronological_block_profit_factor_exclusive"
                ]
            )
            for name in CHRONOLOGY
        ),
        "latest_12_month_profit_factor": windows["LATEST_12_MONTHS"][
            "profit_factor"
        ]
        > float(
            contract[
                "minimum_latest_12_month_profit_factor_exclusive"
            ]
        ),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(
            contract[
                "minimum_top_5pct_winners_removed_profit_factor"
            ]
        ),
    }
    return {
        "windows": windows,
        "extra_0p5pip": stressed,
        "checks": checks,
        "qualified": all(checks.values()),
    }


def deterministic_uniform_scale(
    unscaled: pd.DataFrame,
    target_maximum_concurrent_risk: float,
    target_maximum_drawdown_r: float,
) -> tuple[float, dict[str, float]]:
    unscaled_concurrency = concurrency_audit(unscaled)
    maximum_risk = float(
        unscaled_concurrency["maximum_concurrent_initial_risk_units"]
    )
    unscaled_drawdown = float(
        _scenario_summary(unscaled)["maximum_drawdown_r"]
    )
    risk_scale = (
        1.0
        if maximum_risk <= 0.0
        else float(target_maximum_concurrent_risk) / maximum_risk
    )
    drawdown_scale = (
        1.0
        if unscaled_drawdown <= 0.0
        else float(target_maximum_drawdown_r) / unscaled_drawdown
    )
    scale = min(1.0, risk_scale, drawdown_scale)
    return scale, {
        "unscaled_maximum_concurrent_initial_risk_units": maximum_risk,
        "unscaled_maximum_drawdown_r": unscaled_drawdown,
        "risk_scale_ceiling": risk_scale,
        "drawdown_scale_ceiling": drawdown_scale,
    }


def _render_report(result: dict[str, Any]) -> str:
    full = result["windows"]["FULL_AUDIT"]
    recent = result["windows"]["RECENT_2024H2_2026H1"]
    latest = result["windows"]["LATEST_6_MONTHS"]
    failed = [
        name for name, passed in result["gate_results"].items() if not passed
    ]
    components = "\n".join(
        f"| {name} | {audit['windows']['FULL_AUDIT']['trades']} | "
        f"{audit['windows']['FULL_AUDIT']['profit_factor']:.3f} | "
        f"{audit['extra_0p5pip']['profit_factor']:.3f} | "
        f"{audit['qualified']} |"
        for name, audit in result["added_component_audits"].items()
    )
    return f"""# EURUSD H4 frequency-completion portfolio result

Status: **{result["status"]}**

| Window | Trades | Win rate | Payoff | PF | Net portfolio R |
|---|---:|---:|---:|---:|---:|
| Full 2017-2026 | {full["trades"]} | {full["win_rate"]:.2%} | {full["realized_payoff_ratio"]:.3f} | {full["profit_factor"]:.3f} | {full["net_r"]:+.3f} |
| Recent 2024H2-2026H1 | {recent["trades"]} | {recent["win_rate"]:.2%} | {recent["realized_payoff_ratio"]:.3f} | {recent["profit_factor"]:.3f} | {recent["net_r"]:+.3f} |
| Latest six months | {latest["trades"]} | {latest["win_rate"]:.2%} | {latest["realized_payoff_ratio"]:.3f} | {latest["profit_factor"]:.3f} | {latest["net_r"]:+.3f} |

Frequency: {result["frequency"]["trades_per_fx_day"]:.3f} trades per FX day,
with {result["frequency"]["active_trade_days"]} active days and
{result["frequency"]["active_day_share"]:.2%} calendar coverage.

| Added component | Trades | PF | +0.5-pip PF | Standalone qualified |
|---|---:|---:|---:|---|
{components}

Uniform post-admission risk scale: {result["uniform_risk_scale"]:.4f}.
Maximum concurrent initial risk: {result["concurrency"]["maximum_concurrent_initial_risk_units"]:.3f}R.
Maximum drawdown: {full["maximum_drawdown_r"]:.3f}R.
0.5-pip stressed PF: {result["scenarios"]["COST_PLUS_0P5_PIP"]["profit_factor"]:.3f}.
1.0-pip stressed PF: {result["scenarios"]["COST_PLUS_1P0_PIP"]["profit_factor"]:.3f}.
Best-5%-removed PF: {full["top_5pct_winners_removed_profit_factor"]:.3f}.
Failed gates: {", ".join(failed) if failed else "none"}.

Adaptive historical research only; no broker orders are authorized.
"""


def run(
    config_path: Path, output_dir: Path
) -> tuple[dict[str, Any], pd.DataFrame]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    root = config_path.parent.parent
    anchor_path = root / config["anchor_config"]["path"]
    parent_path = root / config["protected_parent_ledger"]["path"]
    for path, expected in (
        (anchor_path, config["anchor_config"]["sha256"]),
        (parent_path, config["protected_parent_ledger"]["sha256"]),
    ):
        if sha256_file(path) != expected:
            raise RuntimeError(f"Checksum mismatch: {path}")

    anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
    m5 = load_m5(anchor["source"])
    data_audit = audit_m5(m5, anchor["source"])
    h1 = aggregate_h1(m5)
    h1, h4 = add_h4_regimes(h1, anchor["classifier"])
    m15 = aggregate_resolution_bars(m5, h1, h4, 15)
    m30 = aggregate_resolution_bars(m5, h1, h4, 30)
    templates = {
        item["owned_regime"]: item for item in anchor["candidates"]
    }

    parent = pd.read_csv(
        parent_path,
        parse_dates=[
            "signal_time_utc",
            "entry_time_utc",
            "exit_time_utc",
        ],
    )
    if len(parent) != int(
        config["protected_parent_ledger"]["expected_rows"]
    ):
        raise RuntimeError("Unexpected protected parent row count")
    candidate_pieces = [parent]
    audits: dict[str, Any] = {}
    added_counts: dict[str, int] = {}

    for regime, offsets in config["followthrough_offsets_bars"].items():
        for offset in offsets:
            candidate = dict(templates[regime])
            mask = build_fixed_followthrough_mask(
                m15, candidate, int(offset)
            )
            trades, _ = simulate_resolution(
                m15, m5, mask, candidate, anchor, 15, 0
            )
            trades = _evaluation_subset(
                trades, config["evaluation_window"]
            )
            unweighted = apply_portfolio_weight(trades, 1.0)
            name = f"M15_FOLLOW_{int(offset)}_{regime.upper()}"
            audits[name] = component_audit(
                unweighted,
                config["reporting_windows"],
                config["added_component_admission"],
            )
            if not audits[name]["qualified"]:
                raise RuntimeError(
                    f"Frozen follow-through component failed: {name}"
                )
            weighted = apply_portfolio_weight(
                trades,
                float(config["added_component_risk_weight"]),
            )
            weighted["portfolio_sleeve"] = name
            candidate_pieces.append(weighted)
            added_counts[name] = len(weighted)

    m30_pieces = []
    for regime, candidate in templates.items():
        mask = build_resolution_mask(m30, candidate, 30)
        trades, _ = simulate_resolution(
            m30, m5, mask, candidate, anchor, 30, 0
        )
        trades = _evaluation_subset(trades, config["evaluation_window"])
        weighted = apply_portfolio_weight(
            trades, float(config["m30_risk_weights"][regime])
        )
        weighted["portfolio_sleeve"] = f"M30_FIRST_BREAK_{regime.upper()}"
        m30_pieces.append(weighted)
        added_counts[f"M30_FIRST_BREAK_{regime.upper()}"] = len(weighted)
    m30_family = pd.concat(m30_pieces, ignore_index=True, sort=False)
    audits["M30_FIRST_BREAK_FAMILY"] = component_audit(
        m30_family,
        config["reporting_windows"],
        config["added_component_admission"],
    )
    if not audits["M30_FIRST_BREAK_FAMILY"]["qualified"]:
        raise RuntimeError("Frozen M30 first-break family failed")
    candidate_pieces.extend(m30_pieces)

    candidates = pd.concat(candidate_pieces, ignore_index=True, sort=False)
    priority = list(parent["portfolio_sleeve"].drop_duplicates())
    priority.extend(
        name
        for name in config["fixed_added_priority"]
        if name not in priority
    )
    admitted, cap = apply_causal_risk_cap(
        candidates,
        maximum_risk=float(
            config["candidate_risk_cap"][
                "maximum_concurrent_initial_risk_units"
            ]
        ),
        priority=priority,
    )
    scale, scale_audit = deterministic_uniform_scale(
        admitted,
        float(
            config["final_risk_targets"][
                "maximum_concurrent_initial_risk_units"
            ]
        ),
        float(config["final_risk_targets"]["maximum_drawdown_r"]),
    )
    portfolio = scale_uniformly(admitted, scale)

    windows = _windows(portfolio, config["reporting_windows"])
    scenarios = {
        "COST_PLUS_0P5_PIP": _scenario_summary(
            apply_weighted_cost(portfolio, 0.5)
        ),
        "COST_PLUS_1P0_PIP": _scenario_summary(
            apply_weighted_cost(portfolio, 1.0)
        ),
    }
    start, end = map(pd.Timestamp, config["evaluation_window"])
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
    active_days = int(
        portfolio["entry_time_utc"].dt.strftime("%Y-%m-%d").nunique()
    )
    frequency = {
        "trades": len(portfolio),
        "fx_days": fx_days,
        "trades_per_fx_day": len(portfolio) / fx_days,
        "active_trade_days": active_days,
        "active_day_share": active_days / fx_days,
        "trades_per_active_day": len(portfolio) / active_days,
    }
    gates = _gate_results(
        windows,
        scenarios,
        trade_bootstrap,
        calendar_bootstrap,
        frequency,
        config["admission"],
    )
    gates["all_added_components_standalone_qualified"] = all(
        audit["qualified"] for audit in audits.values()
    )
    gates["minimum_executable_lot_equivalent"] = (
        float(portfolio["portfolio_risk_weight"].min())
        * float(config["execution"]["reference_full_risk_lot"])
        >= float(config["execution"]["minimum_broker_lot"])
    )
    status = (
        "BACKTEST_FREQUENCY_AND_EDGE_GATES_PASSED"
        if all(gates.values())
        else "REJECTED_H4_FREQUENCY_COMPLETION_PORTFOLIO"
    )
    result = {
        "schema_version": "eurusd_h4_frequency_completion_result_v1",
        "status": status,
        "demo_ready": False,
        "live_ready": False,
        "broker_action_allowed": False,
        "adaptive_historical_development_not_pristine_oos": True,
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "data_audit": data_audit,
        "parent_trade_count": len(parent),
        "added_candidate_counts": added_counts,
        "added_component_audits": audits,
        "candidate_risk_cap": cap,
        "uniform_risk_scale": scale,
        "uniform_risk_scale_audit": scale_audit,
        "concurrency": concurrency_audit(portfolio),
        "frequency": frequency,
        "windows": windows,
        "scenarios": scenarios,
        "trade_bootstrap": trade_bootstrap,
        "calendar_bootstrap": calendar_bootstrap,
        "latest_6_months_by_month": _latest_months(portfolio),
        "gate_results": gates,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    portfolio.to_csv(output_dir / "TRADES.csv", index=False)
    (output_dir / "RESULT.json").write_text(
        json.dumps(_json_safe(result), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "RESULT.md").write_text(
        _render_report(result), encoding="utf-8", newline="\n"
    )
    return result, portfolio
