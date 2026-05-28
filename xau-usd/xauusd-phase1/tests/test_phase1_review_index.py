from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_review_index_summarizes_phase1_artifacts(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    report_dir = root / "outputs" / "reports"
    bundle_dir = root / "outputs" / "review_bundles"
    report_dir.mkdir(parents=True)
    bundle_dir.mkdir(parents=True)
    _write_reports(report_dir)
    _write_status_summary(report_dir / "PHASE1_STATUS_SUMMARY.json")
    (report_dir / "PHASE1_WOULD_SIGNAL_REVIEW.csv").write_text("cluster_id\n1\n", encoding="utf-8")
    (report_dir / "PHASE1_SOAK_HISTORY.csv").write_text(
        "\n".join(
            [
                "created_at_utc,files_dir,log_verification,soak_analysis,runtime_health,would_signal,acceptance,decision_rows,unique_run_ids,latest_run_id,latest_bar_time,latest_timestamp_broker,latest_timestamp_local,latest_risk_state,latest_trade_permission,latest_dry_run,latest_server_time_status,latest_br_stage,latest_br_direction,latest_br_would_signal,would_signal_rows,would_signal_clusters,required_soak_days,observed_soak_days,soak_progress_pct,summary_path,log_report,soak_report,would_signal_report,would_signal_csv,acceptance_report",
                "2026-05-21T22:14:43+00:00,C:/MT5PortableGoldMission/MQL5/Files,PASS,PASS,PASS,PASS,FAIL,95,5,phase1-dry-run-v0.5,2026.05.21 22:10:00,2026.05.21 22:10:00,2026.05.22 02:09:59,NORMAL,false,true,CLOCK_OK,WAIT_LEVEL_BREAK_RETEST,SHORT,false,6,6,5,0.3507,7.01,summary,log,soak,would,csv,acceptance",
                "2026-05-21T22:15:28+00:00,C:/MT5PortableGoldMission/MQL5/Files,PASS,PASS,PASS,PASS,PENDING,96,5,phase1-dry-run-v0.5,2026.05.21 22:15:00,2026.05.21 22:15:00,2026.05.22 02:14:59,NORMAL,false,true,CLOCK_OK,WAIT_LEVEL_BREAK_RETEST,LONG,false,6,6,5,0.3542,7.08,summary,log,soak,would,csv,acceptance",
            ]
        ),
        encoding="utf-8",
    )
    bundle_path = bundle_dir / "PHASE1_DRY_RUN_BUNDLE_TEST.zip"
    manifest_path = bundle_dir / "PHASE1_DRY_RUN_BUNDLE_TEST_manifest.json"
    bundle_path.write_bytes(b"bundle")
    manifest_path.write_text("{}", encoding="utf-8")

    output = module.generate_phase1_review_index(
        root,
        report_dir / "PHASE1_REVIEW_INDEX.md",
        bundle_path,
        manifest_path,
    )

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PENDING"
    assert "Phase 1 Review Index" in report
    assert "Acceptance report | PENDING" in report
    assert "Phase 2 demo countdown" in report
    assert "Phase 2 VPS bootstrap packet" in report
    assert "Phase 2 local MT5 network baseline" in report
    assert "Phase 2 VPS first-day verification" in report
    assert "Historical acceptance FAIL rows were seen" in report
    assert "PHASE1_DRY_RUN_BUNDLE_TEST.zip" in report
    assert "Broker-action code remains outside the approved scope" in report


def test_review_index_fails_when_required_artifact_missing(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    (root / "outputs" / "reports").mkdir(parents=True)

    output = module.generate_phase1_review_index(root)

    assert output.status == "FAIL"
    assert any(item.status == "FAIL" for item in output.items)


def test_phase2_readiness_failure_is_informational_for_phase1_index(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    report_dir = root / "outputs" / "reports"
    report_dir.mkdir(parents=True)
    _write_reports(report_dir)
    (report_dir / "PHASE2_READINESS_REPORT.md").write_text(
        "# Phase 2 readiness\n\nOverall status: FAIL\n",
        encoding="utf-8",
    )
    _write_status_summary(report_dir / "PHASE1_STATUS_SUMMARY.json")
    (report_dir / "PHASE1_WOULD_SIGNAL_REVIEW.csv").write_text("cluster_id\n1\n", encoding="utf-8")
    (report_dir / "PHASE1_SOAK_HISTORY.csv").write_text("created_at_utc,acceptance\n", encoding="utf-8")

    output = module.generate_phase1_review_index(root)

    assert output.status == "PENDING"
    assert any(
        item.artifact == "Phase 2 readiness report" and item.status == "FAIL"
        for item in output.items
    )


def test_phase2_transition_failures_are_informational_for_phase1_index(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    report_dir = root / "outputs" / "reports"
    report_dir.mkdir(parents=True)
    _write_reports(report_dir)
    (report_dir / "PHASE2_VPS_LATENCY_REPORT.md").write_text(
        "# Phase 2 VPS latency\n\nOverall status: FAIL\n",
        encoding="utf-8",
    )
    _write_status_summary(report_dir / "PHASE1_STATUS_SUMMARY.json")
    (report_dir / "PHASE1_WOULD_SIGNAL_REVIEW.csv").write_text("cluster_id\n1\n", encoding="utf-8")
    (report_dir / "PHASE1_SOAK_HISTORY.csv").write_text("created_at_utc,acceptance\n", encoding="utf-8")

    output = module.generate_phase1_review_index(root)

    assert output.status == "PENDING"
    assert any(
        item.artifact == "Phase 2 VPS latency report" and item.status == "FAIL"
        for item in output.items
    )


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase1_review_index.py"
    spec = importlib.util.spec_from_file_location("generate_phase1_review_index", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase1_review_index"] = module
    spec.loader.exec_module(module)
    return module


def _write_reports(report_dir: Path) -> None:
    statuses = {
        "PHASE1_ACCEPTANCE_REPORT.md": "PENDING",
        "PHASE1_RUNTIME_HEALTH_REPORT.md": "PASS",
        "PHASE1_DRY_RUN_LOG_REPORT.md": "PASS",
        "PHASE1_SOAK_DRIFT_REPORT.md": "PASS",
        "PHASE1_WOULD_SIGNAL_REPORT.md": "PASS",
        "PHASE1_SOAK_HISTORY_REPORT.md": "PASS",
        "PHASE2_READINESS_REPORT.md": "PENDING",
        "PHASE2_DEMO_COUNTDOWN.md": "DEMO_NOT_READY",
        "PHASE2_DEMO_PREFLIGHT_REPORT.md": "PENDING",
        "PHASE2_OWNER_ACTION_PACKET.md": "WAITING_AND_OWNER_ACTION_REQUIRED",
        "PHASE2_VPS_BOOTSTRAP_PACKET.md": "WAITING_AND_VPS_BOOTSTRAP_PENDING",
        "PHASE2_VPS_LATENCY_REPORT.md": "PENDING",
        "PHASE2_LOCAL_MT5_NETWORK_BASELINE.md": "PASS",
        "PHASE2_VPS_FIRST_DAY_VERIFICATION.md": "PENDING",
    }
    for name, status in statuses.items():
        (report_dir / name).write_text(f"# {name}\n\nOverall status: {status}\n", encoding="utf-8")


def _write_status_summary(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "status": {
                    "log_verification": "PASS",
                    "soak_analysis": "PASS",
                    "runtime_health": "PASS",
                    "would_signal": "PASS",
                    "acceptance": "PENDING",
                },
                "runtime": {
                    "decision_rows": 81,
                    "latest_row": {
                        "bar_time": "2026.05.21 20:00:00",
                        "dry_run": "true",
                        "trade_permission": "false",
                        "server_time_status": "CLOCK_OK",
                        "br_stage": "WAIT_LEVEL_BREAK_RETEST",
                    },
                },
                "soak": {
                    "progress_pct": 5.21,
                },
                "would_signal": {
                    "rows": 4,
                    "clusters": 4,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
