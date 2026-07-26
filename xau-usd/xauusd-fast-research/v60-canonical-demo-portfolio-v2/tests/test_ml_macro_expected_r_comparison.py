from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_ml_macro_expected_r_comparison",
    ROOT / "build_ml_macro_expected_r_comparison.py",
)
assert SPEC is not None
assert SPEC.loader is not None
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)


def test_b123_inputs_are_hash_bound() -> None:
    observed = comparison.verify_inputs()
    assert observed == {
        comparison.relative_path(path): digest
        for path, digest in comparison.EXPECTED_SHA256.items()
    }


def test_b123_exact_portfolio_improves_but_latest_window_fails() -> None:
    report, windows, folds, predictions, audit = comparison.build_outputs()
    indexed = windows.set_index("period")

    assert len(predictions) == 2368
    assert len(audit) == 2184
    assert folds["chosen_quantile"].tolist() == [
        0.0,
        0.0,
        0.0,
        0.0,
        0.15,
        0.05,
    ]
    assert np.isclose(
        indexed.at["1Y", "delta_net_pnl_usd"],
        66.72255058200199,
        rtol=0.0,
        atol=1e-6,
    )
    assert np.isclose(
        indexed.at["ALL", "delta_net_pnl_usd"],
        86.78933504949055,
        rtol=0.0,
        atol=1e-6,
    )
    assert indexed.at["ALL", "delta_closed_trade_drawdown_usd"] < 0.0
    assert indexed.at["3M", "delta_net_pnl_usd"] < 0.0
    assert report["deployment_eligible"] is False
    assert report["status"] == "HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL"
