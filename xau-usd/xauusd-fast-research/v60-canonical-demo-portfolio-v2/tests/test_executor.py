from __future__ import annotations

from datetime import UTC, datetime
import json

import pytest

from executor import (
    Candidate,
    candidate_prices,
    due_candidates,
    normalize_candidate,
    refresh_drawdown_state,
)


def source(**overrides):
    value = {
        "source_id": "R4_CHOP",
        "specialist_id": "R4_CHOP",
        "magic": 960401,
        "time_field": "scheduled_entry_time_utc",
        "stop_mode": "ATR",
        "target_r_default": 2.0,
        "maximum_entry_gap_minutes": 5,
        "maximum_spread_r": 0.15,
        "maximum_open_positions": 1,
        "maximum_entries_per_utc_day": 4,
    }
    value.update(overrides)
    return value


def test_normalizes_atr_candidate() -> None:
    candidate = normalize_candidate(
        {
            "candidate_id": "abc",
            "specialist_id": "R4_CHOP",
            "scheduled_entry_time_utc": "2026-07-21T01:00:00Z",
            "direction": "SHORT",
            "signal_atr": 4.0,
            "stop_atr": 1.25,
            "target_r": 2.0,
            "hold_hours": 12,
        },
        source(),
        0.01,
    )
    assert candidate is not None
    assert candidate.stop_distance == 5.0
    assert candidate.direction == "SHORT"
    assert candidate.hold_hours == 12.0


def test_r5_rejects_fractional_broker_weight() -> None:
    row = {
        "candidate_id": "r5",
        "specialist_id": "R5_TRANSITION",
        "scheduled_entry_time": "2026-07-21T01:00:00Z",
        "direction": "LONG",
        "signal_atr": 3.0,
        "stop_atr": 1.0,
        "origin_attempt": 24877,
        "risk_weight": 0.25,
    }
    assert (
        normalize_candidate(
            row,
            source(
                source_id="R5_TRANSITION",
                specialist_id="R5_TRANSITION",
                time_field="scheduled_entry_time",
                allowed_origin_attempts=[23925],
                required_risk_weight=1.0,
            ),
            0.01,
        )
        is None
    )


def test_prices_long_with_broker_side_stop_and_target() -> None:
    candidate = Candidate(
        candidate_id="a",
        source_id="R1_BOX",
        specialist_id="R1_UPTREND_LONG_V1",
        sleeve_type="CORE",
        magic=960101,
        scheduled_at=datetime(2026, 7, 21, tzinfo=UTC),
        direction="LONG",
        stop_distance=5.0,
        target_r=2.0,
        hold_hours=None,
        maximum_entry_gap_minutes=10,
        maximum_spread_r=0.15,
        maximum_open_positions=2,
        maximum_entries_per_utc_day=1,
        initial_risk_usd=5.0,
        event_id=None,
        raw={},
    )
    assert candidate_prices(
        candidate, bid=3300.0, ask=3300.5, digits=2, minimum_stop_distance=0.5
    ) == (3300.5, 3295.5, 3310.5)


def test_prices_reject_excessive_spread() -> None:
    candidate = Candidate(
        candidate_id="a",
        source_id="R2_DOWNTREND",
        specialist_id="R2_DOWNTREND",
        sleeve_type="CORE",
        magic=960201,
        scheduled_at=datetime(2026, 7, 21, tzinfo=UTC),
        direction="SHORT",
        stop_distance=2.0,
        target_r=None,
        hold_hours=12,
        maximum_entry_gap_minutes=10,
        maximum_spread_r=0.15,
        maximum_open_positions=4,
        maximum_entries_per_utc_day=4,
        initial_risk_usd=2.0,
        event_id=None,
        raw={},
    )
    with pytest.raises(ValueError, match="SPREAD_R_EXCEEDED"):
        candidate_prices(
            candidate, bid=3300.0, ask=3300.5, digits=2, minimum_stop_distance=0.1
        )


def test_closed_drawdown_suspend_and_resume_hysteresis() -> None:
    state = {
        "peak_equity_usd": 3000.0,
        "peak_closed_pnl_usd": 100.0,
        "closed_pnl_usd": 100.0,
        "closed_drawdown_usd": 0.0,
        "drawdown_suspended": False,
    }
    risk = {
        "closed_drawdown_suspend_usd": 225.0,
        "closed_drawdown_resume_usd": 180.0,
    }
    refresh_drawdown_state(state, equity=3000.0, closed_pnl=-130.0, risk=risk)
    assert state["drawdown_suspended"] is True
    refresh_drawdown_state(state, equity=3000.0, closed_pnl=-79.0, risk=risk)
    assert state["drawdown_suspended"] is False


def test_addon_candidate_carries_initial_risk_and_event_identity() -> None:
    candidate = normalize_candidate(
        {
            "candidate_id": "V7_event",
            "event_id": "20260721T010000Z_LONG",
            "specialist_id": "V7_SWING_HEALTH",
            "scheduled_entry_time_utc": "2026-07-21T01:00:00Z",
            "direction": "LONG",
            "signal_atr": 4.0,
            "stop_atr": 2.25,
            "target_r": 2.0,
            "hold_hours": 36.0,
        },
        source(
            source_id="V7_SWING_HEALTH",
            specialist_id="V7_SWING_HEALTH",
            sleeve_type="ADDON",
            magic=967007,
            time_field="scheduled_entry_time_utc",
            maximum_risk_usd=30.0,
        ),
        0.01,
    )
    assert candidate is not None
    assert candidate.sleeve_type == "ADDON"
    assert candidate.initial_risk_usd == 9.0
    assert candidate.event_id == "20260721T010000Z_LONG"


def test_addon_candidate_above_locked_risk_cap_is_not_executable() -> None:
    candidate = normalize_candidate(
        {
            "candidate_id": "too_large",
            "specialist_id": "V8_RETEST_HEALTH",
            "scheduled_entry_time_utc": "2026-07-21T01:00:00Z",
            "direction": "SHORT",
            "signal_atr": 15.0,
            "stop_atr": 1.5,
        },
        source(
            source_id="V8_RETEST_HEALTH",
            specialist_id="V8_RETEST_HEALTH",
            sleeve_type="ADDON",
            magic=968008,
            time_field="scheduled_entry_time_utc",
            maximum_risk_usd=20.0,
        ),
        0.01,
    )
    assert candidate is None


def test_due_candidates_deduplicates_identical_append_replay(tmp_path) -> None:
    row = {
        "candidate_id": "same",
        "specialist_id": "R4_CHOP",
        "scheduled_entry_time_utc": "2026-07-21T01:00:00Z",
        "direction": "LONG",
        "signal_atr": 4.0,
        "stop_atr": 1.0,
    }
    path = tmp_path / "candidates.jsonl"
    payload = json.dumps(row)
    path.write_text(payload + "\n" + payload + "\n", encoding="utf-8")
    config = {"sources": [source(path=str(path))]}
    state = {"activated_at_utc": "2026-07-21T00:00:00Z", "seen": {}}
    pending = due_candidates(
        config, state, 0.01, datetime(2026, 7, 21, 2, tzinfo=UTC)
    )
    assert [candidate.candidate_id for candidate in pending] == ["same"]
