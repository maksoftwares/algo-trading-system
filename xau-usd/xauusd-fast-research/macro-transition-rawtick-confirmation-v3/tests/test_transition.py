from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transition import execute_candidate, first_exit_hit, generate_candidates  # noqa: E402


@dataclass(frozen=True)
class Quote:
    timestamp_ms: int
    bid: float
    ask: float


class TickStore:
    def __init__(self, rows: list[tuple[int, float, float]]) -> None:
        self.rows = rows

    def segments(self, start_ms: int, end_ms: int):
        selected = [row for row in self.rows if start_ms <= row[0] <= end_ms]
        if selected:
            yield (
                np.array([row[0] for row in selected], dtype=np.int64),
                np.array([row[1] for row in selected], dtype=float),
                np.array([row[2] for row in selected], dtype=float),
            )

    def first_quote_at_or_after(self, timestamp_ms: int, maximum_delay_ms: int):
        for time, bid, ask in self.rows:
            if timestamp_ms <= time <= timestamp_ms + maximum_delay_ms:
                return Quote(time, bid, ask)
        return None


class Campaign:
    @staticmethod
    def signal_mask_direction(frame, mechanic, params):
        assert mechanic == "TRANS_ANCESTRY_MACRO_REACCELERATION"
        return pd.Series([True], index=frame.index), pd.Series([1], index=frame.index)


def _config() -> dict:
    return {
        "source": {"end_exclusive_utc": "2024-02-01T00:00:00Z"},
        "candidate": {
            "origin_attempt": 23925,
            "origin_variant_id": "00e072837bf6f6e2",
            "regime_owner": "TRANSITION",
            "mechanic": "TRANS_ANCESTRY_MACRO_REACCELERATION",
            "geometry_id": "T_BALANCED",
            "expected_raw_signals": 1,
            "parameters": {"geometry_id": "T_BALANCED"},
            "geometry": {
                "stop_atr": 1.75,
                "target_r": 2.0,
                "maximum_hold_hours": 18.0,
            },
        },
        "execution": {"maximum_entry_gap_minutes": 20},
    }


def _execution() -> dict:
    return {
        "maximum_entry_gap_minutes": 20,
        "maximum_horizon_gap_hours": 72,
        "maximum_entry_spread_r": 0.15,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.05,
    }


def test_candidate_uses_complete_execution_index() -> None:
    times = pd.date_range("2024-01-02T00:15:00Z", periods=6, freq="15min")
    execution = pd.DataFrame(
        {
            "timestamp_utc": times,
            "bar_start_utc": times - pd.Timedelta(minutes=15),
        }
    )
    decisions = pd.DataFrame(
        {
            "timestamp_utc": [times[3]],
            "execution_index": [3],
            "atr14": [2.0],
        }
    )
    candidates = generate_candidates(decisions, execution, Campaign, _config())
    assert len(candidates) == 1
    assert candidates["scheduled_entry_time"].iat[0] == execution["bar_start_utc"].iat[4]
    assert int(candidates["execution_signal_index"].iat[0]) == 3


def test_first_exit_uses_earliest_target_tick() -> None:
    store = TickStore(
        [(1_000, 100.0, 100.2), (2_000, 102.1, 102.3), (3_000, 98.5, 98.7)]
    )
    hit = first_exit_hit(store, 1_000, 3_000, 1, 99.0, 102.0, Quote)
    assert hit is not None
    quote, price, reason = hit
    assert quote.timestamp_ms == 2_000
    assert price == 102.0
    assert reason == "TARGET"


def test_short_stop_uses_observed_slippage_quote() -> None:
    store = TickStore([(1_000, 100.0, 100.2), (2_000, 101.4, 101.7)])
    hit = first_exit_hit(store, 1_000, 2_000, -1, 101.0, 98.0, Quote)
    assert hit is not None
    _, price, reason = hit
    assert price == 101.7
    assert reason == "STOP_SLIPPAGE"


def test_horizon_has_priority_at_deadline() -> None:
    scheduled = pd.Timestamp("2024-01-02T00:00:00Z")
    deadline = scheduled + pd.Timedelta(hours=1)
    rows = [
        (int(scheduled.value // 1_000_000), 99.9, 100.0),
        (int(deadline.value // 1_000_000), 103.0, 103.1),
    ]
    candidate = SimpleNamespace(
        candidate_id="c1",
        origin_attempt=23925,
        origin_variant_id="v1",
        regime_owner="TRANSITION",
        mechanic="TRANS_ANCESTRY_MACRO_REACCELERATION",
        geometry_id="T_BALANCED",
        signal_time=scheduled - pd.Timedelta(minutes=15),
        scheduled_entry_time=scheduled,
        direction_sign=1,
        signal_atr=1.0,
        stop_atr=1.0,
        target_r=2.0,
        hold_hours=1.0,
    )
    outcome, rejection = execute_candidate(candidate, TickStore(rows), Quote, _execution())
    assert rejection is None
    assert outcome is not None
    assert outcome["exit_reason"] == "FIXED_HORIZON"
    assert outcome["exit_price"] == 103.0


def test_target_fill_is_locked_target_price() -> None:
    scheduled = pd.Timestamp("2024-01-02T00:00:00Z")
    rows = [
        (int(scheduled.value // 1_000_000), 99.9, 100.0),
        (int((scheduled + pd.Timedelta(minutes=5)).value // 1_000_000), 102.4, 102.5),
        (int((scheduled + pd.Timedelta(hours=1)).value // 1_000_000), 101.0, 101.1),
    ]
    candidate = SimpleNamespace(
        candidate_id="c1",
        origin_attempt=23925,
        origin_variant_id="v1",
        regime_owner="TRANSITION",
        mechanic="TRANS_ANCESTRY_MACRO_REACCELERATION",
        geometry_id="T_BALANCED",
        signal_time=scheduled - pd.Timedelta(minutes=15),
        scheduled_entry_time=scheduled,
        direction_sign=1,
        signal_atr=1.0,
        stop_atr=1.0,
        target_r=2.0,
        hold_hours=1.0,
    )
    outcome, rejection = execute_candidate(candidate, TickStore(rows), Quote, _execution())
    assert rejection is None
    assert outcome is not None
    assert outcome["exit_reason"] == "TARGET"
    assert outcome["exit_price"] == 102.0
    assert outcome["stress_net_r"] == 1.95

