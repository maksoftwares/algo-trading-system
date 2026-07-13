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
