from __future__ import annotations

import json
from pathlib import Path

import pytest

from ml.a3_meta_v1.external_candidate_ranker import (
    ExternalCandidateRankerError,
    _development_gates,
    _validate_contract,
    _window,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ml/a3_ml_external_candidate_ranker_v1.json"


def test_ranker_contract_excludes_outcome_features() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _validate_contract(contract)
    assert "stress_net_r" not in contract["features"]
    assert "mfe_r" not in contract["features"]
    assert "mae_r" not in contract["features"]


def test_ranker_rejects_future_outcome_feature() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["features"].append("stress_net_r")
    with pytest.raises(ExternalCandidateRankerError, match="outcome-derived"):
        _validate_contract(contract)


def test_chronological_window_is_left_closed_right_open() -> None:
    rows = [
        {"decision_time_ms": 1000, "candidate_id": "a"},
        {"decision_time_ms": 2000, "candidate_id": "b"},
        {"decision_time_ms": 3000, "candidate_id": "c"},
    ]
    start = "1970-01-01T00:00:01Z"
    end = "1970-01-01T00:00:03Z"
    assert [row["candidate_id"] for row in _window(rows, start, end)] == ["a", "b"]


def test_development_gate_requires_both_predictive_metrics() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    economic = {
        "trades": 100,
        "trades_per_source_day": 0.5,
        "stress_profit_factor": 1.3,
        "average_stress_r": 0.1,
        "positive_month_share": 0.7,
        "maximum_closed_drawdown_r": 10.0,
        "top10_winners_removed_net_r": 1.0,
    }
    checks = _development_gates(
        {"auc": 0.60, "spearman": 0.0}, economic, contract["development_gates"]
    )
    assert checks["minimum_auc"]
    assert not checks["minimum_spearman"]
