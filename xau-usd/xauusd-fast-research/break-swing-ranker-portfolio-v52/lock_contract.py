from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config/break_swing_ranker_portfolio_v52.json"
LOCKED_FILES = (
    ".gitattributes",
    ".gitignore",
    "PREREGISTRATION.md",
    "README.md",
    "requirements.txt",
    "config/break_swing_ranker_portfolio_v52.json",
    "src/__init__.py",
    "src/ranker.py",
    "run_study.py",
    "lock_contract.py",
    "tests/conftest.py",
    "tests/test_ranker.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(payload: dict) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def build_contract() -> dict:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    payload = {
        "schema_version": config["schema_version"],
        "locked_before_ranked_later_outcomes_opened": True,
        "files": {
            relative: {
                "bytes": int((ROOT / relative).stat().st_size),
                "sha256": sha256_file(ROOT / relative),
            }
            for relative in LOCKED_FILES
        },
        "model": config["model"],
        "addon_policy": config["addon_policy"],
        "v50_core_policy": config["v50_core_policy"],
        "windows": config["windows"],
        "account_reference": config["account_reference"],
        "gates": config["gates"],
        "research_controls": config["research_controls"],
    }
    payload["contract_sha256"] = canonical_sha256(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    current = build_contract()
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
    if args.verify:
        if json.loads(path.read_text(encoding="utf-8")) != current:
            raise ValueError("V52 contract verification failed")
    print(current["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
