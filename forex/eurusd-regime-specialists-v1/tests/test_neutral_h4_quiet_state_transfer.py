from __future__ import annotations

import math
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_h4_quiet_state_transfer import (
    aggregate_h1,
    profit_factor,
    summarize,
)


def _m5_hour(start: str, bid: float, spread: float = 0.00007) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=12, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "bid_open": bid,
            "bid_high": bid + 0.0001,
            "bid_low": bid - 0.0001,
            "bid_close": bid + 0.00002,
            "ask_open": bid + spread,
            "ask_high": bid + spread + 0.0001,
            "ask_low": bid + spread - 0.0001,
            "ask_close": bid + spread + 0.00002,
        }
    )


def test_aggregate_h1_requires_twelve_m5_bars_for_complete_hour() -> None:
    first = _m5_hour("2026-01-05T00:00:00Z", 1.10)
    second = _m5_hour("2026-01-05T01:00:00Z", 1.11).iloc[:-1]
    result = aggregate_h1(pd.concat([first, second], ignore_index=True))
    assert result["m5_bars"].tolist() == [12, 11]
    assert result["complete_hour"].tolist() == [True, False]


def test_profit_factor_uses_gross_wins_over_gross_losses() -> None:
    assert profit_factor([1.5, 0.5, -1.0, -0.5]) == 2.0 / 1.5
    assert math.isinf(profit_factor([1.0]))


def test_summarize_reports_payoff_and_concentration() -> None:
    trades = pd.DataFrame(
        {
            "exit_time_utc": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-02-01T00:00:00Z",
                    "2026-02-02T00:00:00Z",
                ],
                utc=True,
            ),
            "r": [1.5, 1.5, -1.0, -1.0],
            "stress_r": [1.4, 1.4, -1.1, -1.1],
            "pnl_usd_001_lot": [1.5, 1.5, -1.0, -1.0],
        }
    )
    result = summarize(trades)
    assert result["win_rate"] == 0.5
    assert result["realized_payoff_ratio"] == 1.5
    assert result["profit_factor"] == 1.5
    assert result["top_5pct_winners_removed_profit_factor"] == 0.75
