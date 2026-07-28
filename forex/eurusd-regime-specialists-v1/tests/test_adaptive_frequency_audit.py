from __future__ import annotations

import pandas as pd

from eurusd_regime_specialists.adaptive_frequency_audit import (
    match_oracle,
    profit_metrics,
    with_cost_haircut,
)


def _trades(values: list[float]) -> pd.DataFrame:
    count = len(values)
    return pd.DataFrame(
        {
            "entry_time": pd.date_range(
                "2026-01-01T00:00:00Z", periods=count, freq="h"
            ),
            "exit_time": pd.date_range(
                "2026-01-01T00:30:00Z", periods=count, freq="h"
            ),
            "side": ["LONG"] * count,
            "sleeve": ["TEST"] * count,
            "volume": [0.01] * count,
            "net_pnl_usd": values,
        }
    )


def test_profit_metrics_reports_payoff_pf_and_closed_drawdown() -> None:
    metrics = profit_metrics(_trades([1.5, -1.0, 1.5, -1.0]))
    assert metrics["trades"] == 4
    assert metrics["win_rate"] == 0.5
    assert metrics["realized_payoff_ratio"] == 1.5
    assert metrics["profit_factor"] == 1.5
    assert metrics["net_pnl_usd"] == 1.0
    assert metrics["maximum_closed_trade_drawdown_usd"] == 1.0


def test_cost_haircut_scales_with_volume_or_normalizes() -> None:
    frame = _trades([1.0, 2.0])
    frame["volume"] = [0.01, 0.02]
    stressed = with_cost_haircut(frame, 0.5)
    assert stressed["scenario_pnl_usd"].tolist() == [0.95, 1.9]
    normalized = with_cost_haircut(
        frame, 0.5, normalize_to_0p01_lot=True
    )
    assert normalized["scenario_pnl_usd"].tolist() == [0.95, 0.95]


def test_oracle_matching_is_same_side_same_day_and_one_to_one() -> None:
    predictions = _trades([1.0, 1.0])
    predictions.loc[1, "entry_time"] = pd.Timestamp(
        "2026-01-01T00:10:00Z"
    )
    oracle = pd.DataFrame(
        {
            "entry_time_utc": [
                pd.Timestamp("2026-01-01T00:05:00Z"),
                pd.Timestamp("2026-01-02T00:05:00Z"),
            ],
            "side": ["LONG", "LONG"],
            "oracle_trade_number": [1, 1],
        }
    )
    matches = match_oracle(predictions, oracle, 15)
    assert len(matches) == 1
    assert matches.iloc[0]["absolute_delta_minutes"] == 5.0
