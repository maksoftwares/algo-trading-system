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
    ".gitignore",
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_core_causal_outcome_resolver_v40.json",
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
        "source_contracts": {
            stream: config["frozen_identity"][stream]["contract_sha256"]
            for stream in ("v28", "v29", "v34")
        },
        "aggregate_economics_opened": False,
        "broker_action_authorized": False,
    }
    payload["contract_sha256"] = canonical_sha256(payload)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
