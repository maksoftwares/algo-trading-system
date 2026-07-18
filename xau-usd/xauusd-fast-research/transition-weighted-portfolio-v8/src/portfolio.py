from __future__ import annotations

import hashlib
from itertools import product
import json
from typing import Any, Mapping

import pandas as pd


def generate_manifest(config: Mapping[str, Any]) -> pd.DataFrame:
    components = sorted(config["components"], key=lambda item: int(item["attempt_no"]))
    attempts = [int(item["attempt_no"]) for item in components]
    weight_spaces = [tuple(float(value) for value in item["weights"]) for item in components]
    selection = config["selection"]
    rows: list[dict[str, Any]] = []
    attempt_no = int(selection["attempt_first"])
    for weights in product(*weight_spaces):
        allocation = {
            str(component): float(weight)
            for component, weight in zip(attempts, weights, strict=True)
        }
        for priority in selection["tie_priorities"]:
            canonical = json.dumps(
                {"weights": allocation, "tie_priority": priority},
                sort_keys=True,
                separators=(",", ":"),
            )
            rows.append(
                {
                    "attempt_no": attempt_no,
                    "portfolio_id": hashlib.sha256(
                        canonical.encode("ascii")
                    ).hexdigest()[:16],
                    "weights_json": json.dumps(
                        allocation, sort_keys=True, separators=(",", ":")
                    ),
                    "active_component_count": sum(weight > 0.0 for weight in weights),
                    "total_risk_weight": float(sum(weights)),
                    "tie_priority": str(priority),
                }
            )
            attempt_no += 1
    result = pd.DataFrame(rows)
    if len(result) != int(selection["attempt_count"]):
        raise ValueError("Weighted policy count differs from the contract")
    if int(result["attempt_no"].iat[-1]) != int(selection["attempt_last"]):
        raise ValueError("Weighted attempt boundary differs from the contract")
    if result["portfolio_id"].duplicated().any():
        raise ValueError("Duplicate weighted portfolio IDs")
    return result


def build_weighted_trades(
    component_trades: pd.DataFrame,
    policy: Any,
    maximum_daily: int,
) -> pd.DataFrame:
    weights = {
        int(key): float(value)
        for key, value in json.loads(policy.weights_json).items()
    }
    active = {attempt for attempt, weight in weights.items() if weight > 0.0}
    selected = component_trades.loc[
        component_trades["attempt_no"].isin(active)
    ].copy()
    ascending = str(policy.tie_priority) == "ATTEMPT_ASCENDING"
    if str(policy.tie_priority) not in (
        "ATTEMPT_ASCENDING",
        "ATTEMPT_DESCENDING",
    ):
        raise KeyError(policy.tie_priority)
    selected = selected.sort_values(
        ["entry_time", "attempt_no"],
        ascending=[True, ascending],
        kind="mergesort",
    )
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    rows: list[dict[str, Any]] = []
    for trade in selected.itertuples(index=False):
        entry_time = pd.Timestamp(trade.entry_time)
        if entry_time < position_until:
            continue
        day = entry_time.date()
        if daily_count.get(day, 0) >= maximum_daily:
            continue
        row = trade._asdict()
        component_attempt = int(row["attempt_no"])
        weight = weights[component_attempt]
        row["component_attempt_no"] = component_attempt
        row["component_stress_net_r"] = float(row["stress_net_r"])
        row["component_gross_r"] = float(row["gross_r"])
        row["risk_weight"] = weight
        row["stress_net_r"] = float(row["stress_net_r"]) * weight
        row["gross_r"] = float(row["gross_r"]) * weight
        row["attempt_no"] = int(policy.attempt_no)
        row["portfolio_id"] = str(policy.portfolio_id)
        row["tie_priority"] = str(policy.tie_priority)
        rows.append(row)
        position_until = pd.Timestamp(trade.exit_time)
        daily_count[day] = daily_count.get(day, 0) + 1
    return (
        pd.DataFrame(rows).sort_values("entry_time", kind="mergesort").reset_index(drop=True)
        if rows
        else pd.DataFrame()
    )

