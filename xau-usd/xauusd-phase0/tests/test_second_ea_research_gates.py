from __future__ import annotations

import math

import pandas as pd

from phase0.low_frequency_gates import (
    evaluate_low_frequency_matrix_gates,
    normalized_top5_trade_r,
    normalized_top_trade_r,
    structural_cost_precheck,
)


def test_low_frequency_concentration_formulas():
    assert normalized_top_trade_r(10.0, mean_abs_r=2.0, n_trades=25) == 1.0
    assert normalized_top5_trade_r(20.0, mean_abs_r=2.0, n_trades=16) == 2.5
    assert math.isinf(normalized_top_trade_r(1.0, mean_abs_r=0.0, n_trades=25))


def test_g9a_blocks_tight_stop_candidates_before_running():
    blocked = structural_cost_precheck(200.0, 0.12)
    costly = structural_cost_precheck(300.0, 0.35)
    cautious = structural_cost_precheck(300.0, 0.20)
    clean = structural_cost_precheck(400.0, 0.10)

    assert blocked.status == "BLOCKED_COST_FRAGILE_BY_DESIGN"
    assert costly.status == "BLOCKED_COST_FRAGILE_BY_DESIGN"
    assert cautious.status == "PASS_WITH_COST_CAUTION"
    assert clean.status == "PASS"


def test_g9b_fails_realized_p95_cost_above_absolute_cap():
    df = _passing_matrix()
    df.loc[0, "realized_p95_cost_r"] = 0.31

    results = evaluate_low_frequency_matrix_gates(df, {"total_cells": 9})

    cost_gate = next(result for result in results if result.name == "G9B_realized_measured_cost")
    assert cost_gate.status == "FAIL"


def test_low_frequency_matrix_gates_pass_core_matrix_context():
    results = evaluate_low_frequency_matrix_gates(_passing_matrix(), {"total_cells": 9})
    by_name = {result.name: result.status for result in results}

    assert by_name["G1_pf_survival"] == "PASS"
    assert by_name["G2_sample_size"] == "PASS"
    assert by_name["G4_low_frequency_concentration"] == "PASS"
    assert by_name["G7_cross_venue_floor"] == "PASS"


def _passing_matrix() -> pd.DataFrame:
    rows = []
    cell_id = 1
    for broker in ("capital_com", "pepperstone", "dukascopy"):
        for cost_model, pf in (("best_case", 1.60), ("median", 1.45), ("p95", 1.35)):
            rows.append(
                {
                    "cell_id": cell_id,
                    "broker": broker,
                    "cost_model": cost_model,
                    "profit_factor": pf,
                    "trade_count": 64,
                    "total_net_r": 20.0,
                    "mean_abs_r": 1.0,
                    "top_positive_trade_r": 4.0,
                    "top5_positive_sum_r": 12.0,
                    "max_drawdown_pct": 12.0,
                    "total_return_pct": 8.0,
                    "max_consecutive_zero_trade_months": 1,
                    "realized_median_cost_r": 0.10,
                    "realized_p95_cost_r": 0.20,
                    "era_slice": "2022-2025-06-30",
                }
            )
            cell_id += 1
    return pd.DataFrame(rows)
