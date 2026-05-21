from __future__ import annotations

import math

from phase0.independent_reproduction import _compare_metrics, _floor_to_step, _metrics_from_rows


def test_independent_reproduction_metrics_from_rows():
    trades = [
        {"net_pnl_usd": 100.0, "r_multiple": 1.0},
        {"net_pnl_usd": -50.0, "r_multiple": -0.5},
        {"net_pnl_usd": 25.0, "r_multiple": 0.25},
    ]

    metrics = _metrics_from_rows(trades, starting_equity=1000.0)

    assert metrics["trade_count"] == 3
    assert metrics["profit_factor"] == 2.5
    assert math.isclose(float(metrics["win_rate"]), 2 / 3)
    assert metrics["total_pnl_usd"] == 75.0


def test_independent_reproduction_comparison_uses_relative_tolerance():
    reference = {
        "trade_count": 100,
        "profit_factor": 1.4,
        "win_rate": 0.5,
        "total_pnl_usd": 1000.0,
        "max_drawdown_pct": 10.0,
    }
    observed = {
        "trade_count": 104,
        "profit_factor": 1.45,
        "win_rate": 0.49,
        "total_pnl_usd": 1030.0,
        "max_drawdown_pct": 10.4,
    }

    comparisons = _compare_metrics(reference, observed, tolerance_pct=5.0)

    assert all(row["status"] == "PASS" for row in comparisons)


def test_independent_reproduction_lot_flooring_matches_phase0_policy():
    assert _floor_to_step(0.6558587038, 0.01) == 0.65
    assert _floor_to_step(1.009, 0.01) == 1.0
