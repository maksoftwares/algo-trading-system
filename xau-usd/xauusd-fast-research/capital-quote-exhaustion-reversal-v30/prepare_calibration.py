from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from exhaustion_reversal import (  # noqa: E402
    canonical_hash,
    generate_candidates,
    load_config,
    load_locked_v24,
    sha256_file,
)


def main() -> int:
    config = load_config(ROOT)
    source = Path(config["source"]["calibration_file"])
    if sha256_file(source) != config["source"]["calibration_file_sha256"]:
        raise ValueError("V30 calibration source changed")
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V30 is already locked")
    v24 = load_locked_v24(config)
    ticks, source_audit, _ = v24.load_ticks([source], config)
    candidates, structural = generate_candidates(ticks, config)
    candidate_path = output / config["outputs"]["calibration_candidates"]
    candidate_path.write_bytes(
        candidates.to_csv(index=False, lineterminator="\n").encode("utf-8")
    )
    audit = {
        "schema_version": "xauusd_v30_outcome_blind_calibration_audit",
        "source_file": str(source.resolve()).replace("\\", "/"),
        "source_file_sha256": sha256_file(source),
        "source_audit": source_audit,
        "candidate_definition": config["feature"],
        "episode_definition": config["episode"],
        "impulse_arm_count": structural["impulse_arm_count"],
        "raw_trigger_count": structural["raw_trigger_count"],
        "selected_candidate_count": int(len(candidates)),
        "long_candidates": int(candidates["candidate_side"].eq("LONG").sum()),
        "short_candidates": int(candidates["candidate_side"].eq("SHORT").sum()),
        "observed_utc_blocks": int(candidates["utc_block_start_ms"].nunique()),
        "candidate_file_sha256": sha256_file(candidate_path),
        "post_candidate_prices_used_for_label_or_outcome": False,
        "economic_outcomes_opened": False,
        "pnl_calculated": False,
        "calibration_structure_passed": bool(len(candidates) >= 2),
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    audit_path = output / config["outputs"]["calibration_audit"]
    audit_path.write_bytes(
        (json.dumps(audit, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    print(json.dumps(audit, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
