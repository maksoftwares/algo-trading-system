from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from router_forward import (  # noqa: E402
    load_config,
    load_frozen,
    read_routed_ledger,
    route_candidate,
    validate_existing_routes,
    validate_resolution_rows,
    verify_contract,
    verify_named_prefix,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _safe_status(error: Exception) -> dict[str, Any]:
    return {
        "schema_version": "xauusd_capital_r5_causal_router_runtime_v39",
        "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "FAILED_CLOSED",
        "error": f"{type(error).__name__}: {error}",
        "candidate_outcomes_attached": False,
        "aggregate_economics_opened": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "trade_permission": False,
        "broker_action_allowed": False,
    }


def run_cycle(
    repo_root: Path = REPO_ROOT,
    package_root: Path = ROOT,
    *,
    now: pd.Timestamp | None = None,
) -> dict[str, Any]:
    config = load_config(package_root / "config" / "capital_r5_causal_router_v39.json")
    contract = verify_contract(config, repo_root, package_root)
    frozen = load_frozen(config, repo_root)
    source = config["source"]
    outputs = config["outputs"]
    current = (
        pd.Timestamp.now(tz="UTC")
        if now is None
        else pd.Timestamp(now).tz_convert("UTC")
    )

    v35_runtime = Path(source["v35_candidate_runtime_directory"])
    v38_runtime = Path(source["v38_runtime_directory"])
    v35_status = frozen.v38.verify_candidate_status(
        v35_runtime / source["v35_status_filename"], frozen.v38_config
    )
    v38_status = frozen.v38.read_json(v38_runtime / source["v38_status_filename"])
    if str(v38_status.get("status")) != "ACTIVE_READ_ONLY_CAUSAL_RESOLVER":
        raise ValueError("V39 V38 resolver is not active")
    if str(v38_status.get("contract_sha256")) != str(
        config["frozen_identity"]["v38_contract_sha256"]
    ):
        raise ValueError("V39 V38 runtime contract changed")
    for field in ("broker_action_allowed", "python_predictions_authorized"):
        if bool(v38_status.get(field)):
            raise ValueError(f"V39 V38 runtime has authority enabled: {field}")

    candidate_path = v35_runtime / source["v35_candidate_filename"]
    resolution_path = v38_runtime / source["v38_resolution_filename"]
    candidate_snapshot = frozen.v38.stable_line_prefix(candidate_path)
    resolution_snapshot = frozen.v38.stable_line_prefix(resolution_path)
    v38_state = frozen.v38.read_json(v38_runtime / source["v38_prefix_state_filename"])
    frozen.v38.verify_source_prefix(candidate_snapshot, v38_state)
    frozen.v38.verify_resolution_prefix(resolution_snapshot, v38_state)
    candidates = frozen.v38.parse_candidate_snapshot(
        candidate_snapshot, frozen.v38_config
    )
    raw_resolutions = frozen.v38.read_resolution_ledger(resolution_path)
    resolutions = validate_resolution_rows(raw_resolutions, config)

    runtime = Path(outputs["runtime_directory"])
    runtime.mkdir(parents=True, exist_ok=True)
    state_path = runtime / outputs["source_prefix_state"]
    state = frozen.v38.read_json(state_path) if state_path.is_file() else None
    route_path = runtime / outputs["routed_ledger"]
    route_snapshot = frozen.v38.stable_line_prefix(route_path)
    verify_named_prefix(candidate_snapshot, state, "candidate_source")
    verify_named_prefix(resolution_snapshot, state, "resolution_source")
    verify_named_prefix(route_snapshot, state, "route")
    routes = read_routed_ledger(route_path, frozen.v38)
    validate_existing_routes(routes, candidates, str(contract["contract_sha256"]))

    v35_updated = pd.Timestamp(v35_status["updated_at_utc"])
    v38_updated = pd.Timestamp(v38_status["updated_at_utc"])
    synchronized = (
        int(v38_status.get("candidate_rows", -1)) == len(candidates)
        and int(v38_state.get("candidate_rows", -1)) == len(candidates)
        and (
            not bool(config["forward"]["require_v38_status_not_older_than_v35_status"])
            or v38_updated >= v35_updated
        )
    )
    if synchronized:
        historical = pd.read_parquet(repo_root / source["v9_component_trades"])
        routed_ids = {str(row["candidate_id"]) for row in routes}
        new_routes = [
            route_candidate(
                candidate,
                historical,
                resolutions,
                frozen,
                str(contract["contract_sha256"]),
            )
            for candidate in candidates
            if str(candidate["candidate_id"]) not in routed_ids
        ]
        for route in new_routes:
            route["route_recorded_at_utc"] = frozen.v38.utc_text(current)
        frozen.v38.append_resolution_records(route_path, new_routes)
        routes = read_routed_ledger(route_path, frozen.v38)
        route_snapshot = frozen.v38.stable_line_prefix(route_path)
        validate_existing_routes(routes, candidates, str(contract["contract_sha256"]))
    else:
        new_routes = []

    prefix_state = {
        "schema_version": "xauusd_capital_r5_causal_router_prefix_v39",
        "updated_at_utc": frozen.v38.utc_text(current),
        "candidate_source_prefix_bytes": len(candidate_snapshot),
        "candidate_source_prefix_sha256": frozen.v38.sha256_bytes(candidate_snapshot),
        "resolution_source_prefix_bytes": len(resolution_snapshot),
        "resolution_source_prefix_sha256": frozen.v38.sha256_bytes(resolution_snapshot),
        "route_prefix_bytes": len(route_snapshot),
        "route_prefix_sha256": frozen.v38.sha256_bytes(route_snapshot),
        "candidate_rows": len(candidates),
        "resolution_rows": len(resolutions),
        "route_rows": len(routes),
        "contract_sha256": str(contract["contract_sha256"]),
    }
    frozen.v38.atomic_write_json(state_path, prefix_state)
    status = {
        "schema_version": "xauusd_capital_r5_causal_router_runtime_v39",
        "updated_at_utc": frozen.v38.utc_text(current),
        "status": (
            "ACTIVE_READ_ONLY_CAUSAL_ROUTER" if synchronized else "WAITING_FOR_V38_SYNC"
        ),
        "contract_sha256": str(contract["contract_sha256"]),
        "candidate_rows": len(candidates),
        "resolution_rows": len(resolutions),
        "routed_candidate_rows": len(routes),
        "new_routed_candidate_rows_this_cycle": len(new_routes),
        "v35_updated_at_utc": frozen.v38.utc_text(v35_updated),
        "v38_updated_at_utc": frozen.v38.utc_text(v38_updated),
        "v38_synchronized": synchronized,
        "candidate_outcomes_attached": False,
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
    frozen.v38.atomic_write_json(runtime / outputs["runtime_status"], status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Route R5 candidates with causal outcomes"
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=None)
    args = parser.parse_args()
    config = load_config()
    poll = (
        int(config["forward"]["poll_seconds"])
        if args.poll_seconds is None
        else int(args.poll_seconds)
    )
    while True:
        try:
            status = run_cycle()
            print(json.dumps(status, sort_keys=True), flush=True)
        except Exception as exc:  # pragma: no cover - main loop safety wrapper
            status = _safe_status(exc)
            runtime = Path(config["outputs"]["runtime_directory"])
            _write_json(runtime / config["outputs"]["runtime_status"], status)
            print(json.dumps(status, sort_keys=True), flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(main())
