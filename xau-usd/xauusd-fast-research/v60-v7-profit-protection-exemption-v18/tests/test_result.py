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


def test_v18_tradeoff_is_recorded_against_frozen_v6() -> None:
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
    assert challenger["trades_closed"] < reference["trades_closed"]


def test_recent_gain_is_not_stable_across_calendar_years() -> None:
    result = load_result()
    assert all(
        result["historical"]["windows"][window]["challenger"]["net_pnl_usd"]
        >= result["frozen_v6"]["windows"][window]["challenger"]["net_pnl_usd"]
        for window in ("3m", "6m", "12m")
    )
    assert all(
        result["gates"][f"v6_annual_{year}_not_lower"] is False
        for year in (2021, 2022, 2023, 2024)
    )
    assert all(
        result["gates"][f"v6_annual_{year}_not_lower"] is True
        for year in (2025, 2026)
    )


def test_downside_and_cost_gates_reject_the_challenger() -> None:
    result = load_result()
    assert result["monthly"]["v18"]["negative_month_pnl_usd"] < result["monthly"]["v6"][
        "negative_month_pnl_usd"
    ]
    assert result["gates"]["losing_month_burden_not_worse_v6"] is False
    assert result["gates"]["all_cost_stress_gates"] is False
    assert all(not row["all_gates_pass"] for row in result["cost_stress"].values())


def test_mechanism_was_exercised_without_runtime_deadlock() -> None:
    result = load_result()
    assert result["gates"]["mechanism_exercised"] is True
    assert result["historical"]["challenger"]["v7_profit_protection_exempt_trade_ids"]
    assert result["historical"]["challenger"]["v7_profit_protection_exempt_overlap_cycles"] > 0
    assert result["gates"]["no_open_positions"] is True
    assert result["gates"]["no_flat_deadlock"] is True
    assert result["gates"]["no_floating_deadlock"] is True
    assert result["august_2026"]["status"] == "NOT_EVALUABLE_WITH_FROZEN_ENDPOINT"
