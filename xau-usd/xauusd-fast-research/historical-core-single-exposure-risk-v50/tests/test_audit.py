from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.audit import account_sizing


def test_account_sizing_passes_buffered_reference_case() -> None:
    result = account_sizing(
        335.0,
        {
            "current_equity_dollars": 3000.0,
            "maximum_equity_drawdown_fraction": 0.15,
            "capital_safety_buffer_multiple": 1.25,
            "reference_lot": 0.01,
            "broker_minimum_lot": 0.01,
            "broker_lot_step": 0.01,
        },
    )
    assert result["buffered_drawdown_dollars"] == pytest.approx(418.75)
    assert result["r1_lane_fits_buffered_drawdown_gate"] is True


def test_account_sizing_rejects_drawdown_above_buffered_limit() -> None:
    result = account_sizing(
        400.0,
        {
            "current_equity_dollars": 3000.0,
            "maximum_equity_drawdown_fraction": 0.15,
            "capital_safety_buffer_multiple": 1.25,
            "reference_lot": 0.01,
            "broker_minimum_lot": 0.01,
            "broker_lot_step": 0.01,
        },
    )
    assert result["r1_lane_fits_buffered_drawdown_gate"] is False


def test_account_sizing_rejects_unexpressible_broker_minimum() -> None:
    result = account_sizing(
        335.0,
        {
            "current_equity_dollars": 3000.0,
            "maximum_equity_drawdown_fraction": 0.15,
            "capital_safety_buffer_multiple": 1.25,
            "reference_lot": 0.01,
            "broker_minimum_lot": 0.02,
            "broker_lot_step": 0.01,
        },
    )
    assert result["broker_can_express_safe_lot"] is False
    assert result["r1_lane_fits_buffered_drawdown_gate"] is False


def test_config_locks_single_position_without_parameter_grid() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads(
        (root / "config" / "historical_core_single_exposure_risk_v50.json").read_text(
            encoding="utf-8"
        )
    )
    policy = config["comparison_policies"]["V50_SINGLE_POSITION"]
    assert policy["maximum_concurrent_positions"] == 1
    assert policy["maximum_entries_per_utc_day"] == 1
    assert config["research_controls"]["parameter_search_count"] == 0


def test_preregistration_disclaims_untouched_alpha() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "makes no untouched-alpha claim" in text
    assert "one open R1" in text
