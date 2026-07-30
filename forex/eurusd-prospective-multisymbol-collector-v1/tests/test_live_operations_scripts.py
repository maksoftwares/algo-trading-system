from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_live_forward_cycle.ps1"
INSTALLER = ROOT / "scripts" / "install_live_operations_tasks.ps1"


def test_operations_runner_preserves_read_only_and_append_only_guards() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    required = (
        'if ($ConfigText -notmatch "AllowLiveTrading=0")',
        'if ($ConfigText -notmatch "AllowDllImport=0")',
        "Assert-ExactFile -Expected $PackageExpert -Actual $TerminalExpert",
        "--enforce-append-only",
        "demo_order_authorized",
        "Save-ImmutableDailySnapshot",
        "Assert-SnapshotIntegrity",
        "Immutable snapshot hash mismatch",
        "SNAPSHOT_REVERIFIED",
        "Get-FileHash -Algorithm SHA256",
        "-WindowStyle Hidden",
    )
    for token in required:
        assert token in text
    forbidden = ("OrderSend", "CTrade", ".Buy(", ".Sell(")
    for token in forbidden:
        assert token not in text


def test_task_installer_uses_frequent_health_and_post_outcome_daily_clock() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    required = (
        "Codex-EURUSD-Prospective-Health",
        "Codex-EURUSD-Forward-Learner",
        "New-TimeSpan -Minutes 5",
        'New-ScheduledTaskTrigger -Daily -At "18:10"',
        "14:10 UTC / 18:10 Dubai",
        "-LogonType Interactive",
        "-RunLevel Limited",
    )
    for token in required:
        assert token in text
