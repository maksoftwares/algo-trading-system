from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from router_forward import canonical_sha256, load_config, sha256_file  # noqa: E402


PACKAGE_FILES = (
    ".gitattributes",
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_r5_causal_router_v39.json",
    "lock_contract.py",
    "run_router.py",
    "verify_historical_parity.py",
    "src/__init__.py",
    "src/router_forward.py",
    "tests/test_router_forward.py",
)


def record(path: Path) -> dict[str, object]:
    return {"bytes": int(path.stat().st_size), "sha256": sha256_file(path)}


def main() -> int:
    config = load_config()
    payload = {
        "schema_version": config["schema_version"],
        "package_files": {
            relative: record(ROOT / relative) for relative in PACKAGE_FILES
        },
        "dependencies": {
            relative: record(REPO_ROOT / relative)
            for relative in config["contract_dependencies"]
        },
        "forward_start_inclusive_utc": config["frozen_identity"][
            "forward_start_inclusive_utc"
        ],
        "component_attempts": config["frozen_identity"]["component_attempts"],
        "router_attempt": config["frozen_identity"]["router_attempt"],
        "router_id": config["frozen_identity"]["router_id"],
        "v38_contract_sha256": config["frozen_identity"]["v38_contract_sha256"],
        "strict_causal_knowledge_cutoff": True,
        "broker_action_authorized": False,
    }
    payload["contract_sha256"] = canonical_sha256(payload)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
