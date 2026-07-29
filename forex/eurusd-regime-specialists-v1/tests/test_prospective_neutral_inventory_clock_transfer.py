from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

import prospective_neutral_inventory_clock_transfer as transfer


def _ticks(prices: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_utc": [pd.Timestamp(timestamp) for timestamp, _, _ in prices],
            "bid": [bid for _, bid, _ in prices],
            "ask": [ask for _, _, ask in prices],
        }
    )


def _source(clock: str, side: str = "LONG") -> dict[str, object]:
    hour = int(clock[:2])
    return {
        "entry_date_utc": "2026-07-30",
        "clock": clock,
        "source_observed_at_utc": (f"2026-07-30T{hour:02d}:03:00Z"),
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
        "state_staleness_hours": 0.0,
        "ownership_evidence_sha256": "3" * 64,
    }


def _payload(hour: pd.Timestamp) -> bytes:
    offset = (hour.hour - 2) * 0.0002
    return json.dumps(
        {
            "timestamp": int(hour.timestamp() * 1000),
            "multiplier": 0.00001,
            "bid": 1.10000 + offset,
            "ask": 1.10008 + offset,
            "times": [1000],
            "bids": [0],
            "asks": [0],
            "bidVolumes": [1],
            "askVolumes": [1],
        }
    ).encode("utf-8")


def _fetcher(
    symbol: str,
    hour: pd.Timestamp,
) -> tuple[bytes, dict[str, object]]:
    observed = hour + pd.Timedelta(hours=1, minutes=2)
    return _payload(hour), {
        "symbol": symbol,
        "hour_utc": hour,
        "url": f"https://example.invalid/{hour:%Y%m%d%H}",
        "request_started_utc": observed,
        "request_finished_utc": observed,
        "http_date_utc": observed,
        "observed_at_utc": observed,
        "response_headers": {},
    }


def test_frozen_clocks_use_immediately_prior_completed_four_hours() -> None:
    hours_0605 = transfer.source_hours("2026-07-30", "0605")
    hours_1205 = transfer.source_hours("2026-07-30", "1205")
    assert [value.hour for value in hours_0605] == [2, 3, 4, 5]
    assert [value.hour for value in hours_1205] == [8, 9, 10, 11]
    assert transfer.entry_time("2026-07-30", "0605") == pd.Timestamp(
        "2026-07-30T06:05:00Z"
    )
    assert transfer.entry_time("2026-07-30", "1205") == pd.Timestamp(
        "2026-07-30T12:05:00Z"
    )


def test_same_fade_rule_is_used_at_both_clocks() -> None:
    ticks = _ticks(
        [
            ("2026-07-30T02:00:01Z", 1.10000, 1.10008),
            ("2026-07-30T05:59:59Z", 1.10050, 1.10058),
        ]
    )
    signal = transfer.inventory_signal(ticks, threshold_pips=4.0)
    assert signal["side"] == "SHORT"
    assert signal["signal_eligible"] is True


def test_completed_source_hours_are_prewarmed_then_read_without_network(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    for hour in transfer.source_hours("2026-07-30", "0605"):
        result = transfer.prewarm_source_hour(
            "2026-07-30",
            "0605",
            hour,
            source_root=source_root,
            now_utc=hour + pd.Timedelta(hours=1, minutes=2),
            fetcher=_fetcher,
        )
        assert result["status"] == "SOURCE_HOUR_PREWARMED"
    source = transfer.capture_source(
        "2026-07-30",
        "0605",
        source_root=source_root,
        now_utc="2026-07-30T06:03:00Z",
    )
    assert source["status"] == "SOURCE_SIGNAL"
    assert source["signal"]["side"] == "SHORT"
    assert source["network_request_made"] is False
    assert len(source["raw_links"]) == 4


def test_decisions_are_clock_specific_and_use_daily_neutral_ownership() -> None:
    cfg = transfer.load_config()
    decision_0605 = transfer.build_decision(
        _source("0605"),
        _ownership(),
        config=cfg,
        created_at_utc="2026-07-30T06:04:00Z",
    )
    decision_1205 = transfer.build_decision(
        _source("1205", "SHORT"),
        _ownership(),
        config=cfg,
        created_at_utc="2026-07-30T12:04:00Z",
    )
    assert decision_0605["status"] == "SIGNAL"
    assert decision_0605["side"] == "LONG"
    assert decision_0605["entry_time_utc"] == pd.Timestamp("2026-07-30T06:05:00Z")
    assert decision_1205["status"] == "SIGNAL"
    assert decision_1205["side"] == "SHORT"
    assert decision_1205["entry_time_utc"] == pd.Timestamp("2026-07-30T12:05:00Z")


def test_non_neutral_or_late_daily_ownership_routes_to_cash() -> None:
    ownership = _ownership(neutral=False)
    ownership["ownership_observed_at_utc"] = "2026-07-30T00:04:01Z"
    record = transfer.build_decision(
        _source("0605"),
        ownership,
        config=transfer.load_config(),
        created_at_utc="2026-07-30T06:04:00Z",
    )
    assert record["status"] == "CASH"
    assert "NOT_NEUTRAL" in record["reasons"]
    assert "LATE_DAILY_OWNERSHIP" in record["reasons"]


def test_tick_execution_preserves_one_point_five_r_contract() -> None:
    decision = {
        "side": "LONG",
        "entry_time_utc": "2026-07-30T06:05:00Z",
    }
    result = transfer.execute_ticks(
        decision,
        _ticks(
            [
                ("2026-07-30T06:05:00Z", 1.10000, 1.10008),
                ("2026-07-30T06:10:00Z", 1.10110, 1.10118),
            ]
        ),
        transfer.load_config(),
    )
    assert result["status"] == "CLOSED"
    assert result["exit_reason"] == "TARGET"
    assert result["r"] > 1.4


def test_two_clock_schedule_is_sequential_and_publication_safe() -> None:
    operations = transfer.operations_for_entry_date(date(2026, 7, 30))
    source_prewarm = [row for row in operations if row.name == "PREWARM_SOURCE_HOUR"]
    assert len(source_prewarm) == 8
    assert min(row.due_at_utc for row in source_prewarm) == datetime(
        2026, 7, 30, 3, 2, tzinfo=timezone.utc
    )
    paths = {
        row.slot: row.due_at_utc
        for row in operations
        if row.name == "CAPTURE_CLOSED_TRADE_PATH"
    }
    assert paths == {
        "0605": datetime(2026, 7, 30, 13, 16, tzinfo=timezone.utc),
        "1205": datetime(2026, 7, 30, 19, 16, tzinfo=timezone.utc),
    }
    assert transfer.entry_time("2026-07-30", "0605") + pd.Timedelta(
        hours=6
    ) == transfer.entry_time("2026-07-30", "1205")


def test_scheduler_starts_before_first_source_window() -> None:
    operations = transfer.operations_for_entry_date(date(2026, 7, 30))
    first = min(operations, key=lambda row: row.due_at_utc)
    assert first.due_at_utc == datetime(2026, 7, 29, 21, 2, tzinfo=timezone.utc)
    assert first.name == "PREWARM_ENTRY_OWNERSHIP"
    assert (
        transfer.next_operation(datetime(2026, 7, 29, 11, 0, tzinfo=timezone.utc))
        == first
    )


def test_weekends_have_no_entry_operations() -> None:
    assert transfer.operations_for_entry_date(date(2026, 8, 1)) == []


def test_clock_metrics_cannot_be_hidden_inside_pooled_metrics() -> None:
    assert transfer.SLOTS == ("0605", "1205")
    cfg = transfer.load_config()
    gates = cfg["prospective_admission"]
    assert gates["no_individual_clock_promotion"] is True
    assert gates["minimum_trades_per_clock"] == 20
    assert gates["minimum_each_clock_profit_factor"] == 1.0
    assert gates["maximum_each_clock_temporal_uniform_null_p_value"] == 0.025


def test_preregistration_lock_verifies() -> None:
    lock = transfer.verify_preregistration()
    assert lock["locked_before_prospective_evidence_start"] is True
    assert lock["historical_backtest_allowed"] is False
    assert lock["individual_clock_selection_allowed"] is False
