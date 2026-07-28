from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_london_fix_reversal import (
    build_candidates,
    is_calendar_month_end_weekday,
    london_fix_utc,
    simulate,
)


def _config() -> dict:
    return {
        "strategy": {
            "pre_fix_completed_m5_bars": 12,
            "magnitude_lookback_observations": 2,
        },
        "windows": {
            "development_a_2019_2020": [
                "2019-01-01T00:00:00Z",
                "2020-12-31T23:59:59Z",
            ],
            "development_b_2021_2022": [
                "2021-01-01T00:00:00Z",
                "2022-12-31T23:59:59Z",
            ],
            "chronological_2023": [
                "2023-01-01T00:00:00Z",
                "2023-12-31T23:59:59Z",
            ],
            "chronological_2024": [
                "2024-01-01T00:00:00Z",
                "2024-12-31T23:59:59Z",
            ],
            "chronological_2025": [
                "2025-01-01T00:00:00Z",
                "2025-12-31T23:59:59Z",
            ],
            "recent_2026_h1": [
                "2026-01-01T00:00:00Z",
                "2026-06-30T23:59:59Z",
            ],
        },
        "outcome_blind_census": {
            "minimum_candidates_total": 0,
            "minimum_candidates_development": 0,
            "minimum_candidates_each_full_forward_year": 0,
            "minimum_candidates_recent_half_year": 0,
            "minimum_candidates_each_side": 0,
            "minimum_month_end_candidates_total": 0,
        },
    }


def _points() -> pd.DataFrame:
    dates = ["2022-06-27", "2022-06-28", "2022-06-29"]
    return pd.DataFrame(
        {
            "eligible_date": dates,
            "clock_minute": [0, 0, 0],
            "decision_id": dates,
            "entry_time_utc": pd.to_datetime(
                [f"{date}T00:00:00Z" for date in dates], utc=True
            ),
        }
    )


def _prices() -> pd.DataFrame:
    index = pd.date_range(
        "2022-06-27T14:00:00Z",
        "2022-06-29T15:10:00Z",
        freq="5min",
    )
    base = pd.Series(range(len(index)), index=index) * 0.00001 + 1.1
    frame = pd.DataFrame(
        {
            "bid_open": base,
            "bid_high": base + 0.0001,
            "bid_low": base - 0.0001,
            "bid_close": base + 0.00005,
            "ask_open": base + 0.00008,
            "ask_high": base + 0.00018,
            "ask_low": base - 0.00002,
            "ask_close": base + 0.00013,
        },
        index=index,
    )
    for date in ("2022-06-27", "2022-06-28", "2022-06-29"):
        fix = london_fix_utc(date)
        frame.loc[fix, "bid_close"] = frame.loc[fix, "bid_open"] - 0.0003
        frame.loc[fix, "ask_close"] = frame.loc[fix, "ask_open"] - 0.0003
    return frame


def test_london_fix_uses_dst_aware_utc_clock() -> None:
    assert london_fix_utc("2022-01-10") == pd.Timestamp(
        "2022-01-10T16:00:00Z"
    )
    assert london_fix_utc("2022-06-10") == pd.Timestamp(
        "2022-06-10T15:00:00Z"
    )


def test_calendar_month_end_is_last_weekday() -> None:
    assert is_calendar_month_end_weekday("2022-06-30") is True
    assert is_calendar_month_end_weekday("2022-07-29") is True
    assert is_calendar_month_end_weekday("2022-07-28") is False


def test_candidate_requires_only_prior_threshold_and_fix_bar() -> None:
    candidates, census = build_candidates(
        _points(), _prices(), _config()
    )
    assert len(candidates) == 1
    assert candidates["eligible_date"].iloc[0] == "2022-06-29"
    assert candidates["side"].iloc[0] == "SHORT"
    assert census["passed"] is True


def test_entry_bar_cannot_change_signal() -> None:
    prices = _prices()
    first, _ = build_candidates(_points(), prices, _config())
    altered = prices.copy()
    entry = london_fix_utc("2022-06-29") + pd.Timedelta(minutes=5)
    altered.loc[
        entry,
        [
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_high",
            "ask_low",
            "ask_close",
        ],
    ] = [9.0, 8.0, 8.5, 9.1, 8.1, 8.6]
    second, _ = build_candidates(_points(), altered, _config())
    assert len(first) == len(second) == 1
    assert first["side"].iloc[0] == second["side"].iloc[0]
    assert first["pre_fix_displacement_pips"].iloc[0] == (
        second["pre_fix_displacement_pips"].iloc[0]
    )


def test_same_bar_stop_and_target_resolves_stop_first() -> None:
    entry = pd.Timestamp("2022-06-29T15:05:00Z")
    candidates = pd.DataFrame(
        {
            "entry_time_utc": [entry],
            "expert": ["ORDINARY_FIX_REVERSAL"],
            "side": ["LONG"],
            "eligible_date": ["2022-06-29"],
            "fix_time_utc": [
                pd.Timestamp("2022-06-29T15:00:00Z")
            ],
            "confirmation_bid_low": [1.0998],
            "confirmation_ask_high": [1.1003],
            "pre_fix_displacement_pips": [-5.0],
            "confirmation_displacement_pips": [2.0],
            "prior_20_median_abs_displacement_pips": [4.0],
        }
    )
    m5 = pd.DataFrame(
        {
            "bid_open": [1.1000],
            "bid_high": [1.1020],
            "bid_low": [1.0990],
            "bid_close": [1.1000],
            "ask_open": [1.1001],
            "ask_high": [1.1021],
            "ask_low": [1.0991],
            "ask_close": [1.1001],
        },
        index=pd.DatetimeIndex([entry]),
    )
    cfg = {
        "execution": {
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
        },
        "strategy": {
            "stop_buffer_pips": 0.5,
            "stop_floor_pips": 4.0,
            "stop_ceiling_pips": 25.0,
            "target_r": 1.5,
            "maximum_hold_hours": 12,
        },
    }
    trades, _ = simulate(candidates, m5, cfg)
    assert len(trades) == 1
    assert trades["exit_reason"].iloc[0] == "STOP"
