from __future__ import annotations

import json
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phase0.constants import (
    SECOND_EA_CAMPAIGN_CANDIDATES,
    SECOND_EA_LANE_A_CANDIDATES,
    SECOND_EA_LANE_B_CANDIDATES,
)
from phase0.hashing import sha256_file
from phase0.second_ea_hypotheses import validate_second_ea_hypothesis
from phase0.second_ea_partial_data import validate_partial_data_decision
from phase0.second_ea_preflight import evaluate_second_ea_preflight


AUDIT_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_GOAL_COMPLETION_AUDIT.md")
AUDIT_JSON_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_GOAL_COMPLETION_AUDIT.json")


@dataclass(frozen=True)
class GoalRequirement:
    requirement_id: str
    requirement: str
    status: str
    evidence: str


@dataclass(frozen=True)
class GoalAudit:
    status: str
    generated_at_utc: str
    report_path: Path
    json_path: Path
    requirements: tuple[GoalRequirement, ...]


def generate_second_ea_goal_audit(root: Path) -> GoalAudit:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report_path = root / AUDIT_RELATIVE_PATH
    json_path = root / AUDIT_JSON_RELATIVE_PATH
    requirements = tuple(_evaluate_requirements(root))
    overall = "PASS" if all(item.status == "PASS" for item in requirements) else "BLOCKED"
    audit = GoalAudit(
        status=overall,
        generated_at_utc=generated_at,
        report_path=report_path,
        json_path=json_path,
        requirements=requirements,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_goal_audit(audit), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "status": audit.status,
                "generated_at_utc": audit.generated_at_utc,
                "requirements": [asdict(requirement) for requirement in audit.requirements],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return audit


def render_goal_audit(audit: GoalAudit) -> str:
    rows = [
        {
            "ID": item.requirement_id,
            "Status": item.status,
            "Requirement": item.requirement,
            "Evidence": item.evidence,
        }
        for item in audit.requirements
    ]
    return "\n".join(
        [
            "# Second EA Goal Completion Audit",
            "",
            f"Status: {audit.status}",
            f"Generated at UTC: {audit.generated_at_utc}",
            "",
            "## Boundary",
            "",
            "This audit is evidence-only. It does not authorize candidate matrix runs, observer deployment, demo execution, live execution, MT5 runtime access, or broker action.",
            "",
            "## Definition Of Done Evidence",
            "",
            _markdown_table(rows, ["ID", "Status", "Requirement", "Evidence"]),
            "",
            "A status other than `PASS` means the full second-EA goal remains incomplete.",
            "",
        ]
    )


def _evaluate_requirements(root: Path) -> list[GoalRequirement]:
    preflight = evaluate_second_ea_preflight(root)
    partial_decision = validate_partial_data_decision(root)
    readiness = _read_json(root / "outputs" / "reports" / "SECOND_EA_DATA_EXTENSION_READINESS.json")
    requirements: list[GoalRequirement] = []

    missing_inputs_report = root / "outputs" / "reports" / "SECOND_EA_RESEARCH_MISSING_INPUTS.md"
    missing_inputs = _missing_input_names(missing_inputs_report)
    requirements.append(
        _requirement(
            "PRE-1",
            "Required source documents were checked by exact filename before coding.",
            "PASS" if missing_inputs_report.exists() and not missing_inputs else "MISSING",
            (
                f"{missing_inputs_report}: missing_count={len(missing_inputs)}"
                + (f"; missing={', '.join(missing_inputs)}" if missing_inputs else "")
            ),
        )
    )

    safety_path = root / "outputs" / "reports" / "SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md"
    safety_status = _status_line(safety_path)
    requirements.append(
        _requirement(
            "DOD-1",
            "SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md exists and says PASS.",
            "PASS" if safety_status == "PASS" else "MISSING",
            f"{safety_path}: Status={safety_status or 'MISSING'}",
        )
    )

    readiness_status = str(readiness.get("overall_status", "MISSING"))
    owner_accepted = partial_decision.status == "OWNER_ACCEPTED_PARTIAL"
    requirements.append(
        _requirement(
            "DOD-2",
            "SECOND_EA_DATA_EXTENSION_READINESS.md exists and says PASS or owner-accepted PARTIAL.",
            "PASS" if readiness_status == "PASS" or owner_accepted else "BLOCKED",
            (
                f"readiness={readiness_status}; partial_data_decision={partial_decision.status}; "
                f"matrix_runs_allowed={str(preflight.matrix_runs_allowed).lower()}"
            ),
        )
    )

    lowfreq_doc = root / "docs" / "PHASE0_LOWFREQ_GATE_SET_V1.md"
    lowfreq_hash = _read_json(root / "docs" / "PHASE0_LOWFREQ_GATE_SET_V1.sha256.json")
    lowfreq_lock_status = _lowfreq_lock_status(lowfreq_doc, lowfreq_hash)
    requirements.append(
        _requirement(
            "DOD-3",
            "PHASE0_LOWFREQ_GATE_SET_V1.md is written and SHA256-locked before runs.",
            "PASS" if lowfreq_lock_status == "LOCKED" else "MISSING",
            f"doc_exists={lowfreq_doc.exists()}; hash_status={lowfreq_lock_status}",
        )
    )

    requirements.append(
        _requirement(
            "DOD-4",
            "A1, A2, and A3 hypotheses are written and SHA256-locked before runs.",
            _hypothesis_status(root, SECOND_EA_LANE_A_CANDIDATES, preflight.matrix_runs_allowed),
            _hypothesis_evidence(root, SECOND_EA_LANE_A_CANDIDATES),
        )
    )

    requirements.append(
        _requirement(
            "DOD-5",
            "Lane A results are complete.",
            _first_pass_result_status(root, SECOND_EA_LANE_A_CANDIDATES, preflight.matrix_runs_allowed),
            _first_pass_evidence(root, SECOND_EA_LANE_A_CANDIDATES),
        )
    )

    event_report = root / "outputs" / "reports" / "EVENT_CLOCK_VALIDATION_REPORT.md"
    event_status = _status_line(event_report)
    requirements.append(
        _requirement(
            "DOD-6",
            "Event-clock validation exists before Lane B.",
            "PASS" if event_status == "PASS" else "MISSING",
            f"{event_report}: Status={event_status or 'MISSING'}",
        )
    )

    lane_b_status = "BLOCKED" if _lane_a_not_complete(root) else "NOT_STARTED"
    requirements.append(
        _requirement(
            "DOD-7",
            "B1, B2, and B3 hypotheses are written and SHA256-locked before runs.",
            _hypothesis_status(root, SECOND_EA_LANE_B_CANDIDATES, preflight.matrix_runs_allowed, lane_b_status),
            _hypothesis_evidence(root, SECOND_EA_LANE_B_CANDIDATES),
        )
    )

    requirements.append(
        _requirement(
            "DOD-8",
            "Lane B results are complete.",
            "BLOCKED"
            if _lane_a_not_complete(root) or not preflight.matrix_runs_allowed
            else _first_pass_result_status(root, SECOND_EA_LANE_B_CANDIDATES, preflight.matrix_runs_allowed),
            _first_pass_evidence(root, SECOND_EA_LANE_B_CANDIDATES),
        )
    )

    d2_manifest = root / "outputs" / "reports" / "SECOND_EA_D2_UNIVERSE_MANIFEST.csv"
    campaign_complete = (
        _first_pass_result_status(root, SECOND_EA_CAMPAIGN_CANDIDATES, preflight.matrix_runs_allowed) == "PASS"
    )
    passing_candidates = _passing_candidates(root, SECOND_EA_CAMPAIGN_CANDIDATES)
    if not campaign_complete:
        d2_status = "NOT_STARTED"
        d2_evidence = _d2_manifest_evidence(d2_manifest)
    elif not passing_candidates:
        d2_status = "PASS"
        d2_evidence = (
            "All six campaign verdicts are final with zero passing candidates; the D2 requirement "
            "applies only to passing candidates and is vacuously satisfied. "
            + _d2_manifest_evidence(d2_manifest)
        )
    else:
        d2_status = "NOT_STARTED"
        d2_evidence = (
            f"Passing candidates awaiting D2: {', '.join(passing_candidates)}. "
            + _d2_manifest_evidence(d2_manifest)
        )
    requirements.append(
        _requirement(
            "DOD-9",
            "D2 is run for any passing candidate using candidate-level and family-clustered views.",
            d2_status,
            d2_evidence,
        )
    )

    final_report = root / "outputs" / "reports" / "SECOND_EA_RESEARCH_CAMPAIGN_2026_06_10.md"
    final_text = _read_text(final_report)
    requirements.append(
        _requirement(
            "DOD-10",
            "Final campaign report exists.",
            "BLOCKED" if "CAMPAIGN_BLOCKED_BEFORE_CANDIDATE_RUNS" in final_text else ("PASS" if final_report.exists() else "MISSING"),
            f"{final_report}: blocked pre-run report exists={final_report.exists()}",
        )
    )

    backlog = root / "docs" / "CANDIDATE_RESEARCH_BACKLOG.md"
    backlog_text = _read_text(backlog)
    requirements.append(
        _requirement(
            "DOD-11",
            "CANDIDATE_RESEARCH_BACKLOG.md is updated.",
            "PASS" if "second-EA campaign note" in backlog_text else "MISSING",
            f"{backlog}: second-EA campaign note present={'second-EA campaign note' in backlog_text}",
        )
    )

    requirements.append(
        _requirement(
            "DOD-12",
            "No current EA, MT5 runtime, demo account, or broker-action file was touched.",
            "PASS" if safety_status == "PASS" else "MISSING",
            f"Safety audit status={safety_status or 'MISSING'}; no runtime command was required for this audit.",
        )
    )

    changed_files_section_present = "## Changed Files And Commands" in final_text
    requirements.append(
        _requirement(
            "DOD-13",
            "Final response lists changed files, commands run, and any commands not run.",
            "PASS" if changed_files_section_present else "NOT_STARTED",
            (
                f"{final_report}: 'Changed Files And Commands' section present={changed_files_section_present}; "
                "the same listing must accompany the final user-facing response."
            ),
        )
    )
    return requirements


def _passing_candidates(root: Path, candidates: tuple[str, ...]) -> list[str]:
    passing: list[str] = []
    for candidate in candidates:
        text = _read_text(root / "outputs" / "reports" / f"FIRST_PASS_{candidate}.md")
        if "Final verdict: PASS_APPROVED_FUTURE_EXPERT_CANDIDATE" in text:
            passing.append(candidate)
    return passing


def _requirement(requirement_id: str, requirement: str, status: str, evidence: str) -> GoalRequirement:
    return GoalRequirement(
        requirement_id=requirement_id,
        requirement=requirement,
        status=status,
        evidence=evidence,
    )


def _hypothesis_status(
    root: Path,
    candidates: tuple[str, ...],
    matrix_runs_allowed: bool,
    blocked_status: str = "BLOCKED",
) -> str:
    if all(_hypothesis_locked(root, candidate) for candidate in candidates):
        return "PASS"
    return blocked_status if not matrix_runs_allowed else "NOT_STARTED"


def _hypothesis_evidence(root: Path, candidates: tuple[str, ...]) -> str:
    report = root / "outputs" / "reports" / "SECOND_EA_HYPOTHESIS_VALIDATION_REPORT.md"
    report_status = _status_line(report) or "MISSING"
    reconstruction_report = root / "outputs" / "reports" / "LANE_A_RULE_RECONSTRUCTION_NOTES.md"
    reconstruction_status = _status_line(reconstruction_report) or "MISSING"
    parts: list[str] = []
    for candidate in candidates:
        hypothesis = root / "docs" / f"hypothesis_{candidate}.md"
        lock = root / "docs" / f"hypothesis_{candidate}.sha256.json"
        parts.append(f"{candidate}: hypothesis={hypothesis.exists()}, lock={lock.exists()}")
    evidence = f"{report}: Status={report_status}; " + "; ".join(parts)
    if any(candidate.endswith("_v1_fullhist") for candidate in candidates):
        evidence += f"; {reconstruction_report}: Status={reconstruction_status}"
    return evidence


def _hypothesis_locked(root: Path, candidate: str) -> bool:
    hypothesis = root / "docs" / f"hypothesis_{candidate}.md"
    lock = root / "docs" / f"hypothesis_{candidate}.sha256.json"
    return validate_second_ea_hypothesis(hypothesis, lock).status == "PASS"


def _first_pass_result_status(
    root: Path,
    candidates: tuple[str, ...],
    matrix_runs_allowed: bool,
) -> str:
    texts = [_read_text(root / "outputs" / "reports" / f"FIRST_PASS_{candidate}.md") for candidate in candidates]
    if texts and all("Final verdict: PASS_APPROVED_FUTURE_EXPERT_CANDIDATE" in text or "Final verdict: FAIL_REJECTED_VERSION_FINAL" in text for text in texts):
        return "PASS"
    return "BLOCKED" if not matrix_runs_allowed else "NOT_STARTED"


def _first_pass_evidence(root: Path, candidates: tuple[str, ...]) -> str:
    parts: list[str] = []
    for candidate in candidates:
        report = root / "outputs" / "reports" / f"FIRST_PASS_{candidate}.md"
        text = _read_text(report)
        verdict = "MISSING"
        for line in text.splitlines():
            if line.startswith("Final verdict:"):
                verdict = line.split(":", 1)[1].strip()
                break
        parts.append(f"{candidate}: {verdict}")
    return "; ".join(parts)


def _d2_manifest_evidence(manifest: Path) -> str:
    if not manifest.exists():
        return f"{manifest}: missing"
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    included = [row for row in rows if row.get("d2_included") == "true"]
    campaign_excluded = [
        row
        for row in rows
        if row.get("lane") in {"A", "B"} and row.get("matrix_ledger_status") == "NOT_RUN"
    ]
    families = {row.get("family", "") for row in included if row.get("family")}
    return (
        f"{manifest}: no passing second-EA candidate yet; "
        f"d2_universe_rows={len(rows)}; included_historical_ledgers={len(included)}; "
        f"family_clusters={len(families)}; blocked_campaign_placeholders_excluded={len(campaign_excluded)}"
    )


def _missing_input_names(report: Path) -> tuple[str, ...]:
    text = _read_text(report)
    missing: list[str] = []
    for line in text.splitlines():
        if "| `" not in line or "| MISSING |" not in line:
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            missing.append(parts[1].strip().strip("`"))
    return tuple(missing)


def _lowfreq_lock_status(doc_path: Path, lock_payload: dict[str, Any]) -> str:
    if not doc_path.exists():
        return "MISSING_DOCUMENT"
    if lock_payload.get("status") != "LOCKED":
        return str(lock_payload.get("status", "MISSING"))
    locked_hash = str(lock_payload.get("sha256", ""))
    if not locked_hash:
        return "MISSING_SHA256"
    if locked_hash != sha256_file(doc_path):
        return "STALE_SHA256"
    return "LOCKED"


def _lane_a_not_complete(root: Path) -> bool:
    return _first_pass_result_status(root, SECOND_EA_LANE_A_CANDIDATES, matrix_runs_allowed=False) != "PASS"


def _status_line(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _markdown_table(rows: list[dict[str, str]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)
