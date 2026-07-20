from __future__ import annotations

import heapq
from typing import Any

import pandas as pd


def govern_addons_soft_risk(
    candidates: pd.DataFrame,
    core: pd.DataFrame,
    account: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute unchanged signals with a causal drawdown-based risk multiplier."""
    core_exits = list(
        core.sort_values(["exit_time", "trade_id"], kind="mergesort")[
            [
                "exit_time",
                "pnl_usd",
            ]
        ].itertuples(index=False, name=None)
    )
    core_index = 0
    addon_exit_heap: list[tuple[pd.Timestamp, str, float]] = []
    active: list[tuple[pd.Timestamp, float]] = []
    daily: dict[Any, int] = {}
    accepted: list[int] = []
    accepted_multipliers: list[float] = []
    decisions: list[dict[str, Any]] = []
    equity = 0.0
    peak = 0.0
    derisked = False

    for index, row in candidates.iterrows():
        exits: list[tuple[pd.Timestamp, float]] = []
        while (
            core_index < len(core_exits)
            and core_exits[core_index][0] <= row["entry_time"]
        ):
            exits.append((core_exits[core_index][0], float(core_exits[core_index][1])))
            core_index += 1
        while addon_exit_heap and addon_exit_heap[0][0] <= row["entry_time"]:
            exit_time, _, pnl = heapq.heappop(addon_exit_heap)
            exits.append((exit_time, pnl))
        for _, pnl in sorted(exits, key=lambda value: value[0]):
            equity += pnl
            peak = max(peak, equity)
            drawdown = peak - equity
            if not derisked and drawdown >= float(account["drawdown_derisk_start_usd"]):
                derisked = True
            elif derisked and drawdown <= float(
                account["drawdown_full_risk_resume_usd"]
            ):
                derisked = False

        multiplier = float(account["drawdown_risk_multiplier"]) if derisked else 1.0
        effective_risk = float(row["risk_usd"]) * multiplier
        effective_pnl = float(row["pnl_usd"]) * multiplier
        active = [position for position in active if position[0] > row["entry_time"]]
        date = row["entry_time"].date()
        active_risk = float(sum(position[1] for position in active))
        reason = "ACCEPTED"
        if len(active) >= int(account["maximum_addon_open_positions"]):
            reason = "MAXIMUM_ADDON_OPEN_POSITIONS"
        elif active_risk + effective_risk > float(
            account["maximum_addon_concurrent_initial_risk_usd"]
        ):
            reason = "MAXIMUM_ADDON_CONCURRENT_RISK"
        elif daily.get(date, 0) >= int(account["maximum_addon_entries_per_utc_date"]):
            reason = "MAXIMUM_ADDON_ENTRIES_PER_UTC_DATE"

        decisions.append(
            {
                "trade_id": row["trade_id"],
                "sleeve_id": row["sleeve_id"],
                "entry_time": row["entry_time"],
                "accepted": reason == "ACCEPTED",
                "decision_reason": reason,
                "closed_equity_before_entry_usd": equity,
                "closed_drawdown_before_entry_usd": peak - equity,
                "drawdown_derisked": derisked,
                "risk_multiplier": multiplier,
                "original_risk_usd": float(row["risk_usd"]),
                "effective_risk_usd": effective_risk,
                "original_pnl_usd": float(row["pnl_usd"]),
                "effective_pnl_usd": effective_pnl,
                "addon_active_before_entry": len(active),
                "addon_active_risk_before_entry_usd": active_risk,
            }
        )
        if reason != "ACCEPTED":
            continue
        accepted.append(index)
        accepted_multipliers.append(multiplier)
        active.append((row["exit_time"], effective_risk))
        daily[date] = daily.get(date, 0) + 1
        heapq.heappush(
            addon_exit_heap,
            (row["exit_time"], str(row["trade_id"]), effective_pnl),
        )

    result = candidates.loc[accepted].copy().reset_index(drop=True)
    result["original_risk_usd"] = result["risk_usd"].astype(float)
    result["original_pnl_usd"] = result["pnl_usd"].astype(float)
    result["risk_multiplier"] = accepted_multipliers
    result["risk_usd"] = result["original_risk_usd"] * result["risk_multiplier"]
    result["pnl_usd"] = result["original_pnl_usd"] * result["risk_multiplier"]
    return result, pd.DataFrame(decisions)
