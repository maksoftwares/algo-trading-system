from __future__ import annotations

import numpy as np
import pandas as pd

from src.serving import causal_rank, market_feature_frame, score_candidate


def synthetic_bars(rows: int = 2300) -> pd.DataFrame:
    index = np.arange(rows, dtype=float)
    close = 2000.0 + 0.03 * index + np.sin(index / 17.0)
    return pd.DataFrame(
        {
            "bar_start_utc": pd.date_range(
                "2026-01-01", periods=rows, freq="5min", tz="UTC"
            ),
            "mid_high": close + 0.4,
            "mid_low": close - 0.4,
            "mid_close": close,
        }
    )


def test_causal_rank_uses_right_insertion() -> None:
    reference = np.array([1.0, 2.0, 2.0, 4.0])
    assert causal_rank(2.0, reference) == 0.75


def test_future_bar_change_cannot_change_prior_features() -> None:
    bars = synthetic_bars()
    before = market_feature_frame(bars)
    changed = bars.copy()
    changed.loc[changed.index[-1], "mid_close"] += 100.0
    after = market_feature_frame(changed)
    columns = [
        "atr_ratio",
        "rv_1h",
        "rv_24h",
        "slope_atr",
        "ret_1h",
        "ret_4h",
        "ret_24h",
        "dist_hi_24h",
        "dist_lo_24h",
    ]
    pd.testing.assert_frame_equal(
        before.loc[: before.index[-2], columns],
        after.loc[: after.index[-2], columns],
    )


def test_score_candidate_fails_to_baseline_on_no_completed_bar() -> None:
    features = market_feature_frame(synthetic_bars())
    result = score_candidate(
        {
            "feature_columns": [
                "atr_ratio",
                "rv_1h",
                "rv_24h",
                "slope_atr",
                "ret_1h",
                "ret_4h",
                "ret_24h",
                "dist_hi_24h",
                "dist_lo_24h",
                "hour",
                "dow",
                "is_long",
                "is_core",
            ],
            "models": [],
            "historical_oos_score_reference": np.array([0.0]),
            "rank_threshold_exclusive": 0.8,
        },
        features,
        pd.Timestamp("2025-12-01T00:00:00Z"),
        is_long=True,
        is_core=True,
    )
    assert result == {"topup": False, "reason": "NO_COMPLETED_FEATURE_BAR"}


def test_feature_rows_are_finite_after_frozen_warmup() -> None:
    features = market_feature_frame(synthetic_bars())
    columns = [
        "atr_ratio",
        "rv_1h",
        "rv_24h",
        "slope_atr",
        "ret_1h",
        "ret_4h",
        "ret_24h",
        "dist_hi_24h",
        "dist_lo_24h",
        "hour",
        "dow",
    ]
    mature = features.loc[features["_history_ok"], columns]
    assert np.isfinite(mature.to_numpy(dtype=float)).all()
