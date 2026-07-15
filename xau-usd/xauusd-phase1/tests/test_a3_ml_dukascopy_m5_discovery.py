from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.a3_meta_v1.dukascopy_m5_discovery import (  # noqa: E402
    _direction_and_concentration,
    _m5_frame,
    _pattern_allows,
    _training_source_days,
    _validate_contract,
    apply_profile_execution_controls,
)


def _contract() -> dict:
    return json.loads(
        (ROOT / "config" / "ml" / "a3_ml_dukascopy_m5_discovery_train.json").read_text(
            encoding="utf-8"
        )
    )


def _timestamp(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _pattern_row(**overrides: float) -> dict:
    row = {
        "atr": 2.0,
        "m5_ema": 100.0,
        "m5_ema_prior": 100.0,
        "prior_high": 101.0,
        "prior_low": 99.0,
        "three_bar_move": 1.0,
        "bid_open": 99.8,
        "bid_high": 101.5,
        "bid_low": 98.7,
        "bid_close": 101.2,
    }
    row.update(overrides)
    return row


def test_contract_freezes_full_profile_matrix_and_rejects_authorization() -> None:
    contract = _contract()
    _validate_contract(contract)
    assert len(contract["profiles"]) == 12
    changed = copy.deepcopy(contract)
    changed["authorization"]["validation_outcomes_authorized"] = True
    with pytest.raises(ValueError, match="requires validation_outcomes_authorized=false"):
        _validate_contract(changed)


def test_pullback_requires_directional_ema_reclaim() -> None:
    signal = _contract()["signal"]
    previous = {"bid_close": 99.8}
    matched, _ = _pattern_allows(
        "TREND_PULLBACK", "LONG", _pattern_row(), previous, signal
    )
    assert matched
    matched, _ = _pattern_allows(
        "TREND_PULLBACK",
        "LONG",
        _pattern_row(bid_close=99.7),
        previous,
        signal,
    )
    assert not matched


def test_breakout_requires_close_beyond_prior_extreme_and_momentum() -> None:
    signal = _contract()["signal"]
    previous = {"bid_close": 100.0}
    matched, distance = _pattern_allows(
        "CONTINUATION_BREAKOUT", "LONG", _pattern_row(), previous, signal
    )
    assert matched
    assert distance > 0.0
    matched, _ = _pattern_allows(
        "CONTINUATION_BREAKOUT",
        "LONG",
        _pattern_row(bid_close=101.05),
        previous,
        signal,
    )
    assert not matched


def test_sweep_reclaim_requires_both_sweep_and_reclaim() -> None:
    signal = _contract()["signal"]
    previous = {"bid_close": 100.0}
    matched, distance = _pattern_allows(
        "TREND_SWEEP_RECLAIM", "LONG", _pattern_row(), previous, signal
    )
    assert matched
    assert distance > 0.0
    matched, _ = _pattern_allows(
        "TREND_SWEEP_RECLAIM",
        "LONG",
        _pattern_row(bid_low=98.95),
        previous,
        signal,
    )
    assert not matched


def _bars(count: int = 80) -> list[dict]:
    start = datetime(2020, 1, 1, tzinfo=UTC)
    rows = []
    for index in range(count):
        close = 1500.0 + 0.1 * index
        rows.append(
            {
                "timestamp_ms": _timestamp(start + timedelta(minutes=5 * index)),
                "bid_open": close - 0.1,
                "bid_high": close + 0.3,
                "bid_low": close - 0.3,
                "bid_close": close,
                "tick_count": 10,
            }
        )
    return rows


def test_future_bar_does_not_change_prior_m5_features() -> None:
    contract = _contract()
    baseline = _m5_frame(_bars(), contract)
    changed = _bars()
    changed.append(
        {
            "timestamp_ms": changed[-1]["timestamp_ms"] + 300_000,
            "bid_open": 9990.0,
            "bid_high": 10010.0,
            "bid_low": 9980.0,
            "bid_close": 10000.0,
            "tick_count": 10,
        }
    )
    rerun = _m5_frame(changed, contract).iloc[: len(baseline)]
    for column in ("atr", "m5_ema", "prior_high", "prior_low", "three_bar_move"):
        pd.testing.assert_series_equal(
            baseline[column].reset_index(drop=True),
            rerun[column].reset_index(drop=True),
            check_names=False,
        )


def _label(
    candidate_id: str,
    entry: datetime,
    exit_time: datetime,
    *,
    spread: float = 0.1,
) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=candidate_id,
        family_id="pullback_h1_rr1p0",
        status="RESOLVED",
        exit_reason="TARGET",
        entry_spread=spread,
        stop_distance=3.5,
        entry_time_utc=entry.isoformat().replace("+00:00", "Z"),
        exit_time_utc=exit_time.isoformat().replace("+00:00", "Z"),
    )


def test_profile_controls_enforce_position_spread_and_daily_cap() -> None:
    contract = _contract()
    contract["execution"]["maximum_trades_per_server_day"] = 1
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
            decision_timestamp_ms=_timestamp(
                datetime.fromisoformat(row.entry_time_utc.replace("Z", "+00:00"))
            ),
        )
        for row in labels
    }
    selected, reasons = apply_profile_execution_controls(labels, candidates, contract)
    assert [row.candidate_id for row in selected] == ["a"]
    assert reasons["profile_position_already_open"] == 1
    assert reasons["spread_above_maximum"] == 1
    assert reasons["profile_daily_cap"] == 1


def test_training_source_day_requires_one_hundred_m5_bars() -> None:
    contract = _contract()
    start = datetime(2020, 1, 1, tzinfo=UTC)
    rows = [
        {"timestamp_ms": _timestamp(start + timedelta(minutes=5 * index))}
        for index in range(99)
    ]
    assert _training_source_days(rows, contract) == 0
    rows.append({"timestamp_ms": _timestamp(start + timedelta(minutes=5 * 99))})
    assert _training_source_days(rows, contract) == 1


def test_missing_direction_has_zero_direction_share() -> None:
    rows = [
        SimpleNamespace(
            direction="LONG",
            exit_time_utc="2020-01-02T00:00:00.000Z",
            stress_net_pnl_usd=1.0,
        )
    ]
    assert _direction_and_concentration(rows)["minimum_direction_share"] == 0.0
