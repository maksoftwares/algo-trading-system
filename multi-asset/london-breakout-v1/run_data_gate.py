from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


LANE = Path(__file__).resolve().parent
REPO = LANE.parents[1]
SRC = LANE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_gate import capture_mt5_snapshot, evaluate_data_gate, portable, sha256_file  # noqa: E402


REQUIRED_OUTPUTS = (
    "LONDON_BREAKOUT_RESULT.md", "LONDON_BREAKOUT_RESULT.json", "LONDON_BREAKOUT_SIGNAL_LEDGER.csv",
    "LONDON_BREAKOUT_TRADE_LEDGER.csv", "LONDON_BREAKOUT_INSTRUMENT_RESULTS.csv",
    "LONDON_BREAKOUT_PORTFOLIO_RESULTS.csv", "LONDON_BREAKOUT_CHRONOLOGICAL_SEGMENTS.csv",
    "LONDON_BREAKOUT_MONTHLY_RESULTS.csv", "LONDON_BREAKOUT_ROLLING_RESULTS.csv",
    "LONDON_BREAKOUT_CORRELATION.csv", "LONDON_BREAKOUT_ACCOUNT_FEASIBILITY.csv",
    "LONDON_BREAKOUT_GATE_AUDIT.json", "LONDON_BREAKOUT_RUN_MANIFEST.json",
)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def file_item(path: Path) -> dict[str, Any]:
    return {"path": portable(path, REPO), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}


def report(result: dict[str, Any]) -> str:
    lines = [
        "# Multi-Asset London Range Expansion Fast Discovery V1", "",
        f"- Branch: `{result['branch']}`", f"- Base: `{result['base_commit']}`", f"- Base tree: `{result['base_tree']}`",
        f"- Classification: `{result['classification']}`", "- Strategy scoring performed: `false`", "- Parameter search count: `0`", "",
        "## Mandatory pre-scoring gate", "",
        f"Complete trustworthy instruments: `{result['complete_trustworthy_instruments']}` / `{result['minimum_required_instruments']}`.", "",
        "| Instrument | H1 | M15 | M5 | Historical execution source | Earliest terminal tick returned | Trustworthy full period |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["data_readiness"]:
        lines.append(f"| {row['symbol']} | {row['h1_file_present']} | {row['m15_file_present']} | {row['m5_file_present']} | {row['repository_execution_source']} | {row['first_terminal_tick_utc'] or 'none'} | {row['complete_trustworthy_execution_data']} |")
    lines.extend([
        "", "The existing historical bars contain OHLC plus one spread field, not raw executable Bid/Ask ticks. The connected terminal does not supply ticks back to 2016-07-01, and GBPUSD has no repository Capital.com bar set. Under the frozen authorization, bar-spread reconstruction is insufficient for promotion and fewer than three trustworthy instruments requires stopping before strategy scoring.", "",
        "## Disposition", "", "No signal generation, trade replay, parameter search, instrument selection, economic scoring or portfolio construction was performed. No EA, deployment, demo/live execution, broker order or risk increase is authorized.",
    ])
    return "\n".join(lines) + "\n"


def run(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir = REPO / config["output_dir"]; evidence_dir = REPO / config["evidence_dir"]
    output_dir.mkdir(parents=True, exist_ok=True); evidence_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = evidence_dir / "CAPITAL_COM_CONTRACT_AND_TICK_PROBE.json"
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    else:
        snapshot = capture_mt5_snapshot(config); write_json(snapshot_path, snapshot)
    readiness = evaluate_data_gate(REPO, config, snapshot)
    complete = sum(bool(row["complete_trustworthy_execution_data"]) for row in readiness)
    minimum = int(config["data_gate"]["minimum_complete_trustworthy_instruments"])
    if complete >= minimum:
        raise RuntimeError("Pre-scoring gate unexpectedly passed; strategy scoring is not implemented in this data-audit runner")
    classification = "LONDON_BREAKOUT_V1_DATA_INADEQUATE_NO_SCORING"
    gate = {
        "schema_version": "london_breakout_gate_audit_v1", "classification": classification,
        "complete_trustworthy_instruments": complete, "minimum_required_instruments": minimum,
        "at_least_three_complete_trustworthy_data": False,
        "contract_feasibility_evaluated": False, "strategy_scoring_performed": False,
        "parameter_search_count": 0, "pre_scoring_gate_passed": False,
        "stop_reasons": ["FEWER_THAN_THREE_INSTRUMENTS_HAVE_COMPLETE_TRUSTWORTHY_EXECUTION_DATA"],
    }
    result = {
        "schema_version": "london_breakout_result_v1", "branch": config["branch"], "base_commit": config["base_commit"],
        "base_tree": config["base_tree"], "classification": classification,
        "requested_period": [config["requested_start"], config["requested_end_exclusive"]],
        "complete_trustworthy_instruments": complete, "minimum_required_instruments": minimum,
        "strategy_scoring_performed": False, "parameter_search_count": 0,
        "portfolio_admitted_instruments": [], "data_readiness": readiness,
        "gate_audit": gate, "deployment_authorized": False,
    }
    paths = {name: output_dir / name for name in REQUIRED_OUTPUTS}
    write_json(paths["LONDON_BREAKOUT_RESULT.json"], result)
    paths["LONDON_BREAKOUT_RESULT.md"].write_text(report(result), encoding="utf-8", newline="\n")
    write_json(paths["LONDON_BREAKOUT_GATE_AUDIT.json"], gate)
    signal_fields = ["symbol", "london_date", "signal_time", "direction", "signal_accepted", "rejection_reason"]
    trade_fields = ["symbol", "entry_time", "exit_time", "direction", "net_r", "stress_net_r", "exit_reason"]
    write_csv(paths["LONDON_BREAKOUT_SIGNAL_LEDGER.csv"], signal_fields, [])
    write_csv(paths["LONDON_BREAKOUT_TRADE_LEDGER.csv"], trade_fields, [])
    write_csv(paths["LONDON_BREAKOUT_INSTRUMENT_RESULTS.csv"], ["symbol", "scoring_status", "trades", "profit_factor", "expectancy_r", "net_r"], [{"symbol": symbol, "scoring_status": "NOT_SCORED_DATA_GATE_STOP", "trades": 0} for symbol in config["symbols"]])
    write_csv(paths["LONDON_BREAKOUT_PORTFOLIO_RESULTS.csv"], ["scoring_status", "admitted_instruments", "trades", "profit_factor", "expectancy_r", "net_r"], [{"scoring_status": "NOT_SCORED_DATA_GATE_STOP", "admitted_instruments": 0, "trades": 0}])
    write_csv(paths["LONDON_BREAKOUT_CHRONOLOGICAL_SEGMENTS.csv"], ["segment", "start", "end_exclusive", "scoring_status", "trades"], [
        {"segment": "DEVELOPMENT", "start": config["requested_start"], "end_exclusive": config["development_end_exclusive"], "scoring_status": "NOT_SCORED_DATA_GATE_STOP", "trades": 0},
        {"segment": "VALIDATION", "start": config["development_end_exclusive"], "end_exclusive": config["validation_end_exclusive"], "scoring_status": "NOT_SCORED_DATA_GATE_STOP", "trades": 0},
        {"segment": "LOCKED_EXAM", "start": config["locked_exam_start"], "end_exclusive": config["requested_end_exclusive"], "scoring_status": "NOT_SCORED_DATA_GATE_STOP", "trades": 0},
    ])
    write_csv(paths["LONDON_BREAKOUT_MONTHLY_RESULTS.csv"], ["month", "scoring_status", "trades", "net_r"], [])
    write_csv(paths["LONDON_BREAKOUT_ROLLING_RESULTS.csv"], ["window_months", "start", "end_exclusive", "scoring_status", "trades", "net_r"], [])
    write_csv(paths["LONDON_BREAKOUT_CORRELATION.csv"], ["symbol_a", "symbol_b", "scoring_status", "daily_r_correlation"], [])
    account_rows = []
    for symbol in config["symbols"]:
        contract = snapshot["symbols"].get(symbol, {})
        account_rows.append({
            "symbol": symbol, "exact_mt5_symbol": contract.get("exact_symbol_name"), "volume_min": contract.get("volume_min"),
            "volume_step": contract.get("volume_step"), "contract_size": contract.get("contract_size"),
            "margin_usd_min_volume_at_capture": contract.get("order_calc_margin_usd_min_volume"),
            "total_loss_feasibility_status": "NOT_EVALUATED_DATA_GATE_STOP", "sizing_rejection_pct": "",
        })
    write_csv(paths["LONDON_BREAKOUT_ACCOUNT_FEASIBILITY.csv"], ["symbol", "exact_mt5_symbol", "volume_min", "volume_step", "contract_size", "margin_usd_min_volume_at_capture", "total_loss_feasibility_status", "sizing_rejection_pct"], account_rows)
    readiness_path = output_dir / "LONDON_BREAKOUT_DATA_READINESS.csv"
    write_csv(readiness_path, ["symbol", "exact_mt5_symbol", "contract_available", "h1_file_present", "m15_file_present", "m5_file_present", "repository_execution_source", "repository_bid_ask_promotion_grade", "first_terminal_tick_utc", "full_period_terminal_ticks_complete", "complete_trustworthy_execution_data", "contract_expressibility_status", "data_stop_reason"], readiness)

    source_paths = []
    for row in readiness:
        for item in row["bar_files"].values():
            if item.get("exists"):
                source_paths.append(REPO / item["path"])
    code_paths = [LANE / ".gitattributes", LANE / ".gitignore", LANE / "README.md", Path(__file__).resolve(), *sorted((LANE / "src").glob("*.py")), *sorted((LANE / "tests").glob("*.py"))]
    output_paths = [path for name, path in paths.items() if name != "LONDON_BREAKOUT_RUN_MANIFEST.json"] + [readiness_path]
    manifest = {
        "schema_version": "london_breakout_run_manifest_v1", "branch": config["branch"], "base_commit": config["base_commit"], "base_tree": config["base_tree"],
        "classification": classification, "config": file_item(config_path), "contract_and_tick_probe": file_item(snapshot_path),
        "code_and_tests": [file_item(path) for path in sorted(set(code_paths))],
        "source_data": [file_item(path) for path in sorted(set(source_paths))],
        "outputs": [file_item(path) for path in sorted(set(output_paths))],
        "manifest_excludes_itself_to_avoid_recursive_hashing": True,
    }
    serialized = json.dumps(manifest, sort_keys=True)
    if str(REPO) in serialized or "\\" in serialized:
        raise RuntimeError("Manifest contains a non-portable machine path")
    write_json(paths["LONDON_BREAKOUT_RUN_MANIFEST.json"], manifest)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", required=True, type=Path); args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else REPO / args.config
    print(json.dumps(run(config_path), indent=2, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
