from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.neutral_macro_pressure_reversal import (
    aggregate_h4,
    attach_macro_and_regime,
)


def _m5(start: str, periods: int) -> pd.DataFrame:
    timestamp = pd.date_range(start, periods=periods, freq="5min", tz="UTC")
    base = pd.Series(range(periods), dtype=float) * 0.000001 + 1.10
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "bid_open": base,
            "bid_high": base + 0.0001,
            "bid_low": base - 0.0001,
            "bid_close": base + 0.00002,
            "ask_open": base + 0.00007,
            "ask_high": base + 0.00017,
            "ask_low": base - 0.00003,
            "ask_close": base + 0.00009,
        }
    )


def test_aggregate_h4_keeps_only_complete_48_bar_periods() -> None:
    result = aggregate_h4(_m5("2026-01-05T00:00:00Z", 95))
    assert len(result) == 1
    assert result["m5_bars"].tolist() == [48]


def test_macro_is_not_visible_before_conservative_available_time() -> None:
    h4 = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2026-01-02T20:00:00Z", "2026-01-03T00:00:00Z"], utc=True
            ),
            "value": [1, 2],
        }
    )
    macro = pd.DataFrame(
        {
            "observation_utc": pd.to_datetime(["2026-01-02T00:00:00Z"], utc=True),
            "macro_available_utc": pd.to_datetime(["2026-01-03T00:00:00Z"], utc=True),
            "real_yield_delta_20d": [0.2],
            "dollar_pct_20d": [1.0],
            "macro_pressure_score": [1.5],
        }
    )
    regimes = pd.DataFrame(
        {
            "timestamp": h4["timestamp"],
            "regime": ["chop", "compression"],
        }
    )
    result = attach_macro_and_regime(h4, macro, regimes)
    assert pd.isna(result.loc[0, "macro_pressure_score"])
    assert result.loc[1, "macro_pressure_score"] == 1.5
    assert result["regime"].tolist() == ["chop", "compression"]
