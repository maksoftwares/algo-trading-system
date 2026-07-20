from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "comex-size-segment-flow-v32"
OUTPUTS = ROOT / "outputs"
AUDIT = OUTPUTS / "COMEX_SIZE_SEGMENT_V33_CALIBRATION_AUDIT.json"
LOCK = OUTPUTS / "COMEX_SIZE_SEGMENT_V33_CONTRACT_LOCK.json"
LOCAL_FILES = [
    "PREREGISTRATION.md",
    "README.md",
    "requirements.txt",
    "config/comex_size_segment_flow_v33.json",
    "prepare_calibration.py",
    "lock_contract.py",
    "run_stage.py",
    "src/__init__.py",
    "src/v33.py",
    "tests/test_v33.py",
]
BASE_FILES = [
    "config/comex_size_segment_flow_v32.json",
    "src/size_segment_flow.py",
    "outputs/COMEX_SIZE_SEGMENT_V32_CALIBRATION_AUDIT.json",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest(payload: dict[str, Any]) -> str:
    clean = {key: value for key, value in payload.items() if key != "contract_sha256"}
    return hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if audit.get("decision") != "V33_CALIBRATION_PASS_READY_TO_LOCK":
        raise RuntimeError("V33 calibration did not pass the frequency-only gate.")
    if (
        audit.get("economic_outcomes_opened") is not False
        or audit.get("pnl_opened") is not False
    ):
        raise RuntimeError("V33 calibration opened prohibited economic outcomes.")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_comex_size_segment_v33_contract_lock",
        "campaign_id": "comex-size-segment-flow-v33",
        "calibration_audit_sha256": _sha256(AUDIT),
        "calibration_payload_sha256": audit["audit_sha256"],
        "selected_policy": audit["selected_policy"],
        "selected_candidates_sha256": audit["selected_candidates_sha256"],
        "local_file_sha256": {name: _sha256(ROOT / name) for name in LOCAL_FILES},
        "base_dependency_sha256": {name: _sha256(BASE / name) for name in BASE_FILES},
        "economic_outcomes_opened_at_lock": False,
        "same_version_tuning_authorized": False,
        "broker_action_authorized": False,
    }
    payload["contract_sha256"] = _digest(payload)
    return payload


def verify_lock() -> dict[str, Any]:
    observed = json.loads(LOCK.read_text(encoding="utf-8"))
    expected = build_payload()
    if observed != expected:
        raise RuntimeError("V33 immutable contract verification failed.")
    return observed


def main() -> None:
    payload = build_payload()
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        if json.loads(LOCK.read_text(encoding="utf-8")) != payload:
            raise RuntimeError("Existing V33 lock differs from the current contract.")
        print(f"verified {payload['contract_sha256']}")
        return
    LOCK.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"locked {payload['contract_sha256']}")


if __name__ == "__main__":
    main()
