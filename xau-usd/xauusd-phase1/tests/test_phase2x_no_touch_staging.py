from __future__ import annotations

from phase2x_test_helpers import load_script, write_json, write_presets


def test_phase2x_no_touch_staging_passes_safe_staged_inputs(tmp_path):
    root = tmp_path / "phase1"
    write_presets(root)
    _write_startup_config(root)
    _write_owner_preset(root)
    write_json(
        root / "outputs" / "reports" / "PHASE2_WEAKNESS_BR_V1_PORTABLE_DEMO_TERMINAL.json",
        {
            "status": "PORTABLE_PREPARED_AND_DEPLOYED_NO_LAUNCH",
            "launch_started": False,
            "old_terminal_profile_touched": False,
            "old_terminal_closed_or_restarted": False,
        },
    )
    write_json(root / "outputs" / "reports" / "PHASE2X_DEMO_PREFLIGHT_REPORT.json", {"status": "PENDING"})
    module = load_script("phase2x_no_touch_staging_report")

    payload = module.generate_phase2x_no_touch_staging_report(root)

    assert payload["status"] == "PASS"
    assert payload["phase2x_demo_execution_authorized"] is False


def test_phase2x_no_touch_staging_fails_if_launch_already_started(tmp_path):
    root = tmp_path / "phase1"
    write_presets(root)
    _write_startup_config(root)
    _write_owner_preset(root)
    write_json(
        root / "outputs" / "reports" / "PHASE2_WEAKNESS_BR_V1_PORTABLE_DEMO_TERMINAL.json",
        {
            "status": "PORTABLE_LAUNCHED_WITH_LOG",
            "launch_started": True,
            "old_terminal_profile_touched": False,
            "old_terminal_closed_or_restarted": False,
        },
    )
    write_json(root / "outputs" / "reports" / "PHASE2X_DEMO_PREFLIGHT_REPORT.json", {"status": "PENDING"})
    module = load_script("phase2x_no_touch_staging_report")

    payload = module.generate_phase2x_no_touch_staging_report(root)

    assert payload["status"] == "FAIL"


def _write_startup_config(root):
    path = root / "mt5" / "Config" / "p2weakness_br_v1_startup.ini"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "[Experts]",
                "Enabled=1",
                "AllowLiveTrading=0",
                "AllowDllImport=0",
                "",
                "[StartUp]",
                "Expert=Phase2WeaknessBreakoutRetestExecutor",
                "ExpertParameters=Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set",
                "Symbol=XAUUSD",
                "Period=M5",
                "ShutdownTerminal=0",
            ]
        ),
        encoding="utf-8",
    )


def _write_owner_preset(root):
    path = root / "local" / "Phase2WeaknessBreakoutRetestExecutor.owner_authorized_demo_xauusd.local.set"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "InpRunId=P2WEAKNESS_BR_V1",
                "InpDryRunOnly=false",
                "InpBrokerActionAllowed=true",
                "InpTargetSymbol=XAUUSD",
                "InpMagicNumber=931000",
                "InpFixedLot=0.01",
                "InpMaxFamilyOpenPositions=1",
                "InpMaxEstimatedCostR=0.15",
                "InpMaxMeasuredSpreadPoints=75.0",
            ]
        ),
        encoding="utf-8",
    )
