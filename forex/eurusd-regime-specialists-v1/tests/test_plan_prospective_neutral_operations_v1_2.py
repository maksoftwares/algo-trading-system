from __future__ import annotations

from pathlib import Path

import pandas as pd

import plan_prospective_neutral_operations as base
import plan_prospective_neutral_operations_v1_2 as planner


def _event(family: str, timestamp: str) -> dict:
    return {
        "family": family,
        "event_time_utc": timestamp,
        "stages": [],
    }


def test_runtime_and_oracle_context_supersession_are_locked() -> None:
    checked = planner.verify_lock()
    config = planner.load_config()

    assert config["schema_version"].endswith("_v1_2")
    assert config["supersedes"]["before_prospective_start_and_first_signal"]
    assert config["runtime"]["strategy_or_evidence_semantics_changed"] is False
    assert config["oracle_context_ownership"][
        "oracle_labels_remain_evaluation_only"
    ]
    assert config["supersedes"]["path"] in checked


def test_context_stage_is_shared_with_adjacent_target_event() -> None:
    config = planner.load_config()
    aug_12 = pd.Timestamp("2026-08-12T00:00:00Z")
    aug_13 = pd.Timestamp("2026-08-13T00:00:00Z")
    stage = planner._context_stage(
        event_date=aug_12,
        target_event_dates={aug_12, aug_13},
        available_ownership_dates=set(),
        evaluated_at_utc=pd.Timestamp("2026-08-01T00:00:00Z"),
        config=config,
    )

    assert stage["status"] == "SHARED_WITH_EVENT_DATE_OWNERSHIP"
    assert stage["due"] is False
    assert stage["eligible_date"] == aug_13


def test_missing_context_dates_extend_cache_and_schedule(
    monkeypatch,
) -> None:
    now = pd.Timestamp("2026-07-28T17:00:00Z")
    plan = {
        "schema_version": planner.SCHEMA_VERSION,
        "status": "WAITING_FOR_NEXT_SAFE_ACTION",
        "next_scheduled_action_utc": None,
        "due_actions": [],
        "global_actions": [
            {
                "stage": "OWNERSHIP_CACHE_PREWARM",
                "status": "SCHEDULED",
                "due": False,
                "due_at_utc": "2026-08-07T00:01:00Z",
                "command": None,
                "reason": "old",
            }
        ],
        "events": [
            _event("NFP", "2026-08-07T12:30:00Z"),
            _event("CPI", "2026-08-12T12:30:00Z"),
            _event("PPI", "2026-08-13T12:30:00Z"),
        ],
        "census": {"ownership_cache": None},
    }
    requested = []

    monkeypatch.setattr(
        base,
        "load_ownership_evidence",
        lambda root, evaluated_at_utc: (pd.DataFrame(), {}),
    )

    def fake_status(eligible_date, root, now_utc):
        requested.append(eligible_date)
        return {"missing_safe_symbol_hours": 0}

    monkeypatch.setattr(base, "prewarm_status", fake_status)
    monkeypatch.setattr(
        base,
        "plan_ownership_cache_action",
        lambda status, evaluated_at_utc, eligible_date, config: {
            "stage": "OWNERSHIP_CACHE_PREWARM",
            "status": "SCHEDULED",
            "due": False,
            "due_at_utc": "2026-07-28T18:01:00Z",
            "command": None,
            "reason": "test",
        },
    )

    result = planner._add_oracle_context_operations(
        plan,
        evaluated_at_utc=now,
        roots={"neutral_ownership": Path("unused")},
    )

    assert requested == [pd.Timestamp("2026-08-07T00:00:00Z")]
    assert result["oracle_context_ownership_policy"]["required_dates"] == [
        "2026-08-07",
        "2026-08-08",
        "2026-08-12",
        "2026-08-13",
        "2026-08-14",
    ]
    stages = {
        event["family"]: event["stages"][-1] for event in result["events"]
    }
    assert stages["NFP"]["eligible_date"].startswith("2026-08-08")
    assert stages["CPI"]["status"] == "SHARED_WITH_EVENT_DATE_OWNERSHIP"
    assert stages["PPI"]["eligible_date"].startswith("2026-08-14")


def test_due_cache_precedes_due_context_capture() -> None:
    now = pd.Timestamp("2026-08-08T00:01:00Z")
    plan = {
        "events": [
            {
                **_event("NFP", "2026-08-07T12:30:00Z"),
                "stages": [
                    {
                        "stage": "ORACLE_CONTEXT_OWNERSHIP",
                        "status": "DUE",
                        "due": True,
                        "due_at_utc": now,
                        "command": "capture",
                        "reason": "test",
                    }
                ],
            }
        ],
        "global_actions": [
            {
                "stage": "OWNERSHIP_CACHE_PREWARM",
                "status": "DUE",
                "due": True,
                "due_at_utc": now,
                "command": "prewarm",
                "reason": "test",
            }
        ],
    }

    planner._rebuild_schedule(plan, now)

    assert [row["stage"] for row in plan["due_actions"]] == [
        "OWNERSHIP_CACHE_PREWARM",
        "ORACLE_CONTEXT_OWNERSHIP",
    ]
