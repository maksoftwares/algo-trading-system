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
    assert any(check.name == "selected_vps_consistency" and check.status == "PENDING" for check in output.checks)
    assert any(check.name == "ntp_time_sync_evidence" and check.status == "PENDING" for check in output.checks)
    assert any(check.name == "periodic_scheduler_evidence" and check.status == "PENDING" for check in output.checks)
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
    scheduler = root / "outputs" / "reports" / "vps_periodic_task.txt"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS")
    _write_vps_selection_matrix(root)
    _write_verified_manual_evidence(ntp, backup, recovery, scheduler)

    output = module.generate_phase2_vps_first_day_verification(
        root=root,
        terminal_path=terminal,
        data_path=tmp_path / "mt5",
        files_dir=files_dir,
        compile_log=compile_log,
        ntp_evidence_path=ntp,
        backup_evidence_path=backup,
        recovery_evidence_path=recovery,
        scheduler_evidence_path=scheduler,
    )

    payload = json.loads(output.json_path.read_text(encoding="utf-8"))
    assert output.status == "PASS"
    assert payload["phase2_paper_mode_authorized"] is False
    assert payload["demo_trading_authorized"] is False
    assert all(check.status == "PASS" for check in output.checks)


def test_vps_first_day_verification_rejects_selected_vps_mismatch(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    files_dir = tmp_path / "mt5" / "MQL5" / "Files"
    terminal = tmp_path / "mt5" / "terminal64.exe"
    compile_log = tmp_path / "mt5" / "compile.log"
    ntp = root / "outputs" / "reports" / "vps_ntp_sync.txt"
    backup = root / "outputs" / "reports" / "vps_backup_config.txt"
    recovery = root / "outputs" / "reports" / "vps_rdp_recovery.txt"
    scheduler = root / "outputs" / "reports" / "vps_periodic_task.txt"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS")
    _write_vps_selection_matrix(root, provider="FXVM", region="Dubai")
    _write_verified_manual_evidence(ntp, backup, recovery, scheduler, provider="ForexVPS.net", region="London")

    output = module.generate_phase2_vps_first_day_verification(
        root=root,
        terminal_path=terminal,
        data_path=tmp_path / "mt5",
        files_dir=files_dir,
        compile_log=compile_log,
        ntp_evidence_path=ntp,
        backup_evidence_path=backup,
        recovery_evidence_path=recovery,
        scheduler_evidence_path=scheduler,
    )

    assert output.status == "FAIL"
    assert any(
        check.name == "selected_vps_consistency"
        and check.status == "FAIL"
        and "Selected VPS evidence mismatch" in check.evidence
        for check in output.checks
    )


def test_vps_first_day_verification_rejects_latency_pass_without_local_baseline(tmp_path: Path):
    module = _load_module()
    repo = tmp_path / "repo"
    root = repo / "xau-usd" / "xauusd-phase1"
    files_dir = tmp_path / "mt5" / "MQL5" / "Files"
    terminal = tmp_path / "mt5" / "terminal64.exe"
    compile_log = tmp_path / "mt5" / "compile.log"
    ntp = root / "outputs" / "reports" / "vps_ntp_sync.txt"
    backup = root / "outputs" / "reports" / "vps_backup_config.txt"
    recovery = root / "outputs" / "reports" / "vps_rdp_recovery.txt"
    scheduler = root / "outputs" / "reports" / "vps_periodic_task.txt"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS")
    _write_vps_selection_matrix(root)
    _write_verified_manual_evidence(ntp, backup, recovery, scheduler)
    (root / "outputs" / "reports" / "PHASE2_VPS_LATENCY_REPORT.md").write_text(
        "# Phase 2 VPS Latency Report\n\nOverall status: PASS\n",
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
        scheduler_evidence_path=scheduler,
    )

    assert output.status == "FAIL"
    assert any(
        check.name == "vps_latency_report"
        and check.status == "FAIL"
        and "local_baseline_comparison PASS" in check.evidence
        for check in output.checks
    )


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
    scheduler = root / "outputs" / "reports" / "vps_periodic_task.txt"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS")
    _write_vps_selection_matrix(root)
    for path in (ntp, backup, recovery, scheduler):
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
        scheduler_evidence_path=scheduler,
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
    scheduler = root / "outputs" / "reports" / "vps_periodic_task.txt"
    _seed_git_repo(repo)
    _write_runtime_evidence(root, files_dir, terminal, compile_log, latency_status="PASS")
    _write_vps_selection_matrix(root)
    _write_verified_manual_evidence(ntp, backup, recovery, scheduler)
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
        scheduler_evidence_path=scheduler,
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
        _latency_report_text(latency_status),
        encoding="utf-8",
    )


def _write_vps_selection_matrix(root: Path, provider: str = "FXVM", region: str = "Dubai") -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "PHASE2_VPS_SELECTION_MATRIX.md").write_text(
        "\n".join(
            [
                "# Phase 2 VPS Selection Matrix",
                "",
                "Overall status: PASS",
                "",
                "## Decision Record",
                "",
                "| Field | Value |",
                "| --- | --- |",
                f"| Selected provider | {provider} |",
                f"| Selected region | {region} |",
                "| Selected plan | Advanced VPS |",
                "| Monthly cost | 50 USD |",
                "| Backup method | weekly snapshot |",
                "| Monitoring endpoint or scheduler | Windows Task Scheduler |",
                "| Recovery access owner | maksoftwares |",
                "| Latency evidence path | outputs/reports/PHASE2_VPS_LATENCY_REPORT.md |",
                "| Decision date | 2026-05-29 |",
                "| Owner acceptance | Phase 2 paper-mode only accepted |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_verified_manual_evidence(
    ntp: Path,
    backup: Path,
    recovery: Path,
    scheduler: Path,
    provider: str = "FXVM",
    region: str = "Dubai",
) -> None:
    ntp.parent.mkdir(parents=True, exist_ok=True)
    ntp.write_text(
        "\n".join(
            [
                "evidence_status: VERIFIED",
                "owner_verified: true",
                "time_sync_enabled: true",
                f"provider: {provider}",
                f"region: {region}",
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
                f"provider: {provider}",
                f"region: {region}",
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
                f"provider: {provider}",
                f"region: {region}",
                "password: REDACTED",
                "secret: REDACTED",
            ]
        ),
        encoding="utf-8",
    )
    scheduler.write_text(
        "\n".join(
            [
                "evidence_status: VERIFIED",
                "owner_verified: true",
                "task_registered: true",
                "last_run_verified: true",
                "task_name: phase2-periodic-readiness-check",
                f"provider: {provider}",
                f"region: {region}",
                "last_run_result: PASS",
            ]
        ),
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _latency_report_text(status: str) -> str:
    if status != "PASS":
        return f"# Phase 2 VPS Latency Report\n\nOverall status: {status}\n"
    return "\n".join(
        [
            "# Phase 2 VPS Latency Report",
            "",
            "Overall status: PASS",
            "",
            "## Candidate",
            "",
            "| Provider | Region | Endpoint | Average Ping | Packet Loss | Local Median | Improvement |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            "| FXVM | Dubai | mt5.example.test | 36.00 ms | 0.00% | 50.00 ms | 28.0% |",
            "",
            "## Checks",
            "",
            "| Check | Status | Evidence |",
            "| --- | --- | --- |",
            "| local_baseline_comparison | PASS | VPS average latency improves on local median. |",
            "",
            "## Evidence Paths",
            "",
            "- Local MT5 baseline: `outputs/reports/PHASE2_LOCAL_MT5_NETWORK_BASELINE.md`",
            "",
        ]
    )
