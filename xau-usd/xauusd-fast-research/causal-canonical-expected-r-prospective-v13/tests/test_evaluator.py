from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluator import (
    _metrics,
    apply_portfolio_routing,
    build_numeric_features,
    canonical_hash,
    evaluate_stage,
    sha256_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads(
    (ROOT / "config" / "expected_r_prospective_v13.json").read_text(encoding="utf-8")
)


def _ticks(cutoff: pd.Timestamp) -> pd.DataFrame:
    times = np.arange(
        int((cutoff - pd.Timedelta(hours=25)).value // 1_000_000),
        int(cutoff.value // 1_000_000) + 1,
        60_000,
        dtype=np.int64,
    )
    mid = 2400.0 + np.linspace(0.0, 5.0, len(times))
    return pd.DataFrame(
        {
            "tick_time_msc": times,
            "bid": mid - 0.1,
            "ask": mid + 0.1,
        }
    )


def test_authority_is_disabled() -> None:
    controls = CONFIG["research_controls"]
    assert controls["individual_counterfactual_outcomes_authorized"] is True
    prohibited = {
        key: value
        for key, value in controls.items()
        if key.endswith("_authorized")
        and key != "individual_counterfactual_outcomes_authorized"
    }
    assert prohibited and not any(prohibited.values())


def test_numeric_feature_contract_is_complete() -> None:
    cutoff = pd.Timestamp("2026-07-28T12:00:00Z")
    candidate = {
        "family_id": "V7_SWING_HEALTH",
        "scheduled_entry_time_utc": cutoff.isoformat(),
        "direction": "LONG",
        "stop_distance": 8.0,
        "target_r": 2.0,
        "hold_hours": 36.0,
    }
    values, status = build_numeric_features(candidate, _ticks(cutoff), 4.0, CONFIG)
    assert status == "PASS"
    assert len(values) == 36
    assert values["planned_stop_atr"] == 2.0
    assert values["stop_floor_price"] == 3.5
    assert values["barrier_only_flag"] == 0.0


def test_r1_uses_barrier_cap() -> None:
    cutoff = pd.Timestamp("2026-07-28T12:00:00Z")
    candidate = {
        "family_id": "R1_UPTREND",
        "scheduled_entry_time_utc": cutoff.isoformat(),
        "direction": "LONG",
        "stop_distance": 8.0,
        "target_r": 2.0,
        "hold_hours": None,
    }
    values, status = build_numeric_features(candidate, _ticks(cutoff), 4.0, CONFIG)
    assert status == "PASS"
    assert values["barrier_only_flag"] == 1.0
    assert values["target_absent_flag"] == 0.0
    assert np.isclose(values["log1p_observation_cap_minutes"], np.log1p(129600.0))


def test_metrics_and_stage_gates() -> None:
    rows = []
    for index, value in enumerate((1.0, -0.2, 0.8, -0.1, 0.6, -0.3)):
        rows.append(
            {
                "candidate_id": f"C{index}",
                "family_id": "R4_CHOP" if index < 3 else "V7_SWING_HEALTH",
                "model_score": 0.5,
                "selected": index % 3 != 1,
                "exit_time_msc": index,
                "stress_net_r": value,
                "stress_pnl_usd_0p01": value * 5.0,
            }
        )
    frame = pd.DataFrame(rows)
    metrics = _metrics(frame)
    assert metrics["rows"] == 6
    assert metrics["stress_net_r"] > 0.0
    endpoint = {
        "stage": "validation",
        "eligible_dates": ["2026-07-27"],
        "start_date_utc": "2026-07-27",
        "end_date_utc": "2026-07-27",
        "candidate_ids": [row["candidate_id"] for row in rows],
        "executed_candidate_ids": [row["candidate_id"] for row in rows],
        "model_scored_candidate_ids": [row["candidate_id"] for row in rows],
    }
    audit = evaluate_stage("validation", endpoint, frame, CONFIG, "contract")
    assert audit["runtime_authorized"] is False
    assert audit["required_checks"] == 15


def test_portfolio_routing_enforces_account_initial_risk_cap() -> None:
    frame = pd.DataFrame(
        [
            {
                "candidate_id": "A",
                "source_id": "R2_DOWNTREND",
                "family_id": "R2_DOWNTREND",
                "sleeve_type": "CORE",
                "direction": "LONG",
                "initial_risk_usd": 40.0,
                "event_id": None,
                "maximum_open_positions": 4,
                "maximum_entries_per_utc_day": 4,
                "scheduled_entry_time_utc": "2026-07-27T01:00:00Z",
                "entry_time_msc": 1_000,
                "exit_time_msc": 5_000,
                "selected": True,
            },
            {
                "candidate_id": "B",
                "source_id": "R3_COMPRESSION",
                "family_id": "R3_COMPRESSION",
                "sleeve_type": "CORE",
                "direction": "LONG",
                "initial_risk_usd": 40.0,
                "event_id": None,
                "maximum_open_positions": 4,
                "maximum_entries_per_utc_day": 4,
                "scheduled_entry_time_utc": "2026-07-27T01:01:00Z",
                "entry_time_msc": 2_000,
                "exit_time_msc": 6_000,
                "selected": True,
            },
        ]
    )
    routed = apply_portfolio_routing(frame, CONFIG)
    assert routed["baseline_routed"].tolist() == [True, False]
    assert (
        routed.loc[1, "baseline_route_reason"]
        == "MAXIMUM_ACCOUNT_CONCURRENT_INITIAL_RISK"
    )


def test_portfolio_routing_applies_v57_same_direction_post_loss_cooldown() -> None:
    base = {
        "source_id": "V57_BREAK_SWING_H4ADX_HIGH",
        "family_id": "V57_BREAK_SWING_H4ADX_HIGH",
        "sleeve_type": "ADDON",
        "initial_risk_usd": 10.0,
        "event_id": None,
        "maximum_open_positions": 1,
        "maximum_entries_per_utc_day": 4,
        "selected": True,
    }
    frame = pd.DataFrame(
        [
            {
                **base,
                "candidate_id": "LOSS_LONG",
                "direction": "LONG",
                "scheduled_entry_time_utc": "2026-07-27T00:00:00Z",
                "entry_time_msc": 0,
                "exit_time_msc": 60_000,
                "stress_pnl_usd_0p01": -10.0,
            },
            {
                **base,
                "candidate_id": "A_REPEAT_LONG",
                "direction": "LONG",
                "scheduled_entry_time_utc": "2026-07-27T01:31:00Z",
                "entry_time_msc": 5_460_000,
                "exit_time_msc": 6_000_000,
                "stress_pnl_usd_0p01": 20.0,
            },
            {
                **base,
                "candidate_id": "B_OPPOSITE_SHORT",
                "direction": "SHORT",
                "scheduled_entry_time_utc": "2026-07-27T01:31:00Z",
                "entry_time_msc": 5_460_000,
                "exit_time_msc": 6_100_000,
                "stress_pnl_usd_0p01": 20.0,
            },
        ]
    )
    routed = apply_portfolio_routing(frame, CONFIG)
    assert routed["baseline_routed"].tolist() == [True, False, True]
    assert (
        routed.loc[1, "baseline_route_reason"]
        == "SAME_DIRECTION_POST_LOSS_COOLDOWN"
    )
    assert routed["selected_routed"].tolist() == [True, False, True]


def test_canonical_hash_is_order_independent() -> None:
    assert canonical_hash({"b": 2, "a": 1}, "missing") == canonical_hash(
        {"a": 1, "b": 2}, "missing"
    )
    assert sha256_bytes(b"") == hashlib_sha_empty()


def hashlib_sha_empty() -> str:
    return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
