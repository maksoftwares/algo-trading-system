from __future__ import annotations

import hashlib
import heapq
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_sources(repo_root: Path, sources: dict[str, Any]) -> dict[str, str]:
    verified: dict[str, str] = {}
    for source_id, source in sources.items():
        path = repo_root / str(source["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != str(source["sha256"]):
            raise ValueError(f"Source hash mismatch for {source_id}: {actual}")
        verified[source_id] = actual
    return verified


def profit_factor(values: pd.Series) -> float:
    gain = float(values.loc[values > 0.0].sum())
    loss = float(-values.loc[values < 0.0].sum())
    if loss == 0.0:
        return float("inf") if gain > 0.0 else 0.0
    return gain / loss


def _utc_ns(values: pd.Series) -> np.ndarray:
    return (
        pd.to_datetime(values, utc=True)
        .astype("datetime64[ns, UTC]")
        .astype("int64")
        .to_numpy()
    )


def causal_shadow_health_gate(
    trades: pd.DataFrame,
    window: int,
    minimum_profit_factor: float,
) -> pd.DataFrame:
    ordered = trades.sort_values(
        ["signal_time", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)
    completed = ordered.sort_values(["exit_time", "trade_id"], kind="mergesort")
    exit_ns = _utc_ns(completed["exit_time"])
    pnl = completed["pnl_usd"].to_numpy(dtype=float)
    positive = np.concatenate(([0.0], np.cumsum(np.maximum(pnl, 0.0))))
    negative = np.concatenate(([0.0], np.cumsum(np.maximum(-pnl, 0.0))))
    net = np.concatenate(([0.0], np.cumsum(pnl)))
    completed_count = np.searchsorted(
        exit_ns, _utc_ns(ordered["signal_time"]), side="left"
    )
    lower = np.maximum(0, completed_count - int(window))
    gain = positive[completed_count] - positive[lower]
    loss = negative[completed_count] - negative[lower]
    trailing_net = net[completed_count] - net[lower]
    trailing_pf = np.divide(
        gain, loss, out=np.full(len(gain), np.inf), where=loss > 0.0
    )
    ordered["shadow_completed_count"] = completed_count - lower
    ordered["shadow_profit_factor"] = trailing_pf
    ordered["shadow_net_usd"] = trailing_net
    ordered["health_gate_pass"] = (
        ordered["shadow_completed_count"].ge(int(window))
        & ordered["shadow_profit_factor"].ge(float(minimum_profit_factor))
        & ordered["shadow_net_usd"].gt(0.0)
    )
    return ordered.loc[ordered["health_gate_pass"]].copy()


def load_v50_core(repo_root: Path, config: dict[str, Any]) -> pd.DataFrame:
    sources = config["sources"]
    core = pd.read_parquet(repo_root / sources["normalized_core"]["path"])
    decisions = pd.read_csv(repo_root / sources["v50_decisions"]["path"])
    policy = config["v50_policy"]
    accepted = set(
        decisions.loc[
            decisions["policy_id"].eq(policy["policy_id"])
            & decisions["accepted"].astype(bool),
            "trade_id",
        ].astype(str)
    )
    target = core["specialist_id"].eq(policy["target_specialist_id"]) & core[
        "source_strategy"
    ].eq(policy["target_source_strategy"])
    core = core.loc[~target | core["trade_id"].astype(str).isin(accepted)].copy()
    core["entry_time"] = pd.to_datetime(core["entry_time_utc"], utc=True)
    core["exit_time"] = pd.to_datetime(core["exit_time_utc"], utc=True)
    core["signal_time"] = core["entry_time"]
    core["pnl_usd"] = core["pnl_usd_0p01_equiv"].astype(float)
    core["risk_usd"] = np.nan
    core["sleeve_id"] = "V50_CORE"
    core["trade_id"] = core["trade_id"].astype(str)
    return core


def _enrich_v8(actions: pd.DataFrame) -> pd.DataFrame:
    frame = actions.loc[actions["regime"].ne("UNSAFE_SHOCK")].copy()
    frame["mechanism"] = np.select(
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
    )
    frame["h1adx"] = pd.cut(
        frame["h1_adx"], [-np.inf, 20.0, 30.0, np.inf], labels=["LOW", "MID", "HIGH"]
    ).astype(str)
    frame["atrstate"] = pd.cut(
        frame["atr_ratio"],
        [-np.inf, 0.8, 1.2, np.inf],
        labels=["LOW", "NORMAL", "HIGH"],
    ).astype(str)
    frame["pnl_usd"] = frame["stress_net_r"] * frame["risk_usd"]
    return frame


def execute_single_rule(
    frame: pd.DataFrame, maximum_open: int, maximum_daily: int
) -> pd.DataFrame:
    ordered = frame.sort_values(
        ["entry_time", "event_id"], kind="mergesort"
    ).drop_duplicates("event_id", keep="first")
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    accepted: list[int] = []
    for index, row in ordered.iterrows():
        active = [exit_time for exit_time in active if exit_time > row["entry_time"]]
        date = row["entry_time"].date()
        if len(active) >= maximum_open or daily.get(date, 0) >= maximum_daily:
            continue
        accepted.append(index)
        active.append(row["exit_time"])
        daily[date] = daily.get(date, 0) + 1
    return ordered.loc[accepted].copy().reset_index(drop=True)


def load_addon_candidates(repo_root: Path, config: dict[str, Any]) -> pd.DataFrame:
    sources = config["sources"]
    sleeve = config["sleeves"]

    v7 = pd.read_parquet(repo_root / sources["v7_trades"]["path"])
    v7["pnl_usd"] = v7["portfolio_pnl_usd"].astype(float)
    v7["sleeve_id"] = sleeve["v7"]["sleeve_id"]
    v7["trade_id"] = v7["v7_trade_id"].astype(str)
    v7 = causal_shadow_health_gate(
        v7,
        int(sleeve["v7"]["shadow_window"]),
        float(sleeve["v7"]["minimum_shadow_profit_factor"]),
    )
    v7 = v7.loc[v7["risk_usd"].le(float(sleeve["v7"]["maximum_risk_usd"]))]

    actions = _enrich_v8(
        pd.read_parquet(repo_root / sources["expansion_actions"]["path"])
    )
    v8_policy = sleeve["v8"]
    v8 = actions.loc[
        actions["mechanism"].eq(v8_policy["mechanism"])
        & actions["action_id"].eq(v8_policy["action_id"])
        & actions["h1adx"].eq(v8_policy["h1adx"])
        & actions["atrstate"].eq(v8_policy["atrstate"])
    ]
    v8 = execute_single_rule(
        v8,
        int(v8_policy["maximum_open_positions"]),
        int(v8_policy["maximum_entries_per_utc_date"]),
    )
    v8["sleeve_id"] = v8_policy["sleeve_id"]
    v8["trade_id"] = "V8_" + v8["event_id"].astype(str)
    v8 = causal_shadow_health_gate(
        v8,
        int(v8_policy["shadow_window"]),
        float(v8_policy["minimum_shadow_profit_factor"]),
    )
    v8 = v8.loc[v8["risk_usd"].le(float(v8_policy["maximum_risk_usd"]))]

    v25 = pd.read_parquet(repo_root / sources["v25_trades"]["path"])
    v25["pnl_usd"] = v25["stress_net_r"] * v25["risk_usd"]
    v25["sleeve_id"] = sleeve["v25"]["sleeve_id"]
    v25["trade_id"] = "V25_" + v25["candidate_id"].astype(str)
    v25 = v25.loc[v25["risk_usd"].le(float(sleeve["v25"]["maximum_risk_usd"]))]

    columns = [
        "trade_id",
        "sleeve_id",
        "signal_time",
        "entry_time",
        "exit_time",
        "direction",
        "pnl_usd",
        "risk_usd",
    ]
    candidates = pd.concat([v7[columns], v8[columns], v25[columns]], ignore_index=True)
    for column in ("signal_time", "entry_time", "exit_time"):
        candidates[column] = pd.to_datetime(candidates[column], utc=True)
    if candidates["trade_id"].duplicated().any():
        raise ValueError("Duplicate add-on trade IDs")
    return candidates.sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)


def govern_addons(
    candidates: pd.DataFrame,
    core: pd.DataFrame,
    account: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    core_exits = list(
        core.sort_values(["exit_time", "trade_id"], kind="mergesort")[
            ["exit_time", "pnl_usd"]
        ].itertuples(index=False, name=None)
    )
    core_index = 0
    addon_exit_heap: list[tuple[pd.Timestamp, str, float]] = []
    active: list[tuple[pd.Timestamp, float]] = []
    daily: dict[Any, int] = {}
    accepted: list[int] = []
    decisions: list[dict[str, Any]] = []
    equity = 0.0
    peak = 0.0
    suspended = False

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
            if not suspended and drawdown >= float(account["drawdown_suspend_usd"]):
                suspended = True
            elif suspended and drawdown <= float(account["drawdown_resume_usd"]):
                suspended = False

        active = [position for position in active if position[0] > row["entry_time"]]
        date = row["entry_time"].date()
        active_risk = float(sum(position[1] for position in active))
        reason = "ACCEPTED"
        if suspended:
            reason = "ACCOUNT_DRAWDOWN_SUSPENDED"
        elif len(active) >= int(account["maximum_addon_open_positions"]):
            reason = "MAXIMUM_ADDON_OPEN_POSITIONS"
        elif active_risk + float(row["risk_usd"]) > float(
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
                "addon_active_before_entry": len(active),
                "addon_active_risk_before_entry_usd": active_risk,
            }
        )
        if reason != "ACCEPTED":
            continue
        accepted.append(index)
        active.append((row["exit_time"], float(row["risk_usd"])))
        daily[date] = daily.get(date, 0) + 1
        heapq.heappush(
            addon_exit_heap,
            (row["exit_time"], str(row["trade_id"]), float(row["pnl_usd"])),
        )
    return candidates.loc[accepted].copy().reset_index(drop=True), pd.DataFrame(
        decisions
    )


def window_metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    top_winners: int,
) -> dict[str, Any]:
    selected = trades.loc[
        trades["entry_time"].ge(start) & trades["entry_time"].lt(end)
    ].sort_values(["exit_time", "trade_id"], kind="mergesort")
    pnl = selected["pnl_usd"].astype(float)
    equity = np.concatenate(([0.0], pnl.cumsum().to_numpy(dtype=float)))
    removed = pnl.drop(pnl.nlargest(min(int(top_winners), len(pnl))).index)
    month_index = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end.tz_localize(None) - pd.Timedelta(nanoseconds=1)).to_period("M"),
        freq="M",
    )
    monthly = (
        selected.assign(
            month=selected["entry_time"].dt.tz_localize(None).dt.to_period("M")
        )
        .groupby("month", sort=True)["pnl_usd"]
        .sum()
        .reindex(month_index, fill_value=0.0)
    )
    weekdays = len(
        pd.bdate_range(
            start.tz_localize(None).normalize(),
            (end.tz_localize(None) - pd.Timedelta(nanoseconds=1)).normalize(),
        )
    )
    return {
        "trades": int(len(selected)),
        "calendar_weekdays": int(weekdays),
        "trades_per_weekday": float(len(selected) / weekdays) if weekdays else 0.0,
        "net_usd": float(pnl.sum()),
        "profit_factor": profit_factor(pnl),
        "closed_drawdown_usd": float(np.max(np.maximum.accumulate(equity) - equity)),
        "winner_removed_net_usd": float(removed.sum()),
        "positive_month_share": float((monthly > 0.0).mean()) if len(monthly) else 0.0,
    }


def combine_trades(core: pd.DataFrame, addons: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "trade_id",
        "sleeve_id",
        "signal_time",
        "entry_time",
        "exit_time",
        "direction",
        "pnl_usd",
        "risk_usd",
    ]
    combined = pd.concat([core[columns], addons[columns]], ignore_index=True)
    return combined.sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)


def rows_for_windows(
    core: pd.DataFrame,
    addons: pd.DataFrame,
    combined: pd.DataFrame,
    windows: dict[str, Iterable[str]],
    top_winners: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for window, bounds in windows.items():
        start, end = map(pd.Timestamp, bounds)
        for portfolio_id, trades in (
            ("CORE", core),
            ("ADDON", addons),
            ("COMBINED", combined),
        ):
            rows.append(
                {
                    "window": window,
                    "portfolio_id": portfolio_id,
                    "window_start_utc": start.isoformat(),
                    "cutoff_exclusive_utc": end.isoformat(),
                    **window_metrics(trades, start, end, top_winners),
                }
            )
    return pd.DataFrame(rows)


def evaluate_gates(metrics: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
    gates = config["gates"]
    account = config["account"]
    checks: dict[str, bool] = {}
    for window in gates["required_windows"]:
        addon = metrics.loc[
            metrics["window"].eq(window) & metrics["portfolio_id"].eq("ADDON")
        ].iloc[0]
        combined = metrics.loc[
            metrics["window"].eq(window) & metrics["portfolio_id"].eq("COMBINED")
        ].iloc[0]
        checks[f"{window}_frequency"] = combined["trades_per_weekday"] >= float(
            gates["minimum_combined_trades_per_weekday"]
        )
        checks[f"{window}_addon_pf"] = addon["profit_factor"] >= float(
            gates["minimum_addon_profit_factor"]
        )
        checks[f"{window}_addon_net"] = addon["net_usd"] > float(
            gates["minimum_addon_net_usd"]
        )
        checks[f"{window}_addon_winner_removed"] = addon[
            "winner_removed_net_usd"
        ] > float(gates["minimum_winner_removed_net_usd"])
        checks[f"{window}_combined_pf"] = combined["profit_factor"] >= float(
            gates["minimum_combined_profit_factor"]
        )
        checks[f"{window}_combined_net"] = combined["net_usd"] > float(
            gates["minimum_combined_net_usd"]
        )
        checks[f"{window}_combined_winner_removed"] = combined[
            "winner_removed_net_usd"
        ] > float(gates["minimum_winner_removed_net_usd"])
        checks[f"{window}_combined_drawdown"] = combined[
            "closed_drawdown_usd"
        ] <= float(account["maximum_combined_closed_drawdown_usd"])
    final_addon = metrics.loc[
        metrics["window"].eq("final") & metrics["portfolio_id"].eq("ADDON")
    ].iloc[0]
    final_combined = metrics.loc[
        metrics["window"].eq("final") & metrics["portfolio_id"].eq("COMBINED")
    ].iloc[0]
    checks["final_addon_drawdown"] = final_addon["closed_drawdown_usd"] <= float(
        account["maximum_final_addon_closed_drawdown_usd"]
    )
    checks["final_positive_month_share"] = final_combined[
        "positive_month_share"
    ] >= float(gates["minimum_final_combined_positive_month_share"])
    return {"checks": checks, "passed": bool(all(checks.values()))}
