from __future__ import annotations

import math
from typing import Any, Mapping

import pandas as pd


V59_CORE = "V59_BROKER_CORE"
V97_SLEEVE = "V97_CAUSAL_HOURLY_MODEL"


def profit_factor(values: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="raise").astype(float)
    gains = float(numeric.loc[numeric.gt(0.0)].sum())
    losses = float(-numeric.loc[numeric.lt(0.0)].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = pd.to_numeric(values, errors="raise").astype(float).cumsum()
    if equity.empty:
        return 0.0
    return float((equity.cummax().clip(lower=0.0) - equity).max())


def calendar_weekdays(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(
        len(
            pd.bdate_range(
                start.tz_localize(None).normalize(),
                (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).normalize(),
            )
        )
    )


def prepare_v97_ledger(trades: pd.DataFrame) -> pd.DataFrame:
    required = {
        "attempt_no",
        "policy_id",
        "mechanic",
        "signal_time",
        "entry_time",
        "exit_time",
        "direction",
        "entry_price",
        "exit_price",
        "risk_usd",
        "net_r",
        "stress_net_r",
    }
    missing = sorted(required.difference(trades.columns))
    if missing:
        raise ValueError(f"V97 trade ledger is missing columns: {missing}")
    result = trades.copy()
    for column in ("signal_time", "entry_time", "exit_time"):
        result[column] = pd.to_datetime(result[column], utc=True)
    numeric = (
        "entry_price",
        "exit_price",
        "risk_usd",
        "net_r",
        "stress_net_r",
    )
    for column in numeric:
        result[column] = pd.to_numeric(result[column], errors="raise")
    if result["risk_usd"].le(0.0).any():
        raise ValueError("V97 initial risk must be positive")
    if result["exit_time"].lt(result["entry_time"]).any():
        raise ValueError("V97 exit precedes entry")
    if not result["direction"].isin(("LONG", "SHORT")).all():
        raise ValueError("V97 direction is invalid")
    if result.duplicated(["policy_id", "entry_time"]).any():
        raise ValueError("Duplicate V97 policy entry")

    result["trade_id"] = (
        "V97_"
        + result["policy_id"].astype(str)
        + "_"
        + result["entry_time"].astype("int64").astype(str)
    )
    result["sleeve_id"] = V97_SLEEVE
    result["pnl_usd"] = result["net_r"] * result["risk_usd"]
    result["fee_stress_pnl_usd"] = result["stress_net_r"] * result["risk_usd"]
    result["open_cost_usd"] = 0.0
    result["fee_stress_open_cost_usd"] = (
        result["pnl_usd"] - result["fee_stress_pnl_usd"]
    )
    if result["fee_stress_open_cost_usd"].lt(-1e-9).any():
        raise ValueError("V97 stress cost creates a rebate")
    result["is_core"] = False
    return result.sort_values(
        ["entry_time", "attempt_no", "policy_id"], kind="mergesort"
    ).reset_index(drop=True)


def _active_addons(ledger: pd.DataFrame, timestamp: pd.Timestamp) -> pd.DataFrame:
    return ledger.loc[
        ledger["entry_time"].le(timestamp) & ledger["exit_time"].gt(timestamp)
    ]


def _drawdown_state_at(
    ledger: pd.DataFrame,
    timestamp: pd.Timestamp,
    suspend_usd: float,
    resume_usd: float,
) -> tuple[float, bool]:
    closed = ledger.loc[ledger["exit_time"].le(timestamp)].sort_values(
        ["exit_time", "trade_id"], kind="mergesort"
    )
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    suspended = False
    for pnl in closed["fee_stress_pnl_usd"].astype(float):
        equity += pnl
        peak = max(peak, equity)
        drawdown = peak - equity
        if suspended and drawdown <= resume_usd:
            suspended = False
        elif not suspended and drawdown >= suspend_usd:
            suspended = True
    return drawdown, suspended


def route_v97_candidates(
    v60_ledger: pd.DataFrame,
    candidates: pd.DataFrame,
    limits: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline = v60_ledger.copy()
    for column in ("entry_time", "exit_time"):
        baseline[column] = pd.to_datetime(baseline[column], utc=True)
    baseline["risk_usd"] = pd.to_numeric(baseline["risk_usd"], errors="raise")
    baseline["fee_stress_pnl_usd"] = pd.to_numeric(
        baseline["fee_stress_pnl_usd"], errors="raise"
    )
    baseline_addons = baseline.loc[baseline["sleeve_id"].ne(V59_CORE)].copy()
    prepared = prepare_v97_ledger(candidates)
    accepted_rows: list[pd.Series] = []
    decisions: list[dict[str, Any]] = []
    accepted_entry_times: set[pd.Timestamp] = set()
    accepted_daily: dict[pd.Timestamp, int] = {}
    maximum_positions = int(limits["maximum_addon_open_positions"])
    maximum_risk = float(limits["maximum_addon_concurrent_initial_risk_usd"])
    maximum_v97_daily = int(limits["maximum_v97_entries_per_utc_date"])
    drawdown_suspend = float(limits["drawdown_suspend_usd"])
    drawdown_resume = float(limits["drawdown_resume_usd"])

    for order, row in enumerate(prepared.itertuples(index=False), start=1):
        entry_time = pd.Timestamp(row.entry_time)
        day = entry_time.floor("D")
        reason = "ACCEPTED"
        accepted_frame = (
            pd.DataFrame(accepted_rows) if accepted_rows else prepared.iloc[0:0].copy()
        )
        active = pd.concat(
            [
                _active_addons(baseline_addons, entry_time),
                _active_addons(accepted_frame, entry_time),
            ],
            ignore_index=True,
        )
        concurrent_risk = float(active["risk_usd"].sum())
        closed_ledger = pd.concat([baseline, accepted_frame], ignore_index=True)
        account_drawdown, drawdown_suspended = _drawdown_state_at(
            closed_ledger, entry_time, drawdown_suspend, drawdown_resume
        )
        if entry_time in accepted_entry_times:
            reason = "DUPLICATE_V97_ENTRY_TIME"
        elif drawdown_suspended:
            reason = "ACCOUNT_DRAWDOWN_SUSPENDED"
        elif accepted_daily.get(day, 0) >= maximum_v97_daily:
            reason = "MAXIMUM_V97_ENTRIES_PER_UTC_DATE"
        elif len(active) >= maximum_positions:
            reason = "MAXIMUM_ADDON_OPEN_POSITIONS"
        elif concurrent_risk + float(row.risk_usd) > maximum_risk + 1e-12:
            reason = "MAXIMUM_ADDON_CONCURRENT_INITIAL_RISK_USD"

        accepted = reason == "ACCEPTED"
        decisions.append(
            {
                "routing_order": order,
                "trade_id": str(row.trade_id),
                "policy_id": str(row.policy_id),
                "mechanic": str(row.mechanic),
                "entry_time": entry_time,
                "accepted": accepted,
                "reason": reason,
                "active_addons_before": int(len(active)),
                "active_addon_risk_before_usd": concurrent_risk,
                "candidate_risk_usd": float(row.risk_usd),
                "closed_drawdown_before_usd": account_drawdown,
                "drawdown_suspended": drawdown_suspended,
            }
        )
        if accepted:
            accepted_rows.append(pd.Series(row._asdict()))
            accepted_entry_times.add(entry_time)
            accepted_daily[day] = accepted_daily.get(day, 0) + 1

    accepted = (
        pd.DataFrame(accepted_rows).loc[:, prepared.columns]
        if accepted_rows
        else prepared.iloc[0:0].copy()
    )
    return accepted.reset_index(drop=True), pd.DataFrame(decisions)


def daily_pnl_correlation(
    baseline: pd.DataFrame,
    addon: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> float:
    index = pd.bdate_range(
        start.tz_localize(None).normalize(),
        (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).normalize(),
        tz="UTC",
    )

    def totals(frame: pd.DataFrame, column: str) -> pd.Series:
        if frame.empty:
            return pd.Series(0.0, index=index)
        selected = frame.loc[
            frame["exit_time"].ge(start) & frame["exit_time"].lt(end)
        ].copy()
        grouped = selected.groupby(selected["exit_time"].dt.floor("D"))[column].sum()
        return grouped.reindex(index, fill_value=0.0).astype(float)

    left = totals(baseline, "fee_stress_pnl_usd")
    right = totals(addon, "fee_stress_pnl_usd")
    if left.std(ddof=0) == 0.0 or right.std(ddof=0) == 0.0:
        return 0.0
    value = float(left.corr(right))
    return value if math.isfinite(value) else 0.0


def shared_window_metrics(
    baseline: pd.DataFrame,
    addon: pd.DataFrame,
    windows: Mapping[str, list[str]],
    gates: Mapping[str, Mapping[str, Any]],
    shared: Mapping[str, Any],
) -> pd.DataFrame:
    base = baseline.copy()
    for column in ("entry_time", "exit_time"):
        base[column] = pd.to_datetime(base[column], utc=True)
    rows: list[dict[str, Any]] = []
    stage_by_window = {
        "development_2": "discovery",
        "confirmation": "confirmation",
        "final": "final",
    }
    for window, stage in stage_by_window.items():
        start, end = map(pd.Timestamp, windows[window])
        base_window = base.loc[
            base["entry_time"].ge(start) & base["entry_time"].lt(end)
        ].copy()
        addon_window = addon.loc[
            addon["entry_time"].ge(start) & addon["entry_time"].lt(end)
        ].copy()
        combined = pd.concat(
            [base_window, addon_window], ignore_index=True
        ).sort_values(["exit_time", "trade_id"], kind="mergesort")
        values = combined["fee_stress_pnl_usd"].astype(float)
        addon_values = addon_window["fee_stress_pnl_usd"].astype(float)
        top = int(gates[stage]["top_winners_removed"])
        removed = addon_values.drop(
            addon_values.nlargest(min(top, len(addon_values))).index
        )
        weekdays = calendar_weekdays(start, end)
        frequency = len(combined) / weekdays if weekdays else 0.0
        combined_pf = profit_factor(values)
        addon_pf = profit_factor(addon_values)
        correlation = daily_pnl_correlation(base, addon, start, end)
        checks = {
            "minimum_combined_trades_per_weekday": frequency
            >= float(shared["minimum_combined_trades_per_weekday"]),
            "minimum_combined_stress_pf": combined_pf
            >= float(shared["minimum_combined_stress_pf"]),
            "combined_stress_net_positive": float(values.sum()) > 0.0,
            "minimum_v97_stress_pf": addon_pf
            >= float(gates[stage]["minimum_stress_pf"]),
            "v97_winner_removed_positive": float(removed.sum()) > 0.0,
            "maximum_absolute_daily_pnl_correlation": abs(correlation)
            <= float(shared["maximum_absolute_daily_pnl_correlation"]),
        }
        rows.append(
            {
                "window": window,
                "stage_gate": stage,
                "calendar_weekdays": weekdays,
                "baseline_trades": int(len(base_window)),
                "v97_accepted_trades": int(len(addon_window)),
                "combined_trades": int(len(combined)),
                "combined_trades_per_weekday": frequency,
                "combined_stress_net_usd": float(values.sum()),
                "combined_stress_pf": combined_pf,
                "combined_closed_drawdown_usd": closed_drawdown(values),
                "v97_stress_net_usd": float(addon_values.sum()),
                "v97_stress_pf": addon_pf,
                "v97_winner_removed_stress_net_usd": float(removed.sum()),
                "daily_pnl_correlation": correlation,
                "checks": checks,
                "passed": bool(all(checks.values())),
            }
        )
    return pd.DataFrame(rows)


def post_route_limit_checks(
    floating_curve: pd.DataFrame, shared: Mapping[str, Any]
) -> dict[str, bool]:
    maximum_positions = int(floating_curve["open_addons"].max())
    maximum_risk = float(floating_curve["addon_initial_risk_usd"].max())
    return {
        "maximum_addon_open_positions": maximum_positions
        <= int(shared["maximum_addon_open_positions"]),
        "maximum_addon_concurrent_initial_risk_usd": maximum_risk
        <= float(shared["maximum_addon_concurrent_initial_risk_usd"]) + 1e-9,
    }
