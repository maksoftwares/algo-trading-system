from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from resolver import (  # noqa: E402
    atomic_write_json,
    load_config,
    load_module,
    read_json,
    source_contract_sha256,
    validate_frozen_identity,
    verify_contract,
)


def frame_digest(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return hashlib.sha256(b"").hexdigest()
    payload = (
        frame[columns]
        .to_csv(index=False, lineterminator="\n", float_format="%.10g")
        .encode("utf-8")
    )
    return hashlib.sha256(payload).hexdigest()


def maximum_concurrent(frame: pd.DataFrame) -> int:
    active: list[pd.Timestamp] = []
    maximum = 0
    ordered = frame.sort_values(["entry_time", "candidate_id"], kind="mergesort")
    for row in ordered.itertuples(index=False):
        entry = pd.Timestamp(row.entry_time)
        active = [exit_time for exit_time in active if exit_time > entry]
        active.append(pd.Timestamp(row.exit_time))
        maximum = max(maximum, len(active))
    return maximum


def main() -> int:
    config = load_config()
    contract = verify_contract(config)
    validate_frozen_identity(config)
    historical = config["historical"]
    module = load_module(
        "capital_r1_box_v41_historical_source",
        REPO_ROOT / historical["source_module"],
    )
    source_config = read_json(REPO_ROOT / historical["source_config"])
    run = module.run_portability(source_config)
    primary = run.policy_trades.loc[
        run.policy_trades["policy_id"].eq("PORTFOLIO_CONSTRAINED_PRIMARY")
    ].copy()
    candidate_columns = [
        "candidate_id",
        "signal_time",
        "accepted",
        "rejection_reason",
    ]
    trade_columns = [
        "policy_id",
        "candidate_id",
        "entry_time",
        "exit_time",
        "stress_net_r",
    ]
    candidate_digest = frame_digest(run.candidates, candidate_columns)
    all_policy_digest = frame_digest(run.policy_trades, trade_columns)
    primary_digest = frame_digest(primary, trade_columns)
    maximum_daily = int(primary.groupby(primary["entry_time"].dt.date).size().max())
    maximum_open = maximum_concurrent(primary)
    identity = config["frozen_identity"]
    source_result = read_json(REPO_ROOT / historical["source_result"])
    source_manifest = read_json(REPO_ROOT / historical["source_manifest"])
    checks: dict[str, Any] = {
        "source_contract_sha256": source_contract_sha256(config),
        "candidate_rows": int(len(run.candidates)),
        "executable_trade_rows": int(len(run.all_trades)),
        "all_policy_trade_rows": int(len(run.policy_trades)),
        "primary_policy_trade_rows": int(len(primary)),
        "candidate_digest": candidate_digest,
        "all_policy_trade_digest": all_policy_digest,
        "primary_policy_trade_digest": primary_digest,
        "maximum_primary_concurrent_positions": int(maximum_open),
        "maximum_primary_entries_per_utc_day": int(maximum_daily),
        "candidate_ids_unique": bool(run.candidates["candidate_id"].is_unique),
        "primary_candidate_ids_are_known": bool(
            set(primary["candidate_id"]).issubset(set(run.candidates["candidate_id"]))
        ),
        "source_result_digests_match": bool(
            str(source_result["candidate_digest"]) == candidate_digest
            and str(source_result["trade_digest"]) == all_policy_digest
        ),
        "source_manifest_counts_and_digests_match": bool(
            int(source_manifest["candidate_rows"]) == len(run.candidates)
            and int(source_manifest["all_trade_rows"]) == len(run.all_trades)
            and int(source_manifest["policy_trade_rows"]) == len(run.policy_trades)
            and str(source_manifest["candidate_digest"]) == candidate_digest
            and str(source_manifest["trade_digest"]) == all_policy_digest
        ),
        "execution_has_no_time_exit": bool(
            set(run.all_trades["exit_reason"].astype(str))
            <= {
                "STOP",
                "GAP_THROUGH_STOP",
                "AMBIGUOUS_M5_STOP_FIRST",
                "TARGET",
                "TARGET_GAP_FROZEN_TARGET",
                "END_OF_DATA",
            }
        ),
    }
    checks["pass"] = bool(
        checks["source_contract_sha256"] == identity["source_contract_sha256"]
        and checks["candidate_rows"] == int(identity["historical_candidate_rows"])
        and checks["executable_trade_rows"]
        == int(identity["historical_executable_trade_rows"])
        and checks["primary_policy_trade_rows"]
        == int(identity["historical_primary_policy_trade_rows"])
        and checks["candidate_digest"] == identity["historical_candidate_digest"]
        and checks["all_policy_trade_digest"]
        == identity["historical_all_policy_trade_digest"]
        and checks["primary_policy_trade_digest"]
        == identity["historical_primary_policy_trade_digest"]
        and checks["maximum_primary_concurrent_positions"]
        <= int(config["execution"]["maximum_concurrent_positions"])
        and checks["maximum_primary_entries_per_utc_day"]
        <= int(config["execution"]["maximum_entries_per_utc_day"])
        and checks["candidate_ids_unique"]
        and checks["primary_candidate_ids_are_known"]
        and checks["source_result_digests_match"]
        and checks["source_manifest_counts_and_digests_match"]
        and checks["execution_has_no_time_exit"]
    )
    result = {
        "schema_version": "xauusd_capital_r1_box_causal_outcome_semantic_parity_v41",
        "contract_sha256": contract["contract_sha256"],
        "checks": checks,
        "semantic_parity_passed": bool(checks["pass"]),
        "aggregate_economics_opened": False,
        "broker_action_authorized": False,
    }
    if not result["semantic_parity_passed"]:
        raise ValueError(f"V41 historical semantic parity failed: {result}")
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output / config["outputs"]["historical_semantic_parity"], result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
