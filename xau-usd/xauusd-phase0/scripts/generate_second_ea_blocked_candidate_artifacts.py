from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path


PHASE0_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PHASE0_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase0.constants import SECOND_EA_CAMPAIGN_CANDIDATES, SECOND_EA_LANE_A_CANDIDATES


REPORTS_DIR = PHASE0_ROOT / "outputs" / "reports"
MATRIX_DIR = PHASE0_ROOT / "outputs" / "matrix"


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MATRIX_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for candidate in SECOND_EA_CAMPAIGN_CANDIDATES:
        lane = "A" if candidate in SECOND_EA_LANE_A_CANDIDATES else "B"
        verdict = "BLOCKED_DATA_READINESS" if lane == "A" else "BLOCKED_LANE_A_NOT_COMPLETE"
        write_first_pass(candidate, lane, verdict, now)
        write_matrix_placeholder(candidate, lane, verdict)
        write_era_placeholder(candidate, lane, verdict)
        write_cost_placeholder(candidate, lane, verdict)
        write_stop_placeholder(candidate, lane, verdict)
    write_lane_specific_blocked_reports(now)
    print(f"SECOND_EA_BLOCKED_CANDIDATE_ARTIFACTS_WRITTEN count={len(SECOND_EA_CAMPAIGN_CANDIDATES)}")
    return 0


def write_first_pass(candidate: str, lane: str, verdict: str, generated_at: str) -> None:
    blocker = (
        "`SECOND_EA_DATA_EXTENSION_READINESS.md` is PARTIAL and `SECOND_EA_PARTIAL_DATA_OWNER_DECISION_STATUS.md` is NOT_SIGNED"
        if lane == "A"
        else "Lane B cannot start before Lane A completion or owner override."
    )
    path = REPORTS_DIR / f"FIRST_PASS_{candidate}.md"
    path.write_text(
        "\n".join(
            [
                f"# First Pass: {candidate}",
                "",
                f"Generated at UTC: {generated_at}",
                "",
                "## 1. Candidate metadata",
                "",
                f"- candidate_id: `{candidate}`",
                f"- lane: `{lane}`",
                "- status: NOT_RUN",
                "",
                "## 2. Hypothesis hash and lock status",
                "",
                "Hypothesis status: NOT_LOCKED_BECAUSE_PRE_RUN_MILESTONES_BLOCKED",
                "",
                "## 3. Data windows used",
                "",
                "No data windows were used. Candidate matrix execution is blocked.",
                "",
                "## 4. True-holdout exclusion proof",
                "",
                "No result-producing run occurred. Data-readiness inspection ended no later than 2025-06-30 for current offline files.",
                "",
                "## 5. Matrix gate table",
                "",
                "NOT_RUN",
                "",
                "## 6. Broker x cost model table",
                "",
                "NOT_RUN",
                "",
                "## 7. Era-slice table",
                "",
                "NOT_RUN",
                "",
                "## 8. Fixed-notional R-series summary",
                "",
                "NOT_RUN",
                "",
                "## 9. Win rate, PF, avg R, median R",
                "",
                "NOT_RUN",
                "",
                "## 10. Stop-distance distribution",
                "",
                "NOT_RUN",
                "",
                "## 11. Median and P95 cost_R",
                "",
                "NOT_RUN",
                "",
                "## 12. G1-G12 pass/fail table",
                "",
                "NOT_RUN",
                "",
                "## 13. Failure reason if rejected",
                "",
                f"Not rejected from market evidence. Current blocker: {blocker}",
                "",
                "## 14. No-tuning notice",
                "",
                "No post-result tuning occurred because no result-producing run occurred.",
                "",
                "## 15. Final verdict",
                "",
                f"Final verdict: {verdict}",
                "",
                "No observer/demo/live deployment is authorized.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_matrix_placeholder(candidate: str, lane: str, verdict: str) -> None:
    _write_csv(
        MATRIX_DIR / f"matrix_{candidate}.csv",
        ["candidate_id", "lane", "cell_id", "broker", "cost_model", "status", "verdict"],
        [[candidate, lane, "", "", "", "NOT_RUN", verdict]],
    )


def write_era_placeholder(candidate: str, lane: str, verdict: str) -> None:
    _write_csv(
        REPORTS_DIR / f"era_slices_{candidate}.csv",
        ["candidate_id", "lane", "broker", "era_slice", "status", "verdict"],
        [[candidate, lane, "", "", "NOT_RUN", verdict]],
    )


def write_cost_placeholder(candidate: str, lane: str, verdict: str) -> None:
    _write_csv(
        REPORTS_DIR / f"cost_r_{candidate}.csv",
        ["candidate_id", "lane", "broker", "cost_model", "realized_median_cost_r", "realized_p95_cost_r", "status", "verdict"],
        [[candidate, lane, "", "", "", "", "NOT_RUN", verdict]],
    )


def write_stop_placeholder(candidate: str, lane: str, verdict: str) -> None:
    _write_csv(
        REPORTS_DIR / f"stop_distribution_{candidate}.csv",
        ["candidate_id", "lane", "broker", "p10_stop_points", "median_stop_points", "p90_stop_points", "status", "verdict"],
        [[candidate, lane, "", "", "", "", "NOT_RUN", verdict]],
    )


def write_lane_specific_blocked_reports(generated_at: str) -> None:
    reports = {
        "A1_FULLHIST_FAILURE_MODE_REVIEW.md": [
            "# A1 Full-History Failure Mode Review",
            "",
            "Candidate: `d1_momentum_h4_pullback_v1_fullhist`",
            "Status: BLOCKED_DATA_READINESS",
            "",
            "This review is a required Lane A follow-up report, but no matrix or first-pass evidence exists yet.",
            "",
            "Required future contents after an authorized run:",
            "",
            "- full-history cell results",
            "- low-frequency gate failures or pass evidence",
            "- concentration analysis under normalized G4",
            "- broker and era failure modes",
            "- no-tuning final verdict",
        ],
        "A2_DIRECTIONAL_BIAS_REPORT.md": [
            "# A2 Directional Bias Report",
            "",
            "Candidate: `w1_d1_momentum_continuation_v1_fullhist`",
            "Status: BLOCKED_DATA_READINESS",
            "",
            "This report is required to test whether A2 performance is only long-gold exposure, but no authorized run exists yet.",
            "",
            "Required future contents after an authorized run:",
            "",
            "- long contribution",
            "- short contribution",
            "- directional exposure balance",
            "- bullish-year dependence",
            "- no-tuning final verdict",
        ],
        "A3_CROSS_VENUE_WEAKNESS_REPORT.md": [
            "# A3 Cross-Venue Weakness Report",
            "",
            "Candidate: `h4_inside_bar_d1_momentum_breakout_v1_fullhist`",
            "Status: BLOCKED_DATA_READINESS",
            "",
            "This report is required to document Pepperstone/Dukascopy weakness without rescue attempts, but no authorized run exists yet.",
            "",
            "Required future contents after an authorized run:",
            "",
            "- Capital.com cell results",
            "- Pepperstone cell results",
            "- Dukascopy cell results",
            "- explicit no-rescue verdict if cross-venue weakness appears",
            "- no-tuning final verdict",
        ],
        "B1_ANCESTRY_COMPARISON_REPORT.md": [
            "# B1 Ancestry Comparison Report",
            "",
            "Candidate: `xau_london_open_expansion_flow_v0`",
            "Status: BLOCKED_LANE_A_NOT_COMPLETE",
            "",
            "This report is required before B1 can qualify as mechanism-first independent, but Lane B has not started.",
            "",
            "Required future contents before any B1 lock/run:",
            "",
            "- comparison against rejected `asia_range_london_breakout_v0`",
            "- comparison against rejected `asia_range_london_failed_break_reversal_v0`",
            "- entry-condition overlap estimate",
            "- SAME_MECHANIC_RETEST label if overlap exceeds 50%",
            "- distinct event clock, decision timeframe, stop model, and flow thesis evidence",
        ],
    }
    for filename, body in reports.items():
        (REPORTS_DIR / filename).write_text(
            "\n".join(
                [
                    *body,
                    "",
                    f"Generated at UTC: {generated_at}",
                    "",
                    "No observer/demo/live deployment is authorized.",
                    "",
                ]
            ),
            encoding="utf-8",
        )


def _write_csv(path: Path, fieldnames: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
