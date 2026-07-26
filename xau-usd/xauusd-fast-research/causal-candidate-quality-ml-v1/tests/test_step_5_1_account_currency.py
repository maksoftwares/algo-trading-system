from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))

from step_5_1_account_currency import (  # noqa: E402
    account_policy_contract,
    build_account_economics,
    floating_account_curve,
    run_account_policy,
)


def _step_5_contract() -> dict:
    return json.loads(
        (
            PACKAGE / "config/step_5_shared_account_portfolio_contract_v1.json"
        ).read_text(encoding="utf-8")
    )


def _snapshot() -> dict:
    return {
        "account": {"balance": 3627.19, "equity": 3627.19, "currency": "AED"},
        "conversion": {
            "source_currency": "USD",
            "account_currency": "AED",
            "profit_account_per_source_usd": 3.6715,
            "loss_account_per_source_usd": 3.674,
        },
    }


def _candidate(
    candidate_id: str,
    *,
    risk: float = 2.0,
    stress_r: float = 0.75,
    gross_usd: float = 2.0,
    entry: str = "2025-01-02T00:01:00Z",
    exit_: str = "2025-01-02T00:06:00Z",
) -> dict:
    return {
        "candidate_id": candidate_id,
        "family_id": "R1_UPTREND",
        "broad_mechanic": "TREND_PULLBACK_OR_CONTINUATION",
        "direction": "LONG",
        "structural_episode_id": f"episode-{candidate_id}",
        "decision_time": pd.Timestamp(entry) - pd.Timedelta(minutes=1),
        "entry_time": pd.Timestamp(entry),
        "label_end_time": pd.Timestamp(exit_),
        "entry_price": 100.0,
        "exit_price": 100.0 + gross_usd,
        "initial_risk_usd_0p01": risk,
        "stress_net_r": stress_r,
        "label_status": "RESOLVED_TARGET",
        "broker_executable": True,
        "historical_portfolio_accepted": False,
        "log1p_observation_cap_minutes": np.log1p(60.0),
        "planned_stop_price": 98.0,
    }


def test_account_economics_uses_adverse_rate_for_risk_and_cost() -> None:
    result, conversion = build_account_economics(
        pd.DataFrame([_candidate("winner")]),
        step_5_contract=_step_5_contract(),
        broker_snapshot=_snapshot(),
    )
    row = result.iloc[0]
    assert np.isclose(row["source_pnl_usd"], 1.5)
    assert np.isclose(row["source_implied_cost_usd"], 0.5)
    assert np.isclose(row["initial_risk_usd"], 2.0 * 3.674)
    assert np.isclose(row["gross_endpoint_pnl_usd"], 2.0 * 3.6715)
    assert np.isclose(row["implied_cost_usd"], 0.5 * 3.674)
    assert np.isclose(row["pnl_usd"], 2.0 * 3.6715 - 0.5 * 3.674)
    assert conversion["starting_equity_account"] == 3627.19


def test_account_economics_converts_losing_path_conservatively() -> None:
    result, _ = build_account_economics(
        pd.DataFrame(
            [_candidate("loser", risk=2.0, stress_r=-1.25, gross_usd=-2.0)]
        ),
        step_5_contract=_step_5_contract(),
        broker_snapshot=_snapshot(),
    )
    row = result.iloc[0]
    assert np.isclose(row["source_pnl_usd"], -2.5)
    assert np.isclose(row["source_implied_cost_usd"], 0.5)
    assert np.isclose(row["pnl_usd"], -2.5 * 3.674)


def test_account_governor_applies_risk_fraction_to_aed_equity() -> None:
    step_5 = _step_5_contract()
    mapping = [
        [spec["policy_id"], f"AED_{spec['policy_id']}"]
        for spec in step_5["policies"]
    ]
    contract = account_policy_contract(step_5, _snapshot(), mapping)
    economics, _ = build_account_economics(
        pd.DataFrame([_candidate("too-large", risk=8.0, stress_r=0.25)]),
        step_5_contract=step_5,
        broker_snapshot=_snapshot(),
    )
    spec = next(
        item
        for item in contract["policies"]
        if item["policy_id"] == "AED_NINE_ALL_CANDIDATES_GOVERNED"
    )
    decisions, ledger, state = run_account_policy(
        economics, spec=spec, contract=contract
    )
    assert decisions.iloc[0]["decision_reason"] == "REJECT_SINGLE_TRADE_RISK"
    assert ledger.empty
    assert np.isclose(state["limits_account"]["single_risk"], 3627.19 * 0.0075)


def test_floating_account_curve_marks_bid_and_charges_aed_cost() -> None:
    bars = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                ["2025-01-02T00:00:00Z", "2025-01-02T00:05:00Z"]
            ),
            "bid_low": [99.0, 100.0],
            "bid_high": [101.0, 102.0],
            "bid_close": [100.5, 101.5],
            "ask_low": [99.2, 100.2],
            "ask_high": [101.2, 102.2],
            "ask_close": [100.7, 101.7],
        }
    )
    cost = 0.2 * 3.674
    ledger = pd.DataFrame(
        {
            "candidate_id": ["a"],
            "entry_time": pd.to_datetime(["2025-01-02T00:01:00Z"]),
            "label_end_time": pd.to_datetime(["2025-01-02T00:06:00Z"]),
            "direction": ["LONG"],
            "entry_price": [100.0],
            "open_cost_account": [cost],
            "pnl_account": [1.5 * 3.6715],
            "initial_risk_account": [5.0 * 3.674],
            "margin_account": [5.0 * 3.674],
        }
    )
    curve = floating_account_curve(
        bars,
        ledger,
        starting_equity_account=1000.0,
        bar_minutes=5,
        profit_rate=3.6715,
        loss_rate=3.674,
    )
    assert np.isclose(curve.loc[0, "low_equity_account"], 1000.0 - 3.674 - cost)
    assert np.isclose(curve.loc[0, "high_equity_account"], 1000.0 + 3.6715 - cost)
    assert np.isclose(curve.loc[1, "close_equity_account"], 1000.0 + 1.5 * 3.6715)
    assert curve["open_positions"].tolist() == [1, 1]
