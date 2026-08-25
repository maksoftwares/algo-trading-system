from __future__ import annotations

import pandas as pd

from run_cohort_audit import profit_factor, stratified_permutation_p_value


def test_profit_factor_uses_realized_values() -> None:
    assert profit_factor([2.0, -4.0, -1.0]) == 0.4


def test_stratified_permutation_is_deterministic() -> None:
    frame = pd.DataFrame(
        {
            "source_id": ["A"] * 6,
            "selected_by_v2": [True, True, False, False, False, False],
            "baseline_runtime_pnl_usd": [-5.0, -4.0, 1.0, 2.0, 3.0, 4.0],
        }
    )
    first = stratified_permutation_p_value(
        frame, ["source_id"], iterations=1_000, seed=7
    )
    second = stratified_permutation_p_value(
        frame, ["source_id"], iterations=1_000, seed=7
    )
    assert first == second
    assert 0.0 < first < 0.2
