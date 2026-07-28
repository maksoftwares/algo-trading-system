from __future__ import annotations

import pandas as pd

import plan_prospective_neutral_operations_v1_4 as planner


def _plan(stage_due_at: str) -> dict:
    return {
        "schema_version": "old",
        "status": "WAITING_FOR_NEXT_SAFE_ACTION",
        "due_actions": [],
        "next_scheduled_action_utc": stage_due_at,
        "global_actions": [],
        "events": [
            {
                "family": "NFP",
                "event_time_utc": "2026-08-07T12:30:00Z",
                "stages": [
                    {
                        "stage": "PRE_RELEASE_FORECAST",
                        "status": "SCHEDULED",
                        "due": False,
                        "due_at_utc": stage_due_at,
                        "command": None,
                        "reason": "test",
                    }
                ],
            }
        ],
    }


def test_forecast_deadline_supersession_is_locked() -> None:
    checked = planner.verify_lock()
    config = planner.load_config()

    assert config["schema_version"].endswith("_v1_4")
    assert config["forecast_deadline_gate"][
        "next_poll_may_not_exceed_forecast_deadline"
    ]
    assert config["forecast_deadline_gate"][
        "strategy_or_evidence_semantics_changed"
    ] is False
    assert config["supersedes"]["path"] in checked


def test_poll_is_clamped_to_sixty_second_deadline() -> None:
    now = pd.Timestamp("2026-08-07T12:28:30Z")
    result = planner._clamp_forecast_deadlines(
        _plan("2026-08-07T12:29:30Z"),
        evaluated_at_utc=now,
    )
    stage = result["events"][0]["stages"][0]

    assert stage["due_at_utc"] == "2026-08-07T12:29:00+00:00"
    assert stage["status"] == "SCHEDULED"
    assert stage["command"] is None
    assert result["forecast_deadline_gate"]["clamped_event_stages"] == 1


def test_clamped_poll_becomes_due_at_deadline() -> None:
    deadline = pd.Timestamp("2026-08-07T12:29:00Z")
    result = planner._clamp_forecast_deadlines(
        _plan("2026-08-07T12:29:30Z"),
        evaluated_at_utc=deadline,
    )
    stage = result["events"][0]["stages"][0]

    assert stage["status"] == "DUE"
    assert stage["due"] is True
    assert "capture_prospective_tradingview_consensus.py" in stage["command"]
    assert result["due_actions"][0]["stage"] == "PRE_RELEASE_FORECAST"
