from __future__ import annotations

import inspect

import numpy as np
import pandas as pd

from eurusd_regime_specialists import neutral_prior24_extreme_fade as module


def _config() -> dict:
    return {
        "strategy": {
            "weekdays_only": True,
            "prior_window_hours": 24,
            "required_m5_bars": 288,
            "lower_close_location_max": 0.2,
            "upper_close_location_min": 0.8,
            "minimum_body_fraction": 0.25,
        },
        "neutral_ownership": {
            "maximum_state_known_lag_hours": 4.0,
        },
        "execution_contract_locked_before_census": {
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
            "maximum_risk_pips": 40.0,
        },
    }


def _m5_frame() -> tuple[pd.DataFrame, pd.Timestamp]:
    entry = pd.Timestamp("2026-01-06T00:00:00Z")
    index = pd.date_range(
        entry - pd.Timedelta(hours=24),
        entry,
        freq="5min",
        tz="UTC",
    )
    close = np.linspace(1.1002, 1.1095, len(index))
    bid_open = close.copy()
    bid_close = close.copy()
    bid_high = np.full(len(index), 1.1100)
    bid_low = np.full(len(index), 1.1000)
    ask_offset = 0.00008
    frame = pd.DataFrame(
        {
            "bid_open": bid_open,
            "bid_high": bid_high,
            "bid_low": bid_low,
            "bid_close": bid_close,
            "ask_open": bid_open + ask_offset,
            "ask_high": bid_high + ask_offset,
            "ask_low": bid_low + ask_offset,
            "ask_close": bid_close + ask_offset,
        },
        index=index,
    )
    return frame, entry


def test_complete_prior24_extreme_high_fades_short() -> None:
    m5, entry = _m5_frame()

    points = module.generate_midnight_points(
        m5, _config(), entry_times=[entry]
    )

    assert len(points) == 1
    assert points.iloc[0]["side"] == "SHORT"
    assert bool(points.iloc[0]["signal_eligible"])
    assert points.iloc[0]["prior_m5_bars"] == 288


def test_incomplete_prior24_window_is_cash_by_omission() -> None:
    m5, entry = _m5_frame()
    m5 = m5.drop(index=m5.index[100])

    points = module.generate_midnight_points(
        m5, _config(), entry_times=[entry]
    )

    assert points.empty


def test_entry_bar_cannot_change_prior_direction() -> None:
    m5, entry = _m5_frame()
    baseline = module.generate_midnight_points(
        m5, _config(), entry_times=[entry]
    )
    changed = m5.copy()
    changed.loc[entry, ["bid_high", "ask_high"]] = [
        1.5000,
        1.5001,
    ]

    after = module.generate_midnight_points(
        changed, _config(), entry_times=[entry]
    )

    assert after.iloc[0]["side"] == baseline.iloc[0]["side"]
    assert (
        after.iloc[0]["close_location"]
        == baseline.iloc[0]["close_location"]
    )


def test_stale_state_cannot_be_risk_eligible() -> None:
    m5, entry = _m5_frame()
    owned = pd.DataFrame(
        {
            "family": ["TEST"],
            "entry_time_utc": [entry],
            "side": ["SHORT"],
            "prior_high": [1.11004],
            "prior_low": [1.10004],
            "prior_range": [0.0100],
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
    source = inspect.getsource(module.run_census)
    forbidden = (
        "load_oracle",
        "load_forward_path",
        "simulate_trade",
        "run_execution",
        "attach_oracle_matches",
    )

    assert all(token not in source.lower() for token in forbidden)


def test_preregistration_lock_verifies() -> None:
    checked = module.verify_lock()

    assert len(checked) >= 8
