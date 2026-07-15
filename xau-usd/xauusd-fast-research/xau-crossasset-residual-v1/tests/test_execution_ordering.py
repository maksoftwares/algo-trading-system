from __future__ import annotations

import pytest

from conftest import exit_parameters, tick_frame
from xau_crossasset_residual.core import ExecutionOrderingError, process_ordered_exit_ticks, trade_result_signature


def execute(rows, **overrides):
    return process_ordered_exit_ticks(tick_frame(rows), **exit_parameters(**overrides))


def test_same_timestamp_target_sequence_before_stop_sequence_exits_target():
    result = execute([(0, "0001", 101.6, 101.7), (0, "0002", 98.8, 98.9)])
    assert result["exit_reason"] == "TARGET" and result["exit_source_sequence"] == "0001"


def test_same_timestamp_stop_sequence_before_target_sequence_exits_stop():
    result = execute([(0, "0001", 98.8, 98.9), (0, "0002", 101.6, 101.7)])
    assert result["exit_reason"] == "STOP" and result["exit_source_sequence"] == "0001"


def test_distinct_source_sequence_is_honored_even_when_input_rows_are_reversed():
    result = execute([(0, "0002", 98.8, 98.9), (0, "0001", 101.6, 101.7)])
    assert result["exit_reason"] == "TARGET" and result["exit_source_sequence"] == "0001"
    assert result["diagnostics"]["NON_MONOTONIC_SOURCE_SEQUENCE"] == 1


def test_missing_source_sequence_with_both_barriers_uses_conservative_stop():
    result = execute([(0, None, 101.6, 101.7), (0, None, 98.8, 98.9)])
    assert result["exit_reason"] == "STOP"
    assert result["exit_ordering_quality"] == "IDENTICAL_TIMESTAMP_STOP_FIRST"
    assert result["diagnostics"]["MISSING_SOURCE_SEQUENCE"] == 1


def test_duplicate_conflicting_sequence_with_both_barriers_uses_conservative_stop():
    result = execute([(0, "same", 101.6, 101.7), (0, "same", 98.8, 98.9)])
    assert result["exit_reason"] == "STOP"
    assert result["diagnostics"]["DUPLICATE_SOURCE_SEQUENCE_CONFLICT"] == 1


def test_unresolved_order_without_both_barriers_fails_closed():
    with pytest.raises(ExecutionOrderingError, match="MISSING_SOURCE_SEQUENCE"):
        execute([(0, None, 100.1, 100.2), (0, None, 100.2, 100.3)])


def test_later_tick_in_same_millisecond_cannot_change_earlier_ordered_exit():
    result = execute([(0, "0001", 101.6, 101.7), (0, "0002", 95.0, 95.1)])
    assert result["exit_reason"] == "TARGET"
    assert result["MAE_R"] == 0.0


def test_mfe_ends_at_target_tick():
    result = execute([(0, "0001", 100.4, 100.5), (1, "0002", 101.6, 101.7), (2, "0003", 105.0, 105.1)])
    assert result["exit_reason"] == "TARGET"
    assert result["MFE_R"] == pytest.approx(1.6)


def test_mae_ends_at_stop_tick():
    result = execute([(0, "0001", 99.5, 99.6), (1, "0002", 98.8, 98.9), (2, "0003", 90.0, 90.1)])
    assert result["exit_reason"] == "STOP"
    assert result["MAE_R"] == pytest.approx(-1.2)


def test_mfe_and_mae_exclude_later_same_timestamp_ticks():
    result = execute([(0, "0001", 101.6, 101.7), (0, "0002", 80.0, 80.1), (0, "0003", 120.0, 120.1)])
    assert result["MFE_R"] == pytest.approx(1.6)
    assert result["MAE_R"] == 0.0


def test_modifying_post_exit_ticks_cannot_change_trade_signature():
    base = execute([(0, "0001", 101.6, 101.7), (1, "0002", 100.0, 100.1)])
    changed = execute([(0, "0001", 101.6, 101.7), (1, "0002", 1.0, 200.0), (2, "0003", 500.0, 501.0)])
    assert trade_result_signature(base) == trade_result_signature(changed)


def test_short_execution_uses_ask_and_source_order():
    result = execute([(0, "0001", 100.0, 98.4), (0, "0002", 100.0, 101.2)], direction="SHORT", stop=101.0, target=98.5)
    assert result["exit_reason"] == "TARGET"
