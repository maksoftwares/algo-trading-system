from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_compression_breakout import (  # noqa: E402
    DAY_MS,
    HOUR_MS,
    _validate_contract,
    aggregate_h1_bid_bars,
    generate_compression_breakout_candidates,
)


def _contract() -> dict:
    return json.loads(
        (ROOT / "config" / "ml" / "a3_ml_dukascopy_compression_breakout.json").read_text(
            encoding="utf-8"
        )
    )


def _h1(timestamp_ms: int, price: float) -> dict:
    return {
        "timestamp_ms": timestamp_ms,
        "bid_open": price,
        "bid_high": price + 1.0,
        "bid_low": price - 1.0,
        "bid_close": price + 0.5,
        "tick_count": 100,
    }


def test_aggregation_requires_minimum_active_h1_bars() -> None:
    rows = [_h1(hour * HOUR_MS, 100.0 + hour) for hour in range(11)]
    assert aggregate_h1_bid_bars(rows, width_hours=24, minimum_active_hours=12) == []
    rows.append(_h1(11 * HOUR_MS, 111.0))
    daily = aggregate_h1_bid_bars(rows, width_hours=24, minimum_active_hours=12)
    assert len(daily) == 1
    assert daily[0]["active_h1_bars"] == 12
    assert daily[0]["open"] == pytest.approx(100.0)
    assert daily[0]["close"] == pytest.approx(111.5)


def _synthetic_breakout_inputs() -> tuple[list[dict], list[dict]]:
    d1 = []
    for index in range(300):
        close = 100.0 + 0.2 * index
        daily_range = 10.0 if index < 280 else 4.0
        d1.append(
            {
                "timestamp_ms": index * DAY_MS,
                "open": close - 0.2,
                "high": close + daily_range / 2.0,
                "low": close - daily_range / 2.0,
                "close": close,
                "tick_count": 1000,
            }
        )
    box_high = max(row["high"] for row in d1[-2:])
    h4 = []
    start = 296 * DAY_MS
    for index in range(24):
        timestamp = start + index * 4 * HOUR_MS
        close = box_high - 1.0 + 0.02 * index
        h4.append(
            {
                "timestamp_ms": timestamp,
                "open": close - 0.1,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "tick_count": 500,
            }
        )
    h4.append(
        {
            "timestamp_ms": 300 * DAY_MS,
            "open": box_high - 0.5,
            "high": box_high + 0.7,
            "low": box_high - 0.7,
            "close": box_high + 0.5,
            "tick_count": 700,
        }
    )
    return h4, d1


def test_generator_emits_first_long_breakout_from_completed_daily_data() -> None:
    h4, d1 = _synthetic_breakout_inputs()
    candidates = generate_compression_breakout_candidates(h4, d1, _contract())
    assert candidates
    candidate = candidates[-1]
    assert candidate.direction == "LONG"
    assert candidate.decision_timestamp_ms == 300 * DAY_MS + 4 * HOUR_MS
    assert candidate.reward_r == pytest.approx(2.0)
    assert 1.0 <= candidate.stop_distance_atr <= 3.0


def test_previous_h4_close_outside_box_blocks_repeat_breakout() -> None:
    h4, d1 = _synthetic_breakout_inputs()
    box_high = max(row["high"] for row in d1[-2:])
    h4[-2]["close"] = box_high + 0.1
    candidates = generate_compression_breakout_candidates(h4, d1, _contract())
    decision = 300 * DAY_MS + 4 * HOUR_MS
    assert all(row.decision_timestamp_ms != decision for row in candidates)


def test_future_bars_cannot_change_earlier_candidate_identity() -> None:
    h4, d1 = _synthetic_breakout_inputs()
    baseline = generate_compression_breakout_candidates(h4, d1, _contract())
    assert baseline
    mutated_h4 = copy.deepcopy(h4)
    mutated_d1 = copy.deepcopy(d1)
    mutated_h4.append(
        {
            "timestamp_ms": 301 * DAY_MS,
            "open": 9999.0,
            "high": 10001.0,
            "low": 9998.0,
            "close": 10000.0,
            "tick_count": 100,
        }
    )
    mutated_d1.append(
        {
            "timestamp_ms": 301 * DAY_MS,
            "open": 9999.0,
            "high": 10001.0,
            "low": 9998.0,
            "close": 10000.0,
            "tick_count": 100,
        }
    )
    changed = generate_compression_breakout_candidates(mutated_h4, mutated_d1, _contract())
    cutoff = 301 * DAY_MS
    assert [row.candidate_id for row in baseline if row.decision_timestamp_ms < cutoff] == [
        row.candidate_id for row in changed if row.decision_timestamp_ms < cutoff
    ]


def test_contract_rejects_broker_authorization() -> None:
    contract = _contract()
    contract["authorization"]["broker_action_authorized"] = True
    with pytest.raises(ValueError, match="forbidden authorization"):
        _validate_contract(contract)
