from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from phase0.cli import main
from phase0.config import ConfigError, load_project_config
from phase0.artifact_verifier import verify_real_artifacts
from phase0.hashing import register_hypotheses
from phase0.holdout import write_run_context_manifest
from phase0.intrabar import generate_intrabar_ambiguity_report
from phase0.manifests import generate_result_manifest
from phase0.mt5_presets import generate_mt5_bar_export_presets
from phase0.reference import validate_reference_files
from phase0.review_bundle import generate_review_bundle
from phase0.snapshot import generate_snapshot
from phase0.spread_analysis import analyze_spread_logs
from phase0.workflow import run_all_phase0


def test_analyze_spread_logs_writes_cost_report(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    _write_sample_spread_log(root)
    config = load_project_config(root)

    output = analyze_spread_logs(config, min_observations=3, min_observed_days=1)

    assert output.status == "PASS"
    assert output.measured_cost_model_path.exists()
    assert output.measured_report_path.exists()
    assert "Overall status: PASS" in output.measured_report_path.read_text(encoding="utf-8")
    metrics = pd.read_csv(output.measured_cost_model_path)
    assert {"global", "hour_utc", "day_of_week_utc", "rollover"}.issubset(set(metrics["scope"]))
    assert output.report_path.read_text(encoding="utf-8").startswith("# Spread Distribution Report")


def test_generate_measured_cost_model_pending_without_logs(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)

    output = analyze_spread_logs(config, allow_pending=True)

    assert output.status == "PENDING"
    assert output.source_files == ()
    assert "Overall status: PENDING" in output.measured_report_path.read_text(encoding="utf-8")


def test_analyze_spread_logs_excludes_weekend_legacy_rows_from_coverage(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    _write_legacy_weekend_spread_log(root)
    config = load_project_config(root)

    output = analyze_spread_logs(config, min_observations=2, min_observed_days=3)

    assert output.status == "PENDING"
    measured_text = output.measured_report_path.read_text(encoding="utf-8")
    assert "Overall status: PENDING" in measured_text
    assert "legacy_missing" in measured_text
    assert "Weekend/closed-market rows excluded: 1" in measured_text
    assert "Why Observed Days Reset" in measured_text
    assert "Fresh observed market days, not source-file count or legacy row count, control PASS/PENDING." in measured_text
    metrics = pd.read_csv(output.measured_cost_model_path)
    assert "Saturday" not in set(metrics.loc[metrics["scope"] == "day_of_week_utc", "bucket"])
    assert int(metrics.loc[metrics["scope"] == "global", "observations"].iloc[0]) == 2


def test_generate_snapshot_includes_required_files(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    generate_mt5_bar_export_presets(config)
    (root / "outputs" / "reports").mkdir(parents=True)
    (root / "outputs" / "reports" / "PHASE0_VERDICT.md").write_text("pending\n", encoding="utf-8")

    output = generate_snapshot(config)

    assert output.snapshot_path.exists()
    with zipfile.ZipFile(output.snapshot_path) as archive:
        names = set(archive.namelist())
    assert "config/phase0.yaml" in names
    assert "docs/hypothesis_trend_pullback.md" in names
    assert "data/README_DATA.md" in names
    assert "mt5/PassiveSpreadLogger_XAUUSD.mq5" in names
    assert "mt5/PassiveBarExporter_Phase0.mq5" in names
    assert "mt5/README_BAR_EXPORTER.md" in names
    assert "mt5/bar_exporter_set_example.set" in names
    assert "scripts/run_all_phase0.py" in names
    assert "scripts/generate_result_manifest.py" in names
    assert "src/phase0/snapshot.py" in names
    assert "outputs/hashes/hypothesis_hash_manifest.csv" in names
    assert "outputs/mt5_bar_export_presets/PHASE0_MT5_BAR_EXPORT_PRESETS.csv" in names
    assert "outputs/mt5_bar_export_presets/XAUUSD_capital_com_bar_export.set" in names
    assert "outputs/manifests/PHASE0_RESULT_MANIFEST.csv" in names
    assert "git_commit.txt" in names
    assert "git_status.txt" in names


def test_generate_result_manifest_hashes_generated_outputs(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    report_path = root / "outputs" / "reports" / "PHASE0_VERDICT.md"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("# Verdict\n\nSynthetic smoke only.\n", encoding="utf-8")
    readiness_path = root / "outputs" / "manifests" / "PHASE0_DATA_READINESS.md"
    readiness_path.parent.mkdir(parents=True)
    readiness_path.write_text("# Readiness\n\nStatus: BLOCKED\n", encoding="utf-8")

    manifest_path = generate_result_manifest(config)

    rows = pd.read_csv(manifest_path)
    report_row = rows.loc[rows["path"] == "outputs/reports/PHASE0_VERDICT.md"].iloc[0]
    assert report_row["artifact_type"] == "reports"
    assert report_row["sha256"] == _sha256(report_path)
    readiness_row = rows.loc[rows["path"] == "outputs/manifests/PHASE0_DATA_READINESS.md"].iloc[0]
    assert readiness_row["artifact_type"] == "manifests"
    assert readiness_row["sha256"] == _sha256(readiness_path)
    assert "outputs/hashes/hypothesis_hash_manifest.csv" in set(rows["path"])
    assert "outputs/manifests/PHASE0_RUN_CONTEXT.json" in set(rows["path"])
    assert "outputs/manifests/PHASE0_RESULT_MANIFEST.csv" not in set(rows["path"])


def test_true_holdout_context_manifest_records_required_fields(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)

    output_path = write_run_context_manifest(config)

    data = output_path.read_text(encoding="utf-8")
    assert '"true_holdout_period_start"' in data
    assert '"true_holdout_period_end"' in data
    assert '"true_holdout_unlocked": false' in data
    assert '"true_holdout_unlock_file"' in data
    assert '"true_holdout_overlap_detected"' in data


def test_validate_reference_allows_documented_missing_specs(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)

    output = validate_reference_files(config)

    assert output.status == "DOCUMENTED_MISSING"
    assert "PATH_TO_10.md" in output.missing_files


def test_generate_review_bundle_includes_review_evidence(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    report_path = root / "outputs" / "reports" / "PHASE0_VERDICT.md"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("# Verdict\n\nPending review.\n", encoding="utf-8")
    readiness_path = root / "outputs" / "manifests" / "PHASE0_DATA_READINESS.md"
    readiness_path.parent.mkdir(parents=True)
    readiness_path.write_text("# Readiness\n\nStatus: BLOCKED\n", encoding="utf-8")

    output = generate_review_bundle(config)

    assert output.bundle_path.exists()
    with zipfile.ZipFile(output.bundle_path) as archive:
        names = set(archive.namelist())
    assert "review_bundle_manifest.json" in names
    assert "docs/hypothesis_breakout_retest.md" in names
    assert "outputs/reports/PHASE0_VERDICT.md" in names
    assert "outputs/manifests/PHASE0_DATA_READINESS.md" in names
    assert "outputs/hashes/hypothesis_hash_manifest.csv" in names
    with zipfile.ZipFile(output.bundle_path) as archive:
        manifest = archive.read("review_bundle_manifest.json").decode("utf-8")
    assert "true_holdout_status" in manifest


def test_generate_intrabar_ambiguity_report_summarizes_trade_csv(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    trades_dir = root / "outputs" / "matrix_results" / "breakout_retest"
    trades_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            _trade_row("2020-01-01T00:00:00+00:00", "2020-01-01T00:00:00+00:00", -100.0, True),
            _trade_row("2020-01-01T01:00:00+00:00", "2020-01-01T01:05:00+00:00", 200.0, False),
        ]
    ).to_csv(trades_dir / "cell_1_breakout_retest_capital_com_median_trades.csv", index=False)
    config = load_project_config(root)

    outputs = generate_intrabar_ambiguity_report(config, "breakout_retest")

    assert len(outputs) == 1
    assert outputs[0].total_trades == 2
    assert outputs[0].ambiguous_exit_trades == 1
    assert outputs[0].same_timestamp_exit_trades == 1
    assert outputs[0].adverse_first_profit_factor == "2"
    assert outputs[0].report_path.exists()


def test_verify_real_artifacts_passes_complete_evidence_package(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    (root / "outputs" / "manifests").mkdir(parents=True, exist_ok=True)
    (root / "outputs" / "manifests" / "PHASE0_DATA_READINESS.md").write_text("PASS\n", encoding="utf-8")
    (root / "outputs" / "manifests" / "PHASE0_DATA_MANIFEST.md").write_text("manifest\n", encoding="utf-8")
    reports_dir = root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "PHASE0_VERDICT.md").write_text(
        "\n".join(
            [
                "# Phase 0 Consolidated Verdict",
                "",
                "## Experts Approved for Phase 1",
                "",
                "- breakout_retest",
                "",
                "## Experts Pending Manual Review",
                "",
                "None.",
                "",
                "## Invalid Pre-Registration",
                "",
                "None.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for expert in ("trend_pullback", "breakout_retest", "range_mr"):
        (reports_dir / f"{expert}_intrabar_ambiguity_report.md").write_text("ok\n", encoding="utf-8")
    adversarial_dir = root / "outputs" / "adversarial_review"
    adversarial_dir.mkdir(parents=True, exist_ok=True)
    for expert in ("trend_pullback", "breakout_retest", "range_mr"):
        (adversarial_dir / f"{expert}_adversarial_score.md").write_text("PASS\n", encoding="utf-8")
    generate_result_manifest(config)
    generate_review_bundle(config)

    output = verify_real_artifacts(config)

    assert output.status == "PASS"
    assert output.report_path.exists()


def test_verify_real_artifacts_allows_rejected_expert_pending_gate_detail(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
    (root / "outputs" / "manifests").mkdir(parents=True, exist_ok=True)
    (root / "outputs" / "manifests" / "PHASE0_DATA_READINESS.md").write_text("PASS\n", encoding="utf-8")
    (root / "outputs" / "manifests" / "PHASE0_DATA_MANIFEST.md").write_text("manifest\n", encoding="utf-8")
    reports_dir = root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "PHASE0_VERDICT.md").write_text(
        "\n".join(
            [
                "# Phase 0 Consolidated Verdict",
                "",
                "| Expert | Adversarial | FINAL |",
                "| --- | --- | --- |",
                "| trend_pullback | PENDING | FAIL |",
                "| breakout_retest | PASS | PASS |",
                "| range_mr | PENDING | FAIL |",
                "",
                "## Experts Approved for Phase 1",
                "",
                "- breakout_retest",
                "",
                "## Experts Rejected",
                "",
                "- trend_pullback",
                "- range_mr",
                "",
                "## Experts Pending Manual Review",
                "",
                "None.",
                "",
                "## Invalid Pre-Registration",
                "",
                "None.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for expert in ("trend_pullback", "breakout_retest", "range_mr"):
        (reports_dir / f"{expert}_intrabar_ambiguity_report.md").write_text("ok\n", encoding="utf-8")
    adversarial_dir = root / "outputs" / "adversarial_review"
    adversarial_dir.mkdir(parents=True, exist_ok=True)
    for expert in ("trend_pullback", "breakout_retest", "range_mr"):
        (adversarial_dir / f"{expert}_adversarial_score.md").write_text("ok\n", encoding="utf-8")
    generate_result_manifest(config)
    generate_review_bundle(config)

    output = verify_real_artifacts(config)

    assert output.status == "PASS"


def test_run_all_cli_synthetic(project_root, tmp_path, capsys):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)

    exit_code = main(["--root", str(root), "run-all", "--synthetic-sample"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run-all complete" in captured.out
    assert (root / "outputs" / "reports" / "PHASE0_VERDICT.md").exists()
    assert (root / "outputs" / "manifests" / "PHASE0_RESULT_MANIFEST.csv").exists()


def test_run_all_real_data_preflight_writes_readiness_artifacts(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    _write_complete_hypotheses(root)
    config = load_project_config(root)
    register_hypotheses(config)

    with pytest.raises(ConfigError, match="import-required-bars"):
        run_all_phase0(config)

    assert (root / "outputs" / "manifests" / "PHASE0_DATA_REQUIREMENTS.csv").exists()
    assert (root / "outputs" / "manifests" / "PHASE0_DATA_MANIFEST.md").exists()
    assert (root / "outputs" / "manifests" / "PHASE0_DATA_READINESS.md").exists()


def _copy_project_shell(project_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(project_root / "config", root / "config")
    shutil.copytree(project_root / "docs", root / "docs")
    shutil.copytree(project_root / "scripts", root / "scripts")
    shutil.copytree(project_root / "mt5", root / "mt5")
    shutil.copytree(project_root / "src" / "phase0", root / "src" / "phase0")
    shutil.copytree(project_root / "tests", root / "tests")
    shutil.copytree(project_root / "reference", root / "reference")
    for name in ("pyproject.toml", "requirements.txt", "README.md"):
        shutil.copy2(project_root / name, root / name)
    (root / "data").mkdir(parents=True)
    shutil.copy2(project_root / "data" / "README_DATA.md", root / "data" / "README_DATA.md")
    (root / "outputs" / "hashes").mkdir(parents=True)
    return root


def _trade_row(
    entry_time_utc: str,
    exit_time_utc: str,
    net_pnl_usd: float,
    ambiguous_exit: bool,
) -> dict[str, object]:
    return {
        "expert": "breakout_retest",
        "symbol": "XAUUSD",
        "direction": "LONG",
        "entry_time_utc": entry_time_utc,
        "exit_time_utc": exit_time_utc,
        "entry_price": 2000.0,
        "exit_price": 2001.0,
        "stop_loss": 1999.0,
        "take_profit": 2001.5,
        "lots": 0.1,
        "gross_pnl_usd": net_pnl_usd,
        "costs_usd": 0.0,
        "net_pnl_usd": net_pnl_usd,
        "r_multiple": net_pnl_usd / 100.0,
        "exit_reason": "stop_loss" if net_pnl_usd < 0 else "take_profit",
        "metadata_ambiguous_exit": ambiguous_exit,
    }


def _write_sample_spread_log(root: Path) -> None:
    log_dir = root / "outputs" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        _spread_row("2026-01-05 08:00:00", 21.0, "LONDON", "false"),
        _spread_row("2026-01-05 09:00:00", 24.0, "LONDON", "false"),
        _spread_row("2026-01-05 22:00:00", 60.0, "ROLLOVER", "true"),
    ]
    pd.DataFrame(rows).to_csv(log_dir / "spread_log_123_demo_XAUUSD_20260105.csv", index=False)


def _write_legacy_weekend_spread_log(root: Path) -> None:
    log_dir = root / "outputs" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        _legacy_spread_row("2026-01-02 09:00:00", 50.0, "LONDON", "false"),
        _legacy_spread_row("2026-01-03 09:00:00", 50.0, "WEEKEND", "false"),
        _legacy_spread_row("2026-01-05 09:00:00", 75.0, "LONDON", "false"),
    ]
    pd.DataFrame(rows).to_csv(log_dir / "spread_log_123_demo_XAUUSD_legacy.csv", index=False)


def _write_complete_hypotheses(root: Path) -> None:
    for filename, expert_name in (
        ("hypothesis_trend_pullback.md", "Trend Pullback"),
        ("hypothesis_breakout_retest.md", "Breakout-Retest"),
        ("hypothesis_range_mr.md", "Range Mean-Reversion"),
    ):
        (root / "docs" / filename).write_text(
            f"""# Hypothesis: {expert_name} Expert

Expert name: {expert_name}
Hypothesis date: 2026-05-21
Hypothesis version: v1.0
Author / owner: Phase 0 research desk

## Mechanical Definition

The expert uses a fixed mechanical strategy implementation with completed bars only.

## Expected Behavior

Expected trade count per year: 200 +/- 20%

Expected cost-adjusted PF: 1.30 +/- 0.3

Expected losing-month percentage: 35% +/- 10%

Expected worst single month: -8% equity

Expected max consecutive zero months: 1

Expected R-multiple distribution: median near -1R with positive right-tail winners.

## Why This Hypothesis Should Exist

The setup is expected to capture recurring behavior under adverse-first assumptions.

## What Would Falsify It

The hypothesis is falsified by failed matrix, decile, multisymbol, or adversarial gates.
""",
            encoding="utf-8",
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _spread_row(gmt_time: str, spread_points: float, session_label: str, rollover: str) -> dict[str, object]:
    return {
        "broker_time": gmt_time,
        "gmt_time": gmt_time,
        "local_time": gmt_time,
        "tick_time": gmt_time,
        "tick_time_msc": "1760000000000",
        "seconds_since_tick": "0",
        "tick_fresh": "true",
        "account": "123",
        "server": "demo",
        "symbol": "XAUUSD",
        "bid": 2000.0,
        "ask": 2000.2,
        "spread_price": 0.2,
        "spread_points": spread_points,
        "point": 0.01,
        "digits": 2,
        "session_label": session_label,
        "is_rollover_window": rollover,
    }


def _legacy_spread_row(gmt_time: str, spread_points: float, session_label: str, rollover: str) -> dict[str, object]:
    return {
        "broker_time": gmt_time,
        "gmt_time": gmt_time,
        "local_time": gmt_time,
        "account": "123",
        "server": "demo",
        "symbol": "XAUUSD",
        "bid": 2000.0,
        "ask": 2000.5,
        "spread_price": 0.5,
        "spread_points": spread_points,
        "point": 0.01,
        "digits": 2,
        "session_label": session_label,
        "is_rollover_window": rollover,
    }
