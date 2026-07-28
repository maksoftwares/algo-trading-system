from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_selective_target_probability import (  # noqa: E402
    _side_rows,
)


def config() -> dict:
    return {
        "features": {
            "side_aligned_columns": [
                "aligned_return_3_atr",
                "side_room_atr",
            ],
            "derived_flow_columns": [
                "aligned_kraken_side_imbalance",
                "aligned_binance_taker_imbalance",
                "kraken_imbalance_magnitude",
                "binance_imbalance_magnitude",
            ],
            "model_column_count": 6,
        }
    }


def points() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "decision_id": ["A"],
            "entry_time_utc": pd.to_datetime(
                ["2025-01-02T00:00:00Z"], utc=True
            ),
            "aligned_return_3_atr_long": [0.5],
            "aligned_return_3_atr_short": [-0.5],
            "side_room_atr_long": [1.2],
            "side_room_atr_short": [0.8],
            "kraken_reported_side_imbalance_15m": [0.4],
            "binance_taker_imbalance_15m": [-0.2],
            "target_first_long": [True],
            "target_first_short": [False],
            "exit_time_utc_long": pd.to_datetime(
                ["2025-01-02T01:00:00Z"], utc=True
            ),
            "exit_time_utc_short": pd.to_datetime(
                ["2025-01-02T02:00:00Z"], utc=True
            ),
        }
    )


def test_side_stack_aligns_directional_flow_without_leakage() -> None:
    rows = _side_rows(points(), config(), include_labels=False)
    assert rows["side"].tolist() == ["LONG", "SHORT"]
    assert np.allclose(
        rows["aligned_kraken_side_imbalance"], [0.4, -0.4]
    )
    assert np.allclose(
        rows["aligned_binance_taker_imbalance"], [-0.2, 0.2]
    )
    assert np.allclose(
        rows["kraken_imbalance_magnitude"], [0.4, 0.4]
    )
    assert "target_first" not in rows
    assert "label_known_time_utc" not in rows


def test_training_rows_use_side_specific_label_known_time() -> None:
    rows = _side_rows(points(), config(), include_labels=True)
    assert rows["target_first"].tolist() == [True, False]
    assert rows["label_known_time_utc"].tolist() == [
        pd.Timestamp("2025-01-02T01:00:00Z"),
        pd.Timestamp("2025-01-02T02:00:00Z"),
    ]
