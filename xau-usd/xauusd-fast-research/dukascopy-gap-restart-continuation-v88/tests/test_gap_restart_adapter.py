from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from gap_restart_adapter import (
    generate_candidates,
    label_candidates,
    session_quality,
    v26_candidate_config,
)
from gap_restart import generate_candidates as generate_v26_candidates


ROOT = Path(__file__).resolve().parents[1]


def config() -> dict:
    return json.loads(
        (ROOT / "config" / "dukascopy_gap_restart_continuation_v88.json")
        .read_text()
    )


def quotes(gap_ms: int = 2300, direction: int = 1) -> pd.DataFrame:
    start = int(pd.Timestamp("2019-01-02T07:00:00Z").timestamp() * 1000)
    before = [start, start + 100, start + 200]
    restart = before[-1] + gap_ms
    after = [restart + index * 100 for index in range(35)]
    mid = [1280.0] * len(before)
    mid += [1280.0 + direction * 0.10 * index for index in range(len(after))]
    return pd.DataFrame(
        {
            "timestamp_ms": before + after,
            "bid": [value - 0.10 for value in mid],
            "ask": [value + 0.10 for value in mid],
            "mid": mid,
        }
    )


def test_adapter_is_byte_semantic_parity_with_locked_v26_constructor() -> None:
    values = config()
    date = pd.Timestamp("2019-01-02T00:00:00Z")
    frame = quotes()
    adapted, audit = generate_candidates(
        date, frame, rule=values["candidate_rule"]
    )
    ticks = frame.rename(columns={"timestamp_ms": "tick_time_msc"}).copy()
    ticks["spread_price"] = ticks["ask"] - ticks["bid"]
    direct, direct_audit = generate_v26_candidates(
        ticks, v26_candidate_config(values["candidate_rule"])
    )
    assert audit == direct_audit
    assert len(adapted) == len(direct) == 1
    assert int(adapted.iloc[0]["decision_timestamp_ms"]) == int(
        direct.iloc[0]["tick_time_msc"]
    )
    assert adapted.iloc[0]["direction"] == direct.iloc[0]["candidate_side"]


def test_gap_outside_frozen_range_produces_no_candidate() -> None:
    values = config()
    date = pd.Timestamp("2019-01-02T00:00:00Z")
    for gap in (2000, 5001):
        candidate, _ = generate_candidates(
            date, quotes(gap_ms=gap), rule=values["candidate_rule"]
        )
        assert candidate.empty


def test_candidate_is_causal_under_future_append() -> None:
    values = config()
    date = pd.Timestamp("2019-01-02T00:00:00Z")
    frame = quotes()
    candidate, _ = generate_candidates(
        date, frame, rule=values["candidate_rule"]
    )
    cutoff = int(candidate.iloc[0]["decision_timestamp_ms"])
    prefix = frame.loc[frame["timestamp_ms"].le(cutoff)]
    prefix_candidate, _ = generate_candidates(
        date, prefix, rule=values["candidate_rule"]
    )
    columns = ["candidate_id", "decision_timestamp_ms", "direction"]
    pd.testing.assert_frame_equal(
        candidate[columns].reset_index(drop=True),
        prefix_candidate[columns].reset_index(drop=True),
    )


def test_short_direction_follows_restart_imbalance() -> None:
    values = config()
    candidate, _ = generate_candidates(
        pd.Timestamp("2019-01-02T00:00:00Z"),
        quotes(direction=-1),
        rule=values["candidate_rule"],
    )
    assert candidate.iloc[0]["direction"] == "SHORT"


def test_side_correct_label_includes_ticket_and_slippage() -> None:
    values = config()
    values["execution"]["hold_seconds"] = 1
    date = pd.Timestamp("2019-01-02T00:00:00Z")
    frame = quotes()
    candidate, _ = generate_candidates(date, frame, rule=values["candidate_rule"])
    labels = label_candidates(candidate, quotes=frame, config=values)
    assert labels.iloc[0]["status"] == "RESOLVED"
    decision = int(candidate.iloc[0]["decision_timestamp_ms"])
    entry = frame.loc[frame["timestamp_ms"] > decision].iloc[0]
    target = int(entry["timestamp_ms"]) + 1000
    exit_quote = frame.loc[frame["timestamp_ms"] >= target].iloc[0]
    observed = float(exit_quote["bid"] - entry["ask"])
    expected = observed - 0.10 - 0.30
    assert abs(float(labels.iloc[0]["baseline_net_pnl_usd"]) - expected) < 1e-12


def test_session_quality_rejects_partial_day() -> None:
    values = config()
    quality = session_quality(
        pd.Timestamp("2019-01-02T00:00:00Z"),
        quotes(),
        values["candidate_rule"],
    )
    assert quality["eligible_full_weekday"] is False
