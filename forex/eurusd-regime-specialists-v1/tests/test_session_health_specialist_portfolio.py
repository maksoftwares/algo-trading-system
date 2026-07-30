from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from eurusd_regime_specialists.session_health_specialist_portfolio import (
    causal_session_health_gate,
)


CONTRACT = {
    "buckets": {
        "S00_03": [0, 1, 2, 3],
        "S04_07": [4, 5, 6, 7],
        "S08_11": [8, 9, 10, 11],
        "S12_15": [12, 13, 14, 15],
        "S16_19": [16, 17, 18, 19],
        "S20_23": [20, 21, 22, 23],
    },
    "lookback_completed_shadow_trades_per_bucket": 1,
    "minimum_trailing_profit_factor": 1.0,
}


def _trade(
    entry: datetime, exit_: datetime, pnl: float
) -> dict[str, object]:
    return {
        "entry_time_utc": entry,
        "exit_time_utc": exit_,
        "pnl_usd_001_lot": pnl,
    }


def test_gate_does_not_borrow_another_session_history() -> None:
    start = datetime(2026, 1, 5, 0, tzinfo=UTC)
    trades = pd.DataFrame(
        [
            _trade(start, start + timedelta(minutes=30), 2.0),
            _trade(
                start + timedelta(hours=4),
                start + timedelta(hours=4, minutes=30),
                -1.0,
            ),
        ]
    )
    result = causal_session_health_gate(trades, CONTRACT)
    assert bool(result.iloc[1]["session_health_admitted"]) is False
    assert int(result.iloc[1]["available_completed_session_trades"]) == 0


def test_gate_uses_only_outcomes_completed_by_entry() -> None:
    start = datetime(2026, 1, 5, 8, tzinfo=UTC)
    trades = pd.DataFrame(
        [
            _trade(start, start + timedelta(hours=3), 2.0),
            _trade(
                start + timedelta(hours=1),
                start + timedelta(hours=1, minutes=30),
                -1.0,
            ),
            _trade(
                start + timedelta(hours=3),
                start + timedelta(hours=3, minutes=30),
                1.0,
            ),
        ]
    )
    result = causal_session_health_gate(trades, CONTRACT)
    assert bool(result.iloc[1]["session_health_admitted"]) is False
    assert int(result.iloc[1]["available_completed_session_trades"]) == 0
    assert bool(result.iloc[2]["session_health_admitted"]) is True
    assert int(result.iloc[2]["available_completed_session_trades"]) == 2
