from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microburst import (  # noqa: E402
    canonical_hash,
    generate_candidates,
    load_config,
    load_ticks,
    sha256_file,
    verify_manifest_files,
)


def verify_contract(config: dict) -> dict:
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    contract = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(contract, "contract_sha256") != contract["contract_sha256"]:
        raise ValueError("V24 contract self-hash mismatch")
    for record in contract["package_files"]:
        package_path = REPO / record["path"]
        if sha256_file(package_path) != record["sha256"]:
            raise ValueError(f"Locked V24 file changed: {record['path']}")
    return contract


def main() -> int:
    config = load_config(ROOT)
    contract = verify_contract(config)
    manifest_path = ROOT / config["source"]["calibration_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if canonical_hash(manifest, "manifest_sha256") != manifest["manifest_sha256"]:
        raise ValueError("V24 calibration manifest self-hash mismatch")
    if manifest["manifest_sha256"] != contract["calibration_manifest_sha256"]:
        raise ValueError("V24 calibration manifest differs from contract")
    verify_manifest_files(manifest, "calibration_files")
    paths = [Path(record["path"]) for record in manifest["calibration_files"]]
    ticks, source_audit, _ = load_ticks(paths, config)
    source = config["source"]
    start_ms = int(
        pd.Timestamp(source["calibration_start_inclusive_utc"]).timestamp() * 1000
    )
    end_ms = int(
        pd.Timestamp(source["calibration_end_exclusive_utc"]).timestamp() * 1000
    )
    ticks = ticks.loc[
        ticks["tick_time_msc"].ge(start_ms) & ticks["tick_time_msc"].lt(end_ms)
    ].reset_index(drop=True)
    candidates, features = generate_candidates(ticks, config)
    block_count = int(features["utc_block_start_ms"].nunique())
    long_count = int(candidates["candidate_side"].eq("LONG").sum())
    short_count = int(candidates["candidate_side"].eq("SHORT").sum())
    checks = {
        "at_least_two_candidates": len(candidates) >= 2,
        "no_more_than_one_candidate_per_observed_block": len(candidates) <= block_count,
        "both_directions_present": long_count > 0 and short_count > 0,
        "no_economic_outcomes_opened": True,
    }
    audit = {
        "schema_version": "xauusd_v24_1_calibration_frequency_audit",
        "contract_sha256": contract["contract_sha256"],
        "calibration_manifest_sha256": manifest["manifest_sha256"],
        "source_audit": source_audit,
        "calibration_rows": int(len(ticks)),
        "observed_utc_blocks": block_count,
        "raw_gate_crossings": int(features["raw_gate_crossing"].sum()),
        "candidate_count": int(len(candidates)),
        "candidate_blocks": int(candidates["utc_block_start_ms"].nunique()),
        "long_candidates": long_count,
        "short_candidates": short_count,
        "post_candidate_prices_read_for_labels": False,
        "economic_outcomes_opened": False,
        "pnl_calculated": False,
        "win_rate_calculated": False,
        "gate_checks": checks,
        "calibration_structure_passed": bool(all(checks.values())),
        "decision": (
            "V24_1_CALIBRATION_STRUCTURE_PASS_FORWARD_COLLECTION_REQUIRED"
            if all(checks.values())
            else "V24_1_CALIBRATION_STRUCTURE_FAIL"
        ),
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    output = ROOT / config["outputs"]["directory"]
    candidates_path = output / config["outputs"]["calibration_candidates"]
    audit_path = output / config["outputs"]["calibration_audit"]
    candidates.to_csv(candidates_path, index=False, lineterminator="\n")
    audit_path.write_text(
        json.dumps(audit, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
