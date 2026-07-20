from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
V30_ROOT = ROOT.parent / "capital-quote-exhaustion-reversal-v30"
TRANSPORT_ROOT = ROOT.parent / "capital-quote-exhaustion-reversal-v30-postlock-adapter"
V30_CONTRACT_SHA = "456b4ae5ddca695c2e5b37a79ab297c859d133b39e5197c4a78a80cf8a687d95"
TRANSPORT_CONTRACT_SHA = (
    "3a209900f9e063263356084aa59ff3fd0b7d74c758b73f62452906eb7d2a79d1"
)
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "src/__init__.py",
    "src/alias.py",
    "lock_adapter.py",
    "run_development.py",
    "tests/test_alias.py",
)


def load_v30() -> Any:
    path = V30_ROOT / "src" / "exhaustion_reversal.py"
    spec = importlib.util.spec_from_file_location("v30_alias_lock", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def record(path: Path, v30: Any) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(REPO.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": v30.sha256_file(resolved),
    }


def main() -> int:
    v30 = load_v30()
    v30_contract_path = (
        V30_ROOT / "outputs" / "EXHAUSTION_REVERSAL_V30_CONTRACT_LOCK.json"
    )
    v30_contract = json.loads(v30_contract_path.read_text(encoding="utf-8"))
    if (
        v30.canonical_hash(v30_contract, "contract_sha256") != V30_CONTRACT_SHA
        or v30_contract["contract_sha256"] != V30_CONTRACT_SHA
    ):
        raise ValueError("V30 strategy contract changed")
    transport_path = TRANSPORT_ROOT / "outputs" / "V30_TIMESTAMP_ADAPTER_LOCK.json"
    transport = json.loads(transport_path.read_text(encoding="utf-8"))
    if (
        v30.canonical_hash(transport, "adapter_contract_sha256")
        != TRANSPORT_CONTRACT_SHA
        or transport["adapter_contract_sha256"] != TRANSPORT_CONTRACT_SHA
    ):
        raise ValueError("V30 timestamp adapter contract changed")
    config = v30.load_config(V30_ROOT)
    output = V30_ROOT / config["outputs"]["directory"]
    for key in ("development_audit", "development_trades"):
        if (output / config["outputs"][key]).exists():
            raise ValueError("V30 development outcome existed before alias lock")
    lock_path = ROOT / "outputs" / "V30_SIMULATOR_ALIAS_LOCK.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        raise FileExistsError("V30 simulator alias is already locked")
    package_paths = [(ROOT / relative).resolve() for relative in PACKAGE_FILES]
    missing = [str(path) for path in package_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    contract = {
        "schema_version": "xauusd_v30_simulator_alias_lock",
        "v30_contract_sha256": V30_CONTRACT_SHA,
        "timestamp_adapter_contract_sha256": TRANSPORT_CONTRACT_SHA,
        "v30_contract_file": record(v30_contract_path, v30),
        "timestamp_adapter_contract_file": record(transport_path, v30),
        "package_files": [record(path, v30) for path in package_paths],
        "aliases": {
            "signed_update_imbalance": "impulse_update_imbalance",
            "displacement_price": "impulse_displacement_price",
        },
        "development_outcomes_opened_at_lock": False,
        "strategy_change": False,
        "model_training_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    contract["alias_contract_sha256"] = v30.canonical_hash(
        contract, "alias_contract_sha256"
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
