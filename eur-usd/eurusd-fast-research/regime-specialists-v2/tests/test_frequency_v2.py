import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frequency_v2_evidence_passes_frozen_demo_gates():
    verdict = json.loads(
        (ROOT / "outputs" / "frequency_v2_mt5" / "VERDICT.json").read_text()
    )
    assert verdict["all_gates_pass"] is True
    assert verdict["shadow_demo_ready"] is True
    assert verdict["live_ready"] is False
    assert verdict["metrics"]["trades_per_active_day"] >= 1.0
    assert verdict["metrics"]["profit_factor"] >= 1.30
    assert verdict["metrics"]["top_5pct_removed_profit_factor"] >= 1.0
    assert verdict["metrics"]["maximum_concurrent_positions"] <= 2


def test_frequency_v2_presets_fail_closed():
    shadow = (
        ROOT / "mt5" / "Presets" / "EURUSD_FREQUENCY_V2_M15_SHADOW_DEMO.set"
    ).read_text()
    ordering = (
        ROOT
        / "mt5"
        / "Presets"
        / "EURUSD_FREQUENCY_V2_M15_DEMO_ORDERING_OWNER_AUTHORIZED.template.set"
    ).read_text()
    assert "InpShadowMode=true" in shadow
    assert "InpEnableDemoOrders=false" in shadow
    assert "InpAllowedAccountLogin=0" in shadow
    assert "InpShadowMode=false" in ordering
    assert "InpEnableDemoOrders=true" in ordering
    assert "REPLACE_WITH_CAPITAL_DEMO_LOGIN" in ordering


def test_frequency_v2_ea_has_demo_and_regime_guards():
    source = (
        ROOT.parent.parent.parent
        / "forex-research"
        / "mt5"
        / "Experts"
        / "ForexMeanReversionScout.mq5"
    ).read_text()
    assert "ACCOUNT_TRADE_MODE_DEMO" in source
    assert "InpShadowMode" in source
    assert "InpEnableDemoOrders" in source
    assert "H4TrendRiskOverlayActive" in source
    assert "InpH4UnsafeAtrPercentile" in source
