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
    assert summary["gross_expectancy_r_source"] == "fixed_notional_phase0_baseline"
    assert summary["baseline_assumed_cost_r"] == 0.3228
    assert summary["baseline_net_expectancy_r"] == 0.1888
    assert "median_net_delta_vs_assumed_baseline_r" in summary
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
    assert roles["WS100"]["gross_expectancy_r_source"] == "fixed_notional_phase0_baseline"
    assert roles["WS100"]["baseline_assumed_cost_r"] == "0.3228"
    assert roles["WS100"]["baseline_net_expectancy_r"] == "0.1888"
    assert roles["WS100"]["proxy_cost_r"] == roles["WS100"]["measured_cost_r_proxy"]
    assert roles["WS100"]["net_after_proxy_from_gross_r"] == roles["WS100"]["net_expectancy_r_after_proxy_cost"]
    assert "net_delta_vs_assumed_baseline_r" in roles["WS100"]
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


def test_non_primary_observers_cannot_be_primary_stream_allowed(tmp_path: Path):
    module = _load_script("simulate_phase3_from_would_signals")

    output = module.simulate_phase3_from_would_signals(FIXTURE, tmp_path / "reports")

    with output.ledger_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row["observer"] != "breakout_retest":
            assert row["primary_stream_allowed"] == "false"
            assert row["family_event_role"] != "PRIMARY_EXECUTION_CANDIDATE"


def test_p95_proxy_can_suspend_without_mutating_real_phase2_readiness(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulator.simulate_phase3_from_would_signals(
        FIXTURE,
        phase3 / "outputs" / "reports",
        cost_mode="p95_fresh_proxy",
    )
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(json.dumps({"runtime": {"latest_row": {}}}), encoding="utf-8")
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    simulation = json.loads((phase3 / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_SIMULATION.json").read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert simulation["cost_mode"] == "p95_fresh_proxy"
    assert simulation["kill_rule_counts"]["SUSPEND_FAMILY"] > 0
    assert status["real_phase2_readiness"] == "PENDING"
    assert status["authorized_for_deployment"] is False


def test_phase3_cost_mode_comparison_runs_all_modes(tmp_path: Path):
    module = _load_script("generate_phase3_cost_mode_comparison")

    path = module.generate_cost_mode_comparison(FIXTURE, tmp_path / "reports")

    comparison = json.loads(path.read_text(encoding="utf-8"))
    rows = comparison["rows"]
    modes = {row["cost_mode"] for row in rows}
    assert modes == {"entry_only_proxy", "entry_exit_proxy", "p95_fresh_proxy", "stress_2x_p95_proxy"}
    by_mode = {row["cost_mode"]: row for row in rows}
    assert by_mode["stress_2x_p95_proxy"]["suspend_family_count"] >= by_mode["entry_only_proxy"]["suspend_family_count"]
    assert by_mode["entry_exit_proxy"]["gross_expectancy_r_source"] == "fixed_notional_phase0_baseline"
    assert by_mode["entry_exit_proxy"]["baseline_assumed_cost_r"] == 0.3228
    assert "median_net_delta_vs_assumed_baseline_r" in by_mode["entry_exit_proxy"]
    assert (tmp_path / "reports" / "PHASE3_COST_MODE_COMPARISON.md").exists()
    assert (tmp_path / "reports" / "PHASE3_COST_MODE_COMPARISON.csv").exists()


def test_phase3_status_preserves_real_phase2_pending_and_reports_safety(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    safety_module = _load_script("audit_phase3_experimental_safety")
    suspend_module = _load_script("analyze_phase3_suspend_family")
    comparison_module = _load_script("generate_phase3_cost_mode_comparison")
    dedup_module = _load_script("generate_phase3_family_dedup_audit")
    manifest_module = _load_script("generate_phase3_experimental_manifest")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulation = simulator.simulate_phase3_from_would_signals(FIXTURE, phase3 / "outputs" / "reports")
    safety_module.generate_phase3_safety_report(ROOT, phase3 / "outputs" / "reports")
    suspend_module.analyze_suspend_family(simulation.ledger_path, phase3 / "outputs" / "reports")
    comparison_module.generate_cost_mode_comparison(FIXTURE, phase3 / "outputs" / "reports")
    dedup_module.generate_family_dedup_audit(FIXTURE, phase3 / "outputs" / "reports")
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
    assert status["broker_action_code_allowed"] is False
    assert status["mt5_runtime_touched"] is False
    assert status["safety"]["status"] == "PASS"
    assert status["suspend_family_review"]["status"] == "REVIEW_READY"
    assert status["suspend_family_review"]["suspend_unique_family_events"] == 1
    assert status["manifest"]["status"] == "PENDING"
    assert status["owner_approval_flow"] == "excluded_from_real_phase2_phase3_approval_flow"
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in (
        phase3 / "outputs" / "reports" / "PHASE3_EXPERIMENTAL_STATUS.md"
    ).read_text(encoding="utf-8")


def test_phase3_status_becomes_boundary_fail_if_safety_fails(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    reports = phase3 / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulator.simulate_phase3_from_would_signals(FIXTURE, reports)
    (reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json").write_text(
        json.dumps({"status": "FAIL", "findings_count": 1}),
        encoding="utf-8",
    )
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(json.dumps({"runtime": {"latest_row": {}}}), encoding="utf-8")
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PENDING\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["status"] == "EXPERIMENTAL_BOUNDARY_FAIL"
    assert status["real_phase2_readiness"] == "PENDING"


def test_phase3_status_cannot_set_authorized_for_deployment_true(tmp_path: Path):
    simulator = _load_script("simulate_phase3_from_would_signals")
    status_module = _load_script("generate_phase3_experimental_status")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    phase1_reports = repo / "xau-usd" / "xauusd-phase1" / "outputs" / "reports"
    phase1_reports.mkdir(parents=True)
    simulator.simulate_phase3_from_would_signals(FIXTURE, phase3 / "outputs" / "reports")
    (phase1_reports / "PHASE1_STATUS_SUMMARY.json").write_text(json.dumps({"runtime": {"latest_row": {}}}), encoding="utf-8")
    (phase1_reports / "PHASE1_ACCEPTANCE_REPORT.md").write_text("Overall status: PASS\n", encoding="utf-8")
    (phase1_reports / "PHASE2_READINESS_REPORT.md").write_text("Overall status: PASS\n", encoding="utf-8")

    status_path = status_module.generate_phase3_experimental_status(phase3, repo)

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["authorized_for_deployment"] is False
    assert status["broker_action_code_allowed"] is False
    assert status["mt5_runtime_touched"] is False
    assert status["owner_approval_flow"] == "excluded_from_real_phase2_phase3_approval_flow"


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


def test_phase3_source_safety_predicate_rejects_each_unsafe_case():
    module = _load_script("simulate_phase3_from_would_signals")
    rows = _read_csv(FIXTURE)
    by_cluster = {row["cluster_id"]: row for row in rows}

    assert module._source_row_is_safe(by_cluster["WS100"]) is True
    assert module._source_row_is_safe(by_cluster["WS107"]) is False  # dry_run=false
    assert module._source_row_is_safe(by_cluster["WS108"]) is False  # trade_permission=true
    assert module._source_row_is_safe(by_cluster["WS109"]) is False  # execution_state != EXECUTION_OK
    assert module._source_row_is_safe(by_cluster["WS110"]) is False  # risk_state != NORMAL
    assert module._source_row_is_safe(by_cluster["WS111"]) is False  # server_time_status != CLOCK_OK
    assert module._source_row_is_safe(by_cluster["WS112"]) is False  # disallowed observer


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
    assert review["gross_expectancy_r_source"] == "fixed_notional_phase0_baseline"
    assert review["baseline_assumed_cost_r"] == 0.3228
    assert review["baseline_net_expectancy_r"] == 0.1888
    assert "median_suspend_net_delta_vs_assumed_baseline_r" in review
    assert review["diagnosis_counts"] == {"tight_stop_cost_dominates": 1}
    report = (tmp_path / "reports" / "PHASE3_SUSPEND_FAMILY_REVIEW.md").read_text(encoding="utf-8")
    assert "PHASE2_READINESS_REPORT.md remains the sole real readiness authority" in report


def test_phase3_family_dedup_audit_detects_same_bar_distinct_level(tmp_path: Path):
    module = _load_script("generate_phase3_family_dedup_audit")
    input_csv = tmp_path / "distinct.csv"
    _write_rows(
        input_csv,
        [
            _safe_row("DL001", "breakout_retest", "2026.05.27 12:00:00", "LONG", "latest_swing_high", "4500.00"),
            _safe_row("DL002", "swing_breakout_retest_v0", "2026.05.27 12:00:00", "LONG", "previous_weekly_high", "4510.00"),
        ],
    )

    path = module.generate_family_dedup_audit(input_csv, tmp_path / "reports")

    audit = json.loads(path.read_text(encoding="utf-8"))
    assert audit["classification_counts"] == {"SAME_BAR_DISTINCT_LEVEL": 1}
    row = audit["rows"][0]
    assert row["classification"] == "SAME_BAR_DISTINCT_LEVEL"
    assert "level_kind" in row["differing_fields"]
    assert "level_price" in row["differing_fields"]


def test_phase3_family_dedup_audit_detects_true_duplicate_and_direction_conflict(tmp_path: Path):
    module = _load_script("generate_phase3_family_dedup_audit")
    input_csv = tmp_path / "dedup.csv"
    _write_rows(
        input_csv,
        [
            _safe_row("DD001", "breakout_retest", "2026.05.27 12:00:00", "LONG", "latest_swing_high", "4500.00"),
            _safe_row("DD002", "swing_breakout_retest_v0", "2026.05.27 12:00:00", "LONG", "latest_swing_high", "4500.00"),
            _safe_row("DD003", "breakout_retest", "2026.05.27 12:05:00", "LONG", "latest_swing_high", "4510.00"),
            _safe_row("DD004", "swing_breakout_retest_v0", "2026.05.27 12:05:00", "SHORT", "latest_swing_high", "4510.00"),
        ],
    )

    path = module.generate_family_dedup_audit(input_csv, tmp_path / "reports")

    audit = json.loads(path.read_text(encoding="utf-8"))
    assert audit["classification_counts"] == {
        "SAME_BAR_DIRECTION_CONFLICT": 1,
        "TRUE_DUPLICATE": 1,
    }


def test_phase3_manifest_is_pending_when_required_reports_are_missing(tmp_path: Path):
    module = _load_script("generate_phase3_experimental_manifest")
    repo = tmp_path / "repo"
    phase3 = repo / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    (reports / "PHASE3_EXPERIMENTAL_SAFETY_REPORT.json").write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    (reports / "PHASE3_EXPERIMENTAL_SIMULATION.json").write_text(json.dumps({"status": "EXPERIMENTAL_ACTIVE"}), encoding="utf-8")

    path = module.generate_phase3_experimental_manifest(phase3, repo)

    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["status"] == "PENDING"
    assert manifest["files"]["phase3_cost_mode_comparison_md"]["exists"] is False


def test_phase3_fixture_report_generation_is_deterministic_for_csv_outputs(tmp_path: Path):
    comparison = _load_script("generate_phase3_cost_mode_comparison")
    dedup = _load_script("generate_phase3_family_dedup_audit")

    comparison.generate_cost_mode_comparison(FIXTURE, tmp_path / "a")
    comparison.generate_cost_mode_comparison(FIXTURE, tmp_path / "b")
    dedup.generate_family_dedup_audit(FIXTURE, tmp_path / "a")
    dedup.generate_family_dedup_audit(FIXTURE, tmp_path / "b")

    assert (tmp_path / "a" / "PHASE3_COST_MODE_COMPARISON.csv").read_text(encoding="utf-8") == (
        tmp_path / "b" / "PHASE3_COST_MODE_COMPARISON.csv"
    ).read_text(encoding="utf-8")
    assert (tmp_path / "a" / "PHASE3_FAMILY_DEDUP_AUDIT.csv").read_text(encoding="utf-8") == (
        tmp_path / "b" / "PHASE3_FAMILY_DEDUP_AUDIT.csv"
    ).read_text(encoding="utf-8")


def test_phase3_artifact_verifier_requires_reports_and_authority_sentence(tmp_path: Path):
    module = _load_script("verify_phase3_experimental_artifacts")
    phase3 = tmp_path / "repo" / "xau-usd" / "xauusd-phase3-experimental"
    reports = phase3 / "outputs" / "reports"
    reports.mkdir(parents=True)
    for name in module.REQUIRED_ARTIFACTS:
        path = reports / name
        if path.suffix == ".md":
            path.write_text(module.PHASE2_AUTHORITY_SENTENCE + "\n", encoding="utf-8")
        else:
            path.write_text("event_id\n", encoding="utf-8")

    assert module.verify_phase3_experimental_artifacts(phase3, tmp_path / "repo") == []

    (reports / "PHASE3_EXPERIMENTAL_STATUS.md").write_text("missing authority\n", encoding="utf-8")
    errors = module.verify_phase3_experimental_artifacts(phase3, tmp_path / "repo")
    assert any("missing required Phase 2 authority sentence" in error for error in errors)


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "cluster_id",
        "observer",
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "bar_time",
        "run_id",
        "symbol",
        "direction",
        "level_kind",
        "level_price",
        "entry_price",
        "stop_loss",
        "take_profit",
        "stop_distance_points",
        "spread_points",
        "risk_state",
        "execution_state",
        "server_time_status",
        "reason_code",
        "trade_permission",
        "dry_run",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _safe_row(
    cluster_id: str,
    observer: str,
    bar_time: str,
    direction: str,
    level_kind: str,
    level_price: str,
) -> dict[str, str]:
    return {
        "cluster_id": cluster_id,
        "observer": observer,
        "timestamp_broker": bar_time,
        "timestamp_utc": "2026.05.27 08:00:00",
        "timestamp_local": "2026.05.27 13:30:00",
        "bar_time": bar_time,
        "run_id": "phase1-dry-run-v0.7",
        "symbol": "XAUUSD",
        "direction": direction,
        "level_kind": level_kind,
        "level_price": level_price,
        "entry_price": "4502.00",
        "stop_loss": "4497.00",
        "take_profit": "4509.50",
        "stop_distance_points": "500.00",
        "spread_points": "30.00",
        "risk_state": "NORMAL",
        "execution_state": "EXECUTION_OK",
        "server_time_status": "CLOCK_OK",
        "reason_code": "DRY_RUN_SIGNAL",
        "trade_permission": "false",
        "dry_run": "true",
    }
