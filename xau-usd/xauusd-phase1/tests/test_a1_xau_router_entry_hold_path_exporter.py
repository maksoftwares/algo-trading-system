from __future__ import annotations

import re
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1]
EXPORTER = PHASE1_ROOT / "mt5" / "Experts" / "A1XauRouterEntryHoldPathExporter.mq5"


def source() -> str:
    return EXPORTER.read_text(encoding="utf-8")


def test_exporter_is_tester_only_and_has_no_execution_surface() -> None:
    text = source()
    lowered = text.lower()

    assert "#property strict" in text
    assert '#property tester_file "a1_xau_router_entry_hold_path_schedule_v1.csv"' in text
    assert "MQLInfoInteger(MQL_TESTER)" in text
    assert "if(!(bool)MQLInfoInteger(MQL_TESTER))" in text
    assert "OrderCalcProfit" in text  # calculation-only risk and path marks

    forbidden = (
        "<trade/trade.mqh>",
        "ctrade",
        "ordersend(",
        "ordersendasync(",
        "positionclose(",
        "positionmodify(",
        ".buy(",
        ".sell(",
    )
    for token in forbidden:
        assert token not in lowered


def test_exporter_schedule_is_exact_and_outcome_free() -> None:
    text = source()
    header_match = re.search(
        r"string expected\[\]\s*=\s*\{(?P<body>.*?)\};",
        text,
        flags=re.DOTALL,
    )
    assert header_match is not None
    fields = re.findall(r'"([a-z0-9_]+)"', header_match.group("body"))
    assert fields == [
        "trade_id",
        "source_id",
        "component",
        "expected_regime",
        "direction",
        "signal_time_broker",
        "entry_time_broker",
        "exit_time_broker",
        "native_run_id",
        "native_account",
        "native_symbol",
        "native_magic",
        "native_position_id",
        "native_entry_order",
        "native_entry_deal",
        "native_exit_order",
        "native_exit_deal",
        "executed_volume",
        "actual_entry_price",
        "original_sl",
        "original_tp",
        "order_bid",
        "order_ask",
        "spread_points",
        "estimated_cost_r",
        "signal_reason",
        "native_exit_reason_code",
    ]
    schedule_section = text[text.index("struct VirtualTrade") : text.index("input string InpRunId")]
    assert "final_pnl" not in schedule_section.lower()
    assert "profit_usd" not in schedule_section.lower()
    assert 'input int    InpExpectedScheduleRows = 678;' in text
    assert '"schedule_source_counts", "PASS", "145/413/57/63 total=678"' in text


def test_exporter_uses_exact_event_keys_and_actual_bar_availability() -> None:
    text = source()
    assert "long tester_time_msc;" in text
    assert "long callback_sequence;" in text
    assert "long event_sequence;" in text
    assert "g_callback_sequence++;" in text
    assert "g_event_sequence++;" in text
    assert "g_current_tick.time_msc" in text
    assert '"BAR_AVAILABLE"' in text
    assert "const datetime current_open = iTime(InpTargetSymbol, timeframe, 0);" in text
    assert "const datetime completed_open = iTime(InpTargetSymbol, timeframe, 1);" in text
    assert "completed_open >= current_open" in text
    assert '"minimum_bar_shift=1"' in text

    forbidden_feature_reads = re.findall(
        r"i(?:Open|High|Low|Close)\(InpTargetSymbol,\s*(?:PERIOD_[A-Z0-9]+|timeframe),\s*0\)",
        text,
    )
    assert forbidden_feature_reads == []


def test_exporter_h1_q80_is_prior_252_type7_and_causal() -> None:
    text = source()
    assert "const int H1_Q80_WINDOW = 252;" in text
    assert "const double H1_Q80_PROBABILITY = 0.80;" in text
    assert "const int current_window_first_shift = 2;" in text
    assert "const int previous_window_first_shift = 3;" in text
    assert "ArrayResize(current_window, H1_Q80_WINDOW);" in text
    assert "ArrayResize(previous_window, H1_Q80_WINDOW);" in text
    assert "ArraySort(values);" in text
    assert "(double)(H1_Q80_WINDOW - 1) * H1_Q80_PROBABILITY" in text
    assert "MathFloor(h)" in text
    assert "MathCeil(h)" in text
    assert "values[lower] + (values[upper] - values[lower]) * weight" in text
    assert "ema20_values[current_index + InpRegimeSlopeLagBars]" in text
    assert "current bar excluded" in text


def test_exporter_m15_pivots_are_strict_two_left_two_right() -> None:
    text = source()
    assert "const int candidate_shift = 3;" in text
    for shift in (5, 4, 2, 1):
        assert f"candidate_high > iHigh(InpTargetSymbol, PERIOD_M15, {shift})" in text
        assert f"candidate_low < iLow(InpTargetSymbol, PERIOD_M15, {shift})" in text
    assert "g_last_confirmed_m15_swing_high_key = confirmation_key;" in text
    assert "g_last_confirmed_m15_swing_low_key = confirmation_key;" in text
    assert 'return "AMBIGUOUS";' in text
    assert 'return "UNKNOWN";' in text
    assert "bool TacticalM15Decidable(const SnapshotCore &snapshot)" in text
    assert "!snapshot_core_valid || !TacticalM15Decidable(snapshot)" in text
    build_snapshot = text[text.index("bool BuildSnapshotCore") : text.index("bool TacticalM15Decidable")]
    assert 'snapshot.m15_structure_break != "UNKNOWN"' not in build_snapshot
    assert 'snapshot.m15_structure_break != "AMBIGUOUS"' not in build_snapshot


def test_exporter_schedule_drives_causal_virtual_position_events() -> None:
    text = source()
    for stage in ("SIGNAL", "ENTRY", "H1_HOLD", "EXIT", "RUNTIME_ERROR", "SNAPSHOT_UNAVAILABLE"):
        assert f'"{stage}"' in text
    assert "trade.signal_time_broker <= trade.entry_time_broker" in text
    assert "trade.entry_time_broker < trade.exit_time_broker" in text
    assert "CurrentTickIsStrictlyAfterEntry(trade)" in text
    assert "g_current_tick_time_msc > trade.entry_event_key.tester_time_msc" in text
    assert "g_callback_sequence > trade.entry_event_key.callback_sequence" in text
    assert "ProcessVirtualExits(g_current_tick);" in text
    assert "g_next_signal_index++" in text
    assert "g_next_entry_index++" in text
    assert "for(int trade_index = 0; trade_index < ArraySize(g_trades); trade_index++)" not in text
    assert "if(new_m5)" in text
    assert text.index("const bool new_m5 = ObserveCompletedBar(AUDIT_TF_M5);") < text.index(
        "new_h1 = ObserveCompletedBar(AUDIT_TF_H1);"
    )
    assert text.index("ProcessVirtualExits(g_current_tick);") < text.index(
        "new_h1 = ObserveCompletedBar(AUDIT_TF_H1);"
    )
    assert text.index("LogH1HoldingObservations(g_current_tick);") < text.index(
        "ProcessScheduledSignalsAndEntries(g_current_tick, new_m5);"
    )


def test_exporter_uses_executable_marks_and_pre_event_extrema() -> None:
    text = source()
    assert 'return trade.direction == "LONG" ? tick.bid : tick.ask;' in text
    assert "if(mark_r > trade.mfe_r)" in text
    assert "if(mark_r < trade.mae_r)" in text
    assert "mfe_r_before_event" in text
    assert "mae_r_before_event" in text
    assert "virtual_first_sl_tp_trigger" in text
    assert "tick.bid <= trade.original_sl" in text
    assert "tick.ask >= trade.original_sl" in text
    assert "tick.bid >= trade.original_tp" in text
    assert "tick.ask <= trade.original_tp" in text
    assert "if(!g_trade_session_open)" in text
    assert "SymbolInfoSessionTrade" in text
    assert '"tick_flags", "trade_session_open"' in text
    assert "completed_h1_first_actual_tick|trade_session_closed_quote_mark" in text
    extrema = text[text.index("void UpdateOpenTradeExtrema") : text.index("void WriteStaticProvenance")]
    assert "if(!g_trade_session_open)" not in extrema
    assert "virtual_exit_not_early" in text
    assert "virtual_exit_timestamp_reconciles" in text
    assert "early_exit_trigger_seen" in text
    assert "RemoveActiveTradeAt(active_position);" not in text[
        text.index('if(trigger && tick.time < trade.exit_time_broker)') :
        text.index('if(trigger && tick.time == trade.exit_time_broker)')
    ]


def test_exporter_logs_timezone_symbol_provenance_and_runtime_assertions() -> None:
    text = source()
    assert "TimeCurrent() - TimeGMT()" in text
    assert "TimeTradeServer()" in text
    assert "TimeLocal()" in text
    assert '"broker_to_gmt_offset_seconds"' in text
    for symbol_field in (
        "SYMBOL_POINT",
        "SYMBOL_TRADE_TICK_SIZE",
        "SYMBOL_TRADE_TICK_VALUE_LOSS",
        "SYMBOL_TRADE_CONTRACT_SIZE",
        "SYMBOL_VOLUME_STEP",
    ):
        assert symbol_field in text
    assert '"all_678_schedule_rows_complete"' in text
    assert '"zero_execution_surface_runtime"' in text
    assert "FileFlush(g_assertion_handle);" in text
    assert "g_have_last_completed_h1_snapshot = false;" in text
    assert "SnapshotInvalidDetail(snapshot)" in text


def test_exporter_freezes_router_v1_inputs_and_provenance() -> None:
    text = source()
    expected_defaults = (
        "InpAtrPeriod = 14;",
        "InpRegimeFastEmaPeriod = 20;",
        "InpRegimeSlowEmaPeriod = 50;",
        "InpRegimeSlopeLagBars = 5;",
        "InpRegimePersistenceD1Bars = 2;",
        "InpRegimeRequireH4Confirm = true;",
        "InpRegimeShockH1RangeAtrMultiple = 3.00;",
        "InpRegimeShockD1AtrPercentileMin = 95.00;",
        "InpRegimeShockD1AtrLookback = 60;",
        "InpRegimeCompressionD1AtrPercentileMax = 30.00;",
        "InpRegimeCompressionBoxDays = 5;",
        "InpRegimeCompressionRangeMedianMax = 1.00;",
    )
    for default in expected_defaults:
        assert default in text
    assert "FrozenInputsMatch()" in text
    assert "006824cde421ea61a0bcdb074804f9ccf95c17a9" in text
    assert "3372d8e751141f1d397d9967b8c14272046e1a733a64f67e63fcc3f56e53d355" in text
