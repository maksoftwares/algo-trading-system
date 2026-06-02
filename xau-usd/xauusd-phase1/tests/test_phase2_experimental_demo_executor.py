from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_demo_executor_is_demo_scoped_and_explicitly_armed():
    text = (ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoExecutor.mq5").read_text(encoding="utf-8")

    assert "input bool InpDryRunOnly = false;" in text
    assert "input bool InpBrokerActionAllowed = false;" in text
    assert "InpDryRunOnly || !InpBrokerActionAllowed" in text
    assert "InpExpectedServerMarker" in text
    assert "InpAllowedAccountLoginsCsv" in text
    assert "AccountLoginWhitelisted()" in text
    assert "InpExperimentalAuthorizationToken" in text
    assert "ExperimentalAuthorizationTokenValid()" in text
    assert "InpAuthorizedCandidatesCsv" in text
    assert "CandidateExecutionAuthorized()" in text
    assert "InpMaxAccountOrdersPerDay" in text
    assert "CountOpenExposureForAccount()" in text
    assert "InpKillSwitchFileName" in text
    assert "KillSwitchActive()" in text
    assert 'ContainsText(server, "live")' in text
    assert 'ContainsText(server, "real")' in text
    assert "InpFixedLot = 0.01" in text
    assert "InpMaxOpenPositionsPerInstance = 1" in text
    assert "InpMaxOrdersPerDay = 12" in text
    assert "MARKET_PROXY" in text
    assert "estimated_cost_R" in text
    assert "spread_at_order_points" in text
    assert "OrderSend(request, result)" in text
    assert "EnsureOrderLogHeader" in text
    assert "experimental_demo_executor_order_log" in text


def test_demo_executor_attach_script_arms_only_demo_profile():
    module = _load_module()
    row = module.AttachmentRow(
        candidate="breakout_retest",
        status="ACCEPTED",
        symbol="XAUUSD",
        qualification_source="test",
        observer_supported=True,
    )

    chart = module._render_chart(row, 1)

    assert "path=Experts\\Phase2ExperimentalDemoExecutor.ex5" in chart
    assert "InpDryRunOnly=false" in chart
    assert "InpBrokerActionAllowed=true" in chart
    assert "InpExpectedServerMarker=Demo" in chart
    assert "InpAllowedAccountLoginsCsv=" in chart
    assert "InpExperimentalAuthorizationToken=" in chart
    assert "InpRequiredExperimentalAuthorizationToken=EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY" in chart
    assert "InpAuthorizedCandidatesCsv=breakout_retest" in chart
    assert "InpFixedLot=0.01" in chart
    assert "InpMaxAccountOrdersPerDay=24" in chart
    assert "InpMaxOpenPositionsPerInstance=1" in chart
    assert "InpMaxAccountOpenPositions=3" in chart
    assert "InpKillSwitchFileName=experimental_demo_kill_switch.txt" in chart
    assert "InpOrderLogFileName=experimental_demo_executor_order_log_breakout_retest_xauusd.csv" in chart


def test_phase1_safety_audit_allowlist_names_only_executor():
    audit = (ROOT / "scripts" / "audit_phase1_safety.py").read_text(encoding="utf-8")

    assert "ALLOWED_EXPERIMENTAL_DEMO_EXECUTION_FILES" in audit
    assert '"Phase2ExperimentalDemoExecutor.mq5"' in audit
    assert '"Phase1DryRunShell.mq5"' not in audit


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "attach_phase2_experimental_demo_executors.py"
    spec = importlib.util.spec_from_file_location("attach_phase2_experimental_demo_executors", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["attach_phase2_experimental_demo_executors"] = module
    spec.loader.exec_module(module)
    return module
