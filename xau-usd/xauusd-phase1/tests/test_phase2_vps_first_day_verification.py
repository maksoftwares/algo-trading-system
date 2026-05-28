from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vps_first_day_verification_pending_without_manual_vps_evidence(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    files_dir = tmp_path / "mt5" / "MQL5" / "Files"
    terminal = tmp_path / "mt5" / "terminal64.exe"
    compile_log = tmp_path / "mt5" / "compile.log"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PENDING")

    output = module.generate_phase2_vps_first_day_verification(
        root=root,
        terminal_path=terminal,
        data_path=tmp_path / "mt5",
        files_dir=files_dir,
        compile_log=compile_log,
    )

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PENDING"
    assert any(check.name == "repo_commit_hash" and check.status == "PASS" for check in output.checks)
    assert any(check.name == "vps_latency_report" and check.status == "PENDING" for check in output.checks)
    assert any(check.name == "ntp_time_sync_evidence" and check.status == "PENDING" for check in output.checks)
    assert "Phase 2 paper-mode authorized | false" in report


def test_vps_first_day_verification_passes_with_complete_evidence(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    files_dir = tmp_path / "mt5" / "MQL5" / "Files"
    terminal = tmp_path / "mt5" / "terminal64.exe"
    compile_log = tmp_path / "mt5" / "compile.log"
    ntp = root / "outputs" / "reports" / "vps_ntp_sync.txt"
    backup = root / "outputs" / "reports" / "vps_backup_config.txt"
    recovery = root / "outputs" / "reports" / "vps_rdp_recovery.txt"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS")
    _write_verified_manual_evidence(ntp, backup, recovery)

    output = module.generate_phase2_vps_first_day_verification(
        root=root,
        terminal_path=terminal,
        data_path=tmp_path / "mt5",
        files_dir=files_dir,
        compile_log=compile_log,
        ntp_evidence_path=ntp,
        backup_evidence_path=backup,
        recovery_evidence_path=recovery,
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "PASS"
    assert payload["phase2_paper_mode_authorized"] is False
    assert payload["demo_trading_authorized"] is False
    assert all(check.status == "PASS" for check in output.checks)


def test_vps_first_day_verification_rejects_template_placeholders(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    files_dir = tmp_path / "mt5" / "MQL5" / "Files"
    terminal = tmp_path / "mt5" / "terminal64.exe"
    compile_log = tmp_path / "mt5" / "compile.log"
    ntp = root / "outputs" / "reports" / "vps_ntp_sync.txt"
    backup = root / "outputs" / "reports" / "vps_backup_config.txt"
    recovery = root / "outputs" / "reports" / "vps_rdp_recovery.txt"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS")
    for path in (ntp, backup, recovery):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "evidence_status: PENDING",
                    "owner_verified: false",
                    "time_sync_enabled: false",
                    "backup_configured: false",
                    "restore_owner_confirmed: false",
                    "recovery_login_verified: false",
                    "notes: TODO replace this template",
                ]
            ),
            encoding="utf-8",
        )

    output = module.generate_phase2_vps_first_day_verification(
        root=root,
        terminal_path=terminal,
        data_path=tmp_path / "mt5",
        files_dir=files_dir,
        compile_log=compile_log,
        ntp_evidence_path=ntp,
        backup_evidence_path=backup,
        recovery_evidence_path=recovery,
    )

    assert output.status == "PENDING"
    assert any(
        check.name == "ntp_time_sync_evidence"
        and check.status == "PENDING"
        and "unverified required field" in check.evidence
        for check in output.checks
    )


def test_vps_first_day_verification_fails_on_unredacted_recovery_secret(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    files_dir = tmp_path / "mt5" / "MQL5" / "Files"
    terminal = tmp_path / "mt5" / "terminal64.exe"
    compile_log = tmp_path / "mt5" / "compile.log"
    ntp = root / "outputs" / "reports" / "vps_ntp_sync.txt"
    backup = root / "outputs" / "reports" / "vps_backup_config.txt"
    recovery = root / "outputs" / "reports" / "vps_rdp_recovery.txt"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS")
    _write_verified_manual_evidence(ntp, backup, recovery)
    recovery.write_text(
        "\n".join(
            [
                "evidence_status: VERIFIED",
                "owner_verified: true",
                "recovery_login_verified: true",
                "password: visible-demo-password",
            ]
        ),
        encoding="utf-8",
    )

    output = module.generate_phase2_vps_first_day_verification(
        root=root,
        terminal_path=terminal,
        data_path=tmp_path / "mt5",
        files_dir=files_dir,
        compile_log=compile_log,
        ntp_evidence_path=ntp,
        backup_evidence_path=backup,
        recovery_evidence_path=recovery,
    )

    assert output.status == "FAIL"
    assert any(
        check.name == "rdp_recovery_login_evidence"
        and check.status == "FAIL"
        and "non-redacted `password`" in check.evidence
        for check in output.checks
    )


def test_vps_first_day_verification_fails_on_unsafe_status_summary(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    files_dir = tmp_path / "mt5" / "MQL5" / "Files"
    terminal = tmp_path / "mt5" / "terminal64.exe"
    compile_log = tmp_path / "mt5" / "compile.log"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS", permission="true")

    output = module.generate_phase2_vps_first_day_verification(
        root=root,
        terminal_path=terminal,
        data_path=tmp_path / "mt5",
        files_dir=files_dir,
        compile_log=compile_log,
    )

    assert output.status == "FAIL"
    assert any(check.name == "phase1_status_summary" and check.status == "FAIL" for check in output.checks)


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase2_vps_first_day_verification.py"
    spec = importlib.util.spec_from_file_location("generate_phase2_vps_first_day_verification", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase2_vps_first_day_verification"] = module
    spec.loader.exec_module(module)
    return module


def _seed_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    (repo / "README.md").write_text("# repo\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=repo, check=True, capture_output=True)


def _write_runtime_evidence(
    root: Path,
    files_dir: Path,
    terminal: Path,
    compile_log: Path,
    latency_status: str,
    permission: str = "false",
) -> None:
    reports = root / "outputs" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    terminal.parent.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)
    terminal.write_text("", encoding="utf-8")
    compile_log.write_text("Result: 0 errors, 0 warnings, 651 ms elapsed", encoding="utf-8")
    _write_csv(files_dir / "startup_log.csv", [{"timestamp_utc": "2026-05-28T00:00:00Z"}])
    _write_csv(files_dir / "decision_log.csv", [{"bar_time": "2026.05.28 13:30:00"}])
    (reports / "PHASE1_EXTERNAL_HEALTH.json").write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    (reports / "PHASE1_STATUS_SUMMARY.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "latest_row": {
                        "bar_time": "2026.05.28 13:30:00",
                        "dry_run": "true",
                        "trade_permission": permission,
                        "server_time_status": "CLOCK_OK",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (reports / "PHASE2_READINESS_REPORT.md").write_text(
        "# Phase 2 Readiness Report\n\nOverall status: PENDING\n",
        encoding="utf-8",
    )
    (reports / "PHASE2_VPS_LATENCY_REPORT.md").write_text(
        f"# Phase 2 VPS Latency Report\n\nOverall status: {latency_status}\n",
        encoding="utf-8",
    )


def _write_verified_manual_evidence(ntp: Path, backup: Path, recovery: Path) -> None:
    ntp.parent.mkdir(parents=True, exist_ok=True)
    ntp.write_text(
        "\n".join(
            [
                "evidence_status: VERIFIED",
                "owner_verified: true",
                "time_sync_enabled: true",
                "provider: Test VPS",
                "region: Test Region",
            ]
        ),
        encoding="utf-8",
    )
    backup.write_text(
        "\n".join(
            [
                "evidence_status: VERIFIED",
                "owner_verified: true",
                "backup_configured: true",
                "restore_owner_confirmed: true",
                "backup_method: snapshot",
            ]
        ),
        encoding="utf-8",
    )
    recovery.write_text(
        "\n".join(
            [
                "evidence_status: VERIFIED",
                "owner_verified: true",
                "recovery_login_verified: true",
                "password: REDACTED",
                "secret: REDACTED",
            ]
        ),
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
