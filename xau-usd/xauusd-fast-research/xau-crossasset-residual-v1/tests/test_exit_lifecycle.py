from __future__ import annotations

from conftest import BASE_TS, exit_parameters, model_rows, tick_frame
from xau_crossasset_residual.core import process_ordered_exit_ticks
from xau_crossasset_residual.pipeline import convergence_times


def execute(rows, **overrides):
    return process_ordered_exit_ticks(tick_frame(rows), **exit_parameters(**overrides))


def test_convergence_signal_uses_completed_bar_time():
    model = model_rows([-2.6, -1.0, 0.1])
    candidate = {"candidate_bar_ms": BASE_TS, "UTC_date": "2024-01-01", "direction": "LONG", "excursion_episode_id": "L1"}
    assert convergence_times(model, [candidate])["L1"][0] == BASE_TS + 2 * 300_000 + 300_000


def test_convergence_executes_on_first_tick_at_or_after_completion():
    result = execute([(0, "1", 100.0, 100.1), (601_000, "2", 100.2, 100.3), (602_000, "3", 100.3, 100.4)], convergence_ms=BASE_TS + 600_000, convergence_z=.1)
    assert int(result["exit_tick"]["timestamp_msc"]) == BASE_TS + 601_000
    assert result["exit_reason"] == "RESIDUAL_CONVERGENCE"


def test_stop_before_convergence_execution_wins():
    result = execute([(500_000, "1", 98.9, 99.0), (600_000, "2", 100.0, 100.1)], convergence_ms=BASE_TS + 600_000, convergence_z=.1)
    assert result["exit_reason"] == "STOP"


def test_target_before_convergence_execution_wins():
    result = execute([(500_000, "1", 101.6, 101.7), (600_000, "2", 100.0, 100.1)], convergence_ms=BASE_TS + 600_000, convergence_z=.1)
    assert result["exit_reason"] == "TARGET"


def test_expiry_uses_first_valid_tick_at_or_after_ninety_minutes():
    expiry = BASE_TS + 90 * 60_000
    result = execute([(89 * 60_000, "1", 100.0, 100.1), (90 * 60_000 + 2_000, "2", 100.2, 100.3)], expiry_ms=expiry)
    assert int(result["exit_tick"]["timestamp_msc"]) == expiry + 2_000
    assert result["exit_reason"] == "NINETY_MINUTE_EXPIRY"


def test_stop_on_earlier_tick_wins_over_expiry():
    expiry = BASE_TS + 90 * 60_000
    result = execute([(89 * 60_000, "1", 98.9, 99.0), (90 * 60_000, "2", 100.0, 100.1)], expiry_ms=expiry)
    assert result["exit_reason"] == "STOP"


def test_force_close_uses_first_tick_at_or_after_20_utc():
    force = BASE_TS + 20 * 3_600_000
    result = execute([(19 * 3_600_000, "1", 100.0, 100.1), (20 * 3_600_000 + 1_000, "2", 100.2, 100.3)], force_ms=force)
    assert int(result["exit_tick"]["timestamp_msc"]) == force + 1_000
    assert result["exit_reason"] == "SAME_DAY_FORCE_CLOSE"


def test_no_overnight_carry_returns_no_exit_when_same_day_tick_is_missing():
    result = execute([(0, "1", 100.0, 100.1), (24 * 3_600_000, "2", 100.2, 100.3)])
    assert result is None


def test_missing_same_day_exit_is_not_synthesized():
    assert execute([(0, "1", 100.0, 100.1)]) is None
