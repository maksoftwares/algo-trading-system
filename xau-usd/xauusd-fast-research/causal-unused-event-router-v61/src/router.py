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


def business_days(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(
        np.busday_count(
            np.datetime64(start.tz_convert("UTC").date(), "D"),
            np.datetime64(end.tz_convert("UTC").date(), "D"),
        )
    )


def profit_factor(values: pd.Series | np.ndarray) -> float:
    pnl = np.asarray(values, dtype=float)
    gain = float(pnl[pnl > 0.0].sum())
    loss = float(-pnl[pnl < 0.0].sum())
    if loss == 0.0:
        return float("inf") if gain > 0.0 else 0.0
    return gain / loss


def closed_drawdown(trades: pd.DataFrame) -> float:
    if trades.empty:
        return 0.0
    ordered = trades.sort_values(["exit_time", "trade_id"], kind="mergesort")
    equity = ordered["pnl_usd"].astype(float).cumsum()
    peak = equity.cummax().clip(lower=0.0)
    return float((peak - equity).max())


def enrich_actions(actions: pd.DataFrame) -> pd.DataFrame:
    required = {
        "signal_time",
        "entry_time",
        "exit_time",
        "event_id",
        "direction",
        "regime",
        "action_id",
        "h4_adx",
        "BREAK_AND_RUN",
        "DOWNSIDE_IMPULSE_RETEST",
        "OPENING_RANGE_REVERSAL",
        "stress_net_r",
        "risk_usd",
        "current_account_feasible",
    }
    missing = required - set(actions.columns)
    if missing:
        raise ValueError(f"Action columns missing: {sorted(missing)}")
    frame = actions.copy()
    for column in ("signal_time", "entry_time", "exit_time"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    frame["direction"] = frame["direction"].astype(str).str.upper()
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
    frame["h4adx"] = pd.cut(
        frame["h4_adx"],
        [-np.inf, 20.0, 30.0, np.inf],
        labels=["LOW", "MID", "HIGH"],
    ).astype(str)
    frame["pnl_usd"] = (
        frame["stress_net_r"].astype(float) * frame["risk_usd"].astype(float)
    )
    frame["trade_id"] = (
        "V61_"
        + frame["event_id"].astype(str)
        + "_"
        + frame["action_id"].astype(str)
    )
    return frame


def qualified_event_keys(candidates: pd.DataFrame) -> pd.MultiIndex:
    required = {"signal_time", "direction"}
    missing = required - set(candidates.columns)
    if missing:
        raise ValueError(f"V57 candidate columns missing: {sorted(missing)}")
    signal_time = pd.to_datetime(candidates["signal_time"], utc=True)
    direction = candidates["direction"].astype(str).str.upper()
    return pd.MultiIndex.from_arrays([signal_time, direction]).unique()


def filter_unused_candidates(
    actions: pd.DataFrame,
    excluded_keys: pd.MultiIndex,
    maximum_risk_usd: float,
) -> pd.DataFrame:
    keys = pd.MultiIndex.from_arrays([actions["signal_time"], actions["direction"]])
    mask = (
        actions["regime"].ne("UNSAFE_SHOCK")
        & actions["current_account_feasible"].astype(bool)
        & actions["risk_usd"].astype(float).le(float(maximum_risk_usd))
        & ~keys.isin(excluded_keys)
    )
    return actions.loc[mask].copy()


def _trailing(values: np.ndarray, counts: np.ndarray, window: int) -> dict[str, np.ndarray]:
    positive = np.concatenate(([0.0], np.cumsum(np.maximum(values, 0.0))))
    negative = np.concatenate(([0.0], np.cumsum(np.maximum(-values, 0.0))))
    net = np.concatenate(([0.0], np.cumsum(values)))
    lower = np.maximum(0, counts - int(window))
    gain = positive[counts] - positive[lower]
    loss = negative[counts] - negative[lower]
    trailing_net = net[counts] - net[lower]
    trailing_pf = np.divide(
        gain,
        loss,
        out=np.full(len(gain), np.inf),
        where=loss > 0.0,
    )
    return {
        "count": counts - lower,
        "net": trailing_net,
        "pf": trailing_pf,
        "mean": np.divide(
            trailing_net,
            counts - lower,
            out=np.zeros(len(trailing_net)),
            where=(counts - lower) > 0,
        ),
    }


def causal_state_health(
    actions: pd.DataFrame,
    state_columns: Iterable[str],
    short_window: int,
    long_window: int,
) -> pd.DataFrame:
    state = list(state_columns)
    missing = set(state) - set(actions.columns)
    if missing:
        raise ValueError(f"State columns missing: {sorted(missing)}")
    if short_window >= long_window:
        raise ValueError("Short window must be smaller than long window")
    pieces: list[pd.DataFrame] = []
    grouper: str | list[str] = state[0] if len(state) == 1 else state
    for _, group in actions.groupby(grouper, sort=False, observed=True, dropna=False):
        signals = group.sort_values(
            ["signal_time", "event_id", "action_id"], kind="mergesort"
        ).copy()
        completed = group.sort_values(
            ["exit_time", "event_id", "action_id"], kind="mergesort"
        )
        exit_ns = completed["exit_time"].astype("int64").to_numpy()
        signal_ns = signals["signal_time"].astype("int64").to_numpy()
        completed_count = np.searchsorted(exit_ns, signal_ns, side="left")
        outcomes = completed["stress_net_r"].astype(float).to_numpy()
        short = _trailing(outcomes, completed_count, short_window)
        long = _trailing(outcomes, completed_count, long_window)
        for prefix, values in (("short", short), ("long", long)):
            for metric, array in values.items():
                signals[f"{prefix}_{metric}"] = array
        signals["health_score"] = np.minimum(short["mean"], long["mean"])
        pieces.append(signals)
    result = pd.concat(pieces, ignore_index=True)
    return result.sort_values(
        ["signal_time", "event_id", "action_id"], kind="mergesort"
    ).reset_index(drop=True)


def eligible_actions(
    health: pd.DataFrame,
    excluded_keys: pd.MultiIndex,
    maximum_risk_usd: float,
    short_window: int,
    long_window: int,
    minimum_profit_factor: float,
) -> pd.DataFrame:
    candidates = filter_unused_candidates(health, excluded_keys, maximum_risk_usd)
    candidates = candidates.loc[
        candidates["short_count"].ge(int(short_window))
        & candidates["long_count"].ge(int(long_window))
        & candidates["short_pf"].ge(float(minimum_profit_factor))
        & candidates["long_pf"].ge(float(minimum_profit_factor))
        & candidates["short_net"].gt(0.0)
        & candidates["long_net"].gt(0.0)
    ].copy()
    ordered = candidates.sort_values(
        ["event_id", "health_score", "action_id"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    return ordered.drop_duplicates("event_id", keep="first").sort_values(
        ["entry_time", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def govern_new_lane(
    candidates: pd.DataFrame,
    frozen: pd.DataFrame,
    account: dict[str, Any],
) -> pd.DataFrame:
    frozen_exits = list(
        frozen.sort_values(["exit_time", "trade_id"], kind="mergesort")[
            ["exit_time", "pnl_usd"]
        ].itertuples(index=False, name=None)
    )
    frozen_index = 0
    new_exits: list[tuple[pd.Timestamp, str, float]] = []
    active: list[tuple[pd.Timestamp, float]] = []
    daily: dict[Any, int] = {}
    accepted: list[int] = []
    equity = 0.0
    peak = 0.0
    suspended = False
    ordered = candidates.sort_values(
        ["entry_time", "event_id", "action_id"], kind="mergesort"
    )
    for index, row in ordered.iterrows():
        exits: list[tuple[pd.Timestamp, float]] = []
        while (
            frozen_index < len(frozen_exits)
            and frozen_exits[frozen_index][0] <= row["entry_time"]
        ):
            exits.append(
                (frozen_exits[frozen_index][0], float(frozen_exits[frozen_index][1]))
            )
            frozen_index += 1
        while new_exits and new_exits[0][0] <= row["entry_time"]:
            exit_time, _, pnl = heapq.heappop(new_exits)
            exits.append((exit_time, pnl))
        for _, pnl in sorted(exits, key=lambda item: item[0]):
            equity += pnl
            peak = max(peak, equity)
            drawdown = peak - equity
            if not suspended and drawdown >= float(account["drawdown_suspend_usd"]):
                suspended = True
            elif suspended and drawdown <= float(account["drawdown_resume_usd"]):
                suspended = False
        active = [position for position in active if position[0] > row["entry_time"]]
        date = row["entry_time"].date()
        risk = float(row["risk_usd"])
        active_risk = float(sum(position[1] for position in active))
        if suspended:
            continue
        if len(active) >= int(account["maximum_new_open_positions"]):
            continue
        if active_risk + risk > float(
            account["maximum_new_concurrent_initial_risk_usd"]
        ):
            continue
        if daily.get(date, 0) >= int(account["maximum_new_entries_per_utc_date"]):
            continue
        accepted.append(index)
        active.append((row["exit_time"], risk))
        daily[date] = daily.get(date, 0) + 1
        heapq.heappush(
            new_exits,
            (row["exit_time"], str(row["trade_id"]), float(row["pnl_usd"])),
        )
    return ordered.loc[accepted].copy().reset_index(drop=True)


def window_metrics(
    trades: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    exit_cutoff: pd.Timestamp,
) -> dict[str, Any]:
    selected = trades.loc[
        trades["entry_time"].ge(start)
        & trades["entry_time"].lt(end)
        & trades["exit_time"].lt(exit_cutoff)
    ].copy()
    pnl = selected["pnl_usd"].astype(float)
    winners = pnl.nlargest(min(5, len(pnl))).index
    removed = pnl.drop(winners)
    return {
        "trades": int(len(selected)),
        "trades_per_weekday": float(len(selected) / business_days(start, end)),
        "net_usd": float(pnl.sum()),
        "profit_factor": profit_factor(pnl),
        "closed_drawdown_usd": closed_drawdown(selected),
        "top5_removed_net_usd": float(removed.sum()),
    }


def evaluate_policy(
    new_trades: pd.DataFrame,
    frozen: pd.DataFrame,
    windows: dict[str, list[str]],
    cutoff: pd.Timestamp,
) -> dict[str, dict[str, Any]]:
    combined = pd.concat(
        [frozen.assign(portfolio_source="FROZEN_V59"), new_trades.assign(portfolio_source="NEW_V61")],
        ignore_index=True,
        sort=False,
    )
    output: dict[str, dict[str, Any]] = {}
    for name, bounds in windows.items():
        start, end = (pd.Timestamp(value) for value in bounds)
        output[name] = {
            "new": window_metrics(new_trades, start, end, cutoff),
            "combined": window_metrics(combined, start, end, cutoff),
        }
    return output


def development_passes(
    metrics: dict[str, dict[str, Any]], gates: dict[str, Any]
) -> bool:
    for window_name, window_gates in gates.items():
        new = metrics[window_name]["new"]
        combined = metrics[window_name]["combined"]
        checks = [
            new["trades"] >= int(window_gates["minimum_new_trades"]),
            new["profit_factor"]
            >= float(window_gates["minimum_new_profit_factor"]),
            new["net_usd"] > float(window_gates["minimum_new_net_usd"]),
            new["top5_removed_net_usd"]
            > float(window_gates["minimum_new_top5_removed_net_usd"]),
            combined["profit_factor"]
            >= float(window_gates["minimum_combined_profit_factor"]),
            combined["closed_drawdown_usd"]
            <= float(window_gates["maximum_combined_closed_drawdown_usd"]),
        ]
        if "minimum_combined_trades_per_weekday" in window_gates:
            checks.append(
                combined["trades_per_weekday"]
                >= float(window_gates["minimum_combined_trades_per_weekday"])
            )
        if not all(checks):
            return False
    return True
