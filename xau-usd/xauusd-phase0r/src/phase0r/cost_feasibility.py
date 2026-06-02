from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from phase0r.candidate_registry import Candidate, selected_candidates


@dataclass(frozen=True)
class SpreadAssumptions:
    measured_median_spread_points: float = 50.0
    measured_p95_spread_points: float = 75.0
    measured_max_spread_points: float = 180.0


@dataclass(frozen=True)
class CostFeasibilityResult:
    candidate_id: str
    expected_median_stop_points: float
    projected_cost_r_median: float
    projected_cost_r_p95: float
    projected_cost_r_max: float
    structural_cost_ratio_p95: float
    status: str
    block_reason: str

    @property
    def cost_feasible(self) -> bool:
        return self.status.startswith("PASS")


DEFAULT_SPREAD_ASSUMPTIONS = SpreadAssumptions()


def projected_cost_r(spread_points: float, stop_points: float) -> float:
    if stop_points <= 0:
        raise ValueError("stop_points must be positive")
    return spread_points / stop_points


def evaluate_candidate_cost(
    candidate: Candidate,
    assumptions: SpreadAssumptions = DEFAULT_SPREAD_ASSUMPTIONS,
) -> CostFeasibilityResult:
    stop_points = float(candidate.expected_median_stop_points)
    median = projected_cost_r(assumptions.measured_median_spread_points, stop_points)
    p95 = projected_cost_r(assumptions.measured_p95_spread_points, stop_points)
    max_cost = projected_cost_r(assumptions.measured_max_spread_points, stop_points)

    if p95 > 0.30:
        status = "STRUCTURAL_COST_RISK"
        block_reason = "Measured P95 spread exceeds 0.30R of expected median stop distance."
    elif p95 <= 0.20 and median <= 0.30:
        status = "PASS_PREFERRED"
        block_reason = "none"
    elif median <= 0.30 and p95 <= 0.50:
        status = "PASS_ACCEPTABLE"
        block_reason = "P95 cost_R is above the preferred 0.20R target but within the hard gate."
    else:
        status = "STRUCTURAL_COST_RISK"
        block_reason = "Projected measured cost_R breaches the hard structural cost gate."

    return CostFeasibilityResult(
        candidate_id=candidate.candidate_id,
        expected_median_stop_points=stop_points,
        projected_cost_r_median=median,
        projected_cost_r_p95=p95,
        projected_cost_r_max=max_cost,
        structural_cost_ratio_p95=p95,
        status=status,
        block_reason=block_reason,
    )


def run_cost_feasibility(
    candidate_id: str = "all",
    assumptions: SpreadAssumptions = DEFAULT_SPREAD_ASSUMPTIONS,
) -> list[CostFeasibilityResult]:
    return [evaluate_candidate_cost(candidate, assumptions) for candidate in selected_candidates(candidate_id)]


def write_cost_feasibility_report(
    root: Path,
    candidate_id: str = "all",
    assumptions: SpreadAssumptions = DEFAULT_SPREAD_ASSUMPTIONS,
) -> Path:
    results = run_cost_feasibility(candidate_id, assumptions)
    report_path = root / "outputs" / "reports" / "PHASE0R_COST_FEASIBILITY_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if all(result.cost_feasible for result in results) else "BLOCKED"
    lines = [
        "# Phase 0R Cost Feasibility Report",
        "",
        f"Overall status: {status}",
        "",
        "Measured spread assumptions:",
        "",
        f"- measured_median_spread_points: {assumptions.measured_median_spread_points:g}",
        f"- measured_p95_spread_points: {assumptions.measured_p95_spread_points:g}",
        f"- measured_max_spread_points: {assumptions.measured_max_spread_points:g}",
        "",
        "Hard rule: measured P95 spread divided by expected median stop points must be <= 0.30R.",
        "",
        "| candidate_id | expected_median_stop_points | median_cost_R | p95_cost_R | max_cost_R | status | block_reason |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            f"{result.candidate_id} | "
            f"{result.expected_median_stop_points:.0f} | "
            f"{result.projected_cost_r_median:.3f} | "
            f"{result.projected_cost_r_p95:.3f} | "
            f"{result.projected_cost_r_max:.3f} | "
            f"{result.status} | "
            f"{result.block_reason} |"
        )
    lines.extend(
        [
            "",
            "No candidate has passed Phase 0R. This report is a structural precheck only.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
