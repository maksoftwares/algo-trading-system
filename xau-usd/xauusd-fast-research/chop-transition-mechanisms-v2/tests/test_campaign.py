from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import (  # noqa: E402
    add_changed_features,
    generate_manifest,
    parameter_space,
    signal_mask_direction,
)


def _config() -> dict:
    return json.loads(
        (ROOT / "config" / "chop_transition_mechanisms_v2.json").read_text(
            encoding="utf-8"
        )
    )


def _frame() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02T00:00:00Z", periods=24, freq="h")
    close = pd.Series(np.linspace(2000.0, 2004.6, len(timestamps)))
    regime = ["TREND_DOWN"] * 4 + ["TRANSITION_UNKNOWN"] * 8 + ["CHOP"] * 12
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "mid_open": close - 0.05,
            "mid_high": close + 0.2,
            "mid_low": close - 0.2,
            "mid_close": close,
            "tick_count": np.arange(1, len(timestamps) + 1),
            "atr14": 1.0,
            "regime": regime,
            "candle_direction": 1,
            "body": 0.25,
            "upper_wick": 0.25,
            "lower_wick": 0.25,
            "efficiency_ratio": 0.2,
            "ema_fast": close - 0.1,
            "ema_slope_atr_h4": -0.2,
            "rsi_2": 80.0,
            "rsi_3": 80.0,
            "rsi_4": 80.0,
            "rsi_6": 80.0,
            "rsi_9": 80.0,
            **{
                f"return_{bars}_local": close.diff(bars)
                for bars in (1, 2, 3, 4, 6, 8, 12)
            },
            **{
                f"prior_high_{bars}": close.shift(1).rolling(bars).max()
                for bars in (4, 6, 8, 12, 18, 24)
            },
            **{
                f"prior_low_{bars}": close.shift(1).rolling(bars).min()
                for bars in (4, 6, 8, 12, 18, 24)
            },
        }
    )


def test_manifest_is_complete_unique_and_contiguous() -> None:
    manifest = generate_manifest(_config()["selection"])
    assert len(manifest) == 2000
    assert manifest["attempt_no"].tolist() == list(range(15120, 17120))
    assert manifest["variant_id"].is_unique
    assert manifest.groupby("regime_owner").size().to_dict() == {
        "CHOP": 1000,
        "TRANSITION": 1000,
    }


def test_failure_fade_age_windows_are_reachable() -> None:
    assert all(
        int(params["transition_age_min"]) <= int(params["transition_age_max"])
        for params in parameter_space("TRANS_ANCESTRY_FAILURE_FADE")
    )


def test_changed_features_do_not_change_when_future_prices_change() -> None:
    original = _frame()
    altered = original.copy()
    altered.loc[16:, ["mid_open", "mid_high", "mid_low", "mid_close"]] += 500.0
    left = add_changed_features(original).iloc[:16]
    right = add_changed_features(altered).iloc[:16]
    columns = [
        "day_open",
        "anchored_vwap",
        "asian_high",
        "asian_low",
        "asian_close",
        "last_resolved_regime",
        "ancestry_direction",
        "transition_age_h1",
    ]
    pd.testing.assert_frame_equal(left[columns], right[columns])


def test_transition_lineage_uses_only_prior_resolved_regime() -> None:
    featured = add_changed_features(_frame())
    transition = featured.loc[featured["regime"].eq("TRANSITION_UNKNOWN")]
    assert transition["last_resolved_regime"].eq("TREND_DOWN").all()
    assert transition["ancestry_direction"].eq(-1).all()
    assert transition["transition_age_h1"].tolist() == list(range(1, 9))


def test_shock_is_never_eligible() -> None:
    frame = add_changed_features(_frame())
    frame["regime"] = "UNSAFE_SHOCK"
    params = {
        "deviation_atr": 0.25,
        "minimum_day_bars": 4,
        "maximum_day_displacement_atr": 3.0,
        "require_confirmation": False,
        "hour_window": "ALL",
        "hold_hours": 4,
        "stop_atr": 1.0,
    }
    mask, _ = signal_mask_direction(frame, "CHOP_ANCHORED_VWAP_REVERSION", params)
    assert not mask.any()
