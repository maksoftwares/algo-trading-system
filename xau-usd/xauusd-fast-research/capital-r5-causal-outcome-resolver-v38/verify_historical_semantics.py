from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from resolver import (  # noqa: E402
    atomic_write_json,
    load_config,
    read_json,
    validate_frozen_identity,
    verify_contract,
)


def main() -> int:
    config = load_config()
    contract = verify_contract(config)
    execution = validate_frozen_identity(config)
    candidates_path = (
        REPO_ROOT
        / "xau-usd/xauusd-fast-research/transition-weighted-rawtick-confirmation-v9/outputs/TRANSITION_WEIGHTED_RAWTICK_V9_CANDIDATES.parquet"
    )
    candidates = pd.read_parquet(candidates_path)
    signal = pd.to_datetime(candidates["signal_time"], utc=True)
    scheduled = pd.to_datetime(candidates["scheduled_entry_time"], utc=True)
    equal = signal.eq(scheduled)
    v35_lock = read_json(REPO_ROOT / config["source"]["v35_contract_lock"])
    result = {
        "schema_version": "xauusd_capital_r5_causal_outcome_semantic_parity_v38",
        "contract_sha256": contract["contract_sha256"],
        "candidate_rows": int(len(candidates)),
        "signal_equals_entry_rows": int(equal.sum()),
        "component_attempts": sorted(
            int(value) for value in candidates["origin_attempt"].unique()
        ),
        "v35_historical_candidate_rows": int(
            v35_lock["historical_parity"]["candidate_rows"]
        ),
        "execution_config": execution,
        "semantic_parity_passed": bool(
            len(candidates)
            == int(config["frozen_identity"]["historical_candidate_rows"])
            and equal.all()
            and sorted(int(value) for value in candidates["origin_attempt"].unique())
            == sorted(
                int(value) for value in config["frozen_identity"]["component_attempts"]
            )
        ),
        "aggregate_economics_opened": False,
        "broker_action_authorized": False,
    }
    if not result["semantic_parity_passed"]:
        raise ValueError("V38 historical semantic parity failed")
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output / config["outputs"]["historical_semantic_parity"], result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
