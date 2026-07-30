from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists import frozen_residual_history_diagnostic as module


def _config() -> dict:
    return json.loads(module.CONFIG_PATH.read_text(encoding="utf-8"))


def test_value_metrics_reports_requested_edge_geometry() -> None:
    metrics = module.value_metrics(
        [2.0, -1.0, 2.0, -1.0],
        [1.9, -1.1, 1.9, -1.1],
        4,
    )
    assert metrics["trades_per_weekday"] == 1.0
    assert metrics["win_rate"] == 0.5
    assert metrics["payoff_ratio"] == 2.0
    assert metrics["profit_factor"] == 2.0
    assert round(metrics["stressed_profit_factor"], 10) == round(3.8 / 2.2, 10)


def test_best_removed_profit_factor_removes_largest_winners() -> None:
    values = [10.0, 2.0, -1.0, 2.0, -1.0]
    assert module.best_removed_profit_factor(values) == 2.0


def test_portfolio_metrics_uses_unique_weekday_coverage() -> None:
    frame = pd.DataFrame(
        {
            "entry_time": pd.to_datetime(
                [
                    "2026-08-03T08:00:00Z",
                    "2026-08-03T20:00:00Z",
                    "2026-08-04T20:00:00Z",
                ]
            ),
            "decision_date": ["2026-08-03", "2026-08-03", "2026-08-04"],
            "component": ["M15_REGIME", "RESIDUAL_LIVE", "RESIDUAL_LIVE"],
            "pnl_usd": [2.0, -1.0, 2.0],
            "stressed_pnl_usd": [1.9, -1.1, 1.9],
        }
    )
    metrics = module.portfolio_metrics(frame, 4)
    assert metrics["trades_per_weekday"] == 0.75
    assert metrics["weekday_coverage"] == 0.5


def test_residual_metrics_counts_friday_cash_in_denominator() -> None:
    records = [
        {
            "decision_date": "2026-09-03",
            "status": "RESOLVED",
            "eligible_side": "LONG",
            "eligible_result_r": 1.5,
        },
        {
            "decision_date": "2026-09-04",
            "status": "CASH_MARKET_CLOSURE",
            "eligible_side": "CASH",
            "eligible_result_r": None,
        },
    ]
    metrics = module.residual_metrics(
        records,
        "2026-09-01",
        "2026-10-01",
        0.0625,
    )
    assert metrics["complete_weekdays"] == 2
    assert metrics["trades"] == 1
    assert metrics["trades_per_weekday"] == 0.5
    assert metrics["friday_market_closure_cash"] == 1


def test_source_verifier_rejects_any_changed_contract() -> None:
    config = copy.deepcopy(_config())
    config["source"]["protected_m15_trades_sha256"] = "0" * 64
    try:
        module.verify_sources(config)
    except RuntimeError as error:
        assert "source mismatch" in str(error)
    else:
        raise AssertionError("changed diagnostic source was accepted")


def test_diagnostic_is_one_variant_and_never_forward_evidence() -> None:
    config = _config()
    assert config["candidate_parameters_may_change"] is False
    assert config["result_can_count_as_forward_evidence"] is False
    assert config["demo_order_authorized"] is False
    assert "NO_PARAMETER_GRID" in config["prohibitions"]
    assert "NO_ORDER_AUTHORIZATION" in config["prohibitions"]
