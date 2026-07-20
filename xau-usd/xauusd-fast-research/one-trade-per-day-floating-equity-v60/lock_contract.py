from __future__ import annotations

import json
from pathlib import Path

from src.audit import canonical_sha256, directory_manifest, sha256_file, verify_repo_sources


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "one_trade_per_day_floating_equity_v60.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    repo_hashes = verify_repo_sources(REPO_ROOT, config["repo_sources"])
    market = config["market_data"]
    modern = Path(str(market["modern_m5"]["path"]))
    modern_hash = sha256_file(modern)
    if modern_hash != str(market["modern_m5"]["sha256"]):
        raise ValueError("Modern M5 source hash mismatch")
    bid_manifest = directory_manifest(market["legacy_bid_m5"])
    ask_manifest = directory_manifest(market["legacy_ask_m5"])
    implementation_hashes = {
        "audit": sha256_file(ROOT / "src" / "audit.py"),
        "runner": sha256_file(ROOT / "run_evaluation.py"),
    }
    contract = {
        "schema_version": "xauusd_one_trade_per_day_floating_equity_v60_contract",
        "config_sha256": sha256_file(CONFIG_PATH),
        "repo_source_hashes": repo_hashes,
        "modern_m5_sha256": modern_hash,
        "legacy_bid_manifest": bid_manifest,
        "legacy_ask_manifest": ask_manifest,
        "implementation_hashes": implementation_hashes,
    }
    contract["contract_sha256"] = canonical_sha256(contract)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(contract["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
