from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_validated_consensus import consensus_trades


def test_training_consensus_uses_same_veto_as_score_consensus() -> None:
    signals = pd.DataFrame(
        {
            "signal_id": ["x"],
            "side_return_3_atr": [0.8],
            "side_macro_pressure_clipped": [-2.0],
        }
    )
    outcome = pd.Series({"signal_id": "x", "direction": "LONG", "r": 1.5})
    lookup = {("x", "LONG"): outcome}
    admitted = [
        {
            "expert_id": "momentum",
            "mechanism_group": "price_momentum",
            "expert": {
                "feature": "side_return_3_atr",
                "absolute_threshold": 0.6,
                "positive_direction": "LONG",
            },
        },
        {
            "expert_id": "macro",
            "mechanism_group": "macro_follow",
            "expert": {
                "feature": "side_macro_pressure_clipped",
                "absolute_threshold": 1.5,
                "positive_direction": "SHORT",
            },
        },
    ]
    result = consensus_trades(
        signals,
        lookup,
        admitted,
        {
            "minimum_agreeing_experts": 2,
            "minimum_agreeing_mechanism_groups": 2,
        },
    )
    assert len(result) == 1
    assert result.iloc[0]["direction"] == "LONG"
