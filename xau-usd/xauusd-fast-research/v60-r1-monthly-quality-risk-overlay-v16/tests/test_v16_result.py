from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_result() -> dict:
    return json.loads((ROOT / "outputs/RESULT.json").read_text(encoding="utf-8"))


def test_result_passes_but_does_not_authorize_deployment() -> None:
    result = load_result()
    assert result["decision"] == "RESEARCH_CHALLENGER_PASSES_FORWARD_CONFIRMATION_REQUIRED"
    assert result["deployment_authorized"] is False
    assert result["broker_action_authorized"] is False
    assert all(result["gates"].values())


def test_v16_improves_v6_without_more_losing_months() -> None:
    result = load_result()
    delta = result["delta_vs_v6"]
    assert delta["net_pnl_usd"] > 0.0
    assert delta["profit_factor"] > 0.0
    assert delta["closed_drawdown_usd"] <= 0.0
    assert delta["equity_drawdown_usd"] <= 0.0
    assert result["monthly"]["v16"]["negative_months"] <= result[
        "frozen_v6_monthly_reference"
    ]["negative_months"]
    assert result["monthly"]["v16"]["negative_month_pnl_usd"] > result[
        "frozen_v6_monthly_reference"
    ]["negative_month_pnl_usd"]


def test_external_and_stress_gates_pass() -> None:
    result = load_result()
    assert all(result["august_2026_through_25"]["gates"].values())
    assert all(result["dukascopy_crossfeed"]["gates"].values())
    assert all(item["all_gates_pass"] for item in result["cost_stress"].values())
    assert "v16" in result["august_2026_through_25"]
    assert "v16" in result["dukascopy_crossfeed"]


def test_canonical_99_percent_retention_caveat_is_explicit() -> None:
    result = load_result()
    retention = result["canonical_goal_trade_retention"]
    assert retention["observed_fraction_vs_v6"] >= 0.99
    assert retention["observed_fraction_vs_v60"] < 0.99
    assert retention["passes"] is False
    assert result["canonical_goal_authorized"] is False
