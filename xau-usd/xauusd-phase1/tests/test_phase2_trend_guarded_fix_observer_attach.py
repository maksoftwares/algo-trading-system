from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_trend_guarded_attach_plan_is_multisymbol_and_v2():
    module = _load_module()

    rows = module._build_attachment_plan()
    assert len(rows) == 14
    assert {row.symbol for row in rows} == {"XAUUSD", "EURUSD", "GBPUSD"}
    assert sum(1 for row in rows if row.symbol == "XAUUSD") == 5
    assert sum(1 for row in rows if row.symbol == "EURUSD") == 5
    assert sum(1 for row in rows if row.symbol == "GBPUSD") == 4
    assert module.AttachmentRow("session_extreme_retest_v0_repair_v1", "EURUSD") in rows
    assert module.DEFAULT_PORTABLE_ROOT.as_posix().endswith("MT5PortableTrendGuardedFixObservers")
    assert module.POLICY_VERSION == "trend_guarded_fix_policy_20260612_v2"


def test_trend_guarded_attach_chart_uses_observer_ex5_and_safe_preset_inputs():
    module = _load_module()

    chart = module._render_chart(ROOT, module.AttachmentRow("round_number_retest_v0", "XAUUSD"), 1)

    assert "path=Experts\\Phase2TrendGuardedFixObserver.ex5" in chart
    assert "InpDryRunOnly=true" in chart
    assert "InpTargetSymbol=XAUUSD" in chart
    assert "InpCandidate=round_number_retest_v0" in chart
    assert "InpExpectedServerMarker=Demo" in chart
    assert "InpCandidateStatus=TREND_GUARDED_FIX_OBSERVER_V2" in chart
    assert "InpShadowPolicyVersion=trend_guarded_fix_policy_20260612_v2" in chart
    assert "InpDubaiUtcOffsetMinutes=240" in chart
    assert "OrderSend" not in chart
    assert "CTrade" not in chart
    assert "BrokerActionAllowed" not in chart


def test_trend_guarded_attach_chart_renders_fx_symbol_inputs():
    module = _load_module()

    chart = module._render_chart(ROOT, module.AttachmentRow("session_extreme_retest_v0_repair_v1", "EURUSD"), 1)

    assert "symbol=EURUSD" in chart
    assert "digits=5" in chart
    assert "tick_size=0.00001" in chart
    assert "InpTargetSymbol=EURUSD" in chart
    assert "InpQualifiedSymbolsCsv=EURUSD" in chart
    assert "InpCandidate=session_extreme_retest_v0_repair_v1" in chart
    assert "trend_guarded_fix_observer_v2_signal_log_session_extreme_retest_v0_repair_v1_eurusd.csv" in chart
    assert "OrderSend" not in chart


def test_trend_guarded_attach_script_refuses_standard_demo_terminal():
    module = _load_module()

    try:
        module._guard_not_standard_demo_terminal(
            module.STANDARD_DEMO_TERMINAL_DATA_DIR,
            module.DEFAULT_PORTABLE_ROOT / "terminal64.exe",
        )
    except RuntimeError as exc:
        assert "standard demo trading terminal" in str(exc)
    else:
        raise AssertionError("standard demo terminal data dir was not rejected")


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "attach_phase2_trend_guarded_fix_observers.py"
    spec = importlib.util.spec_from_file_location("attach_phase2_trend_guarded_fix_observers", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["attach_phase2_trend_guarded_fix_observers"] = module
    spec.loader.exec_module(module)
    return module
