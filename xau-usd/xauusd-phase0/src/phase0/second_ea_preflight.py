from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase0.hashing import sha256_file
from phase0.second_ea_partial_data import PartialDataDecision, validate_partial_data_decision


READINESS_JSON_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_DATA_EXTENSION_READINESS.json")
SAFETY_REPORT_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md")
LOWFREQ_HASH_RELATIVE_PATH = Path("docs/PHASE0_LOWFREQ_GATE_SET_V1.sha256.json")
LOWFREQ_DOC_RELATIVE_PATH = Path("docs/PHASE0_LOWFREQ_GATE_SET_V1.md")


@dataclass(frozen=True)
class SecondEaPreflightResult:
    status: str
    matrix_runs_allowed: bool
    safety_status: str
    data_readiness_status: str
    partial_data_decision_status: str
    lowfreq_gate_hash_status: str
    message: str


def evaluate_second_ea_preflight(root: Path) -> SecondEaPreflightResult:
    safety_status = _read_safety_status(root / SAFETY_REPORT_RELATIVE_PATH)
    readiness = _read_json(root / READINESS_JSON_RELATIVE_PATH)
    readiness_status = str(readiness.get("overall_status", "MISSING"))
    lowfreq_hash_status = _read_lowfreq_hash_status(
        root / LOWFREQ_HASH_RELATIVE_PATH,
        root / LOWFREQ_DOC_RELATIVE_PATH,
    )
    partial_decision = validate_partial_data_decision(root)

    data_ok = readiness_status == "PASS" or (
        readiness_status == "PARTIAL" and partial_decision.status == "OWNER_ACCEPTED_PARTIAL"
    )
    allowed = safety_status == "PASS" and data_ok and lowfreq_hash_status == "LOCKED"
    blockers: list[str] = []
    if safety_status != "PASS":
        blockers.append(f"M0 safety status is {safety_status}.")
    if not data_ok:
        blockers.append(
            f"M1 data readiness is {readiness_status}; partial-data decision is {partial_decision.status}."
        )
    if lowfreq_hash_status != "LOCKED":
        blockers.append(f"M2 low-frequency gate hash status is {lowfreq_hash_status}.")

    return SecondEaPreflightResult(
        status="PASS" if allowed else "BLOCKED",
        matrix_runs_allowed=allowed,
        safety_status=safety_status,
        data_readiness_status=readiness_status,
        partial_data_decision_status=partial_decision.status,
        lowfreq_gate_hash_status=lowfreq_hash_status,
        message="Second-EA candidate matrix runs are allowed."
        if allowed
        else " ".join(blockers),
    )


def render_preflight_report(result: SecondEaPreflightResult) -> str:
    return "\n".join(
        [
            "# Second EA Run Preflight",
            "",
            f"Status: {result.status}",
            f"Matrix runs allowed: {str(result.matrix_runs_allowed).lower()}",
            "",
            "| Check | Status |",
            "| --- | --- |",
            f"| M0 safety audit | `{result.safety_status}` |",
            f"| M1 data readiness | `{result.data_readiness_status}` |",
            f"| M1 partial-data owner decision | `{result.partial_data_decision_status}` |",
            f"| M2 low-frequency gate hash | `{result.lowfreq_gate_hash_status}` |",
            "",
            "## Message",
            "",
            result.message,
            "",
            "No result-producing Lane A or Lane B command may run unless this report is `PASS`.",
            "",
        ]
    )


def _read_safety_status(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return "UNKNOWN"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_lowfreq_hash_status(lock_path: Path, doc_path: Path) -> str:
    if not lock_path.exists():
        return "MISSING"
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "INVALID_JSON"
    if payload.get("status") != "LOCKED":
        return str(payload.get("status", "UNKNOWN"))
    if not doc_path.exists():
        return "MISSING_DOCUMENT"
    locked_hash = str(payload.get("sha256", ""))
    if not locked_hash:
        return "MISSING_SHA256"
    if locked_hash != sha256_file(doc_path):
        return "STALE_SHA256"
    return "LOCKED"
