from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_weakness_executor_has_distinct_demo_order_identity():
    text = (ROOT / "mt5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5").read_text(encoding="utf-8")

    assert 'input string InpRunId = "P2WEAKNESS_BR_V1";' in text
    assert 'return "P2WEAKNESS_BR_V1";' in text
    assert "input int InpMagicNumber = 930101;" in text
    assert "InpMagicNumber < 930000" in text
    assert "InpMagicNumber >= 931000" in text
    assert "request.magic = InpMagicNumber;" in text
    assert "request.comment = InstanceComment();" in text
    assert "p2weakness_br_v1_order_log_xauusd.csv" in text


def test_weakness_executor_is_xauusd_breakout_only_and_demo_scoped():
    text = (ROOT / "mt5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5").read_text(encoding="utf-8")

    assert 'input string InpTargetSymbol = "XAUUSD";' in text
    assert 'return "breakout_retest";' in text
    assert "g_breakout_observer.Configure(false);" in text
    assert '_Symbol != InpTargetSymbol || _Symbol != "XAUUSD"' in text
    assert 'ContainsText(server, "live")' in text
    assert 'ContainsText(server, "real")' in text
    assert 'input string InpExpectedServerMarker = "Demo";' in text
    assert 'input string InpAllowedAccountLoginsCsv = "1025742";' in text
    assert "AccountLoginWhitelisted()" in text
    assert "ExperimentalAuthorizationTokenValid()" in text
    assert "OrderSend(request, result)" in text


def test_weakness_executor_suppresses_same_family_duplicates():
    text = (ROOT / "mt5" / "Experts" / "Phase2WeaknessBreakoutRetestExecutor.mq5").read_text(encoding="utf-8")

    assert "input int InpDuplicateLockBars = 12;" in text
    assert "IsDemoFamilyMagic" in text
    assert "magic >= 920000 && magic < 921000" in text
    assert "magic >= 930000 && magic < 931000" in text
    assert "SameDirectionFamilyExposureExists" in text
    assert "DuplicateFamilyLockActive" in text
    assert "SetDuplicateFamilyLock(observation)" in text
    assert "duplicate_same_direction_family_exposure_exists" in text
    assert "duplicate_family_lock_active" in text


def test_weakness_deploy_script_does_not_touch_profiles_or_restart_terminal():
    text = (ROOT / "scripts" / "deploy_phase2_weakness_breakout_executor.py").read_text(encoding="utf-8")

    assert "Phase2WeaknessBreakoutRetestExecutor" in text
    assert '"terminal_profile_touched": False' in text
    assert '"terminal_closed_or_restarted": False' in text
    assert "_deploy_sources" in text
    assert "_compile_ea" in text
    assert "_replace_default_profile" not in text
    assert "_close_terminal" not in text


def test_weakness_launch_script_uses_startup_config_without_profile_replacement():
    text = (ROOT / "scripts" / "launch_phase2_weakness_breakout_executor.py").read_text(encoding="utf-8")
    config = (ROOT / "mt5" / "Config" / "p2weakness_br_v1_startup.ini").read_text(encoding="utf-8")

    assert "/config:" in text
    assert '"profile_touched": False' in text
    assert '"terminal_closed_or_restarted": False' in text
    assert "_replace_default_profile" not in text
    assert "_close_terminal" not in text
    assert "Expert=Phase2WeaknessBreakoutRetestExecutor" in config
    assert "ExpertParameters=Phase2WeaknessBreakoutRetestExecutor.demo_xauusd.set" in config
    assert "Symbol=XAUUSD" in config
    assert "Period=M5" in config


def test_weakness_portable_setup_keeps_current_terminal_untouched():
    text = (ROOT / "scripts" / "setup_phase2_weakness_portable_demo_terminal.py").read_text(encoding="utf-8")

    assert "C:/MT5PortableP2WeaknessDemo" in text
    assert '"old_terminal_profile_touched": False' in text
    assert '"old_terminal_closed_or_restarted": False' in text
    assert "/portable" in text
    assert "deploy_phase2_weakness_breakout_executor" in text
    assert "_replace_default_profile" not in text
    assert "_close_terminal" not in text


def test_broker_action_boundary_audit_accepts_weakness_executor(tmp_path):
    module = _load_boundary_audit_module()
    result = module.audit_broker_action_file_boundary(
        ROOT.parents[1],
        output_json=tmp_path / "broker_action_boundary.json",
    )

    report = (tmp_path / "broker_action_boundary.json").read_text(encoding="utf-8")
    assert "Phase2WeaknessBreakoutRetestExecutor.mq5" in report
    rows = [
        row
        for row in __import__("json").loads(report)["files"]
        if row["path"].endswith("Phase2WeaknessBreakoutRetestExecutor.mq5")
    ]
    assert rows == [
        {
            "path": "xau-usd\\xauusd-phase1\\mt5\\Experts\\Phase2WeaknessBreakoutRetestExecutor.mq5",
            "classification": "approved_experimental_quarantined",
            "broker_action_terms": ["OrderSend"],
            "status": "PASS",
            "evidence": "guarded experimental broker-action file",
        }
    ]


def test_broker_action_boundary_audit_accepts_wr50_order_executor(tmp_path):
    module = _load_boundary_audit_module()
    module.audit_broker_action_file_boundary(
        ROOT.parents[1],
        output_json=tmp_path / "broker_action_boundary.json",
    )

    report = (tmp_path / "broker_action_boundary.json").read_text(encoding="utf-8")
    rows = [
        row
        for row in __import__("json").loads(report)["files"]
        if row["path"].endswith("WR50_OrderExecutor.mqh")
    ]
    assert rows == [
        {
            "path": "xau-usd\\xauusd-wr50-experimental\\mt5\\Include\\WR50_OrderExecutor.mqh",
            "classification": "approved_experimental_quarantined",
            "broker_action_terms": ["OrderSend"],
            "status": "PASS",
            "evidence": "guarded experimental broker-action file",
        }
    ]


def _load_boundary_audit_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "audit_broker_action_file_boundary.py"
    spec = importlib.util.spec_from_file_location("audit_broker_action_file_boundary", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_broker_action_file_boundary"] = module
    spec.loader.exec_module(module)
    return module
