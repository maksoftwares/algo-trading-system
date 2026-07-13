import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
ATTACH = ROOT / "scripts" / "attach_a1_xau_m5_momentum_continuation.py"
RUNNER = ROOT / "scripts" / "run_a1_xau_m5_momentum_backtest_variants.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _attach_module():
    spec = importlib.util.spec_from_file_location("attach_a1_momentum", ATTACH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _runner_module():
    spec = importlib.util.spec_from_file_location("run_a1_momentum_variants", RUNNER)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Dataclasses resolve postponed annotations through the defining module.
    # Register the dynamically loaded runner just as the normal import path does.
    sys.modules[spec.name] = module
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

    assert "input double InpSplitEntryFirstLotFraction    = 0.50;" in text
    assert "input int    InpSplitEntryBreakEvenMode       = 1;" in text
    assert "input int    InpManagementLogMode             = 1;" in text
    assert "InpSplitEntryBreakEvenMode != 1" in text
    assert "InpSplitEntryBreakEvenMode == 2" in text


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


def test_goal_split_grid_variants_are_predeclared_once() -> None:
    module = _runner_module()
    variants = [variant for variant in module.VARIANTS if variant.name.startswith("goal_split_")]

    assert len(variants) == 81

    cell_ids = {
        "_".join(variant.name.split("_")[2:-1])
        for variant in variants
    }
    assert len(cell_ids) == 27

    for variant in variants:
        inputs = variant.tester_inputs
        assert inputs["InpSplitEntryEnabled"] == "true"
        assert inputs["InpSplitEntryShadowOnly"] == "false"
        assert inputs["InpSplitEntryFirstTargetR"] == "0.70"
        assert inputs["InpSplitEntryFirstLotFraction"] in {"0.333333", "0.500000", "0.666667"}
        assert inputs["InpSplitEntryRunnerTargetR"] in {"2.00", "2.50", "3.00"}
        assert inputs["InpSplitEntryBreakEvenMode"] in {"0", "1", "2"}
        assert inputs["InpManagementLogMode"] == "0"
