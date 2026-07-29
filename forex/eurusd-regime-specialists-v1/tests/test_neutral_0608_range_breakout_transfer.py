from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_0608_range_breakout_transfer import (  # noqa: E402
    assign_neutral_ownership,
    build_candidates,
    generate_session_signals,
    load_config,
    summarize_census,
)


def synthetic_config() -> dict:
    cfg = copy.deepcopy(load_config())
    cfg["strategy"].update(
        {
            "atr_period_m15": 1,
            "d1_atr_period": 1,
            "range_atr_min": 0.01,
            "range_atr_max": 100.0,
            "daily_range_atr_min": 0.0,
        }
    )
    cfg["windows"] = {
        "development_2019_2022": [
            "2026-01-02T00:00:00Z",
            "2026-01-02T23:59:59Z",
        ],
        "validation_2023": [
            "2027-01-01T00:00:00Z",
            "2027-01-01T23:59:59Z",
        ],
        "validation_2024": [
            "2028-01-01T00:00:00Z",
            "2028-01-01T23:59:59Z",
        ],
        "pseudo_oos_2025": [
            "2029-01-01T00:00:00Z",
            "2029-01-01T23:59:59Z",
        ],
        "pseudo_oos_2026h1": [
            "2030-01-01T00:00:00Z",
            "2030-01-01T23:59:59Z",
        ],
    }
    cfg["recent_six_months"] = [
        "2026-01-02T00:00:00Z",
        "2026-01-02T23:59:59Z",
    ]
    cfg["outcome_blind_capacity_gates"] = {
        "minimum_risk_eligible_candidates_total": 1,
        "minimum_distinct_candidate_dates_total": 1,
        "minimum_candidates_development_2019_2022": 1,
        "minimum_candidates_each_full_oos_year": 0,
        "minimum_candidates_pseudo_oos_2026h1": 0,
        "minimum_candidates_each_side": 0,
        "minimum_recent_six_month_candidates": 1,
        "maximum_candidate_state_known_lag_hours": 4.0,
    }
    return cfg


def synthetic_m5() -> pd.DataFrame:
    index = pd.date_range(
        "2026-01-01T00:00:00Z",
        "2026-01-02T08:15:00Z",
        freq="5min",
    )
    mid_open = np.full(len(index), 1.10000)
    mid_close = np.full(len(index), 1.10000)
    mid_high = np.full(len(index), 1.10005)
    mid_low = np.full(len(index), 1.09995)
    signal = (
        (index >= pd.Timestamp("2026-01-02T08:00:00Z"))
        & (index < pd.Timestamp("2026-01-02T08:15:00Z"))
    )
    mid_open[signal] = [1.10010, 1.10045, 1.10075]
    mid_close[signal] = [1.10045, 1.10075, 1.10110]
    mid_high[signal] = [1.10050, 1.10080, 1.10115]
    mid_low[signal] = [1.10005, 1.10040, 1.10070]
    bid_open = mid_open - 0.00005
    bid_high = mid_high - 0.00005
    bid_low = mid_low - 0.00005
    bid_close = mid_close - 0.00005
    ask_open = mid_open + 0.00005
    ask_high = mid_high + 0.00005
    ask_low = mid_low + 0.00005
    ask_close = mid_close + 0.00005
    return pd.DataFrame(
        {
            "timestamp_ms": index.astype("int64") // 1_000_000,
            "bid_open": bid_open,
            "bid_high": bid_high,
            "bid_low": bid_low,
            "bid_close": bid_close,
            "ask_open": ask_open,
            "ask_high": ask_high,
            "ask_low": ask_low,
            "ask_close": ask_close,
            "tick_count": 100,
        },
        index=index,
    )


def synthetic_state(*, shock: bool = False) -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [
            pd.Timestamp("2026-01-02T07:00:00Z"),
            pd.Timestamp("2026-01-02T08:00:00Z"),
        ],
        name="timestamp_utc",
    )
    return pd.DataFrame(
        {
            "direction": ["NEUTRAL", "USD_UP"],
            "phase": ["UNRESOLVED", "TRANSITION"],
            "shock": [shock, False],
            "DXY_compressed": [False, False],
            "EURUSD_compressed": [False, False],
        },
        index=index,
    )


def test_completed_0608_range_breakout_selects_long() -> None:
    signals = generate_session_signals(
        synthetic_m5(),
        synthetic_config(),
    )
    assert len(signals) == 1
    assert signals.iloc[0]["side"] == "LONG"
    assert signals.iloc[0]["signal_complete_utc"] == pd.Timestamp(
        "2026-01-02T08:15:00Z"
    )


def test_incomplete_signal_bar_cannot_generate_candidate() -> None:
    frame = synthetic_m5().drop(
        pd.Timestamp("2026-01-02T08:10:00Z")
    )
    signals = generate_session_signals(frame, synthetic_config())
    assert signals.empty


def test_entry_bar_cannot_change_completed_signal_direction() -> None:
    frame = synthetic_m5()
    baseline = generate_session_signals(frame, synthetic_config())
    entry = pd.Timestamp("2026-01-02T08:15:00Z")
    frame.loc[
        entry,
        [
            "bid_open",
            "bid_high",
            "bid_low",
            "bid_close",
            "ask_open",
            "ask_high",
            "ask_low",
            "ask_close",
        ],
    ] = [
        1.0900,
        1.0901,
        1.0899,
        1.0900,
        1.0901,
        1.0902,
        1.0900,
        1.0901,
    ]
    changed = generate_session_signals(frame, synthetic_config())
    assert baseline.iloc[0]["side"] == changed.iloc[0]["side"]


def test_future_hourly_state_is_not_used() -> None:
    signals = generate_session_signals(
        synthetic_m5(),
        synthetic_config(),
    )
    owned = assign_neutral_ownership(
        signals,
        synthetic_state(),
        synthetic_config(),
    )
    assert owned.iloc[0]["matched_state_time_utc"] == pd.Timestamp(
        "2026-01-02T07:00:00Z"
    )
    assert bool(owned.iloc[0]["neutral_owned"])


def test_shock_state_routes_signal_to_cash() -> None:
    candidates = build_candidates(
        synthetic_m5(),
        synthetic_state(shock=True),
        synthetic_config(),
    )
    assert len(candidates) == 1
    assert not bool(candidates.iloc[0]["neutral_owned"])
    assert not bool(candidates.iloc[0]["risk_eligible"])


def test_census_contains_no_outcome_or_oracle_fields() -> None:
    cfg = synthetic_config()
    candidates = build_candidates(
        synthetic_m5(),
        synthetic_state(),
        cfg,
    )
    census = summarize_census(candidates, cfg)
    assert census["census_pass"]
    assert census["stop_or_target_path_loaded"] is False
    assert census["eurusd_return_loaded"] is False
    assert census["eurusd_pnl_loaded"] is False
    assert census["oracle_rows_loaded"] is False
    assert census["performance_gate_evaluated"] is False
    forbidden = {
        "r",
        "pnl",
        "return",
        "exit_time_utc",
        "exit_price",
        "exit_reason",
        "oracle_member",
    }
    assert not forbidden.intersection(candidates.columns)


def test_empty_census_fails_capacity_without_opening_outcomes() -> None:
    cfg = synthetic_config()
    census = summarize_census(pd.DataFrame(), cfg)
    assert not census["census_pass"]
    assert census["status"] == "CENSUS_FAIL_NO_PNL_ALLOWED"
    assert census["risk_eligible_candidates_total"] == 0
    assert census["eurusd_pnl_loaded"] is False
    assert census["oracle_rows_loaded"] is False
