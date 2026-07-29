from __future__ import annotations

from pathlib import Path

import pandas as pd

import validate_prospective_neutral_inventory_clock_portfolio as portfolio


def _closed(
    rows: list[tuple[str, str, str, str]],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "signal_id": signal_id,
                "clock": clock,
                "entry_tick_time_utc": entry,
                "exit_time_utc": exit_time,
                "status": "CLOSED",
                "r": 1.5,
            }
            for signal_id, clock, entry, exit_time in rows
        ]
    )


def test_portfolio_contract_freezes_all_three_clocks() -> None:
    cfg = portfolio.load_config()
    contract = cfg["portfolio_contract"]
    gates = cfg["prospective_admission"]
    assert contract["frozen_clocks"] == ["0005", "0605", "1205"]
    assert contract["maximum_concurrent_positions"] == 1
    assert contract["maximum_gross_research_lots"] == 0.01
    assert cfg["component_selection_forbidden"] is True
    assert cfg["clock_reweighting_forbidden"] is True
    assert gates["all_component_campaign_gates_required"] is True
    assert gates["minimum_overall_profit_factor"] == 1.3
    assert gates["minimum_stressed_profit_factor"] == 1.15
    assert gates["maximum_each_clock_temporal_uniform_null_p_value"] == 1 / 60


def test_exact_boundary_close_before_next_entry_is_not_overlap() -> None:
    result = portfolio.interval_integrity(
        _closed(
            [
                (
                    "a",
                    "0005",
                    "2026-07-30T00:05:00Z",
                    "2026-07-30T06:05:00Z",
                ),
                (
                    "b",
                    "0605",
                    "2026-07-30T06:05:00Z",
                    "2026-07-30T12:05:00Z",
                ),
                (
                    "c",
                    "1205",
                    "2026-07-30T12:05:00Z",
                    "2026-07-30T18:05:00Z",
                ),
            ]
        )
    )
    assert result["no_duplicate_entry_timestamps"] is True
    assert result["no_position_overlap"] is True
    assert result["maximum_concurrent_positions"] == 1


def test_duplicate_and_overlapping_entries_fail_closed() -> None:
    result = portfolio.interval_integrity(
        _closed(
            [
                (
                    "a",
                    "0005",
                    "2026-07-30T00:05:00Z",
                    "2026-07-30T07:00:00Z",
                ),
                (
                    "b",
                    "0605",
                    "2026-07-30T06:05:00Z",
                    "2026-07-30T12:05:00Z",
                ),
                (
                    "c",
                    "1205",
                    "2026-07-30T06:05:00Z",
                    "2026-07-30T13:00:00Z",
                ),
            ]
        )
    )
    assert result["no_duplicate_entry_timestamps"] is False
    assert result["no_position_overlap"] is False
    assert result["maximum_concurrent_positions"] == 3
    assert len(result["overlaps"]) == 2


def test_primary_cash_decision_is_assigned_only_to_0005() -> None:
    rows = portfolio._component_rows(
        [
            {
                "decision_sha256": "1" * 64,
                "campaign_id": "primary",
                "entry_date_utc": "2026-07-30",
                "entry_time_utc": "2026-07-30T00:05:00Z",
                "side": "CASH",
                "status": "CASH",
            }
        ],
        Path("unused"),
        evaluated_at_utc=pd.Timestamp("2026-07-30T01:00:00Z"),
        fixed_clock="0005",
    )
    assert len(rows) == 1
    assert rows[0]["clock"] == "0005"
    assert rows[0]["status"] == "CASH"


def test_empty_component_roots_produce_schema_complete_frame(
    tmp_path: Path,
) -> None:
    frame = portfolio.collect_portfolio_rows(
        evaluated_at_utc="2026-07-29T12:00:00Z",
        primary_ledger_root=tmp_path / "primary-ledger",
        primary_path_root=tmp_path / "primary-path",
        transfer_ledger_root=tmp_path / "transfer-ledger",
        transfer_path_root=tmp_path / "transfer-path",
    )
    assert frame.empty
    assert {
        "signal_id",
        "clock",
        "side",
        "status",
        "entry_tick_time_utc",
        "exit_time_utc",
    }.issubset(frame.columns)


def test_active_weekday_denominator_is_calendar_based() -> None:
    assert (
        portfolio._active_weekdays(
            pd.Timestamp("2026-07-30T00:00:00Z"),
            pd.Timestamp("2026-08-03T12:00:00Z"),
        )
        == 3
    )


def test_zero_evidence_status_waits_for_prospective_start() -> None:
    status = portfolio.build_validation_status(evaluated_at_utc="2026-07-29T12:00:00Z")
    assert status["status"] == "WAITING_FOR_PROSPECTIVE_START"
    assert status["frequency"]["closed_trades"] == 0
    assert status["component_selection_allowed"] is False
    assert status["controlled_demo_ready"] is False
    assert status["broker_action_allowed"] is False


def test_portfolio_preregistration_lock_verifies() -> None:
    lock = portfolio.verify_preregistration()
    assert lock["locked_before_first_component_observation"] is True
    assert lock["component_selection_allowed"] is False
    assert lock["clock_reweighting_allowed"] is False
