from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from confirmation import (  # noqa: E402
    execute_candidate,
    first_exit_hit,
    generate_candidates,
    independent_signal_mask_direction,
)


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


PARAMS = {
    "counter_flow_max": -0.01,
    "counter_move_12_max": 0.0,
    "counter_move_3_max": 0.0,
    "geometry_id": "EXTENDED",
    "m15_state_age_m5_max": 1,
    "mean_slope_abs_max": 0.35,
    "return_acf_max": -0.1,
    "session": "ALL",
    "stationarity_window": 384,
    "variance_horizon": 4,
    "variance_ratio_max": 1.1,
    "z_abs_min": 1.0,
}


def _frame() -> pd.DataFrame:
    starts = pd.date_range("2024-01-02T00:00:00Z", periods=5, freq="5min")
    return pd.DataFrame(
        {
            "bar_start_utc": starts,
            "bar_end_utc": starts + pd.Timedelta(minutes=5),
            "regime": ["TREND_UP", "CHOP", "TREND_UP", "TREND_UP", "TREND_UP"],
            "m15_state_age_m5": [0, 1, 0, 0, 0],
            "z_384": [0.0, 1.5, 0.0, 0.0, 0.0],
            "variance_ratio_4_384": [2.0, 1.0, 2.0, 2.0, 2.0],
            "return_acf_1_384": [0.0, -0.2, 0.0, 0.0, 0.0],
            "mean_slope_atr_384": [1.0, 0.1, 1.0, 1.0, 1.0],
            "risk_atr": [2.0] * 5,
            "return_3": [0.0, -0.2, 0.0, 0.0, 0.0],
            "return_12": [0.0, 0.2, 0.0, 0.0, 0.0],
            "tick_imbalance_15m": [0.0, -0.1, 0.0, 0.0, 0.0],
            "spread_ratio": [1.0] * 5,
        }
    )


class ReferenceCampaign:
    @staticmethod
    def signal_mask_direction(frame, mechanic, params):
        assert mechanic == "CHOP_COUNTERFLOW_DUAL_WINDOW_ENVELOPE"
        return independent_signal_mask_direction(frame, params)


def _config() -> dict:
    return {
        "source": {"end_exclusive_utc": "2024-02-01T00:00:00Z"},
        "candidate": {
            "origin_attempt": 39583,
            "origin_variant_id": "229111b27bb96c07",
            "regime_owner": "CHOP",
            "mechanic": "CHOP_COUNTERFLOW_DUAL_WINDOW_ENVELOPE",
            "geometry_id": "EXTENDED",
            "expected_raw_signals": 1,
            "parameters": PARAMS,
            "geometry": {
                "stop_atr": 1.0,
                "target_r": 2.0,
                "hold_bars": 2,
                "maximum_hold_hours": 1 / 6,
            },
        },
    }


def _execution() -> dict:
    return {
        "maximum_entry_gap_minutes": 5,
        "maximum_horizon_gap_minutes": 5,
        "maximum_entry_spread_r": 0.15,
        "maximum_research_risk_usd": 50.0,
        "ounces_at_lot_size": 1.0,
        "ticket_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.05,
    }


def test_independent_signal_is_counterflow_continuation() -> None:
    mask, direction = independent_signal_mask_direction(_frame(), PARAMS)
    assert mask.tolist() == [False, True, False, False, False]
    assert int(direction.loc[mask].iat[0]) == 1


def test_candidate_stream_requires_exact_reference_parity() -> None:
    candidates, parity = generate_candidates(_frame(), ReferenceCampaign, _config())
    assert len(candidates) == 1
    assert parity["mask_equal"] and parity["direction_equal"]
    assert parity["independent_signal_sha256"] == parity["reference_signal_sha256"]
    assert candidates["scheduled_entry_time"].iat[0] == _frame()[
        "bar_start_utc"
    ].iat[2]
    assert candidates["scheduled_deadline"].iat[0] == _frame()[
        "bar_start_utc"
    ].iat[4]


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


def _candidate(scheduled: pd.Timestamp) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id="c1",
        origin_attempt=39583,
        origin_variant_id="229111b27bb96c07",
        regime_owner="CHOP",
        mechanic="CHOP_COUNTERFLOW_DUAL_WINDOW_ENVELOPE",
        geometry_id="EXTENDED",
        signal_time=scheduled - pd.Timedelta(minutes=5),
        scheduled_entry_time=scheduled,
        scheduled_deadline=scheduled + pd.Timedelta(hours=1),
        direction_sign=1,
        signal_atr=1.0,
        stop_atr=1.0,
        target_r=2.0,
        hold_hours=1.0,
    )


def test_horizon_has_priority_at_deadline() -> None:
    scheduled = pd.Timestamp("2024-01-02T00:00:00Z")
    deadline = scheduled + pd.Timedelta(hours=1)
    rows = [
        (int(scheduled.value // 1_000_000), 99.9, 100.0),
        (int(deadline.value // 1_000_000), 103.0, 103.1),
    ]
    outcome, rejection = execute_candidate(
        _candidate(scheduled), TickStore(rows), Quote, _execution()
    )
    assert rejection is None
    assert outcome is not None
    assert outcome["exit_reason"] == "FIXED_HORIZON"
    assert outcome["exit_price"] == 103.0


def test_target_fill_is_locked_target_price() -> None:
    scheduled = pd.Timestamp("2024-01-02T00:00:00Z")
    rows = [
        (int(scheduled.value // 1_000_000), 99.9, 100.0),
        (
            int((scheduled + pd.Timedelta(minutes=5)).value // 1_000_000),
            102.4,
            102.5,
        ),
        (
            int((scheduled + pd.Timedelta(hours=1)).value // 1_000_000),
            101.0,
            101.1,
        ),
    ]
    outcome, rejection = execute_candidate(
        _candidate(scheduled), TickStore(rows), Quote, _execution()
    )
    assert rejection is None
    assert outcome is not None
    assert outcome["exit_reason"] == "TARGET"
    assert outcome["exit_price"] == 102.0
    assert outcome["stress_net_r"] == 1.95
