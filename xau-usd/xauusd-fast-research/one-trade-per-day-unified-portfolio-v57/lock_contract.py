from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V53_SRC = ROOT.parent / "one-trade-per-day-health-portfolio-v53" / "src"
V56_SRC = ROOT.parent / "one-trade-per-day-break-overlay-v56" / "src"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(V53_SRC))

from policy import resolve_config  # noqa: E402
from portfolio import sha256_file, verify_sources  # noqa: E402


def main() -> int:
    config_path = ROOT / "config" / "one_trade_per_day_unified_portfolio_v57.json"
    config, overlay = resolve_config(REPO_ROOT, config_path)
    base_path = REPO_ROOT / overlay["base_config_path"]
    if sha256_file(base_path) != overlay["base_config_sha256"]:
        raise ValueError("V53 base config hash mismatch")
    source_hashes = verify_sources(REPO_ROOT, config["sources"])
    implementation_hashes = {
        "base_portfolio": sha256_file(V53_SRC / "portfolio.py"),
        "candidate_builder": sha256_file(V56_SRC / "overlay.py"),
        "policy": sha256_file(ROOT / "src" / "policy.py"),
        "runner": sha256_file(ROOT / "run_evaluation.py"),
    }
    policy_payload = {
        "v50_policy": config["v50_policy"],
        "sleeves": config["sleeves"],
        "overlay_sleeve": config["overlay_sleeve"],
        "account": config["account"],
        "windows": config["windows"],
        "gates": config["gates"],
    }
    payload = {
        "schema_version": "xauusd_one_trade_per_day_unified_portfolio_v57_contract_lock",
        "overlay_config_sha256": sha256_file(config_path),
        "base_config_sha256": sha256_file(base_path),
        "source_hashes": source_hashes,
        "implementation_hashes": implementation_hashes,
        "policy_sha256": hashlib.sha256(
            json.dumps(policy_payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
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
