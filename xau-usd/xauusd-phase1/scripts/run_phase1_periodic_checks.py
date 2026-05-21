from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from append_phase1_soak_history import append_phase1_soak_history
from check_phase1_external_health import check_external_health
from generate_phase1_acceptance_report import generate_phase1_acceptance_report
from generate_phase1_review_index import generate_phase1_review_index
from generate_phase1_runtime_health_report import generate_phase1_runtime_health_report
from generate_phase1_soak_history_report import generate_phase1_soak_history_report
from generate_phase1_status_summary import generate_phase1_status_summary
from generate_phase2_readiness_report import generate_phase2_readiness_report


@dataclass(frozen=True)
class PeriodicCheckOutput:
    status: str
    status_summary_path: Path
    external_health_path: Path
    soak_history_rows: int
    acceptance_status: str
    phase2_readiness_status: str
    review_index_status: str


def run_phase1_periodic_checks(
    root: Path,
    files_dir: Path,
    compile_log: Path,
    max_fresh_minutes: int = 15,
) -> PeriodicCheckOutput:
    root = root.resolve()
    report_dir = root / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    status_summary_path = generate_phase1_status_summary(
        files_dir=files_dir,
        output_path=report_dir / "PHASE1_STATUS_SUMMARY.json",
        compile_log=compile_log,
        source_root=root,
    )
    soak_history = append_phase1_soak_history(
        summary_path=status_summary_path,
        history_path=report_dir / "PHASE1_SOAK_HISTORY.csv",
    )
    soak_history_report = generate_phase1_soak_history_report(
        history_path=soak_history.history_path,
        report_path=report_dir / "PHASE1_SOAK_HISTORY_REPORT.md",
    )
    runtime_health = generate_phase1_runtime_health_report(
        files_dir=files_dir,
        report_path=report_dir / "PHASE1_RUNTIME_HEALTH_REPORT.md",
        max_fresh_minutes=max_fresh_minutes,
    )
    acceptance = generate_phase1_acceptance_report(
        files_dir=files_dir,
        report_path=report_dir / "PHASE1_ACCEPTANCE_REPORT.md",
        compile_log=compile_log,
        source_root=root,
        soak_history_report=soak_history_report.report_path,
        runtime_health_report=runtime_health.report_path,
        max_fresh_minutes=max_fresh_minutes,
    )
    phase2_readiness = generate_phase2_readiness_report(
        root=root,
        report_path=report_dir / "PHASE2_READINESS_REPORT.md",
    )
    review_index = generate_phase1_review_index(
        root=root,
        report_path=report_dir / "PHASE1_REVIEW_INDEX.md",
    )
    external_health_path = report_dir / "PHASE1_EXTERNAL_HEALTH.json"
    external_health = check_external_health(
        files_dir=files_dir,
        status_summary=status_summary_path,
        output_path=external_health_path,
        max_fresh_minutes=max_fresh_minutes,
    )
    status = "PASS" if external_health.status == "PASS" else "FAIL"
    return PeriodicCheckOutput(
        status=status,
        status_summary_path=status_summary_path,
        external_health_path=external_health_path,
        soak_history_rows=soak_history.row_count,
        acceptance_status=acceptance.status,
        phase2_readiness_status=phase2_readiness.status,
        review_index_status=review_index.status,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1 periodic soak and readiness checks.")
    parser.add_argument("--files-dir", type=Path, required=True)
    parser.add_argument(
        "--compile-log",
        type=Path,
        default=Path("C:/MT5PortableGoldMission/compile_Phase1DryRunShell.log"),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--max-fresh-minutes", type=int, default=15)
    args = parser.parse_args(argv)

    output = run_phase1_periodic_checks(
        root=args.root,
        files_dir=args.files_dir,
        compile_log=args.compile_log,
        max_fresh_minutes=args.max_fresh_minutes,
    )
    print(f"Periodic checks: {output.status}")
    print(f"Status summary: {output.status_summary_path}")
    print(f"External health: {output.external_health_path}")
    print(f"Soak history rows: {output.soak_history_rows}")
    print(f"Acceptance: {output.acceptance_status}")
    print(f"Phase 2 readiness: {output.phase2_readiness_status}")
    print(f"Review index: {output.review_index_status}")
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
