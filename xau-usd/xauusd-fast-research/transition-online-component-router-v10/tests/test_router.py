from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from router import build_routed_trades, generate_manifest, route_candidates  # noqa: E402


def _trades() -> pd.DataFrame:
    rows = []
    for component, offset in ((1, 0), (2, 1)):
        for index, value in enumerate((1.0, -1.0, 0.5)):
            entry = pd.Timestamp("2024-01-01T00:00:00Z") + pd.Timedelta(
                days=index * 2, hours=offset
            )
            rows.append(
                {
                    "candidate_id": f"{component}-{index}",
                    "attempt_no": component,
                    "entry_time": entry,
                    "exit_time": entry + pd.Timedelta(hours=2),
                    "stress_net_r": value,
                    "gross_r": value,
                }
            )
    return pd.DataFrame(rows)


def _policy(mechanic: str, params: dict) -> SimpleNamespace:
    return SimpleNamespace(
        attempt_no=10,
        router_id="test",
        mechanic=mechanic,
        parameters_json=json.dumps(params, sort_keys=True),
        tie_priority="ATTEMPT_ASCENDING",
    )


def test_current_and_future_outcomes_cannot_change_earlier_routes() -> None:
    trades = _trades()
    policy = _policy(
        "TRAILING_MEAN_GATE",
        {
            "lookback_days": 365,
            "minimum_history": 1,
            "cold_start": "BASE",
            "weak_multiplier": 0.0,
            "threshold": 0.0,
        },
    )
    before = route_candidates(trades, policy, {1: 1.0, 2: 1.0})
    changed = trades.copy()
    changed.loc[changed["entry_time"].ge("2024-01-05"), "stress_net_r"] = -99.0
    after = route_candidates(changed, policy, {1: 1.0, 2: 1.0})
    cutoff = pd.Timestamp("2024-01-05T00:00:00Z")
    left = before.loc[before["entry_time"].lt(cutoff), "route_multiplier"].tolist()
    right = after.loc[after["entry_time"].lt(cutoff), "route_multiplier"].tolist()
    assert left == right


def test_current_outcome_cannot_change_its_own_route() -> None:
    trades = _trades()
    policy = _policy(
        "TRAILING_PF_GATE",
        {
            "lookback_days": 365,
            "minimum_history": 1,
            "cold_start": "BASE",
            "weak_multiplier": 0.0,
            "threshold": 1.0,
        },
    )
    before = route_candidates(trades, policy, {1: 1.0, 2: 1.0})
    target_id = "1-2"
    changed = trades.copy()
    changed.loc[changed["candidate_id"].eq(target_id), "stress_net_r"] = -999.0
    after = route_candidates(changed, policy, {1: 1.0, 2: 1.0})
    before_weight = before.loc[
        before["candidate_id"].eq(target_id), "route_multiplier"
    ].iat[0]
    after_weight = after.loc[
        after["candidate_id"].eq(target_id), "route_multiplier"
    ].iat[0]
    assert before_weight == after_weight


def test_open_shadow_trade_is_not_available() -> None:
    trades = pd.DataFrame(
        [
            {
                "candidate_id": "prior",
                "attempt_no": 1,
                "entry_time": pd.Timestamp("2024-01-01T00:00:00Z"),
                "exit_time": pd.Timestamp("2024-01-03T00:00:00Z"),
                "stress_net_r": 10.0,
                "gross_r": 10.0,
            },
            {
                "candidate_id": "current",
                "attempt_no": 1,
                "entry_time": pd.Timestamp("2024-01-02T00:00:00Z"),
                "exit_time": pd.Timestamp("2024-01-02T01:00:00Z"),
                "stress_net_r": -1.0,
                "gross_r": -1.0,
            },
        ]
    )
    policy = _policy(
        "TRAILING_MEAN_GATE",
        {
            "lookback_days": 365,
            "minimum_history": 1,
            "cold_start": "OFF",
            "weak_multiplier": 0.0,
            "threshold": 0.0,
        },
    )
    routed = route_candidates(trades, policy, {1: 1.0})
    current = routed.loc[routed["candidate_id"].eq("current")].iloc[0]
    assert current["shadow_count"] == 0
    assert current["route_multiplier"] == 0.0


def test_portfolio_overlap_applies_after_causal_routing() -> None:
    trades = _trades().iloc[:2].copy()
    trades.loc[:, "entry_time"] = pd.Timestamp("2024-01-02T00:00:00Z")
    trades.loc[:, "exit_time"] = pd.Timestamp("2024-01-02T02:00:00Z")
    policy = _policy(
        "TRAILING_MEAN_GATE",
        {
            "lookback_days": 365,
            "minimum_history": 10,
            "cold_start": "BASE",
            "weak_multiplier": 0.0,
            "threshold": 0.0,
        },
    )
    routed = build_routed_trades(trades, policy, {1: 1.0}, 4)
    assert len(routed) == 1


def test_manifest_is_deterministic_and_balanced() -> None:
    config = json.loads(
        (ROOT / "config" / "transition_online_component_router_v10.json").read_text(
            encoding="utf-8"
        )
    )
    first = generate_manifest(config)
    second = generate_manifest(config)
    assert first.equals(second)
    assert len(first) == 1000
    assert first.groupby("mechanic").size().eq(200).all()
    assert first["attempt_no"].tolist() == list(range(25239, 26239))
