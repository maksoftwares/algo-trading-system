from __future__ import annotations

from itertools import combinations
import hashlib
import json
from typing import Any, Mapping

import pandas as pd


def generate_manifest(config: Mapping[str, Any]) -> pd.DataFrame:
    selection = config["selection"]
    attempts = sorted(int(item["attempt_no"]) for item in config["component_pool"])
    rows: list[dict[str, Any]] = []
    attempt_no = int(selection["attempt_first"])
    for size in range(
        int(selection["minimum_subset_size"]),
        int(selection["maximum_subset_size"]) + 1,
    ):
        for members in combinations(attempts, size):
            for priority in selection["tie_priorities"]:
                canonical = json.dumps(
                    {"component_attempts": members, "tie_priority": priority},
                    sort_keys=True,
                    separators=(",", ":"),
                )
                rows.append(
                    {
                        "attempt_no": attempt_no,
                        "composite_id": hashlib.sha256(
                            canonical.encode("ascii")
                        ).hexdigest()[:16],
                        "component_attempts_json": json.dumps(list(members)),
                        "component_count": size,
                        "tie_priority": str(priority),
                    }
                )
                attempt_no += 1
    result = pd.DataFrame(rows)
    if len(result) != int(selection["attempt_count"]):
        raise ValueError("Composite policy count differs from the contract")
    if int(result["attempt_no"].iat[-1]) != int(selection["attempt_last"]):
        raise ValueError("Composite attempt boundary differs from the contract")
    if result["composite_id"].duplicated().any():
        raise ValueError("Duplicate composite IDs")
    return result


def build_composite_trades(
    component_trades: pd.DataFrame,
    policy: Any,
    maximum_daily: int,
) -> pd.DataFrame:
    members = {int(value) for value in json.loads(policy.component_attempts_json)}
    selected = component_trades.loc[
        component_trades["attempt_no"].isin(members)
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
        row["component_attempt_no"] = int(row["attempt_no"])
        row["attempt_no"] = int(policy.attempt_no)
        row["composite_id"] = str(policy.composite_id)
        row["tie_priority"] = str(policy.tie_priority)
        rows.append(row)
        position_until = pd.Timestamp(trade.exit_time)
        daily_count[day] = daily_count.get(day, 0) + 1
    return (
        pd.DataFrame(rows).sort_values("entry_time", kind="mergesort").reset_index(drop=True)
        if rows
        else pd.DataFrame()
    )

