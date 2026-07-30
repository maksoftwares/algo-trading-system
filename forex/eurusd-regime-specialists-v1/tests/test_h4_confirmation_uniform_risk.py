from __future__ import annotations

import pandas as pd
import pytest

from eurusd_regime_specialists.h4_confirmation_uniform_risk import (
    scale_uniformly,
)


def test_uniform_scale_changes_every_risk_quantity_and_no_trade_identity() -> None:
    source = pd.DataFrame(
        [
            {
                "specialist_id": "A",
                "entry_time_utc": "2026-01-01T00:00:00Z",
                "portfolio_risk_weight": 1.0,
                "r": 1.2,
                "stress_r": 1.1,
                "pnl_usd_001_lot": 3.0,
                "pnl_usd_001_lot_equivalent": 3.0,
            },
            {
                "specialist_id": "B",
                "entry_time_utc": "2026-01-02T00:00:00Z",
                "portfolio_risk_weight": 0.5,
                "r": -0.5,
                "stress_r": -0.6,
                "pnl_usd_001_lot": -1.0,
                "pnl_usd_001_lot_equivalent": -1.0,
            },
        ]
    )
    result = scale_uniformly(source, 0.75)
    assert result["specialist_id"].tolist() == ["A", "B"]
    assert result["entry_time_utc"].tolist() == source["entry_time_utc"].tolist()
    assert result["portfolio_risk_weight"].tolist() == [0.75, 0.375]
    assert result["r"].tolist() == pytest.approx([0.9, -0.375])
    assert result["pnl_usd_001_lot"].tolist() == pytest.approx(
        [2.25, -0.75]
    )
