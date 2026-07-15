from __future__ import annotations

import json
from pathlib import Path

from xau_crossasset_residual.core import (
    BASE_COMMIT, BASE_PARENT, BASE_TREE, BRANCH, COMMIT_MESSAGE, INSTRUMENTS, PHASE,
    SOURCE_PHASE, classify, no_search_tokens,
)

LANE = Path(__file__).resolve().parents[1]


def test_exact_correction_repository_identity_constants():
    assert BRANCH == "codex/xau-crossasset-residual-v1-review-corrections"
    assert BASE_COMMIT == "0722a66a41cf7a3d109a4bc129f8f469b80ca022"
    assert BASE_TREE == "89dbd09a45c85e98a67b3a1487ea87730ce7d172"
    assert BASE_PARENT == "c21c98711e21f3e2e4d705d64ac8cf1391aca228"
    assert COMMIT_MESSAGE == "fix: correct XAU residual V1 research evidence"


def test_correction_and_reviewed_phase_identities_are_distinct():
    assert PHASE == "XAU_CROSSASSET_RESIDUAL_V1_REVIEW_CORRECTIONS"
    assert SOURCE_PHASE == "XAU_CROSSASSET_RESIDUAL_DIRECTIONAL_SPECIALISTS_V1"


def test_frozen_instrument_contract_is_exact():
    assert INSTRUMENTS == {"XAUUSD": "XAU-USD", "XAGUSD": "XAG-USD", "EURUSD": "EUR-USD", "USDJPY": "USD-JPY"}


def test_frozen_configuration_has_zero_search_budgets():
    config = json.loads((LANE / "config" / "frozen_config.json").read_text(encoding="utf-8"))
    assert config["model"] == {"method": "OLS", "intercept": True, "window": 3000, "minimum_observations": 2500, "condition_number_limit": 1000000, "residual_window": 500}
    assert config["episodes"] == {"long_threshold": -2.5, "short_threshold": 2.5, "maximum_hours": 6}
    assert (config["stop_atr"], config["target_r"], config["maximum_hold_minutes"]) == (1.25, 1.5, 90)
    assert config["parameter_search_count"] == config["feature_search_count"] == config["model_search_count"] == config["router_training_count"] == 0


def test_source_contains_no_optimizer_mt5_or_order_api_calls():
    source = "\n".join(path.read_text(encoding="utf-8") for path in (LANE / "src").rglob("*.py"))
    assert no_search_tokens(source)
    assert "place_order" not in source.lower()


def test_positive_and_rejection_classification_strings_are_exact():
    long_id = "XAU_NEGATIVE_RESIDUAL_LONG_SPECIALIST"
    short_id = "XAU_POSITIVE_RESIDUAL_SHORT_SPECIALIST"
    assert classify(True, True, [long_id], [long_id]) == "XAU_CROSSASSET_RESIDUAL_V1_LONG_SPECIALIST_CONFIRMATION_REQUIRED"
    assert classify(True, True, [short_id], [short_id]) == "XAU_CROSSASSET_RESIDUAL_V1_SHORT_SPECIALIST_CONFIRMATION_REQUIRED"
    assert classify(True, True, [long_id, short_id], [long_id, short_id], True) == "XAU_CROSSASSET_RESIDUAL_V1_BIDIRECTIONAL_SPECIALIST_CONFIRMATION_REQUIRED"
    assert classify(True, True, []) == "XAU_CROSSASSET_RESIDUAL_V1_NO_DIRECTIONAL_SURVIVOR"
