from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "historical_core_single_exposure_risk_v50.json"
LOCKED_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "README.md",
    "requirements.txt",
    "config/historical_core_single_exposure_risk_v50.json",
    "src/__init__.py",
    "src/audit.py",
    "run_audit.py",
    "lock_contract.py",
    "tests/conftest.py",
    "tests/test_audit.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def payload() -> dict:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": config["schema_version"],
        "files": {
            relative: {
                "sha256": sha256_file(ROOT / relative),
                "bytes": (ROOT / relative).stat().st_size,
            }
            for relative in LOCKED_FILES
        },
    }


def canonical_sha256(value: dict) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    current = payload()
    current["contract_sha256"] = canonical_sha256(current)
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(current["contract_sha256"])
        return
    expected = json.loads(path.read_text(encoding="utf-8"))
    if current != expected:
        raise SystemExit("V50 contract verification failed")
    print(f"verified {current['contract_sha256']}")


if __name__ == "__main__":
    main()
