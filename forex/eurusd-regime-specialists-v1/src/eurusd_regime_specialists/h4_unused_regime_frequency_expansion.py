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
)
from .h4_dual_regime_portfolio_diagnostic import (
    apply_portfolio_weight,
    apply_weighted_cost,
    apply_weighted_rollover,
    circular_calendar_month_bootstrap,
    concurrency_audit,
)
from .h4_session_frequency_expansion import (
    CHRONOLOGY,
    _fx_days,
    _windows,
    apply_causal_risk_cap,
    evaluate_final_gates,
)
from .neutral_h4_quiet_state_transfer import (
    PIP,
    PIP_VALUE_USD_001_LOT,
    PRICE_COLUMNS,
    _overlaps_quarantine,
    add_h4_regimes,
    aggregate_h1,
    build_signal_mask,
    load_m5,
    sha256_file,
    simulate_short,
)


def build_directional_masks(
    h1: pd.DataFrame, candidate: dict[str, Any]
) -> dict[str, pd.Series]:
    date = h1["timestamp"].dt.strftime("%Y-%m-%d")
    hour = h1["timestamp"].dt.hour
    reference = hour.isin(candidate["reference_hours_utc"]) & h1["complete_hour"]
    ref_high = h1["mid_high"].where(reference).groupby(date).transform("max")
    ref_low = h1["mid_low"].where(reference).groupby(date).transform("min")
    ref_count = reference.groupby(date).transform("sum")
    common = (
        hour.isin(candidate["decision_hours_utc"])
        & ref_count.eq(len(candidate["reference_hours_utc"]))
        & h1["complete_hour"]
        & h1["contiguous_next"]
        & (h1["body_fraction"] >= float(candidate["body_fraction_minimum"]))
        & h1["regime"].eq(candidate["owned_regime"])
        & h1["atr"].notna()
    ).fillna(False)
    raw_long = common & (h1["mid_close"] > ref_high)
    raw_short = common & (h1["mid_close"] < ref_low)
    direction = candidate["direction"]
    if direction == "LONG":
        return {"LONG": raw_long & raw_long.groupby(date).cumsum().eq(1)}
    if direction == "SHORT":
        return {"SHORT": raw_short & raw_short.groupby(date).cumsum().eq(1)}
    if direction != "TWO_SIDED":
        raise ValueError(f"Unsupported direction: {direction}")
    first = (raw_long | raw_short) & (raw_long | raw_short).groupby(date).cumsum().eq(1)
    return {"LONG": first & raw_long, "SHORT": first & raw_short}


def simulate_long(
    h1: pd.DataFrame,
    m5: pd.DataFrame,
    mask: pd.Series,
    candidate: dict[str, Any],
    config: dict[str, Any],
    entry_delay_minutes: int = 0,
) -> tuple[pd.DataFrame, dict[str, int]]:
    execution = config["execution"]
    spread_floor = float(execution["minimum_retail_spread_pips"]) * PIP
    maximum_spread = float(execution["maximum_entry_spread_pips"])
    slip = float(execution["adverse_slippage_pips_per_side"]) * PIP
    stress_extra = float(execution["extra_round_trip_stress_pips"])
    maximum_bars = int(candidate["maximum_hold_hours"]) * 12
    times = m5["timestamp"].to_numpy()
    time_to_index = {pd.Timestamp(value): index for index, value in enumerate(times)}
    arrays = {name: m5[name].to_numpy(dtype=float) for name in PRICE_COLUMNS}
    eligible = np.flatnonzero(mask.to_numpy())
    blocked_until = -1
    records: list[dict[str, Any]] = []
    diagnostics = {
        "signals": len(eligible),
        "missing_entry": 0,
        "incomplete_path": 0,
        "spread_rejection": 0,
        "overlap_rejection": 0,
        "quarantine_rejection": 0,
    }
    for signal_index in eligible:
        signal_time = pd.Timestamp(h1["timestamp"].iloc[signal_index])
        entry_time = signal_time + pd.Timedelta(
            hours=1, minutes=int(entry_delay_minutes)
        )
        entry_index = time_to_index.get(entry_time)
        if entry_index is None:
            diagnostics["missing_entry"] += 1
            continue
        if entry_index <= blocked_until:
            diagnostics["overlap_rejection"] += 1
            continue
        final_index = entry_index + maximum_bars - 1
        if final_index >= len(m5) or (
            pd.Timestamp(times[final_index]) - entry_time
            != pd.Timedelta(minutes=5 * (maximum_bars - 1))
        ):
            diagnostics["incomplete_path"] += 1
            continue
        effective_ask_open = max(
            arrays["ask_open"][entry_index],
            arrays["bid_open"][entry_index] + spread_floor,
        )
        entry_spread_pips = (effective_ask_open - arrays["bid_open"][entry_index]) / PIP
        if entry_spread_pips > maximum_spread:
            diagnostics["spread_rejection"] += 1
            continue
        stop_distance = float(candidate["stop_atr_multiple"]) * float(
            h1["atr"].iloc[signal_index]
        )
        if not math.isfinite(stop_distance) or stop_distance <= 0.0:
            diagnostics["incomplete_path"] += 1
            continue
        entry = effective_ask_open + slip
        stop = entry - stop_distance
        target = entry + float(candidate["target_r_multiple"]) * stop_distance
        exit_index = final_index
        exit_price = arrays["bid_close"][final_index] - slip
        exit_reason = "TIME"
        for position in range(entry_index, final_index + 1):
            bid_open = min(
                arrays["bid_open"][position],
                arrays["ask_open"][position] - spread_floor,
            )
            bid_high = min(
                arrays["bid_high"][position],
                arrays["ask_high"][position] - spread_floor,
            )
            bid_low = min(
                arrays["bid_low"][position],
                arrays["ask_low"][position] - spread_floor,
            )
            if bid_open <= stop:
                exit_index = position
                exit_price = min(bid_open, stop) - slip
                exit_reason = "STOP_GAP"
                break
            if bid_low <= stop:
                exit_index = position
                exit_price = stop - slip
                exit_reason = "STOP"
                break
            if bid_high >= target:
                exit_index = position
                exit_price = max(bid_open, target) - slip
                exit_reason = "TARGET"
                break
        exit_time = pd.Timestamp(times[exit_index])
        if _overlaps_quarantine(
            entry_time, exit_time + pd.Timedelta(minutes=5), config["source"]
        ):
            diagnostics["quarantine_rejection"] += 1
            continue
        net_pips = (exit_price - entry) / PIP
        stop_pips = stop_distance / PIP
        r = net_pips / stop_pips
        records.append(
            {
                "specialist_id": candidate["specialist_id"],
                "owned_regime": candidate["owned_regime"],
                "side": "LONG",
                "signal_time_utc": signal_time,
                "entry_time_utc": entry_time,
                "entry_delay_minutes": int(entry_delay_minutes),
                "exit_time_utc": exit_time,
                "entry": entry,
                "stop": stop,
                "target": target,
                "exit": exit_price,
                "entry_spread_pips": entry_spread_pips,
                "stop_pips": stop_pips,
                "net_pips": net_pips,
                "r": r,
                "stress_r": r - stress_extra / stop_pips,
                "pnl_usd_001_lot": net_pips * PIP_VALUE_USD_001_LOT,
                "exit_reason": exit_reason,
            }
        )
        blocked_until = exit_index
    return pd.DataFrame(records), diagnostics


def make_regime_candidate(
    template: dict[str, Any], expert_id: str, specification: dict[str, Any]
) -> dict[str, Any]:
    result = dict(template)
    result["specialist_id"] = expert_id
    result["owned_regime"] = specification["owned_regime"]
    result["direction"] = specification["direction"]
    result["prior_evidence"] = "None; direction-aligned unused-regime transfer."
    return result


def simulate_candidate(
    h1: pd.DataFrame,
    m5: pd.DataFrame,
    candidate: dict[str, Any],
    anchor: dict[str, Any],
    delay: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    masks = build_directional_masks(h1, candidate)
    pieces = []
    diagnostics = {}
    for side, mask in masks.items():
        if side == "SHORT":
            trades, diag = simulate_short(
                h1,
                m5,
                mask,
                candidate,
                anchor,
                entry_delay_minutes=delay,
            )
        else:
            trades, diag = simulate_long(
                h1,
                m5,
                mask,
                candidate,
                anchor,
                entry_delay_minutes=delay,
            )
        pieces.append(trades)
        diagnostics[side] = diag
    ledger = pd.concat(pieces, ignore_index=True)
    return ledger.sort_values("exit_time_utc"), diagnostics


def evaluate_expert(
    trades: pd.DataFrame,
    reporting_windows: dict[str, list[str]],
    gates: dict[str, Any],
    two_sided: bool,
) -> dict[str, Any]:
    windows = _windows(trades, reporting_windows)
    stress = _scenario_summary(apply_weighted_cost(trades, 0.5))
    full = windows["FULL_AUDIT"]
    side_metrics = {
        side: _scenario_summary(group) for side, group in trades.groupby("side")
    }
    checks = {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "full_profit_factor": full["profit_factor"]
        >= float(gates["minimum_full_profit_factor"]),
        "extra_0p5pip_profit_factor": stress["profit_factor"]
        >= float(gates["minimum_extra_0p5pip_profit_factor"]),
        "chronological_blocks": all(
            windows[name]["profit_factor"]
            >= float(gates["minimum_each_chronological_block_profit_factor"])
            for name in CHRONOLOGY
        ),
        "latest_12_month_profit_factor": windows["LATEST_12_MONTHS"]["profit_factor"]
        > float(gates["minimum_latest_12_month_profit_factor_exclusive"]),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
    }
    if two_sided:
        checks["transition_each_side_sample"] = all(
            side_metrics.get(side, {}).get("trades", 0)
            >= int(gates["transition_minimum_trades_each_side"])
            for side in ("LONG", "SHORT")
        )
        checks["transition_each_side_profit_factor"] = all(
            side_metrics.get(side, {}).get("profit_factor", 0.0)
            >= float(gates["transition_minimum_profit_factor_each_side"])
            for side in ("LONG", "SHORT")
        )
    return {
        "windows": windows,
        "extra_0p5pip": stress,
        "side_metrics": side_metrics,
        "admission_checks": checks,
        "admitted": all(checks.values()),
    }


def _render_report(result: dict[str, Any]) -> str:
    baseline = result["baseline"]["windows"]["FULL_AUDIT"]
    final = result["final"]["windows"]["FULL_AUDIT"]
    latest = result["final"]["windows"]["LATEST_6_MONTHS"]
    expert_lines = "\n".join(
        f"| {name} | {item['windows']['FULL_AUDIT']['trades']} | "
        f"{item['windows']['FULL_AUDIT']['profit_factor']:.3f} | "
        f"{item['extra_0p5pip']['profit_factor']:.3f} | "
        f"{item['windows']['LATEST_12_MONTHS']['profit_factor']:.3f} | "
        f"{item['admitted']} |"
        for name, item in result["experts"].items()
    )
    failed = [
        name for name, passed in result["final"]["gate_results"].items() if not passed
    ]
    return f"""# EURUSD H4 unused-regime frequency expansion result

Status: **{result["status"]}**

| Expert | Trades | PF | +0.5 pip PF | Latest-12M PF | Admitted |
|---|---:|---:|---:|---:|---:|
{expert_lines}

| Portfolio | Trades | Trades/FX day | PF | Net R | Max DD |
|---|---:|---:|---:|---:|---:|
| Baseline | {baseline["trades"]} | {result["baseline"]["frequency"]["trades_per_fx_day"]:.3f} | {baseline["profit_factor"]:.3f} | {baseline["net_r"]:+.3f} | {baseline["maximum_drawdown_r"]:.3f} |
| Final | {final["trades"]} | {result["final"]["frequency"]["trades_per_fx_day"]:.3f} | {final["profit_factor"]:.3f} | {final["net_r"]:+.3f} | {final["maximum_drawdown_r"]:.3f} |

Trade-count gain: {result["final"]["frequency"]["trade_count_gain"]:.1%}.

Latest six months: {latest["trades"]} trades, PF {latest["profit_factor"]:.3f}, {latest["net_r"]:+.3f}R, {latest["pnl_usd_001_lot"]:+.2f} USD.

Failed final gates: {", ".join(failed) if failed else "none"}.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    package_root = config_path.parent.parent
    anchor_path = package_root / config["anchor_config"]["path"]
    prior_path = package_root / config["prior_unweighted_ledger"]["path"]
    if sha256_file(anchor_path) != config["anchor_config"]["sha256"]:
        raise RuntimeError("Anchor configuration checksum mismatch")
    if sha256_file(prior_path) != config["prior_unweighted_ledger"]["sha256"]:
        raise RuntimeError("Prior ledger checksum mismatch")
    anchor = json.loads(anchor_path.read_bytes())
    m5 = load_m5(anchor["source"])
    data_audit = audit_m5(m5, anchor["source"])
    h1 = aggregate_h1(m5)
    h1, _ = add_h4_regimes(h1, anchor["classifier"])
    templates = {item["owned_regime"]: item for item in anchor["candidates"]}
    template = next(
        item
        for item in anchor["candidates"]
        if item["specialist_id"]
        == config["transfer_contract"]["source_parameter_template"]
    )
    start, end = map(pd.Timestamp, config["evaluation_window"])
    delays = (0, *config["stress_scenarios"]["entry_delay_minutes"])

    baseline_raw = {}
    parity = {}
    diagnostics = {}
    for delay in delays:
        for regime, base_candidate in templates.items():
            raw, diag = simulate_short(
                h1,
                m5,
                build_signal_mask(h1, base_candidate),
                base_candidate,
                anchor,
                entry_delay_minutes=int(delay),
            )
            raw = _evaluation_subset(raw, config["evaluation_window"])
            baseline_raw[(int(delay), regime)] = raw
            diagnostics[f"BASELINE_{regime}_{delay}m"] = diag
            if delay == 0:
                parity[regime] = _parity_check(
                    raw,
                    prior_path,
                    base_candidate["specialist_id"],
                    config["evaluation_window"],
                )

    candidates = {
        expert_id: make_regime_candidate(template, expert_id, specification)
        for expert_id, specification in config["new_regime_experts"].items()
    }
    expert_raw = {}
    expert_results = {}
    for expert_id, candidate in candidates.items():
        raw, diag = simulate_candidate(h1, m5, candidate, anchor, 0)
        raw = _evaluation_subset(raw, config["evaluation_window"])
        expert_raw[(0, expert_id)] = raw
        diagnostics[f"{expert_id}_0m"] = diag
        weighted = apply_portfolio_weight(raw, 1.0)
        expert_results[expert_id] = evaluate_expert(
            weighted,
            config["reporting_windows"],
            config["expert_admission"],
            two_sided=candidate["direction"] == "TWO_SIDED",
        )
    admitted = [
        expert_id for expert_id, item in expert_results.items() if item["admitted"]
    ]
    for delay in config["stress_scenarios"]["entry_delay_minutes"]:
        for expert_id in admitted:
            raw, diag = simulate_candidate(
                h1, m5, candidates[expert_id], anchor, int(delay)
            )
            expert_raw[(int(delay), expert_id)] = _evaluation_subset(
                raw, config["evaluation_window"]
            )
            diagnostics[f"{expert_id}_{delay}m"] = diag

    max_risk = float(config["portfolio_risk"]["maximum_concurrent_initial_risk_units"])
    priority = config["portfolio_risk"]["fixed_priority"]

    def assemble(
        delay: int, include_admitted: bool
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        pieces = []
        for regime in ("chop", "compression"):
            weight = float(
                config["protected_baseline"][templates[regime]["specialist_id"]]
            )
            piece = apply_portfolio_weight(baseline_raw[(delay, regime)], weight)
            piece["portfolio_sleeve"] = f"BASELINE_{regime.upper()}"
            pieces.append(piece)
        if include_admitted:
            scale = float(
                config["transfer_contract"]["admitted_expert_portfolio_scale"]
            )
            for expert_id in admitted:
                piece = apply_portfolio_weight(expert_raw[(delay, expert_id)], scale)
                piece["portfolio_sleeve"] = expert_id
                pieces.append(piece)
        return apply_causal_risk_cap(
            pd.concat(pieces, ignore_index=True),
            maximum_risk=max_risk,
            priority=priority,
        )

    baseline, baseline_cap = assemble(0, False)
    final_ledgers = {}
    cap_diagnostics = {}
    for delay in delays:
        final_ledgers[int(delay)], cap_diagnostics[f"{delay}m"] = assemble(
            int(delay), True
        )
    final = final_ledgers[0]
    plus_half = apply_weighted_cost(final, 0.5)
    plus_one = apply_weighted_cost(final, 1.0)
    rollover = apply_weighted_rollover(
        final,
        float(config["stress_scenarios"]["rollover_charge_pips_per_utc_21_crossing"]),
    )
    scenario_ledgers = {
        "BASE": final,
        "COST_PLUS_0P5_PIP": plus_half,
        "COST_PLUS_1P0_PIP": plus_one,
        "ENTRY_DELAY_5M": final_ledgers[5],
        "ENTRY_DELAY_15M": final_ledgers[15],
        "ROLLOVER_0P5_PIP": rollover,
    }
    scenarios = {
        name: _scenario_summary(trades) for name, trades in scenario_ledgers.items()
    }
    baseline_windows = _windows(baseline, config["reporting_windows"])
    final_windows = _windows(final, config["reporting_windows"])
    boot = config["bootstrap"]
    trade_bootstrap = circular_block_bootstrap(
        final["r"].to_numpy(dtype=float),
        samples=int(boot["samples"]),
        block_trades=int(boot["trade_block_trades"]),
        seed=int(boot["seed"]),
        lower_quantile=float(boot["lower_quantile"]),
    )
    calendar_bootstrap = circular_calendar_month_bootstrap(
        final,
        start=start,
        end=end,
        samples=int(boot["samples"]),
        block_months=int(boot["calendar_block_months"]),
        seed=int(boot["seed"]),
        lower_quantile=float(boot["lower_quantile"]),
    )
    gate_results = evaluate_final_gates(
        baseline_windows["FULL_AUDIT"]["trades"],
        final_windows,
        scenarios,
        trade_bootstrap,
        calendar_bootstrap,
        config["frequency_preserving_edge_gates"],
    )
    fx_days = _fx_days(m5, start, end)
    baseline_frequency = {
        "trades": len(baseline),
        "fx_days": fx_days,
        "trades_per_fx_day": len(baseline) / fx_days,
    }
    final_frequency = {
        "trades": len(final),
        "fx_days": fx_days,
        "trades_per_fx_day": len(final) / fx_days,
        "trade_count_gain": len(final) / len(baseline) - 1.0,
    }
    all_gates = all(gate_results.values())
    result = {
        "schema_version": "eurusd_h4_unused_regime_frequency_expansion_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor["source"]["sha256"],
        "post_hoc_developmental_not_pristine_oos": True,
        "broker_action_allowed": False,
        "data_audit": data_audit,
        "baseline_parity": parity,
        "diagnostics": diagnostics,
        "experts": expert_results,
        "admitted_experts": admitted,
        "baseline": {
            "windows": baseline_windows,
            "risk_cap": baseline_cap,
            "frequency": baseline_frequency,
        },
        "final": {
            "windows": final_windows,
            "scenarios": scenarios,
            "trade_bootstrap": trade_bootstrap,
            "calendar_bootstrap": calendar_bootstrap,
            "risk_cap": cap_diagnostics,
            "concurrency": concurrency_audit(final),
            "frequency": final_frequency,
            "gate_results": gate_results,
            "all_frequency_preserving_edge_gates_passed": all_gates,
        },
        "status": (
            "FREQUENCY_INCREASED_WITH_HISTORICAL_EDGE_PRESERVED_REQUIRES_FRESH_CONFIRMATION"
            if all_gates
            else "NO_SAFE_UNUSED_REGIME_FREQUENCY_EXPANSION"
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    final.to_csv(output_dir / "TRADES.csv", index=False, lineterminator="\n")
    pd.DataFrame(
        [{"scenario": name, **metrics} for name, metrics in scenarios.items()]
    ).to_csv(output_dir / "SCENARIO_METRICS.csv", index=False, lineterminator="\n")
    pd.DataFrame(
        [
            {
                "expert": name,
                "admitted": item["admitted"],
                **item["windows"]["FULL_AUDIT"],
                "extra_0p5pip_profit_factor": item["extra_0p5pip"]["profit_factor"],
                "latest_12_month_profit_factor": item["windows"]["LATEST_12_MONTHS"][
                    "profit_factor"
                ],
            }
            for name, item in expert_results.items()
        ]
    ).to_csv(output_dir / "EXPERTS.csv", index=False, lineterminator="\n")
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (
        package_root
        / "EURUSD_H4_UNUSED_REGIME_FREQUENCY_EXPANSION_RESULT_2026_07_30.md"
    ).write_text(
        _render_report(result),
        encoding="utf-8",
        newline="\n",
    )
    return result
