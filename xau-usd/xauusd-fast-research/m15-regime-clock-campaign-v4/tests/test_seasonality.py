from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seasonality import (  # noqa: E402
    generate_manifest,
    load_config,
    prepare_clock_features,
    signal_mask_direction,
)


def _frame(days: int = 3) -> pd.DataFrame:
    periods = days * 96
    starts = pd.date_range("2024-01-01", periods=periods, freq="15min", tz="UTC")
    close = pd.Series(np.linspace(2000.0, 2030.0, periods))
    day = starts.normalize()
    day_open = pd.Series(close.to_numpy(), index=day).groupby(level=0).transform("first")
    result = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "timestamp_utc": starts + pd.Timedelta(minutes=15),
            "mid_open": close - 0.05,
            "mid_close": close,
            "mid_high": close + 0.10,
            "mid_low": close - 0.10,
            "atr14": 1.0,
            "regime": "CHOP",
            "hour": starts.hour,
            "day_open": day_open.to_numpy(),
            "last_resolved_regime": "CHOP",
            "transition_age_m15": 0,
            "ancestry_direction": 0,
            **{
                f"return_{bars}_local": close.diff(bars)
                for bars in (8, 16, 24, 32)
            },
        }
    )
    return prepare_clock_features(result)


def test_manifest_is_complete_unique_and_contiguous() -> None:
    manifest = generate_manifest(load_config(ROOT)["selection"])
    assert len(manifest) == 1000
    assert manifest["attempt_no"].tolist() == list(range(20120, 21120))
    assert manifest["variant_id"].is_unique
    assert manifest.groupby("mechanic").size().eq(100).all()


def test_asia_close_is_not_available_before_0600() -> None:
    frame = _frame()
    assert frame.loc[frame["hour"].lt(6), "asia_close"].isna().all()
    assert frame.loc[
        frame["hour"].eq(6) & frame["minute"].eq(0), "asia_close"
    ].notna().all()


def test_prior_day_return_is_shifted() -> None:
    frame = _frame()
    first_day = frame["bar_start_utc"].dt.normalize().min()
    second_day = first_day + pd.Timedelta(days=1)
    assert frame.loc[
        frame["bar_start_utc"].dt.normalize().eq(first_day), "prior_day_return_atr"
    ].isna().all()
    assert frame.loc[
        frame["bar_start_utc"].dt.normalize().eq(second_day), "prior_day_return_atr"
    ].notna().all()


def test_fixed_clock_carry_and_shock_exclusion() -> None:
    frame = _frame()
    params = {
        "signal_hour": 8,
        "fixed_direction": -1,
        "weekday_group": "ALL",
        "stop_atr": 1.25,
        "target_r": 2.0,
        "hold_hours": 4,
    }
    mask, direction, target = signal_mask_direction(
        frame, "CHOP_FIXED_CLOCK_CARRY", params
    )
    assert mask.any()
    assert frame.loc[mask, "hour"].eq(8).all()
    assert frame.loc[mask, "minute"].eq(0).all()
    assert direction.loc[mask].eq(-1).all()
    assert (target.loc[mask] < frame.loc[mask, "mid_close"]).all()

    shock = frame.copy()
    shock["regime"] = "UNSAFE_SHOCK"
    shock_mask, _, _ = signal_mask_direction(
        shock, "CHOP_FIXED_CLOCK_CARRY", params
    )
    assert not shock_mask.any()


def test_transition_ancestry_response_is_causal_and_directional() -> None:
    frame = _frame()
    frame["regime"] = "TRANSITION_UNKNOWN"
    frame["last_resolved_regime"] = "TREND_DOWN"
    frame["ancestry_direction"] = -1
    frame["transition_age_m15"] = 4
    params = {
        "signal_hour": 12,
        "ancestry_response": "CONTINUE",
        "transition_age_max": 16,
        "weekday_group": "ALL",
        "stop_atr": 1.5,
        "target_r": 2.0,
        "hold_hours": 8,
    }
    mask, direction, _ = signal_mask_direction(
        frame, "TRANS_TREND_ANCESTRY_CLOCK", params
    )
    assert mask.any()
    assert direction.loc[mask].eq(-1).all()


def test_manifest_parameters_are_canonical_json() -> None:
    manifest = generate_manifest(load_config(ROOT)["selection"])
    for value in manifest["parameters_json"].head(20):
        assert json.dumps(
            json.loads(value), sort_keys=True, separators=(",", ":")
        ) == value
