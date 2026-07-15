from __future__ import annotations

import numpy as np

from ml.a3_meta_v1.six_iteration_final_qualification import _block_bootstrap


def test_block_bootstrap_is_deterministic() -> None:
    daily = np.asarray([1.0, -0.5, 0.0, 2.0, -1.0] * 10)
    config = {
        "simulations": 100,
        "block_trading_days": 5,
        "batch_size": 25,
        "random_seed": 7,
        "drawdown_threshold_pct": 0.15,
    }
    first = _block_bootstrap(daily, 100.0, config)
    second = _block_bootstrap(daily, 100.0, config)
    assert first == second


def test_profitable_path_has_zero_ruin_at_large_capital() -> None:
    daily = np.ones(20)
    config = {
        "simulations": 100,
        "block_trading_days": 5,
        "batch_size": 20,
        "random_seed": 9,
        "drawdown_threshold_pct": 0.15,
    }
    result = _block_bootstrap(daily, 1000.0, config)
    assert result["risk_of_ruin_probability"] == 0.0
    assert result["drawdown_threshold_breach_probability"] == 0.0
    assert result["median_max_drawdown_pct"] == 0.0
