from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from adapter import load_adapter_config, load_v30_module, v30_root  # noqa: E402


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/adapter.json",
    "src/__init__.py",
    "src/adapter.py",
    "lock_adapter.py",
    "run_development_adapter.py",
    "tests/test_adapter.py",
)


def record(path: Path, v30: Any) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(REPO.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": v30.sha256_file(resolved),
    }


def main() -> int:
    adapter_config = load_adapter_config()
    v30 = load_v30_module(adapter_config)
    v30_path = v30_root(adapter_config)
    v30_config = v30.load_config(v30_path)
    v30_contract_path = v30_path / adapter_config["v30_contract_relative"]
    v30_contract = json.loads(v30_contract_path.read_text(encoding="utf-8"))
    if (
        v30.canonical_hash(v30_contract, "contract_sha256")
        != v30_contract["contract_sha256"]
    ):
        raise ValueError("V30 contract self-hash changed")
    if v30_contract["contract_sha256"] != adapter_config["v30_contract_sha256"]:
        raise ValueError("V30 contract identity changed")
    output = ROOT / "outputs"
    output.mkdir(parents=True, exist_ok=True)
    lock_path = ROOT / adapter_config["outputs"]["adapter_lock"]
    if lock_path.exists():
        raise FileExistsError("V30 timestamp adapter already locked")
    for key in ("development_audit", "development_trades"):
        if (v30_path / v30_config["outputs"][key]).exists():
            raise ValueError("V30 development outcome existed before adapter lock")
    package_paths = [(ROOT / relative).resolve() for relative in PACKAGE_FILES]
    missing = [str(path) for path in package_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    contract = {
        "schema_version": "xauusd_v30_timestamp_adapter_lock",
        "v30_contract_sha256": v30_contract["contract_sha256"],
        "v30_contract_file": record(v30_contract_path, v30),
        "package_files": [record(path, v30) for path in package_paths],
        "timestamp_rule": adapter_config["timestamp_rule"],
        "maximum_same_second_disagreement_ms": adapter_config[
            "maximum_same_second_disagreement_ms"
        ],
        "development_outcomes_opened_at_lock": False,
        "strategy_change": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    contract["adapter_contract_sha256"] = v30.canonical_hash(
        contract, "adapter_contract_sha256"
    )
    lock_path.write_bytes(
        (
            json.dumps(contract, allow_nan=False, indent=2, sort_keys=True) + "\n"
        ).encode()
    )
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
