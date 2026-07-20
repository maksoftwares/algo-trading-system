from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from portfolio import sha256_file, verify_sources  # noqa: E402


def main() -> int:
    config_path = ROOT / "config" / "one_trade_per_day_health_portfolio_v53.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_hashes = verify_sources(REPO_ROOT, config["sources"])
    config_sha = sha256_file(config_path)
    payload = {
        "schema_version": "xauusd_one_trade_per_day_health_portfolio_v53_contract_lock",
        "config_sha256": config_sha,
        "source_hashes": source_hashes,
        "policy_sha256": hashlib.sha256(
            json.dumps(
                {
                    "v50_policy": config["v50_policy"],
                    "sleeves": config["sleeves"],
                    "account": config["account"],
                    "windows": config["windows"],
                    "gates": config["gates"],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    }
    payload["contract_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(payload["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
