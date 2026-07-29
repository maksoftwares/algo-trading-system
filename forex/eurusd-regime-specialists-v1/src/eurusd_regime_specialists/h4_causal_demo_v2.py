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
from .h4_dual_regime_portfolio_diagnostic import (
    apply_portfolio_weight,
    apply_weighted_cost,
    apply_weighted_rollover,
    circular_calendar_month_bootstrap,
    concurrency_audit,
)
from .h4_intrahour_frequency_ladder import (
    _period_metrics,
    aggregate_resolution_bars,
    simulate_resolution,
)
from .h4_session_frequency_expansion import (
    CHRONOLOGY,
    _fx_days,
    _windows,
    apply_causal_risk_cap,
)
from .h4_unused_regime_frequency_expansion import simulate_long
from .neutral_h4_quiet_state_transfer import (
    add_h4_regimes,
    aggregate_h1,
    build_signal_mask,
    load_m5,
    sha256_file,
    simulate_short,
)


def build_causal_confirmation_mask(
    bars: pd.DataFrame,
    candidate: dict[str, Any],
    side: str,
    mode: str,
    *,
    resolution_minutes: int = 15,
    retest_bars: int = 4,
) -> pd.Series:
    if side not in {"LONG", "SHORT"}:
        raise ValueError(f"Unsupported side: {side}")
    if mode not in {"IMMEDIATE", "NEXT_CLOSE", "RETEST_REJECT"}:
        raise ValueError(f"Unsupported confirmation mode: {mode}")
    date = bars["timestamp"].dt.strftime("%Y-%m-%d")
    minute = bars["timestamp"].dt.hour * 60 + bars["timestamp"].dt.minute
    reference = minute.ge(0) & minute.lt(360) & bars["complete_bar"]
    ref_high = bars["mid_high"].where(reference).groupby(date).transform("max")
    ref_low = bars["mid_low"].where(reference).groupby(date).transform("min")
    ref_count = reference.groupby(date).transform("sum")
    decision = minute.ge(360) & minute.lt(600)
    common = (
        decision
        & ref_count.eq(360 // resolution_minutes)
        & bars["complete_bar"]
        & (bars["body_fraction"] >= float(candidate["body_fraction_minimum"]))
        & bars["regime"].eq(candidate["owned_regime"])
        & bars["atr"].notna()
    ).fillna(False)
    boundary = ref_high if side == "LONG" else ref_low
    beyond = (
        bars["mid_close"] > boundary
        if side == "LONG"
        else bars["mid_close"] < boundary
    )
    raw = (common & beyond).fillna(False)
    first_break = raw & raw.groupby(date).cumsum().eq(1)
    if mode == "IMMEDIATE":
        return first_break

    selected = pd.Series(False, index=bars.index)
    for position in first_break.to_numpy().nonzero()[0]:
        first_time = pd.Timestamp(bars["timestamp"].iloc[position])
        if mode == "NEXT_CLOSE":
            candidates = range(position + 1, position + 2)
        else:
            candidates = range(position + 1, position + 1 + int(retest_bars))
        for confirmation in candidates:
            if confirmation >= len(bars):
                break
            timestamp = pd.Timestamp(bars["timestamp"].iloc[confirmation])
            if timestamp - first_time != pd.Timedelta(
                minutes=resolution_minutes * (confirmation - position)
            ):
                break
            if timestamp.strftime("%Y-%m-%d") != first_time.strftime("%Y-%m-%d"):
                break
            confirmation_minute = timestamp.hour * 60 + timestamp.minute
            if confirmation_minute >= 600:
                break
            if (
                not bool(bars["complete_bar"].iloc[confirmation])
                or bars["regime"].iloc[confirmation] != candidate["owned_regime"]
                or not math.isfinite(float(bars["atr"].iloc[confirmation]))
            ):
                if mode == "NEXT_CLOSE":
                    break
                continue
            close = float(bars["mid_close"].iloc[confirmation])
            limit = float(boundary.iloc[position])
            closes_beyond = close > limit if side == "LONG" else close < limit
            if mode == "NEXT_CLOSE":
                if closes_beyond:
                    selected.iloc[confirmation] = True
                break
            touched = (
                float(bars["mid_low"].iloc[confirmation]) <= limit
                if side == "LONG"
                else float(bars["mid_high"].iloc[confirmation]) >= limit
            )
            if touched and closes_beyond:
                selected.iloc[confirmation] = True
                break
    return selected


def simulate_resolution_long(
    bars: pd.DataFrame,
    m5: pd.DataFrame,
    mask: pd.Series,
    candidate: dict[str, Any],
    anchor: dict[str, Any],
    resolution_minutes: int,
    delay: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    simulation_bars = bars.copy()
    offset = 60 - int(resolution_minutes)
    simulation_bars["timestamp"] = simulation_bars["timestamp"] - pd.Timedelta(
        minutes=offset
    )
    trades, diagnostics = simulate_long(
        simulation_bars,
        m5,
        mask,
        candidate,
        anchor,
        entry_delay_minutes=int(delay),
    )
    if not trades.empty:
        trades["signal_time_utc"] = trades["signal_time_utc"] + pd.Timedelta(
            minutes=offset
        )
        trades["signal_resolution_minutes"] = int(resolution_minutes)
    return trades, diagnostics


def _variant_mode(variant: str) -> str:
    if variant.endswith("IMMEDIATE"):
        return "IMMEDIATE"
    if variant.endswith("NEXT_CLOSE"):
        return "NEXT_CLOSE"
    if variant.endswith("RETEST_REJECT_4"):
        return "RETEST_REJECT"
    raise ValueError(f"Unknown intrahour variant: {variant}")


def simulate_variant(
    variant: str,
    side: str,
    candidate: dict[str, Any],
    h1: pd.DataFrame,
    bars: pd.DataFrame,
    m5: pd.DataFrame,
    anchor: dict[str, Any],
    delay: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    candidate = dict(candidate)
    candidate["direction"] = side
    candidate["specialist_id"] = (
        f"{variant}_{side}_{candidate['owned_regime'].upper()}"
    )
    if variant == "H60_PROTECTED":
        if side != "SHORT":
            raise ValueError("The protected H60 control is short-only")
        trades, diagnostics = simulate_short(
            h1,
            m5,
            build_signal_mask(h1, candidate),
            candidate,
            anchor,
            entry_delay_minutes=int(delay),
        )
        if not trades.empty:
            trades["signal_resolution_minutes"] = 60
        return trades, diagnostics
    mode = _variant_mode(variant)
    mask = build_causal_confirmation_mask(bars, candidate, side, mode)
    if side == "SHORT":
        return simulate_resolution(
            bars, m5, mask, candidate, anchor, 15, int(delay)
        )
    return simulate_resolution_long(
        bars, m5, mask, candidate, anchor, 15, int(delay)
    )


def evaluate_component(
    trades: pd.DataFrame,
    reporting_windows: dict[str, list[str]],
    gates: dict[str, Any],
) -> dict[str, Any]:
    weighted = apply_portfolio_weight(trades, 1.0)
    windows = _windows(weighted, reporting_windows)
    stress = _scenario_summary(apply_weighted_cost(weighted, 0.5))
    full = windows["FULL_AUDIT"]
    latest = windows["LATEST_12_MONTHS"]
    checks = {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "full_profit_factor": full["profit_factor"]
        > float(gates["minimum_full_profit_factor_exclusive"]),
        "extra_0p5pip_profit_factor": stress["profit_factor"]
        >= float(gates["minimum_extra_0p5pip_profit_factor"]),
        "each_chronological_block_profit_factor": all(
            windows[name]["profit_factor"]
            > float(
                gates[
                    "minimum_each_chronological_block_profit_factor_exclusive"
                ]
            )
            for name in CHRONOLOGY
        ),
        "latest_12_month_profit_factor": latest["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "latest_12_month_net_r": latest["net_r"]
        > float(gates["minimum_latest_12_month_net_r_exclusive"]),
        "positive_active_month_share": full["positive_active_month_share"]
        >= float(gates["minimum_positive_active_month_share"]),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
    }
    return {
        "windows": windows,
        "extra_0p5pip": stress,
        "checks": checks,
        "admitted": all(checks.values()),
    }


def evaluate_demo_gates(
    windows: dict[str, dict[str, Any]],
    scenarios: dict[str, dict[str, Any]],
    frequency: dict[str, Any],
    trade_bootstrap: dict[str, Any],
    calendar_bootstrap: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    full = windows["FULL_AUDIT"]
    return {
        "minimum_trades_per_fx_day": frequency["trades_per_fx_day"]
        >= float(gates["minimum_trades_per_fx_day"]),
        "full_profit_factor": full["profit_factor"]
        >= float(gates["minimum_full_profit_factor"]),
        "extra_0p5pip_profit_factor": scenarios["COST_PLUS_0P5_PIP"][
            "profit_factor"
        ]
        >= float(gates["minimum_extra_0p5pip_profit_factor"]),
        "extra_1p0pip_profit_factor": scenarios["COST_PLUS_1P0_PIP"][
            "profit_factor"
        ]
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
        "latest_12_month_profit_factor": windows["LATEST_12_MONTHS"][
            "profit_factor"
        ]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "latest_12_month_net_r": windows["LATEST_12_MONTHS"]["net_r"]
        > float(gates["minimum_latest_12_month_net_r_exclusive"]),
        "latest_6_month_net_r": windows["LATEST_6_MONTHS"]["net_r"]
        > float(gates["minimum_latest_6_month_net_r_exclusive"]),
        "win_rate": float(gates["minimum_win_rate_inclusive"])
        <= full["win_rate"]
        <= float(gates["maximum_win_rate_inclusive"]),
        "realized_payoff_ratio": float(
            gates["minimum_realized_payoff_ratio_inclusive"]
        )
        <= full["realized_payoff_ratio"]
        <= float(gates["maximum_realized_payoff_ratio_inclusive"]),
        "positive_active_month_share": full["positive_active_month_share"]
        >= float(gates["minimum_positive_active_month_share"]),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
        "entry_delay_5m_profit_factor": scenarios["ENTRY_DELAY_5M"]["profit_factor"]
        >= float(gates["minimum_5m_delay_profit_factor"]),
        "entry_delay_15m_profit_factor": scenarios["ENTRY_DELAY_15M"][
            "profit_factor"
        ]
        >= float(gates["minimum_15m_delay_profit_factor"]),
        "trade_bootstrap_pf_5pct": trade_bootstrap["profit_factor"]["q05"]
        > float(gates["minimum_trade_bootstrap_pf_5pct_exclusive"]),
        "trade_bootstrap_probability_pf_lte_1": trade_bootstrap[
            "probability_profit_factor_lte_1"
        ]
        <= float(gates["maximum_trade_bootstrap_probability_pf_lte_1"]),
        "calendar_bootstrap_pf_5pct": calendar_bootstrap["profit_factor"]["q05"]
        > float(gates["minimum_calendar_bootstrap_pf_5pct_exclusive"]),
        "calendar_bootstrap_probability_pf_lte_1": calendar_bootstrap[
            "probability_profit_factor_lte_1"
        ]
        <= float(gates["maximum_calendar_bootstrap_probability_pf_lte_1"]),
    }


def _render_report(result: dict[str, Any]) -> str:
    variant_rows = []
    for name, item in result["variants"].items():
        full = item["evaluation"]["windows"]["FULL_AUDIT"]
        variant_rows.append(
            f"| {name} | {full['trades']} | {full['win_rate']:.1%} | "
            f"{full['realized_payoff_ratio']:.3f} | {full['profit_factor']:.3f} | "
            f"{item['evaluation']['extra_0p5pip']['profit_factor']:.3f} | "
            f"{item['evaluation']['windows']['LATEST_12_MONTHS']['profit_factor']:.3f} | "
            f"{item['evaluation']['admitted']} |"
        )
    full = result["portfolio"]["windows"]["FULL_AUDIT"]
    latest = result["portfolio"]["windows"]["LATEST_6_MONTHS"]
    failed = [name for name, passed in result["portfolio"]["gates"].items() if not passed]
    month_rows = "\n".join(
        f"| {row['period']} | {row['trades']} | {row['win_rate']:.1%} | "
        f"{'infinite' if row['profit_factor_is_infinite'] else format(row['profit_factor'], '.3f')} | "
        f"{row['net_r']:+.3f} | ${row['pnl_usd_001_lot']:+.2f} |"
        for row in result["portfolio"]["latest_6_months_by_month"]
    )
    return f"""# EURUSD causal demo V2 historical result

Status: **{result["status"]}**

This is inspected historical development. A passing result would still require
Python/MT5 parity and prospective demo observation before promotion.

| Variant | Trades | Win rate | Payoff | PF | +0.5 pip PF | Latest-12M PF | Admitted |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(variant_rows)}

Selected components: {", ".join(result["selected_components"]) or "none"}.

Portfolio: {full["trades"]} trades, {result["portfolio"]["frequency"]["trades_per_fx_day"]:.3f}
trades/FX day, {full["win_rate"]:.1%} wins, {full["realized_payoff_ratio"]:.3f}
payoff, PF {full["profit_factor"]:.3f}, {full["net_r"]:+.3f}R,
${full["pnl_usd_001_lot"]:+.2f} at fixed 0.01 lot, and
{full["maximum_drawdown_r"]:.3f}R closed-trade drawdown.

Latest six months: {latest["trades"]} trades, PF {latest["profit_factor"]:.3f},
{latest["net_r"]:+.3f}R, ${latest["pnl_usd_001_lot"]:+.2f}.

Failed historical demo gates: {", ".join(failed) if failed else "none"}.

## Latest six calendar months

| Month | Trades | Win rate | PF | Net R | Fixed 0.01 lot |
|---|---:|---:|---:|---:|---:|
{month_rows}
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    package_root = config_path.parent.parent
    anchor_path = package_root / config["anchor_config"]["path"]
    if sha256_file(anchor_path) != config["anchor_config"]["sha256"]:
        raise RuntimeError("Anchor configuration checksum mismatch")
    anchor = json.loads(anchor_path.read_bytes())
    m5 = load_m5(anchor["source"])
    data_audit = audit_m5(m5, anchor["source"])
    h1 = aggregate_h1(m5)
    h1, h4 = add_h4_regimes(h1, anchor["classifier"])
    bars = aggregate_resolution_bars(m5, h1, h4, 15)
    templates = {item["owned_regime"]: item for item in anchor["candidates"]}
    delays = (0, *config["stress_scenarios"]["entry_delay_minutes"])
    raw_ledgers: dict[tuple[str, str, str, int], pd.DataFrame] = {}
    variants: dict[str, Any] = {}

    for side, ladder in config["variant_ladders"].items():
        for regime, template in templates.items():
            for variant in ladder:
                trades, diagnostics = simulate_variant(
                    variant,
                    side,
                    template,
                    h1,
                    bars,
                    m5,
                    anchor,
                    0,
                )
                trades = _evaluation_subset(trades, config["evaluation_window"])
                key = f"{side}_{regime.upper()}_{variant}"
                raw_ledgers[(side, regime, variant, 0)] = trades
                variants[key] = {
                    "side": side,
                    "regime": regime,
                    "variant": variant,
                    "diagnostics": diagnostics,
                    "evaluation": evaluate_component(
                        trades,
                        config["reporting_windows"],
                        config["component_admission"],
                    ),
                }

    selected: list[tuple[str, str, str]] = []
    for side, ladder in config["variant_ladders"].items():
        for regime in templates:
            admitted = [
                variant
                for variant in ladder
                if variants[
                    f"{side}_{regime.upper()}_{variant}"
                ]["evaluation"]["admitted"]
            ]
            if admitted:
                order = {name: index for index, name in enumerate(ladder)}
                chosen = max(
                    admitted,
                    key=lambda name: (
                        len(raw_ledgers[(side, regime, name, 0)]),
                        -order[name],
                    ),
                )
                selected.append((side, regime, chosen))

    for side, regime, variant in selected:
        for delay in delays[1:]:
            trades, _ = simulate_variant(
                variant,
                side,
                templates[regime],
                h1,
                bars,
                m5,
                anchor,
                int(delay),
            )
            raw_ledgers[(side, regime, variant, int(delay))] = _evaluation_subset(
                trades, config["evaluation_window"]
            )

    def assemble(delay: int) -> tuple[pd.DataFrame, dict[str, Any]]:
        pieces = []
        for side, regime, variant in selected:
            piece = apply_portfolio_weight(
                raw_ledgers[(side, regime, variant, delay)], 1.0
            )
            piece["portfolio_sleeve"] = f"{side}_{regime.upper()}"
            pieces.append(piece)
        if not pieces:
            return pd.DataFrame(), {"accepted": 0, "risk_cap_rejections": 0}
        return apply_causal_risk_cap(
            pd.concat(pieces, ignore_index=True),
            maximum_risk=float(
                config["portfolio_risk"]["maximum_concurrent_initial_risk_units"]
            ),
            priority=config["portfolio_risk"]["fixed_priority"],
        )

    ledgers = {}
    risk_caps = {}
    for delay in delays:
        ledgers[int(delay)], risk_caps[f"{delay}m"] = assemble(int(delay))
    portfolio = ledgers[0]
    if portfolio.empty:
        raise RuntimeError("No standalone component passed the frozen admission gates")
    plus_half = apply_weighted_cost(portfolio, 0.5)
    plus_one = apply_weighted_cost(portfolio, 1.0)
    rollover = apply_weighted_rollover(
        portfolio,
        float(config["stress_scenarios"]["rollover_charge_pips_per_utc_21_crossing"]),
    )
    scenarios = {
        "BASE": _scenario_summary(portfolio),
        "COST_PLUS_0P5_PIP": _scenario_summary(plus_half),
        "COST_PLUS_1P0_PIP": _scenario_summary(plus_one),
        "ENTRY_DELAY_5M": _scenario_summary(ledgers[5]),
        "ENTRY_DELAY_15M": _scenario_summary(ledgers[15]),
        "ROLLOVER_0P5_PIP": _scenario_summary(rollover),
    }
    windows = _windows(portfolio, config["reporting_windows"])
    start, end = map(pd.Timestamp, config["evaluation_window"])
    fx_days = _fx_days(m5, start, end)
    active_days = int(
        portfolio["entry_time_utc"].dt.strftime("%Y-%m-%d").nunique()
    )
    frequency = {
        "trades": len(portfolio),
        "fx_days": fx_days,
        "trades_per_fx_day": len(portfolio) / fx_days,
        "active_trade_days": active_days,
        "trades_per_active_trade_day": len(portfolio) / active_days,
    }
    boot = config["bootstrap"]
    trade_bootstrap = circular_block_bootstrap(
        portfolio["r"].to_numpy(float),
        samples=int(boot["samples"]),
        block_trades=int(boot["trade_block_trades"]),
        seed=int(boot["seed"]),
        lower_quantile=float(boot["lower_quantile"]),
    )
    calendar_bootstrap = circular_calendar_month_bootstrap(
        portfolio,
        start=start,
        end=end,
        samples=int(boot["samples"]),
        block_months=int(boot["calendar_block_months"]),
        seed=int(boot["seed"]),
        lower_quantile=float(boot["lower_quantile"]),
    )
    gates = evaluate_demo_gates(
        windows,
        scenarios,
        frequency,
        trade_bootstrap,
        calendar_bootstrap,
        config["demo_historical_gates"],
    )
    latest_6 = _evaluation_subset(
        portfolio, config["reporting_windows"]["LATEST_6_MONTHS"]
    )
    historical_pass = all(gates.values())
    result = {
        "schema_version": "eurusd_h4_causal_demo_v2_result",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor["source"]["sha256"],
        "post_hoc_developmental_not_pristine_oos": True,
        "broker_action_allowed": False,
        "data_audit": data_audit,
        "variants": variants,
        "selected_components": [
            f"{side}_{regime.upper()}_{variant}"
            for side, regime, variant in selected
        ],
        "portfolio": {
            "windows": windows,
            "scenarios": scenarios,
            "frequency": frequency,
            "risk_cap": risk_caps,
            "concurrency": concurrency_audit(portfolio),
            "trade_bootstrap": trade_bootstrap,
            "calendar_bootstrap": calendar_bootstrap,
            "gates": gates,
            "all_historical_demo_gates_passed": historical_pass,
            "latest_6_months_by_month": _period_metrics(latest_6, "%Y-%m"),
        },
        "status": (
            "HISTORICAL_GATES_PASS_REQUIRES_MT5_PARITY_AND_PROSPECTIVE_DEMO"
            if historical_pass
            else "NO_DEMO_PROMOTION"
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    portfolio.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    pd.DataFrame(
        [
            {
                "variant": name,
                "admitted": item["evaluation"]["admitted"],
                **item["evaluation"]["windows"]["FULL_AUDIT"],
                "extra_0p5pip_profit_factor": item["evaluation"]["extra_0p5pip"][
                    "profit_factor"
                ],
                "latest_12_month_profit_factor": item["evaluation"]["windows"][
                    "LATEST_12_MONTHS"
                ]["profit_factor"],
            }
            for name, item in variants.items()
        ]
    ).to_csv(output_dir / "VARIANTS.csv", index=False, lineterminator="\n")
    pd.DataFrame(
        [{"scenario": name, **metrics} for name, metrics in scenarios.items()]
    ).to_csv(output_dir / "SCENARIOS.csv", index=False, lineterminator="\n")
    pd.DataFrame(result["portfolio"]["latest_6_months_by_month"]).to_csv(
        output_dir / "LATEST_6_MONTHS.csv", index=False, lineterminator="\n"
    )
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (package_root / "EURUSD_H4_CAUSAL_DEMO_V2_RESULT_2026_07_30.md").write_text(
        _render_report(result), encoding="utf-8", newline="\n"
    )
    return result
