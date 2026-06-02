from __future__ import annotations

from pathlib import Path

from phase0r.candidate_registry import CANDIDATES
from phase0r.cost_feasibility import run_cost_feasibility


def write_candidate_status_report(root: Path) -> Path:
    cost_by_id = {result.candidate_id: result for result in run_cost_feasibility("all")}
    report_path = root / "outputs" / "reports" / "PHASE0R_CANDIDATE_STATUS.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 0R Candidate Status",
        "",
        "These candidates are separate research candidates. They are not canonical EAs and are not execution-authorized.",
        "",
        "| candidate_id | version | status | same_family_as_breakout_retest | hypothesis_locked | structural_cost_precheck | phase0r_matrix_status | measured_cost_revalidation_status | observer_status | promotion_status | block_reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in CANDIDATES:
        cost = cost_by_id[candidate.candidate_id]
        lines.append(
            "| "
            f"{candidate.candidate_id} | "
            f"{candidate.version} | "
            f"{candidate.status} | "
            f"{str(candidate.same_family_as_breakout_retest).lower()} | "
            f"{str(candidate.status == 'LOCKED').lower()} | "
            f"{cost.status} | "
            "NOT_RUN | "
            "NOT_RUN | "
            "OBSERVER_ONLY_DRAFT | "
            "BLOCKED | "
            "hypothesis_not_locked_and_phase0r_not_run |"
        )
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def write_verdict_report(root: Path) -> Path:
    report_path = root / "outputs" / "reports" / "PHASE0R_VERDICT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 0R Verdict",
        "",
        "Overall status: NOT_RUN",
        "",
        "No candidate has passed Phase 0R. Paper mode is not authorized.",
        "",
        "Promotion gates remain blocked until every required gate is run after hypothesis lock:",
        "",
        "- Hypothesis locked before run",
        "- Structural cost precheck PASS",
        "- 9-cell matrix PASS",
        "- Decile persistence PASS",
        "- Measured-cost revalidation PASS",
        "- Adversarial review PASS",
        "- Reality Check / SPA inclusion review",
        "- Observer parity PASS",
        "- Owner approval recorded",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
