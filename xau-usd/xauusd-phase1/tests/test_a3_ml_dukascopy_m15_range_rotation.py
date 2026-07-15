from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ml.a3_meta_v1.dukascopy_m15_range_rotation import (
    M15_WIDTH_MS,
    _aggregate_m15,
    _raw_train_gates,
    _simulate_range_trade,
    _validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ml/a3_ml_dukascopy_m15_range_rotation_v1.json"


def _m5_row(timestamp_ms: int, price: float) -> dict[str, float | int | str | bool]:
    row: dict[str, float | int | str | bool] = {
        "timestamp_ms": timestamp_ms,
        "xau_tick_count": 100,
        "tick_signed_move": 10,
        "tick_move_count": 50,
        "tick_realized_variance": 0.5,
        "tick_spread_mean": 0.2,
        "tick_spread_last": 0.2,
        "tick_spread_max": 0.3,
        "tick_book_imbalance_mean": 0.1,
        "tick_microprice_edge_mean": 0.05,
        "tick_imbalance_5m": 0.2,
        "book_imbalance_5m": 0.1,
        "microprice_edge_5m": 0.05,
        "price_efficiency_5m": 0.5,
        "xau_return_5m_price": 0.1,
        "xagusd_return_5m": 1.0,
    }
    for prefix, offset in (("xauusd_mid", 0.0), ("xauusd_bid", -0.1), ("xauusd_ask", 0.1)):
        row[f"{prefix}_open"] = price + offset
        row[f"{prefix}_high"] = price + offset + 0.4
        row[f"{prefix}_low"] = price + offset - 0.4
        row[f"{prefix}_close"] = price + offset + 0.1
    for symbol, value in (("xagusd", 25.0), ("eurusd", 1.1), ("usdjpy", 110.0)):
        row[f"{symbol}_mid_close"] = value + timestamp_ms / 10**10
    return row


def test_contract_is_locked_and_research_only() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _validate_contract(contract)
    assert contract["authorization"]["validation_requires_train_raw_pass"] is True
    assert contract["authorization"]["broker_action_authorized"] is False


def test_contract_rejects_firewall_weakening() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["authorization"]["validation_requires_train_raw_pass"] = False
    with pytest.raises(ValueError, match="firewall"):
        _validate_contract(contract)


def test_m15_aggregation_requires_three_complete_contiguous_m5_bars() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    frame = pd.DataFrame(
        [
            _m5_row(0, 100.0),
            _m5_row(300_000, 100.2),
            _m5_row(600_000, 100.1),
            _m5_row(900_000, 100.3),
            _m5_row(1_200_000, 100.4),
        ]
    )
    result = _aggregate_m15(frame, contract)
    assert result["timestamp_ms"].tolist() == [0]
    assert result.loc[0, "source_bar_count"] == 3
    assert result.loc[0, "xau_tick_count"] == 300
    assert result.loc[0, "xauusd_mid_open"] == pytest.approx(100.0)
    assert result.loc[0, "xauusd_mid_close"] == pytest.approx(100.2)


def test_range_trade_uses_midline_target_and_stop_first_collision() -> None:
    frame = pd.DataFrame(
        [
            {
                "timestamp_ms": 0,
                "atr": 1.0,
                "range_midline": 100.0,
                "xauusd_mid_low": 97.0,
                "xauusd_mid_high": 98.0,
                "xauusd_bid_open": 97.8,
                "xauusd_ask_open": 98.0,
                "xauusd_bid_high": 98.0,
                "xauusd_bid_low": 97.0,
                "xauusd_bid_close": 97.8,
                "xauusd_ask_high": 98.2,
                "xauusd_ask_low": 97.2,
                "xauusd_ask_close": 98.0,
            },
            {
                "timestamp_ms": M15_WIDTH_MS,
                "atr": 1.0,
                "range_midline": 100.0,
                "xauusd_mid_low": 97.0,
                "xauusd_mid_high": 100.2,
                "xauusd_bid_open": 97.8,
                "xauusd_ask_open": 98.0,
                "xauusd_bid_high": 100.2,
                "xauusd_bid_low": 96.5,
                "xauusd_bid_close": 99.0,
                "xauusd_ask_high": 100.4,
                "xauusd_ask_low": 96.7,
                "xauusd_ask_close": 99.2,
            },
            {
                "timestamp_ms": 2 * M15_WIDTH_MS,
                "atr": 1.0,
                "range_midline": 100.0,
                "xauusd_mid_low": 98.5,
                "xauusd_mid_high": 99.5,
                "xauusd_bid_open": 99.0,
                "xauusd_ask_open": 99.2,
                "xauusd_bid_high": 99.4,
                "xauusd_bid_low": 98.4,
                "xauusd_bid_close": 99.0,
                "xauusd_ask_high": 99.6,
                "xauusd_ask_low": 98.6,
                "xauusd_ask_close": 99.2,
            },
        ]
    )
    execution = {
        "minimum_stop_atr": 1.25,
        "structural_stop_buffer_atr": 0.25,
        "minimum_target_r": 0.50,
        "maximum_holding_bars": 2,
        "maximum_entry_spread_r": 0.33,
        "stress_slippage_r": 0.10,
    }
    result = _simulate_range_trade(frame, 0, "LONG", execution)
    assert result is not None
    assert result["target_price"] == pytest.approx(100.0)
    assert result["exit_reason"] == "STOP"
    assert result["baseline_net_r"] == pytest.approx(-1.0)
    assert result["stress_net_r"] == pytest.approx(-1.1)


def test_raw_gate_requires_near_break_even_economics() -> None:
    gate = {
        "minimum_trades": 200,
        "minimum_baseline_profit_factor": 0.95,
        "minimum_stress_profit_factor": 0.85,
        "minimum_average_stress_r": -0.05,
    }
    metrics = {
        "trades": 250,
        "baseline_profit_factor": 1.0,
        "stress_profit_factor": 0.9,
        "average_stress_r": -0.04,
    }
    assert all(_raw_train_gates(metrics, gate).values())
    metrics["stress_profit_factor"] = 0.8
    assert _raw_train_gates(metrics, gate)["stress_profit_factor"] is False
