from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd

import capture_prospective_neutral_inventory_unwind_0005 as decision
import capture_prospective_neutral_inventory_unwind_0005_path as path
import run_prospective_neutral_inventory_unwind_0005_daily_operations as ops
from validate_prospective_neutral_inventory_unwind_0005 import (
    trade_metrics,
)


def _ticks(prices: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_utc": [
                pd.Timestamp(timestamp) for timestamp, _, _ in prices
            ],
            "bid": [bid for _, bid, _ in prices],
            "ask": [ask for _, _, ask in prices],
        }
    )


def _source(side: str = "LONG") -> dict[str, object]:
    return {
        "entry_date_utc": "2026-07-30",
        "source_observed_at_utc": "2026-07-30T00:03:00Z",
        "source_record_sha256": "1" * 64,
        "file_sha256": "2" * 64,
        "signal": {
            "side": side,
            "displacement_pips": -5.0 if side == "LONG" else 5.0,
        },
    }


def _ownership(*, neutral: bool = True) -> dict[str, object]:
    return {
        "ownership_observed_at_utc": "2026-07-30T00:02:30Z",
        "is_neutral": neutral,
        "state_staleness_hours": 2.0,
        "ownership_evidence_sha256": "3" * 64,
    }


def test_source_hours_are_completed_prior_20_to_23_utc() -> None:
    hours = decision.source_hours("2026-07-30T00:00:00Z")
    assert [value.hour for value in hours] == [20, 21, 22, 23]
    assert hours[0].date().isoformat() == "2026-07-29"


def test_inventory_signal_fades_completed_displacement() -> None:
    long = decision.inventory_signal(
        _ticks(
            [
                ("2026-07-29T20:00:00Z", 1.10000, 1.10008),
                ("2026-07-29T23:59:59Z", 1.09950, 1.09958),
            ]
        ),
        threshold_pips=4.0,
    )
    short = decision.inventory_signal(
        _ticks(
            [
                ("2026-07-29T20:00:00Z", 1.10000, 1.10008),
                ("2026-07-29T23:59:59Z", 1.10050, 1.10058),
            ]
        ),
        threshold_pips=4.0,
    )
    assert long["side"] == "LONG"
    assert short["side"] == "SHORT"


def test_subthreshold_inventory_stays_cash() -> None:
    result = decision.inventory_signal(
        _ticks(
            [
                ("2026-07-29T20:00:00Z", 1.10000, 1.10008),
                ("2026-07-29T23:59:59Z", 1.10010, 1.10018),
            ]
        ),
        threshold_pips=4.0,
    )
    assert result["side"] == "CASH"


def test_on_time_neutral_evidence_creates_signal() -> None:
    record = decision.build_decision(
        _source(),
        _ownership(),
        config=decision.load_config(),
        created_at_utc="2026-07-30T00:04:00Z",
    )
    assert record["status"] == "SIGNAL"
    assert record["side"] == "LONG"
    assert record["entry_time_utc"] == pd.Timestamp(
        "2026-07-30T00:05:00Z"
    )


def test_non_neutral_or_late_evidence_routes_to_cash() -> None:
    source = _source()
    source["source_observed_at_utc"] = "2026-07-30T00:04:01Z"
    record = decision.build_decision(
        source,
        _ownership(neutral=False),
        config=decision.load_config(),
        created_at_utc="2026-07-30T00:04:10Z",
    )
    assert record["status"] == "CASH"
    assert "LATE_SOURCE" in record["reasons"]
    assert "NOT_NEUTRAL" in record["reasons"]


def test_long_tick_execution_hits_target() -> None:
    cfg = decision.load_config()
    record = {
        "side": "LONG",
        "entry_time_utc": "2026-07-30T00:05:00Z",
    }
    result = path.execute_ticks(
        record,
        _ticks(
            [
                ("2026-07-30T00:05:00Z", 1.10000, 1.10008),
                ("2026-07-30T00:10:00Z", 1.10110, 1.10118),
            ]
        ),
        cfg,
    )
    assert result["status"] == "CLOSED"
    assert result["exit_reason"] == "TARGET"
    assert result["r"] > 1.4


def test_short_tick_execution_hits_stop() -> None:
    cfg = decision.load_config()
    record = {
        "side": "SHORT",
        "entry_time_utc": "2026-07-30T00:05:00Z",
    }
    result = path.execute_ticks(
        record,
        _ticks(
            [
                ("2026-07-30T00:05:00Z", 1.10000, 1.10008),
                ("2026-07-30T00:10:00Z", 1.10062, 1.10070),
            ]
        ),
        cfg,
    )
    assert result["status"] == "CLOSED"
    assert result["exit_reason"] == "STOP"
    assert result["r"] < -1.0


def test_path_publication_boundary_includes_final_hour() -> None:
    hours = path.required_path_hours(
        "2026-07-30T00:05:00Z",
        maximum_hold_hours=6,
    )
    assert [value.hour for value in hours] == list(range(7))
    assert path.earliest_path_capture(
        "2026-07-30T00:05:00Z",
        maximum_hold_hours=6,
    ) == pd.Timestamp("2026-07-30T07:01:00Z")


def test_trade_metrics_report_pf_and_drawdown() -> None:
    metrics = trade_metrics([1.5, -1.0, 1.5, -1.0])
    assert metrics["win_rate"] == 0.5
    assert metrics["realized_payoff_ratio"] == 1.5
    assert metrics["profit_factor"] == 1.5
    assert metrics["max_drawdown_r"] == 1.0


def test_scheduler_starts_before_first_entry() -> None:
    operations = ops.operations_for_entry_date(date(2026, 7, 30))
    names = {row.name for row in operations}
    assert "CAPTURE_ENTRY_OWNERSHIP" in names
    assert "CAPTURE_INVENTORY_SOURCE" in names
    assert "EVALUATE_FROZEN_DECISION" in names
    assert "CAPTURE_CLOSED_TRADE_PATH" in names
    assert "CAPTURE_COMPLETED_ORACLE_DATE" in names
    first = min(operations, key=lambda row: row.due_at_utc)
    assert first.due_at_utc == datetime(
        2026, 7, 29, 21, 2, tzinfo=timezone.utc
    )


def test_weekends_have_no_entry_operations() -> None:
    assert ops.operations_for_entry_date(date(2026, 8, 1)) == []


def test_preregistration_lock_verifies() -> None:
    checked = decision.verify_preregistration()
    assert checked["locked_before_prospective_start"] is True
    assert checked["historical_backtest_allowed"] is False
