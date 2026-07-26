from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))

from step_5_portfolio import (  # noqa: E402
    floating_equity_curve,
    prepare_candidate_economics,
    run_policy,
)


def _contract() -> dict:
    return json.loads(
        (PACKAGE / "config/step_5_shared_account_portfolio_contract_v1.json").read_text(
            encoding="utf-8"
        )
    )


def _candidate(
    candidate_id: str,
    *,
    family: str = "R1_UPTREND",
    mechanic: str = "TREND_PULLBACK_OR_CONTINUATION",
    direction: str = "LONG",
    entry: str = "2025-01-02T00:01:00Z",
    exit_: str = "2025-01-02T00:10:00Z",
    episode: str | None = None,
    risk: float = 5.0,
    stress_r: float = 0.3,
    historical: bool = False,
) -> dict:
    entry_price = 100.0
    gross = stress_r * risk + 0.5
    exit_price = entry_price + gross if direction == "LONG" else entry_price - gross
    return {
        "candidate_id": candidate_id,
        "family_id": family,
        "broad_mechanic": mechanic,
        "direction": direction,
        "structural_episode_id": episode or f"episode-{candidate_id}",
        "decision_time": pd.Timestamp(entry) - pd.Timedelta(minutes=1),
        "entry_time": pd.Timestamp(entry),
        "label_end_time": pd.Timestamp(exit_),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "initial_risk_usd_0p01": risk,
        "stress_net_r": stress_r,
        "label_status": "RESOLVED_TARGET",
        "broker_executable": True,
        "historical_portfolio_accepted": historical,
        "log1p_observation_cap_minutes": np.log1p(60.0),
        "planned_stop_price": risk,
    }


def test_prepare_candidate_economics_reconciles_endpoint() -> None:
    contract = _contract()
    rows = [
        _candidate("long", risk=2.0, stress_r=0.75),
        _candidate("short", direction="SHORT", risk=2.0, stress_r=0.75),
    ]
    result = prepare_candidate_economics(pd.DataFrame(rows), contract["account"])
    assert np.allclose(result["pnl_usd"], 1.5)
    assert np.allclose(result["implied_cost_usd"], 0.5)
    assert np.allclose(
        result["gross_endpoint_pnl_usd"]
        - result["implied_cost_usd"]
        - result["pnl_usd"],
        0.0,
    )


def test_governor_deduplicates_and_enforces_open_risk_structure() -> None:
    contract = _contract()
    rows = [
        _candidate("a", episode="same", entry="2025-01-02T00:01:00Z"),
        _candidate(
            "b",
            family="R2_DOWNTREND",
            direction="SHORT",
            episode="same",
            entry="2025-01-02T00:01:00Z",
        ),
        _candidate("c", entry="2025-01-02T00:02:00Z"),
        _candidate(
            "d",
            family="R3_COMPRESSION",
            mechanic="BREAKOUT_OR_VOLATILITY_EXPANSION",
            entry="2025-01-02T00:03:00Z",
        ),
        _candidate(
            "e",
            family="R4_CHOP",
            mechanic="CHOP_MEAN_REVERSION",
            entry="2025-01-02T00:04:00Z",
        ),
        _candidate(
            "f",
            family="R4_CHOP",
            mechanic="CHOP_MEAN_REVERSION",
            entry="2025-01-02T00:11:00Z",
            exit_="2025-01-02T00:20:00Z",
        ),
    ]
    economics = prepare_candidate_economics(pd.DataFrame(rows), contract["account"])
    spec = next(
        item
        for item in contract["policies"]
        if item["policy_id"] == "NINE_ALL_CANDIDATES_GOVERNED"
    )
    decisions, ledger, state = run_policy(economics, spec=spec, contract=contract)
    reasons = decisions.set_index("candidate_id")["decision_reason"].to_dict()
    assert reasons["a"] == "ACCEPTED"
    assert reasons["b"] == "REJECT_STRUCTURAL_EPISODE_DUPLICATE"
    assert reasons["c"] == "REJECT_FAMILY_POSITION_CAP"
    assert reasons["d"] == "ACCEPTED"
    assert reasons["e"] == "REJECT_DIRECTION_POSITION_CAP"
    assert reasons["f"] == "ACCEPTED"
    assert set(ledger["candidate_id"]) == {"a", "d", "f"}
    assert state["risk_invariants_pass"] is True


def test_frozen_policy_reproduces_historical_accept_field() -> None:
    contract = _contract()
    rows = [_candidate("a", historical=True), _candidate("b", historical=False)]
    economics = prepare_candidate_economics(pd.DataFrame(rows), contract["account"])
    spec = next(
        item
        for item in contract["policies"]
        if item["policy_id"] == "FIVE_FROZEN_POLICY_AS_RECORDED"
    )
    decisions, ledger, _ = run_policy(economics, spec=spec, contract=contract)
    assert decisions.set_index("candidate_id").at["a", "accepted"]
    assert not decisions.set_index("candidate_id").at["b", "accepted"]
    assert ledger["candidate_id"].tolist() == ["a"]


def test_floating_curve_marks_long_to_bid_and_charges_cost_at_open() -> None:
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
    ledger = pd.DataFrame(
        {
            "candidate_id": ["a"],
            "entry_time": pd.to_datetime(["2025-01-02T00:01:00Z"]),
            "label_end_time": pd.to_datetime(["2025-01-02T00:06:00Z"]),
            "direction": ["LONG"],
            "entry_price": [100.0],
            "open_cost_usd": [0.2],
            "pnl_usd": [1.5],
            "initial_risk_usd": [5.0],
            "margin_usd": [5.0],
        }
    )
    curve = floating_equity_curve(
        bars, ledger, starting_equity_usd=1000.0, bar_minutes=5
    )
    assert np.isclose(curve.loc[0, "low_equity_usd"], 998.8)
    assert np.isclose(curve.loc[0, "high_equity_usd"], 1000.8)
    assert np.isclose(curve.loc[1, "close_equity_usd"], 1001.5)
    assert curve["open_positions"].tolist() == [1, 1]
