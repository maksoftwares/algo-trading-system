from __future__ import annotations

import heapq
from typing import Any

import numpy as np
import pandas as pd


def _mechanism(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.select(
            [
                frame["BREAK_AND_RUN"].eq(1)
                & frame["DOWNSIDE_IMPULSE_RETEST"].eq(0)
                & frame["OPENING_RANGE_REVERSAL"].eq(0),
                frame["BREAK_AND_RUN"].eq(0)
                & frame["DOWNSIDE_IMPULSE_RETEST"].eq(1)
                & frame["OPENING_RANGE_REVERSAL"].eq(0),
                frame["BREAK_AND_RUN"].eq(0)
                & frame["DOWNSIDE_IMPULSE_RETEST"].eq(0)
                & frame["OPENING_RANGE_REVERSAL"].eq(1),
            ],
            ["BREAK", "RETEST", "OPEN_REV"],
            default="MULTI",
        ),
        index=frame.index,
    )


def build_overlay_candidates(
    actions: pd.DataFrame,
    base_candidates: pd.DataFrame,
    sleeve: dict[str, Any],
    execute_single_rule: Any,
    causal_shadow_health_gate: Any,
) -> tuple[pd.DataFrame, dict[str, int]]:
    frame = actions.loc[actions["regime"].ne("UNSAFE_SHOCK")].copy()
    for column in ("signal_time", "entry_time", "exit_time"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame["mechanism"] = _mechanism(frame)
    frame["h4adx"] = pd.cut(
        frame["h4_adx"],
        [-np.inf, 20.0, 30.0, np.inf],
        labels=["LOW", "MID", "HIGH"],
    ).astype(str)
    selected = frame.loc[
        frame["mechanism"].eq(sleeve["mechanism"])
        & frame["action_id"].eq(sleeve["action_id"])
        & frame["h4adx"].eq(sleeve["h4_adx_bucket"])
    ].copy()
    selected = execute_single_rule(
        selected,
        int(sleeve["maximum_open_positions"]),
        int(sleeve["maximum_entries_per_utc_date"]),
    )
    selected["pnl_usd"] = selected["stress_net_r"] * selected["risk_usd"]
    selected["trade_id"] = "V56_BREAK_" + selected["event_id"].astype(str)
    selected = causal_shadow_health_gate(
        selected,
        int(sleeve["shadow_window"]),
        float(sleeve["minimum_shadow_profit_factor"]),
    )
    selected = selected.loc[
        selected["risk_usd"].le(float(sleeve["maximum_risk_usd"]))
    ].copy()

    active_events: set[str] = set()
    for sleeve_id in sleeve["duplicate_event_sleeves"]:
        prefix = "V7_" if sleeve_id == "V7_SWING_HEALTH" else "V8_"
        ids = base_candidates.loc[
            base_candidates["sleeve_id"].eq(sleeve_id), "trade_id"
        ].astype(str)
        active_events.update(value.removeprefix(prefix) for value in ids)
    duplicate_mask = selected["event_id"].astype(str).isin(active_events)
    audit = {
        "eligible_before_duplicate_exclusion": int(len(selected)),
        "duplicate_events_excluded": int(duplicate_mask.sum()),
    }
    selected = selected.loc[~duplicate_mask].copy()
    selected["sleeve_id"] = str(sleeve["sleeve_id"])
    columns = [
        "trade_id",
        "sleeve_id",
        "event_id",
        "signal_time",
        "entry_time",
        "exit_time",
        "direction",
        "pnl_usd",
        "risk_usd",
        "shadow_completed_count",
        "shadow_profit_factor",
        "shadow_net_usd",
    ]
    return (
        selected[columns]
        .sort_values(["entry_time", "trade_id"], kind="mergesort")
        .reset_index(drop=True),
        audit,
    )


def govern_incremental_overlay(
    candidates: pd.DataFrame,
    fixed_trades: pd.DataFrame,
    account: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixed = fixed_trades.sort_values(["exit_time", "trade_id"], kind="mergesort").copy()
    base_addons = fixed.loc[fixed["sleeve_id"].ne("V50_CORE")].copy()
    fixed_exits = list(
        fixed[["exit_time", "pnl_usd"]].itertuples(index=False, name=None)
    )
    fixed_exit_index = 0
    overlay_exit_heap: list[tuple[pd.Timestamp, str, float]] = []
    active_overlay: list[tuple[pd.Timestamp, float]] = []
    base_daily = base_addons.groupby(base_addons["entry_time"].dt.date).size().to_dict()
    overlay_daily: dict[Any, int] = {}
    accepted: list[int] = []
    decisions: list[dict[str, Any]] = []
    equity = 0.0
    peak = 0.0
    suspended = False

    for index, row in candidates.iterrows():
        exits: list[tuple[pd.Timestamp, float]] = []
        while (
            fixed_exit_index < len(fixed_exits)
            and fixed_exits[fixed_exit_index][0] <= row["entry_time"]
        ):
            exits.append(
                (
                    fixed_exits[fixed_exit_index][0],
                    float(fixed_exits[fixed_exit_index][1]),
                )
            )
            fixed_exit_index += 1
        while overlay_exit_heap and overlay_exit_heap[0][0] <= row["entry_time"]:
            exit_time, _, pnl = heapq.heappop(overlay_exit_heap)
            exits.append((exit_time, pnl))
        for _, pnl in sorted(exits, key=lambda value: value[0]):
            equity += pnl
            peak = max(peak, equity)
            drawdown = peak - equity
            if not suspended and drawdown >= float(account["drawdown_suspend_usd"]):
                suspended = True
            elif suspended and drawdown <= float(account["drawdown_resume_usd"]):
                suspended = False

        active_overlay = [
            position for position in active_overlay if position[0] > row["entry_time"]
        ]
        active_base = base_addons.loc[
            base_addons["entry_time"].le(row["entry_time"])
            & base_addons["exit_time"].gt(row["entry_time"])
        ]
        date = row["entry_time"].date()
        active_risk = float(active_base["risk_usd"].sum()) + float(
            sum(position[1] for position in active_overlay)
        )
        daily_entries = int(base_daily.get(date, 0)) + int(overlay_daily.get(date, 0))
        reason = "ACCEPTED"
        if suspended:
            reason = "ACCOUNT_DRAWDOWN_SUSPENDED"
        elif len(active_base) + len(active_overlay) >= int(
            account["maximum_addon_open_positions"]
        ):
            reason = "MAXIMUM_ADDON_OPEN_POSITIONS"
        elif active_risk + float(row["risk_usd"]) > float(
            account["maximum_addon_concurrent_initial_risk_usd"]
        ):
            reason = "MAXIMUM_ADDON_CONCURRENT_RISK"
        elif daily_entries >= int(account["maximum_addon_entries_per_utc_date"]):
            reason = "MAXIMUM_ADDON_ENTRIES_PER_UTC_DATE"

        decisions.append(
            {
                "trade_id": row["trade_id"],
                "entry_time": row["entry_time"],
                "accepted": reason == "ACCEPTED",
                "decision_reason": reason,
                "closed_equity_before_entry_usd": equity,
                "closed_drawdown_before_entry_usd": peak - equity,
                "base_addon_active_before_entry": int(len(active_base)),
                "overlay_active_before_entry": int(len(active_overlay)),
                "addon_active_risk_before_entry_usd": active_risk,
                "addon_entries_on_utc_date_before_entry": daily_entries,
            }
        )
        if reason != "ACCEPTED":
            continue
        accepted.append(index)
        active_overlay.append((row["exit_time"], float(row["risk_usd"])))
        overlay_daily[date] = overlay_daily.get(date, 0) + 1
        heapq.heappush(
            overlay_exit_heap,
            (row["exit_time"], str(row["trade_id"]), float(row["pnl_usd"])),
        )

    return candidates.loc[accepted].copy().reset_index(drop=True), pd.DataFrame(
        decisions
    )
