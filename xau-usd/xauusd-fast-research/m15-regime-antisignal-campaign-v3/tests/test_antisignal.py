from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from antisignal import generate_manifest, load_config, signal_mask_direction  # noqa: E402


def _frame() -> pd.DataFrame:
    rows = 120
    close = pd.Series(np.linspace(100.0, 110.0, rows))
    return pd.DataFrame(
        {
            "mid_close": close,
            "mid_open": close - 0.1,
            "mid_high": close + 0.2,
            "mid_low": close - 0.2,
            "atr14": 1.0,
            "regime": "CHOP",
            "hour": 10,
            "candle_direction": 1,
            "body": 0.3,
            "efficiency_ratio": 0.3,
            "day_bar_number": 40,
            "vwap_deviation_atr": 1.0,
            "anchored_vwap": close - 1.0,
            "asian_high": 105.0,
            "asian_low": 95.0,
            "asian_range_atr": 10.0,
            "prior_day_high": 105.0,
            "prior_day_low": 95.0,
            "last_resolved_regime": "CHOP",
            "transition_age_m15": 4,
            "ancestry_direction": 0,
            "ema_fast": close - 0.5,
            "upper_wick": 0.2,
            "lower_wick": 0.2,
            **{f"return_{bars}_local": close.diff(bars) for bars in (2, 4, 8, 16, 24)},
            **{f"rsi_{period}": 80.0 for period in (2, 3, 4, 6, 9)},
            **{f"prior_high_{bars}": close.shift(1).rolling(bars).max() for bars in (8, 12, 16, 24, 32, 48, 72, 96)},
            **{f"prior_low_{bars}": close.shift(1).rolling(bars).min() for bars in (8, 12, 16, 24, 32, 48, 72, 96)},
            **{f"prior_mean_{bars}": close.shift(1).rolling(bars).mean() for bars in (16, 24, 32, 48, 72, 96)},
        }
    )


def test_manifest_is_complete_unique_and_contiguous() -> None:
    manifest = generate_manifest(load_config(ROOT)["selection"])
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(19120, 20120))
    assert manifest["variant_id"].is_unique


def test_vwap_escape_points_away_from_vwap() -> None:
    params = {
        "deviation_atr": 0.4,
        "body_min": 0.1,
        "efficiency_min": 0.05,
        "minimum_day_bars": 16,
        "hour_window": "ALL",
        "stop_atr": 1.0,
        "target_r": 1.5,
        "hold_hours": 4,
    }
    frame = _frame()
    mask, direction, target = signal_mask_direction(frame, "CHOP_VWAP_ESCAPE", params)
    assert mask.any()
    assert direction.loc[mask].eq(1).all()
    assert (target.loc[mask] > frame.loc[mask, "mid_close"]).all()


def test_shock_is_never_eligible() -> None:
    params = {
        "deviation_atr": 0.4,
        "body_min": 0.1,
        "efficiency_min": 0.05,
        "minimum_day_bars": 16,
        "hour_window": "ALL",
        "stop_atr": 1.0,
        "target_r": 1.5,
        "hold_hours": 4,
    }
    frame = _frame()
    frame["regime"] = "UNSAFE_SHOCK"
    mask, _, _ = signal_mask_direction(frame, "CHOP_VWAP_ESCAPE", params)
    assert not mask.any()
