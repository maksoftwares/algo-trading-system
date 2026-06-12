from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "Phase2TrendGuardedFixObserver.mq5"
PRESETS = ROOT / "mt5" / "Presets"


def test_trend_guarded_fix_observer_is_separate_source_file():
    text = EA.read_text(encoding="utf-8")

    assert "Phase2TrendGuardedFixObserver" in text
    assert "Phase2ShadowFixObserver refused" not in text
    assert 'InpRunId = "phase2-trend-guarded-fix-observer-v0.1"' in text
    assert 'InpShadowPolicyVersion = "trend_guarded_fix_policy_20260612_v2"' in text


def test_trend_guarded_fix_observer_has_no_broker_action_terms():
    text = EA.read_text(encoding="utf-8")

    forbidden_terms = [
        "OrderSend",
        "OrderSendAsync",
        "CTrade",
        "trade.Buy",
        "trade.Sell",
        "PositionOpen",
        "PositionModify",
        "PositionClose",
        "TRADE_ACTION_DEAL",
        "ORDER_TYPE_BUY",
        "ORDER_TYPE_SELL",
    ]
    for term in forbidden_terms:
        assert term not in text


def test_trend_guarded_fix_observer_is_dry_run_locked_by_default():
    text = EA.read_text(encoding="utf-8")

    assert "input bool InpDryRunOnly = true;" in text
    assert "const bool BROKER_ACTION_ALLOWED = false;" in text
    assert "broker_action_allowed" in text


def test_trend_guarded_fix_observer_logs_review_8_fields():
    text = EA.read_text(encoding="utf-8")

    required_fields = [
        "timestamp_dubai",
        "d1_bias",
        "d1_bias_status",
        "m15_ema20_slope_points",
        "m15_ema20_slope_status",
        "h1_ema20_slope_points",
        "h1_ema20_slope_status",
        "atr14_m5_points",
        "estimated_cost_r",
        "m15_ema20_distance_points",
        "trend_veto_action",
        "trend_veto_reason",
        "fixed_shadow_action",
        "fixed_shadow_reason",
    ]
    for field in required_fields:
        assert field in text


def test_trend_guarded_fix_observer_blocks_countertrend_xau_signals():
    text = EA.read_text(encoding="utf-8")

    assert "BLOCK_XAUUSD_SHORT_UPTREND_M15_H1" in text
    assert "BLOCK_XAUUSD_LONG_DOWNTREND_M15_H1" in text
    assert "SLOPE_UNAVAILABLE_M15_H1" in text
    assert "ConfigureIndicatorHandles" in text
    assert "ReleaseIndicatorHandles" in text
    assert "m15_ema20_slope_points >= InpMinSlopePoints" in text
    assert "h1_ema20_slope_points >= InpMinSlopePoints" in text
    assert "m15_ema20_slope_points <= -InpMinSlopePoints" in text
    assert "h1_ema20_slope_points <= -InpMinSlopePoints" in text


def test_trend_guarded_fix_observer_supports_eurusd_repair_observer_label():
    text = EA.read_text(encoding="utf-8")

    assert "session_extreme_retest_v0_repair_v1" in text
    assert "SESSION_EXTREME_RETEST_REPAIR_V1" in text
    assert 'candidate == "session_extreme_retest_v0" || candidate == "session_extreme_retest_v0_repair_v1"' in text


def test_trend_guarded_fix_presets_are_observer_only_and_xau_scoped():
    preset_paths = sorted(PRESETS.glob("Phase2TrendGuardedFixObserver.*_xauusd.set"))

    assert len(preset_paths) == 5
    expected_candidates = {
        "breakout_retest",
        "swing_breakout_retest_v0",
        "symbol_normalized_round_retest_v0",
        "round_number_retest_v0",
        "session_extreme_retest_v0",
    }
    seen_candidates = set()
    for preset_path in preset_paths:
        text = preset_path.read_text(encoding="utf-8")
        assert "InpDryRunOnly=true" in text
        assert "InpTargetSymbol=XAUUSD" in text
        assert "InpQualifiedSymbolsCsv=XAUUSD" in text
        assert "InpExpectedServerMarker=Demo" in text
        assert "InpTrendVetoEnabled=true" in text
        assert "InpMinSlopePoints=50.0" in text
        assert "InpDubaiUtcOffsetMinutes=240" in text
        assert "trend_guarded_fix_policy_20260612_v2" in text
        assert "InpCandidateStatus=TREND_GUARDED_FIX_OBSERVER_V2" in text
        assert "trend_guarded_fix_observer_v2_" in text
        assert "BrokerActionAllowed" not in text
        for line in text.splitlines():
            if line.startswith("InpCandidate="):
                seen_candidates.add(line.split("=", 1)[1])

    assert seen_candidates == expected_candidates
