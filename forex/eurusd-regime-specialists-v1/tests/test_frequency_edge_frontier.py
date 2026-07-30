from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
from eurusd_regime_specialists.frequency_edge_frontier import (
    causal_shadow_gate,
    outcome_metrics,
)


def _trade(
    entry: datetime,
    exit_: datetime,
    pnl: float,
    regime: str = "NEUTRAL",
) -> dict[str, object]:
    return {
        "entry_time": entry,
        "exit_time": exit_,
        "pnl_usd": pnl,
        "causal_regime": regime,
        "component": "RSI_SHADOW",
        "side": "LONG",
    }


def test_gate_uses_only_outcomes_exited_before_candidate_entry() -> None:
    start = datetime(2026, 8, 3, 8, tzinfo=UTC)
    trades = pd.DataFrame(
        [
            _trade(start, start + timedelta(hours=4), 2.0),
            _trade(
                start + timedelta(hours=1),
                start + timedelta(hours=2),
                -1.0,
            ),
            _trade(
                start + timedelta(hours=3),
                start + timedelta(hours=3, minutes=30),
                1.0,
            ),
        ]
    )
    gated = causal_shadow_gate(trades, "GLOBAL", 1, 0.5)
    assert bool(gated.iloc[1]["admitted"]) is False
    assert int(gated.iloc[1]["available_closed_shadow_trades"]) == 0
    assert bool(gated.iloc[2]["admitted"]) is False
    assert int(gated.iloc[2]["available_closed_shadow_trades"]) == 1


def test_regime_gate_does_not_borrow_other_regime_history() -> None:
    start = datetime(2026, 8, 3, 8, tzinfo=UTC)
    trades = pd.DataFrame(
        [
            _trade(start, start + timedelta(minutes=30), 2.0, "USD_UP"),
            _trade(
                start + timedelta(hours=1),
                start + timedelta(hours=2),
                -1.0,
                "NEUTRAL",
            ),
        ]
    )
    gated = causal_shadow_gate(trades, "REGIME", 1, 0.5)
    assert bool(gated.iloc[1]["admitted"]) is False
    assert int(gated.iloc[1]["available_closed_shadow_trades"]) == 0


def test_metrics_map_sunday_forex_open_to_monday_trading_date() -> None:
    sunday = datetime(2026, 8, 2, 22, tzinfo=UTC)
    monday = datetime(2026, 8, 3, 8, tzinfo=UTC)
    frame = pd.DataFrame(
        [
            _trade(sunday, sunday + timedelta(hours=1), 1.0),
            _trade(monday, monday + timedelta(hours=1), -0.5),
        ]
    )
    metrics = outcome_metrics(frame, 1, 0.05)
    assert metrics["trades"] == 2
    assert metrics["active_trading_dates"] == 1
    assert metrics["weekday_coverage"] == 1.0
