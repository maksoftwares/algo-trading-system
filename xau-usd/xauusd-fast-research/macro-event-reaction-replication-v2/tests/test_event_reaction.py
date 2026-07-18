from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from event_reaction import (  # noqa: E402
    _timestamp_series_ms,
    _timestamp_ms,
    candidate_for_event_policy,
    first_threshold_hit,
    holm_adjust,
    label_candidates,
)


@dataclass
class Tick:
    timestamp_ms: int
    bid: float
    ask: float


def _bars(
    last_open: float, last_close: float, last_high: float, last_low: float
) -> pd.DataFrame:
    starts = pd.date_range("2020-01-03 13:30", periods=6, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "bid_open": [100.0, 100.2, 100.1, 100.4, 100.5, last_open],
            "bid_high": [100.5, 100.6, 100.4, 100.8, 100.65, last_high],
            "bid_low": [99.8, 100.0, 99.9, 100.2, 100.3, last_low],
            "bid_close": [100.2, 100.1, 100.3, 100.5, 100.55, last_close],
            "atr": [1.0] * 6,
        }
    )


def _event() -> dict:
    return {
        "event_id": "NFP_2020-01-03",
        "event_type": "NFP",
        "event_time_utc": pd.Timestamp("2020-01-03 13:30", tz="UTC"),
        "source_kind": "TEST",
        "source_url": "https://example.test/event",
    }


def _policy(mode: str) -> dict:
    return {
        "policy_id": f"TEST_{mode}",
        "mode": mode,
        "impulse_minutes": 15,
        "start_minutes": 5 if mode == "IMPULSE" else 15,
        "end_minutes": 60 if mode == "IMPULSE" else 90,
        "break_atr": 0.1,
        "stop_buffer_atr": 0.1,
        "minimum_body_fraction": 0.35,
        "target_r": 2.0,
    }


def test_impulse_uses_only_completed_post_event_bar() -> None:
    bars = _bars(
        last_open=100.7, last_close=101.4, last_high=101.5, last_low=100.6
    )
    candidate = candidate_for_event_policy(_event(), _policy("IMPULSE"), bars)
    assert candidate is not None
    assert candidate["direction"] == "LONG"
    assert candidate["feature_time_utc"] == pd.Timestamp(
        "2020-01-03 14:00", tz="UTC"
    )
    assert candidate["raw_stop_distance"] > 0.0


def test_fade_requires_sweep_and_close_back_inside() -> None:
    bars = _bars(
        last_open=100.0, last_close=100.3, last_high=100.4, last_low=99.6
    )
    candidate = candidate_for_event_policy(_event(), _policy("FADE"), bars)
    assert candidate is not None
    assert candidate["direction"] == "LONG"


def test_tick_threshold_order_is_not_inferred_from_bar_extremes() -> None:
    ticks = [
        Tick(1, 100.0, 100.1),
        Tick(2, 102.1, 102.2),
        Tick(3, 98.9, 99.0),
    ]
    hit = first_threshold_hit(ticks, "LONG", 99.0, 102.0, 1, 3)
    assert hit is not None
    assert hit[2] == "TARGET"
    assert hit[0].timestamp_ms == 2


@pytest.mark.parametrize("unit", ["ms", "us", "ns"])
def test_epoch_milliseconds_are_independent_of_datetime_storage_unit(unit: str) -> None:
    times = pd.Series(
        pd.date_range("2024-01-02 12:00", periods=2, freq="5min", tz="UTC")
    ).astype(f"datetime64[{unit}, UTC]")
    assert _timestamp_series_ms(times).tolist() == [1704196800000, 1704197100000]


@pytest.mark.parametrize(
    ("later_bid", "bid_low", "bid_high", "expected_reason"),
    [
        (102.2, 100.0, 102.2, "TARGET"),
        (99.0, 99.0, 100.2, "STOP"),
    ],
)
def test_label_candidates_detects_thresholds_with_millisecond_bars(
    monkeypatch: pytest.MonkeyPatch,
    later_bid: float,
    bid_low: float,
    bid_high: float,
    expected_reason: str,
) -> None:
    decision = pd.Timestamp("2024-01-02 12:00", tz="UTC")
    decision_ms = _timestamp_ms(decision)
    ticks = [
        Tick(decision_ms + 1, 100.0, 100.1),
        Tick(decision_ms + 60_000, later_bid, later_bid + 0.1),
    ]
    store_calls: list[tuple[int, int]] = []

    class Store:
        def ticks_between(self, start_ms: int, end_ms: int):
            store_calls.append((start_ms, end_ms))
            return [
                tick
                for tick in ticks
                if start_ms <= tick.timestamp_ms <= end_ms
            ]

    import event_reaction

    monkeypatch.setattr(event_reaction.SPOT, "load_dukascopy_foundation", lambda: object())
    monkeypatch.setattr(
        event_reaction.SPOT,
        "VerifiedSpotTickStore",
        lambda **_: Store(),
    )
    starts = pd.Series(pd.date_range(decision, periods=2, freq="5min")).astype(
        "datetime64[ms, UTC]"
    )
    m5 = pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "bid_low": [bid_low, 100.0],
            "bid_high": [bid_high, 100.2],
            "ask_low": [bid_low + 0.1, 100.1],
            "ask_high": [bid_high + 0.1, 100.3],
        }
    )
    candidates = pd.DataFrame(
        [
            {
                "candidate_id": "candidate",
                "policy_id": "policy",
                "event_id": "event",
                "event_type": "NFP",
                "mode": "IMPULSE",
                "regime": "CHOP",
                "direction": "LONG",
                "feature_time_utc": decision,
                "raw_stop_distance": 1.0,
                "target_r": 2.0,
                "signal_atr": 1.0,
            }
        ]
    )
    outcomes, audit = label_candidates(
        candidates,
        m5,
        Path("unused"),
        "XAUUSD",
        {"maximum_entry_delay_ms": 10_000, "exit_tick_grace_ms": 10_000},
        {
            "minimum_stop_distance_usd": 1.0,
            "maximum_stop_distance_usd": 10.0,
            "maximum_entry_spread_usd": 1.0,
            "maximum_entry_spread_r": 0.5,
            "maximum_hold_hours": 1,
            "ounces": 1.0,
            "ticket_cost_usd": 0.0,
            "holding_cost_per_24h_usd": 0.0,
            "stress_slippage_r": 0.0,
            "current_account_risk_usd": 10.0,
        },
    )
    assert not outcomes.empty, (audit, store_calls)
    assert outcomes.loc[0, "exit_reason"] == expected_reason
    assert audit[f"{expected_reason.lower()}_outcomes"] == 1
    assert audit["max_hold_outcomes"] == 0


def test_holm_adjustment_matches_registered_family_size() -> None:
    adjusted = holm_adjust(pd.Series([0.01, 0.04, 0.03]))
    assert adjusted.round(4).tolist() == [0.03, 0.06, 0.06]
