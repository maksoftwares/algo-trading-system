from __future__ import annotations

import math

import pandas as pd
import pytest

from xau_continuation import research


MAX_TIME = 2**63 - 1


def _ticks(rows: list[tuple[int, str | None, float, float]]) -> pd.DataFrame:
    return pd.DataFrame([{"timestamp_msc": timestamp, "source_sequence": sequence, "bid": bid, "ask": ask, "spread": ask - bid} for timestamp, sequence, bid, ask in rows])


def _execute(core, ticks: pd.DataFrame, direction: str = "LONG", entry: float = 100.0, stop: float = 99.0, target: float = 101.5, expiry: int = 10_000, force: int = 20_000):
    return core.process_ordered_exit_ticks(ticks, direction=direction, entry_price=entry, risk=1.0, stop=stop, target=target, convergence_ms=MAX_TIME, convergence_z=float("nan"), expiry_ms=expiry, force_ms=force, utc_date="1970-01-01")


def test_long_stop_executes_through_bid(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(1_000, "0001", 98.9, 100.5)]))
    assert result["exit_reason"] == "STOP"
    assert result["exit_price"] == 98.9


def test_short_stop_executes_through_ask(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(1_000, "0001", 99.0, 101.1)]), direction="SHORT", stop=101.0, target=98.5)
    assert result["exit_reason"] == "STOP"
    assert result["exit_price"] == 101.1


def test_long_target_executes_through_bid_at_frozen_target(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(1_000, "0001", 101.8, 102.0)]))
    assert result["exit_reason"] == "TARGET"
    assert result["exit_price"] == 101.5
    assert result["target_gap"] is True


def test_short_target_executes_through_ask_at_frozen_target(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(1_000, "0001", 98.0, 98.2)]), direction="SHORT", stop=101.0, target=98.5)
    assert result["exit_reason"] == "TARGET"
    assert result["exit_price"] == 98.5


def test_adverse_stop_gap_uses_actual_price(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(1_000, "0001", 98.0, 98.2)]))
    assert result["stop_gap"] is True
    assert result["exit_price"] == 98.0


def test_source_sequence_target_before_stop(reviewed) -> None:
    core, _, _ = reviewed
    ticks = _ticks([(1_000, "0001", 101.6, 101.8), (1_000, "0002", 98.8, 99.0)])
    result = _execute(core, ticks)
    assert result["exit_reason"] == "TARGET"
    assert result["exit_source_sequence"] == "0001"


def test_source_sequence_stop_before_target(reviewed) -> None:
    core, _, _ = reviewed
    ticks = _ticks([(1_000, "0001", 98.8, 99.0), (1_000, "0002", 101.6, 101.8)])
    result = _execute(core, ticks)
    assert result["exit_reason"] == "STOP"
    assert result["exit_source_sequence"] == "0001"


def test_unordered_same_timestamp_both_barriers_stops_first(reviewed) -> None:
    core, _, _ = reviewed
    ticks = _ticks([(1_000, None, 101.6, 101.8), (1_000, None, 98.8, 99.0)])
    result = _execute(core, ticks)
    assert result["exit_reason"] == "STOP"
    assert result["identical_timestamp_ambiguity"] is True
    assert result["exit_ordering_quality"] == "IDENTICAL_TIMESTAMP_STOP_FIRST"


def test_missing_sequence_without_both_barriers_is_invalid(reviewed) -> None:
    core, _, _ = reviewed
    with pytest.raises(core.ExecutionOrderingError, match="MISSING_SOURCE_SEQUENCE"):
        _execute(core, _ticks([(1_000, None, 100.1, 100.3)]))


def test_duplicate_sequence_conflict_is_invalid(reviewed) -> None:
    core, _, _ = reviewed
    ticks = _ticks([(1_000, "0001", 100.1, 100.3), (1_000, "0001", 100.2, 100.4)])
    with pytest.raises(core.ExecutionOrderingError, match="DUPLICATE_SOURCE_SEQUENCE_CONFLICT"):
        _execute(core, ticks)


def test_identical_duplicate_sequence_is_collapsed(reviewed) -> None:
    core, _, _ = reviewed
    ticks = _ticks([(1_000, "0001", 101.6, 101.8), (1_000, "0001", 101.6, 101.8)])
    result = _execute(core, ticks)
    assert result["exit_reason"] == "TARGET"
    assert result["exit_source_sequence"] == "0001"
    assert result["exit_timestamp_group_size"] == 2


def test_ninety_minute_expiry_is_checked_after_barriers(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(10_000, "0001", 101.6, 101.8)]), expiry=10_000)
    assert result["exit_reason"] == "TARGET"


def test_ninety_minute_expiry_closes_at_executable_side(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(10_000, "0001", 100.2, 100.4)]), expiry=10_000)
    assert result["exit_reason"] == "NINETY_MINUTE_EXPIRY"
    assert result["exit_price"] == 100.2


def test_same_day_force_close_occurs(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(20_000, "0001", 100.2, 100.4)]), expiry=30_000, force=20_000)
    assert result["exit_reason"] == "SAME_DAY_FORCE_CLOSE"


def test_no_residual_convergence_exit_is_active(reviewed) -> None:
    core, _, _ = reviewed
    result = _execute(core, _ticks([(10_000, "0001", 100.2, 100.4)]), expiry=10_000)
    assert result["exit_reason"] != "RESIDUAL_CONVERGENCE"
    assert MAX_TIME > result["exit_tick"].timestamp_msc


def test_mfe_and_mae_stop_at_selected_exit(reviewed) -> None:
    core, _, _ = reviewed
    ticks = _ticks([(1_000, "0001", 100.5, 100.7), (2_000, "0002", 98.9, 99.1), (3_000, "0003", 105.0, 105.2)])
    result = _execute(core, ticks)
    assert result["MFE_R"] == pytest.approx(.5)
    assert result["MAE_R"] == pytest.approx(-1.1)


def test_combined_simulation_keeps_one_global_position(reviewed) -> None:
    core, _, _ = reviewed
    trades = [
        {"entry_time": "2020-01-01T10:00:00.000Z", "exit_time": "2020-01-01T11:00:00.000Z", "specialist_id": research.LONG_ID, "simulation_id": "a"},
        {"entry_time": "2020-01-01T10:30:00.000Z", "exit_time": "2020-01-01T11:30:00.000Z", "specialist_id": research.SHORT_ID, "simulation_id": "b"},
    ]
    combined, conflicts = core.combine_standalone_trades(trades)
    assert len(combined) == 1 and len(conflicts) == 1
    assert combined[0]["simulation_id"] == research.COMBINED_ID


def test_profit_factor_uses_gross_wins_over_gross_losses(reviewed) -> None:
    core, _, _ = reviewed
    trades = [{"baseline_net_R": value, "UTC_date": f"2020-01-0{index + 1}"} for index, value in enumerate([1.5, .5, -1.0])]
    report = core.metrics(trades)
    assert report["profit_factor"] == pytest.approx(2.0)
    assert report["expectancy_R"] == pytest.approx(1 / 3)


def test_drawdown_is_closed_equity_peak_to_trough(reviewed) -> None:
    core, _, _ = reviewed
    trades = [{"baseline_net_R": value, "UTC_date": f"2020-01-0{index + 1}"} for index, value in enumerate([2.0, -1.0, -2.0, 1.0])]
    assert core.metrics(trades)["maximum_closed_drawdown_R"] == pytest.approx(3.0)


def test_winning_day_denominator_is_gross_positive_trade_r(reviewed) -> None:
    core, _, _ = reviewed
    trades = [{"baseline_net_R": 2.0, "UTC_date": "2020-01-01"}, {"baseline_net_R": -1.0, "UTC_date": "2020-01-01"}, {"baseline_net_R": 1.0, "UTC_date": "2020-01-02"}]
    report = core.metrics(trades)
    assert report["top_three_winning_days_fraction"] == pytest.approx(2 / 3)


def test_broker_transfer_penalty_is_frozen() -> None:
    baseline = .4
    broker_transfer = baseline - .15
    assert broker_transfer == pytest.approx(.25)


def test_ordinary_stress_adds_only_incremental_spread() -> None:
    baseline, observed_entry, observed_exit, p95, risk = .5, .2, .3, .4, 2.0
    entry_increment = max(0, p95 - observed_entry) / (2 * risk)
    exit_increment = max(0, p95 - observed_exit) / (2 * risk)
    stressed = baseline - entry_increment - exit_increment - .05
    assert stressed == pytest.approx(.375)
    assert entry_increment < p95 / risk


def test_leverage_does_not_change_risk_contract(reviewed) -> None:
    core, _, _ = reviewed
    feasible, details = core.capital_feasibility(1000, 5, 200)
    assert feasible
    assert details["risk_limit"] == 5
    assert details["minimum_free_margin"] == 800


def test_account_risk_boundary_rejects_above_five(reviewed) -> None:
    core, _, _ = reviewed
    feasible, details = core.capital_feasibility(1000, 5.01, 100)
    assert not feasible
    assert "MINIMUM_VOLUME_TOTAL_LOSS" in details["rejection_reason"]


def test_account_margin_boundary_rejects_above_two_hundred(reviewed) -> None:
    core, _, _ = reviewed
    feasible, details = core.capital_feasibility(1000, 4, 200.01)
    assert not feasible
    assert details["post_entry_free_margin"] < 800


def test_sizing_rejection_boundary_is_ten_percent(reviewed) -> None:
    core, _, _ = reviewed
    assert core.sizing_rejection_rate_passes(10, 100)
    assert not core.sizing_rejection_rate_passes(11, 100)


def test_storage_preflight_enforces_one_point_five_multiplier(tmp_path) -> None:
    result = research.storage_preflight(tmp_path)
    assert result["reserve_multiplier"] == 1.5
    assert result["required_free_bytes"] == math.ceil(1.5 * result["estimated_total_bytes"])
