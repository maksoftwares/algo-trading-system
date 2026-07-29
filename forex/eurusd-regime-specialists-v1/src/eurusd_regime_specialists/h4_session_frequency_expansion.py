from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

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
from .neutral_h4_quiet_state_transfer import (
    add_h4_regimes,
    aggregate_h1,
    build_signal_mask,
    load_m5,
    sha256_file,
    simulate_short,
    summarize,
)

CHRONOLOGY = (
    "EARLY_2017_2019",
    "MIDDLE_2020_2022H1",
    "LATE_2022H2_2024H1",
    "RECENT_2024H2_2026H1",
)


def transferred_candidate(
    template: dict[str, Any],
    session_name: str,
    session: dict[str, Any],
) -> dict[str, Any]:
    result = dict(template)
    regime_name = str(template["owned_regime"]).upper()
    result["specialist_id"] = f"{session_name}_{regime_name}_SHORT_TRANSFER"
    result["reference_hours_utc"] = list(session["reference_hours_utc"])
    result["decision_hours_utc"] = list(session["decision_hours_utc"])
    result["prior_evidence"] = "None; mechanical session transfer."
    return result


def apply_causal_risk_cap(
    trades: pd.DataFrame,
    *,
    maximum_risk: float,
    priority: list[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if trades.empty:
        return trades.copy(), {"accepted": 0, "risk_cap_rejections": 0}
    order = {name: index for index, name in enumerate(priority)}
    work = trades.copy()
    work["_priority"] = work["portfolio_sleeve"].map(order)
    if work["_priority"].isna().any():
        missing = sorted(
            work.loc[work["_priority"].isna(), "portfolio_sleeve"].unique()
        )
        raise RuntimeError(f"Missing fixed priority for sleeves: {missing}")
    work = work.sort_values(
        ["entry_time_utc", "_priority", "specialist_id"], kind="stable"
    )
    active: list[tuple[pd.Timestamp, float]] = []
    accepted_indices: list[int] = []
    rejected_by_sleeve: dict[str, int] = {}
    for index, row in work.iterrows():
        entry = pd.Timestamp(row["entry_time_utc"])
        active = [(exit_time, risk) for exit_time, risk in active if exit_time > entry]
        open_risk = sum(risk for _, risk in active)
        risk = float(row["portfolio_risk_weight"])
        if open_risk + risk > float(maximum_risk) + 1e-12:
            sleeve = str(row["portfolio_sleeve"])
            rejected_by_sleeve[sleeve] = rejected_by_sleeve.get(sleeve, 0) + 1
            continue
        accepted_indices.append(index)
        active.append((pd.Timestamp(row["exit_time_utc"]), risk))
    accepted = work.loc[accepted_indices].drop(columns="_priority")
    accepted = accepted.sort_values("exit_time_utc", kind="stable").reset_index(
        drop=True
    )
    return accepted, {
        "candidate_trades": len(work),
        "accepted": len(accepted),
        "risk_cap_rejections": len(work) - len(accepted),
        "risk_cap_rejections_by_sleeve": rejected_by_sleeve,
    }


def _windows(
    trades: pd.DataFrame, reporting_windows: dict[str, list[str]]
) -> dict[str, dict[str, Any]]:
    return {
        name: summarize(_evaluation_subset(trades, window))
        for name, window in reporting_windows.items()
    }


def evaluate_session_bundle(
    trades: pd.DataFrame,
    reporting_windows: dict[str, list[str]],
    gates: dict[str, Any],
) -> dict[str, Any]:
    windows = _windows(trades, reporting_windows)
    stress = _scenario_summary(apply_weighted_cost(trades, 0.5))
    full = windows["FULL_AUDIT"]
    checks = {
        "minimum_trades": full["trades"] >= int(gates["minimum_trades"]),
        "full_profit_factor": full["profit_factor"]
        >= float(gates["minimum_full_profit_factor"]),
        "extra_0p5pip_profit_factor": stress["profit_factor"]
        > float(gates["minimum_extra_0p5pip_profit_factor_exclusive"]),
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
    return {
        "windows": windows,
        "extra_0p5pip": stress,
        "admission_checks": checks,
        "admitted": all(checks.values()),
    }


def evaluate_final_gates(
    baseline_trades: int,
    windows: dict[str, dict[str, Any]],
    scenarios: dict[str, dict[str, Any]],
    trade_bootstrap: dict[str, Any],
    calendar_bootstrap: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    full = windows["FULL_AUDIT"]
    return {
        "minimum_trade_count_gain": full["trades"]
        >= baseline_trades * (1.0 + float(gates["minimum_trade_count_gain"])),
        "full_profit_factor": full["profit_factor"]
        >= float(gates["minimum_full_profit_factor"]),
        "extra_0p5pip_profit_factor": scenarios["COST_PLUS_0P5_PIP"]["profit_factor"]
        >= float(gates["minimum_extra_0p5pip_profit_factor"]),
        "extra_1p0pip_profit_factor": scenarios["COST_PLUS_1P0_PIP"]["profit_factor"]
        >= float(gates["minimum_extra_1p0pip_profit_factor"]),
        "each_chronological_block_profit_factor": all(
            windows[name]["profit_factor"]
            > float(gates["minimum_each_chronological_block_profit_factor_exclusive"])
            for name in CHRONOLOGY
        ),
        "latest_12_month_profit_factor": windows["LATEST_12_MONTHS"]["profit_factor"]
        >= float(gates["minimum_latest_12_month_profit_factor"]),
        "latest_6_month_net_r": windows["LATEST_6_MONTHS"]["net_r"]
        > float(gates["minimum_latest_6_month_net_r_exclusive"]),
        "top_5pct_winners_removed_profit_factor": full[
            "top_5pct_winners_removed_profit_factor"
        ]
        >= float(gates["minimum_top_5pct_winners_removed_profit_factor"]),
        "maximum_closed_trade_drawdown": full["maximum_drawdown_r"]
        <= float(gates["maximum_closed_trade_drawdown_r"]),
        "entry_delay_5m_profit_factor": scenarios["ENTRY_DELAY_5M"]["profit_factor"]
        >= float(gates["minimum_5m_delay_profit_factor"]),
        "entry_delay_15m_profit_factor": scenarios["ENTRY_DELAY_15M"]["profit_factor"]
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


def _fx_days(m5: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> int:
    subset = m5[(m5["timestamp"] >= start) & (m5["timestamp"] < end)]
    return int(subset["timestamp"].dt.strftime("%Y-%m-%d").nunique())


def _render_report(result: dict[str, Any]) -> str:
    baseline = result["baseline"]["windows"]["FULL_AUDIT"]
    final = result["final"]["windows"]["FULL_AUDIT"]
    latest = result["final"]["windows"]["LATEST_6_MONTHS"]
    session_lines = "\n".join(
        f"| {name} | {item['windows']['FULL_AUDIT']['trades']} | "
        f"{item['windows']['FULL_AUDIT']['profit_factor']:.3f} | "
        f"{item['extra_0p5pip']['profit_factor']:.3f} | "
        f"{item['windows']['LATEST_12_MONTHS']['profit_factor']:.3f} | "
        f"{item['admitted']} |"
        for name, item in result["session_bundles"].items()
    )
    failed = [
        name for name, passed in result["final"]["gate_results"].items() if not passed
    ]
    return f"""# EURUSD H4 session-frequency expansion result

Status: **{result["status"]}**

## Transferred session bundles

| Session | Trades | PF | +0.5 pip PF | Latest-12M PF | Admitted |
|---|---:|---:|---:|---:|---:|
{session_lines}

## Protected baseline versus final

| Portfolio | Trades | Trades/FX day | PF | Net R | Max DD |
|---|---:|---:|---:|---:|---:|
| Baseline | {baseline["trades"]} | {result["baseline"]["frequency"]["trades_per_fx_day"]:.3f} | {baseline["profit_factor"]:.3f} | {baseline["net_r"]:+.3f} | {baseline["maximum_drawdown_r"]:.3f} |
| Final | {final["trades"]} | {result["final"]["frequency"]["trades_per_fx_day"]:.3f} | {final["profit_factor"]:.3f} | {final["net_r"]:+.3f} | {final["maximum_drawdown_r"]:.3f} |

Trade-count gain: {result["final"]["frequency"]["trade_count_gain"]:.1%}.

Latest six months: {latest["trades"]} trades, PF {latest["profit_factor"]:.3f}, {latest["net_r"]:+.3f}R, {latest["pnl_usd_001_lot"]:+.2f} USD at the research lot equivalents.

Failed frozen final gates: {", ".join(failed) if failed else "none"}.

Only complete session bundles could qualify; no favorable regime, side, year,
or subgroup was selected after outcomes.
"""


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    package_root = config_path.parent.parent
    anchor_path = package_root / config["anchor_config"]["path"]
    prior_ledger_path = package_root / config["prior_unweighted_ledger"]["path"]
    if sha256_file(anchor_path) != config["anchor_config"]["sha256"]:
        raise RuntimeError("Anchor configuration checksum mismatch")
    if sha256_file(prior_ledger_path) != config["prior_unweighted_ledger"]["sha256"]:
        raise RuntimeError("Prior ledger checksum mismatch")
    anchor = json.loads(anchor_path.read_bytes())
    m5 = load_m5(anchor["source"])
    data_audit = audit_m5(m5, anchor["source"])
    h1 = aggregate_h1(m5)
    h1, _ = add_h4_regimes(h1, anchor["classifier"])
    templates = {item["owned_regime"]: item for item in anchor["candidates"]}
    start, end = map(pd.Timestamp, config["evaluation_window"])

    baseline_raw: dict[tuple[int, str], pd.DataFrame] = {}
    diagnostics: dict[str, Any] = {}
    parity = {}
    for delay in (0, *config["stress_scenarios"]["entry_delay_minutes"]):
        for regime, template in templates.items():
            raw, diag = simulate_short(
                h1,
                m5,
                build_signal_mask(h1, template),
                template,
                anchor,
                entry_delay_minutes=int(delay),
            )
            raw = _evaluation_subset(raw, config["evaluation_window"])
            baseline_raw[(int(delay), regime)] = raw
            diagnostics[f"BASELINE_{regime}_{delay}m"] = diag
            if delay == 0:
                parity[regime] = _parity_check(
                    raw,
                    prior_ledger_path,
                    template["specialist_id"],
                    config["evaluation_window"],
                )

    transfer_raw: dict[tuple[int, str, str], pd.DataFrame] = {}
    bundle_results = {}
    contract = config["transfer_contract"]
    for session_name, session in config["transferred_sessions"].items():
        pieces = []
        for regime, template in templates.items():
            candidate = transferred_candidate(template, session_name, session)
            raw, diag = simulate_short(
                h1,
                m5,
                build_signal_mask(h1, candidate),
                candidate,
                anchor,
            )
            raw = _evaluation_subset(raw, config["evaluation_window"])
            transfer_raw[(0, session_name, regime)] = raw
            diagnostics[f"{session_name}_{regime}_0m"] = diag
            regime_weight = (
                float(contract["session_bundle_chop_weight"])
                if regime == "chop"
                else float(contract["session_bundle_compression_weight"])
            )
            piece = apply_portfolio_weight(raw, regime_weight)
            pieces.append(piece)
        bundle = pd.concat(pieces, ignore_index=True).sort_values("exit_time_utc")
        bundle_results[session_name] = evaluate_session_bundle(
            bundle,
            config["reporting_windows"],
            config["session_bundle_admission"],
        )

    admitted = [name for name, item in bundle_results.items() if item["admitted"]]
    for delay in config["stress_scenarios"]["entry_delay_minutes"]:
        for session_name in admitted:
            session = config["transferred_sessions"][session_name]
            for regime, template in templates.items():
                candidate = transferred_candidate(template, session_name, session)
                raw, diag = simulate_short(
                    h1,
                    m5,
                    build_signal_mask(h1, candidate),
                    candidate,
                    anchor,
                    entry_delay_minutes=int(delay),
                )
                transfer_raw[(int(delay), session_name, regime)] = _evaluation_subset(
                    raw, config["evaluation_window"]
                )
                diagnostics[f"{session_name}_{regime}_{delay}m"] = diag

    priority = config["portfolio_risk"]["fixed_priority"]
    max_risk = float(config["portfolio_risk"]["maximum_concurrent_initial_risk_units"])

    def assemble(
        delay: int, include_admitted: bool
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        pieces = []
        for regime, raw in (
            ("chop", baseline_raw[(delay, "chop")]),
            ("compression", baseline_raw[(delay, "compression")]),
        ):
            weight = float(
                config["protected_baseline"][templates[regime]["specialist_id"]]
            )
            piece = apply_portfolio_weight(raw, weight)
            piece["portfolio_sleeve"] = f"BASELINE_{regime.upper()}"
            pieces.append(piece)
        if include_admitted:
            scale = float(contract["admitted_session_portfolio_scale"])
            for session_name in admitted:
                for regime in ("chop", "compression"):
                    base_weight = (
                        float(contract["session_bundle_chop_weight"])
                        if regime == "chop"
                        else float(contract["session_bundle_compression_weight"])
                    )
                    piece = apply_portfolio_weight(
                        transfer_raw[(delay, session_name, regime)],
                        base_weight * scale,
                    )
                    piece["portfolio_sleeve"] = f"{session_name}_{regime.upper()}"
                    pieces.append(piece)
        candidates = pd.concat(pieces, ignore_index=True)
        return apply_causal_risk_cap(
            candidates, maximum_risk=max_risk, priority=priority
        )

    baseline, baseline_cap = assemble(0, False)
    final_ledgers = {}
    cap_diagnostics = {}
    for delay in (0, *config["stress_scenarios"]["entry_delay_minutes"]):
        ledger, cap = assemble(int(delay), True)
        final_ledgers[int(delay)] = ledger
        cap_diagnostics[f"{delay}m"] = cap
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
    all_gates = all(gate_results.values())
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
    result = {
        "schema_version": "eurusd_h4_session_frequency_expansion_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor["source"]["sha256"],
        "post_hoc_developmental_not_pristine_oos": True,
        "broker_action_allowed": False,
        "data_audit": data_audit,
        "baseline_parity": parity,
        "diagnostics": diagnostics,
        "session_bundles": bundle_results,
        "admitted_session_bundles": admitted,
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
            else "NO_SAFE_SESSION_FREQUENCY_EXPANSION"
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
                "session": name,
                "admitted": item["admitted"],
                **item["windows"]["FULL_AUDIT"],
                "extra_0p5pip_profit_factor": item["extra_0p5pip"]["profit_factor"],
                "latest_12_month_profit_factor": item["windows"]["LATEST_12_MONTHS"][
                    "profit_factor"
                ],
            }
            for name, item in bundle_results.items()
        ]
    ).to_csv(output_dir / "SESSION_BUNDLES.csv", index=False, lineterminator="\n")
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (
        package_root / "EURUSD_H4_SESSION_FREQUENCY_EXPANSION_RESULT_2026_07_30.md"
    ).write_text(
        _render_report(result),
        encoding="utf-8",
        newline="\n",
    )
    return result
