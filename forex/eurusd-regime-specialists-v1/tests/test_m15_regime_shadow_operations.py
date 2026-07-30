from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "scripts" / "audit_m15_regime_shadow.py"
RUNNER = ROOT / "scripts" / "run_m15_regime_shadow_health.ps1"
INSTALLER = ROOT / "scripts" / "install_m15_regime_shadow_health_task.ps1"
LIVE_AUDIT = (
    ROOT
    / "outputs"
    / "m15_regime_portfolio_live_shadow_prestart"
    / "LIVE_SHADOW_AUDIT.json"
)


def _load_auditor():
    spec = importlib.util.spec_from_file_location("m15_shadow_audit", AUDITOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_prestart_audit_is_no_order_and_headerless_compatible(
    tmp_path: Path,
) -> None:
    module = _load_auditor()
    row = [
        "2026.07.30 06:55:36",
        "2026.07.30 06:55:19",
        "EURUSD_M15_REGIME_FORWARD_V1",
        "INIT_OK",
        "shadow_demo",
        "1033669",
        "Capital.ComMena-Demo",
        "EURUSD",
        "26073060",
        "UNAVAILABLE",
        "NONE",
        "0.00",
        "0.00000",
        "0.00000",
        "0.00000",
        "true",
        "false",
        "true",
    ]
    latch = row.copy()
    latch[3] = "STARTUP_LATCH"
    path = tmp_path / "audit.csv"
    path.write_text(
        ",".join(row) + "\n" + ",".join(latch) + "\n",
        encoding="utf-16",
    )
    result = module.audit(
        path, datetime(2026, 7, 30, 7, 0, tzinfo=UTC)
    )
    assert result["status"] == "PASS_RUNNING_PRESTART"
    assert result["header_present"] is False
    assert result["signals"] == 0
    assert all(result["checks"].values())


def test_pre_floor_signal_is_rejected(tmp_path: Path) -> None:
    module = _load_auditor()
    common = [
        "2026.07.30 06:55:36",
        "2026.07.30 06:55:19",
        "EURUSD_M15_REGIME_FORWARD_V1",
        "INIT_OK",
        "shadow_demo",
        "1033669",
        "Capital.ComMena-Demo",
        "EURUSD",
        "26073060",
        "UNAVAILABLE",
        "NONE",
        "0.00",
        "0.00000",
        "0.00000",
        "0.00000",
        "true",
        "false",
        "true",
    ]
    rows = [common.copy(), common.copy(), common.copy(), common.copy()]
    rows[1][3] = "STARTUP_LATCH"
    rows[2][3] = "SIGNAL"
    rows[2][9] = "CHOP"
    rows[3][3] = "ORDER_BLOCKED"
    rows[3][4] = "shadow_or_orders_disabled"
    rows[3][9] = "CHOP"
    path = tmp_path / "audit.csv"
    path.write_text(
        "".join(",".join(row) + "\n" for row in rows),
        encoding="utf-16",
    )
    result = module.audit(
        path, datetime(2026, 7, 30, 7, 0, tzinfo=UTC)
    )
    assert result["status"] == "FAIL"
    assert result["checks"]["no_pre_floor_signal"] is False


def test_health_runner_and_task_are_fail_closed() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    for token in (
        "Assert-ExactFile -Expected $PackageExpert -Actual $TerminalExpert",
        "AllowLiveTrading=0",
        "AllowDllImport=0",
        "InpShadowMode=true",
        "InpEnableDemoOrders=false",
        "InpEmergencyStop=true",
        "InpTesterOrdersEnabled=false",
        "InpDemoArmToken=DISARMED",
        "-WindowStyle Hidden",
    ):
        assert token in runner
    installer = INSTALLER.read_text(encoding="utf-8")
    for token in (
        "Codex-EURUSD-M15-Regime-Shadow-Health",
        "New-TimeSpan -Minutes 5",
        "-LogonType Interactive",
        "-RunLevel Limited",
    ):
        assert token in installer


def test_captured_live_prestart_deployment_passed_every_check() -> None:
    result = json.loads(LIVE_AUDIT.read_text(encoding="utf-8"))
    assert result["status"] == "PASS_RUNNING_PRESTART"
    assert result["before_forward_floor"] is True
    assert result["signals"] == 0
    assert result["blocked_signals"] == 0
    assert all(result["checks"].values())
