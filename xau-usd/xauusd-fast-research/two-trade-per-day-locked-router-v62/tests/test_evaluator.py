from __future__ import annotations

import pandas as pd

from src.evaluator import gate_results


def _windows(final_frequency: float) -> pd.DataFrame:
    rows = []
    for window in ("development_2", "confirmation", "final"):
        for portfolio in ("NEW", "COMBINED"):
            rows.append(
                {
                    "window": window,
                    "portfolio_id": portfolio,
                    "trades": 200,
                    "profit_factor": 1.6,
                    "net_usd": 100.0,
                    "top5_removed_net_usd": 50.0,
                    "trades_per_weekday": (
                        final_frequency
                        if window == "final" and portfolio == "COMBINED"
                        else 2.1
                    ),
                    "closed_drawdown_usd": 200.0,
                    "positive_month_share": 0.6,
                }
            )
    return pd.DataFrame(rows)


def _gates() -> dict:
    return {
        "required_windows": ["development_2", "confirmation", "final"],
        "minimum_new_trades": 100,
        "minimum_new_profit_factor": 1.15,
        "minimum_new_net_usd": 0.0,
        "minimum_new_top5_removed_net_usd": 0.0,
        "minimum_combined_trades_per_weekday": 2.0,
        "minimum_combined_profit_factor": 1.5,
        "minimum_combined_net_usd": 0.0,
        "maximum_combined_closed_drawdown_usd": 300.0,
        "minimum_combined_positive_month_share": 0.5,
    }


def test_gate_rejects_final_frequency_below_target() -> None:
    results = gate_results(_windows(1.99), _gates())
    assert results[-1]["passed"] is False


def test_gate_accepts_all_required_windows() -> None:
    results = gate_results(_windows(2.01), _gates())
    assert all(item["passed"] for item in results)
