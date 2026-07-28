from __future__ import annotations

import pandas as pd
import pytest

from eurusd_regime_specialists.adaptive_frequency_audit import (
    CONTROL_SLEEVE,
    M15_SLEEVE,
    cross_sleeve_overlap_audit,
    match_oracle,
    profit_metrics,
    synchronized_m5_portfolio_proxy,
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


def test_cross_sleeve_overlap_is_recomputed_from_half_open_intervals() -> None:
    frame = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:05:00Z",
                ]
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-01T00:10:00Z",
                    "2026-01-01T00:15:00Z",
                ]
            ),
            "side": ["LONG", "SHORT"],
            "sleeve": [M15_SLEEVE, CONTROL_SLEEVE],
            "volume": [0.01, 0.01],
            "entry_price": [1.1000, 1.1000],
            "exit_price": [1.1010, 1.1005],
            "net_pnl_usd": [1.0, -0.5],
        }
    )
    metrics, pairs = cross_sleeve_overlap_audit(frame)
    assert metrics["cross_sleeve_overlap_pairs"] == 1
    assert metrics["cross_sleeve_same_entry_pairs"] == 0
    assert metrics["cross_sleeve_entry_pairs_within_15_minutes"] == 1
    assert metrics["cross_sleeve_opposite_side_pairs"] == 1
    assert metrics["maximum_concurrent_positions_exact_intervals"] == 2
    assert metrics["maximum_concurrent_gross_lots_exact_intervals"] == 0.02
    assert metrics["maximum_absolute_net_lots_exact_intervals"] == 0.01
    assert metrics["maximum_opposing_lots_exact_intervals"] == 0.01
    assert pairs.iloc[0]["overlap_minutes"] == 5.0


def test_synchronized_proxy_marks_opposing_positions_on_bid_ask_extremes() -> None:
    frame = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-01T00:05:00Z",
                ]
            ),
            "exit_time": pd.to_datetime(
                [
                    "2026-01-01T00:10:00Z",
                    "2026-01-01T00:15:00Z",
                ]
            ),
            "side": ["LONG", "SHORT"],
            "sleeve": [M15_SLEEVE, CONTROL_SLEEVE],
            "volume": [0.01, 0.01],
            "entry_price": [1.1000, 1.1000],
            "exit_price": [1.1010, 1.1005],
            "commission": [0.0, 0.0],
            "swap": [0.0, 0.0],
            "net_pnl_usd": [1.0, -0.5],
        }
    )
    index = pd.date_range(
        "2026-01-01T00:00:00Z", periods=4, freq="5min"
    )
    quotes = pd.DataFrame(
        {
            "bid_low": [1.0990, 1.0980, 1.1000, 1.1000],
            "ask_high": [1.1002, 1.1020, 1.1030, 1.1000],
        },
        index=index,
    )
    metrics, curve = synchronized_m5_portfolio_proxy(
        frame,
        quotes,
        pd.Timestamp("2026-01-01T00:00:00Z"),
        pd.Timestamp("2026-01-01T00:20:00Z"),
    )
    assert metrics["trades_in_proxy"] == 2
    assert metrics[
        "maximum_conservative_floating_drawdown_usd"
    ] == pytest.approx(4.0)
    assert metrics["maximum_open_positions_intersecting_one_m5_bar"] == 2
    assert metrics["maximum_gross_lots_intersecting_one_m5_bar"] == 0.02
    assert metrics["maximum_absolute_net_lots_intersecting_one_m5_bar"] == 0.01
    assert metrics["maximum_opposing_lots_intersecting_one_m5_bar"] == 0.01
    assert metrics["terminal_realized_equity_usd"] == 0.5
    assert metrics["terminal_reconciliation_difference_usd"] == 0.0
    assert curve.loc[
        curve["timestamp_utc"].eq(pd.Timestamp("2026-01-01T00:05:00Z")),
        "conservative_equity_usd",
    ].iloc[0] == pytest.approx(-4.0)
