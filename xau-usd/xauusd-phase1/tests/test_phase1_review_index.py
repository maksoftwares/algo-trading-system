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
    (report_dir / "PHASE1_SOAK_HISTORY.csv").write_text("created_at_utc\n2026-05-21T20:00:00+00:00\n", encoding="utf-8")
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
    assert "PHASE1_DRY_RUN_BUNDLE_TEST.zip" in report
    assert "Broker-action code remains outside the approved scope" in report


def test_review_index_fails_when_required_artifact_missing(tmp_path):
    module = _load_module()
    root = tmp_path / "phase1"
    (root / "outputs" / "reports").mkdir(parents=True)

    output = module.generate_phase1_review_index(root)

    assert output.status == "FAIL"
    assert any(item.status == "FAIL" for item in output.items)


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
