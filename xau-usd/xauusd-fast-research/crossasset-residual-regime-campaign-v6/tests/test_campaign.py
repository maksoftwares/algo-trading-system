from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import campaign  # noqa: E402


def _feature_config() -> dict:
    return {
        "residual_features": {
            "keys": ["H1_D2"],
            "rolling_windows": {"D2": "2D"},
            "minimum_observations": {"D2": 2},
            "beta_clip": 3.0,
        }
    }


def _base_frame(rows: int = 12) -> pd.DataFrame:
    time = pd.date_range("2024-01-02T00:00:00Z", periods=rows, freq="15min")
    x = np.linspace(-1.0, 1.0, rows)
    return pd.DataFrame(
        {
            "timestamp_utc": time,
            "dxy_pressure_H1_D2": x,
            "bond_pressure_H1_D2": x * 0.8,
            "gold_return_H1_atr": x * 0.4 + np.sin(np.arange(rows)) * 0.1,
        }
    )


def test_residual_features_do_not_change_when_future_is_appended() -> None:
    base = _base_frame()
    first = campaign.enrich_residual_features(base.iloc[:8], _feature_config())
    changed = base.copy()
    changed.loc[8:, "gold_return_H1_atr"] = 1000.0
    second = campaign.enrich_residual_features(changed, _feature_config()).iloc[:8]
    pd.testing.assert_series_equal(
        first["residual_z_H1_D2"], second["residual_z_H1_D2"], check_names=False
    )


def test_chop_signal_abstains_outside_chop() -> None:
    frame = campaign.enrich_residual_features(_base_frame(), _feature_config())
    frame["hour_utc"] = frame["timestamp_utc"].dt.hour
    frame["body"] = 1.0
    frame["candle_direction"] = 1
    frame["atr14"] = 1.0
    frame["ancestry_direction"] = 1
    frame["transition_age_m15"] = 1
    frame["regime"] = "TREND_UP"
    params = {
        "feature_key": "H1_D2",
        "hour_window": "ALL",
        "geometry_id": "C_FAST",
        "z_min": 0.0,
        "macro_mode": "ANY",
        "pressure_min": 0.0,
        "require_confirmation": False,
        "body_min": 0.0,
    }
    mask, _ = campaign.signal_mask_direction(
        frame, "CHOP_MACRO_RESIDUAL_FADE", params
    )
    assert not bool(mask.any())


def test_transition_signal_abstains_in_shock() -> None:
    frame = campaign.enrich_residual_features(_base_frame(), _feature_config())
    frame["hour_utc"] = frame["timestamp_utc"].dt.hour
    frame["body"] = 1.0
    frame["candle_direction"] = 1
    frame["atr14"] = 1.0
    frame["ancestry_direction"] = 1
    frame["transition_age_m15"] = 1
    frame["regime"] = "UNSAFE_SHOCK"
    params = {
        "feature_key": "H1_D2",
        "hour_window": "ALL",
        "geometry_id": "T_FAST",
        "z_min": 0.0,
        "pressure_min": 0.0,
        "macro_relation": "ANY",
        "transition_age_max": 48,
        "require_confirmation": False,
        "body_min": 0.0,
    }
    mask, _ = campaign.signal_mask_direction(frame, "TRANS_RESIDUAL_BREAKOUT", params)
    assert not bool(mask.any())

