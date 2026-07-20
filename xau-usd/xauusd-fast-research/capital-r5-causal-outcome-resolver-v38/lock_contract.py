from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from resolver import canonical_sha256, load_config, sha256_file  # noqa: E402


PACKAGE_FILES = (
    ".gitattributes",
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_r5_causal_outcome_resolver_v38.json",
    "lock_contract.py",
    "run_resolver.py",
    "verify_historical_semantics.py",
    "src/__init__.py",
    "src/resolver.py",
    "tests/test_resolver.py",
)


def record(path: Path) -> dict[str, object]:
    return {"bytes": int(path.stat().st_size), "sha256": sha256_file(path)}


def main() -> int:
    config = load_config()
    dependencies = {
        relative: record(REPO_ROOT / relative)
        for relative in config["contract_dependencies"]
    }
    payload = {
        "schema_version": config["schema_version"],
        "package_files": {
            relative: record(ROOT / relative) for relative in PACKAGE_FILES
        },
        "dependencies": dependencies,
        "forward_start_inclusive_utc": config["frozen_identity"][
            "forward_start_inclusive_utc"
        ],
        "component_attempts": config["frozen_identity"]["component_attempts"],
        "v35_contract_sha256": config["frozen_identity"]["v35_contract_sha256"],
        "v35_rule_dependency_sha256": config["frozen_identity"][
            "v35_rule_dependency_sha256"
        ],
        "broker_action_authorized": False,
    }
    payload["contract_sha256"] = canonical_sha256(payload)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
