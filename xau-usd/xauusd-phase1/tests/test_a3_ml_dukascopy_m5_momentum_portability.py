from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_m5_momentum_portability import (  # noqa: E402
    HOUR_MS,
    M5_MS,
    _aggregate_ticks_to_m5,
    _server_time,
    _source_days_by_window,
    _validate_contract,
    apply_lane_execution_controls,
    generate_m5_momentum_candidates,
)


def _contract() -> dict:
    return json.loads(
        (
            ROOT
            / "config"
            / "ml"
            / "a3_ml_dukascopy_m5_momentum_portability.json"
        ).read_text(encoding="utf-8")
    )


def _timestamp(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def test_raw_ticks_are_aggregated_to_bid_ask_m5_ohlc() -> None:
    start = _timestamp(datetime(2020, 1, 1, tzinfo=UTC))
    ticks = [
        SimpleNamespace(timestamp_ms=start + 1_000, bid=1500.0, ask=1500.2),
        SimpleNamespace(timestamp_ms=start + 120_000, bid=1501.0, ask=1501.3),
        SimpleNamespace(timestamp_ms=start + 240_000, bid=1499.5, ask=1499.8),
        SimpleNamespace(timestamp_ms=start + M5_MS + 1_000, bid=1502.0, ask=1502.2),
    ]
    bars = _aggregate_ticks_to_m5(ticks)
    assert len(bars) == 2
    assert bars[0]["bid_open"] == pytest.approx(1500.0)
    assert bars[0]["bid_high"] == pytest.approx(1501.0)
    assert bars[0]["bid_low"] == pytest.approx(1499.5)
    assert bars[0]["bid_close"] == pytest.approx(1499.5)
    assert bars[0]["ask_close"] == pytest.approx(1499.8)
    assert bars[0]["tick_count"] == 3


def test_server_time_is_frozen_at_utc_plus_four() -> None:
    utc = datetime(2020, 1, 1, 22, 0, tzinfo=UTC)
    server = _server_time(_timestamp(utc), _contract())
    assert server.hour == 2
    assert server.date().isoformat() == "2020-01-02"


def test_contract_binds_source_hashes_and_rejects_authorization() -> None:
    contract = _contract()
    _validate_contract(ROOT, contract)
    contract["authorization"]["broker_action_authorized"] = True
    with pytest.raises(ValueError, match="forbidden authorization"):
        _validate_contract(ROOT, contract)


def _h1_bars(hours: int = 500) -> list[dict]:
    start = datetime(2020, 1, 1, tzinfo=UTC)
    rows = []
    for index in range(hours):
        close = 1500.0 + 0.2 * index
        rows.append(
            {
                "timestamp_ms": _timestamp(start + timedelta(hours=index)),
                "bid_open": close - 0.1,
                "bid_high": close + 0.3,
                "bid_low": close - 0.3,
                "bid_close": close,
                "tick_count": 100,
            }
        )
    return rows


def _m5_bars(count: int = 360) -> list[dict]:
    start = datetime(2020, 1, 15, tzinfo=UTC)
    rows = []
    for index in range(count):
        middle = 1800.0 + 0.005 * index
        rows.append(
            {
                "timestamp_ms": _timestamp(start + timedelta(minutes=5 * index)),
                "bid_open": middle - 0.05,
                "bid_high": middle + 0.2,
                "bid_low": middle - 0.2,
                "bid_close": middle + 0.05,
                "ask_open": middle + 0.15,
                "ask_high": middle + 0.4,
                "ask_low": middle,
                "ask_close": middle + 0.25,
                "tick_count": 50,
            }
        )
    return rows


def _set_long_breakout(rows: list[dict], index: int) -> None:
    recent_high = max(row["bid_high"] for row in rows[index - 12 : index])
    rows[index].update(
        {
            "bid_open": recent_high - 0.3,
            "bid_high": recent_high + 1.0,
            "bid_low": recent_high - 0.4,
            "bid_close": recent_high + 0.9,
        }
    )


def test_generator_reproduces_frozen_long_breakout_with_completed_htf_trend() -> None:
    m5 = _m5_bars()
    index = next(
        index
        for index, row in enumerate(m5)
        if datetime.fromtimestamp(row["timestamp_ms"] / 1000, UTC).hour == 3
        and datetime.fromtimestamp(row["timestamp_ms"] / 1000, UTC).minute == 55
        and index > 30
    )
    _set_long_breakout(m5, index)
    candidates = generate_m5_momentum_candidates(m5, _h1_bars(), _contract())
    decision = m5[index]["timestamp_ms"] + M5_MS
    selected = [row for row in candidates if row.decision_timestamp_ms == decision]
    assert len(selected) == 1
    assert selected[0].family_id == "dukascopy_clean_long_v5_move12"
    assert selected[0].direction == "LONG"
    assert selected[0].reward_r == pytest.approx(0.7)
    assert selected[0].stop_distance >= 3.5


def test_future_m5_bar_cannot_change_prior_candidate_identity() -> None:
    m5 = _m5_bars()
    index = next(
        index
        for index, row in enumerate(m5)
        if datetime.fromtimestamp(row["timestamp_ms"] / 1000, UTC).hour == 3
        and datetime.fromtimestamp(row["timestamp_ms"] / 1000, UTC).minute == 55
        and index > 30
    )
    _set_long_breakout(m5, index)
    baseline = generate_m5_momentum_candidates(m5, _h1_bars(), _contract())
    assert baseline
    changed = copy.deepcopy(m5)
    changed.append(
        {
            "timestamp_ms": changed[-1]["timestamp_ms"] + M5_MS,
            "bid_open": 9998.0,
            "bid_high": 10001.0,
            "bid_low": 9997.0,
            "bid_close": 10000.0,
            "ask_open": 9998.2,
            "ask_high": 10001.2,
            "ask_low": 9997.2,
            "ask_close": 10000.2,
            "tick_count": 10,
        }
    )
    rerun = generate_m5_momentum_candidates(changed, _h1_bars(), _contract())
    cutoff = m5[-1]["timestamp_ms"] + M5_MS
    assert [row.candidate_id for row in baseline] == [
        row.candidate_id for row in rerun if row.decision_timestamp_ms <= cutoff
    ]


def _label(
    candidate_id: str,
    entry: datetime,
    exit_time: datetime,
    *,
    spread: float = 0.1,
) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=candidate_id,
        family_id="dukascopy_clean_long_v5_move12",
        status="RESOLVED",
        exit_reason="TARGET",
        entry_spread=spread,
        stop_distance=3.5,
        entry_time_utc=entry.isoformat().replace("+00:00", "Z"),
        exit_time_utc=exit_time.isoformat().replace("+00:00", "Z"),
    )


def test_lane_controls_enforce_position_spread_and_daily_cap() -> None:
    contract = _contract()
    contract["lanes"][0]["maximum_trades_per_server_day"] = 1
    start = datetime(2020, 1, 1, 8, 0, tzinfo=UTC)
    labels = [
        _label("a", start, start + timedelta(hours=1)),
        _label("b", start + timedelta(minutes=5), start + timedelta(minutes=30)),
        _label("c", start + timedelta(hours=2), start + timedelta(hours=3), spread=1.0),
        _label("d", start + timedelta(hours=4), start + timedelta(hours=5)),
    ]
    candidates = {
        row.candidate_id: SimpleNamespace(
            candidate_id=row.candidate_id,
            decision_timestamp_ms=_timestamp(_parse(row.entry_time_utc)),
        )
        for row in labels
    }
    selected, reasons = apply_lane_execution_controls(labels, candidates, contract)
    assert [row.candidate_id for row in selected] == ["a"]
    assert reasons["lane_position_already_open"] == 1
    assert reasons["spread_above_maximum"] == 1
    assert reasons["lane_daily_cap"] == 1


def test_source_day_requires_one_hundred_m5_bars() -> None:
    start = datetime(2020, 1, 1, tzinfo=UTC)
    rows = [
        {"timestamp_ms": _timestamp(start + timedelta(minutes=5 * index))}
        for index in range(99)
    ]
    assert _source_days_by_window(rows, _contract())["prehistory"] == 0
    rows.append({"timestamp_ms": _timestamp(start + timedelta(minutes=5 * 99))})
    assert _source_days_by_window(rows, _contract())["prehistory"] == 1


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
