from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "mt5" / "Experts" / "Phase2PositionPathObserver.mq5"
PRESET = ROOT / "mt5" / "Presets" / "Phase2PositionPathObserver.demo_account_readonly.set"


def test_position_path_observer_is_read_only():
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
        "TRADE_ACTION",
        "MqlTradeRequest",
        "ORDER_TYPE_BUY",
        "ORDER_TYPE_SELL",
    ]
    for term in forbidden_terms:
        assert term not in text


def test_position_path_observer_is_dry_run_and_demo_locked():
    text = EA.read_text(encoding="utf-8")

    assert 'InpRunId = "phase2-position-path-observer-v0.1"' in text
    assert "input bool InpDryRunOnly = true;" in text
    assert "const bool BROKER_ACTION_ALLOWED = false;" in text
    assert "InpExpectedServerMarker = \"Demo\"" in text
    assert "ContainsText(server, \"live\")" in text
    assert "ContainsText(server, \"real\")" in text
    assert "PositionsTotal()" in text
    assert "PositionGetTicket" in text
    assert "PositionSelectByTicket" in text


def test_position_path_observer_logs_required_snapshot_schema():
    text = EA.read_text(encoding="utf-8")

    required_fields = [
        "ts_utc",
        "ts_broker",
        "ts_dubai",
        "time_bucket",
        "observed_in_evening",
        "position_ticket",
        "magic",
        "candidate",
        "position_comment",
        "sl_initial",
        "tp_initial",
        "initial_stop_points",
        "unrealized_R",
        "distance_to_sl_points",
        "distance_to_tp_points",
        "atr14_m5_points",
        "m15_ema20_slope_points",
        "h1_ema20_slope_points",
        "d1_bias",
        "same_symbol_same_dir_count",
        "account_floating_total",
        "row_type",
    ]
    for field in required_fields:
        assert field in text


def test_position_path_observer_logs_close_summary_and_boundary_rows():
    text = EA.read_text(encoding="utf-8")

    assert "position_path_summary.csv" in text
    assert "close_time_bucket" in text
    assert "observed_in_evening" in text
    assert "CLOSE_DETECTED" in text
    assert "FIRST_SEEN" in text
    assert "SNAPSHOT" in text
    assert "HistorySelect" in text
    assert "DEAL_POSITION_ID" in text
    assert "DEAL_ENTRY_OUT" in text


def test_position_path_observer_slippage_uses_exit_reason_and_latest_sl_tp():
    text = EA.read_text(encoding="utf-8")

    assert "SlippagePointsForExitText" in text
    assert 'exit_reason == "SL"' in text
    assert "reference = state.sl_last" in text
    assert 'exit_reason == "TP"' in text
    assert "reference = state.tp_last" in text
    assert 'return "NA"' in text
    assert "SlippagePointsForExit(state, exit_price)" not in text


def test_position_path_observer_does_not_block_snapshots_on_unsynced_history():
    text = EA.read_text(encoding="utf-8")

    assert "SeriesReady" in text
    assert "SERIES_SYNCHRONIZED" in text
    assert "BarsCalculated(handle) <= shift" in text
    assert "AverageRangePrice" in text
    assert "DailyBiasText" in text


def test_position_path_observer_maps_current_demo_magic_namespaces():
    text = EA.read_text(encoding="utf-8")

    required_fragments = [
        "magic == 930101",
        "magic >= 930000 && magic < 930100",
        "WR50_BreakoutEvening_v0",
        "magic >= 930100 && magic < 930200",
        "WR50_BreakoutQuality_v0",
        "magic >= 930200 && magic < 930300",
        "WR50_Exit1R_v0",
        "magic >= 930300 && magic < 930400",
        "WR50_BreakoutWideStop_WST12",
        "magic >= 930400 && magic < 930500",
        "WR50_BreakoutWideStop_WST15",
        "magic >= 932100 && magic < 932200",
        "W1D1_momentum_continuation",
    ]
    for fragment in required_fragments:
        assert fragment in text


def test_position_path_observer_preset_is_safe():
    text = PRESET.read_text(encoding="utf-8")

    assert "InpDryRunOnly=true" in text
    assert "InpExpectedServerMarker=Demo" in text
    assert "InpSnapshotSeconds=10" in text
    assert "InpDubaiUtcOffsetMinutes=240" in text
    assert "BrokerActionAllowed" not in text
    assert "OrderSend" not in text
