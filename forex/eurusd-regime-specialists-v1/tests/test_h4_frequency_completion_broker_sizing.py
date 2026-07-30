from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.h4_frequency_completion_broker_sizing import (
    IDENTITY_COLUMNS,
    is_legal_volume,
)
from eurusd_regime_specialists.h4_frequency_completion_equal_risk import (
    set_equal_trade_risk,
)


def test_only_exact_broker_grid_lots_are_legal() -> None:
    assert is_legal_volume(0.01, 0.01, 100.0, 0.01)
    assert is_legal_volume(0.02, 0.01, 100.0, 0.01)
    assert not is_legal_volume(0.015, 0.01, 100.0, 0.01)
    assert not is_legal_volume(0.005, 0.01, 100.0, 0.01)


def test_uniform_broker_sizing_preserves_trade_identity() -> None:
    row = {
        "specialist_id": "A",
        "portfolio_sleeve": "BASELINE_CHOP",
        "signal_time_utc": "2026-01-01T06:00:00Z",
        "entry_time_utc": "2026-01-01T06:15:00Z",
        "exit_time_utc": "2026-01-01T07:00:00Z",
        "side": "SHORT",
        "entry": 1.1,
        "stop": 1.2,
        "target": 1.0,
        "exit": 1.0,
        "exit_reason": "TARGET",
        "portfolio_risk_weight": 0.15,
        "r": 0.15,
        "pnl_usd_001_lot": 1.5,
    }
    source = pd.DataFrame([row])
    result = set_equal_trade_risk(source, 0.1)
    assert source[IDENTITY_COLUMNS].equals(result[IDENTITY_COLUMNS])
    assert result.loc[0, "portfolio_risk_weight"] == 0.1
