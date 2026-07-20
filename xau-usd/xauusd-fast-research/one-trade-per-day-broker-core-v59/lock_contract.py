from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.policy import load_v58_audit


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "one_trade_per_day_broker_core_v59.json"


def canonical_sha256(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    module_path = REPO_ROOT / config["sources"]["v58_audit_module"]["path"]
    v58 = load_v58_audit(module_path)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "xauusd_one_trade_per_day_broker_core_v59_contract",
        "config_sha256": v58.sha256_file(CONFIG_PATH),
        "source_hashes": v58.verify_sources(REPO_ROOT, config["sources"]),
        "implementation_hashes": {
            "policy": v58.sha256_file(ROOT / "src" / "policy.py"),
            "runner": v58.sha256_file(ROOT / "run_evaluation.py"),
        },
        "same_version_post_outcome_tuning_authorized": False,
    }
    payload["contract_sha256"] = canonical_sha256(payload)
    (output / config["outputs"]["contract_lock"]).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(payload["contract_sha256"])


if __name__ == "__main__":
    main()
