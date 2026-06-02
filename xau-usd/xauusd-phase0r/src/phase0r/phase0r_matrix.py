from __future__ import annotations

from pathlib import Path

from phase0r.candidate_registry import selected_candidates


RESULT_COMMANDS = {
    "run-matrix": "PHASE0R_MATRIX_STATUS",
    "run-deciles": "PHASE0R_DECILE_STATUS",
    "run-measured-cost-revalidation": "PHASE0R_MEASURED_COST_REVALIDATION_STATUS",
    "create-adversarial-packet": "PHASE0R_ADVERSARIAL_PACKET_STATUS",
}


def unlocked_candidates(candidate_id: str) -> list[str]:
    return [candidate.candidate_id for candidate in selected_candidates(candidate_id) if candidate.status != "LOCKED"]


def write_blocked_result_stub(root: Path, command: str, candidate_id: str) -> Path:
    output_name = RESULT_COMMANDS.get(command, "PHASE0R_RESULT_STATUS")
    report_path = root / "outputs" / "reports" / f"{output_name}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    blocked = unlocked_candidates(candidate_id)
    status = "BLOCKED_HYPOTHESIS_NOT_LOCKED" if blocked else "PENDING_IMPLEMENTATION"
    lines = [
        f"# {output_name}",
        "",
        f"Command: {command}",
        f"Candidate: {candidate_id}",
        f"Status: {status}",
        "",
        "This placeholder does not contain backtest or validation results.",
        "Phase 0R result-producing runs require a LOCKED hypothesis registered before execution.",
        "",
    ]
    if blocked:
        lines.extend(["Blocked candidates:", "", *[f"- {name}" for name in blocked], ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
