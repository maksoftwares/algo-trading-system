from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

PHASE0_SRC = Path(__file__).resolve().parents[2] / "xauusd-phase0" / "src"
if PHASE0_SRC.exists() and str(PHASE0_SRC) not in sys.path:
    sys.path.insert(0, str(PHASE0_SRC))

from generate_phase2_readiness_report import generate_phase2_readiness_report
from generate_project_status_page import generate_project_status_page
from verify_status_report_freshness import verify_status_report_freshness
from phase0.config import ConfigError, load_project_config
from phase0.measured_revalidation import generate_measured_cost_revalidation
from phase0.spread_analysis import analyze_spread_logs


DEFAULT_SPREAD_FILES_DIR = Path("C:/MT5PortableSpreadLogger/MQL5/Files")


@dataclass(frozen=True)
class MeasuredCostPassSequenceOutput:
    status: str
    measured_cost_status: str
    measured_cost_report: Path
    measured_cost_csv: Path
    revalidation_report: Path | None
    phase2_readiness_report: Path | None
    status_html: Path | None


def run_measured_cost_pass_sequence(
    phase1_root: Path,
    spread_files_dir: Path = DEFAULT_SPREAD_FILES_DIR,
    expert: str = "breakout_retest",
    status_path: Path | None = None,
    file_glob: str = "spread_log_*.csv",
) -> MeasuredCostPassSequenceOutput:
    phase1_root = phase1_root.resolve()
    repo_root = phase1_root.parents[1]
    phase0_root = phase1_root.parent / "xauusd-phase0"
    status_path = (status_path or repo_root / "status.html").resolve()
    config = load_project_config(phase0_root)

    measured = analyze_spread_logs(
        config,
        input_dir=spread_files_dir,
        file_glob=file_glob,
        allow_pending=True,
    )
    if measured.status != "PASS":
        return MeasuredCostPassSequenceOutput(
            status="REFUSED_MEASURED_COST_PENDING",
            measured_cost_status=measured.status,
            measured_cost_report=measured.measured_report_path,
            measured_cost_csv=measured.measured_cost_model_path,
            revalidation_report=None,
            phase2_readiness_report=None,
            status_html=None,
        )

    revalidation = generate_measured_cost_revalidation(config, expert=expert)
    phase2_readiness = generate_phase2_readiness_report(
        root=phase1_root,
        report_path=phase1_root / "outputs" / "reports" / "PHASE2_READINESS_REPORT.md",
    )
    status_output = generate_project_status_page(repo_root, status_path)
    freshness_errors = verify_status_report_freshness(repo_root, status_output.output_path)
    if freshness_errors:
        raise ConfigError("Status/report freshness failed after measured-cost pass sequence: " + "; ".join(freshness_errors))

    return MeasuredCostPassSequenceOutput(
        status="PASS_SEQUENCE_COMPLETE",
        measured_cost_status=measured.status,
        measured_cost_report=measured.measured_report_path,
        measured_cost_csv=measured.measured_cost_model_path,
        revalidation_report=revalidation.report_path,
        phase2_readiness_report=phase2_readiness.report_path,
        status_html=status_output.output_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the measured-cost pass sequence after MEASURED_COST_MODEL.md is eligible. "
            "The command refuses to run revalidation while the measured-cost model is PENDING."
        )
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Phase 1 root.")
    parser.add_argument(
        "--spread-files-dir",
        type=Path,
        default=DEFAULT_SPREAD_FILES_DIR,
        help="Passive spread logger MQL5/Files directory.",
    )
    parser.add_argument("--expert", default="breakout_retest")
    parser.add_argument("--glob", default="spread_log_*.csv", help="Spread logger CSV glob.")
    parser.add_argument("--status-path", type=Path, default=None, help="status.html path.")
    args = parser.parse_args(argv)

    output = run_measured_cost_pass_sequence(
        phase1_root=args.root,
        spread_files_dir=args.spread_files_dir,
        expert=args.expert,
        status_path=args.status_path,
        file_glob=args.glob,
    )
    print(f"Measured-cost pass sequence: {output.status}")
    print(f"Measured-cost status: {output.measured_cost_status}")
    print(f"Measured-cost report: {output.measured_cost_report}")
    print(f"Measured-cost CSV: {output.measured_cost_csv}")
    if output.status == "REFUSED_MEASURED_COST_PENDING":
        print("Revalidation was not run because MEASURED_COST_MODEL.md is not PASS.")
        return 2
    print(f"Revalidation report: {output.revalidation_report}")
    print(f"Phase 2 readiness report: {output.phase2_readiness_report}")
    print(f"Status page: {output.status_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
