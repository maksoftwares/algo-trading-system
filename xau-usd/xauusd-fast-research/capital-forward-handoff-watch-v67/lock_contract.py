from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from handoff import canonical_hash, load_json, sha256_file  # noqa: E402


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_forward_handoff_watch_v67.json",
    "src/__init__.py",
    "src/handoff.py",
    "lock_contract.py",
    "run_watch.py",
    "tests/test_handoff.py",
)


def record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def main() -> int:
    config = load_json(ROOT / "config" / "capital_forward_handoff_watch_v67.json")
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("V67 contract already exists")
    package_paths = [ROOT / relative for relative in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)

    v27_root = REPO_ROOT / str(config["v27"]["root"])
    v27_contract_path = v27_root / str(config["v27"]["contract"])
    if sha256_file(v27_contract_path) != str(config["v27"]["contract_file_sha256"]):
        raise ValueError("V67 V27 contract file changed")
    v27_contract = load_json(v27_contract_path)
    if canonical_hash(v27_contract, "contract_sha256") != str(
        v27_contract.get("contract_sha256")
    ):
        raise ValueError("V67 V27 contract self-hash changed")
    if str(v27_contract["contract_sha256"]) != str(config["v27"]["contract_sha256"]):
        raise ValueError("V67 V27 contract identity changed")

    contract = {
        "schema_version": "xauusd_capital_forward_handoff_watch_v67_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "v27_contract": record(v27_contract_path, REPO_ROOT),
        "v27_contract_sha256": str(v27_contract["contract_sha256"]),
        "runtime": config["runtime"],
        "economic_logic_present": False,
        **config["research_controls"],
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(
        (json.dumps(contract, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    print(json.dumps(contract, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
