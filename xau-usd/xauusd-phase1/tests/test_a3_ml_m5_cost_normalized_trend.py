from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ml.a3_meta_v1.dukascopy_label_factory import Candidate, Label
from ml.a3_meta_v1.m5_cost_normalized_trend import (
    M5CostNormalizedTrendError,
    _apply_portfolio_controls,
    _profile_candidates,
    _replay_profile,
    _stage_for_timestamp,
    _validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/ml/a3_ml_m5_cost_normalized_trend_v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _candidate(
    *, timestamp: str = "2019-01-01T10:00:00.000Z", atr: float = 2.0
) -> Candidate:
    return Candidate(
        candidate_id="base",
        family_id="lane",
        symbol="XAUUSD",
        split="prehistory",
        direction="LONG",
        signal_bar_start_utc="2019-01-01T09:55:00.000Z",
        decision_time_utc=timestamp,
        decision_timestamp_ms=int(pd.Timestamp(timestamp).timestamp() * 1000),
        signal_open=100.0,
        signal_high=101.0,
        signal_low=99.0,
        signal_close=100.5,
        ema_fast=100.0,
        ema_slow=99.0,
        ema_fast_slope_atr=0.1,
        atr=atr,
        body_fraction=0.5,
        close_location=0.75,
        touch_distance_atr=0.2,
        stop_distance=5.0,
        stop_distance_atr=2.5,
        reward_r=0.7,
        signal_tick_count=100,
    )


def test_contract_is_exact_and_fail_closed() -> None:
    contract = _contract()
    _validate_contract(contract)
    assert not any(contract["authorization"].values())
    assert not contract["selection"]["ml_ranking_authorized"]


def test_contract_rejects_geometry_or_trigger_changes() -> None:
    geometry = _contract()
    geometry["geometry_profiles"][0]["reward_r"] = 1.1
    with pytest.raises(M5CostNormalizedTrendError, match="geometry profiles"):
        _validate_contract(geometry)
    trigger = _contract()
    trigger["source_lock"]["candidate_threshold_changes_authorized"] = True
    with pytest.raises(M5CostNormalizedTrendError, match="threshold changes"):
        _validate_contract(trigger)


def test_profile_geometry_uses_locked_atr_floor_and_stage() -> None:
    profiled = _profile_candidates([_candidate(atr=1.0)], _contract())
    assert len(profiled) == 3
    assert {row.stop_distance for row in profiled} == {7.0, 8.0}
    assert {row.reward_r for row in profiled} == {1.0, 1.5, 2.0}
    assert {row.split for row in profiled} == {"DEVELOPMENT"}
    assert len({row.candidate_id for row in profiled}) == 3


def test_profile_rejects_risk_above_fifty_dollars() -> None:
    profiled = _profile_candidates([_candidate(atr=20.0)], _contract())
    assert profiled == []


def test_stage_windows_are_left_closed_and_right_open() -> None:
    contract = _contract()
    assert _stage_for_timestamp("2020-06-30T23:59:59Z", contract) == "DEVELOPMENT"
    assert _stage_for_timestamp("2020-07-01T00:00:00Z", contract) == "VALIDATION"
    assert _stage_for_timestamp("2022-07-01T00:00:00Z", contract) == "INTERNAL_TEST"
    assert _stage_for_timestamp("2024-07-01T00:00:00Z", contract) == "EXAM"
    assert _stage_for_timestamp("2026-07-01T00:00:00Z", contract) is None


def test_portfolio_controls_enforce_cost_direction_and_daily_caps() -> None:
    rows = []
    for index in range(7):
        rows.append(
            {
                "candidate_id": str(index),
                "status": "RESOLVED",
                "entry_time_utc": f"2020-01-01T10:{index:02d}:00Z",
                "exit_time_utc": "2020-01-01T12:00:00Z",
                "direction": "LONG" if index < 5 else "SHORT",
                "immediate_cost_r": 0.10 if index != 0 else 0.16,
                "risk_usd": 7.0,
            }
        )
    selected, reasons = _apply_portfolio_controls(pd.DataFrame(rows), _contract())
    assert len(selected) == 2
    assert set(selected["direction"]) == {"LONG", "SHORT"}
    assert reasons["immediate_cost_r"] == 1
    assert reasons["maximum_same_direction"] == 3
    assert reasons["maximum_concurrent"] == 1


def test_portfolio_control_tie_break_is_deterministic() -> None:
    frame = pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "status": "RESOLVED",
                "entry_time_utc": "2020-01-01T10:00:00Z",
                "exit_time_utc": "2020-01-01T11:00:00Z",
                "direction": "LONG",
                "immediate_cost_r": 0.1,
                "risk_usd": 7.0,
            }
            for candidate_id in ("b", "a")
        ]
    )
    selected, _ = _apply_portfolio_controls(frame, _contract())
    assert selected["candidate_id"].tolist() == ["a"]


def test_replay_applies_spread_floor_and_segment_boundary(monkeypatch) -> None:
    candidate = _profile_candidates([_candidate(atr=1.0)], _contract())[0]

    def fake_replay(*_args, **_kwargs):
        return [
            Label(
                candidate_id=candidate.candidate_id,
                family_id=candidate.family_id,
                symbol="XAUUSD",
                split="DEVELOPMENT",
                direction="LONG",
                decision_time_utc=candidate.decision_time_utc,
                status="RESOLVED",
                entry_time_utc="2019-01-01T10:00:00.000Z",
                exit_time_utc="2020-07-01T00:00:00.000Z",
                entry_price=100.5,
                exit_price=110.5,
                entry_bid=100.0,
                entry_ask=100.5,
                entry_spread=0.5,
                planned_stop=93.5,
                planned_target=107.5,
                stop_distance=7.0,
                reward_r=1.0,
                exit_reason="TARGET",
                duration_hours=24.0,
                gross_pnl_usd=10.0,
                execution_stress_usd=0.3,
                holding_stress_usd=0.35,
                stress_net_pnl_usd=9.35,
                gross_r=10.0 / 7.0,
                stress_net_r=9.35 / 7.0,
                mfe_r=1.0,
                mae_r=0.0,
                label_profitable_after_stress=1,
                signal_open=candidate.signal_open,
                signal_high=candidate.signal_high,
                signal_low=candidate.signal_low,
                signal_close=candidate.signal_close,
                ema_fast=candidate.ema_fast,
                ema_slow=candidate.ema_slow,
                ema_fast_slope_atr=candidate.ema_fast_slope_atr,
                atr=candidate.atr,
                body_fraction=candidate.body_fraction,
                close_location=candidate.close_location,
                touch_distance_atr=candidate.touch_distance_atr,
                stop_distance_atr=candidate.stop_distance_atr,
                signal_tick_count=candidate.signal_tick_count,
            )
        ]

    monkeypatch.setattr(
        "ml.a3_meta_v1.m5_cost_normalized_trend.replay_candidates", fake_replay
    )
    result = _replay_profile(
        [candidate],
        [],
        object(),
        _contract()["geometry_profiles"][0],
        _contract(),
        "DEVELOPMENT",
    )
    assert result.loc[0, "spread_floor_uplift_usd"] == pytest.approx(0.25)
    assert result.loc[0, "stress_net_pnl_usd"] == pytest.approx(9.10)
    assert result.loc[0, "stress_net_r"] == pytest.approx(1.3)
    assert result.loc[0, "immediate_cost_r"] == pytest.approx(0.15)
    assert result.loc[0, "status"] == "SEGMENT_CROSS"
