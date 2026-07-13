from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "A1XauM5MomentumContinuationExecutor.mq5"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_a1_r3_inside_compression_h1_boundary_m15_sweep_reclaim_v1_exact as runner  # noqa: E402


def source() -> str:
    return EA.read_text(encoding="utf-8")


def block(text: str, start: str, end: str) -> str:
    first = text.index(start)
    return text[first : text.index(end, first)]


def test_mode28_identity_is_append_only_after_reserved_mode27() -> None:
    text = source()
    assert (
        "SIGNAL_R1_SECOND_CONTINUATION_HIGHER_LOW_LONG = 26,\n"
        "   SIGNAL_R2_M15_IMPULSE_M5_CONTINUATION_SHORT = 27,\n"
        "   SIGNAL_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM = 28"
    ) in text
    assert "REGIME_ROUTER_R3_INSIDE_COMPRESSION_TREND_SHOCK_BLOCK = 6" in text


def test_all_frozen_mode28_inputs_exist_with_exact_defaults() -> None:
    text = source()
    names = [name for name in runner.FROZEN_INPUTS if name.startswith("InpR3Chop")]
    assert names
    for name in names:
        value = runner.FROZEN_INPUTS[name]
        assert re.search(rf"input\s+\w+\s+{name}\s*=\s*{re.escape(value)}\s*;", text)


def test_mode28_lifecycle_runs_before_generic_m5_prerequisites() -> None:
    text = source()
    m15_modes = block(text, "bool IsM15DecisionSignalMode()", "bool IsH1DecisionSignalMode()")
    assert "SIGNAL_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM" in m15_modes
    evaluate = block(text, "void EvaluateCompletedM5Bar()", "//+------------------------------------------------------------------+")
    lifecycle = evaluate.index("TryR3InsideCompressionH1BoundaryM15SweepReclaimSignal")
    generic_m5 = evaluate.index("if(iBars(InpTargetSymbol, PERIOD_M5)")
    assert lifecycle < generic_m5
    snapshot = evaluate.index("if(InpRegimeSnapshotLogEnabled")
    assert "SIGNAL_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM" in evaluate[
        snapshot : evaluate.index("const int compression_bars", snapshot)
    ]
    assert "if(!r3_chop_mode && InpMaxThreeBarMoveAtr" in evaluate
    assert "if(!r3_chop_mode && InpMinBreakDistanceAtr" in evaluate
    assert "if(!r3_chop_mode && InpMaxBreakDistanceAtr" in evaluate


def test_daily_context_is_completed_d1_and_exact_compression_owner() -> None:
    text = source()
    context = block(
        text,
        "bool R3ChopCompletedD1CompressionContext(",
        "void LogR3ChopEventConsumption",
    )
    assert "IndicatorAtrPercentile(PERIOD_D1, atr_period, percentile_lookback, 1)" in context
    assert "TimeframeHigh(PERIOD_D1, 1, box_days)" in context
    assert "TimeframeLow(PERIOD_D1, 1, box_days)" in context
    assert "TimeframeMedianRange(PERIOD_D1, median_lookback, 1)" in context
    assert "PERIOD_D1, 0" not in context
    refresh = block(text, "void RefreshR3ChopDailyContext", "void LogR3ChopH1Decision")
    assert "const bool owned = compressed && regime == XAU_REGIME_COMPRESSION" in refresh
    assert 'loss_outcome = "shock"' in refresh
    assert 'loss_outcome = "trend_handoff"' in refresh
    assert 'loss_outcome = "compression_lost"' in refresh
    assert "const bool prior_suspended = g_r3_chop_context_suspended" in refresh
    assert '"|prior_context_suspended="' in text
    assert '"|direction_state=" + direction_state' in text
    assert '"|transition=0"' in text


def test_h1_event_is_shift_one_scalar_and_old_m15_is_processed_first() -> None:
    text = source()
    register = block(
        text,
        "void RegisterR3ChopEventAtCompletedH1",
        "bool R3ChopTakeDistinctCompletedM15Bar",
    )
    assert "TimeframeHigh(PERIOD_H1, 1, lookback)" in register
    assert "TimeframeLow(PERIOD_H1, 1, lookback)" in register
    assert "IndicatorAtrPrice(PERIOD_H1" in register
    assert '"R3CHOP_" + IntegerToString((long)setup_time)' in register
    assert "g_r3_chop_state != R3_CHOP_STATE_IDLE" in register
    assert 'LogR3ChopH1Decision("active_event"' in register
    context_gate = register.index('if(g_r3_chop_context_id == "")')
    inactive_log = register.index('LogR3ChopH1Decision("context_inactive"')
    assert context_gate < inactive_log
    driver = block(
        text,
        "bool TryR3InsideCompressionH1BoundaryM15SweepReclaimSignal",
        "bool TryWeeklyLevel",
    )
    process = driver.index("ProcessR3ChopCompletedM15")
    next_event = driver.index("RegisterR3ChopEventAtCompletedH1")
    assert process < next_event
    init = driver.index("if(g_r3_chop_last_scanned_h1_bar == 0)")
    assert init < driver.index("return false;", init) < process


def test_m15_counter_is_distinct_completed_bar_not_elapsed_time() -> None:
    text = source()
    counter = block(
        text,
        "bool R3ChopTakeDistinctCompletedM15Bar",
        "bool ProcessR3ChopCompletedM15",
    )
    assert "m15_close_time <= g_r3_chop_setup_time" in counter
    assert "m15_bar_time == g_r3_chop_last_counted_m15_bar" in counter
    assert "g_r3_chop_m15_bars_seen++" in counter
    assert "PeriodSeconds(PERIOD_M15) *" not in counter
    process = block(
        text,
        "bool ProcessR3ChopCompletedM15",
        "bool TryR3InsideCompressionH1BoundaryM15SweepReclaimSignal",
    )
    decision = process.index('"R3_CHOP_M15_DECISION"')
    ambiguous = process.index('ConsumeR3ChopEvent("ambiguous"')
    expiry = process.index('ConsumeR3ChopEvent("expired"')
    reserve = process.index("ReserveR3ChopFirstSweepConsumption()")
    assert decision < ambiguous
    assert decision < expiry
    assert decision < reserve


def test_first_sweep_is_reserved_before_quality_and_stop_geometry() -> None:
    text = source()
    process = block(
        text,
        "bool ProcessR3ChopCompletedM15",
        "bool TryR3InsideCompressionH1BoundaryM15SweepReclaimSignal",
    )
    reserve = process.index("ReserveR3ChopFirstSweepConsumption()")
    quality = process.index("const bool lower_quality")
    stop = process.index("const double stop_price")
    failed = process.index('FinalizeR3ChopFirstSweepConsumption("first_sweep_failed"')
    entry = process.index('FinalizeR3ChopFirstSweepConsumption("entry"')
    signal = process.index('"WOULD_SIGNAL"')
    assert reserve < quality < stop < failed
    assert reserve < entry < signal
    assert process.count("ReserveR3ChopFirstSweepConsumption()") == 1
    assert "candidate_stop_distance <= MathMax(0.0, InpR3ChopMaxStopH1Atr) * event_h1_atr" in process
    assert "low - MathMax(0.0, InpR3ChopStopBufferM15Atr) * m15_atr" in process
    assert "high + MathMax(0.0, InpR3ChopStopBufferM15Atr) * m15_atr" in process


def test_lifecycle_right_censor_and_common_fields_are_wired() -> None:
    text = source()
    for stage in runner.LIFECYCLE_STAGES.values():
        assert f'"{stage}"' in text
    common = block(text, "string R3ChopEventCommonFields()", "void LogR3ChopTelemetry")
    for token in (
        "event_id=",
        "episode_id=",
        "context_id=",
        "setup_time=",
        "setup=COMPRESSED",
        "entry=COMPRESSED",
        "direction_state=NEUTRAL",
        "shock=0",
        "established=0",
        "transition=0",
    ):
        assert token in common
    deinit = block(text, "void OnDeinit(const int reason)", "void OnTick()")
    assert "g_r3_chop_m15_bars_seen < MathMax(1, InpR3ChopEventWindowM15Bars)" in deinit
    assert 'ConsumeR3ChopEvent("window_end_incomplete", 0, true)' in deinit


def test_router6_is_mode28_only_and_exact_compression_fail_closed() -> None:
    text = source()
    router = block(text, "bool RegimeRouterAllows", "double OwnClosedPnlBetween")
    start = router.index("REGIME_ROUTER_R3_INSIDE_COMPRESSION_TREND_SHOCK_BLOCK")
    route6 = router[start:]
    assert "InpSignalMode != SIGNAL_R3_INSIDE_COMPRESSION_H1_BOUNDARY_M15_SWEEP_RECLAIM" in route6
    assert "regime == XAU_REGIME_COMPRESSION" in route6
    assert "g_r3_chop_context_active" in route6
    assert "!g_r3_chop_context_suspended" in route6
    assert "SIGNAL_R3_COMPRESSION_H1_ACCEPT_M15_FIRST_PULLBACK" not in route6


def test_hard_risk_is_normalized_direction_aware_loss_only_and_wired() -> None:
    text = source()
    risk = block(text, "bool R3ChopHardRiskAllowed", "bool R1HlfHardRiskAllowed")
    assert "const double hard_limit_usd = 50.00" in risk
    assert 'direction == "LONG" ? ORDER_TYPE_BUY : ORDER_TYPE_SELL' in risk
    assert 'AccountInfoString(ACCOUNT_CURRENCY) != "USD"' in risk
    assert "NormalizeLotsForSymbol(lots)" in risk
    assert "NormalizeDouble(direction == \"LONG\" ? ask : bid, digits)" in risk
    assert "OrderCalcProfit(order_type" in risk
    assert "projected_pnl >= 0.0" in risk
    assert "actual_risk_usd = -projected_pnl" in risk
    assert "actual_risk_usd <= hard_limit_usd + 0.0000001" in risk
    execution = block(text, "double actual_risk_usd = 0.0;", "//+------------------------------------------------------------------+")
    assert "R3ChopHardRiskAllowed" in execution
    assert 'risk_block_reason = "r3_chop_hard_50usd_risk_block"' in execution
    assert 'LogOrder("ORDER_SEND_OK"' in execution
    assert 'exact_hard_risk_log ? "OrderCalcProfit"' in execution
