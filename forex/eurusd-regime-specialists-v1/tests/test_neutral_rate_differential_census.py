from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_rate_differential_census import (
    build_candidates,
    build_common_curve,
    load_config,
    verify_lock,
)


def test_contract_is_frozen_before_candidate_count() -> None:
    lock = verify_lock()
    assert lock["frozen_before_candidate_count"] is True
    assert lock["eurusd_outcome_use_allowed"] is False


def test_common_curve_is_us_minus_euro() -> None:
    treasury = pd.DataFrame(
        {
            "observation_date": pd.to_datetime(
                ["2025-01-01", "2025-01-02"]
            ),
            "us_treasury_2y_percent": [4.0, 4.1],
        }
    )
    ecb = pd.DataFrame(
        {
            "observation_date": pd.to_datetime(
                ["2025-01-01", "2025-01-02"]
            ),
            "ecb_euro_area_aaa_2y_percent": [2.0, 2.0],
        }
    )
    common = build_common_curve(treasury, ecb)
    assert round(common.iloc[-1]["spread_percent"], 8) == 2.1
    assert round(common.iloc[-1]["spread_change_bps"], 8) == 10.0


def test_candidate_uses_two_day_lag_and_fixed_direction() -> None:
    config = load_config()
    config["capacity_gates"] = {
        "minimum_total_candidates": 0,
        "minimum_development_candidates": 0,
        "minimum_candidates_each_full_oos_year": 0,
        "minimum_candidates_2026_h1": 0,
        "minimum_candidates_each_side": 0,
    }
    neutral = pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2025-01-04T00:00:00Z", "2025-01-05T00:00:00Z"],
                utc=True,
            )
        }
    )
    common = pd.DataFrame(
        {
            "observation_date": pd.to_datetime(
                ["2024-12-31", "2025-01-02", "2025-01-03"]
            ),
            "us_treasury_2y_percent": [4.0, 4.1, 3.9],
            "ecb_euro_area_aaa_2y_percent": [2.0, 2.0, 2.0],
            "spread_percent": [2.0, 2.1, 1.9],
            "spread_change_bps": [float("nan"), 10.0, -20.0],
        }
    )
    candidates, _ = build_candidates(neutral, common, config)
    assert candidates["side"].tolist() == ["SHORT", "LONG"]
    assert candidates["observation_lag_calendar_days"].tolist() == [2, 2]
    assert candidates["observation_date"].tolist() == [
        "2025-01-02",
        "2025-01-03",
    ]
