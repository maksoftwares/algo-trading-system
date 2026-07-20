from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
CALIBRATION_AUDIT = OUTPUTS / "COMEX_SIZE_SEGMENT_V32_CALIBRATION_AUDIT.json"
LOCK = OUTPUTS / "COMEX_SIZE_SEGMENT_V32_CONTRACT_LOCK.json"
TRACKED = [
    "PREREGISTRATION.md",
    "README.md",
    "requirements.txt",
    "config/comex_size_segment_flow_v32.json",
    "prepare_calibration.py",
    "lock_contract.py",
    "run_stage.py",
    "src/__init__.py",
    "src/size_segment_flow.py",
    "tests/test_size_segment_flow.py",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contract_digest(payload: dict[str, Any]) -> str:
    clean = {key: value for key, value in payload.items() if key != "contract_sha256"}
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_payload() -> dict[str, Any]:
    if not CALIBRATION_AUDIT.is_file():
        raise FileNotFoundError("Outcome-blind calibration audit is missing.")
    audit = json.loads(CALIBRATION_AUDIT.read_text(encoding="utf-8"))
    if (
        audit.get("economic_outcomes_opened") is not False
        or audit.get("pnl_opened") is not False
    ):
        raise RuntimeError("Calibration audit opened forbidden economic outcomes.")
    if audit.get("decision") != "V32_CALIBRATION_PASS_READY_TO_LOCK":
        raise RuntimeError("Calibration did not identify a frequency-capable policy.")
    if not audit.get("selected_policy"):
        raise RuntimeError("Calibration audit has no selected policy.")
    file_hashes = {name: _sha256(ROOT / name) for name in TRACKED}
    payload: dict[str, Any] = {
        "schema_version": "xauusd_comex_size_segment_v32_contract_lock",
        "campaign_id": "comex-size-segment-flow-v32",
        "calibration_audit_sha256": _sha256(CALIBRATION_AUDIT),
        "calibration_payload_sha256": audit["audit_sha256"],
        "selected_policy": audit["selected_policy"],
        "selected_candidates_sha256": audit["selected_candidates_sha256"],
        "tracked_file_sha256": file_hashes,
        "economic_outcomes_opened_at_lock": False,
        "same_version_tuning_authorized": False,
        "broker_action_authorized": False,
    }
    payload["contract_sha256"] = _contract_digest(payload)
    return payload


def verify_lock() -> dict[str, Any]:
    if not LOCK.is_file():
        raise FileNotFoundError("V32 contract lock is missing.")
    observed = json.loads(LOCK.read_text(encoding="utf-8"))
    expected = build_payload()
    if observed != expected:
        raise RuntimeError("V32 immutable contract verification failed.")
    return observed


def main() -> None:
    payload = build_payload()
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        observed = json.loads(LOCK.read_text(encoding="utf-8"))
        if observed != payload:
            raise RuntimeError("Existing V32 lock differs from the current contract.")
        print(f"verified {payload['contract_sha256']}")
        return
    LOCK.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"locked {payload['contract_sha256']}")


if __name__ == "__main__":
    main()
