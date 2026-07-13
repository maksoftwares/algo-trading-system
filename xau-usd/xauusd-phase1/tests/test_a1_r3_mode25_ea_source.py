from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r3_compression_acceptance_first_pullback_v1_exact as runner  # noqa: E402


def source() -> str:
    return EA.read_text(encoding="utf-8")


def function_block(text: str, start: str, end: str) -> str:
    first = text.index(start)
    last = text.index(end, first)
    return text[first:last]


def test_mode25_is_append_only_and_preserves_modes22_through24() -> None:
    text = source()
    expected = (
        "SIGNAL_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT = 22,\n"
        "   SIGNAL_R1_PRIOR_D1_HIGH_FIRST_RETEST_LONG = 23,\n"
        "   SIGNAL_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT = 24,\n"
        "   SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK = 25"
    )
    assert expected in text
    assert "REGIME_ROUTER_R3_COMPRESSION_RELEASE_SHOCK_BLOCK = 5" in text


def test_frozen_r3_inputs_exist_and_match_the_preregistered_geometry() -> None:
    text = source()
    expected = {
        "InpR3CompressionAtrPeriod": "14",
        "InpR3CompressionAtrPercentileLookback": "252",
        "InpR3CompressionAtrPercentileMax": "30.00",
        "InpR3CompressionBoxDays": "5",
        "InpR3CompressionRangeMedianLookback": "20",
        "InpR3CompressionRangeMedianMax": "1.00",
        "InpR3SetupLifetimeH1Bars": "24",
        "InpR3AcceptBreakMarginH1Atr": "0.10",
        "InpR3AcceptMinBodyFraction": "0.50",
        "InpR3AcceptLongCloseLocationMin": "0.75",
        "InpR3AcceptShortCloseLocationMax": "0.25",
        "InpR3RetestWindowM15Bars": "12",
        "InpR3RetestTouchM15Atr": "0.25",
        "InpR3InvalidationH1Atr": "0.10",
        "InpR3RejectDistanceM15Atr": "0.10",
        "InpR3RejectMinBodyFraction": "0.50",
        "InpR3RejectLongCloseLocationMin": "0.75",
        "InpR3RejectShortCloseLocationMax": "0.25",
        "InpR3StopBufferM15Atr": "0.20",
        "InpR3MaxStopH1Atr": "1.00",
        "InpR3ConsumeOnFirstTouch": "true",
    }
    for name, value in expected.items():
        assert re.search(rf"input\s+\w+\s+{name}\s*=\s*{re.escape(value)}\s*;", text)
        assert runner.R3_INPUTS[name] == value


def test_mode25_runs_only_on_new_completed_m15_decisions() -> None:
    text = source()
    block = function_block(text, "bool IsM15DecisionSignalMode()", "bool IsH1DecisionSignalMode()")
    assert "InpSignalMode == SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK" in block
    dispatch = function_block(text, "void EvaluateCompletedM5Bar()", "//+------------------------------------------------------------------+")
    assert "TryR3CompressionH1AcceptM15FirstPullbackSignal" in dispatch


def test_compression_setup_uses_completed_d1_shift_one_only() -> None:
    text = source()
    block = function_block(
        text,
        "bool R3CompletedD1CompressionSetup(",
        "bool RegisterR3CompressionEventAtH1Shift",
    )
    assert "IndicatorAtrPercentile(PERIOD_D1, atr_period, percentile_lookback, 1)" in block
    assert "TimeframeHigh(PERIOD_D1, 1, box_days)" in block
    assert "TimeframeLow(PERIOD_D1, 1, box_days)" in block
    assert "TimeframeMedianRange(PERIOD_D1, median_lookback, 1)" in block
    assert "PERIOD_D1, 0" not in block
    assert "range_ratio = (width / (double)box_days) / median_range" in block


def test_h1_refresh_is_no_backfill_scalar_and_first_decision_per_day() -> None:
    text = source()
    block = function_block(
        text,
        "void RefreshR3CompressionTransitionState()",
        "bool TryR3CompressionH1AcceptM15FirstPullbackSignal",
    )
    init = block.index("if(g_r3_last_scanned_h1_bar == 0)")
    init_return = block.index("return;", init)
    register = block.index("RegisterR3CompressionEventAtH1Shift(1)")
    assert init < init_return < register
    assert "g_r3_transition_state != R3_TRANSITION_STATE_IDLE" in block
    assert "if(!first_h1_of_new_day)" in block
    assert block.count("RegisterR3CompressionEventAtH1Shift(1)") == 1


def test_h1_acceptance_is_symmetric_and_hands_established_trends_away() -> None:
    text = source()
    acceptance = function_block(
        text,
        "bool AcceptR3ReleaseAtH1Shift",
        "void RefreshR3CompressionTransitionState",
    )
    assert "close >= g_r3_box_high +" in acceptance
    assert "close <= g_r3_box_low -" in acceptance
    assert "close_location >= InpR3AcceptLongCloseLocationMin" in acceptance
    assert "close_location <= InpR3AcceptShortCloseLocationMax" in acceptance
    assert 'LogR3TransitionLifecycle("R3_H1_ACCEPTED", "accepted")' in acceptance
    refresh = function_block(
        text,
        "void RefreshR3CompressionTransitionState()",
        "bool TryR3CompressionH1AcceptM15FirstPullbackSignal",
    )
    assert 'ConsumeR3TransitionEvent("shock")' in refresh
    assert 'ConsumeR3TransitionEvent("established_trend_handoff")' in refresh


def test_lifetimes_use_completed_bar_counters_not_wall_clock_seconds() -> None:
    text = source()
    refresh = function_block(
        text,
        "void RefreshR3CompressionTransitionState()",
        "bool TryR3CompressionH1AcceptM15FirstPullbackSignal",
    )
    pullback = function_block(
        text,
        "bool TryR3CompressionH1AcceptM15FirstPullbackSignal",
        "bool TryWeeklyLevel",
    )
    assert "g_r3_setup_h1_bars_elapsed++" in refresh
    assert "g_r3_pullback_m15_bars_elapsed++" in pullback
    assert "g_r3_setup_h1_bars_elapsed = 1" in text
    assert "m15_close_time <= g_r3_acceptance_time" in pullback
    assert "g_r3_setup_expiry" not in text
    assert "g_r3_pullback_expiry" not in text
    assert "InpR3SetupLifetimeH1Bars) * PeriodSeconds" not in text
    assert "InpR3RetestWindowM15Bars) * PeriodSeconds" not in text


def test_deinit_records_truthful_right_censoring_instead_of_false_expiry() -> None:
    text = source()
    block = function_block(text, "void OnDeinit(const int reason)", "void OnTick()")
    assert "const int completed_bars" in block
    assert "const int lifetime_bars" in block
    assert "completed_bars >= lifetime_bars" in block
    assert 'lifetime_elapsed ? "expired" : "window_end_incomplete"' in block


def test_first_touch_is_consumed_before_quality_and_has_no_retry() -> None:
    text = source()
    block = function_block(
        text,
        "bool TryR3CompressionH1AcceptM15FirstPullbackSignal",
        "bool TryWeeklyLevel",
    )
    touch = block.index("const bool first_touch")
    reserve = block.index("ReserveR3FirstTouchConsumption()")
    quality = block.index("const bool accepted_pullback")
    assert touch < reserve < quality
    assert block.count("ReserveR3FirstTouchConsumption()") == 1
    assert 'FinalizeR3FirstTouchConsumption("entry")' in block
    assert 'FinalizeR3FirstTouchConsumption("first_touch_failed")' in block
    assert "R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK_LONG" in block
    assert "R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK_SHORT" in block
    assert '"|setup=COMPRESSED|phase=TRANSITION|shock=0|established=0"' in block


def test_lifecycle_stages_and_all_frozen_terminal_outcomes_are_logged() -> None:
    text = source()
    for stage in ("R3_EVENT_REGISTERED", "R3_H1_ACCEPTED", "R3_EVENT_CONSUMED"):
        assert stage in text
    for outcome in runner.ALLOWED_CONSUMPTION_OUTCOMES:
        if outcome == "window_end_incomplete":
            assert f'"{outcome}"' in text
        else:
            assert f'("{outcome}")' in text or f', "{outcome}")' in text
    assert "R3TransitionEventId()" in text
    assert '"|event_id=" + event_id' in text


def test_router5_preserves_legacy_mode7_and_accepts_only_new_mode25_alongside_it() -> None:
    text = source()
    block = function_block(text, "bool RegimeRouterAllows", "double OwnClosedPnlBetween")
    shock = block.index("if(regime == XAU_REGIME_SHOCK)")
    router5 = block.index("REGIME_ROUTER_R3_COMPRESSION_RELEASE_SHOCK_BLOCK")
    assert shock < router5
    assert "InpSignalMode == SIGNAL_D1_COMPRESSION_H4_EXPANSION" in block
    assert "InpSignalMode == SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK" in block
    assert block.index("REGIME_ROUTER_SHORT_R5_UPTREND_CHOP_ONLY", router5 + 1) > router5
    assert "SIGNAL_R2_PRIOR_D1_LOW_FIRST_RETEST_SHORT" not in block[router5:]
    assert "SIGNAL_R2_SECOND_CONTINUATION_LOWER_HIGH_SHORT" not in block[router5:]


def test_direction_aware_ordercalcprofit_guard_is_fail_closed_at_fifty_dollars() -> None:
    text = source()
    block = function_block(text, "bool R3TransitionHardRiskAllowed", "double RecentHigh")
    assert "actual_risk_usd = -1.0" in block
    assert "const double hard_limit_usd = 50.00" in block
    assert 'direction == "LONG" ? ORDER_TYPE_BUY : ORDER_TYPE_SELL' in block
    assert 'direction == "LONG" ? ask : bid' in block
    assert "OrderCalcProfit(order_type" in block
    assert 'AccountInfoString(ACCOUNT_CURRENCY) != "USD"' in block
    assert "MathAbs(InpMaxRiskOvershootPct) > 0.0000001" in block
    assert "actual_risk_usd <= hard_limit_usd + 0.0000001" in block


def test_mode25_risk_reason_and_successful_actual_risk_logging_are_wired() -> None:
    text = source()
    execution = function_block(text, "double actual_risk_usd = 0.0;", "//+------------------------------------------------------------------+")
    assert "R3TransitionHardRiskAllowed" in execution
    assert 'risk_block_reason = "r3_normalized_entry_to_stop_risk_overshoot"' in execution
    assert "InpSignalMode == SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK" in execution
    assert 'LogOrder("ORDER_SEND_OK"' in execution
    assert "logged_actual_risk_usd" in execution


def test_frozen_history_is_authorized_after_semantic_review() -> None:
    assert runner.HISTORICAL_RUN_AUTHORIZED is True
    assert runner.FROZEN_INPUTS_SHA256 == "ca53d3b0e4b19df61b45c110943452178f3b45b547ff154860b517d2c02bfc5f"
