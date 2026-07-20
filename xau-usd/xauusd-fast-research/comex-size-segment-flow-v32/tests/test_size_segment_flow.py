from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from size_segment_flow import (  # noqa: E402
    build_bar_features,
    circular_block_bootstrap_pvalue,
    generate_candidates,
    select_policy,
    session_trades,
)


RULE = {
    "family": "large_small_divergence_continuation",
    "timezone": "America/New_York",
    "session_start": "08:20",
    "session_end": "13:30",
    "bar_minutes": 5,
    "small_trade_maximum_size": 2,
    "minimum_small_volume": 50,
    "cooldown_minutes": 60,
    "minimum_session_coverage_minutes": 0,
    "minimum_nonempty_bars": 1,
}
POLICY = {
    "large_trade_size": 10,
    "minimum_large_volume": 40,
    "minimum_absolute_large_imbalance": 0.5,
    "minimum_absolute_opposing_small_imbalance": 0.2,
}


def _events() -> pd.DataFrame:
    start = pd.Timestamp("2024-01-02T13:20:00Z")
    rows = []
    for index in range(5):
        rows.append(
            {
                "ts_event": start + pd.Timedelta(seconds=index),
                "instrument_id": 7,
                "side": "B",
                "price": 2050.0 + index * 0.1,
                "size": 10,
            }
        )
    for index in range(30):
        rows.append(
            {
                "ts_event": start + pd.Timedelta(seconds=10 + index),
                "instrument_id": 7,
                "side": "A",
                "price": 2050.4,
                "size": 2,
            }
        )
    rows.append(
        {
            "ts_event": pd.Timestamp("2024-01-02T18:31:00Z"),
            "instrument_id": 7,
            "side": "B",
            "price": 2051.0,
            "size": 100,
        }
    )
    return pd.DataFrame(rows)


def test_completed_bar_generates_large_flow_direction() -> None:
    session = session_trades(_events(), RULE)
    assert len(session) == 35
    bars = build_bar_features(session, large_trade_size=10, rule=RULE)
    candidates = generate_candidates(bars, policy=POLICY, rule=RULE)
    assert len(candidates) == 1
    row = candidates.iloc[0]
    assert row["direction"] == "LONG"
    assert row["feature_time_utc"] == pd.Timestamp("2024-01-02T13:25:00Z")
    assert row["last_event_utc"] < row["feature_time_utc"]
    assert row["large_imbalance"] == 1.0
    assert row["small_imbalance"] == -1.0


def test_cooldown_is_global_and_does_not_fill_quota() -> None:
    times = pd.to_datetime(
        ["2024-01-02T13:25:00Z", "2024-01-02T13:55:00Z", "2024-01-02T14:25:00Z"],
        utc=True,
    )
    bars = pd.DataFrame(
        {
            "instrument_id": [1, 1, 1],
            "feature_time_utc": times,
            "large_volume": [100.0] * 3,
            "large_signed_volume": [100.0] * 3,
            "large_imbalance": [1.0] * 3,
            "small_volume": [100.0] * 3,
            "small_imbalance": [-1.0] * 3,
        }
    )
    candidates = generate_candidates(bars, policy=POLICY, rule=RULE)
    assert candidates["feature_time_utc"].tolist() == [times[0], times[2]]


def test_selector_uses_only_candidate_facts_and_strict_tiebreak() -> None:
    selection = {"target_candidates_per_full_weekday": 2.9}
    rows = [
        {
            "policy_id": "loose",
            "large_trade_size": 8,
            "minimum_large_volume": 40,
            "minimum_absolute_large_imbalance": 0.35,
            "minimum_absolute_opposing_small_imbalance": 0.1,
            "candidates_per_full_weekday": 2.8,
            "selection_eligible": True,
        },
        {
            "policy_id": "strict",
            "large_trade_size": 12,
            "minimum_large_volume": 80,
            "minimum_absolute_large_imbalance": 0.55,
            "minimum_absolute_opposing_small_imbalance": 0.3,
            "candidates_per_full_weekday": 3.0,
            "selection_eligible": True,
        },
    ]
    assert select_policy(rows, selection)["policy_id"] == "strict"
    assert not any("pnl" in key or "profit" in key for key in rows[0])


def test_bootstrap_is_deterministic_and_rejects_nonpositive_mean() -> None:
    values = np.array([1.0, 0.5, -0.1, 0.8, 0.2] * 8)
    first = circular_block_bootstrap_pvalue(
        values, block_length=5, resamples=500, seed=32
    )
    second = circular_block_bootstrap_pvalue(
        values, block_length=5, resamples=500, seed=32
    )
    assert first == second
    assert (
        circular_block_bootstrap_pvalue(-values, block_length=5, resamples=500, seed=32)
        == 1.0
    )
