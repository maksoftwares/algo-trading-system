from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


@dataclass(frozen=True)
class RiskAuditArtifacts:
    result: dict[str, Any]
    windows: pd.DataFrame
    decisions: pd.DataFrame


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def account_sizing(drawdown: float, account: Mapping[str, Any]) -> dict[str, Any]:
    equity = float(account["current_equity_dollars"])
    limit = float(account["maximum_equity_drawdown_fraction"])
    buffer = float(account["capital_safety_buffer_multiple"])
    lot = float(account["reference_lot"])
    allowed = equity * limit
    buffered_drawdown = drawdown * buffer
    maximum_lot = lot * allowed / buffered_drawdown
    minimum_equity = buffered_drawdown / limit
    broker_minimum = float(account["broker_minimum_lot"])
    fits = buffered_drawdown <= allowed and broker_minimum <= maximum_lot
    return {
        "current_equity_dollars": equity,
        "maximum_allowed_drawdown_dollars": allowed,
        "exact_stress_drawdown_dollars": drawdown,
        "unbuffered_drawdown_fraction": drawdown / equity,
        "buffered_drawdown_dollars": buffered_drawdown,
        "buffered_drawdown_fraction": buffered_drawdown / equity,
        "buffered_minimum_equity_dollars": minimum_equity,
        "capital_reserve_above_buffered_minimum_dollars": equity - minimum_equity,
        "maximum_lot_at_current_equity_with_buffer": maximum_lot,
        "broker_minimum_lot": broker_minimum,
        "broker_lot_step": float(account["broker_lot_step"]),
        "broker_can_express_safe_lot": broker_minimum <= maximum_lot,
        "r1_lane_fits_buffered_drawdown_gate": fits,
    }


def _control(config: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **config["target"],
        "maximum_concurrent_positions": int(policy["maximum_concurrent_positions"]),
        "maximum_entries_per_utc_day": int(policy["maximum_entries_per_utc_day"]),
    }


def run_audit(config: Mapping[str, Any], repo_root: Path) -> RiskAuditArtifacts:
    v43_path = repo_root / config["sources"]["v43_audit_module"]["path"]
    v43 = load_module(v43_path, "xau_historical_core_drawdown_v43_for_v50")
    source_audit = v43.verify_sources(repo_root, config["sources"], external=False)
    external_audit = v43.verify_sources(
        repo_root, config["external_sources"], external=True
    )
    ledger = v43.load_ledger(
        repo_root / config["sources"]["normalized_core_ledger"]["path"]
    )
    policy_frames: dict[str, pd.DataFrame] = {"ORIGINAL": ledger}
    decision_frames: list[pd.DataFrame] = []
    for policy_id, policy in config["comparison_policies"].items():
        capped, decisions = v43.apply_frozen_r1_cap(ledger, _control(config, policy))
        policy_frames[policy_id] = capped
        decisions = decisions.copy()
        decisions.insert(0, "policy_id", policy_id)
        decision_frames.append(decisions)

    cutoff = pd.Timestamp(config["cutoff_exclusive_utc"])
    rows: list[dict[str, Any]] = []
    for window, start_text in config["windows"].items():
        start = pd.Timestamp(start_text)
        for policy_id, frame in policy_frames.items():
            rows.append(
                {
                    "window": window,
                    **v43.window_metrics(frame, start, cutoff, policy_id),
                }
            )
    windows = pd.DataFrame(rows)

    portability = v43._load_portability_module(
        Path(source_audit["r1_portability_module"]["path"])
    )
    portability_config = json.loads(
        Path(source_audit["r1_portability_config"]["path"]).read_text(encoding="utf-8")
    )
    portability_run = portability.run_portability(portability_config)
    single = config["comparison_policies"]["V50_SINGLE_POSITION"]
    policy_trades = portability.BASE.apply_policy(
        portability_run.all_trades,
        "V50_SINGLE_POSITION",
        single,
    )
    base_m5 = v43.mark_portability_policy(
        policy_trades,
        portability_run.source_m5,
        portability_config["execution"],
        stress=False,
    )
    stress_m5 = v43.mark_portability_policy(
        policy_trades,
        portability_run.source_m5,
        portability_config["execution"],
        stress=True,
    )
    peak_ticks = v43.load_dukascopy_hour(
        Path(external_audit["exact_peak_hour"]["path"])
    )
    trough_ticks = v43.load_dukascopy_hour(
        Path(external_audit["exact_trough_hour"]["path"])
    )
    base_exact = v43.exact_tick_drawdown(
        peak_ticks,
        trough_ticks,
        policy_trades,
        portability_config["execution"],
        stress=False,
    )
    stress_exact = v43.exact_tick_drawdown(
        peak_ticks,
        trough_ticks,
        policy_trades,
        portability_config["execution"],
        stress=True,
    )
    if pd.Timestamp(stress_m5["peak_bar_start_utc"]).floor("h") != pd.Timestamp(
        stress_exact["peak_time_utc"]
    ).floor("h"):
        raise ValueError("Exact peak hour does not match global M5 stress peak")
    if pd.Timestamp(stress_m5["trough_bar_start_utc"]).floor("h") != pd.Timestamp(
        stress_exact["trough_time_utc"]
    ).floor("h"):
        raise ValueError("Exact trough hour does not match global M5 stress trough")

    sizing = account_sizing(
        float(stress_exact["maximum_drawdown_dollars"]),
        config["account_reference"],
    )
    one_year = windows.loc[windows["window"].eq("1Y")].set_index("policy")
    single_one_year = one_year.loc["V50_SINGLE_POSITION"]
    two_one_year = one_year.loc["V43_TWO_POSITION"]
    pass_pf = float(single_one_year["profit_factor"]) >= float(
        config["gates"]["minimum_one_year_profit_factor"]
    )
    pass_closed_dd = float(single_one_year["closed_drawdown_dollars"]) < float(
        two_one_year["closed_drawdown_dollars"]
    )
    lane_pass = bool(
        sizing["r1_lane_fits_buffered_drawdown_gate"] and pass_pf and pass_closed_dd
    )
    result = {
        "schema_version": config["schema_version"],
        "decision": (
            "V50_SINGLE_R1_EXPOSURE_RISK_GATE_PASS"
            if lane_pass
            else "V50_SINGLE_R1_EXPOSURE_RISK_GATE_FAIL"
        ),
        "source_audit": source_audit,
        "external_source_audit": external_audit,
        "policy": {
            "specialist_id": config["target"]["specialist_id"],
            "source_strategy": config["target"]["source_strategy"],
            "maximum_concurrent_positions": int(single["maximum_concurrent_positions"]),
            "maximum_entries_per_utc_day": int(single["maximum_entries_per_utc_day"]),
            "selection_basis": "SMALLEST_NONZERO_BROKER_EXPRESSIBLE_EXPOSURE",
            "parameter_search_count": 0,
        },
        "one_year_comparison": {
            policy: {
                "trades": int(row["trades"]),
                "trades_per_weekday": float(row["trades_per_weekday"]),
                "net_pnl_dollars": float(row["net_pnl_dollars"]),
                "profit_factor": float(row["profit_factor"]),
                "closed_drawdown_dollars": float(row["closed_drawdown_dollars"]),
            }
            for policy, row in one_year.iterrows()
        },
        "independent_dukascopy_single_position": {
            "trades": int(len(policy_trades)),
            "base_m5_conservative": base_m5,
            "stress_m5_conservative": stress_m5,
            "base_exact_tick": base_exact,
            "stress_exact_tick": stress_exact,
        },
        "account_sizing": sizing,
        "gates": {
            "buffered_drawdown_gate_pass": bool(
                sizing["r1_lane_fits_buffered_drawdown_gate"]
            ),
            "one_year_profit_factor_gate_pass": pass_pf,
            "closed_drawdown_improvement_gate_pass": pass_closed_dd,
            "all_r1_lane_gates_pass": lane_pass,
        },
        "required_controls": {
            "r1_box_maximum_concurrent_positions": 1,
            "r1_box_maximum_entries_per_utc_day": 1,
            "reject_any_second_r1_box_entry_while_first_is_open": True,
            "retain_15_percent_account_drawdown_ceiling": True,
            "retain_25_percent_capital_buffer": True,
            "retain_sealed_shared_account_forward_gate": True,
            "demo_or_live_activation_authorized": False,
        },
        "limitations": {
            "diagnostic_after_outcome_observation": True,
            "full_historical_core_floating_curve_reconstructed": False,
            "r1_lane_pass_does_not_equal_whole_account_readiness": True,
            "sealed_forward_shared_account_evidence_required": True,
        },
        "research_controls": config["research_controls"],
    }
    result["result_sha256"] = v43.canonical_sha256(result)
    decisions = pd.concat(decision_frames, ignore_index=True)
    return RiskAuditArtifacts(result, windows, decisions)
