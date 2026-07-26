from __future__ import annotations

import json
from pathlib import Path

from src.evaluator import (
    load_model,
    read_json,
    stable_jsonl_snapshot,
    verify_contract,
    verify_score_replay,
)

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config/macro_expected_r_prospective_v14.json"


def main() -> int:
    config = read_json(CONFIG)
    contract = verify_contract(ROOT, config)
    runtime = Path(str(config["runtime"]["directory"]))
    score_path = runtime / str(config["runtime"]["score_ledger"])
    rows, _ = stable_jsonl_snapshot(score_path)
    verify_score_replay(rows, load_model(config))
    result = {
        "status": "MACRO_EXPECTED_R_PROSPECTIVE_V14_VERIFICATION_PASS",
        "contract_sha256": contract["contract_sha256"],
        "score_rows": len(rows),
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
