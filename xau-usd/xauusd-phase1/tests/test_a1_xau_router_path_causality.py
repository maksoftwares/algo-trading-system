from __future__ import annotations

import dataclasses
from decimal import Decimal

from test_a1_xau_router_entry_hold_path import A, _input, _key, _snapshot


def test_type7_q80_uses_exact_prior_distribution_rule():
    values = [Decimal(index) for index in range(252)]
    assert A.type7_quantile(values, "0.80") == Decimal("200.80")


def test_bar_zero_and_future_snapshot_fail_closed():
    base = _input()
    bar_zero = dataclasses.replace(base.entry_snapshot, minimum_bar_shift=0)
    future = dataclasses.replace(
        base.entry_snapshot,
        observation_event_key=_key(base.entry_deal_event_key.tester_time_msc + 1),
    )
    assert A.classify_trade(dataclasses.replace(base, entry_snapshot=bar_zero)).primary_class is A.PrimaryClass.DATA_OR_TIMESTAMP_ERROR
    assert A.classify_trade(dataclasses.replace(base, entry_snapshot=future)).primary_class is A.PrimaryClass.DATA_OR_TIMESTAMP_ERROR


def test_holding_path_requires_strict_monotone_open_interval():
    base = _input()
    at_exit = A.PathObservation(base.exit_deal_event_key, _key(399), "DOWNTREND", 1, True)
    result = A.classify_trade(dataclasses.replace(base, holding_path=(at_exit,)))
    assert result.primary_class is A.PrimaryClass.DATA_OR_TIMESTAMP_ERROR
    assert "holding observation is outside open interval" in result.errors


def test_same_millisecond_change_counts_only_when_event_order_precedes_exit():
    base = _input(holding_path=())
    before_exit = A.PathObservation(_key(400, 4, 3), _key(399), "DOWNTREND", 1, True)
    after_exit = A.PathObservation(_key(400, 4, 5), _key(399), "DOWNTREND", 1, False)
    changed = A.classify_trade(dataclasses.replace(base, exit_snapshot=before_exit))
    invalid = A.classify_trade(dataclasses.replace(base, exit_snapshot=after_exit))
    assert changed.primary_class is A.PrimaryClass.CORRECT_ENTRY_LATER_REGIME_CHANGE
    assert invalid.primary_class is A.PrimaryClass.DATA_OR_TIMESTAMP_ERROR
