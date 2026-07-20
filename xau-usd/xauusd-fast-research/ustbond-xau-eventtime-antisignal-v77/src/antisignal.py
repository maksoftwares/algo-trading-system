from __future__ import annotations

from typing import Any

import pandas as pd


def invert_candidates(candidates: pd.DataFrame, *, family: str) -> pd.DataFrame:
    required = {"candidate_id", "policy_id", "direction", "decision_timestamp_ms"}
    if missing := sorted(required - set(candidates.columns)):
        raise ValueError(f"V77 candidates are missing columns: {missing}")
    result = candidates.copy()
    if not result["direction"].isin(["LONG", "SHORT"]).all():
        raise ValueError("V77 source direction is invalid")
    result["source_direction"] = result["direction"]
    result["direction"] = result["source_direction"].map(
        {"LONG": "SHORT", "SHORT": "LONG"}
    )
    result["family"] = family
    result["candidate_id"] = (
        "V77:"
        + result["policy_id"].astype(str)
        + ":"
        + result["decision_timestamp_ms"].astype("int64").astype(str)
        + ":"
        + result["direction"]
    )
    if result["candidate_id"].duplicated().any():
        raise ValueError("V77 candidate IDs are not unique")
    return result


def without_minimum_sample(gates: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in gates.items() if key != "minimum_resolved_trades"}
