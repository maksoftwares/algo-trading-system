from __future__ import annotations

import json
from pathlib import Path

from eurusd_regime_specialists.crosspair_strength_daily import (
    CONFIG_PATH,
    vote_direction,
)


def test_contract_is_frozen_and_excludes_eurusd_predictor() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["status"] == "LOCKED_BEFORE_EURUSD_OUTCOME_INSPECTION"
    assert config["signal"]["eurusd_predictor_prohibited"] is True
    assert "EURUSD" not in config["signal"]["predictor_symbols"]
    assert config["execution"]["nominal_reward_risk"] == 1.5
    assert config["source_only_census"]["candidates"] == 2594


def test_three_of_four_vote_direction() -> None:
    assert vote_direction([1, 1, 1, -1]) == 1
    assert vote_direction([-1, -1, -1, 1]) == -1
    assert vote_direction([1, 1, -1, -1]) == 0
    assert vote_direction([1, 1, 1, 1]) == 1
    assert vote_direction([-1, -1, -1, -1]) == -1
