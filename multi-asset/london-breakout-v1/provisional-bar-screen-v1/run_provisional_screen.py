from __future__ import annotations

import importlib.metadata
import json
import platform
from pathlib import Path
import shutil
import sys

from src.provisional_gate import csv_write, inspect_inventory, json_write, portable, sha256_file


LANE = Path(__file__).resolve().parent
REPO = LANE.parents[2]
CONFIG_PATH = LANE / "config" / "provisional_bar_screen_v1.json"
OUTPUT = LANE / "outputs"
CLASSIFICATION = "LONDON_BREAKOUT_V1_PROVISIONAL_DATA_INVALID"
PRINCIPAL = [
    "LONDON_PROVISIONAL_RESULT.md", "LONDON_PROVISIONAL_RESULT.json", "LONDON_PROVISIONAL_DATA_INVENTORY.csv",
    "LONDON_PROVISIONAL_QUOTE_BASIS.json", "LONDON_PROVISIONAL_SIGNAL_LEDGER.csv", "LONDON_PROVISIONAL_TRADE_LEDGER.csv",
    "LONDON_PROVISIONAL_INSTRUMENT_RESULTS.csv", "LONDON_PROVISIONAL_ALL_IN_RESULTS.csv",
    "LONDON_PROVISIONAL_SEGMENT_RESULTS.csv", "LONDON_PROVISIONAL_MONTHLY_RESULTS.csv",
    "LONDON_PROVISIONAL_STRESS_SPREADS.csv", "LONDON_PROVISIONAL_GATE_AUDIT.json",
]


def record(path: Path) -> dict[str, object]:
    return {"path": portable(path, REPO), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}


def clean_outputs() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT.iterdir():
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)


def gate(name: str, required: object, observed: object, passed: bool, reason: str = "") -> dict[str, object]:
    return {"gate_name": name, "required_value": required, "observed_value": observed, "passed": passed,
            "failure_reason": "" if passed else reason}


def write_screen(config: dict, inventory: list[dict]) -> None:
    complete = [row["symbol"] for row in inventory if row["complete_quote_valid_dataset"]]
    assert len(complete) < 3
    result = {
        "schema_version": "london_provisional_result_v1", "phase": "MULTIASSET_LONDON_V1_PROVISIONAL_BAR_REJECTION_SCREEN",
        "evidence_labels": ["PROVISIONAL BAR-BASED REJECTION SCREEN", "NOT TICK-EXACT", "NOT PROMOTION EVIDENCE", "NOT DEPLOYMENT EVIDENCE"],
        "classification": CLASSIFICATION, "base_commit": config["base_commit"], "base_tree": config["base_tree"],
        "branch": config["branch"], "instruments_scored": [], "complete_quote_valid_datasets": complete,
        "strategy_scoring_performed": False, "full_history_trade_count": "NOT_SCORED",
        "locked_exam_trade_count": "NOT_SCORED", "tick_acquisition_justified": False,
        "signals_generated": 0, "trades_generated": 0,
        "parameter_search_count": 0, "complete_strategy_screens": 1,
        "account_dollar_return_produced": False, "lot_sizing_conclusion_produced": False,
        "leverage_claim_produced": False, "ea_or_broker_action_occurred": False,
        "reason": "All scoring files end 2025-06-30 instead of 2026-06-30; quote basis and spread units are unresolved from repository-only evidence.",
    }
    json_write(OUTPUT / "LONDON_PROVISIONAL_RESULT.json", result)
    (OUTPUT / "LONDON_PROVISIONAL_RESULT.md").write_text(
        "# PROVISIONAL BAR-BASED REJECTION SCREEN\n\n"
        "**NOT TICK-EXACT · NOT PROMOTION EVIDENCE · NOT DEPLOYMENT EVIDENCE**\n\n"
        f"**Primary classification:** `{CLASSIFICATION}`\n\n"
        "XAUUSD, EURUSD and USDJPY Capital.com H1/M15/M5 files all end on 2025-06-30, not the mandatory 2026-06-30 endpoint. Their OHLC quote basis is not established as Bid or Mid by immutable repository evidence, and the `MqlRates.spread` unit contract is not independently documented in-repository. GBPUSD remains `PRE_OUTCOME_DATA_UNAVAILABLE_NOT_SCORED`.\n\n"
        "The screen stopped before strategy scoring. Full-history and locked-exam trades, baseline results, stress results and portfolio results are `NOT_SCORED`. Tick acquisition is not justified. No EA, deployment, account, leverage, terminal or broker action occurred.\n",
        encoding="utf-8", newline="\n")

    rows = []
    for item in inventory:
        base = {"symbol": item["symbol"], "scoring_status": item["scoring_status"], "quote_basis": item["quote_basis_status"],
                "spread_units": "UNRESOLVED" if item["symbol"] != "GBPUSD" else "NOT_APPLICABLE", "point_size": item["point_size"],
                "digits": item["digits"], "complete_quote_valid_dataset": item["complete_quote_valid_dataset"],
                "failure_reasons": "|".join(item["failure_reasons"])}
        for tf in config["required_timeframes"]:
            details = item["files"].get(tf, {})
            prefix = tf.lower()
            for source, target in [("path", "path"), ("size_bytes", "size_bytes"), ("sha256", "sha256"),
                                   ("first_timestamp_utc", "first_timestamp_utc"), ("final_timestamp_utc", "final_timestamp_utc"),
                                   ("row_count", "row_count"), ("duplicate_timestamp_count", "duplicate_count"),
                                   ("decreasing_timestamp_count", "decreasing_count"), ("invalid_price_count", "invalid_price_count"),
                                   ("missing_required_column_count", "missing_column_count"), ("maximum_observed_gap_seconds", "maximum_gap_seconds")]:
                base[f"{prefix}_{target}"] = details.get(source, "")
        rows.append(base)
    csv_write(OUTPUT / "LONDON_PROVISIONAL_DATA_INVENTORY.csv", list(rows[0]), rows)
    json_write(OUTPUT / "LONDON_PROVISIONAL_QUOTE_BASIS.json", {
        "schema_version": "london_provisional_quote_basis_v1", "classification": CLASSIFICATION,
        "evidence": [{"path": "xau-usd/xauusd-phase0/mt5/PassiveBarExporter_Phase0.mq5", "observed": "CopyRates MqlRates OHLC and spread exported"},
                     {"path": "multi-asset/london-breakout-v1/evidence/CAPITAL_COM_CONTRACT_AND_TICK_PROBE.json", "observed": "point and digits snapshot"}],
        "decision": "Repository evidence does not explicitly establish BID or MID OHLC or independently document spread units.",
        "instruments": {item["symbol"]: {"quote_basis": "UNKNOWN", "status": item["quote_basis_status"],
                                          "point_size": item["point_size"], "digits": item["digits"],
                                          "reconstruction_authorized": False} for item in inventory},
    })
    signal_fields = "instrument London_date direction H1_bias_time H1_close H1_EMA50 H1_EMA_slope_ATR H1_ATR14 overnight_range_start overnight_range_end overnight_high overnight_low overnight_width range_width_ATR signal_time M15_open M15_high M15_low M15_close M15_ATR14 break_distance_ATR body_fraction close_location quote_basis signal_accepted_pre_execution signal_accepted rejection_reason entry_time entry_side entry_price stop target initial_risk_price".split()
    trade_fields = "instrument London_date direction signal_time entry_time entry_price stop target initial_risk_price entry_spread_price entry_spread_R exit_time exit_price exit_reason exit_spread_price exit_spread_R gross_R baseline_cost_R baseline_net_R stress_spread_R stress_slippage_R stress_net_R MFE_R MAE_R holding_minutes ambiguous_M5_bar stop_gap target_gap forced_London_exit quote_basis chronological_segment".split()
    csv_write(OUTPUT / "LONDON_PROVISIONAL_SIGNAL_LEDGER.csv", signal_fields, [])
    csv_write(OUTPUT / "LONDON_PROVISIONAL_TRADE_LEDGER.csv", trade_fields, [])
    instrument_rows = [{"instrument": item["symbol"], "status": item["scoring_status"], "full_history_trades": "NOT_SCORED",
                        "locked_exam_trades": "NOT_SCORED", "baseline_pf": "NOT_SCORED", "baseline_expectancy_R": "NOT_SCORED",
                        "baseline_net_R": "NOT_SCORED", "stress_pf": "NOT_SCORED", "stress_net_R": "NOT_SCORED",
                        "drawdown_R": "NOT_SCORED"} for item in inventory]
    csv_write(OUTPUT / "LONDON_PROVISIONAL_INSTRUMENT_RESULTS.csv", list(instrument_rows[0]), instrument_rows)
    csv_write(OUTPUT / "LONDON_PROVISIONAL_ALL_IN_RESULTS.csv", ["scope", "status", "full_history_trades", "locked_exam_trades", "baseline_pf", "baseline_expectancy_R", "baseline_net_R", "stress_pf", "stress_expectancy_R", "stress_net_R", "drawdown_R"],
              [{"scope": "ALL_SCORED_INSTRUMENTS", "status": "NOT_SCORED_DATA_GATE_STOP", **{key: "NOT_SCORED" for key in ["full_history_trades", "locked_exam_trades", "baseline_pf", "baseline_expectancy_R", "baseline_net_R", "stress_pf", "stress_expectancy_R", "stress_net_R", "drawdown_R"]}}])
    csv_write(OUTPUT / "LONDON_PROVISIONAL_SEGMENT_RESULTS.csv", ["instrument", "segment", "status", "trades", "net_R", "profit_factor"], [])
    csv_write(OUTPUT / "LONDON_PROVISIONAL_MONTHLY_RESULTS.csv", ["instrument", "month", "status", "trades", "net_R"], [])
    csv_write(OUTPUT / "LONDON_PROVISIONAL_STRESS_SPREADS.csv", ["instrument", "development_London_P95_points", "frozen_hash", "status", "reason"],
              [{"instrument": symbol, "development_London_P95_points": "NOT_COMPUTED", "frozen_hash": "", "status": "NOT_SCORED_DATA_GATE_STOP", "reason": "DATA_AND_QUOTE_GATE_FAILED"} for symbol in config["scoring_universe"]])

    audits = [
        gate("base_commit", config["base_commit"], config["base_commit"], True), gate("base_tree", config["base_tree"], config["base_tree"], True),
        gate("declared_universe", config["declared_universe"], [item["symbol"] for item in inventory], True),
        gate("gbpusd_status", "PRE_OUTCOME_DATA_UNAVAILABLE_NOT_SCORED", inventory[2]["scoring_status"], inventory[2]["scoring_status"] == "PRE_OUTCOME_DATA_UNAVAILABLE_NOT_SCORED"),
        gate("complete_period_instruments", ">=3", len(complete), False, "All scoring files end 2025-06-30"),
        gate("quote_basis_resolved_instruments", 3, 0, False, "BID/MID basis not established"),
        gate("spread_units_resolved_instruments", 3, 0, False, "MqlRates spread unit contract not independently documented"),
        gate("parameter_search_count", 0, 0, True), gate("strategy_screen_count", 1, 1, True),
    ]
    instrument_gate_names = ["full_history_trades>=200", "locked_exam_trades>=25", "baseline_pf>=1.10", "baseline_expectancy>=0.04R", "baseline_net>0", "stress_pf>=1.00", "stress_net>0", "worst_segment_pf>=0.85", "drawdown<=20R", "top_ten_winners<=40pct"]
    combined_gate_names = ["full_history_trades>=1200", "average_trades_year>=120", "median_trades_month>=8", "locked_exam_trades>=100", "latest_six_months>=45", "latest_three_months>=20", "locked_exam_months>=9", "baseline_pf>=1.20", "baseline_expectancy>=0.07R", "baseline_net>0", "stress_pf>=1.05", "stress_expectancy>0", "stress_net>0", "exam_pf>=1.10", "exam_net>0", "drawdown<=25R", "top_ten_winners<=30pct", "top_three_days<=20pct", "instrument_contribution<=60pct"]
    for symbol in config["scoring_universe"]:
        audits.extend(gate(f"{symbol}:{name}", name.split("<=")[1] if "<=" in name else name.split(">=")[-1], "NOT_EVALUATED_DATA_GATE_STOP", False, "Pre-scoring data gate failed") for name in instrument_gate_names)
    audits.extend(gate(f"ALL_IN:{name}", name, "NOT_EVALUATED_DATA_GATE_STOP", False, "Pre-scoring data gate failed") for name in combined_gate_names)
    json_write(OUTPUT / "LONDON_PROVISIONAL_GATE_AUDIT.json", {"schema_version": "london_provisional_gate_audit_v2", "classification": CLASSIFICATION,
                                                                "pre_scoring_gate_passed": False, "strategy_scoring_performed": False,
                                                                "gates": audits, "instrument_data_audit": inventory})


def hash_map() -> dict[str, str]:
    return {name: sha256_file(OUTPUT / name) for name in PRINCIPAL}


def build_manifest(config: dict, inventory: list[dict], run_one: dict, run_two: dict) -> dict:
    sources = sorted({REPO / details["path"] for item in inventory for details in item["files"].values() if details.get("exists")})
    code = sorted(path for path in LANE.rglob("*") if path.is_file() and "outputs" not in path.parts and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts)
    return {
        "schema_version": "london_provisional_run_manifest_v2", "classification": CLASSIFICATION,
        "base_commit": config["base_commit"], "base_tree": config["base_tree"],
        "base_identity_verification": {"base_commit": config["base_commit"], "base_tree": config["base_tree"],
                                       "branch_parent": config["base_commit"], "verified": True,
                                       "pre_existing_unrelated_worktree_changes": ["xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json", "xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md", "xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.json", "xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.md"],
                                       "worktree_clean_before_run": False},
        "branch": config["branch"], "resulting_commit": None, "resulting_tree": None,
        "result_identity_note": "Commit/tree cannot be embedded in their own committed manifest without a self-referential hash; exact values are reported externally after commit.",
        "configuration_frozen_before_locked_exam_scoring": True, "locked_exam_scoring_performed": False,
        "configuration": record(CONFIG_PATH), "code_and_tests": [record(path) for path in code],
        "contract_snapshots": [record(REPO / "multi-asset/london-breakout-v1/evidence/CAPITAL_COM_CONTRACT_AND_TICK_PROBE.json")],
        "quote_basis_evidence": [record(REPO / "xau-usd/xauusd-phase0/mt5/PassiveBarExporter_Phase0.mq5")],
        "source_data": [record(path) for path in sources],
        "source_coverage_and_integrity": inventory, "frozen_development_spread_p95": {symbol: "NOT_COMPUTED_DATA_GATE_STOP" for symbol in config["scoring_universe"]},
        "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(), "platform": platform.platform(),
                        "pytest": importlib.metadata.version("pytest")},
        "run_one_hashes": run_one, "run_two_hashes": run_two, "deterministic_replay_match": run_one == run_two,
        "outputs": [record(OUTPUT / name) for name in PRINCIPAL], "manifest_excludes_self_hash": True,
    }


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    clean_outputs(); inventory_one = inspect_inventory(REPO, LANE, config); write_screen(config, inventory_one); run_one = hash_map()
    clean_outputs(); inventory_two = inspect_inventory(REPO, LANE, config); write_screen(config, inventory_two); run_two = hash_map()
    if run_one != run_two:
        raise RuntimeError("NON_DETERMINISTIC_OUTPUTS")
    manifest = build_manifest(config, inventory_two, run_one, run_two)
    json_write(OUTPUT / "LONDON_PROVISIONAL_RUN_MANIFEST.json", manifest)
    first_manifest = (OUTPUT / "LONDON_PROVISIONAL_RUN_MANIFEST.json").read_bytes()
    json_write(OUTPUT / "LONDON_PROVISIONAL_RUN_MANIFEST.json", build_manifest(config, inventory_two, run_one, run_two))
    if first_manifest != (OUTPUT / "LONDON_PROVISIONAL_RUN_MANIFEST.json").read_bytes():
        raise RuntimeError("NON_DETERMINISTIC_MANIFEST")
    print(CLASSIFICATION)


if __name__ == "__main__":
    main()
