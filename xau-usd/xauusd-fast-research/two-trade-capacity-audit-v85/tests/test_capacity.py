from __future__ import annotations

import pandas as pd
import pytest

from capacity import calendar_weekdays, validate_ledgers, window_capacity


def frame(ids: list[str], dates: list[str], sleeve: str) -> pd.DataFrame:
    entry = pd.to_datetime(dates, utc=True)
    return pd.DataFrame(
        {
            "trade_id": ids,
            "sleeve_id": sleeve,
            "entry_time": entry,
            "exit_time": entry + pd.Timedelta(hours=1),
        }
    )


def ledgers() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    core = frame(["c1", "c2"], ["2024-01-01T08:00Z", "2024-01-02T08:00Z"], "CORE")
    candidates = frame(
        ["a1", "a2", "a3", "a4"],
        [
            "2024-01-01T09:00Z",
            "2024-01-01T10:00Z",
            "2024-01-02T09:00Z",
            "2024-01-02T10:00Z",
        ],
        "ADDON",
    )
    decisions = candidates[["trade_id", "sleeve_id", "entry_time"]].copy()
    decisions["accepted"] = [True, False, True, False]
    decisions["decision_reason"] = ["ACCEPTED", "DAILY_CAP", "ACCEPTED", "DAILY_CAP"]
    combined = pd.concat(
        [core, candidates.loc[candidates["trade_id"].isin(["a1", "a3"])]],
        ignore_index=True,
    )
    return core, candidates, decisions, combined


def test_calendar_weekdays_excludes_weekend() -> None:
    assert calendar_weekdays(
        pd.Timestamp("2024-01-01T00:00Z"), pd.Timestamp("2024-01-08T00:00Z")
    ) == 5


def test_window_capacity_reports_optimistic_upper_bound() -> None:
    core, candidates, decisions, _ = ledgers()
    row, reasons = window_capacity(
        window="test",
        start=pd.Timestamp("2024-01-01T00:00Z"),
        end=pd.Timestamp("2024-01-03T00:00Z"),
        core=core,
        candidates=candidates,
        decisions=decisions,
        target=2.0,
    )
    assert row["current_combined_trades"] == 4
    assert row["mechanical_upper_bound_trades"] == 6
    assert row["mechanical_upper_bound_trades_per_weekday"] == 3.0
    assert row["upper_bound_reaches_two_per_weekday"]
    assert reasons.to_dict(orient="records") == [
        {"window": "test", "decision_reason": "DAILY_CAP", "rejected_addons": 2}
    ]


def test_validation_requires_exact_candidate_decision_identity() -> None:
    core, candidates, decisions, combined = ledgers()
    expected = {
        "core_rows": 2,
        "candidate_rows": 4,
        "accepted_addons": 2,
        "combined_rows": 4,
    }
    validate_ledgers(core, candidates, decisions, combined, expected)
    changed = decisions.copy()
    changed.loc[0, "trade_id"] = "wrong"
    with pytest.raises(ValueError, match="candidate and decision IDs differ"):
        validate_ledgers(core, candidates, changed, combined, expected)
