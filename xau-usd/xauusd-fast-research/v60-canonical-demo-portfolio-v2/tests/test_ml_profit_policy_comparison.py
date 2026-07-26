from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_ml_profit_policy_comparison",
    ROOT / "build_ml_profit_policy_comparison.py",
)
assert SPEC is not None
assert SPEC.loader is not None
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)


def test_hashes_and_exact_join_are_frozen() -> None:
    observed = comparison.verify_inputs()
    trades, checks = comparison.load_joined_trades()

    assert observed == {
        comparison.relative_path(path): digest
        for path, digest in comparison.EXPECTED_SHA256.items()
    }
    assert len(trades) == 2184
    assert all(checks.values())
    missing = trades.loc[~trades["v12_prediction_available"]]
    assert missing["v12_retained"].all()
    assert missing["v12_action"].eq("MODEL_ABSTAIN_RETAIN_ALL").all()


def test_last_twelve_months_reconciles_exact_corrected_portfolio() -> None:
    trades, _ = comparison.load_joined_trades()
    cooldowns = comparison.load_cooldowns()
    start = comparison.FINAL_END - comparison.pd.DateOffset(months=12)
    frame = trades.loc[
        trades["entry_time"].ge(start) & trades["entry_time"].lt(comparison.FINAL_END)
    ]

    result, _ = comparison.replay_comparison(frame, cooldowns)

    assert result["raw"]["trade_rows"] == 356
    assert result["ml_v12"]["trade_rows"] == 325
    assert np.isclose(
        result["raw"]["net_pnl_usd"],
        2502.7232508824322,
        rtol=0.0,
        atol=1e-9,
    )
    assert np.isclose(
        result["ml_v12"]["net_pnl_usd"],
        2565.658074658697,
        rtol=0.0,
        atol=1e-9,
    )
    assert result["ml_v12"]["profit_factor"] > result["raw"]["profit_factor"]
    assert (
        result["ml_v12"]["closed_trade_drawdown_usd"]
        < result["raw"]["closed_trade_drawdown_usd"]
    )


def test_diagnostic_is_positive_but_not_deployable() -> None:
    report, windows, _, _, _, _ = comparison.build_outputs()
    indexed = windows.set_index("period")

    assert indexed.at["3M", "delta_net_pnl_usd"] < 0.0
    assert indexed.at["6M", "delta_net_pnl_usd"] > 0.0
    assert indexed.at["1Y", "delta_net_pnl_usd"] > 0.0
    assert indexed.at["ALL", "delta_net_pnl_usd"] > 0.0
    assert indexed.at["ALL", "delta_closed_trade_drawdown_usd"] > 0.0
    assert report["deployment_eligible"] is False
    assert not any(
        report["authorization"][key]
        for key in (
            "python_serving_authorized",
            "ml_shadow_authorized",
            "ea_consumption_authorized",
            "demo_authorized",
            "live_authorized",
            "broker_action_authorized",
            "runtime_change_authorized",
        )
    )
    assert (
        report["final_research_policy"]["selection_reason"]
        == "RETAIN_ALL_INSUFFICIENT_CALIBRATION_USD_IMPROVEMENT"
    )
