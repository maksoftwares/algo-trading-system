from __future__ import annotations

import hashlib
import json
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
from .h4_session_frequency_expansion import (
    _fx_days,
    _windows,
    apply_causal_risk_cap,
    evaluate_final_gates,
)
from .neutral_h4_quiet_state_transfer import (
    add_h4_regimes,
    aggregate_h1,
    build_signal_mask,
    load_m5,
    sha256_file,
    simulate_short,
)


def candidate_at_threshold(
    template: dict[str, Any], level_name: str, threshold: float
) -> dict[str, Any]:
    result = dict(template)
    result["specialist_id"] = f"{level_name}_{template['owned_regime'].upper()}"
    result["body_fraction_minimum"] = float(threshold)
    result["prior_evidence"] = "Frozen body-filter frequency ladder."
    return result


def _render_report(result: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| {name} | {item['windows']['FULL_AUDIT']['trades']} | "
        f"{item['frequency']['trade_count_gain']:.1%} | "
        f"{item['windows']['FULL_AUDIT']['profit_factor']:.3f} | "
        f"{item['scenarios']['COST_PLUS_0P5_PIP']['profit_factor']:.3f} | "
        f"{item['windows']['LATEST_12_MONTHS']['profit_factor']:.3f} | "
        f"{item['eligible']} |"
        for name, item in result["levels"].items()
    )
    selected = result["levels"][result["selected_level"]]
    latest = selected["windows"]["LATEST_6_MONTHS"]
    return f"""# EURUSD H4 body-filter frequency ladder result

Status: **{result["status"]}**

| Level | Trades | Gain | PF | +0.5 pip PF | Latest-12M PF | Eligible |
|---|---:|---:|---:|---:|---:|---:|
{rows}

Selected level: **{result["selected_level"]}**.

Selected latest six months: {latest["trades"]} trades, PF {latest["profit_factor"]:.3f}, {latest["net_r"]:+.3f}R, {latest["pnl_usd_001_lot"]:+.2f} USD.
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
    h1, _ = add_h4_regimes(h1, anchor["classifier"])
    templates = {item["owned_regime"]: item for item in anchor["candidates"]}
    start, end = map(pd.Timestamp, config["evaluation_window"])
    delays = (0, *config["stress_scenarios"]["entry_delay_minutes"])
    priority = config["portfolio_risk"]["fixed_priority"]
    max_risk = float(config["portfolio_risk"]["maximum_concurrent_initial_risk_units"])
    boot = config["bootstrap"]
    level_results = {}
    level_ledgers = {}
    diagnostics = {}
    protected_trade_count = 0

    for level_name, thresholds in config["body_threshold_ladder"].items():
        delayed_ledgers = {}
        delayed_caps = {}
        for delay in delays:
            pieces = []
            for regime in ("chop", "compression"):
                candidate = candidate_at_threshold(
                    templates[regime], level_name, float(thresholds[regime])
                )
                raw, diag = simulate_short(
                    h1,
                    m5,
                    build_signal_mask(h1, candidate),
                    candidate,
                    anchor,
                    entry_delay_minutes=int(delay),
                )
                raw = _evaluation_subset(raw, config["evaluation_window"])
                diagnostics[f"{level_name}_{regime}_{delay}m"] = diag
                piece = apply_portfolio_weight(
                    raw, float(config["protected_weights"][regime])
                )
                piece["portfolio_sleeve"] = f"BASELINE_{regime.upper()}"
                pieces.append(piece)
            delayed_ledgers[int(delay)], delayed_caps[f"{delay}m"] = (
                apply_causal_risk_cap(
                    pd.concat(pieces, ignore_index=True),
                    maximum_risk=max_risk,
                    priority=priority,
                )
            )
        ledger = delayed_ledgers[0]
        if level_name == "L0_PROTECTED":
            protected_trade_count = len(ledger)
        plus_half = apply_weighted_cost(ledger, 0.5)
        plus_one = apply_weighted_cost(ledger, 1.0)
        rollover = apply_weighted_rollover(
            ledger,
            float(
                config["stress_scenarios"]["rollover_charge_pips_per_utc_21_crossing"]
            ),
        )
        scenario_ledgers = {
            "BASE": ledger,
            "COST_PLUS_0P5_PIP": plus_half,
            "COST_PLUS_1P0_PIP": plus_one,
            "ENTRY_DELAY_5M": delayed_ledgers[5],
            "ENTRY_DELAY_15M": delayed_ledgers[15],
            "ROLLOVER_0P5_PIP": rollover,
        }
        scenarios = {
            name: _scenario_summary(trades) for name, trades in scenario_ledgers.items()
        }
        windows = _windows(ledger, config["reporting_windows"])
        trade_bootstrap = circular_block_bootstrap(
            ledger["r"].to_numpy(float),
            samples=int(boot["samples"]),
            block_trades=int(boot["trade_block_trades"]),
            seed=int(boot["seed"]),
            lower_quantile=float(boot["lower_quantile"]),
        )
        calendar_bootstrap = circular_calendar_month_bootstrap(
            ledger,
            start=start,
            end=end,
            samples=int(boot["samples"]),
            block_months=int(boot["calendar_block_months"]),
            seed=int(boot["seed"]),
            lower_quantile=float(boot["lower_quantile"]),
        )
        level_ledgers[level_name] = ledger
        level_results[level_name] = {
            "thresholds": thresholds,
            "windows": windows,
            "scenarios": scenarios,
            "trade_bootstrap": trade_bootstrap,
            "calendar_bootstrap": calendar_bootstrap,
            "risk_cap": delayed_caps,
            "concurrency": concurrency_audit(ledger),
        }

    for level_name, item in level_results.items():
        gate_results = evaluate_final_gates(
            protected_trade_count,
            item["windows"],
            item["scenarios"],
            item["trade_bootstrap"],
            item["calendar_bootstrap"],
            {
                **config["frequency_preserving_edge_gates"],
                "minimum_trade_count_gain": float(
                    config["selection_rule"]["minimum_trade_count_gain_over_L0"]
                ),
            },
        )
        count = item["windows"]["FULL_AUDIT"]["trades"]
        item["frequency"] = {
            "trades": count,
            "trade_count_gain": count / protected_trade_count - 1.0,
        }
        item["gate_results"] = gate_results
        item["eligible"] = all(gate_results.values())

    eligible = [
        name
        for name in config["body_threshold_ladder"]
        if level_results[name]["eligible"]
    ]
    selected_level = eligible[-1] if eligible else "L0_PROTECTED"
    selected = level_results[selected_level]
    fx_days = _fx_days(m5, start, end)
    for item in level_results.values():
        item["frequency"]["fx_days"] = fx_days
        item["frequency"]["trades_per_fx_day"] = item["frequency"]["trades"] / fx_days
    selected_gain = selected["frequency"]["trade_count_gain"]
    status = (
        "BODY_FILTER_WIDENED_WITH_HISTORICAL_EDGE_PRESERVED_REQUIRES_FRESH_CONFIRMATION"
        if selected_level != "L0_PROTECTED"
        else "NO_SAFE_BODY_FILTER_FREQUENCY_EXPANSION"
    )
    result = {
        "schema_version": "eurusd_h4_body_frequency_ladder_result_v1",
        "frozen_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_sha256": anchor["source"]["sha256"],
        "post_hoc_developmental_not_pristine_oos": True,
        "broker_action_allowed": False,
        "data_audit": data_audit,
        "diagnostics": diagnostics,
        "levels": level_results,
        "eligible_nonbaseline_levels": [
            name for name in eligible if name != "L0_PROTECTED"
        ],
        "selected_level": selected_level,
        "selected_trade_count_gain": selected_gain,
        "status": status,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    level_ledgers[selected_level].to_csv(
        output_dir / "SELECTED_TRADES.csv", index=False, lineterminator="\n"
    )
    pd.DataFrame(
        [
            {
                "level": name,
                "eligible": item["eligible"],
                **item["thresholds"],
                **item["windows"]["FULL_AUDIT"],
                "trade_count_gain": item["frequency"]["trade_count_gain"],
                "extra_0p5pip_profit_factor": item["scenarios"]["COST_PLUS_0P5_PIP"][
                    "profit_factor"
                ],
                "latest_12_month_profit_factor": item["windows"]["LATEST_12_MONTHS"][
                    "profit_factor"
                ],
            }
            for name, item in level_results.items()
        ]
    ).to_csv(output_dir / "LEVELS.csv", index=False, lineterminator="\n")
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (package_root / "EURUSD_H4_BODY_FREQUENCY_LADDER_RESULT_2026_07_30.md").write_text(
        _render_report(result),
        encoding="utf-8",
        newline="\n",
    )
    return result
