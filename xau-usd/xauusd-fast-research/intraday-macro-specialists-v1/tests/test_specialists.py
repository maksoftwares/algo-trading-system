from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from specialists import prepare_frame


def frames(rows: int = 220) -> tuple[pd.DataFrame, pd.DataFrame]:
    ends = pd.date_range("2026-01-01T00:15:00Z", periods=rows, freq="15min", tz="UTC")
    x = np.arange(rows, dtype=float)
    gold_close = 2000.0 + 0.2 * x + np.sin(x / 5.0)
    gold = pd.DataFrame(
        {
            "timestamp_utc": ends,
            "mid_open": gold_close - 0.1,
            "mid_high": gold_close + 0.5,
            "mid_low": gold_close - 0.5,
            "mid_close": gold_close,
        }
    )
    dxy = 100.0 + 0.01 * x + 0.05 * np.sin(x / 3.0)
    bond = 120.0 + 0.01 * x + 0.04 * np.cos(x / 4.0)
    macro = pd.DataFrame(
        {
            "timestamp_utc": ends,
            "dollaridxusd_close": dxy,
            "ustbondtrusd_close": bond,
        }
    )
    return gold, macro


def geometry() -> dict:
    return {
        "macro_return_bars": 4,
        "macro_scale_bars": 192,
        "macro_scale_minimum_bars": 96,
    }


def test_dollar_pressure_is_inverse_and_bond_pressure_is_direct() -> None:
    gold, macro = frames()
    result = prepare_frame(gold, macro, geometry()).dropna()
    assert np.allclose(result["dxy_gold_pressure_z"], -result["dollaridxusd_return_z"])
    assert np.allclose(result["bond_gold_pressure_z"], result["ustbondtrusd_return_z"])


def test_macro_join_requires_exact_completed_timestamp() -> None:
    gold, macro = frames(30)
    macro = macro.drop(index=10)
    result = prepare_frame(gold, macro, geometry())
    assert len(result) == 29
    assert gold.iloc[10]["timestamp_utc"] not in set(result["timestamp_utc"])


def test_configuration_cannot_authorize_execution() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "config" / "intraday_macro_specialists_v1.json").read_text())
    controls = config["research_controls"]
    assert controls["research_only"] is True
    assert controls["python_predictions_authorized"] is False
    assert controls["ea_consumption_authorized"] is False
    assert controls["broker_action_authorized"] is False
