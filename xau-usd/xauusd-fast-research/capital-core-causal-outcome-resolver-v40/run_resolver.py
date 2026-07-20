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
    PROCESSORS,
    STREAMS,
    append_resolution_records,
    atomic_write_json,
    latest_observed_timestamp_ms,
    load_config,
    load_tick_snapshots,
    parse_candidate_snapshot,
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


def _status_candidate_count(stream: str, status: dict[str, Any]) -> int:
    if stream == "v28":
        return sum(int(value) for value in status.get("candidate_counts", {}).values())
    if stream == "v29":
        return int(status.get("candidate_count", 0))
    return int(status.get("total_forward_candidates", 0))


def run_cycle(
    repo_root: Path = REPO_ROOT,
    package_root: Path = ROOT,
    *,
    now: pd.Timestamp | None = None,
) -> dict[str, Any]:
    config = load_config(
        package_root / "config" / "capital_core_causal_outcome_resolver_v40.json"
    )
    contract = verify_contract(config, repo_root, package_root)
    validate_frozen_identity(config, repo_root)
    validate_historical_parity_artifact(config, contract, package_root)
    current = (
        pd.Timestamp.now(tz="UTC")
        if now is None
        else pd.Timestamp(now).tz_convert("UTC")
    )
    runtime = Path(config["outputs"]["runtime_directory"])
    runtime.mkdir(parents=True, exist_ok=True)

    snapshots: dict[str, bytes] = {}
    candidates_by_stream: dict[str, list[dict[str, Any]]] = {}
    existing_by_stream: dict[str, list[dict[str, Any]]] = {}
    state_by_stream: dict[str, dict[str, Any] | None] = {}
    unresolved: list[dict[str, Any]] = []
    for stream in STREAMS:
        identity = config["frozen_identity"][stream]
        source_runtime = Path(identity["runtime_directory"])
        source_status = verify_candidate_status(
            stream, source_runtime / identity["status_filename"], config
        )
        candidate_path = source_runtime / identity["candidate_filename"]
        snapshot = stable_line_prefix(candidate_path)
        state_path = runtime / f"{stream}_prefix_state.json"
        state = read_json(state_path) if state_path.is_file() else None
        verify_prefix(
            snapshot,
            state,
            "source_prefix_bytes",
            "source_prefix_sha256",
            f"{stream} candidate source",
        )
        candidates = parse_candidate_snapshot(stream, snapshot, config)
        if _status_candidate_count(stream, source_status) > len(candidates):
            raise ValueError(f"V40 {stream} candidate snapshot is behind its status")

        ledger_path = runtime / f"{stream}_resolutions.jsonl"
        ledger_snapshot = stable_line_prefix(ledger_path)
        verify_prefix(
            ledger_snapshot,
            state,
            "resolution_prefix_bytes",
            "resolution_prefix_sha256",
            f"{stream} resolution ledger",
        )
        existing = read_resolution_ledger(ledger_path)
        existing_ids = {str(row["candidate_id"]) for row in existing}
        unresolved.extend(
            row for row in candidates if str(row["candidate_id"]) not in existing_ids
        )
        snapshots[stream] = snapshot
        candidates_by_stream[stream] = candidates
        existing_by_stream[stream] = existing
        state_by_stream[stream] = state

    source = config["source"]
    all_tick_paths = sorted(
        Path(source["tick_directory"]).glob(source["tick_filename_glob"])
    )
    selected_paths = select_tick_paths(all_tick_paths, unresolved)
    ticks, tick_records = load_tick_snapshots(selected_paths, config)
    observed_through_ms = latest_observed_timestamp_ms(all_tick_paths, config)

    status_streams: dict[str, Any] = {}
    for stream in STREAMS:
        ledger_path = runtime / f"{stream}_resolutions.jsonl"
        new_rows, pending = PROCESSORS[stream](
            candidates_by_stream[stream],
            existing_by_stream[stream],
            ticks,
            tick_records,
            observed_through_ms,
            config,
            current,
        )
        append_resolution_records(ledger_path, new_rows)
        resolutions = read_resolution_ledger(ledger_path)
        resolution_snapshot = stable_line_prefix(ledger_path)
        state = {
            "schema_version": f"xauusd_capital_core_{stream}_prefix_state_v40",
            "updated_at_utc": utc_text(current),
            "source_prefix_bytes": len(snapshots[stream]),
            "source_prefix_sha256": sha256_bytes(snapshots[stream]),
            "candidate_rows": len(candidates_by_stream[stream]),
            "resolution_prefix_bytes": len(resolution_snapshot),
            "resolution_prefix_sha256": sha256_bytes(resolution_snapshot),
            "resolution_rows": len(resolutions),
            "contract_sha256": str(contract["contract_sha256"]),
        }
        atomic_write_json(runtime / f"{stream}_prefix_state.json", state)
        status_streams[stream] = {
            "candidate_rows": len(candidates_by_stream[stream]),
            "resolution_rows": len(resolutions),
            "executed_resolution_rows": sum(
                str(row["resolution_status"]) == "EXECUTED" for row in resolutions
            ),
            "rejected_resolution_rows": sum(
                str(row["resolution_status"]) == "REJECTED" for row in resolutions
            ),
            "unresolved_candidate_rows": len(candidates_by_stream[stream])
            - len(resolutions),
            "new_resolution_rows_this_cycle": len(new_rows),
            "pending_reasons": pending,
        }

    status = {
        "schema_version": "xauusd_capital_core_causal_outcome_runtime_v40",
        "updated_at_utc": utc_text(current),
        "status": "ACTIVE_READ_ONLY_CAUSAL_RESOLVER",
        "account_login": int(source["account_login"]),
        "account_server": str(source["account_server"]),
        "symbol": str(source["symbol"]),
        "contract_sha256": str(contract["contract_sha256"]),
        "streams": status_streams,
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
    atomic_write_json(runtime / config["outputs"]["runtime_status"], status)
    return status


def failure_status(error: Exception) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_capital_core_causal_outcome_runtime_v40",
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
        description="Resolve frozen R1-R4 Core candidate outcomes causally"
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
        time.sleep(max(30, poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
