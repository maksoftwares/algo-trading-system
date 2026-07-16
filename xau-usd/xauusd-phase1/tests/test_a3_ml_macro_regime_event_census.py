from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ml.a3_meta_v1.dukascopy_confirmed_event_specialists import BAR_WIDTH_MS
from ml.a3_meta_v1.macro_regime_event_census import (
    H1_WIDTH_MS,
    _classification,
    _label_event,
    aggregate_h1,
    attach_causal_macro,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/ml/a3_ml_macro_regime_event_census_v1.json"
BASE_MS = int(pd.Timestamp("2017-01-02T00:00:00Z").timestamp() * 1000)


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _m5_row(index: int, **overrides: float | int | str) -> dict:
    row = {
        "timestamp_ms": BASE_MS + index * BAR_WIDTH_MS,
        "mid_open": 100.0,
        "mid_high": 100.5,
        "mid_low": 99.5,
        "mid_close": 100.2,
        "bid_open": 99.7,
        "bid_high": 100.2,
        "bid_low": 99.2,
        "bid_close": 99.9,
        "ask_open": 100.3,
        "ask_high": 100.8,
        "ask_low": 99.8,
        "ask_close": 100.5,
        "tick_spread_mean": 0.6,
        "tick_spread_last": 0.6,
        "tick_spread_max": 0.7,
        "tick_imbalance_5m": 0.1,
        "quote_intensity_ratio": 1.0,
    }
    row.update(overrides)
    return row


def _event(**overrides: float | int | str) -> dict:
    event = {
        "event_id": "event-1",
        "family_id": "macro_shock_h1_continuation_v1",
        "direction": "LONG",
        "split": "train",
        "decision_time_utc": "2017-01-02T01:00:00.000Z",
        "decision_timestamp_ms": BASE_MS + H1_WIDTH_MS,
        "source_last_index": 11,
        "macro_cutoff_date": "2016-12-31",
        "macro_latest_source_date": "2016-12-30",
        "atr": 5.0,
        "signal_high": 102.0,
        "signal_low": 98.0,
        "stop_atr": 1.75,
        "structural_buffer_atr": 0.0,
        "target_r": 1.5,
        "maximum_hold_hours": 1,
    }
    event.update(overrides)
    return event


def test_contract_is_research_only_and_has_eight_hypotheses() -> None:
    contract = _contract()
    validate_contract(contract)
    assert contract["selection"]["maximum_hypotheses"] == 8
    assert contract["selection"]["parameter_grid_search_authorized"] is False
    assert contract["research_controls"]["model_training_authorized"] is False
    assert contract["authorization"]["broker_action_authorized"] is False


def test_h1_aggregation_requires_twelve_contiguous_m5_bars() -> None:
    contract = _contract()
    rows = [_m5_row(index) for index in range(12)]
    result = aggregate_h1(pd.DataFrame(rows), contract)
    assert len(result) == 1
    assert result.iloc[0]["source_last_index"] == 11
    assert result.iloc[0]["decision_timestamp_ms"] == BASE_MS + H1_WIDTH_MS
    rows[-1]["timestamp_ms"] += BAR_WIDTH_MS
    assert aggregate_h1(pd.DataFrame(rows), contract).empty


def test_macro_attachment_enforces_two_day_cutoff() -> None:
    contract = _contract()
    h1 = pd.DataFrame(
        {
            "decision_timestamp_ms": [
                int(pd.Timestamp("2020-01-10T12:00:00Z").timestamp() * 1000)
            ]
        }
    )
    macro = pd.DataFrame(
        {
            "macro_cutoff_date": pd.to_datetime(["2020-01-08"], utc=True),
            "DFII10": [1.0],
            "DFII10_change_5": [-0.1],
            "DFII10_source_date": pd.to_datetime(["2020-01-08"], utc=True),
            "DGS2": [1.5],
            "DGS2_source_date": pd.to_datetime(["2020-01-08"], utc=True),
            "DGS10": [1.8],
            "DGS10_source_date": pd.to_datetime(["2020-01-08"], utc=True),
            "DTWEXBGS": [100.0],
            "DTWEXBGS_pct_change_5": [-0.2],
            "DTWEXBGS_source_date": pd.to_datetime(["2020-01-08"], utc=True),
            "curve_2s10": [0.3],
            "breakeven_10y": [0.8],
            "macro_shock_score": [2.0],
        }
    )
    result = attach_causal_macro(h1, macro, contract)
    assert str(result.iloc[0]["macro_cutoff_date"].date()) == "2020-01-08"
    assert bool(result.iloc[0]["macro_lag_enforced"])
    assert bool(result.iloc[0]["macro_long_aligned"])


def test_label_uses_next_m5_ask_and_broker_cost_floor() -> None:
    contract = _contract()
    rows = [_m5_row(index) for index in range(24)]
    for index in range(12, 24):
        rows[index].update(
            bid_open=100.0,
            ask_open=100.5,
            bid_low=99.5,
            bid_high=120.0,
            bid_close=110.0,
        )
    label = _label_event(pd.DataFrame(rows), _event(), contract)
    assert label["status"] == "RESOLVED"
    assert label["entry_price"] == 100.5
    assert label["broker_spread_floor"] == 0.75
    assert label["stressed_entry_cost_price"] == pytest.approx(1.05)
    assert label["stop_distance"] == pytest.approx(8.75)
    assert label["exit_reason"] == "TARGET"


def test_label_rejects_risk_over_fifty_dollars() -> None:
    contract = _contract()
    rows = [_m5_row(index) for index in range(24)]
    label = _label_event(
        pd.DataFrame(rows),
        _event(atr=40.0, stop_atr=1.75),
        contract,
    )
    assert label["status"] == "INELIGIBLE"
    assert label["exit_reason"] == "INITIAL_RISK_USD"


def test_label_rejects_spread_cost_over_fifteen_percent_of_risk() -> None:
    contract = _contract()
    rows = [_m5_row(index) for index in range(24)]
    rows[12].update(bid_open=100.0, ask_open=102.0)
    label = _label_event(pd.DataFrame(rows), _event(), contract)
    assert label["status"] == "INELIGIBLE"
    assert label["exit_reason"] == "STRESSED_ENTRY_COST_R"


def test_same_m5_stop_target_collision_is_stop_first() -> None:
    contract = _contract()
    rows = [_m5_row(index) for index in range(24)]
    rows[12].update(
        bid_open=100.0,
        ask_open=100.5,
        bid_low=90.0,
        bid_high=120.0,
    )
    label = _label_event(pd.DataFrame(rows), _event(), contract)
    assert label["status"] == "RESOLVED"
    assert label["exit_reason"] == "STOP"
    assert label["exit_price"] == pytest.approx(91.75)


def test_firewall_classification_cannot_be_rescued_by_exam() -> None:
    quality = {"quality": True}
    survivors = {
        "train": [],
        "validation": ["candidate"],
        "internal_test": ["candidate"],
        "exam": ["candidate"],
    }
    assert (
        _classification(quality, survivors)
        == "MACRO_REGIME_EVENT_CENSUS_NO_TRAIN_SURVIVOR"
    )
