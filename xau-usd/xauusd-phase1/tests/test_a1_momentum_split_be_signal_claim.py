import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
ATTACH = ROOT / "scripts" / "attach_a1_xau_m5_momentum_continuation.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _attach_module():
    spec = importlib.util.spec_from_file_location("attach_a1_momentum", ATTACH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_signal_claim_defaults_are_safe_and_guard_is_before_order_send() -> None:
    text = _text(EA)

    assert "input bool   InpSignalClaimEnabled            = false;" in text
    assert 'input string InpSignalClaimNamespace          = "A1MOM_SPLIT_BE";' in text
    assert "input int    InpSignalClaimPriority           = 0;" in text
    assert "input int    InpSignalClaimWindowMinutes      = 4;" in text
    assert "input int    InpSignalClaimGraceSeconds       = 2;" in text

    assert "SignalClaimKey" in text
    assert "HigherPrioritySignalClaimExists" in text
    assert "ClaimSignalSlot" in text
    assert "GlobalVariableSetOnCondition" in text
    assert "GlobalVariablesFlush" in text
    assert "signal_claimed_by_higher_priority" in text
    assert "signal_claim_slot_already_claimed" in text
    assert "SIGNAL_CLAIM_OK" in text

    evaluation = text[text.index("void EvaluateCompletedM5Bar()") :]
    assert evaluation.index("ClaimSignalSlot") < evaluation.index(
        "if(InpSplitEntryEnabled && !InpSplitEntryShadowOnly)"
    )
    assert evaluation.index("ClaimSignalSlot") < evaluation.index("g_trade.Buy(first_lots")
    assert evaluation.index("ClaimSignalSlot") < evaluation.index("g_trade.Sell(first_lots")


def test_split_be_tp1_attach_configs_render_priority_claim_stack() -> None:
    module = _attach_module()
    expected = [
        ("split_be_tp1_v6_max2", "1", "A1_XAU_M5_MOM_SPLIT_BE_V6"),
        ("split_be_tp1_weak_hours", "2", "A1_XAU_M5_MOM_SPLIT_BE_WH"),
        ("split_be_tp1_v13", "3", "A1_XAU_M5_MOM_SPLIT_BE_V13"),
    ]

    for index, (variant, priority, comment) in enumerate(expected, start=40):
        config = module.VARIANT_CONFIGS[variant]
        chart = module.render_chart(index, config)

        assert "InpMagicNumber=932280" in chart
        assert f"InpOrderComment={comment}" in chart
        assert "InpUseRiskNormalizedLots=true" in chart
        assert "InpRiskAmountUsd=10.00" in chart
        assert "InpMaxRiskLots=0.05" in chart
        assert "InpSplitEntryEnabled=true" in chart
        assert "InpSplitEntryShadowOnly=false" in chart
        assert "InpSplitEntryFirstTargetR=0.70" in chart
        assert "InpSplitEntryRunnerTargetR=2.00" in chart
        assert "InpSplitEntryMoveRunnerSLToBE=true" in chart
        assert "InpSplitEntryUseMinLotPair=true" in chart
        assert "InpSignalClaimEnabled=true" in chart
        assert "InpSignalClaimNamespace=A1MOM_SPLIT_BE" in chart
        assert f"InpSignalClaimPriority={priority}" in chart
        assert "InpSignalClaimWindowMinutes=4" in chart
        assert "InpSignalClaimGraceSeconds=2" in chart
