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
from assert_cost_suspension import assert_cost_suspension
from audit_broker_action_file_boundary import audit_broker_action_file_boundary
from audit_experimental_executor_governance import audit_experimental_executor_governance
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
from generate_phase2_demo_account_isolation_report import generate_phase2_demo_account_isolation_report
from generate_phase2_demo_next_actions_report import generate_phase2_demo_next_actions_report
from generate_phase2_demo_preflight_report import generate_phase2_demo_preflight_report
from generate_phase2_blocker_summary import generate_phase2_blocker_summary
from generate_phase2_actual_demo_cost_reconciliation import generate_phase2_actual_demo_cost_reconciliation
from generate_phase2_mt5_network_baseline import generate_phase2_mt5_network_baseline
from generate_phase2_owner_action_packet import generate_phase2_owner_action_packet
from generate_phase2_paper_ledger_schema_report import generate_phase2_paper_ledger_schema_report
from generate_phase2b_passive_observer_reports import generate_phase2b_passive_observer_reports
from generate_phase2_readiness_report import generate_phase2_readiness_report
from generate_phase2_vps_bootstrap_packet import generate_phase2_vps_bootstrap_packet
from generate_phase2_vps_first_day_verification import generate_phase2_vps_first_day_verification
from generate_phase2_vps_latency_report import generate_phase2_vps_latency_report
from generate_phase2_vps_selection_decision_check import generate_phase2_vps_selection_decision_check
from import_phase2b_passive_observer_logs import DEFAULT_FILES_DIR as DEFAULT_PHASE2B_PASSIVE_FILES_DIR
from import_phase2b_passive_observer_logs import import_phase2b_passive_observer_logs
from phase0.config import ConfigError, load_project_config
from phase0.concentration_audit import generate_concentration_frequency_audit
from phase0.measured_revalidation import generate_measured_cost_revalidation
from phase0.measured_sanity import generate_measured_cost_revalidation_sanity_check
from phase0.spread_analysis import analyze_spread_logs
from verify_readiness_consistency import verify_readiness_consistency
from verify_canonical_phase2_block import verify_canonical_phase2_block
from verify_experimental_quarantine import verify_experimental_quarantine
from verify_no_cost_suspended_family_promotion import verify_no_cost_suspended_family_promotion
from verify_phase3_proxy_non_authoritative import verify_phase3_proxy_non_authoritative
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
    phase2_demo_account_isolation_status: str
    phase2_actual_demo_cost_reconciliation_status: str
    experimental_executor_governance_status: str
    cost_suspension_enforcement_status: str
    broker_action_boundary_status: str
    phase2_readiness_consistency_status: str
    phase2_owner_action_status: str
    phase2_vps_bootstrap_status: str
    vps_first_day_status: str
    review_index_status: str
    phase2_blocker_summary_status: str = "UNKNOWN"
    canonical_phase2_block_status: str = "UNKNOWN"
    experimental_quarantine_status: str = "UNKNOWN"
    phase2b_passive_observer_status: str = "UNKNOWN"
    cost_suspended_promotion_blocker_status: str = "UNKNOWN"
    phase3_proxy_non_authoritative_status: str = "UNKNOWN"
    phase2b_passive_import_status: str = "UNKNOWN"


def run_phase1_periodic_checks(
    root: Path,
    files_dir: Path,
    compile_log: Path,
    spread_files_dir: Path | None = None,
    phase2b_passive_files_dir: Path | None = None,
    max_fresh_minutes: int = 15,
) -> PeriodicCheckOutput:
    root = root.resolve()
    spread_files_dir = spread_files_dir or files_dir
    phase2b_passive_files_dir = phase2b_passive_files_dir or DEFAULT_PHASE2B_PASSIVE_FILES_DIR
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
        generate_measured_cost_revalidation_sanity_check(phase0_config, expert="breakout_retest")

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
    _refresh_local_runtime_latency_if_selected(root)
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
    demo_account_isolation = generate_phase2_demo_account_isolation_report(root=root)
    experimental_governance = audit_experimental_executor_governance(root)
    cost_suspension = assert_cost_suspension(root)
    broker_action_boundary = audit_broker_action_file_boundary(root.parents[1])
    actual_demo_cost_reconciliation = generate_phase2_actual_demo_cost_reconciliation(root)
    phase2_blocker_summary = generate_phase2_blocker_summary(root)
    canonical_block_status = "PASS" if verify_canonical_phase2_block(root) == 0 else "FAIL"
    experimental_quarantine_status = "PASS" if verify_experimental_quarantine(root) == 0 else "FAIL"
    phase2b_passive_import = import_phase2b_passive_observer_logs(root, files_dir=phase2b_passive_files_dir)
    phase2b_passive_observer = generate_phase2b_passive_observer_reports(root)
    cost_suspended_promotion_status = (
        "PASS" if verify_no_cost_suspended_family_promotion(root) == 0 else "FAIL"
    )
    phase3_proxy_non_authoritative_status = (
        "PASS" if verify_phase3_proxy_non_authoritative(root) == 0 else "FAIL"
    )
    phase2_preflight = generate_phase2_demo_preflight_report(root=root)
    owner_action_packet = generate_phase2_owner_action_packet(root=root)
    vps_bootstrap_packet = generate_phase2_vps_bootstrap_packet(root=root)
    generate_phase2_demo_next_actions_report(root=root)
    readiness_consistency = verify_readiness_consistency(root=root)
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
    status = (
        "PASS"
        if external_health.status == "PASS"
        and experimental_governance.status == "PASS"
        and cost_suspension.status == "PASS"
        and broker_action_boundary.status == "PASS"
        and phase2_blocker_summary.status == "BLOCKED_BY_MEASURED_COST"
        and canonical_block_status == "PASS"
        and experimental_quarantine_status == "PASS"
        and cost_suspended_promotion_status == "PASS"
        and phase3_proxy_non_authoritative_status == "PASS"
        else "FAIL"
    )
    return PeriodicCheckOutput(
        status=status,
        status_summary_path=status_summary_path,
        external_health_path=external_health_path,
        soak_history_rows=soak_history.row_count,
        acceptance_status=acceptance.status,
        phase2_readiness_status=phase2_readiness.status,
        phase2_demo_preflight_status=phase2_preflight.status,
        phase2_demo_account_isolation_status=demo_account_isolation.status,
        phase2_actual_demo_cost_reconciliation_status=actual_demo_cost_reconciliation.status,
        experimental_executor_governance_status=experimental_governance.status,
        cost_suspension_enforcement_status=cost_suspension.status,
        broker_action_boundary_status=broker_action_boundary.status,
        phase2_blocker_summary_status=phase2_blocker_summary.status,
        canonical_phase2_block_status=canonical_block_status,
        experimental_quarantine_status=experimental_quarantine_status,
        phase2b_passive_observer_status=phase2b_passive_observer.status,
        phase2b_passive_import_status=phase2b_passive_import.status,
        cost_suspended_promotion_blocker_status=cost_suspended_promotion_status,
        phase3_proxy_non_authoritative_status=phase3_proxy_non_authoritative_status,
        phase2_readiness_consistency_status=readiness_consistency.status,
        phase2_owner_action_status=owner_action_packet.status,
        phase2_vps_bootstrap_status=vps_bootstrap_packet.status,
        vps_first_day_status=vps_first_day.status,
        review_index_status=review_index.status,
    )


def _refresh_local_runtime_latency_if_selected(root: Path) -> None:
    fields = _decision_record_fields(root / "docs" / "PHASE2_VPS_SELECTION_MATRIX.md")
    if fields.get("selected_provider", "").strip().upper() != "LOCAL_SYSTEM_RUNTIME":
        return
    generate_phase2_vps_latency_report(
        root=root,
        provider="LOCAL_SYSTEM_RUNTIME",
        region=fields.get("selected_region", "Local Windows workstation"),
        endpoint="Capital.ComMena MT5 local authorization ping baseline",
    )


def _decision_record_fields(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    fields: dict[str, str] = {}
    in_decision_record = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            in_decision_record = line.strip().lower() == "## decision record"
            continue
        if not in_decision_record or not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Field |"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 2:
            fields[parts[0].strip().lower().replace(" ", "_").replace("-", "_")] = parts[1].strip()
    return fields


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
        "--phase2b-passive-files-dir",
        type=Path,
        default=DEFAULT_PHASE2B_PASSIVE_FILES_DIR,
        help="MT5 Files directory containing passive Phase 2B observer attachment logs.",
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
        phase2b_passive_files_dir=args.phase2b_passive_files_dir,
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
    print(f"Phase 2 demo account isolation: {output.phase2_demo_account_isolation_status}")
    print(f"Experimental executor governance: {output.experimental_executor_governance_status}")
    print(f"Cost suspension enforcement: {output.cost_suspension_enforcement_status}")
    print(f"Broker action boundary: {output.broker_action_boundary_status}")
    print(f"Phase 2 readiness consistency: {output.phase2_readiness_consistency_status}")
    print(f"Phase 2 owner action packet: {output.phase2_owner_action_status}")
    print(f"Phase 2 VPS bootstrap packet: {output.phase2_vps_bootstrap_status}")
    print(f"VPS first-day verification: {output.vps_first_day_status}")
    print(f"Phase 2B passive import: {output.phase2b_passive_import_status}")
    print(f"Phase 2B passive observer: {output.phase2b_passive_observer_status}")
    print(f"Cost-suspended promotion blocker: {output.cost_suspended_promotion_blocker_status}")
    print(f"Phase 3 proxy non-authoritative: {output.phase3_proxy_non_authoritative_status}")
    print(f"Review index: {output.review_index_status}")
    return 0 if output.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
