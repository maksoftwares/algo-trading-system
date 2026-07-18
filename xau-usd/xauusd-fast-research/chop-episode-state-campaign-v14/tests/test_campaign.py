from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import (  # noqa: E402
    add_episode_features,
    signal_mask_direction,
    simulate_fixed_outcome,
)


def _base_frame() -> pd.DataFrame:
    starts = pd.date_range("2024-01-01T00:00:00Z", periods=12, freq="15min")
    close = np.linspace(100.0, 101.1, len(starts))
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "timestamp_utc": starts + pd.Timedelta(minutes=15),
            "mid_open": close - 0.05,
            "mid_high": close + 0.2,
            "mid_low": close - 0.2,
            "mid_close": close,
            "atr14": 1.0,
            "ema_fast": close,
            "ema_slow": close - 0.1,
            "body": 0.4,
            "upper_wick": 0.3,
            "lower_wick": 0.3,
            "candle_direction": 1,
            "efficiency_ratio": 0.5,
            "return_2_local": 0.4,
            "return_4_local": 0.6,
            "return_8_local": 0.8,
            "return_12_local": 1.0,
            "regime": [
                "TREND_UP",
                "TREND_UP",
                "CHOP",
                "CHOP",
                "CHOP",
                "CHOP",
                "TREND_DOWN",
                "CHOP",
                "CHOP",
                "CHOP",
                "CHOP",
                "CHOP",
            ],
        }
    )


def test_chop_age_resets_and_ancestry_is_causal() -> None:
    enriched = add_episode_features(_base_frame())
    assert enriched["chop_age_m15"].tolist() == [0, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 5]
    assert enriched.loc[2:5, "chop_ancestor"].eq("TREND_UP").all()
    assert enriched.loc[7:, "chop_ancestor"].eq("TREND_DOWN").all()
    assert enriched.loc[2:5, "ancestry_direction"].eq(1).all()
    assert enriched.loc[7:, "ancestry_direction"].eq(-1).all()
    assert enriched.loc[2:5, "bars_since_ancestor"].tolist() == [1.0, 2.0, 3.0, 4.0]


def test_episode_bounds_exclude_current_bar() -> None:
    enriched = add_episode_features(_base_frame())
    assert np.isnan(enriched.loc[2, "episode_high_prior"])
    assert enriched.loc[3, "episode_high_prior"] == _base_frame().loc[2, "mid_high"]
    expected = _base_frame().loc[2:4, "mid_high"].max()
    assert enriched.loc[5, "episode_high_prior"] == expected


def test_transition_between_trend_and_chop_preserves_directional_ancestry() -> None:
    frame = _base_frame()
    frame.loc[1, "regime"] = "TRANSITION_UNKNOWN"
    enriched = add_episode_features(frame)
    assert enriched.loc[2, "chop_ancestor"] == "TREND_UP"
    assert enriched.loc[2, "ancestry_direction"] == 1
    assert enriched.loc[2, "bars_since_ancestor"] == 2.0


def test_future_prices_do_not_change_prior_episode_features() -> None:
    frame = _base_frame()
    before = add_episode_features(frame)
    changed = frame.copy()
    changed.loc[10:, ["mid_open", "mid_high", "mid_low", "mid_close"]] += 100.0
    after = add_episode_features(changed)
    columns = [
        "chop_age_m15",
        "ancestry_direction",
        "episode_high_prior",
        "episode_low_prior",
    ]
    pd.testing.assert_frame_equal(before.loc[:9, columns], after.loc[:9, columns])


def test_fresh_continuation_uses_ancestor_direction() -> None:
    frame = add_episode_features(_base_frame())
    params = {
        "age_max": 8,
        "ancestry_max_bars": 128,
        "pullback_distance_atr": 0.25,
        "body_min": 0.1,
        "efficiency_min": 0.1,
        "require_slow_side": False,
        "hour_window": "ALL_LIQUID",
        "geometry_id": "C_SCALP",
    }
    frame["hour"] = 10
    mask, direction = signal_mask_direction(
        frame, "CHOP_FRESH_ANCESTRY_CONTINUATION", params
    )
    assert mask.loc[2:5].all()
    assert direction.loc[2:5].eq(1).all()
    assert not mask.loc[7:].any()
    assert direction.loc[7:].eq(-1).all()


def _execution_frame() -> pd.DataFrame:
    starts = pd.date_range("2024-01-02T10:00:00Z", periods=4, freq="15min")
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "timestamp_utc": starts + pd.Timedelta(minutes=15),
            "atr14": 1.0,
            "bid_open": [100.0, 100.0, 100.0, 100.0],
            "ask_open": [100.1, 100.1, 100.1, 100.1],
            "bid_high": [100.2, 101.7, 100.2, 100.2],
            "bid_low": [99.8, 99.0, 99.8, 99.8],
            "ask_high": [100.3, 101.8, 100.3, 100.3],
            "ask_low": [99.9, 99.1, 99.9, 99.9],
            "bid_close": [100.0, 100.0, 100.0, 100.0],
            "ask_close": [100.1, 100.1, 100.1, 100.1],
        }
    )


def test_same_bar_stop_wins_over_fixed_target() -> None:
    geometry = {
        "stop_atr": 0.75,
        "maximum_hold_hours": 4.0,
        "target_r": 1.5,
    }
    execution = {
        "maximum_entry_gap_minutes": 40,
        "maximum_entry_spread_r": 0.2,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.3,
        "holding_cost_per_24h_usd": 0.35,
        "stress_slippage_r": 0.05,
    }
    result = simulate_fixed_outcome(_execution_frame(), 0, 1, geometry, execution)
    assert result is not None
    assert result["exit_reason"] == "STOP"
    assert result["gross_r"] == -1.0
