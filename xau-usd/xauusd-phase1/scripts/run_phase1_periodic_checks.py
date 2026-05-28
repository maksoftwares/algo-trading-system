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

from append_phase1_soak_history import append_phase1_soak_history
from analyze_phase1_soak import analyze_phase1_soak
from check_phase1_external_health import check_external_health
from generate_phase1_acceptance_report import generate_phase1_acceptance_report
from generate_phase1_observer_parity_report import generate_phase1_observer_parity_report
from generate_phase1_review_index import generate_phase1_review_index
from generate_phase1_runtime_health_report import generate_phase1_runtime_health_report
from generate_phase1_soak_history_report import generate_phase1_soak_history_report
from generate_phase1_status_summary import generate_phase1_status_summary
from generate_phase1_would_signal_report import generate_phase1_would_signal_report
from generate_project_status_page import assert_status_page_current, generate_project_status_page
from generate_phase2_demo_countdown_report import generate_phase2_demo_countdown_report
from generate_phase2_demo_next_actions_report import generate_phase2_demo_next_actions_report
from generate_phase2_demo_preflight_report import generate_phase2_demo_preflight_report
from generate_phase2_mt5_network_baseline import generate_phase2_mt5_network_baseline
from generate_phase2_owner_action_packet import generate_phase2_owner_action_packet
from generate_phase2_paper_ledger_schema_report import generate_phase2_paper_ledger_schema_report
from generate_phase2_readiness_report import generate_phase2_readiness_report
from generate_phase2_vps_bootstrap_packet import generate_phase2_vps_bootstrap_packet
from generate_phase2_vps_first_day_verification import generate_phase2_vps_first_day_verification
from generate_phase2_vps_selection_decision_check import generate_phase2_vps_selection_decision_check
from phase0.config import ConfigError, load_project_config
from phase0.concentration_audit import generate_concentration_frequency_audit
from phase0.measured_revalidation import generate_measured_cost_revalidation
from phase0.spread_analysis import analyze_spread_logs
from verify_phase1_logs import verify_phase1_logs


@dataclass(frozen=True)
class PeriodicCheckOutput:
    status: str
    status_summary_path: Path
    external_health_path: Path
    soak_history_rows: int
    acceptance_status: str
    phase2_readiness_status: str
    phase2_demo_preflight_status: str
    phase2_owner_action_status: str
    phase2_vps_bootstrap_status: str
    vps_first_day_status: str
    review_index_status: str


def run_phase1_periodic_checks(
    root: Path,
    files_dir: Path,
    compile_log: Path,
    spread_files_dir: Path | None = None,
    max_fresh_minutes: int = 15,
) -> PeriodicCheckOutput:
    root = root.resolve()
    spread_files_dir = spread_files_dir or files_dir
    report_dir = root / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    phase0_root = root.parent / "xauusd-phase0"
    if phase0_root.exists():
        phase0_config = load_project_config(phase0_root)
        generate_concentration_frequency_audit(phase0_config)
        try:
            analyze_spread_logs(phase0_config, input_dir=spread_files_dir, allow_pending=True)
        except ConfigError as exc:
            warning_path = phase0_root / "outputs" / "reports" / "SPREAD_LOG_FRESHNESS_SCHEMA_WARNING.md"
            warning_path.parent.mkdir(parents=True, exist_ok=True)
            warning_path.write_text(
                "\n".join(
                    [
                        "# Spread Log Freshness Schema Warning",
                        "",
                        "Overall status: WARN",
                        "",
                        "The passive spread analyzer requires tick freshness columns. Existing legacy spread logs were left untouched so the Phase 1 periodic checks can continue using the last generated measured-cost evidence.",
                        "",
                        f"Reason: {exc}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
        generate_measured_cost_revalidation(phase0_config, expert="breakout_retest")

    log_verification = verify_phase1_logs(files_dir, report_dir / "PHASE1_DRY_RUN_LOG_REPORT.md")
    soak_analysis = analyze_phase1_soak(
        files_dir,
        report_dir / "PHASE1_SOAK_DRIFT_REPORT.md",
        max_fresh_minutes=max_fresh_minutes,
    )
    runtime_health = generate_phase1_runtime_health_report(
        files_dir=files_dir,
        report_path=report_dir / "PHASE1_RUNTIME_HEALTH_REPORT.md",
        max_fresh_minutes=max_fresh_minutes,
    )
    would_signal = generate_phase1_would_signal_report(
        files_dir,
        report_dir / "PHASE1_WOULD_SIGNAL_REPORT.md",
    )
    acceptance = generate_phase1_acceptance_report(
        files_dir=files_dir,
        report_path=report_dir / "PHASE1_ACCEPTANCE_REPORT.md",
        compile_log=compile_log,
        source_root=root,
        runtime_health_report=runtime_health.report_path,
        max_fresh_minutes=max_fresh_minutes,
    )
    status_summary_path = generate_phase1_status_summary(
        files_dir=files_dir,
        output_path=report_dir / "PHASE1_STATUS_SUMMARY.json",
        compile_log=compile_log,
        source_root=root,
        log_status=log_verification,
        soak_status=soak_analysis,
        runtime_health_status=runtime_health,
        would_signal_status=would_signal,
        acceptance_status=acceptance,
    )
    soak_history = append_phase1_soak_history(
        summary_path=status_summary_path,
        history_path=report_dir / "PHASE1_SOAK_HISTORY.csv",
    )
    soak_history_report = generate_phase1_soak_history_report(
        history_path=soak_history.history_path,
        report_path=report_dir / "PHASE1_SOAK_HISTORY_REPORT.md",
    )
    generate_phase2_paper_ledger_schema_report(
        root=root,
        report_path=report_dir / "PHASE2_PAPER_LEDGER_SCHEMA_REPORT.md",
        columns_csv_path=report_dir / "PHASE2_PAPER_LEDGER_COLUMNS.csv",
    )
    generate_phase1_observer_parity_report(
        phase1_root=root,
        report_path=report_dir / "PHASE1_OBSERVER_PARITY_REPORT.md",
    )
    vps_first_day = generate_phase2_vps_first_day_verification(
        root=root,
        files_dir=files_dir,
        compile_log=compile_log,
    )
    generate_phase2_mt5_network_baseline(
        logs_dir=files_dir.parent.parent / "logs",
        report_path=report_dir / "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md",
    )
    generate_phase2_vps_selection_decision_check(root=root)
    acceptance = generate_phase1_acceptance_report(
        files_dir=files_dir,
        report_path=report_dir / "PHASE1_ACCEPTANCE_REPORT.md",
        compile_log=compile_log,
        source_root=root,
        soak_history_report=soak_history_report.report_path,
        runtime_health_report=runtime_health.report_path,
        max_fresh_minutes=max_fresh_minutes,
    )
    status_summary_path = generate_phase1_status_summary(
        files_dir=files_dir,
        output_path=report_dir / "PHASE1_STATUS_SUMMARY.json",
        compile_log=compile_log,
        source_root=root,
        log_status=log_verification,
        soak_status=soak_analysis,
        runtime_health_status=runtime_health,
        would_signal_status=would_signal,
        acceptance_status=acceptance,
    )
    generate_phase1_review_index(
        root=root,
        report_path=report_dir / "PHASE1_REVIEW_INDEX.md",
        include_phase2_readiness=False,
    )
    phase2_readiness = generate_phase2_readiness_report(
        root=root,
        report_path=report_dir / "PHASE2_READINESS_REPORT.md",
    )
    generate_phase2_demo_countdown_report(root=root)
    phase2_preflight = generate_phase2_demo_preflight_report(root=root)
    owner_action_packet = generate_phase2_owner_action_packet(root=root)
    vps_bootstrap_packet = generate_phase2_vps_bootstrap_packet(root=root)
    generate_phase2_demo_next_actions_report(root=root)
    review_index = generate_phase1_review_index(
        root=root,
        report_path=report_dir / "PHASE1_REVIEW_INDEX.md",
    )
    repo_root = root.parents[1]
    generate_project_status_page(repo_root, repo_root / "status.html")
    assert_status_page_current(repo_root, repo_root / "status.html", status_summary_path)
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
        phase2_demo_preflight_status=phase2_preflight.status,
        phase2_owner_action_status=owner_action_packet.status,
        phase2_vps_bootstrap_status=vps_bootstrap_packet.status,
        vps_first_day_status=vps_first_day.status,
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
        "--spread-files-dir",
        type=Path,
        help="Optional passive spread logger Files directory. Defaults to --files-dir.",
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
        spread_files_dir=args.spread_files_dir,
        max_fresh_minutes=args.max_fresh_minutes,
    )
    print(f"Periodic checks: {output.status}")
    print(f"Status summary: {output.status_summary_path}")
    print(f"External health: {output.external_health_path}")
    print(f"Spread files dir: {args.spread_files_dir or args.files_dir}")
    print(f"Soak history rows: {output.soak_history_rows}")
    print(f"Acceptance: {output.acceptance_status}")
    print(f"Phase 2 readiness: {output.phase2_readiness_status}")
    print(f"Phase 2 demo preflight: {output.phase2_demo_preflight_status}")
    print(f"Phase 2 owner action packet: {output.phase2_owner_action_status}")
    print(f"Phase 2 VPS bootstrap packet: {output.phase2_vps_bootstrap_status}")
    print(f"VPS first-day verification: {output.vps_first_day_status}")
    print(f"Review index: {output.review_index_status}")
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
