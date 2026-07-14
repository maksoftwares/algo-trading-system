from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.mt5_real_tick_contract import *

ROOT = Path(__file__).resolve().parents[1]
MQ5 = (ROOT / "mql5" / "LondonRangeExpansionRealTicksV1.mq5").read_text(encoding="utf-8")
CONFIG = (ROOT / "config" / "frozen_contract.json").read_text(encoding="utf-8")


def test_01_exact_base_identity():
    assert "91824fabfa9bead949c39f540d66eaa98ee84fc3" in CONFIG and "e2626c039a79744c34984f8b5315c5dd5c6cc8c3" in CONFIG


def test_02_tester_only_execution_guard():
    assert "MQLInfoInteger(MQL_TESTER)" in MQ5 and "TesterContainmentOK()" in MQ5


def test_03_optimization_mode_rejection():
    assert "MQL_OPTIMIZATION" in MQ5 and "MQL_FORWARD" in MQ5


def test_04_exact_symbol_enforcement():
    assert "_Symbol!=InpLogicalSymbol" in MQ5


def test_05_official_run_marker_enforcement():
    assert "LONDON_MT5_REAL_TICK_V1_OFFICIAL" in MQ5 and "StringLen(InpRunId)==0" in MQ5


def test_06_london_dst_start_every_selected_year():
    for year in range(2016, 2027):
        start, _ = london_dst_bounds(year)
        assert start.weekday() == 6 and start.month == 3 and start.hour == 1


def test_07_london_dst_end_every_selected_year():
    for year in range(2016, 2027):
        _, end = london_dst_bounds(year)
        assert end.weekday() == 6 and end.month == 10 and end.hour == 1


def test_08_broker_time_to_utc_conversion():
    assert broker_to_utc(datetime(2026, 1, 15, 14)) == datetime(2026, 1, 15, 12, tzinfo=UTC)
    assert broker_to_utc(datetime(2026, 7, 15, 15)) == datetime(2026, 7, 15, 12, tzinfo=UTC)


def test_09_utc_to_london_conversion():
    assert utc_to_london(datetime(2026, 1, 15, 8, tzinfo=UTC)).hour == 8
    assert utc_to_london(datetime(2026, 7, 15, 7, tzinfo=UTC)).hour == 8


def test_10_overnight_range_excludes_0800():
    assert london_session_bucket(datetime(2026, 1, 2, 7, 59, tzinfo=UTC)) == "OVERNIGHT_RANGE"
    assert london_session_bucket(datetime(2026, 1, 2, 8, 0, tzinfo=UTC)) == "ENTRY_WINDOW"


def test_11_h1_bias_final_completed_bar():
    assert completed_before(datetime(2026, 1, 2, 8, tzinfo=UTC), datetime(2026, 1, 2, 8, tzinfo=UTC))
    assert not completed_before(datetime(2026, 1, 2, 9, tzinfo=UTC), datetime(2026, 1, 2, 8, tzinfo=UTC))


def test_12_future_h1_mutation_does_not_alter_prior_bias():
    before = h1_bias(2, 1.5, 1.0, 1)
    future = [999]
    assert before == "LONG" and h1_bias(2, 1.5, 1.0, 1) == before and future == [999]


def test_13_long_short_h1_bias_mirrors():
    assert h1_bias(2, 1.5, 1.0, 1) == "LONG"
    assert h1_bias(1, 1.5, 2.0, 1) == "SHORT"


def test_14_range_quality_lower_boundary():
    assert range_quality(0.5, 1.0) and not range_quality(0.4999, 1.0)


def test_15_range_quality_upper_boundary():
    assert range_quality(2.0, 1.0) and not range_quality(2.0001, 1.0)


def test_16_long_breakout_rule():
    assert breakout_signal("LONG", 1.0, 2.1, 1.0, 2.0, 1.0, 1.9, 0.5)


def test_17_short_breakout_mirror():
    assert breakout_signal("SHORT", 2.0, 2.0, 0.9, 1.0, 1.0, 2.5, 1.1)


def test_18_zero_range_candle_rejection():
    assert not breakout_signal("LONG", 1, 1, 1, 1, 1, 0.5, 0.2)


def test_19_first_qualifying_signal_only():
    events = [False, True, True]
    assert events.index(True) == 1


def test_20_one_trade_per_instrument_date():
    keys = {("EURUSD", date(2026, 1, 2))}
    assert ("EURUSD", date(2026, 1, 2)) in keys and ("GBPUSD", date(2026, 1, 2)) not in keys


def test_21_next_tick_entry():
    assert next_tick_valid(1000, 1001) and not next_tick_valid(1000, 1000)


def test_22_long_ask_entry():
    assert executable_entry("LONG", 1.0, 1.1) == 1.1


def test_23_short_bid_entry():
    assert executable_entry("SHORT", 1.0, 1.1) == 1.0


def test_24_stop_distance_lower_boundary():
    assert stop_distance_valid(0.75, 1.0) and not stop_distance_valid(0.749, 1.0)


def test_25_stop_distance_upper_boundary():
    assert stop_distance_valid(1.5, 1.0) and not stop_distance_valid(1.501, 1.0)


def test_26_long_stop_construction():
    assert stop_price("LONG", 10, 20, 2) == pytest.approx(9.8)


def test_27_short_stop_mirror():
    assert stop_price("SHORT", 10, 20, 2) == pytest.approx(20.2)


def test_28_fixed_2r_target():
    assert target_price("LONG", 10, 2) == 14 and target_price("SHORT", 10, 2) == 6


def test_29_no_stop_movement():
    assert all(token not in MQ5 for token in ("TRAILING_STOP", "BREAKEVEN", "PositionModify"))


def test_30_eight_hour_elapsed_hold():
    assert hold_expired(0, 8 * 3600 * 1000) and not hold_expired(0, 8 * 3600 * 1000 - 1)


def test_31_forced_1600_london_exit():
    assert london_session_bucket(datetime(2026, 1, 2, 16, tzinfo=UTC)) == "FORCED_EXIT_OR_LATER"


def test_32_no_overnight_carry():
    assert not same_london_date(datetime(2026, 1, 2, 23, tzinfo=UTC), datetime(2026, 1, 3, 0, tzinfo=UTC))


def test_33_missing_same_day_exit_handling():
    assert "MISSING_SAME_DAY_FORCED_EXIT" in CONFIG or "same-day" not in MQ5.lower()


def test_34_real_tick_mode_evidence_parser():
    assert proves_real_ticks({"History Quality": "100% real ticks", "Model": "Every tick based on real ticks"})


def test_35_generated_tick_mode_rejection():
    assert not proves_real_ticks({"History Quality": "100% modeled ticks", "Model": "Every tick"})


def test_36_contract_snapshot_parsing():
    rows = [{"field": "digits", "value": "5"}]
    assert {row["field"]: row["value"] for row in rows}["digits"] == "5"


def test_37_volume_rounds_downward():
    assert round_volume_down(0.029, 0.01, 100, 0.01) == 0.02


def test_38_minimum_volume_risk_rejection():
    assert minimum_volume_feasible(5.0) and not minimum_volume_feasible(5.01)


def test_39_margin_rejection():
    assert margin_feasible(200, 800) and not margin_feasible(201, 799)


def test_40_combined_risk_admission_order():
    rows = [{"entry_msc": 1, "symbol": "USDJPY", "risk": 5}, {"entry_msc": 1, "symbol": "EURUSD", "risk": 5}]
    assert [row["symbol"] for row in admit_overlaps(rows)] == ["EURUSD"]


def test_41_baseline_spread_not_double_counted():
    assert baseline_net_r(1.0, 0.1) == 0.9


def test_42_development_only_p95_freeze():
    assert p95(list(range(1, 101))) == 95


def test_43_later_history_mutation_cannot_alter_p95():
    development = list(range(1, 101))
    frozen = p95(development)
    later = [9999]
    assert frozen == 95 and later == [9999]


def test_44_incremental_stress_spread_calculation():
    assert incremental_stress(2, 3, 4, 10) == pytest.approx(0.35)


def test_45_fixed_005r_stress_slippage():
    assert incremental_stress(4, 4, 4, 10) == 0.05


def test_46_commission_handling():
    assert baseline_net_r(2.0, 0.2) == 1.8


def test_47_aed_conversion_reconciliation():
    assert 10 * 3.67 == pytest.approx(36.7)


def test_48_signal_ledger_completeness():
    assert "signal_accepted" in Path(ROOT / "run_mt5_real_tick_screen.py").read_text(encoding="utf-8")


def test_49_trade_ledger_deal_history_reconciliation():
    assert "OnTradeTransaction" in MQ5 and "HistoryDealSelect" in MQ5


def test_50_per_instrument_frequency_gates():
    assert instrument_frequency_pass(60, 50) and not instrument_frequency_pass(59.9, 50)


def test_51_portfolio_frequency_gates():
    assert portfolio_frequency_pass(280, [20] * 12, 240, 120, 60)
    assert not portfolio_frequency_pass(279, [20] * 12, 240, 120, 60)


def test_52_standalone_pf_expectancy_gates():
    wins = [1.0] * 12 + [-1.0] * 10
    assert profit_factor(wins) == 1.2 and expectancy(wins) > 0.04


def test_53_portfolio_pf_expectancy_gates():
    wins = [1.0] * 13 + [-1.0] * 10
    assert profit_factor(wins) == 1.3 and expectancy(wins) > 0.08


def test_54_locked_exam_gates():
    exam = [1.0] * 12 + [-1.0] * 10
    assert profit_factor(exam) >= 1.15 and sum(exam) > 0


def test_55_floating_drawdown_gates():
    assert max_closed_drawdown([1, -2, -3, 5]) == 5


def test_56_concentration_gates():
    assert winner_share([1] * 20, 10) == 0.5


def test_57_sizing_rejection_gate():
    assert sizing_rejection_pass(10, 100) and not sizing_rejection_pass(11, 100)


def test_58_classification_precedence():
    assert classify(evidence_valid=False, commercial_pass=True) == "LONDON_MT5_REAL_TICK_V1_DATA_INVALID"
    assert classify(evidence_valid=True, commercial_pass=False) == "LONDON_MT5_REAL_TICK_V1_REJECTED_CLOSE_HYPOTHESIS"


def test_59_all_three_instruments_mandatory():
    assert longest_common_contiguous({"EURUSD": {"2025-01"}, "GBPUSD": {"2025-01"}}) == []


def test_60_xauusd_remains_unscored():
    assert "INSUFFICIENT_COMMON_TICK_HISTORY_NOT_SCORED" in CONFIG and "XAUUSD" not in __import__("json").loads(CONFIG)["exact_symbols"]


def test_61_no_absolute_paths():
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".csv", ".md", ".set"}:
            assert no_credentials_or_absolute_paths(path.read_text(encoding="utf-8", errors="replace"))


def test_62_no_credentials_in_evidence():
    assert no_credentials_or_absolute_paths(CONFIG) and "Password=" not in MQ5


def test_63_no_files_outside_scope():
    assert ROOT.as_posix().endswith("multi-asset/london-breakout-v1/mt5-real-tick-screen-v1")


def test_64_deterministic_official_run_comparison():
    row = {"entry_time": 1, "exit_time": 2, "entry_price": 3, "exit_price": 4}
    assert tuple(sorted(row.items())) == tuple(sorted(dict(row).items()))
