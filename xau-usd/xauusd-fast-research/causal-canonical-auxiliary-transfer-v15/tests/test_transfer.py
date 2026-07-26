from __future__ import annotations

import numpy as np
import pandas as pd

from src.transfer import (
    CONTINUOUS_FEATURES,
    PASSTHROUGH_FEATURES,
    DomainNormalizer,
    canonical_features,
    exclude_overlapping_episodes,
)


def test_overlap_removes_entire_episode() -> None:
    auxiliary = pd.DataFrame(
        {
            "signal_time": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z", "2026-01-02T00:00:00Z"]
            ),
            "direction": ["LONG", "SHORT", "LONG"],
            "event_id": ["a", "b", "c"],
            "structural_episode_id": ["episode_1", "episode_1", "episode_2"],
            "stress_net_r_positive": [True, False, True],
        }
    )
    canonical = pd.DataFrame(
        {
            "decision_time": pd.to_datetime(["2026-01-01T00:00:00Z"]),
            "direction": ["LONG"],
        }
    )
    kept, audit = exclude_overlapping_episodes(auxiliary, canonical)
    assert kept["event_id"].tolist() == ["c"]
    assert audit["removed_structural_episodes"] == 1
    assert audit["removed_events"] == 2


def test_canonical_mapping_is_outcome_blind() -> None:
    frame = pd.DataFrame(
        {
            "xau_spread_last_atr": [0.2],
            "xau_quote_intensity_ratio_15m_60m": [1.1],
            "dir_xau_return_15m_atr": [0.1],
            "dir_xau_return_60m_atr": [0.2],
            "dir_xau_return_4h_atr": [0.3],
            "dir_xau_return_24h_atr": [0.4],
            "xau_range_60m_atr": [2.0],
            "dir_xau_tick_imbalance_5m": [0.01],
            "dir_xau_tick_imbalance_15m": [0.02],
            "target_r_filled": [2.0],
            "direction_sign": [1.0],
            "utc_hour_sin": [0.0],
            "utc_hour_cos": [1.0],
            "utc_weekday_sin": [0.5],
            "utc_weekday_cos": [0.5],
            "target_absent_flag": [0.0],
            "barrier_only_flag": [0.0],
            "planned_stop_atr": [1.5],
            "log1p_observation_cap_minutes": [np.log1p(720.0)],
            "broad_mechanic": ["BREAKOUT_OR_VOLATILITY_EXPANSION"],
            "stress_net_r": [-99.0],
        }
    )
    features = canonical_features(frame)
    assert "stress_net_r" not in features
    assert set(features) == set((*CONTINUOUS_FEATURES, *PASSTHROUGH_FEATURES))
    assert features.at[0, "mechanism_break_and_run"] == 1.0


def test_domain_normalizer_is_finite_with_missing_values() -> None:
    frame = pd.DataFrame(
        {
            **{
                column: [0.0, 1.0, np.nan, 3.0]
                for column in CONTINUOUS_FEATURES
            },
            **{column: [0.0, 1.0, 0.0, 1.0] for column in PASSTHROUGH_FEATURES},
        }
    )
    normalizer = DomainNormalizer.fit(frame, quantiles=4)
    transformed = normalizer.transform(frame)
    assert transformed.shape == (
        len(frame),
        len(CONTINUOUS_FEATURES) + len(PASSTHROUGH_FEATURES),
    )
    assert np.isfinite(transformed).all()
