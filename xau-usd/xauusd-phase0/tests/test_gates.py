from __future__ import annotations

import pandas as pd

from phase0.config import load_project_config
from phase0.gates import (
    evaluate_adversarial_gate,
    evaluate_decile_gate,
    evaluate_matrix_gates,
    evaluate_multisymbol_gate,
)


def test_matrix_gates_pass(project_root):
    config = load_project_config(project_root)

    results = evaluate_matrix_gates(_passing_matrix(), config.phase0["gates"])

    assert {result.status for result in results} == {"PASS"}


def test_matrix_gates_fail_sample_size(project_root):
    config = load_project_config(project_root)
    matrix = _passing_matrix()
    matrix.loc[0, "trade_count"] = 10

    results = evaluate_matrix_gates(matrix, config.phase0["gates"])

    sample = next(result for result in results if result.name == "sample_size")
    assert sample.status == "FAIL"
    assert "1" in sample.observed


def test_decile_gate(project_root):
    config = load_project_config(project_root)
    deciles = pd.DataFrame({"profit_factor": [1.2] * 10, "trade_count": [12] * 10})

    result = evaluate_decile_gate(deciles, config.phase0["gates"])

    assert result.status == "PASS"


def test_multisymbol_gate_with_xau_justification(project_root):
    config = load_project_config(project_root)
    multisymbol = pd.DataFrame({"symbol": ["EURUSD", "USDJPY"], "profit_factor": [0.8, 0.95]})

    result = evaluate_multisymbol_gate(
        multisymbol,
        config.phase0["gates"],
        xau_specific_mechanism="XAU session-specific liquidity behavior.",
    )

    assert result.status == "PASS_WITH_XAU_SPECIFIC_JUSTIFICATION"


def test_adversarial_gate_pending(project_root):
    config = load_project_config(project_root)

    result = evaluate_adversarial_gate(None, config.phase0["gates"], manual_review_complete=False)

    assert result.status == "PENDING"


def _passing_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cell_id": list(range(1, 10)),
            "profit_factor": [1.5] * 9,
            "trade_count": [50] * 9,
            "max_drawdown_pct": [10.0] * 9,
            "total_return_pct": [5.0] * 9,
            "largest_single_trade_pct_of_pnl": [5.0] * 9,
            "top5_trades_pct_of_pnl": [20.0] * 9,
            "max_consecutive_zero_trade_months": [1] * 9,
        }
    )
