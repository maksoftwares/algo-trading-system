from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "outputs" / "RESULT.json"


def load_result() -> dict:
    return json.loads(
        RESULT.read_text(encoding="utf-8"),
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"Non-standard JSON constant: {value}")
        ),
    )


def test_rejected_result_cannot_authorize_broker_actions() -> None:
    result = load_result()
    assert result["decision"] == "REJECT_KEEP_V60_AND_FROZEN_V6"
    assert result["deployment_authorized"] is False
    assert result["broker_action_authorized"] is False
    assert result["evidence_status"] == "RETROSPECTIVE_POSTHOC_FORWARD_CONFIRMATION_REQUIRED"


def test_v20_gain_does_not_hide_worse_risk_adjusted_metrics() -> None:
    result = load_result()
    challenger = result["historical"]["challenger"]
    reference = result["frozen_v6"]["challenger"]

    assert challenger["net_pnl_usd"] > reference["net_pnl_usd"]
    assert challenger["profit_factor"] < reference["profit_factor"]
    assert (
        challenger["maximum_lifetime_closed_drawdown_usd"]
        > reference["maximum_lifetime_closed_drawdown_usd"]
    )
    assert (
        challenger["maximum_lifetime_equity_drawdown_usd"]
        > reference["maximum_lifetime_equity_drawdown_usd"]
    )
    assert challenger["trades_closed"] == reference["trades_closed"] - 2


def test_annual_and_downside_instability_is_recorded() -> None:
    result = load_result()
    assert all(
        result["gates"][f"v6_annual_{year}_not_lower"] is False
        for year in (2022, 2023, 2024)
    )
    assert all(
        result["gates"][f"v6_annual_{year}_not_lower"] is True
        for year in (2021, 2025, 2026)
    )
    assert result["monthly"]["v20"]["negative_month_pnl_usd"] < result["monthly"][
        "v6"
    ]["negative_month_pnl_usd"]
    assert result["gates"]["losing_month_burden_not_worse_v6"] is False


def test_cost_stress_and_retention_gates_reject_v20() -> None:
    result = load_result()
    assert result["gates"]["all_cost_stress_gates"] is False
    assert result["gates"]["trade_retention_vs_v60"] is False
    assert result["gates"]["frequency_retention_vs_v60"] is False
    assert all(not row["all_gates_pass"] for row in result["cost_stress"].values())


def test_solo_bypass_and_mixed_delegation_were_exercised_without_deadlock() -> None:
    result = load_result()
    challenger = result["historical"]["challenger"]
    assert result["gates"]["mechanism_exercised"] is True
    assert challenger["v7_solo_bypass_trade_ids"]
    assert challenger["v7_solo_bypass_cycles"] > 0
    assert challenger["v7_mixed_basket_cycles"] > 0
    assert challenger["standard_protection_cycles"] > challenger["v7_mixed_basket_cycles"]
    assert result["gates"]["no_open_positions"] is True
    assert result["gates"]["no_flat_deadlock"] is True
    assert result["gates"]["no_floating_deadlock"] is True
