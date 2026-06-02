from __future__ import annotations

import argparse
from pathlib import Path

from phase0r.cost_feasibility import write_cost_feasibility_report
from phase0r.hypothesis_lock import (
    locked_hypotheses_match_manifest,
    register_hypotheses,
    validate_hypotheses_complete,
)
from phase0r.phase0r_estimates import run_phase0r_estimates
from phase0r.phase0r_matrix import unlocked_candidates, write_blocked_result_stub
from phase0r.phase0r_reports import write_candidate_status_report, write_verdict_report


DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phase0r", description="Separate XAUUSD Phase 0R research CLI")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-hypotheses-complete")
    validate.set_defaults(func=_cmd_validate_hypotheses_complete)

    hash_cmd = subparsers.add_parser("hash-hypotheses")
    hash_cmd.add_argument("--register", action="store_true")
    hash_cmd.set_defaults(func=_cmd_hash_hypotheses)

    cost = subparsers.add_parser("run-cost-feasibility")
    cost.add_argument("--candidate", default="all")
    cost.set_defaults(func=_cmd_run_cost_feasibility)

    estimates = subparsers.add_parser(
        "run-estimates",
        help="Run draft estimate-only backtests over existing processed bars.",
    )
    estimates.add_argument("--candidate", default="all")
    estimates.add_argument("--phase0-root", type=Path, default=None)
    estimates.add_argument("--measured-cost", choices=("median", "p95"), default="p95")
    estimates.set_defaults(func=_cmd_run_estimates)

    for command in (
        "run-matrix",
        "run-deciles",
        "run-measured-cost-revalidation",
        "create-adversarial-packet",
    ):
        sub = subparsers.add_parser(command)
        sub.add_argument("--candidate", default="all")
        sub.set_defaults(func=_cmd_result_command)

    verdict = subparsers.add_parser("generate-verdict")
    verdict.add_argument("--candidate", default="all")
    verdict.set_defaults(func=_cmd_generate_verdict)

    status = subparsers.add_parser("generate-candidate-status")
    status.set_defaults(func=_cmd_generate_candidate_status)

    return parser


def _cmd_validate_hypotheses_complete(args: argparse.Namespace) -> int:
    validations = validate_hypotheses_complete(args.root)
    failures = [item for item in validations if item.status != "PASS"]
    for item in validations:
        print(f"{item.status}: {item.path.name}")
        if item.missing_fields:
            print(f"  missing: {', '.join(item.missing_fields)}")
        if item.placeholder_fields:
            print(f"  placeholders: {', '.join(item.placeholder_fields)}")
    return 0 if not failures else 1


def _cmd_hash_hypotheses(args: argparse.Namespace) -> int:
    if args.register:
        path = register_hypotheses(args.root)
        print(path)
        return 0
    errors = locked_hypotheses_match_manifest(args.root)
    for error in errors:
        print(error)
    return 0 if not errors else 1


def _cmd_run_cost_feasibility(args: argparse.Namespace) -> int:
    path = write_cost_feasibility_report(args.root, args.candidate)
    print(path)
    return 0


def _cmd_run_estimates(args: argparse.Namespace) -> int:
    phase0_root = args.phase0_root or args.root.parent / "xauusd-phase0"
    output = run_phase0r_estimates(args.root, phase0_root, args.candidate, args.measured_cost)
    print(output.report_path)
    print(output.summary_path)
    for path in output.trade_paths:
        print(path)
    print("Status: ESTIMATE_ONLY_NOT_PHASE0R_GATE")
    return 0


def _cmd_result_command(args: argparse.Namespace) -> int:
    command = args.command
    path = write_blocked_result_stub(args.root, command, args.candidate)
    print(path)
    blocked = unlocked_candidates(args.candidate)
    return 1 if blocked else 0


def _cmd_generate_verdict(args: argparse.Namespace) -> int:
    path = write_verdict_report(args.root)
    print(path)
    return 0


def _cmd_generate_candidate_status(args: argparse.Namespace) -> int:
    path = write_candidate_status_report(args.root)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
