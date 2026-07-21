from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from capacity import canonical_hash, sha256_file  # noqa: E402


CONFIG = ROOT / "config" / "two_trade_capacity_audit_v85.json"
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/two_trade_capacity_audit_v85.json",
    "src/__init__.py",
    "src/capacity.py",
    "lock_contract.py",
    "run_audit.py",
    "tests/conftest.py",
    "tests/test_capacity.py",
)


def record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def build_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    package_paths = [ROOT / name for name in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    source_records = []
    for source in config["sources"].values():
        path = REPO_ROOT / str(source["path"])
        if sha256_file(path) != source["sha256"]:
            raise ValueError(f"V85 source hash changed: {path}")
        source_records.append(record(path, REPO_ROOT))
    lock: dict[str, Any] = {
        "schema_version": "xauusd_two_trade_capacity_audit_v85_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "source_files": source_records,
        "expected": config["expected"],
        "target_trades_per_weekday": config["target_trades_per_weekday"],
        "required_windows": config["required_windows"],
        "research_controls": config["research_controls"],
        "capacity_result_opened_before_lock": False,
        "v59_v60_modified": False,
    }
    lock["contract_sha256"] = canonical_hash(lock, "contract_sha256")
    return lock


def verify_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    path = ROOT / str(config["outputs"]["directory"]) / str(
        config["outputs"]["contract_lock"]
    )
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock != build_lock(config):
        raise ValueError("V85 immutable contract verification failed")
    return lock


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("V85 contract already exists")
    forbidden = [
        output / str(config["outputs"][key])
        for key in ("windows", "rejection_reasons", "result_json", "result_markdown")
    ]
    if existing := [str(path) for path in forbidden if path.exists()]:
        raise ValueError(f"V85 result existed before lock: {existing}")
    lock = build_lock(config)
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"contract_sha256": lock["contract_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
