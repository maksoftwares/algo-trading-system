from __future__ import annotations

import json
from pathlib import Path

import pytest

from ml.a3_meta_v1.dukascopy_m15_expansion_ranker_discovery import _validate_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ml/a3_ml_dukascopy_m15_expansion_ranker_discovery_v1.json"


def test_discovery_contract_closes_all_post_development_outcomes() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _validate_contract(contract)
    assert contract["windows"]["development_evaluation_end_exclusive_utc"] == "2020-07-01T00:00:00Z"
    assert contract["windows"]["outcomes_after_2020_07_authorized"] is False
    assert contract["authorization"]["strategy_promotion_authorized"] is False
    assert contract["authorization"]["broker_action_authorized"] is False


def test_discovery_contract_rejects_later_outcome_access() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["windows"]["development_evaluation_end_exclusive_utc"] = "2021-07-01T00:00:00Z"
    with pytest.raises(ValueError, match="boundary"):
        _validate_contract(contract)


def test_discovery_contract_rejects_retention_search() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["train_score_top_fractions"].append(0.10)
    with pytest.raises(ValueError, match="retention"):
        _validate_contract(contract)
