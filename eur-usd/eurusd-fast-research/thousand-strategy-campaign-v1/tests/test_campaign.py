from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.campaign import (  # noqa: E402
    ARCHETYPES,
    Candidate,
    benjamini_hochberg,
    build_candidate_manifest,
    month_keys,
    profit_factor,
    simulate,
    summarize_family_results,
)


def config() -> dict:
    return json.loads(
        (ROOT / "config" / "eurusd_thousand_strategy_campaign_v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_manifest_is_exactly_one_thousand_unique_candidates() -> None:
    candidates = build_candidate_manifest()

    assert len(candidates) == 1000
    assert len({candidate.sha256 for candidate in candidates}) == 1000
    assert len({candidate.candidate_id for candidate in candidates}) == 1000
    assert {candidate.archetype for candidate in candidates} == {
        row[0] for row in ARCHETYPES
    }
    assert all(
        sum(candidate.archetype == archetype for candidate in candidates) == 100
        for archetype, *_ in ARCHETYPES
    )


def test_source_contract_contains_exactly_120_months() -> None:
    months = month_keys(
        "2016-07-01T00:00:00Z", "2026-07-01T00:00:00Z"
    )

    assert len(months) == 120
    assert months[0] == "2016-07"
    assert months[-1] == "2026-06"


def test_simulator_uses_next_contiguous_ask_and_stop_first() -> None:
    timestamps = pd.date_range("2020-01-01", periods=4, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "atr": [0.0010] * 4,
            "bid_open": [1.1000, 1.1000, 1.1000, 1.1000],
            "bid_high": [1.1001, 1.1020, 1.1001, 1.1001],
            "bid_low": [1.0999, 1.0980, 1.0999, 1.0999],
            "bid_close": [1.1000] * 4,
            "ask_open": [1.1001, 1.1001, 1.1001, 1.1001],
            "ask_high": [1.1002, 1.1021, 1.1002, 1.1002],
            "ask_low": [1.1000, 1.0981, 1.1000, 1.1000],
            "ask_close": [1.1001] * 4,
        }
    )
    candidate = Candidate(
        candidate_id="TEST",
        attempt=1,
        archetype="range_breakout_long",
        direction="long",
        threshold=0,
        stop_atr=1,
        target_r=1,
        max_hold_bars=2,
        sha256="x",
    )
    trades = simulate(
        frame,
        candidate,
        np.asarray([True, False, False, False]),
        pd.Timestamp("2020-01-01", tz="UTC"),
        pd.Timestamp("2020-01-02", tz="UTC"),
        config(),
    )

    assert len(trades) == 1
    assert trades[0]["entry_time"] == timestamps[1].isoformat()
    assert trades[0]["exit_reason"] == "stop"
    assert trades[0]["entry"] > frame.loc[1, "ask_open"]


def test_noncontiguous_signal_cannot_enter() -> None:
    timestamps = pd.to_datetime(
        ["2020-01-01T00:00:00Z", "2020-01-01T02:00:00Z"]
    )
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "atr": [0.001, 0.001],
            "bid_open": [1.1, 1.1],
            "bid_high": [1.1, 1.1],
            "bid_low": [1.1, 1.1],
            "bid_close": [1.1, 1.1],
            "ask_open": [1.1001, 1.1001],
            "ask_high": [1.1001, 1.1001],
            "ask_low": [1.1001, 1.1001],
            "ask_close": [1.1001, 1.1001],
        }
    )
    candidate = build_candidate_manifest()[0]
    trades = simulate(
        frame,
        candidate,
        np.asarray([True, False]),
        pd.Timestamp("2020-01-01", tz="UTC"),
        pd.Timestamp("2020-01-02", tz="UTC"),
        config(),
    )

    assert trades == []


def test_profit_factor_and_bh_are_deterministic() -> None:
    assert profit_factor([2.0, -1.0, 1.0, -1.0]) == 1.5
    adjusted = benjamini_hochberg({"a": 0.01, "b": 0.04, "c": 0.20})
    assert adjusted == pytest.approx({"c": 0.20, "b": 0.06, "a": 0.03})


def test_research_controls_prohibit_runtime_and_post_outcome_tuning() -> None:
    controls = config()["research_controls"]

    assert controls["same_version_post_outcome_tuning_authorized"] is False
    assert controls["h1_screen_can_authorize_strategy"] is False
    assert controls["mt5_run_authorized"] is False
    assert controls["ea_implementation_authorized"] is False
    assert controls["reviewer_submission_authorized"] is False
    assert controls["chart_demo_live_shadow_authorized"] is False
    assert controls["broker_action_authorized"] is False


def test_family_summary_excludes_tiny_infinite_profit_factor() -> None:
    rows = []
    for archetype, *_ in ARCHETYPES:
        for stage in ("discovery_fit", "discovery_confirm"):
            rows.append(
                {
                    "candidate_id": f"{archetype}_{stage}",
                    "archetype": archetype,
                    "stage": stage,
                    "trades": 3,
                    "stress_profit_factor": float("inf"),
                    "stage_gate_pass": False,
                }
            )

    summary = summarize_family_results(rows)

    assert all(row["best_minimum_trade_stress_pf"] is None for row in summary)
