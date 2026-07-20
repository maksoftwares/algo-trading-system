from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.audit import sha256_file, verify_sources


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "one_trade_per_day_native_core_v58.json"


def canonical_sha256(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "xauusd_one_trade_per_day_native_core_v58_contract",
        "config_sha256": sha256_file(CONFIG_PATH),
        "source_hashes": verify_sources(REPO_ROOT, config["sources"]),
        "implementation_hashes": {
            "audit": sha256_file(ROOT / "src" / "audit.py"),
            "runner": sha256_file(ROOT / "run_evaluation.py"),
        },
        "same_version_post_outcome_tuning_authorized": False,
    }
    payload["contract_sha256"] = canonical_sha256(payload)
    path = output / config["outputs"]["contract_lock"]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["contract_sha256"])


if __name__ == "__main__":
    main()
