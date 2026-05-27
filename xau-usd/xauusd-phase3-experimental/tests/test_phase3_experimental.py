from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample_would_signals.csv"


def test_phase3_simulation_filters_unsafe_rows_and_deduplicates_family_events(tmp_path: Path):
    module = _load_script("simulate_phase3_from_would_signals")

    output = module.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")

    assert output.status == "EXPERIMENTAL_COST_SUSPEND_SCENARIO"
    assert output.accepted_events == 7
    assert output.rejected_source_rows == 6
    summary = json.loads(output.summary_path.read_text(encoding="utf-8"))
    assert summary["raw_observer_event_count"] == 7
    assert summary["family_unique_event_count"] == 3
    assert summary["observer_duplicate_count"] == 1
    assert summary["observer_conflict_count"] == 2
    assert summary["primary_stream_allowed_count"] == 3
    assert summary["kill_rule_counts"] == {
        "COST_WATCH": 1,
        "NORMAL": 5,
        "SUSPEND_FAMILY": 1,
    }
    with output.ledger_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    roles = {row["source_cluster_id"]: row for row in rows}
    assert roles["WS100"]["family_event_role"] == "PRIMARY_EXECUTION_CANDIDATE"
    assert roles["WS100"]["primary_stream_allowed"] == "true"
    assert roles["WS101"]["family_event_role"] == "OBSERVER_DUPLICATE"
    assert roles["WS101"]["primary_stream_allowed"] == "false"
    assert roles["WS104"]["family_event_role"] == "OBSERVER_CONFLICT"
    assert roles["WS105"]["family_event_role"] == "OBSERVER_CONFLICT"
    assert roles["WS106"]["family_event_role"] == "OBSERVER_ONLY_NO_PRIMARY"
    assert roles["WS102"]["kill_rule_state"] == "COST_WATCH"
    assert roles["WS103"]["kill_rule_state"] == "SUSPEND_FAMILY"
    assert roles["WS100"]["cost_mode"] == "entry_exit_proxy"
    assert "This report has no authority over Phase 2 readiness." in output.report_path.read_text(encoding="utf-8")


def test_phase3_cost_modes_are_explicit(tmp_path: Path):
    module = _load_script("simulate_phase3_from_would_signals")

    entry_only = module.simulate_phase3_from_would_signals(
        FIXTURE,
        tmp_path / "entry",
        cost_mode="entry_only_proxy",
    )
    stress = module.simulate_phase3_from_would_signals(
        FIXTURE,
        tmp_path / "stress",
        cost_mode="stress_2x_p95_proxy",
    )

    entry_summary = json.loads(entry_only.summary_path.read_text(encoding="utf-8"))
    stress_summary = json.loads(stress.summary_path.read_text(encoding="utf-8"))
    assert entry_summary["cost_mode"] == "entry_only_proxy"
    assert stress_summary["cost_mode"] == "stress_2x_p95_proxy"
    assert stress_summary["kill_rule_counts"]["SUSPEND_FAMILY"] > entry_summary["kill_rule_counts"]["SUSPEND_FAMILY"]


def test_phase3_status_preserves_real_phase2_pending_and_reports_safety(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    safety_module = _load_script("audit_phase3_experimental_safety")
    suspend_module = _load_script("analyze_phase3_suspend_family")
    manifest_module = _load_script("generate_phase3_experimental_manifest")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, phase3 / "outputs" / "reports")
    safety_module.generate_phase3_safety_report(ROOT, phase3 / "outputs" / "reports")
    suspend_module.analyze_suspend_family(simulation.ledger_path, phase3 / "outputs" / "reports")
    manifest_module.generate_phase3_experimental_manifest(phase3, repo)
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "latest_row": {
                        "bar_time": "2026.05.27 19:20:00",
                        "run_id": "phase1-dry-run-v0.7",
                        "dry_run": "true",
                        "trade_permission": "false",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["status"] == "EXPERIMENTAL_COST_SUSPEND_SCENARIO"
    assert status["real_phase2_readiness"] == "PENDING"
    assert status["authorized_for_deployment"] is False
    assert status["mt5_runtime_touched"] is False
    assert status["safety"]["status"] == "PASS"
    assert status["suspend_family_review"]["status"] == "REVIEW_READY"
    assert status["suspend_family_review"]["suspend_unique_family_events"] == 1
    assert status["manifest"]["status"] == "PASS"
    assert status["owner_approval_flow"] == "excluded_from_real_phase2_phase3_approval_flow"
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in (
        phase3 / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_STATUS.md"
    ).read_text(encoding="utf-8")


def test_phase3_safety_audit_passes_and_report_is_generated(tmp_path: Path):
    module = _load_script("audit_phase3_experimental_safety")

    findings = module.audit_phase3_tree(ROOT)
    output = module.generate_phase3_safety_report(ROOT, tmp_path / "reports")

    assert findings == []
    assert output.status == "PASS"
    assert output.findings_count == 0
    assert output.report_path.exists()
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in output.report_path.read_text(
        encoding="utf-8"
    )


def test_phase3_safety_audit_detects_forbidden_broker_action_reference(tmp_path: Path):
    module = _load_script("audit_phase3_experimental_safety")
    root = tmp_path / "xauusd-phase3-experimental"
    root.mkdir()
    forbidden = "Order" + "Send"
    (root / "unsafe.py").write_text(f"def unsafe():\n    return '{forbidden}'\n", encoding="utf-8")

    output = module.generate_phase3_safety_report(root)

    assert output.status == "FAIL"
    assert output.findings_count == 1
    summary = json.loads(output.summary_path.read_text(encoding="utf-8"))
    assert summary["findings"][0]["term"] == forbidden


def test_phase3_suspend_family_review_summarizes_primary_vs_duplicate_rows(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    suspend_module = _load_script("analyze_phase3_suspend_family")
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")

    review_path = suspend_module.analyze_suspend_family(simulation.ledger_path, tmp_path / "reports")

    review = json.loads(review_path.read_text(encoding="utf-8"))
    assert review["status"] == "REVIEW_READY"
    assert review["suspend_raw_rows"] == 1
    assert review["suspend_unique_family_events"] == 1
    assert review["suspend_primary_rows"] == 1
    assert review["suspend_duplicate_rows"] == 0
    assert review["diagnosis_counts"] == {"tight_stop_cost_dominates": 1}
    report = (tmp_path / "reports" / "PHASE3_SUSPEND_FAMILY_REVIEW.md").read_text(encoding="utf-8")
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def _load_script(name: str):
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
