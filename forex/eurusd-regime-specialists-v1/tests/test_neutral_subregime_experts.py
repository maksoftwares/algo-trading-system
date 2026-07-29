from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_subregime_experts import (
    _training_diagnostics,
    enforce_nonoverlap,
    expert_direction,
)


def test_expert_direction_uses_frozen_sign_mapping() -> None:
    row = pd.Series({"side_return_3_atr": 0.8})
    follow = {
        "feature": "side_return_3_atr",
        "absolute_threshold": 0.6,
        "positive_direction": "LONG",
    }
    fade = {
        "feature": "side_return_3_atr",
        "absolute_threshold": 0.6,
        "positive_direction": "SHORT",
    }
    assert expert_direction(row, follow) == "LONG"
    assert expert_direction(row, fade) == "SHORT"
    assert expert_direction(pd.Series({"side_return_3_atr": -0.8}), follow) == "SHORT"
    assert expert_direction(pd.Series({"side_return_3_atr": 0.2}), follow) is None


def test_nonoverlap_is_fail_closed_at_equal_exit_index() -> None:
    trades = pd.DataFrame(
        {
            "signal_id": ["a", "b", "c"],
            "entry_time_utc": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T04:00:00Z",
                    "2026-01-01T08:00:00Z",
                ],
                utc=True,
            ),
            "entry_index": [10, 20, 21],
            "exit_index": [20, 22, 25],
        }
    )
    kept, rejected = enforce_nonoverlap(trades)
    assert kept["signal_id"].tolist() == ["a", "c"]
    assert rejected == 1


def test_empty_training_diagnostics_fail_admission() -> None:
    result = _training_diagnostics(
        pd.DataFrame(),
        pd.Timestamp("2026-01-01T00:00:00Z"),
        {
            "minimum_training_trades": 24,
            "minimum_each_half_trades": 8,
            "minimum_training_profit_factor": 1.15,
            "minimum_training_stress_profit_factor": 1.05,
            "minimum_each_half_profit_factor_exclusive": 1.0,
            "minimum_training_net_r_exclusive": 0.0,
        },
    )
    assert result["training_trades"] == 0
    assert result["admitted"] is False
