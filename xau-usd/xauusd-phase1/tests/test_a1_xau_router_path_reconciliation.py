from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from test_a1_xau_router_entry_hold_path import A, _input


def test_namespaced_trade_identity_is_required_and_unique():
    invalid = dataclasses.replace(_input(), trade_id="42")
    assert A.classify_trade(invalid).primary_class is A.PrimaryClass.DATA_OR_TIMESTAMP_ERROR
    with pytest.raises(A.AuditEvidenceError, match="duplicate trade ID"):
        A.lock_classifications([_input(), _input()])


def test_decimal_reconciliation_helpers_do_not_use_binary_float():
    rows = [{"value": "0.10"}, {"value": "0.20"}]
    assert A._sum_decimal(rows, "value") == Decimal("0.30")


def test_status_precedence_fails_closed_before_performance_gates():
    valid = A.classify_trade(_input())
    wrong_item = dataclasses.replace(
        _input(), entry_snapshot=dataclasses.replace(_input().entry_snapshot, router_state="SHOCK")
    )
    wrong = A.classify_trade(wrong_item)
    assert A.select_status(
        evidence_valid=False, assignments=[valid], stale_pass=True, holding_pass=True
    ) is A.AuditStatus.INVALID_EVIDENCE
    assert A.select_status(
        evidence_valid=True, assignments=[wrong], stale_pass=True, holding_pass=True
    ) is A.AuditStatus.WRONG_ENTRY_DEFECT
    assert A.select_status(
        evidence_valid=True, assignments=[valid], stale_pass=True, holding_pass=True
    ) is A.AuditStatus.STALE_ENTRY_V2_JUSTIFIED
