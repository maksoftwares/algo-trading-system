from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


DECISION_RELATIVE_PATH = Path("docs/SECOND_EA_PARTIAL_DATA_OWNER_DECISION.md")
READINESS_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_DATA_EXTENSION_READINESS.md")
READINESS_JSON_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_DATA_EXTENSION_READINESS.json")
REQUIRED_DECISION = "OWNER_ACCEPTED_PARTIAL_DATA"


@dataclass(frozen=True)
class PartialDataDecision:
    status: str
    owner_decision: str
    decision_status: str
    accepted_report_sha256: str
    current_report_sha256: str
    message: str


def validate_partial_data_decision(
    root: Path,
    current_readiness_content_sha256: str | None = None,
) -> PartialDataDecision:
    decision_path = root / DECISION_RELATIVE_PATH
    readiness_path = root / READINESS_RELATIVE_PATH
    if not readiness_path.exists():
        return _decision("FAIL", "", "", "", "", f"Missing readiness report: {readiness_path}")

    current_hash = current_readiness_content_sha256 or _current_readiness_content_hash(root)
    if not decision_path.exists():
        return _decision(
            "NOT_SIGNED",
            "",
            "",
            "",
            current_hash,
            f"Missing owner decision file: {decision_path}",
        )

    fields = _parse_fields(decision_path)
    owner_decision = fields.get("owner_decision", "")
    decision_status = fields.get("decision_status", "")
    accepted_hash = fields.get("accepted_readiness_content_sha256") or fields.get(
        "accepted_report_sha256", ""
    )
    signed = owner_decision == REQUIRED_DECISION and decision_status == "SIGNED"
    hash_matches = accepted_hash == current_hash

    if signed and hash_matches:
        return _decision(
            "OWNER_ACCEPTED_PARTIAL",
            owner_decision,
            decision_status,
            accepted_hash,
            current_hash,
            "Owner accepted partial data for the exact current readiness content hash.",
        )
    if signed and not hash_matches:
        return _decision(
            "STALE_SIGNATURE",
            owner_decision,
            decision_status,
            accepted_hash,
            current_hash,
            "Owner decision is signed but does not match the current readiness content hash.",
        )
    return _decision(
        "NOT_SIGNED",
        owner_decision,
        decision_status,
        accepted_hash,
        current_hash,
        "Owner partial-data acceptance is not signed.",
    )


def render_decision_status(decision: PartialDataDecision) -> str:
    return "\n".join(
        [
            "# Second EA Partial Data Owner Decision Status",
            "",
            f"Status: {decision.status}",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| owner_decision | `{decision.owner_decision}` |",
            f"| decision_status | `{decision.decision_status}` |",
            f"| accepted_readiness_content_sha256 | `{decision.accepted_report_sha256}` |",
            f"| current_readiness_content_sha256 | `{decision.current_report_sha256}` |",
            "",
            "## Message",
            "",
            decision.message,
            "",
            "A status other than `OWNER_ACCEPTED_PARTIAL` keeps second-EA candidate matrix runs blocked.",
            "",
        ]
    )


def _decision(
    status: str,
    owner_decision: str,
    decision_status: str,
    accepted_report_sha256: str,
    current_report_sha256: str,
    message: str,
) -> PartialDataDecision:
    return PartialDataDecision(
        status=status,
        owner_decision=owner_decision,
        decision_status=decision_status,
        accepted_report_sha256=accepted_report_sha256,
        current_report_sha256=current_report_sha256,
        message=message,
    )


def _parse_fields(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("##"):
            break
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if key not in fields:
            fields[key] = value.strip().strip("`")
    return fields


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _current_readiness_content_hash(root: Path) -> str:
    json_path = root / READINESS_JSON_RELATIVE_PATH
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        content_hash = payload.get("readiness_content_sha256")
        if content_hash:
            return str(content_hash)
    return _sha256_file(root / READINESS_RELATIVE_PATH)
