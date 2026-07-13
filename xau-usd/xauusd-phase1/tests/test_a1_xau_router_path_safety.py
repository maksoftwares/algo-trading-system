from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from test_a1_xau_router_entry_hold_path import A, _input


ROOT = Path(__file__).resolve().parents[1]


def test_classifier_schema_structurally_excludes_outcome_fields():
    assert A.CLASSIFIER_INPUT_FIELDS.isdisjoint(A.PROHIBITED_CLASSIFIER_FIELDS)
    assert A.CLASSIFIER_SCHEMA_FIELD_NAMES.isdisjoint(A.PROHIBITED_CLASSIFIER_FIELDS)
    for field in ("final_r", "final_pnl_usd", "mfe_r", "mae_r", "unrealized_r_at_change", "post_change_r"):
        assert field not in A.CLASSIFIER_INPUT_FIELDS


def test_prohibited_outcome_field_is_rejected_not_silently_ignored():
    payload = A._canonical(_input())
    payload["final_pnl_usd"] = "999999.99"
    with pytest.raises(A.AuditEvidenceError, match="schema mismatch"):
        A.ClassifierInput.from_dict(payload)


def test_classification_is_invariant_to_separate_outcome_replacement():
    item = _input(exit_is_exact_deal_reason_sl=True)
    before = A.classify_trade(item)
    outcome_a = {"final_pnl_usd": "-100.00", "final_r": "-1.0", "mfe_r": "0.1"}
    outcome_b = {"final_pnl_usd": "100000.00", "final_r": "999", "mfe_r": "1000"}
    assert outcome_a != outcome_b
    assert A.classify_trade(item) == before


def test_audit_analyzer_and_verifier_have_no_broker_action_surface():
    forbidden_imports = {"subprocess", "socket", "requests", "MetaTrader5"}
    forbidden_calls = {"order_send", "OrderSend", "WebRequest", "ShellExecuteW", "Popen", "run"}
    for name in ("analyze_a1_xau_router_entry_hold_path.py", "verify_a1_xau_router_entry_hold_path.py"):
        tree = ast.parse((ROOT / "scripts" / name).read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        calls = {
            node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
        }
        assert imported.isdisjoint(forbidden_imports)
        assert calls.isdisjoint(forbidden_calls)
