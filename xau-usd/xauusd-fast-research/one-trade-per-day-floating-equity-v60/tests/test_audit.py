from __future__ import annotations

import pandas as pd

from src.audit import envelope_drawdown, floating_curve


def _bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z"], utc=True
            ),
            "bid_low": [99.0, 101.0],
            "bid_high": [102.0, 103.0],
            "bid_close": [101.0, 102.0],
            "ask_low": [100.0, 102.0],
            "ask_high": [103.0, 104.0],
            "ask_close": [102.0, 103.0],
        }
    )


def test_long_floating_curve_charges_cost_at_entry() -> None:
    ledger = pd.DataFrame(
        {
            "trade_id": ["L1"],
            "sleeve_id": ["V59_BROKER_CORE"],
            "entry_time": pd.to_datetime(["2026-01-01T00:00:01Z"], utc=True),
            "exit_time": pd.to_datetime(["2026-01-01T00:09:00Z"], utc=True),
            "direction": ["LONG"],
            "entry_price": [100.0],
            "pnl_usd": [1.0],
            "open_cost_usd": [0.5],
            "risk_usd": [2.0],
        }
    )
    curve = floating_curve(_bars(), ledger, "pnl_usd", "open_cost_usd", 5)
    assert curve["low_equity_pnl_usd"].tolist() == [-1.5, 0.5]
    assert curve["high_equity_pnl_usd"].tolist() == [1.5, 2.5]
    assert curve["open_positions"].tolist() == [1, 1]


def test_envelope_allows_same_bar_peak_then_trough() -> None:
    curve = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z"], utc=True
            ),
            "high_equity_pnl_usd": [5.0, 4.0],
            "low_equity_pnl_usd": [-2.0, 1.0],
            "open_positions": [1, 1],
            "open_addons": [0, 0],
            "known_initial_risk_usd": [2.0, 2.0],
            "addon_initial_risk_usd": [0.0, 0.0],
        }
    )
    result = envelope_drawdown(curve)
    assert result["maximum_drawdown_usd"] == 7.0
    assert result["peak_time_utc"] == "2026-01-01T00:00:00+00:00"
    assert result["trough_time_utc"] == "2026-01-01T00:00:00+00:00"
