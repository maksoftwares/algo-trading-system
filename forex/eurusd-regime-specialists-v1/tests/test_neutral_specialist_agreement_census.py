from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.neutral_specialist_agreement_census import (
    build_exact_clock_agreements,
    route_earliest_per_day,
    verify_lock,
)


def _signal(clock: str, side: str, expert: str, row: int) -> dict:
    return {
        "entry_time_utc": pd.Timestamp(clock),
        "side": side,
        "expert_id": expert,
        "source_row": row,
    }


def test_census_contract_forbids_outcomes() -> None:
    lock = verify_lock()
    assert lock["outcome_loading_allowed"] is False
    assert lock["oracle_loading_allowed"] is False


def test_exact_clock_agreement_deduplicates_expert_and_vetoes_conflict() -> None:
    signals = pd.DataFrame(
        [
            _signal("2023-01-02T00:00:00Z", "LONG", "A", 0),
            _signal("2023-01-02T00:00:00Z", "LONG", "A", 1),
            _signal("2023-01-02T00:00:00Z", "LONG", "B", 0),
            _signal("2023-01-03T00:00:00Z", "LONG", "A", 2),
            _signal("2023-01-03T00:00:00Z", "LONG", "B", 1),
            _signal("2023-01-03T00:00:00Z", "SHORT", "C", 0),
        ]
    )
    agreements, conflicts = build_exact_clock_agreements(
        signals, minimum_distinct_experts=2
    )
    assert len(agreements) == 1
    assert agreements.iloc[0]["expert_combination"] == "A|B"
    assert agreements.iloc[0]["distinct_experts"] == 2
    assert len(conflicts) == 1
    assert conflicts.iloc[0]["status"] == "CASH_CONFLICT"


def test_router_keeps_earliest_agreement_per_utc_day() -> None:
    agreements = pd.DataFrame(
        [
            {
                "entry_time_utc": pd.Timestamp("2023-01-02T00:15:00Z"),
                "side": "SHORT",
                "distinct_experts": 2,
                "expert_combination": "A|B",
                "eligible_date": "2023-01-02",
            },
            {
                "entry_time_utc": pd.Timestamp("2023-01-02T00:00:00Z"),
                "side": "LONG",
                "distinct_experts": 2,
                "expert_combination": "A|C",
                "eligible_date": "2023-01-02",
            },
        ]
    )
    routed = route_earliest_per_day(agreements)
    assert len(routed) == 1
    assert routed.iloc[0]["entry_time_utc"] == pd.Timestamp(
        "2023-01-02T00:00:00Z"
    )
