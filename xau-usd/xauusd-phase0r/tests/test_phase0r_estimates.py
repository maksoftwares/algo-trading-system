from __future__ import annotations

from phase0r.phase0r_estimates import _dedupe_trades, _max_drawdown, _summary_row


def test_estimate_overall_dedupes_repeated_matrix_cost_cells():
    trades = [
        {
            "candidate_id": "sample_v0",
            "broker": "capital_com",
            "signal_time_utc": "2020-01-01T00:00:00Z",
            "direction": "LONG",
            "entry_price": 1900.0,
            "stop_loss": 1890.0,
        },
        {
            "candidate_id": "sample_v0",
            "broker": "capital_com",
            "signal_time_utc": "2020-01-01T00:00:00Z",
            "direction": "LONG",
            "entry_price": 1900.0,
            "stop_loss": 1890.0,
        },
    ]

    assert len(_dedupe_trades(trades)) == 1


def test_estimate_summary_uses_net_r_and_fixed_risk_pnl():
    trades = [
        {"net_r": 1.25, "gross_r": 1.5, "stop_distance_points": 500, "applied_cost_r": 0.15},
        {"net_r": -1.15, "gross_r": -1.0, "stop_distance_points": 500, "applied_cost_r": 0.15},
    ]

    row = _summary_row(
        "sample_v0",
        trades,
        cell_id="all",
        broker="mixed",
        cost_model="measured",
        period="sample",
        measured_cost="p95",
        level="overall",
    )

    assert row["trade_count"] == 2
    assert row["win_rate_pct"] == 50.0
    assert row["total_net_r"] == 0.1
    assert row["estimated_net_pnl_usd"] == 5.0


def test_estimate_max_drawdown_is_cumulative_r_drawdown():
    assert _max_drawdown([1.0, -0.5, -1.0, 0.25]) == 1.5
