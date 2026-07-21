from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], hash_key: str) -> str:
    values = dict(payload)
    values.pop(hash_key, None)
    encoded = json.dumps(
        values, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def calendar_weekdays(start: pd.Timestamp, end: pd.Timestamp) -> int:
    if end <= start:
        raise ValueError("V85 window end must follow its start")
    return int(len(pd.bdate_range(start.normalize(), end.normalize(), inclusive="left")))


def _slice(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return frame.loc[frame["entry_time"].between(start, end, inclusive="left")].copy()


def validate_ledgers(
    core: pd.DataFrame,
    candidates: pd.DataFrame,
    decisions: pd.DataFrame,
    combined: pd.DataFrame,
    expected: Mapping[str, Any],
) -> None:
    required = {
        "core": (core, {"trade_id", "entry_time", "exit_time"}),
        "candidates": (
            candidates,
            {"trade_id", "sleeve_id", "entry_time", "exit_time"},
        ),
        "decisions": (
            decisions,
            {"trade_id", "sleeve_id", "entry_time", "accepted", "decision_reason"},
        ),
        "combined": (combined, {"trade_id", "sleeve_id", "entry_time", "exit_time"}),
    }
    for name, (frame, columns) in required.items():
        missing = columns.difference(frame.columns)
        if missing:
            raise ValueError(f"V85 {name} columns missing: {sorted(missing)}")
        if frame["trade_id"].astype(str).duplicated().any():
            raise ValueError(f"V85 {name} trade IDs are not unique")
    counts = {
        "core_rows": len(core),
        "candidate_rows": len(candidates),
        "accepted_addons": int(decisions["accepted"].sum()),
        "combined_rows": len(combined),
    }
    for key, value in counts.items():
        if value != int(expected[key]):
            raise ValueError(f"V85 {key} changed: {value}")
    if set(candidates["trade_id"].astype(str)) != set(decisions["trade_id"].astype(str)):
        raise ValueError("V85 candidate and decision IDs differ")
    accepted_ids = set(
        decisions.loc[decisions["accepted"], "trade_id"].astype(str)
    )
    core_ids = set(core["trade_id"].astype(str))
    combined_ids = set(combined["trade_id"].astype(str))
    if core_ids.intersection(candidates["trade_id"].astype(str)):
        raise ValueError("V85 Core and add-on IDs overlap")
    if combined_ids != core_ids.union(accepted_ids):
        raise ValueError("V85 combined ledger is not Core plus accepted add-ons")


def window_capacity(
    *,
    window: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    core: pd.DataFrame,
    candidates: pd.DataFrame,
    decisions: pd.DataFrame,
    target: float,
) -> tuple[dict[str, Any], pd.DataFrame]:
    days = calendar_weekdays(start, end)
    required_trades = int(math.ceil(target * days))
    core_window = _slice(core, start, end)
    candidate_window = _slice(candidates, start, end)
    decision_window = _slice(decisions, start, end)
    accepted = decision_window.loc[decision_window["accepted"]].copy()
    rejected = decision_window.loc[~decision_window["accepted"]].copy()
    current_trades = len(core_window) + len(accepted)
    upper_trades = len(core_window) + len(candidate_window)

    current_dates = pd.concat(
        [core_window["entry_time"], accepted["entry_time"]], ignore_index=True
    ).dt.date.value_counts()
    upper_dates = pd.concat(
        [core_window["entry_time"], candidate_window["entry_time"]], ignore_index=True
    ).dt.date.value_counts()
    current_days_at_target = int((current_dates >= target).sum())
    upper_days_at_target = int((upper_dates >= target).sum())

    row = {
        "window": window,
        "start_utc": start.isoformat(),
        "end_exclusive_utc": end.isoformat(),
        "calendar_weekdays": days,
        "target_trades": required_trades,
        "core_trades": int(len(core_window)),
        "accepted_addons": int(len(accepted)),
        "rejected_addons": int(len(rejected)),
        "all_distinct_addon_candidates": int(len(candidate_window)),
        "current_combined_trades": int(current_trades),
        "current_trades_per_weekday": current_trades / days,
        "current_trade_shortfall": max(0, required_trades - current_trades),
        "mechanical_upper_bound_trades": int(upper_trades),
        "mechanical_upper_bound_trades_per_weekday": upper_trades / days,
        "upper_bound_trade_shortfall": max(0, required_trades - upper_trades),
        "upper_bound_reaches_two_per_weekday": bool(upper_trades >= required_trades),
        "current_days_with_at_least_two_entries": current_days_at_target,
        "upper_bound_days_with_at_least_two_entries": upper_days_at_target,
        "current_days_with_at_least_two_share": current_days_at_target / days,
        "upper_bound_days_with_at_least_two_share": upper_days_at_target / days,
    }
    reasons = (
        rejected["decision_reason"]
        .value_counts()
        .rename_axis("decision_reason")
        .reset_index(name="rejected_addons")
    )
    reasons.insert(0, "window", window)
    return row, reasons
