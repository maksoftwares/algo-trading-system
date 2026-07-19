from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from gap_restart import (  # noqa: E402
    assert_v24_execution_parity,
    canonical_hash,
    generate_candidates,
    load_config,
    load_locked_v24,
    sha256_file,
)


def main() -> int:
    config = load_config(ROOT)
    v24 = load_locked_v24(config)
    assert_v24_execution_parity(config, v24)
    output = ROOT / config["outputs"]["directory"]
    candidates_path = output / config["outputs"]["calibration_candidates"]
    audit_path = output / config["outputs"]["calibration_audit"]
    contract_path = output / config["outputs"]["contract_lock"]
    if candidates_path.exists() or audit_path.exists() or contract_path.exists():
        raise FileExistsError("V26 calibration or contract already exists")
    source_path = Path(config["source"]["calibration_file"])
    if sha256_file(source_path) != config["source"]["calibration_file_sha256"]:
        raise ValueError("V26 calibration source hash changed")
    ticks, source_audit, _ = v24.load_ticks([source_path], config)
    candidates, structural = generate_candidates(ticks, config)
    block_ms = int(config["episode"]["utc_block_hours"]) * 60 * 60 * 1000
    observed_blocks = int((ticks["tick_time_msc"] // block_ms).nunique())
    observed = {
        "unique_quote_rows": int(len(ticks)),
        "observed_four_hour_blocks": observed_blocks,
        "restart_episode_count": int(structural["restart_episode_count"]),
        "raw_candidate_count": int(structural["raw_candidate_count"]),
        "block_candidate_count": int(len(candidates)),
        "long_candidates": int(candidates["candidate_side"].eq("LONG").sum()),
        "short_candidates": int(candidates["candidate_side"].eq("SHORT").sum()),
    }
    expected = config["calibration_expected"]
    checks = {key: observed[key] == int(expected[key]) for key in expected}
    if not all(checks.values()):
        raise ValueError(f"V26 calibration structure changed: {checks}")
    output.mkdir(parents=True, exist_ok=True)
    candidates_path.write_bytes(
        candidates.to_csv(index=False, lineterminator="\n").encode("utf-8")
    )
    audit = {
        "schema_version": "xauusd_gap_restart_v26_calibration_audit",
        "source_audit": source_audit,
        "observed_structure": observed,
        "expected_structure": expected,
        "structure_checks": checks,
        "calibration_structure_passed": True,
        "candidate_file_sha256": sha256_file(candidates_path),
        "candidate_times_utc": candidates["timestamp_utc"].tolist(),
        "candidate_sides": candidates["candidate_side"].tolist(),
        "full_calibration_source_loaded": True,
        "post_candidate_prices_used_for_label_or_outcome": False,
        "economic_outcomes_opened": False,
        "pnl_calculated": False,
        "parameter_grid_used": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    audit_path.write_bytes(
        (json.dumps(audit, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    print(json.dumps(audit, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
