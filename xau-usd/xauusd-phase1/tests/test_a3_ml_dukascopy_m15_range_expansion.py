from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ml.a3_meta_v1.dukascopy_m15_range_expansion import (
    _simulate_expansion_trade,
    _validate_contract,
)
from ml.a3_meta_v1.dukascopy_m15_range_rotation import M15_WIDTH_MS


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ml/a3_ml_dukascopy_m15_range_expansion_v1.json"


def test_contract_preserves_train_first_firewall() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    _validate_contract(contract)
    assert contract["authorization"]["validation_requires_train_raw_pass"] is True
    assert contract["authorization"]["internal_test_requires_validation_pass"] is True
    assert contract["authorization"]["exam_requires_internal_test_pass"] is True
    assert contract["authorization"]["broker_action_authorized"] is False


def test_contract_rejects_broker_authorization() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["authorization"]["broker_action_authorized"] = True
    with pytest.raises(ValueError, match="broker_action_authorized"):
        _validate_contract(contract)


def test_expansion_trade_uses_executable_quotes_and_stop_first() -> None:
    frame = pd.DataFrame(
        [
            {
                "timestamp_ms": 0,
                "atr": 1.0,
                "xauusd_mid_low": 99.0,
                "xauusd_mid_high": 100.0,
                "xauusd_bid_open": 99.8,
                "xauusd_ask_open": 100.0,
                "xauusd_bid_high": 100.0,
                "xauusd_bid_low": 99.0,
                "xauusd_bid_close": 99.8,
                "xauusd_ask_high": 100.2,
                "xauusd_ask_low": 99.2,
                "xauusd_ask_close": 100.0,
            },
            {
                "timestamp_ms": M15_WIDTH_MS,
                "atr": 1.0,
                "xauusd_mid_low": 98.5,
                "xauusd_mid_high": 102.0,
                "xauusd_bid_open": 99.8,
                "xauusd_ask_open": 100.0,
                "xauusd_bid_high": 102.0,
                "xauusd_bid_low": 98.5,
                "xauusd_bid_close": 101.0,
                "xauusd_ask_high": 102.2,
                "xauusd_ask_low": 98.7,
                "xauusd_ask_close": 101.2,
            },
            {
                "timestamp_ms": 2 * M15_WIDTH_MS,
                "atr": 1.0,
                "xauusd_mid_low": 100.0,
                "xauusd_mid_high": 101.0,
                "xauusd_bid_open": 100.0,
                "xauusd_ask_open": 100.2,
                "xauusd_bid_high": 101.0,
                "xauusd_bid_low": 100.0,
                "xauusd_bid_close": 100.5,
                "xauusd_ask_high": 101.2,
                "xauusd_ask_low": 100.2,
                "xauusd_ask_close": 100.7,
            },
        ]
    )
    execution = {
        "minimum_stop_atr": 1.0,
        "structural_stop_buffer_atr": 0.25,
        "reward_r": 1.5,
        "maximum_holding_bars": 2,
        "maximum_entry_spread_r": 0.30,
        "stress_slippage_r": 0.10,
    }
    result = _simulate_expansion_trade(frame, 0, "LONG", execution)
    assert result is not None
    assert result["entry_price"] == pytest.approx(100.0)
    assert result["stop_price"] == pytest.approx(98.75)
    assert result["target_price"] == pytest.approx(101.875)
    assert result["exit_reason"] == "STOP"
    assert result["baseline_net_r"] == pytest.approx(-1.0)
    assert result["stress_net_r"] == pytest.approx(-1.1)
