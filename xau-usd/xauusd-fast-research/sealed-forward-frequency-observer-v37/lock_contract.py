from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from observer import load_config, sha256_file, verify_locked_dependencies  # noqa: E402


FILES = (
    ".gitattributes",
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/sealed_forward_frequency_observer_v37.json",
    "lock_contract.py",
    "run_observer.py",
    "src/__init__.py",
    "src/observer.py",
    "tests/test_observer.py",
)


def main() -> int:
    config = load_config()
    payload = {
        "schema_version": config["schema_version"],
        "files": {name: sha256_file(ROOT / name) for name in FILES},
        "dependencies": verify_locked_dependencies(config),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["contract_sha256"] = hashlib.sha256(canonical).hexdigest()
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
