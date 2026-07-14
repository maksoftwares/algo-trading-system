from __future__ import annotations

import json
from pathlib import Path


def test_authorized_period_symbol_and_router_hysteresis_are_frozen() -> None:
    config_path = Path(__file__).resolve().parents[1] / "config" / "multiregime_fast_discovery_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["symbol"] == "XAUUSD"
    assert config["requested_start"] == "2016-07-01T00:00:00Z"
    assert config["requested_end_exclusive"] == "2026-07-01T00:00:00Z"
    assert config["router"]["entry_consecutive"] == 2
    assert config["router"]["exit_consecutive"] == 2
    assert set(config["strategies"]) == {"trend", "compression", "failed_auction"}


def test_result_uses_one_approved_machine_classification() -> None:
    result_path = Path(__file__).resolve().parents[1] / "outputs" / "MULTIREGIME_FAST_DISCOVERY_RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    allowed = {
        "MULTIREGIME_PORTFOLIO_CONFIRMATION_CANDIDATE", "POSITIVE_BUT_COMMERCIALLY_UNDERPOWERED",
        "NO_DEFENSIBLE_MULTIREGIME_EDGE", "MULTIREGIME_V1_DATA_INCOMPLETE_NO_ADVANCEMENT",
        "XAUUSD_1000_ACCOUNT_CONTRACT_GRANULARITY_INADEQUATE", "EVIDENCE_INVALID",
    }
    assert result["decision"] in allowed
