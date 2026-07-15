from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pandas as pd

from xau_continuation import research


def test_reviewed_engine_is_patched_to_continuation_ids(reviewed) -> None:
    core, pipeline, _ = reviewed
    assert core.LONG_ID == pipeline.LONG_ID == research.LONG_ID
    assert core.SHORT_ID == pipeline.SHORT_ID == research.SHORT_ID


def test_reviewed_engine_uses_independent_stage_a_months(reviewed) -> None:
    _, pipeline, _ = reviewed
    assert pipeline.months() == research.month_keys()
    assert max(pipeline.months()) == "2021-06"


def test_convergence_schedule_is_disabled(reviewed) -> None:
    _, pipeline, _ = reviewed
    candidates = [{"excursion_episode_id": "LONG-1"}]
    schedule = pipeline.convergence_times(pd.DataFrame(), candidates)
    assert schedule["LONG-1"][0] == 2**63 - 1


def test_model_contract_is_single_specification(lane: Path) -> None:
    config = json.loads((lane / "config" / "frozen_config.json").read_text())
    assert config["model"] == {"method": "OLS", "intercept": True, "window": 3000, "minimum_observations": 2500, "condition_number_limit": 1000000, "residual_window": 500}


def test_stop_target_and_holding_contract_are_frozen(lane: Path) -> None:
    config = json.loads((lane / "config" / "frozen_config.json").read_text())
    assert (config["stop_atr"], config["target_r"], config["maximum_hold_minutes"]) == (1.25, 1.5, 90)


def test_trading_hour_contract_is_frozen(lane: Path) -> None:
    config = json.loads((lane / "config" / "frozen_config.json").read_text())
    assert config["entry_window_utc"] == [6, 18]
    assert config["force_close_hour_utc"] == 20


def test_unsafe_filter_contract_is_prior_only(lane: Path) -> None:
    config = json.loads((lane / "config" / "frozen_config.json").read_text())
    assert config["h1_atr_reference"] == 500
    assert config["h1_atr_reject_percentile"] == 95
    assert config["spread_reject_percentile"] == 99


def test_stress_contract_has_separate_penalties(lane: Path) -> None:
    config = json.loads((lane / "config" / "frozen_config.json").read_text())
    assert config["ordinary_stress_fixed_r"] == .05
    assert config["broker_transfer_r"] == .15
    assert config["ordinary_stress_fixed_r"] != config["broker_transfer_r"]


def test_canonical_bytes_are_key_order_independent() -> None:
    left = research.canonical_bytes({"b": 2, "a": 1})
    right = research.canonical_bytes({"a": 1, "b": 2})
    assert left == right
    assert hashlib.sha256(left).hexdigest() == hashlib.sha256(right).hexdigest()


def test_required_outputs_use_continuation_namespace() -> None:
    outputs = research.required_outputs()
    assert all(name.startswith("XAU_CONTINUATION_") for name in outputs)
    assert len(outputs) == len(set(outputs))


def test_result_report_and_manifest_are_mandatory() -> None:
    outputs = set(research.required_outputs())
    assert {"XAU_CONTINUATION_RESULT.md", "XAU_CONTINUATION_RESULT.json", "XAU_CONTINUATION_RUN_MANIFEST.json"}.issubset(outputs)


def test_signal_and_trade_ledgers_are_mandatory() -> None:
    outputs = set(research.required_outputs())
    assert "XAU_CONTINUATION_SIGNAL_LEDGER.csv" in outputs
    assert "XAU_CONTINUATION_TRADE_LEDGER.csv" in outputs


def test_quarantine_audit_is_mandatory() -> None:
    assert "XAU_CONTINUATION_QUARANTINE_AUDIT.json" in research.required_outputs()


def test_determinism_evidence_is_mandatory() -> None:
    outputs = set(research.required_outputs())
    assert "XAU_CONTINUATION_MODEL_DETERMINISM.json" in outputs
    assert "XAU_CONTINUATION_TEST_COVERAGE.json" in outputs


def test_capability_profile_is_mandatory() -> None:
    assert "XAU_CONTINUATION_CAPABILITY_PROFILE.csv" in research.required_outputs()


def test_primary_no_survivor_classification_is_exact() -> None:
    assert research.PRIMARY_NO_SURVIVOR == "XAU_RESIDUAL_CONTINUATION_V1_NO_DIRECTIONAL_SURVIVOR"


def test_evidence_invalid_classification_is_exact() -> None:
    assert research.PRIMARY_INVALID == "XAU_RESIDUAL_CONTINUATION_V1_EVIDENCE_INVALID"


def test_no_placeholder_parametrized_tests_exist(lane: Path) -> None:
    for path in (lane / "tests").glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                assert node.attr != "parametrize"


def test_every_test_function_contains_assertion_or_expected_exception(lane: Path) -> None:
    for path in (lane / "tests").glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                has_assert = any(isinstance(child, ast.Assert) for child in ast.walk(node))
                has_raises = any(isinstance(child, ast.Attribute) and child.attr == "raises" for child in ast.walk(node))
                assert has_assert or has_raises, f"{path.name}:{node.name} lacks a substantive assertion"


def test_stage_b_periods_are_disjoint_from_quarantine(lane: Path) -> None:
    config = json.loads((lane / "config" / "frozen_config.json").read_text())
    assert config["validation"][0] == config["hypothesis_generation_quarantine"][1]
    assert config["stage_a"][1] == config["hypothesis_generation_quarantine"][0]
