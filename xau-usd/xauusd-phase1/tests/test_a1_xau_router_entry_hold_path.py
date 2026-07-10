from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_analyzer():
    name = "analyze_a1_xau_router_entry_hold_path"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


A = _load_analyzer()


def _key(time_msc: int, callback: int = 0, event: int = 0):
    return A.EventKey(time_msc, callback, event)


def _snapshot(source_key, *, router="UPTREND", d1="UP", h4="UP", h4_stack=True, m15="NONE"):
    available = _key(source_key.tester_time_msc - 1)
    return A.SnapshotFeatures(
        source_event_key=source_key,
        observation_event_key=source_key,
        d1_bar_available_key=available,
        h4_bar_available_key=available,
        h1_bar_available_key=available,
        m15_bar_available_key=available,
        m5_bar_available_key=available,
        minimum_bar_shift=1,
        router_state=router,
        d1_structural_direction=d1,
        h4_structural_direction=h4,
        h4_expected_stack=h4_stack,
        h1_close=Decimal("2100"),
        h1_ema50=Decimal("2000"),
        h1_ema20_slope_5_norm=Decimal("0.10"),
        h1_abs_slope_q80=Decimal("0.50"),
        h1_previous_close=Decimal("2100"),
        h1_previous_ema50=Decimal("2000"),
        h1_previous_ema20_slope_5_norm=Decimal("0.10"),
        h1_previous_abs_slope_q80=Decimal("0.50"),
        m15_structure_break=m15,
    )


def _input(**changes):
    signal_key = _key(100, 1, 1)
    entry_key = _key(200, 2, 2)
    exit_key = _key(400, 4, 4)
    item = A.ClassifierInput(
        source_id="h4_d1_long_best_box2_atr80",
        component="R1",
        trade_id="h4_d1_long_best_box2_atr80::run::account::XAUUSD::91001::42",
        direction="LONG",
        expected_regime="UPTREND",
        signal_event_key=signal_key,
        entry_deal_event_key=entry_key,
        exit_deal_event_key=exit_key,
        signal_snapshot=_snapshot(signal_key),
        entry_snapshot=_snapshot(entry_key),
        holding_path=(A.PathObservation(_key(300, 3, 3), _key(299), "UPTREND", 1, True),),
        exit_snapshot=A.PathObservation(_key(390, 3, 4), _key(299), "UPTREND", 1, True),
        path_complete=True,
        original_order_identity_complete=True,
        exit_is_exact_deal_reason_sl=False,
        original_sl_never_modified=True,
    )
    return dataclasses.replace(item, **changes)


def test_primary_class_precedence_and_all_terminal_classes():
    stable = _input()
    wrong = _input(entry_snapshot=_snapshot(stable.entry_deal_event_key, router="SHOCK", d1="UP", h4="DOWN"))
    transition = _input(entry_snapshot=_snapshot(stable.entry_deal_event_key, d1="UP", h4="DOWN"))
    stale = _input(entry_snapshot=_snapshot(stable.entry_deal_event_key, m15="BEARISH"))
    changed = _input(
        holding_path=(A.PathObservation(_key(300, 3, 3), _key(299), "DOWNTREND", 1, True),)
    )
    stopped = _input(exit_is_exact_deal_reason_sl=True, original_sl_never_modified=True)
    invalid = _input(path_complete=False)

    assert A.classify_trade(stable).primary_class is A.PrimaryClass.CORRECT_ENTRY_STABLE_REGIME
    assert A.classify_trade(wrong).primary_class is A.PrimaryClass.WRONG_ROUTER_ENTRY
    assert A.classify_trade(transition).primary_class is A.PrimaryClass.TRANSITION_ENTRY
    assert A.classify_trade(stale).primary_class is A.PrimaryClass.STALE_TREND_ENTRY
    assert A.classify_trade(changed).primary_class is A.PrimaryClass.CORRECT_ENTRY_LATER_REGIME_CHANGE
    assert A.classify_trade(stopped).primary_class is A.PrimaryClass.VALID_LOSS_IN_EXPECTED_REGIME
    assert A.classify_trade(invalid).primary_class is A.PrimaryClass.DATA_OR_TIMESTAMP_ERROR

    wrong_and_transition = dataclasses.replace(
        wrong, entry_snapshot=_snapshot(wrong.entry_deal_event_key, router="SHOCK", d1="UP", h4="DOWN")
    )
    assert A.classify_trade(wrong_and_transition).primary_class is A.PrimaryClass.WRONG_ROUTER_ENTRY


def test_exact_protective_sl_reason_does_not_read_numeric_outcome():
    stopped = _input(exit_is_exact_deal_reason_sl=True, original_sl_never_modified=True)
    classification = A.classify_trade(stopped)
    assert classification.primary_class is A.PrimaryClass.VALID_LOSS_IN_EXPECTED_REGIME
    assert "final_pnl_usd" not in A.CLASSIFIER_INPUT_FIELDS
    assert "final_r" not in A.CLASSIFIER_INPUT_FIELDS


def test_class_lock_is_deterministic_and_trade_order_independent():
    first = _input()
    second = dataclasses.replace(first, trade_id=first.trade_id[:-2] + "43")
    left = A.lock_classifications([first, second])
    right = A.lock_classifications([second, first])
    assert left[1:] == right[1:]
    assert [item.trade_id for item in left[0]] == [item.trade_id for item in right[0]]


def test_full_frozen_contract_recomputes_and_verifies_without_outcome_leakage():
    trades = []
    position = 0
    for source_id, (component, direction, expected_regime, count, frozen_pnl) in A.SOURCE_CONTRACT.items():
        for source_index in range(count):
            position += 1
            base = _input()
            signal = base.signal_snapshot
            entry = base.entry_snapshot
            holding = base.holding_path[0]
            exit_snapshot = base.exit_snapshot
            if expected_regime == "DOWNTREND":
                signal = dataclasses.replace(
                    signal,
                    router_state="DOWNTREND",
                    d1_structural_direction="DOWN",
                    h4_structural_direction="DOWN",
                    h1_close=Decimal("1900"),
                    h1_previous_close=Decimal("1900"),
                )
                entry = dataclasses.replace(
                    entry,
                    router_state="DOWNTREND",
                    d1_structural_direction="DOWN",
                    h4_structural_direction="DOWN",
                    h1_close=Decimal("1900"),
                    h1_previous_close=Decimal("1900"),
                )
                holding = dataclasses.replace(holding, router_state="DOWNTREND")
                exit_snapshot = dataclasses.replace(exit_snapshot, router_state="DOWNTREND")
            item = dataclasses.replace(
                base,
                source_id=source_id,
                component=component,
                direction=direction,
                expected_regime=expected_regime,
                trade_id=f"{source_id}::run::account::XAUUSD::91001::{position}",
                signal_snapshot=signal,
                entry_snapshot=entry,
                holding_path=(holding,),
                exit_snapshot=exit_snapshot,
            )
            trades.append(
                {
                    "classifier_input": A._canonical(item),
                    "outcome": {
                        "final_pnl_usd": str(frozen_pnl if source_index == 0 else Decimal("0")),
                        "final_r": "0",
                    },
                }
            )
    evidence = {
        "schema_version": A.SCHEMA_VERSION,
        "audit_id": A.AUDIT_ID,
        "provenance_id": "unit-test-provenance",
        "reconciliation": {
            "all_valid": True,
            "checks": {name: True for name in A.RECONCILIATION_REQUIRED_CHECKS},
            "details": {},
        },
        "trades": trades,
    }
    result = A.analyze_evidence(evidence)
    assert result["status"] == A.AuditStatus.VALID_NO_CHANGE.value
    assert result["frozen_control_reconciliation"]["pass"] is True
    assert result["class_counts"][A.PrimaryClass.CORRECT_ENTRY_STABLE_REGIME.value] == 678

    verifier_path = ROOT / "scripts" / "verify_a1_xau_router_entry_hold_path.py"
    spec = importlib.util.spec_from_file_location("verify_a1_xau_router_entry_hold_path", verifier_path)
    assert spec and spec.loader
    verifier = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = verifier
    spec.loader.exec_module(verifier)
    assert verifier.verify_analysis(evidence, result) == []

    tampered = json.loads(json.dumps(result))
    tampered["status"] = A.AuditStatus.STALE_ENTRY_V2_JUSTIFIED.value
    assert "analysis does not reproduce from immutable evidence" in verifier.verify_analysis(evidence, tampered)
