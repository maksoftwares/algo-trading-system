from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_selective_post_event import (  # noqa: E402
    _side_rows,
    add_features,
)


def config() -> dict:
    return {
        "features": {
            "side_aligned_columns": [
                "aligned_impulse_pips",
                "aligned_pre_event_return_15m_pips",
                "aligned_pre_event_return_60m_pips",
                "aligned_pre_event_return_240m_pips",
                "own_risk_pips",
                "risk_advantage_pips",
            ],
            "shared_columns": [
                "observation_range_pips",
                "observation_range_to_prior_median",
                "event_hour_sin",
                "event_hour_cos",
                "event_has_eur",
                "event_has_usd",
                "log1p_event_cluster_size",
            ],
            "model_column_count": 13,
            "pre_event_history_bars": 288,
            "minimum_pre_event_history_bars": 49,
            "prior_range_median_bars": 288,
        }
    }


def m5() -> pd.DataFrame:
    index = pd.date_range(
        "2024-01-05T00:00:00Z", periods=60, freq="5min"
    )
    base = 1.10 + np.arange(len(index)) * 0.00001
    return pd.DataFrame(
        {
            "bid_open": base,
            "bid_high": base + 0.0002,
            "bid_low": base - 0.0002,
            "bid_close": base + 0.00005,
            "ask_open": base + 0.0001,
            "ask_high": base + 0.0003,
            "ask_low": base - 0.0001,
            "ask_close": base + 0.00015,
        },
        index=index,
    )


def candidates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pair_id": ["2024-01-05:EVENT"],
            "eligible_date": ["2024-01-05"],
            "event_time_utc": pd.to_datetime(
                ["2024-01-05T04:04:00Z"], utc=True
            ),
            "event_currencies": ["EUR|USD"],
            "event_cluster_size": [2],
            "observation_start_utc": pd.to_datetime(
                ["2024-01-05T04:05:00Z"], utc=True
            ),
            "entry_time_utc": pd.to_datetime(
                ["2024-01-05T04:20:00Z"], utc=True
            ),
            "impulse_pips": [6.0],
            "observation_range_pips": [8.0],
            "risk_pips_long": [5.0],
            "risk_pips_short": [7.0],
        }
    )


def test_features_ignore_entry_and_future_bars() -> None:
    original, reasons = add_features(candidates(), m5(), config())
    changed_m5 = m5()
    changed_m5.loc[
        changed_m5.index
        >= pd.Timestamp("2024-01-05T04:20:00Z"),
        ["bid_close", "ask_close", "bid_high", "ask_high"],
    ] = 9.0
    changed, changed_reasons = add_features(
        candidates(), changed_m5, config()
    )
    columns = [
        "pre_event_return_15m_pips",
        "pre_event_return_60m_pips",
        "pre_event_return_240m_pips",
        "observation_range_to_prior_median",
        "event_hour_sin",
        "event_hour_cos",
    ]
    assert reasons == {"insufficient_pre_event_history": 0}
    assert changed_reasons == reasons
    assert original.loc[0, columns].to_numpy(dtype=float) == pytest.approx(
        changed.loc[0, columns].to_numpy(dtype=float)
    )


def test_side_stacking_aligns_direction_and_risk() -> None:
    featured, _ = add_features(candidates(), m5(), config())
    stacked = _side_rows(featured, config())
    long = stacked[stacked["side"].eq("LONG")].iloc[0]
    short = stacked[stacked["side"].eq("SHORT")].iloc[0]
    assert long["aligned_impulse_pips"] == pytest.approx(6.0)
    assert short["aligned_impulse_pips"] == pytest.approx(-6.0)
    assert long["own_risk_pips"] == pytest.approx(5.0)
    assert short["own_risk_pips"] == pytest.approx(7.0)
    assert long["risk_advantage_pips"] == pytest.approx(2.0)
    assert short["risk_advantage_pips"] == pytest.approx(-2.0)
    assert long["event_has_eur"] == short["event_has_eur"] == 1.0
