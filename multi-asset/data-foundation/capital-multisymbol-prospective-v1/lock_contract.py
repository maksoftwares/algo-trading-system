from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config" / "capital_multisymbol_prospective_v1.json"
OUTPUT = ROOT / "outputs" / "CAPITAL_MULTISYMBOL_PROSPECTIVE_V1_CONTRACT_LOCK.json"
BOUND_FILES = (
    ROOT / "README.md",
    ROOT / "PREREGISTRATION.md",
    ROOT / "requirements.txt",
    CONFIG,
    ROOT / "src" / "__init__.py",
    ROOT / "src" / "collector.py",
    ROOT / "run_collector.py",
    ROOT / "lock_contract.py",
    ROOT / "verify.py",
    ROOT / "tests" / "test_collector.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    boundary = datetime.fromisoformat(
        config["information_boundary"]["start_inclusive_utc"].replace(
            "Z", "+00:00"
        )
    )
    locked_at = datetime.now(tz=UTC)
    if locked_at >= boundary:
        raise RuntimeError("contract must be locked before the prospective boundary")
    data_root = Path(config["storage"]["root"])
    existing = []
    if data_root.exists():
        existing = [str(path) for path in data_root.rglob("*.csv")]
    if existing:
        raise RuntimeError(f"prospective data already exists before lock: {existing[:3]}")
    payload = {
        "schema_version": "capital_multisymbol_prospective_contract_v1",
        "decision": "CAPITAL_MULTISYMBOL_PROSPECTIVE_V1_CONTRACT_LOCKED",
        "locked_at_utc": locked_at.isoformat().replace("+00:00", "Z"),
        "boundary_utc": boundary.isoformat().replace("+00:00", "Z"),
        "account_login": config["account"]["expected_login"],
        "account_server": config["account"]["expected_server"],
        "symbols": config["symbols"],
        "authority": config["authority"],
        "files": {
            path.relative_to(ROOT).as_posix(): sha256(path) for path in BOUND_FILES
        },
        "preboundary_prospective_csv_count": len(existing),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["contract_sha256"] = hashlib.sha256(canonical).hexdigest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

