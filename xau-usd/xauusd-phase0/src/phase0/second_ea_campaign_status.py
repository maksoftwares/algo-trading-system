from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from phase0.constants import SECOND_EA_LANE_A_CANDIDATES, SECOND_EA_LANE_B_CANDIDATES
from phase0.second_ea_hypotheses import validate_second_ea_hypothesis
from phase0.second_ea_preflight import evaluate_second_ea_preflight


STATUS_REPORT_RELATIVE_PATH = Path("outputs/reports/SECOND_EA_RESEARCH_CAMPAIGN_STATUS.md")


@dataclass(frozen=True)
class CampaignMilestone:
    milestone_id: str
    milestone_name: str
    status: str
    blocking_reason: str
    last_updated_utc: str
    output_file: str


@dataclass(frozen=True)
class CampaignStatusReport:
    status: str
    generated_at_utc: str
    report_path: Path
    milestones: tuple[CampaignMilestone, ...]


def generate_second_ea_campaign_status(root: Path) -> CampaignStatusReport:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report_path = root / STATUS_REPORT_RELATIVE_PATH
    milestones = tuple(evaluate_second_ea_campaign_milestones(root, generated_at))
    # OWNER_ACCEPTED_PARTIAL is a terminal owner-signed state (matrix runs allowed with
    # DATA_WINDOW_ASYMMETRY_PRESENT disclosed), not a blocker.
    acceptable = {"PASS", "OWNER_ACCEPTED_PARTIAL"}
    overall = "PASS" if all(milestone.status in acceptable for milestone in milestones) else "BLOCKED"
    report = CampaignStatusReport(
        status=overall,
        generated_at_utc=generated_at,
        report_path=report_path,
        milestones=milestones,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_campaign_status(report), encoding="utf-8")
    return report


def evaluate_second_ea_campaign_milestones(root: Path, timestamp_utc: str) -> list[CampaignMilestone]:
    preflight = evaluate_second_ea_preflight(root)
    safety_status = _status_line(root / "outputs/reports/SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md") or "MISSING"
    lowfreq_test_status = _status_line(root / "outputs/reports/SECOND_EA_LOW_FREQ_GATE_TESTS.md") or "MISSING"
    event_status = _status_line(root / "outputs/reports/EVENT_CLOCK_VALIDATION_REPORT.md") or "MISSING"
    goal_status = _status_line(root / "outputs/reports/SECOND_EA_GOAL_COMPLETION_AUDIT.md") or "MISSING"
    missing_inputs = _missing_inputs(root / "outputs/reports/SECOND_EA_RESEARCH_MISSING_INPUTS.md")
    lane_a_complete = _results_complete(root, SECOND_EA_LANE_A_CANDIDATES)
    lane_b_complete = _results_complete(root, SECOND_EA_LANE_B_CANDIDATES)
    lane_a_locked = _hypotheses_locked(root, SECOND_EA_LANE_A_CANDIDATES)
    lane_b_locked = _hypotheses_locked(root, SECOND_EA_LANE_B_CANDIDATES)

    m1_status = _m1_status(preflight.data_readiness_status, preflight.partial_data_decision_status)
    return [
        CampaignMilestone(
            "M0",
            "Safety boundary and no-runtime-touch audit",
            "PASS" if safety_status == "PASS" else "BLOCKED",
            "Static safety audit status is PASS; no runtime or broker-action command is authorized."
            if safety_status == "PASS"
            else f"Safety audit status is {safety_status}.",
            timestamp_utc,
            "outputs/reports/SECOND_EA_NO_RUNTIME_TOUCH_AUDIT.md",
        ),
        CampaignMilestone(
            "M1",
            "Data extension readiness",
            m1_status,
            _m1_reason(preflight.data_readiness_status, preflight.partial_data_decision_status),
            timestamp_utc,
            "outputs/reports/SECOND_EA_DATA_EXTENSION_READINESS.md",
        ),
        CampaignMilestone(
            "M2",
            "Low-frequency gate set locked",
            "PASS" if preflight.lowfreq_gate_hash_status == "LOCKED" and lowfreq_test_status == "PASS" else "BLOCKED",
            (
                "Gate-set hash is LOCKED and generated low-frequency gate-test evidence is PASS."
                if preflight.lowfreq_gate_hash_status == "LOCKED" and lowfreq_test_status == "PASS"
                else f"Gate hash={preflight.lowfreq_gate_hash_status}; gate tests={lowfreq_test_status}."
            ),
            timestamp_utc,
            "docs/PHASE0_LOWFREQ_GATE_SET_V1.md",
        ),
        CampaignMilestone(
            "M3",
            "Lane A hypotheses locked",
            "PASS" if lane_a_locked else ("BLOCKED" if not preflight.matrix_runs_allowed else "NOT_STARTED"),
            "Lane A hypotheses are not locked; M1/preflight must pass before candidate run evidence can be produced."
            if not lane_a_locked
            else "Lane A hypothesis files and locks validate.",
            timestamp_utc,
            "outputs/reports/LANE_A_RULE_RECONSTRUCTION_NOTES.md",
        ),
        CampaignMilestone(
            "M4",
            "Lane A matrix runs complete",
            "PASS" if lane_a_complete else ("BLOCKED" if not preflight.matrix_runs_allowed else "NOT_STARTED"),
            "Lane A result-producing matrix runs remain blocked by second-EA preflight."
            if not lane_a_complete and not preflight.matrix_runs_allowed
            else ("Lane A first-pass verdicts are complete." if lane_a_complete else "Lane A runs are not started."),
            timestamp_utc,
            "outputs/reports/SECOND_EA_MATRIX_MANIFEST.csv",
        ),
        CampaignMilestone(
            "M5",
            "Lane A verdicts complete",
            "PASS" if lane_a_complete else "BLOCKED",
            "Lane A has no market-evidence verdicts while M1/preflight is blocked."
            if not lane_a_complete
            else "Lane A first-pass verdicts are complete.",
            timestamp_utc,
            "outputs/reports/A1_FULLHIST_FAILURE_MODE_REVIEW.md",
        ),
        CampaignMilestone(
            "M6",
            "Event-clock validation complete",
            "PASS" if event_status == "PASS" else "BLOCKED",
            "Offline event-clock schema and DST validation report is PASS."
            if event_status == "PASS"
            else f"Event-clock validation status is {event_status}.",
            timestamp_utc,
            "outputs/reports/EVENT_CLOCK_VALIDATION_REPORT.md",
        ),
        CampaignMilestone(
            "M7",
            "Lane B hypotheses locked",
            "PASS" if lane_b_locked else ("NOT_STARTED" if not lane_a_complete else "BLOCKED"),
            "Lane B remains after Lane A unless owner override is supplied; hypotheses are not locked."
            if not lane_b_locked
            else "Lane B hypothesis files and locks validate.",
            timestamp_utc,
            "outputs/reports/B1_ANCESTRY_COMPARISON_REPORT.md",
        ),
        CampaignMilestone(
            "M8",
            "Lane B matrix runs complete",
            "PASS" if lane_b_complete else ("NOT_STARTED" if not lane_b_locked else "BLOCKED"),
            "Lane B cannot run until M7 passes and second-EA preflight is PASS."
            if not lane_b_complete
            else "Lane B first-pass verdicts are complete.",
            timestamp_utc,
            "",
        ),
        CampaignMilestone(
            "M9",
            "D2 / Reality Check complete for any passing candidate",
            "PASS"
            if lane_a_complete and lane_b_complete and not _passing_candidates(root)
            else "NOT_STARTED",
            "All campaign verdicts are final with zero passing candidates; D2 applies only to "
            "passing candidates and is vacuously satisfied."
            if lane_a_complete and lane_b_complete and not _passing_candidates(root)
            else _d2_reason(root / "outputs/reports/SECOND_EA_D2_UNIVERSE_MANIFEST.csv"),
            timestamp_utc,
            "outputs/reports/SECOND_EA_D2_UNIVERSE_MANIFEST.csv",
        ),
        CampaignMilestone(
            "M10",
            "Final campaign report complete",
            "PASS" if goal_status == "PASS" and not missing_inputs else "BLOCKED",
            "Final campaign report and goal audit are complete."
            if goal_status == "PASS" and not missing_inputs
            else "Goal audit remains blocked"
            + (f"; missing exact source input: {', '.join(missing_inputs)}." if missing_inputs else "."),
            timestamp_utc,
            "outputs/reports/SECOND_EA_GOAL_COMPLETION_AUDIT.md",
        ),
    ]


def _passing_candidates(root: Path) -> list[str]:
    passing: list[str] = []
    for candidate in (*SECOND_EA_LANE_A_CANDIDATES, *SECOND_EA_LANE_B_CANDIDATES):
        text = _read_text(root / "outputs" / "reports" / f"FIRST_PASS_{candidate}.md")
        if "Final verdict: PASS_APPROVED_FUTURE_EXPERT_CANDIDATE" in text:
            passing.append(candidate)
    return passing


def render_campaign_status(report: CampaignStatusReport) -> str:
    rows = [
        {
            "milestone_id": milestone.milestone_id,
            "milestone_name": milestone.milestone_name,
            "status": milestone.status,
            "blocking_reason": milestone.blocking_reason,
            "last_updated_utc": milestone.last_updated_utc,
            "output_file": f"`{milestone.output_file}`" if milestone.output_file else "",
        }
        for milestone in report.milestones
    ]
    return "\n".join(
        [
            "# Second EA Research Campaign Status",
            "",
            f"Status: {report.status}",
            f"Generated at UTC: {report.generated_at_utc}",
            "",
            _markdown_table(
                rows,
                [
                    "milestone_id",
                    "milestone_name",
                    "status",
                    "blocking_reason",
                    "last_updated_utc",
                    "output_file",
                ],
            ),
            "",
            "This report is generated by `scripts/generate_second_ea_campaign_status.py`.",
            "",
            "Research-only boundary: no observer deployment, demo execution, paper trading, live trading, MT5 runtime access, preset mutation, or broker action is authorized.",
            "",
        ]
    )


def _m1_status(readiness_status: str, partial_decision_status: str) -> str:
    if readiness_status == "PASS":
        return "PASS"
    if readiness_status == "PARTIAL" and partial_decision_status == "OWNER_ACCEPTED_PARTIAL":
        return "OWNER_ACCEPTED_PARTIAL"
    return "BLOCKED"


def _m1_reason(readiness_status: str, partial_decision_status: str) -> str:
    if readiness_status == "PASS":
        return "Data readiness is PASS."
    if readiness_status == "PARTIAL" and partial_decision_status == "OWNER_ACCEPTED_PARTIAL":
        return "Owner accepted partial data; all outputs must disclose DATA_WINDOW_ASYMMETRY_PRESENT."
    return f"Data readiness is {readiness_status}; partial-data owner decision is {partial_decision_status}."


def _hypotheses_locked(root: Path, candidates: tuple[str, ...]) -> bool:
    for candidate in candidates:
        hypothesis = root / "docs" / f"hypothesis_{candidate}.md"
        lock = root / "docs" / f"hypothesis_{candidate}.sha256.json"
        if validate_second_ea_hypothesis(hypothesis, lock).status != "PASS":
            return False
    return True


def _results_complete(root: Path, candidates: tuple[str, ...]) -> bool:
    final_verdicts = {
        "PASS_APPROVED_FUTURE_EXPERT_CANDIDATE",
        "FAIL_REJECTED_VERSION_FINAL",
    }
    for candidate in candidates:
        text = _read_text(root / "outputs" / "reports" / f"FIRST_PASS_{candidate}.md")
        if not any(f"Final verdict: {verdict}" in text for verdict in final_verdicts):
            return False
    return True


def _d2_reason(manifest: Path) -> str:
    if not manifest.exists():
        return "D2 universe manifest is missing."
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    included = [row for row in rows if row.get("d2_included") == "true"]
    blocked_campaign = [
        row
        for row in rows
        if row.get("lane") in {"A", "B"} and row.get("matrix_ledger_status") == "NOT_RUN"
    ]
    return (
        "No passing second-EA candidate yet; "
        f"included_historical_ledgers={len(included)}; "
        f"blocked_campaign_placeholders_excluded={len(blocked_campaign)}."
    )


def _missing_inputs(report: Path) -> tuple[str, ...]:
    text = _read_text(report)
    missing: list[str] = []
    for line in text.splitlines():
        if "| `" not in line or "| MISSING |" not in line:
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            missing.append(parts[1].strip().strip("`"))
    return tuple(missing)


def _status_line(path: Path) -> str:
    for line in _read_text(path).splitlines():
        if line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


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
