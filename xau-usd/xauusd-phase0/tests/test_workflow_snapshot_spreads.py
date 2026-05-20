from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from phase0.cli import main
from phase0.config import ConfigError, load_project_config
from phase0.hashing import register_hypotheses
from phase0.manifests import generate_result_manifest
from phase0.snapshot import generate_snapshot
from phase0.spread_analysis import analyze_spread_logs
from phase0.workflow import run_all_phase0


def test_analyze_spread_logs_writes_cost_report(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    _write_sample_spread_log(root)
    config = load_project_config(root)

    output = analyze_spread_logs(config)

    assert output.measured_cost_model_path.exists()
    metrics = pd.read_csv(output.measured_cost_model_path)
    assert {"global", "hour_utc", "day_of_week_utc", "rollover"}.issubset(set(metrics["scope"]))
    assert output.report_path.read_text(encoding="utf-8").startswith("# Spread Distribution Report")


def test_generate_snapshot_includes_required_files(project_root, tmp_path):
    root = _copy_project_shell(project_root, tmp_path)
    config = load_project_config(root)
    register_hypotheses(config)
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
    assert "scripts/run_all_phase0.py" in names
    assert "scripts/generate_result_manifest.py" in names
    assert "src/phase0/snapshot.py" in names
    assert "outputs/hashes/hypothesis_hash_manifest.csv" in names
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
    assert "outputs/manifests/PHASE0_RESULT_MANIFEST.csv" not in set(rows["path"])


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
    for name in ("pyproject.toml", "requirements.txt", "README.md"):
        shutil.copy2(project_root / name, root / name)
    (root / "data").mkdir(parents=True)
    shutil.copy2(project_root / "data" / "README_DATA.md", root / "data" / "README_DATA.md")
    (root / "outputs" / "hashes").mkdir(parents=True)
    return root


def _write_sample_spread_log(root: Path) -> None:
    log_dir = root / "outputs" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        _spread_row("2026-01-05 08:00:00", 21.0, "LONDON", "false"),
        _spread_row("2026-01-05 09:00:00", 24.0, "LONDON", "false"),
        _spread_row("2026-01-05 22:00:00", 60.0, "ROLLOVER", "true"),
    ]
    pd.DataFrame(rows).to_csv(log_dir / "spread_log_123_demo_XAUUSD_20260105.csv", index=False)


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
