from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.campaign import (
    BREAK_FAMILY,
    RETEST_FAMILY,
    causal_health_frame,
    generate_manifest,
    parameter_space,
    route_schedule,
)


ROOT = Path(__file__).resolve().parents[1]


def config() -> dict:
    return json.loads(
        (ROOT / "config" / "causal_health_gated_event_sleeves_v100.json").read_text(
            encoding="utf-8"
        )
    )


def _health_source() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": ["a", "b", "c"],
            "family_id": [BREAK_FAMILY] * 3,
            "entry_time": pd.to_datetime(
                [
                    "2025-01-01T00:00:00Z",
                    "2025-01-01T01:00:00Z",
                    "2025-01-01T01:01:00Z",
                ]
            ),
            "exit_time": pd.to_datetime(
                [
                    "2025-01-01T01:00:00Z",
                    "2025-01-01T02:00:00Z",
                    "2025-01-01T02:01:00Z",
                ]
            ),
            "stress_net_r": [1.0, -1.0, -1.0],
        }
    )


def test_policy_registry_is_exactly_1000() -> None:
    values = parameter_space(config())
    assert len(values) == 1000
    assert len({json.dumps(value, sort_keys=True) for value in values}) == 1000


def test_manifest_attempts_are_contiguous() -> None:
    frame = pd.DataFrame(
        {
            "event_id": ["a", "b"],
            "family_id": [BREAK_FAMILY, RETEST_FAMILY],
            "horizon_minutes": [60, 60],
            "entry_time": pd.to_datetime(
                ["2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z"]
            ),
        }
    )
    manifest = generate_manifest(
        frame,
        config(),
        pd.Timestamp("2022-07-01T00:00:00Z"),
        pd.Timestamp("2024-07-01T00:00:00Z"),
    )
    assert manifest["attempt_no"].tolist() == list(range(131001, 132001))


def test_health_uses_only_exits_strictly_before_entry() -> None:
    result = causal_health_frame(
        _health_source(), lookback=1, minimum_pf=1.0, cooldown_days=0
    ).set_index("event_id")
    assert int(result.loc["b", "health_completed_events"]) == 0
    assert not bool(result.loc["b", "health_active"])
    assert int(result.loc["c", "health_completed_events"]) == 1
    assert bool(result.loc["c", "health_active"])


def test_route_caps_each_family_and_utc_day() -> None:
    health = pd.DataFrame(
        {
            "event_id": ["a", "b", "c"],
            "family_id": [BREAK_FAMILY, BREAK_FAMILY, RETEST_FAMILY],
            "entry_time": pd.to_datetime(
                [
                    "2025-01-02T08:00:00Z",
                    "2025-01-02T09:00:00Z",
                    "2025-01-02T10:00:00Z",
                ]
            ),
            "exit_time": pd.to_datetime(
                [
                    "2025-01-02T08:30:00Z",
                    "2025-01-02T09:30:00Z",
                    "2025-01-02T10:30:00Z",
                ]
            ),
            "entry_spread_atr": [0.1, 0.1, 0.1],
            "health_active": [True, True, True],
        }
    )
    params = {"anchor_hour_utc": 8, "window_hours": 8}
    selected = route_schedule(
        health,
        params,
        config(),
        pd.Timestamp("2025-01-01T00:00:00Z"),
        pd.Timestamp("2025-01-03T00:00:00Z"),
    )
    assert selected["event_id"].tolist() == ["a", "c"]


def test_program_ceiling_and_authority_are_locked() -> None:
    controls = config()["research_controls"]
    assert controls["program_version_ceiling"] == 100
    assert controls["model_training_authorized"] is False
    assert controls["broker_action_authorized"] is False
    assert controls["databento_use_authorized"] is False
