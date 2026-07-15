from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.a3_meta_v1.dukascopy_microstructure_regime import (
    BAR_WIDTH_MS,
    _aggregate_tick_arrays,
    _candidate_features,
    _portfolio_select,
    _simulate_trade,
    _validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ml/a3_ml_dukascopy_microstructure_regime_v1.json"


def test_contract_is_research_only_and_chronologically_firewalled() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _validate_contract(contract)
    authorization = contract["authorization"]
    assert authorization["internal_test_requires_validation_pass"] is True
    assert authorization["exam_requires_internal_test_pass"] is True
    assert authorization["python_demo_predictions_authorized"] is False
    assert authorization["ea_consumption_authorized"] is False
    assert authorization["broker_action_authorized"] is False


def test_contract_rejects_weakened_firewall() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["authorization"]["exam_requires_internal_test_pass"] = False
    with pytest.raises(ValueError, match="firewall"):
        _validate_contract(contract)


def test_tick_aggregation_uses_only_ticks_inside_each_completed_bucket() -> None:
    timestamps = np.array([1_000, 2_000, 299_000, 301_000, 302_000], dtype=np.int64)
    bid = np.array([100.0, 100.1, 100.0, 200.0, 199.9])
    ask = bid + 0.2
    bid_volume = np.array([3.0, 4.0, 3.0, 1.0, 1.0])
    ask_volume = np.array([1.0, 1.0, 1.0, 3.0, 4.0])
    result = _aggregate_tick_arrays(timestamps, bid, ask, bid_volume, ask_volume)
    assert result["timestamp_ms"].tolist() == [0, BAR_WIDTH_MS]
    assert result["xau_tick_count"].tolist() == [3, 2]
    assert result.loc[0, "tick_signed_move"] == 0
    assert result.loc[0, "tick_move_count"] == 2
    # The 100 -> 200 jump is between buckets and must not leak into either bucket.
    assert result.loc[1, "tick_signed_move"] == -1
    assert result.loc[1, "tick_move_count"] == 1


def test_same_bar_collision_is_stop_first_with_executable_quotes() -> None:
    frame = pd.DataFrame(
        [
            {
                "timestamp_ms": 0,
                "atr": 1.0,
                "xauusd_bid_open": 100.0,
                "xauusd_ask_open": 100.2,
                "xauusd_bid_high": 100.0,
                "xauusd_bid_low": 100.0,
                "xauusd_bid_close": 100.0,
                "xauusd_ask_high": 100.2,
                "xauusd_ask_low": 100.2,
                "xauusd_ask_close": 100.2,
            },
            {
                "timestamp_ms": BAR_WIDTH_MS,
                "atr": 1.0,
                "xauusd_bid_open": 100.0,
                "xauusd_ask_open": 100.2,
                "xauusd_bid_high": 101.8,
                "xauusd_bid_low": 99.1,
                "xauusd_bid_close": 100.5,
                "xauusd_ask_high": 102.0,
                "xauusd_ask_low": 99.3,
                "xauusd_ask_close": 100.7,
            },
            {
                "timestamp_ms": 2 * BAR_WIDTH_MS,
                "atr": 1.0,
                "xauusd_bid_open": 100.5,
                "xauusd_ask_open": 100.7,
                "xauusd_bid_high": 100.8,
                "xauusd_bid_low": 100.1,
                "xauusd_bid_close": 100.4,
                "xauusd_ask_high": 101.0,
                "xauusd_ask_low": 100.3,
                "xauusd_ask_close": 100.6,
            },
        ]
    )
    execution = {
        "maximum_holding_bars": 2,
        "risk_atr_multiple": 1.0,
        "reward_r": 1.5,
        "maximum_entry_spread_r": 0.25,
        "stress_slippage_r": 0.10,
    }
    result = _simulate_trade(frame, 0, "LONG", execution)
    assert result is not None
    assert result["entry_price"] == pytest.approx(100.2)
    assert result["exit_reason"] == "STOP"
    assert result["baseline_net_r"] == pytest.approx(-1.0)
    assert result["stress_net_r"] == pytest.approx(-1.1)


def test_portfolio_selection_chooses_one_best_candidate_and_honors_overlap() -> None:
    base = {
        "entry_time_ms": BAR_WIDTH_MS,
        "entry_time_utc": "2020-01-01T00:05:00.000Z",
        "exit_time_ms": 4 * BAR_WIDTH_MS,
        "exit_time_utc": "2020-01-01T00:20:00.000Z",
        "stress_net_r": 1.0,
        "baseline_net_r": 1.1,
        "family_id": "TREND_BREAKOUT",
        "regime": "TREND_UP",
        "direction": "LONG",
        "decision_time_utc": "2020-01-01T00:00:00.000Z",
        "exit_reason": "TARGET",
        "mfe_r": 1.5,
        "mae_r": -0.2,
    }
    rows = [
        {**base, "candidate_id": "a", "decision_time_ms": 0},
        {**base, "candidate_id": "b", "decision_time_ms": 0},
        {
            **base,
            "candidate_id": "c",
            "decision_time_ms": BAR_WIDTH_MS,
            "entry_time_ms": 2 * BAR_WIDTH_MS,
        },
    ]
    selected = _portfolio_select(
        rows,
        [0.4, 0.8, 0.9],
        0.0,
        {
            "maximum_concurrent_trades": 1,
            "maximum_trades_per_utc_day": 4,
            "portfolio_cooldown_minutes": 0,
        },
    )
    assert [row["candidate_id"] for row in selected] == ["b"]


def test_candidate_feature_contract_is_exact() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    row = pd.Series(
        {
            "atr": 2.0,
            "ema_fast": 101.0,
            "ema_slow": 100.0,
            "xauusd_mid_close": 102.0,
            "xau_return_5m_price": 0.1,
            "xau_return_15m_price": 0.2,
            "xau_return_60m_price": 0.3,
            "tick_imbalance_5m": 0.1,
            "tick_imbalance_15m": 0.2,
            "tick_imbalance_60m": 0.3,
            "book_imbalance_5m": 0.1,
            "book_imbalance_15m": 0.2,
            "microprice_edge_5m": 0.1,
            "microprice_edge_15m": 0.2,
            "xagusd_return_5m": 1.0,
            "xagusd_return_15m": 2.0,
            "xagusd_return_60m": 3.0,
            "eurusd_return_15m": 1.0,
            "eurusd_return_60m": 2.0,
            "usdjpy_return_15m": -1.0,
            "usdjpy_return_60m": -2.0,
            "atr_ratio_1d": 1.0,
            "quote_intensity_ratio": 1.1,
            "realized_volatility_ratio": 1.2,
            "spread_shock_ratio": 1.3,
            "price_efficiency_5m": 0.4,
            "timestamp_ms": 0,
        }
    )
    features = _candidate_features(row, "TREND_BREAKOUT", "TREND_UP", "LONG", 0.1)
    assert list(features) == contract["features"]
    assert all(np.isfinite(value) for value in features.values())
