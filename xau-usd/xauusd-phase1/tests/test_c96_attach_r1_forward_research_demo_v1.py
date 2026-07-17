from __future__ import annotations

from pathlib import Path

from scripts.c96_attach_r1_forward_research_demo_v1 import (
    _is_armed,
    _parse_expert,
    _render_chart,
    _replace_expert_input,
)


def test_chart_parser_reads_only_expert_inputs() -> None:
    text = """<chart>
<expert>
name=Phase2ExperimentalDemoExecutor
<inputs>
InpDryRunOnly=false
InpBrokerActionAllowed=true
</inputs>
</expert>
<object>
name=autotrade historical object
</object>
</chart>
"""
    expert, inputs = _parse_expert(text)

    assert expert == "Phase2ExperimentalDemoExecutor"
    assert inputs == {"InpDryRunOnly": "false", "InpBrokerActionAllowed": "true"}
    assert _is_armed(inputs)


def test_pause_replacement_is_limited_to_expert_block() -> None:
    text = """<expert>
name=Phase2ExperimentalDemoExecutor
<inputs>
InpDryRunOnly=false
InpBrokerActionAllowed=true
</inputs>
</expert>
InpBrokerActionAllowed=historical_object_value
"""
    changed = _replace_expert_input(text, "InpBrokerActionAllowed", "false")

    assert "InpBrokerActionAllowed=false" in changed
    assert "InpBrokerActionAllowed=historical_object_value" in changed


def test_rendered_target_chart_is_armed_with_frozen_risk_and_signal(tmp_path: Path) -> None:
    inputs = {
        "InpRunId": "A3_R1_FORWARD_RESEARCH_DEMO_V1_20260717",
        "InpAllowDemoTrading": "true",
        "InpMagicNumber": "934100",
        "InpSignalMode": "7",
        "InpDirectionMode": "1",
        "InpRegimeRouterMode": "1",
        "InpRiskAmountUsd": "30.00",
        "InpMaxRiskLots": "0.01",
        "InpRejectRiskOvershootEnabled": "true",
        "InpMaxRiskOvershootPct": "0.00",
    }
    text = _render_chart(tmp_path / "chart08.chr", "A1XauM5MomentumContinuationExecutor", inputs)
    expert, parsed = _parse_expert(text)

    assert expert == "A1XauM5MomentumContinuationExecutor"
    assert _is_armed(parsed)
    assert parsed["InpMagicNumber"] == "934100"
    assert parsed["InpSignalMode"] == "7"
    assert parsed["InpRiskAmountUsd"] == "30.00"
    assert parsed["InpMaxRiskOvershootPct"] == "0.00"
