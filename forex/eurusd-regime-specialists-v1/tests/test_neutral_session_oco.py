from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_session_oco import (
    build_anchor_candidates,
    simulate,
)


def _config() -> dict[str, object]:
    return {
        "strategy": {
            "anchor_hours_utc": [0],
            "range_lookback_m5_bars": 12,
            "entry_buffer_pips": 0.2,
            "pending_order_minutes": 90,
            "maximum_trades_per_utc_day": 4,
        },
        "neutral_ownership": {"requires_direction": "NEUTRAL"},
        "execution": {
            "risk_pips": 4.0,
            "target_r": 1.5,
            "maximum_hold_hours": 12,
            "minimum_retail_spread_pips": 0.7,
            "extra_slippage_pips_per_side": 0.1,
        },
    }


def _bars(*, ambiguous: bool = False) -> pd.DataFrame:
    index = pd.date_range(
        "2025-01-01T23:00:00Z", periods=40, freq="5min"
    )
    bid_open = np.full(len(index), 1.1000)
    bid_high = np.full(len(index), 1.1002)
    bid_low = np.full(len(index), 1.0998)
    bid_close = np.full(len(index), 1.1000)
    trigger = 12
    bid_high[trigger] = 1.1007
    bid_low[trigger] = 1.0999
    bid_close[trigger] = 1.1006
    if ambiguous:
        bid_low[trigger] = 1.0993
    bid_high[trigger + 1] = 1.1015
    bid_low[trigger + 1] = 1.1005
    bid_close[trigger + 1] = 1.1013
    spread = 0.00007
    return pd.DataFrame(
        {
            "bid_open": bid_open,
            "bid_high": bid_high,
            "bid_low": bid_low,
            "bid_close": bid_close,
            "ask_open": bid_open + spread,
            "ask_high": bid_high + spread,
            "ask_low": bid_low + spread,
            "ask_close": bid_close + spread,
            "tick_count": 10,
        },
        index=index,
    )


def _state(direction: str = "NEUTRAL") -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [pd.Timestamp("2025-01-01T23:00:00Z")],
        name="timestamp_utc",
    )
    return pd.DataFrame(
        {
            "direction": [direction],
            "shock": [False],
            "DXY_compressed": [False],
            "EURUSD_compressed": [False],
        },
        index=index,
    )


def test_first_oco_side_triggers_and_reaches_fixed_target():
    bars = _bars()
    candidates = build_anchor_candidates(
        bars, _state(), _config()
    )
    assert len(candidates) == 1
    assert bool(candidates.iloc[0]["neutral_eligible"])
    trades, diagnostics = simulate(candidates, bars, _config())
    assert len(trades) == 1
    assert trades.iloc[0]["side"] == "LONG"
    assert trades.iloc[0]["exit_reason"] == "TARGET"
    assert trades.iloc[0]["r"] > 1.4
    assert diagnostics.iloc[0]["trigger_status"] == "TRIGGERED"


def test_same_bar_two_sided_trigger_is_no_trade():
    bars = _bars(ambiguous=True)
    candidates = build_anchor_candidates(
        bars, _state(), _config()
    )
    trades, diagnostics = simulate(candidates, bars, _config())
    assert trades.empty
    assert (
        diagnostics.iloc[0]["trigger_status"]
        == "AMBIGUOUS_BOTH_SIDES_NO_TRADE"
    )


def test_non_neutral_state_cannot_own_anchor():
    candidates = build_anchor_candidates(
        _bars(), _state("USD_UP"), _config()
    )
    assert not bool(candidates.iloc[0]["neutral_eligible"])
