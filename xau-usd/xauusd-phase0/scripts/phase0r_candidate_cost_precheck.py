from __future__ import annotations

import argparse
from dataclasses import dataclass


MEASURED_MEDIAN_SPREAD_POINTS = 50.0
MEASURED_P95_SPREAD_POINTS = 75.0
MIN_STOP_POINTS = 250.0
PREFERRED_STOP_POINTS = 375.0
MAX_P95_COST_R = 0.30


@dataclass(frozen=True)
class CandidateCostPrecheck:
    candidate: str
    median_stop_points: float
    median_cost_r: float
    p95_cost_r: float
    status: str
    reason: str


def run_precheck(candidate: str, median_stop_points: float) -> CandidateCostPrecheck:
    if median_stop_points <= 0:
        raise ValueError("median_stop_points must be positive.")
    median_cost_r = MEASURED_MEDIAN_SPREAD_POINTS / median_stop_points
    p95_cost_r = MEASURED_P95_SPREAD_POINTS / median_stop_points
    if median_stop_points < MIN_STOP_POINTS:
        return CandidateCostPrecheck(
            candidate,
            median_stop_points,
            median_cost_r,
            p95_cost_r,
            "REJECT_COST_FRAGILE",
            "Expected median stop distance is below 250 points.",
        )
    if p95_cost_r > MAX_P95_COST_R:
        return CandidateCostPrecheck(
            candidate,
            median_stop_points,
            median_cost_r,
            p95_cost_r,
            "REJECT_P95_COST_TOO_HIGH",
            "Measured P95 cost_R exceeds 0.30R.",
        )
    if median_stop_points < PREFERRED_STOP_POINTS:
        return CandidateCostPrecheck(
            candidate,
            median_stop_points,
            median_cost_r,
            p95_cost_r,
            "PASS_WITH_COST_CAUTION",
            "Candidate clears hard cost precheck but is below preferred 375-500+ point stop budget.",
        )
    return CandidateCostPrecheck(
        candidate,
        median_stop_points,
        median_cost_r,
        p95_cost_r,
        "PASS",
        "Candidate clears measured-cost structural precheck.",
    )


def _render(output: CandidateCostPrecheck) -> str:
    return "\n".join(
        [
            f"Candidate: {output.candidate}",
            f"Status: {output.status}",
            f"Median stop points: {output.median_stop_points:.2f}",
            f"Measured median cost_R: {output.median_cost_r:.4f}",
            f"Measured P95 cost_R: {output.p95_cost_r:.4f}",
            f"Reason: {output.reason}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Precheck a Phase 0R candidate against measured spread cost.")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--median-stop-points", type=float, required=True)
    args = parser.parse_args(argv)
    output = run_precheck(args.candidate, args.median_stop_points)
    print(_render(output))
    return 0 if output.status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
