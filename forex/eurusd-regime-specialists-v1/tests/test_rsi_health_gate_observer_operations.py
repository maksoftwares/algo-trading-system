from __future__ import annotations

import importlib.util
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "scripts" / "audit_rsi_health_gate_observer.py"
RUNNER = ROOT / "scripts" / "run_rsi_health_gate_observer_health.ps1"
INSTALLER = (
    ROOT / "scripts" / "install_rsi_health_gate_observer_health_task.ps1"
)


def _load_auditor():
    spec = importlib.util.spec_from_file_location("rsi_observer_audit", AUDITOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(event: str, signal_time: str = "") -> list[str]:
    return [
        "2026.07.30 20:00:00",
        "2026.07.30 16:00:00",
        "EURUSD_RSI_HEALTH_GATE_FORWARD_V1",
        event,
        "fixture",
        "1033669",
        "Capital.ComMena-Demo",
        "EURUSD",
        "26073091",
        signal_time,
        "1.10000",
        "1.09900",
        "1.10080",
        "0.00000",
        "0.0000",
        "0.0000",
        "0",
        "0.00000000",
        "false",
        "false",
    ]


def test_prestart_zero_order_ledger_passes(tmp_path: Path) -> None:
    module = _load_auditor()
    path = tmp_path / "audit.csv"
    rows = [
        _row("STATE_INITIALIZED"),
        _row("INIT_OK"),
        _row("STARTUP_LATCH"),
    ]
    import csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(module.EXPECTED_HEADER)
        writer.writerows(rows)
    result = module.audit(
        path,
        datetime(2026, 8, 1, tzinfo=UTC),
        datetime(2026, 7, 30, 16, 0, tzinfo=UTC),
    )
    assert result["status"] == "PASS_RUNNING_PRESTART"
    assert result["demo_order_authorized"] is False
    assert all(result["checks"].values())


def test_pre_floor_virtual_open_fails(tmp_path: Path) -> None:
    module = _load_auditor()
    path = tmp_path / "audit.csv"
    rows = [
        _row("STATE_INITIALIZED"),
        _row("INIT_OK"),
        _row("STARTUP_LATCH"),
        _row("VIRTUAL_OPEN", "2026.07.31 23:45:00"),
    ]
    import csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(module.EXPECTED_HEADER)
        writer.writerows(rows)
    result = module.audit(
        path,
        datetime(2026, 8, 1, tzinfo=UTC),
        datetime(2026, 8, 1, 0, 1, tzinfo=UTC),
    )
    assert result["status"] == "FAIL"
    assert result["checks"]["no_pre_floor_virtual_open"] is False


def test_health_runner_and_task_are_fail_closed() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    for token in (
        "Assert-ExactFile -Expected $PackageExpert -Actual $TerminalExpert",
        "AllowLiveTrading=0",
        "AllowDllImport=0",
        "InpRequireDemoAccount=true",
        "InpResetPersistentState=false",
        "demo_order_authorized",
        "OBSERVER_RESTART_RETRY stale_mutex_recovery",
        "Start-Sleep -Seconds 7",
        "-WindowStyle Hidden",
    ):
        assert token in runner
    installer = INSTALLER.read_text(encoding="utf-8")
    for token in (
        "Codex-EURUSD-RSI-Health-Gate-Observer",
        "New-TimeSpan -Minutes 5",
        "-LogonType Interactive",
        "-RunLevel Limited",
    ):
        assert token in installer
