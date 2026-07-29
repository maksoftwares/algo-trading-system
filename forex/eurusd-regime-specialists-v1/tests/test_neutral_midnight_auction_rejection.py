from __future__ import annotations

import inspect

import pandas as pd

from eurusd_regime_specialists import (
    neutral_midnight_auction_rejection as module,
)


def _config() -> dict:
    return {
        "strategy": {
            "weekdays_only": True,
            "observation_bars_m5": 3,
            "minimum_failed_excursion_pips": 3.0,
            "maximum_opening_range_pips": 20.0,
            "minimum_rejection_wick_fraction": 0.55,
        },
        "neutral_ownership": {
            "maximum_state_known_lag_hours": 4.0,
        },
        "execution_contract_locked_before_census": {
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
            "minimum_stop_distance_pips": 4.0,
            "maximum_risk_pips": 15.0,
        },
        "windows": {
            "development_2019_2022": [
                "2019-01-02T00:00:00Z",
                "2022-12-31T23:59:59Z",
            ],
            "validation_2023": [
                "2023-01-01T00:00:00Z",
                "2023-12-31T23:59:59Z",
            ],
            "validation_2024": [
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z",
            ],
            "pseudo_oos_2025": [
                "2025-01-01T00:00:00Z",
                "2025-12-31T23:59:59Z",
            ],
            "pseudo_oos_2026h1": [
                "2026-01-01T00:00:00Z",
                "2026-06-30T23:59:59Z",
            ],
        },
    }


def _m5_frame() -> tuple[pd.DataFrame, pd.Timestamp]:
    midnight = pd.Timestamp("2026-01-06T00:00:00Z")
    index = pd.date_range(
        midnight,
        periods=4,
        freq="5min",
    )
    frame = pd.DataFrame(
        {
            "bid_open": [1.1000, 1.1001, 1.1000, 1.0999],
            "bid_high": [1.1005, 1.1006, 1.1004, 1.1000],
            "bid_low": [1.0999, 1.0998, 1.0999, 1.0998],
            "bid_close": [1.1001, 1.1000, 1.0999, 1.0999],
            "ask_open": [1.10008, 1.10018, 1.10008, 1.09998],
            "ask_high": [1.10058, 1.10068, 1.10048, 1.10008],
            "ask_low": [1.09998, 1.09988, 1.09998, 1.09988],
            "ask_close": [1.10018, 1.10008, 1.09998, 1.09998],
        },
        index=index,
    )
    return frame, midnight


def test_completed_upward_failed_auction_fades_short() -> None:
    m5, midnight = _m5_frame()

    points = module.generate_auction_points(
        m5, _config(), dates=[midnight]
    )

    assert len(points) == 1
    assert points.iloc[0]["side"] == "SHORT"
    assert bool(points.iloc[0]["signal_eligible"])


def test_incomplete_observation_is_cash_by_omission() -> None:
    m5, midnight = _m5_frame()
    m5 = m5.drop(index=midnight + pd.Timedelta(minutes=5))

    points = module.generate_auction_points(
        m5, _config(), dates=[midnight]
    )

    assert points.empty


def test_entry_bar_cannot_change_signal() -> None:
    m5, midnight = _m5_frame()
    baseline = module.generate_auction_points(
        m5, _config(), dates=[midnight]
    )
    changed = m5.copy()
    entry = midnight + pd.Timedelta(minutes=15)
    changed.loc[entry, ["bid_high", "ask_high"]] = [
        1.5000,
        1.5001,
    ]

    after = module.generate_auction_points(
        changed, _config(), dates=[midnight]
    )

    assert after.iloc[0]["side"] == baseline.iloc[0]["side"]
    assert (
        after.iloc[0]["upper_wick_fraction"]
        == baseline.iloc[0]["upper_wick_fraction"]
    )


def test_stale_state_cannot_be_risk_eligible() -> None:
    m5, midnight = _m5_frame()
    entry = midnight + pd.Timedelta(minutes=15)
    owned = pd.DataFrame(
        {
            "family": ["TEST"],
            "entry_time_utc": [entry],
            "side": ["SHORT"],
            "auction_high": [1.10064],
            "auction_low": [1.09984],
            "neutral_owned": [True],
            "state_known_lag_hours": [4.25],
        }
    )

    candidates = module.add_decision_time_risk(
        owned, m5, _config()
    )

    assert not bool(candidates.iloc[0]["state_fresh"])
    assert not bool(candidates.iloc[0]["risk_eligible"])


def test_census_source_has_no_outcome_loader() -> None:
    source = inspect.getsource(module.run_census).lower()
    forbidden = (
        "load_oracle",
        "load_forward_path",
        "simulate_trade",
        "run_execution",
        "attach_oracle_matches",
    )

    assert all(token not in source for token in forbidden)


def test_preregistration_lock_verifies() -> None:
    checked = module.verify_lock()

    assert len(checked) >= 8
