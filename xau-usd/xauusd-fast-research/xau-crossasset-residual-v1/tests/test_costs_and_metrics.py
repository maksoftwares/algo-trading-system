from __future__ import annotations

import pytest

from xau_crossasset_residual.core import COMBINED_ID, LONG_ID, SHORT_ID, combine_standalone_trades, metrics, stage_a_gate


def trades(values, field="baseline_net_R"):
    return [{"UTC_date": f"2024-01-{index + 1:02d}", field: value} for index, value in enumerate(values)]


def test_profit_factor_uses_gross_wins_over_absolute_gross_losses():
    assert metrics(trades([2.0, 1.0, -1.5]))["profit_factor"] == pytest.approx(2.0)


def test_expectancy_and_net_r_are_trade_level_arithmetic():
    report = metrics(trades([1.0, -0.5, 0.25]))
    assert report["net_R"] == pytest.approx(.75)
    assert report["expectancy_R"] == pytest.approx(.25)


def test_closed_drawdown_uses_closed_trade_equity_curve():
    report = metrics(trades([2.0, -1.0, -2.0, 1.0]))
    assert report["maximum_closed_drawdown_R"] == pytest.approx(3.0)


def test_top_ten_winner_share_uses_gross_positive_trade_r():
    values = [1.0] * 20 + [-2.0]
    assert metrics(trades(values))["top_ten_winners_fraction"] == pytest.approx(.5)


def test_top_three_winning_day_denominator_is_gross_positive_trade_r():
    fixture = [
        {"UTC_date": "2024-01-01", "baseline_net_R": 2.0},
        {"UTC_date": "2024-01-01", "baseline_net_R": -1.0},
        {"UTC_date": "2024-01-02", "baseline_net_R": 1.0},
    ]
    assert metrics(fixture)["top_three_winning_days_fraction"] == pytest.approx(2 / 3)


def test_baseline_stress_and_transfer_fields_are_separated():
    fixture = [{"UTC_date": "2024-01-01", "baseline_net_R": 1.0, "stress_net_R": .8, "broker_transfer_R": .85}, {"UTC_date": "2024-01-02", "baseline_net_R": -1.0, "stress_net_R": -1.2, "broker_transfer_R": -1.15}]
    assert metrics(fixture)["net_R"] == 0
    assert metrics(fixture, "stress_net_R")["net_R"] == pytest.approx(-.4)
    assert metrics(fixture, "broker_transfer_R")["net_R"] == pytest.approx(-.3)


def test_daily_grouping_nets_only_the_winning_day_numerator():
    fixture = [{"UTC_date": "2024-01-01", "baseline_net_R": 3.0}, {"UTC_date": "2024-01-01", "baseline_net_R": -2.0}, {"UTC_date": "2024-01-02", "baseline_net_R": -1.0}]
    assert metrics(fixture)["top_three_winning_days_fraction"] == pytest.approx(1 / 3)


def test_monthly_frequency_and_active_month_count_are_trade_based():
    fixture = [{"UTC_date": "2024-01-01", "baseline_net_R": 1}, {"UTC_date": "2024-01-02", "baseline_net_R": -1}, {"UTC_date": "2024-02-01", "baseline_net_R": 1}]
    report = metrics(fixture)
    assert report["active_months"] == 2
    assert report["median_monthly_trades"] == pytest.approx(1.5)


def test_combined_conflict_handling_permits_only_one_global_position():
    base = {"simulation_id": LONG_ID + "_STANDALONE", "specialist_id": LONG_ID, "entry_time": "2024-01-01T10:00:00.000Z", "exit_time": "2024-01-01T10:30:00.000Z"}
    overlap = {"simulation_id": SHORT_ID + "_STANDALONE", "specialist_id": SHORT_ID, "entry_time": "2024-01-01T10:15:00.000Z", "exit_time": "2024-01-01T10:45:00.000Z"}
    later = {**overlap, "entry_time": "2024-01-01T10:30:00.000Z", "exit_time": "2024-01-01T11:00:00.000Z"}
    combined, conflicts = combine_standalone_trades([overlap, base, later])
    assert len(combined) == 2 and all(row["simulation_id"] == COMBINED_ID for row in combined)
    assert len(conflicts) == 1 and conflicts[0]["rejection_reason"] == "GLOBAL_XAU_POSITION_ALREADY_OPEN"


def test_stage_a_gate_retains_frozen_performance_thresholds():
    baseline = {"trades": 90, "annualized_trades": 30, "active_months": 18, "profit_factor": 1.18, "expectancy_R": .07, "net_R": .01, "maximum_closed_drawdown_R": 10, "top_ten_winners_fraction": .35, "top_three_winning_days_fraction": .25}
    stress = {**baseline, "profit_factor": 1.07, "expectancy_R": .02}
    broker = {**baseline, "profit_factor": 1.02, "expectancy_R": .001}
    assert stage_a_gate(baseline, stress, broker)[0]
    assert "baseline_profit_factor" in stage_a_gate({**baseline, "profit_factor": 1.179}, stress, broker)[1]
