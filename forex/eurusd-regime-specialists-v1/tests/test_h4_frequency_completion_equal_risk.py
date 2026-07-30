from __future__ import annotations

import pandas as pd
import pytest

from eurusd_regime_specialists.h4_frequency_completion_equal_risk import (
    set_equal_trade_risk,
)


def test_equal_risk_preserves_identity_and_rescales_all_risk_fields() -> None:
    source = pd.DataFrame(
        [
            {
                "specialist_id": "A",
                "portfolio_sleeve": "ONE",
                "portfolio_risk_weight": 0.45,
                "r": 0.9,
                "stress_r": 0.8,
                "pnl_usd_001_lot": 4.5,
                "pnl_usd_001_lot_equivalent": 4.5,
            },
            {
                "specialist_id": "B",
                "portfolio_sleeve": "TWO",
                "portfolio_risk_weight": 0.075,
                "r": -0.075,
                "stress_r": -0.08,
                "pnl_usd_001_lot": -0.75,
                "pnl_usd_001_lot_equivalent": -0.75,
            },
        ]
    )
    result = set_equal_trade_risk(source, 0.15)
    assert result["specialist_id"].tolist() == ["A", "B"]
    assert result["portfolio_sleeve"].tolist() == ["ONE", "TWO"]
    assert result["portfolio_risk_weight"].tolist() == [0.15, 0.15]
    assert result["r"].tolist() == pytest.approx([0.3, -0.15])
    assert result["pnl_usd_001_lot"].tolist() == pytest.approx([1.5, -1.5])


def test_equal_risk_rejects_nonpositive_parent_weight() -> None:
    source = pd.DataFrame(
        [{"portfolio_risk_weight": 0.0, "r": 1.0}]
    )
    with pytest.raises(ValueError):
        set_equal_trade_risk(source, 0.15)
