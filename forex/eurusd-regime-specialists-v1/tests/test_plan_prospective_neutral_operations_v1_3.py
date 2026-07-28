from __future__ import annotations

import pandas as pd

import plan_prospective_neutral_operations_v1_3 as planner


def _plan(*, missing_safe_symbol_hours: int) -> dict:
    now = "2026-08-08T00:01:00Z"
    return {
        "schema_version": "old",
        "status": "ACTION_DUE",
        "due_actions": [],
        "next_scheduled_action_utc": None,
        "global_actions": [
            {
                "stage": "OWNERSHIP_CACHE_PREWARM",
                "status": (
                    "DUE" if missing_safe_symbol_hours else "SCHEDULED"
                ),
                "due": bool(missing_safe_symbol_hours),
                "due_at_utc": now,
                "command": (
                    "prewarm" if missing_safe_symbol_hours else None
                ),
                "reason": "test",
            }
        ],
        "events": [
            {
                "family": "NFP",
                "event_time_utc": "2026-08-07T12:30:00Z",
                "stages": [
                    {
                        "stage": "NEUTRAL_OWNERSHIP",
                        "status": "DUE",
                        "due": True,
                        "due_at_utc": "2026-08-07T00:01:00Z",
                        "command": "capture-aug7",
                        "reason": "test",
                    },
                    {
                        "stage": "ORACLE_CONTEXT_OWNERSHIP",
                        "eligible_date": "2026-08-08T00:00:00Z",
                        "status": "DUE",
                        "due": True,
                        "due_at_utc": now,
                        "command": "capture-aug8",
                        "reason": "test",
                    },
                ],
            }
        ],
        "census": {
            "ownership_cache": {
                "missing_safe_symbol_hours": missing_safe_symbol_hours
            }
        },
        "oracle_context_ownership_policy": {
            "missing_dates": ["2026-08-07", "2026-08-08"]
        },
    }


def test_dependency_supersession_is_locked() -> None:
    checked = planner.verify_lock()
    config = planner.load_config()

    assert config["schema_version"].endswith("_v1_3")
    assert config["dependency_gate"]["replan_after_each_mutating_command"]
    assert config["dependency_gate"]["strategy_or_evidence_semantics_changed"] is False
    assert config["supersedes"]["path"] in checked


def test_cache_gap_blocks_capture_and_later_date() -> None:
    now = pd.Timestamp("2026-08-08T00:01:00Z")
    result = planner._gate_ownership_dependencies(
        _plan(missing_safe_symbol_hours=120),
        evaluated_at_utc=now,
    )
    stages = result["events"][0]["stages"]

    assert stages[0]["status"] == "BLOCKED_PENDING_OWNERSHIP_CACHE"
    assert stages[1]["status"] == "BLOCKED_EARLIER_OWNERSHIP_DATE"
    assert [row["stage"] for row in result["due_actions"]] == [
        "OWNERSHIP_CACHE_PREWARM"
    ]


def test_zero_gap_cache_releases_only_earliest_date() -> None:
    now = pd.Timestamp("2026-08-08T00:01:00Z")
    result = planner._gate_ownership_dependencies(
        _plan(missing_safe_symbol_hours=0),
        evaluated_at_utc=now,
    )
    stages = result["events"][0]["stages"]

    assert stages[0]["status"] == "DUE"
    assert stages[0]["command"] == "capture-aug7"
    assert stages[1]["status"] == "BLOCKED_EARLIER_OWNERSHIP_DATE"
    assert [row["stage"] for row in result["due_actions"]] == [
        "NEUTRAL_OWNERSHIP"
    ]
