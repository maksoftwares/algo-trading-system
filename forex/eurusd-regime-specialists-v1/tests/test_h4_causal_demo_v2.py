from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_causal_demo_v2 import (
    build_causal_confirmation_mask,
)


def _bars(closes: list[float], highs: list[float], lows: list[float]) -> pd.DataFrame:
    count = len(closes)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2026-01-05T00:00Z", periods=count, freq="15min"
            ),
            "complete_bar": True,
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": closes,
            "body_fraction": 0.8,
            "regime": "chop",
            "atr": 0.001,
        }
    )


def test_next_close_uses_confirmation_bar_not_first_break() -> None:
    closes = [1.1] * 24 + [0.99, 0.98]
    bars = _bars(closes, [1.2] * 26, [1.0] * 24 + [0.98, 0.97])
    mask = build_causal_confirmation_mask(
        bars,
        {"body_fraction_minimum": 0.35, "owned_regime": "chop"},
        "SHORT",
        "NEXT_CLOSE",
    )
    assert mask.sum() == 1
    assert bars.loc[mask, "timestamp"].iloc[0] == pd.Timestamp(
        "2026-01-05T06:15Z"
    )


def test_next_close_rejects_reentry_after_failed_immediate_confirmation() -> None:
    closes = [1.1] * 24 + [0.99, 1.01, 0.98]
    bars = _bars(closes, [1.2] * 27, [1.0] * 24 + [0.98, 0.99, 0.97])
    mask = build_causal_confirmation_mask(
        bars,
        {"body_fraction_minimum": 0.35, "owned_regime": "chop"},
        "SHORT",
        "NEXT_CLOSE",
    )
    assert mask.sum() == 0


def test_retest_requires_touch_and_close_beyond_boundary() -> None:
    closes = [1.1] * 24 + [0.99, 0.98, 0.99]
    highs = [1.2] * 24 + [1.00, 0.995, 1.005]
    lows = [1.0] * 24 + [0.98, 0.97, 0.98]
    bars = _bars(closes, highs, lows)
    mask = build_causal_confirmation_mask(
        bars,
        {"body_fraction_minimum": 0.35, "owned_regime": "chop"},
        "SHORT",
        "RETEST_REJECT",
    )
    assert mask.sum() == 1
    assert bars.loc[mask, "timestamp"].iloc[0] == pd.Timestamp(
        "2026-01-05T06:30Z"
    )


def test_long_mirror_is_symmetric() -> None:
    closes = [1.1] * 24 + [1.21, 1.22]
    highs = [1.2] * 24 + [1.22, 1.23]
    lows = [1.0] * 26
    bars = _bars(closes, highs, lows)
    mask = build_causal_confirmation_mask(
        bars,
        {"body_fraction_minimum": 0.35, "owned_regime": "chop"},
        "LONG",
        "NEXT_CLOSE",
    )
    assert mask.sum() == 1
    assert bars.loc[mask, "timestamp"].iloc[0] == pd.Timestamp(
        "2026-01-05T06:15Z"
    )
