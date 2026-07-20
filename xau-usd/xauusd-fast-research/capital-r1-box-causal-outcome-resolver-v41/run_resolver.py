from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from resolver import (  # noqa: E402
    append_resolution_records,
    atomic_write_json,
    latest_observed_timestamp_ms,
    load_config,
    load_tick_snapshots,
    parse_candidate_snapshot,
    process_candidates,
    read_json,
    read_resolution_ledger,
    select_tick_paths,
    sha256_bytes,
    stable_line_prefix,
    utc_text,
    validate_frozen_identity,
    validate_historical_parity_artifact,
    verify_candidate_status,
    verify_contract,
    verify_prefix,
)


def run_cycle(
    repo_root: Path = REPO_ROOT,
    package_root: Path = ROOT,
    *,
    now: pd.Timestamp | None = None,
) -> dict[str, Any]:
    config = load_config(
        package_root / "config" / "capital_r1_box_causal_outcome_resolver_v41.json"
    )
    contract = verify_contract(config, repo_root, package_root)
    validate_frozen_identity(config, repo_root)
    validate_historical_parity_artifact(config, contract, package_root)
    current = (
        pd.Timestamp.now(tz="UTC")
        if now is None
        else pd.Timestamp(now).tz_convert("UTC")
    )
    source = config["source"]
    outputs = config["outputs"]
    candidate_runtime = Path(source["candidate_runtime_directory"])
    source_status = verify_candidate_status(
        candidate_runtime / source["candidate_status_filename"], config
    )
    candidate_path = candidate_runtime / source["candidate_filename"]
    candidate_snapshot = stable_line_prefix(candidate_path)

    runtime = Path(outputs["runtime_directory"])
    runtime.mkdir(parents=True, exist_ok=True)
    state_path = runtime / outputs["source_prefix_state"]
    state = read_json(state_path) if state_path.is_file() else None
    verify_prefix(
        candidate_snapshot,
        state,
        "source_prefix_bytes",
        "source_prefix_sha256",
        "candidate source",
    )
    candidates = parse_candidate_snapshot(candidate_snapshot, config)
    if int(source_status.get("candidate_count", 0)) > len(candidates):
        raise ValueError("V41 candidate snapshot is behind the R1 source status")

    ledger_path = runtime / outputs["resolution_ledger"]
    ledger_snapshot = stable_line_prefix(ledger_path)
    verify_prefix(
        ledger_snapshot,
        state,
        "resolution_prefix_bytes",
        "resolution_prefix_sha256",
        "resolution ledger",
    )
    existing = read_resolution_ledger(ledger_path)
    existing_ids = {str(row["candidate_id"]) for row in existing}
    unresolved = [
        row for row in candidates if str(row["candidate_id"]) not in existing_ids
    ]

    all_tick_paths = sorted(
        Path(source["tick_directory"]).glob(source["tick_filename_glob"])
    )
    selected_paths = select_tick_paths(all_tick_paths, unresolved)
    ticks, tick_records = load_tick_snapshots(selected_paths, config)
    observed_through_ms = latest_observed_timestamp_ms(all_tick_paths, config)
    new_rows, pending = process_candidates(
        candidates,
        existing,
        ticks,
        tick_records,
        observed_through_ms,
        config,
        current,
    )
    append_resolution_records(ledger_path, new_rows)
    resolutions = read_resolution_ledger(ledger_path)
    resolution_snapshot = stable_line_prefix(ledger_path)
    prefix_state = {
        "schema_version": "xauusd_capital_r1_box_candidate_prefix_v41",
        "updated_at_utc": utc_text(current),
        "source_path": str(candidate_path.resolve()).replace("\\", "/"),
        "source_prefix_bytes": len(candidate_snapshot),
        "source_prefix_sha256": sha256_bytes(candidate_snapshot),
        "candidate_rows": len(candidates),
        "resolution_prefix_bytes": len(resolution_snapshot),
        "resolution_prefix_sha256": sha256_bytes(resolution_snapshot),
        "resolution_rows": len(resolutions),
        "contract_sha256": str(contract["contract_sha256"]),
    }
    atomic_write_json(state_path, prefix_state)

    executed = sum(str(row["resolution_status"]) == "EXECUTED" for row in resolutions)
    rejected = sum(str(row["resolution_status"]) == "REJECTED" for row in resolutions)
    status = {
        "schema_version": "xauusd_capital_r1_box_causal_outcome_runtime_v41",
        "updated_at_utc": utc_text(current),
        "status": "ACTIVE_READ_ONLY_CAUSAL_RESOLVER",
        "account_login": int(source["account_login"]),
        "account_server": str(source["account_server"]),
        "symbol": str(source["symbol"]),
        "specialist_id": str(source["specialist_id"]),
        "contract_sha256": str(contract["contract_sha256"]),
        "source_contract_sha256": str(
            config["frozen_identity"]["source_contract_sha256"]
        ),
        "candidate_rows": len(candidates),
        "resolution_rows": len(resolutions),
        "executed_resolution_rows": int(executed),
        "rejected_resolution_rows": int(rejected),
        "unresolved_candidate_rows": int(len(candidates) - len(resolutions)),
        "new_resolution_rows_this_cycle": len(new_rows),
        "pending_reasons": pending,
        "selected_tick_files": len(selected_paths),
        "selected_unique_ticks": len(ticks),
        "quote_ledger_observed_through_utc": (
            None
            if observed_through_ms is None
            else utc_text(pd.Timestamp(observed_through_ms, unit="ms", tz="UTC"))
        ),
        "prospective_individual_outcomes_recorded": True,
        "aggregate_economics_opened": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "trade_permission": False,
        "broker_action_allowed": False,
    }
    atomic_write_json(runtime / outputs["runtime_status"], status)
    return status


def failure_status(error: Exception) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_capital_r1_box_causal_outcome_runtime_v41",
        "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "FAILED_CLOSED",
        "error": f"{type(error).__name__}: {error}",
        "prospective_individual_outcomes_recorded": False,
        "aggregate_economics_opened": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "trade_permission": False,
        "broker_action_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve frozen R1 box candidate outcomes causally"
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=None)
    args = parser.parse_args()
    config = load_config()
    poll_seconds = (
        int(config["forward"]["poll_seconds"])
        if args.poll_seconds is None
        else int(args.poll_seconds)
    )
    while True:
        try:
            status = run_cycle()
            print(json.dumps(status, sort_keys=True), flush=True)
        except Exception as exc:  # pragma: no cover
            status = failure_status(exc)
            runtime = Path(config["outputs"]["runtime_directory"])
            atomic_write_json(runtime / config["outputs"]["runtime_status"], status)
            print(json.dumps(status, sort_keys=True), flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
