from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_attachment_plan_includes_all_approved_and_provisional_symbols():
    module = _load_module()

    plan = module.build_attachment_plan(ROOT)
    pairs = {(row.candidate, row.symbol) for row in plan}

    assert ("breakout_retest", "XAUUSD") in pairs
    assert ("breakout_retest", "EURUSD") in pairs
    assert ("breakout_retest", "USDJPY") in pairs
    assert ("swing_breakout_retest_v0", "EURUSD") in pairs
    assert ("symbol_normalized_round_retest_v0", "USDJPY") in pairs
    assert ("round_number_retest_v0", "XAUUSD") in pairs
    assert ("round_number_retest_v0", "USDJPY") in pairs
    assert ("round_number_retest_v0", "EURUSD") not in pairs
    assert ("session_extreme_retest_v0", "EURUSD") in pairs


def test_attachment_chart_is_dry_run_and_demo_scoped():
    module = _load_module()
    row = module.AttachmentRow(
        candidate="breakout_retest",
        status="ACCEPTED",
        symbol="XAUUSD",
        qualification_source="test",
        observer_supported=True,
    )

    chart = module._render_chart(row, 1)

    assert "path=Experts\\Phase2ExperimentalDemoObserver.ex5" in chart
    assert "InpDryRunOnly=true" in chart
    assert "InpExpectedServerMarker=Demo" in chart
    assert "InpCandidate=breakout_retest" in chart
    assert "InpTargetSymbol=XAUUSD" in chart


def test_experimental_demo_observer_contains_no_broker_action_terms():
    script = (ROOT / "scripts" / "attach_phase2_experimental_demo_observers.py").read_text(encoding="utf-8")
    ea = (ROOT / "mt5" / "Experts" / "Phase2ExperimentalDemoObserver.mq5").read_text(encoding="utf-8")
    combined = script + "\n" + ea

    assert "OrderSend" not in combined
    assert "OrderSendAsync" not in combined
    assert "CTrade" not in combined
    assert "trade.Buy" not in combined
    assert "trade.Sell" not in combined
    assert "PositionOpen" not in combined


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "attach_phase2_experimental_demo_observers.py"
    spec = importlib.util.spec_from_file_location("attach_phase2_experimental_demo_observers", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["attach_phase2_experimental_demo_observers"] = module
    spec.loader.exec_module(module)
    return module
