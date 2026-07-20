from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.policy import filter_broker_expressible_core


ROOT = Path(__file__).resolve().parents[1]


def test_fractional_r5_is_rejected_without_rounding() -> None:
    core = pd.DataFrame(
        [
            {
                "trade_id": "full",
                "specialist_id": "R5_TRANSITION",
                "signal_time": "2026-01-01T00:00:00Z",
                "entry_time": "2026-01-01T00:00:00Z",
                "exit_time": "2026-01-01T01:00:00Z",
                "sleeve_id": "V58_NATIVE_CORE",
            },
            {
                "trade_id": "fractional",
                "specialist_id": "R5_TRANSITION",
                "signal_time": "2026-01-02T00:00:00Z",
                "entry_time": "2026-01-02T00:00:00Z",
                "exit_time": "2026-01-02T01:00:00Z",
                "sleeve_id": "V58_NATIVE_CORE",
            },
        ]
    )
    router = pd.DataFrame(
        [
            {"candidate_id": "full", "attempt_no": 7, "risk_weight": 1.0},
            {"candidate_id": "fractional", "attempt_no": 7, "risk_weight": 0.5},
        ]
    )
    settings = {
        "r5_specialist_id": "R5_TRANSITION",
        "r5_router_attempt": 7,
        "full_weight": 1.0,
        "weight_absolute_tolerance": 1e-12,
        "expected_r5_rows": 2,
        "expected_full_weight_rows": 1,
        "expected_fractional_rows": 1,
    }
    kept, rejected, audit = filter_broker_expressible_core(core, router, settings)
    assert list(kept["trade_id"]) == ["full"]
    assert list(rejected["trade_id"]) == ["fractional"]
    assert audit["fractional_rounding_used"] is False


def test_config_retains_one_trade_and_drawdown_gates() -> None:
    config = json.loads(
        (ROOT / "config" / "one_trade_per_day_broker_core_v59.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["gates"]["minimum_combined_trades_per_weekday"] == 1.0
    assert config["account"]["maximum_combined_closed_drawdown_usd"] == 300.0
    assert config["research_controls"]["fractional_rounding_authorized"] is False


def test_preregistration_disclaims_execution() -> None:
    text = (ROOT / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "No Python serving, EA, demo, live" in text
    assert "reject, rather than round up" in text.lower()
