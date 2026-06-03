from __future__ import annotations

import argparse
import sys
from pathlib import Path


PHASE0R_ROOT = Path(__file__).resolve().parents[1]
SRC = PHASE0R_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase0r.refinement import (  # noqa: E402
    generate_all_refinement_reports,
    load_refinement_data,
    write_demo_ea_deduped_review,
    write_demo_ea_performance_review,
    write_ea_cost_r_bucket_report,
    write_ea_loss_quality_report,
    write_ea_stop_distance_bucket_report,
    write_ea_win_rate_expectancy_report,
    write_vnext_candidate_proposals,
)


REPORT_WRITERS = {
    "performance": write_demo_ea_performance_review,
    "deduped": write_demo_ea_deduped_review,
    "expectancy": write_ea_win_rate_expectancy_report,
    "loss_quality": write_ea_loss_quality_report,
    "cost_bucket": write_ea_cost_r_bucket_report,
    "stop_bucket": write_ea_stop_distance_bucket_report,
    "vnext": write_vnext_candidate_proposals,
}


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--root", type=Path, default=PHASE0R_ROOT)
    parser.add_argument("--phase1-root", type=Path, default=None)
    parser.add_argument("--actual-log", type=Path, default=None)
    parser.add_argument("--signal-log", type=Path, default=None)
    parser.add_argument("--passive-log", type=Path, default=None)
    parser.add_argument("--report-dir", type=Path, default=None)
    parser.add_argument("--synthetic-sample", action="store_true")
    return parser


def load_data(args: argparse.Namespace):
    return load_refinement_data(
        args.root,
        args.phase1_root,
        actual_log_path=args.actual_log,
        signal_log_path=args.signal_log,
        passive_log_path=args.passive_log,
        synthetic_sample=args.synthetic_sample,
    )


def run_report(report_key: str, description: str) -> int:
    parser = build_parser(description)
    args = parser.parse_args()
    data = load_data(args)
    path = REPORT_WRITERS[report_key](data, args.report_dir)
    print(path)
    return 0


def run_all(description: str) -> int:
    parser = build_parser(description)
    args = parser.parse_args()
    data = load_data(args)
    output = generate_all_refinement_reports(data, args.report_dir)
    for path in output.report_paths:
        print(path)
    print(output.manifest_path)
    return 0
