from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "EurUsdV4AsiaLondonCompressionShort.mq5"
SHADOW = ROOT / "mt5" / "Presets" / "EURUSD_V4_SHADOW_DEMO.set"
VERDICT = ROOT / "outputs" / "capital_mt5_real_tick" / "VERDICT.json"


def test_shadow_preset_cannot_order():
    text = SHADOW.read_text(encoding="utf-8")
    assert "ShadowMode=true" in text
    assert "EnableDemoOrders=false" in text
    assert "OwnedRegimeMode=1" in text
    assert "TargetRMultiple=1.25" in text


def test_ea_hard_blocks_non_demo_accounts():
    text = EA.read_text(encoding="utf-8")
    assert "ACCOUNT_TRADE_MODE_DEMO" in text
    assert "if(ShadowMode || !EnableDemoOrders) return;" in text
    assert "OwnedRegimeMode == 0 ? compression : chop" in text


def test_real_tick_verdict_is_demo_only():
    text = VERDICT.read_text(encoding="utf-8")
    assert '"status": "CONTROLLED_DEMO_REHEARSAL_READY"' in text
    assert '"production_ready": false' in text
    assert '"live_ready": false' in text
