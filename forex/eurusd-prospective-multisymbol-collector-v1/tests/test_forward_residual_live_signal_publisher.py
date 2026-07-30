from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, timedelta

from src import forward_selective_learner as base
from src.forward_residual_live_signal_publisher import (
    CONFIG_PATH,
    process_once,
    reconstruct_histories,
    write_outputs,
)
from src.forward_residual_regime_specialist import (
    CONFIG_PATH as STRATEGY_CONFIG_PATH,
)

ROOT = CONFIG_PATH.parents[1]
LOCK = (
    ROOT
    / "EURUSD_FORWARD_RESIDUAL_LIVE_SIGNAL_PUBLISHER_LOCK_2026_07_30.sha256.json"
)


def _configs() -> tuple[dict, dict]:
    strategy = json.loads(STRATEGY_CONFIG_PATH.read_text(encoding="utf-8"))
    publisher = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return strategy, publisher


def _bar(when: datetime, symbol: str, first: float, last: float) -> base.Bar:
    point = 0.001 if symbol.endswith("JPY") else 0.00001
    spread = 10 * point
    return base.Bar(
        interval_open=when,
        symbol=symbol,
        status="OK",
        copied_ticks=100,
        first_bid=first,
        first_ask=first + spread,
        last_bid=last,
        last_ask=last + spread,
        bid_high=max(first, last) + spread,
        bid_low=min(first, last) - spread,
        ask_high=max(first, last) + 2 * spread,
        ask_low=min(first, last),
        spread_mean_points=10.0,
        point=point,
    )


def _context_bars(day: date) -> dict[datetime, dict[str, base.Bar]]:
    decision = datetime.combine(day, datetime.min.time()) + timedelta(hours=20)
    start = decision - timedelta(hours=4)
    symbols = ["EURUSD", "EURGBP", "EURJPY", "GBPUSD", "USDJPY"]
    bases = {
        "EURUSD": 1.15,
        "EURGBP": 0.86,
        "EURJPY": 175.0,
        "GBPUSD": 1.34,
        "USDJPY": 151.0,
    }
    grouped = {}
    for index in range(48):
        when = start + timedelta(minutes=5 * index)
        grouped[when] = {}
        for symbol in symbols:
            if symbol == "EURUSD":
                first = bases[symbol]
                last = first
            else:
                scale = 0.00003 if not symbol.endswith("JPY") else 0.004
                direction = -1 if symbol == "USDJPY" else 1
                first = bases[symbol] + direction * scale * index
                last = first + direction * scale
            grouped[when][symbol] = _bar(when, symbol, first, last)
    return grouped


def _resolved_record(day: date, regime: str = "BROAD_EUR_UP") -> dict:
    return {
        "decision_date": day.isoformat(),
        "status": "RESOLVED",
        "regime": regime,
        "long_outcome": {
            "side": "LONG",
            "result_r": 1.5,
        },
        "short_outcome": {
            "side": "SHORT",
            "result_r": -1.0,
        },
    }


def _prior_records(count: int, start: date = date(2026, 8, 3)) -> list[dict]:
    records = []
    cursor = start
    while len(records) < count:
        if cursor.weekday() < 5:
            records.append(_resolved_record(cursor))
        cursor += timedelta(days=1)
    return records


def test_history_reconstruction_uses_only_prior_resolved_regime_days() -> None:
    strategy, _ = _configs()
    current = date(2026, 9, 1)
    records = [
        _resolved_record(date(2026, 8, 27)),
        {
            "decision_date": "2026-08-28",
            "status": "UPSTREAM_OWNED",
        },
        _resolved_record(
            date(2026, 8, 31),
            regime="MIXED_TRANSITION",
        ),
    ]
    histories, resolved = reconstruct_histories(records, current, strategy)
    assert resolved == 2
    assert histories["BROAD_EUR_UP"]["LONG"] == [1.5]
    assert histories["MIXED_TRANSITION"]["SHORT"] == [-1.0]
    assert histories["BROAD_EUR_DOWN"]["LONG"] == []


def test_pre_floor_run_publishes_nothing() -> None:
    strategy, publisher = _configs()
    records, summary = process_once(
        {},
        [],
        set(),
        [],
        datetime(2026, 7, 31, 20, 3, tzinfo=UTC),
        strategy,
        publisher,
    )
    assert records == []
    assert summary["status"] == "WAITING_FORWARD_FLOOR"


def test_signal_is_published_before_outcome_exists() -> None:
    strategy, publisher = _configs()
    day = date(2026, 9, 1)
    records, summary = process_once(
        _context_bars(day),
        _prior_records(20),
        set(),
        [],
        datetime(2026, 9, 1, 20, 3, tzinfo=UTC),
        strategy,
        publisher,
    )
    assert len(records) == 1
    assert records[0]["status"] == "PUBLISHED_SIGNAL"
    assert records[0]["regime"] == "BROAD_EUR_UP"
    assert records[0]["eligible_side"] == "LONG"
    assert records[0]["training_days_before"] == 20
    assert "long_outcome" not in records[0]
    assert "short_outcome" not in records[0]
    assert summary["eligible_signals"] == 1
    assert summary["demo_order_authorized"] is False


def test_upstream_owned_date_is_immutable_cash() -> None:
    strategy, publisher = _configs()
    day = date(2026, 9, 1)
    records, _ = process_once(
        _context_bars(day),
        _prior_records(20),
        {day.isoformat()},
        [],
        datetime(2026, 9, 1, 20, 3, tzinfo=UTC),
        strategy,
        publisher,
    )
    assert records[0]["status"] == "CASH_UPSTREAM_OWNED"
    assert records[0]["eligible_side"] == "CASH"


def test_missing_publication_context_is_cash_not_late_recovered() -> None:
    strategy, publisher = _configs()
    records, _ = process_once(
        {},
        _prior_records(20),
        set(),
        [],
        datetime(2026, 9, 1, 20, 3, tzinfo=UTC),
        strategy,
        publisher,
    )
    assert records[0]["status"] == "CASH_MISSING_CONTEXT"
    assert records[0]["eligible_side"] == "CASH"


def test_late_run_records_cash_and_never_recovers_signal() -> None:
    strategy, publisher = _configs()
    day = date(2026, 9, 1)
    records, _ = process_once(
        _context_bars(day),
        _prior_records(20),
        set(),
        [],
        datetime(2026, 9, 1, 20, 11, tzinfo=UTC),
        strategy,
        publisher,
    )
    assert records[0]["status"] == "CASH_MISSED_PUBLICATION_DEADLINE"
    assert records[0]["eligible_side"] == "CASH"
    repeated, summary = process_once(
        _context_bars(day),
        _prior_records(20),
        set(),
        records,
        datetime(2026, 9, 1, 20, 12, tzinfo=UTC),
        strategy,
        publisher,
    )
    assert repeated == records
    assert summary["status"] == "ALREADY_PUBLISHED"


def test_live_signal_ledger_is_append_only(tmp_path) -> None:
    strategy, publisher = _configs()
    day = date(2026, 9, 1)
    records, summary = process_once(
        _context_bars(day),
        _prior_records(20),
        set(),
        [],
        datetime(2026, 9, 1, 20, 3, tzinfo=UTC),
        strategy,
        publisher,
    )
    write_outputs(records, summary, tmp_path)
    mutated = json.loads(json.dumps(records))
    mutated[0]["eligible_side"] = "SHORT"
    try:
        write_outputs(mutated, summary, tmp_path)
    except ValueError as error:
        assert "mutation refused" in str(error)
    else:
        raise AssertionError("published live decision was mutated")


def test_contract_has_no_order_or_backfill_authorization() -> None:
    _, publisher = _configs()
    assert publisher["demo_order_authorized"] is False
    assert "NO_HISTORICAL_BACKFILL" in publisher["prohibitions"]
    assert "NO_POST_OUTCOME_PUBLICATION" in publisher["prohibitions"]
    assert "NO_ORDERS" in publisher["prohibitions"]


def test_live_publisher_lock_matches_every_frozen_file() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert lock["locked_before_forward_floor"] is True
    assert lock["locked_with_zero_forward_feature_rows"] is True
    assert lock["locked_with_zero_live_decisions"] is True
    assert lock["historical_backfill_allowed"] is False
    assert lock["demo_order_authorized"] is False
    for relative, expected in lock["files"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
