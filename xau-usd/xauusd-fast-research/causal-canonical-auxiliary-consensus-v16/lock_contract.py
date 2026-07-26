from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "auxiliary_consensus_v16.json"
OUTPUT = ROOT / "outputs"
CONTRACT_PATH = OUTPUT / "AUX_CONSENSUS_V16_CONTRACT_LOCK.json"
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/auxiliary_consensus_v16.json",
    "src/__init__.py",
    "src/consensus.py",
    "run_evaluation.py",
    "verify.py",
    "tests/test_consensus.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("contract_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def record(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(base.resolve()).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def main() -> int:
    if CONTRACT_PATH.exists():
        raise FileExistsError("V16 contract already exists")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inputs = []
    for name, relative in config["inputs"].items():
        path = REPO_ROOT / str(relative)
        if not path.is_file():
            raise FileNotFoundError(path)
        inputs.append({"name": name, **record(path, REPO_ROOT)})
    package = []
    for relative in PACKAGE_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        package.append(record(path, ROOT))
    contract = {
        "schema_version": "xauusd_auxiliary_consensus_v16_contract",
        "package_files": package,
        "inputs": inputs,
        "expected": config["expected"],
        "authorization": config["authorization"],
        "historical_outcomes_already_exposed": True,
        "v14_immutable": True,
        "v15_immutable": True,
    }
    contract["contract_sha256"] = canonical_hash(contract)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(
        json.dumps(contract, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
