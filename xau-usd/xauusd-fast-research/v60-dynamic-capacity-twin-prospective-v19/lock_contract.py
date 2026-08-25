from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

from src.capacity import canonical_sha256, sha256_file, utc_timestamp


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config" / "prospective.json"
LOCK = ROOT / "outputs" / "CONTRACT_LOCK.json"

PACKAGE_FILES = (
    "PREREGISTRATION.md",
    "README.md",
    "requirements.txt",
    "lock_contract.py",
    "run_evaluation.py",
    "config/prospective.json",
    "config/replay_contract_snapshot.json",
    "src/__init__.py",
    "src/capacity.py",
    "tests/conftest.py",
    "tests/test_capacity.py",
    "tests/test_runner.py",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def identity(path: Path) -> dict[str, object]:
    return {"bytes": int(path.stat().st_size), "sha256": sha256_file(path)}


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else REPO_ROOT / value


def main() -> int:
    config = read_json(CONFIG)
    boundary = utc_timestamp(config["boundary"]["evidence_start_inclusive_utc"])
    now = datetime.now(UTC)
    if now >= boundary.to_pydatetime():
        raise RuntimeError("V19 cannot be locked at or after its evidence boundary")
    if LOCK.exists():
        raise FileExistsError("V19 contract lock already exists")

    runtime = Path(config["outputs"]["runtime_directory"])
    forbidden = [
        runtime / config["outputs"][name]
        for name in ("state", "status", "resolved_candidates", "portfolio_events")
    ]
    if any(path.exists() for path in forbidden):
        raise RuntimeError("V19 runtime evidence exists before contract lock")

    package_files = {}
    for relative in PACKAGE_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        package_files[relative] = identity(path)

    input_files = {}
    for name, record in config["inputs"].items():
        if not isinstance(record, dict) or "sha256" not in record:
            continue
        path = resolve(str(record["path"]))
        actual = sha256_file(path)
        if actual != str(record["sha256"]):
            raise ValueError(f"V19 input identity changed: {name}: {actual}")
        input_files[name] = {
            "path": str(record["path"]),
            "bytes": int(path.stat().st_size),
            "sha256": actual,
        }

    lock = {
        "schema_version": "v60_dynamic_capacity_twin_prospective_v19_contract_lock",
        "locked_at_utc": now.isoformat().replace("+00:00", "Z"),
        "evidence_start_inclusive_utc": boundary.isoformat().replace("+00:00", "Z"),
        "aggregate_economics_present_at_lock": False,
        "broker_action_authorized": False,
        "deployment_authorized": False,
        "runtime_changes_authorized": False,
        "package_files": package_files,
        "input_files": input_files,
    }
    lock["contract_sha256"] = canonical_sha256(lock)
    payload = json.dumps(lock, indent=2, sort_keys=True) + "\n"
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(payload, encoding="utf-8", newline="\n")
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / config["outputs"]["contract_lock"]).write_text(
        payload, encoding="utf-8", newline="\n"
    )
    print(json.dumps(lock, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
