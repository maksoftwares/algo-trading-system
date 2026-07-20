from __future__ import annotations

import hashlib
import heapq
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_sources(repo_root: Path, sources: Mapping[str, Any]) -> dict[str, str]:
    verified: dict[str, str] = {}
    for source_id, record in sources.items():
        path = repo_root / str(record["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        observed = sha256_file(path)
        if observed != str(record["sha256"]):
            raise ValueError(f"Source hash mismatch for {source_id}: {observed}")
        verified[source_id] = observed
    return verified


def _close(observed: float, expected: float) -> bool:
    return bool(np.isclose(observed, expected, rtol=0.0, atol=1e-8))


def _validate_native_controls(native: pd.DataFrame, settings: Mapping[str, Any]) -> None:
    if len(native) != int(settings["expected_rows"]):
        raise ValueError(f"Native R1 row count changed: {len(native)}")
    if native["trade_id"].astype(str).duplicated().any():
        raise ValueError("Native R1 trade IDs are not unique")
    if not native["evidence_status"].eq(settings["expected_evidence_status"]).all():
        raise ValueError("Native R1 contains invalid reconciliation evidence")
    expected_fee = bool(settings["expected_fee_evidence_complete"])
    observed_fee = native["native_fee_evidence_complete"].astype(bool)
    if not observed_fee.eq(expected_fee).all():
        raise ValueError("Native R1 fee-evidence state changed")
    if not native["direction"].astype(str).str.upper().eq("LONG").all():
        raise ValueError("Native R1 contains a non-long trade")
    if not np.isclose(
        pd.to_numeric(native["native_entry_volume"], errors="raise"), 0.01
    ).all():
        raise ValueError("Native R1 contains a non-0.01 entry volume")
    for source_id, control in settings["source_controls"].items():
        rows = native.loc[native["source_id"].eq(source_id)]
        if len(rows) != int(control["expected_rows"]):
            raise ValueError(f"Native R1 source count changed for {source_id}")
        if not _close(
            float(rows["native_pnl_usd"].sum()),
            float(control["expected_pnl_usd"]),
        ):
            raise ValueError(f"Native R1 source P/L changed for {source_id}")
    if not _close(
        float(native["native_pnl_usd"].sum()),
        float(settings["expected_total_pnl_usd"]),
    ):
        raise ValueError("Native R1 total P/L changed")


def apply_single_position_policy(
    core: pd.DataFrame, policy: Mapping[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_mask = core["specialist_id"].eq(policy["target_specialist_id"]) & core[
        "source_strategy"
    ].eq(policy["target_source_strategy"])
    target = core.loc[target_mask].sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    )
    active: list[pd.Timestamp] = []
    daily: dict[Any, int] = {}
    accepted: set[str] = set()
    decisions: list[dict[str, Any]] = []
    for row in target.itertuples(index=False):
        entry = pd.Timestamp(row.entry_time)
        active = [exit_time for exit_time in active if exit_time > entry]
        date = entry.date()
        if len(active) >= int(policy["maximum_concurrent_positions"]):
            reason = "MAXIMUM_CONCURRENT_POSITIONS"
        elif daily.get(date, 0) >= int(policy["maximum_entries_per_utc_day"]):
            reason = "MAXIMUM_ENTRIES_PER_UTC_DAY"
        else:
            reason = "ACCEPTED"
        decisions.append(
            {
                "policy_id": str(policy["policy_id"]),
                "trade_id": str(row.trade_id),
                "native_trade_id": str(row.native_trade_id),
                "entry_time": entry,
                "exit_time": pd.Timestamp(row.exit_time),
                "pnl_usd": float(row.pnl_usd),
                "accepted": reason == "ACCEPTED",
                "decision_reason": reason,
                "active_before_decision": len(active),
                "entries_on_day_before_decision": daily.get(date, 0),
            }
        )
        if reason != "ACCEPTED":
            continue
        accepted.add(str(row.trade_id))
        active.append(pd.Timestamp(row.exit_time))
        daily[date] = daily.get(date, 0) + 1
    kept = core.loc[
        ~target_mask | core["trade_id"].astype(str).isin(accepted)
    ].copy()
    return (
        kept.sort_values(["entry_time", "trade_id"], kind="mergesort").reset_index(
            drop=True
        ),
        pd.DataFrame(decisions),
    )


def build_native_core(
    normalized: pd.DataFrame,
    reconciliation: pd.DataFrame,
    native_settings: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    core = normalized.copy()
    for column in ("entry_time_utc", "exit_time_utc"):
        core[column] = pd.to_datetime(core[column], utc=True, errors="raise")
    if core["trade_id"].astype(str).duplicated().any():
        raise ValueError("Normalized Core trade IDs are not unique")

    source_ids = set(native_settings["source_controls"])
    native = reconciliation.loc[reconciliation["source_id"].isin(source_ids)].copy()
    _validate_native_controls(native, native_settings)
    native["native_entry_time_utc"] = pd.to_datetime(
        native["native_entry_time"], utc=True, errors="raise"
    )
    native["native_exit_time_utc"] = pd.to_datetime(
        native["native_exit_time"], utc=True, errors="raise"
    )
    if native.duplicated(["source_id", "native_entry_time_utc"]).any():
        raise ValueError("Native R1 source/entry key is not unique")

    r1_mask = core["specialist_id"].eq(native_settings["specialist_id"])
    r1 = core.loc[r1_mask].copy()
    if set(r1["source_strategy"].astype(str)) != source_ids:
        raise ValueError("Normalized R1 source membership changed")
    joined = r1.merge(
        native,
        left_on=["source_strategy", "entry_time_utc"],
        right_on=["source_id", "native_entry_time_utc"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_native"),
    )
    if joined["native_trade_id" if "native_trade_id" in joined else "trade_id_native"].isna().any():
        raise ValueError("A normalized R1 row has no native-position match")
    native_id_column = "native_trade_id" if "native_trade_id" in joined else "trade_id_native"
    if not np.isclose(
        joined.groupby("source_strategy")["pnl_usd_0p01_equiv"].sum().sort_index(),
        joined.groupby("source_strategy")["native_pnl_usd"].sum().sort_index(),
        rtol=0.0,
        atol=1e-8,
    ).all():
        raise ValueError("Native repair changed an R1 source aggregate")

    corrected_r1 = r1.copy().reset_index(drop=True)
    joined = joined.reset_index(drop=True)
    corrected_r1["entry_time_utc"] = joined["native_entry_time_utc"]
    corrected_r1["exit_time_utc"] = joined["native_exit_time_utc"]
    corrected_r1["pnl_usd_0p01_equiv"] = joined["native_pnl_usd"].astype(float)
    corrected_r1["pnl_basis"] = "EXACT_MT5_NATIVE_POSITION_PNL_FEE_INCOMPLETE"
    corrected_r1["entry_price"] = joined["native_entry_price"].astype(float)
    corrected_r1["exit_price"] = joined["native_exit_price"].astype(float)
    corrected_r1["volume"] = joined["native_entry_volume"].astype(float)
    corrected_r1["native_trade_id"] = joined[native_id_column].astype(str)
    corrected_r1["price_source"] = "MT5_NATIVE_POSITION"

    non_r1 = core.loc[~r1_mask].copy()
    non_r1["entry_price"] = np.nan
    non_r1["exit_price"] = np.nan
    non_r1["volume"] = 0.01
    non_r1["native_trade_id"] = ""
    non_r1["price_source"] = "UPSTREAM_RAW_TICK_LEDGER"
    corrected = pd.concat([non_r1, corrected_r1], ignore_index=True)
    corrected["entry_time"] = corrected["entry_time_utc"]
    corrected["exit_time"] = corrected["exit_time_utc"]
    corrected["signal_time"] = corrected["entry_time"]
    corrected["pnl_usd"] = corrected["pnl_usd_0p01_equiv"].astype(float)
    corrected["sleeve_id"] = "V58_NATIVE_CORE"
    corrected["risk_usd"] = pd.to_numeric(corrected["risk_usd"], errors="coerce")
    corrected, decisions = apply_single_position_policy(corrected, policy)
    audit = {
        "native_r1_rows": int(len(native)),
        "legacy_exit_deal_mismatches": int(
            native["legacy_exit_deal_mismatch"].astype(bool).sum()
        ),
        "legacy_pnl_mismatches": int(native["legacy_pnl_mismatch"].astype(bool).sum()),
        "native_r1_total_pnl_usd_before_cap": float(native["native_pnl_usd"].sum()),
        "target_rows_before_cap": int(len(decisions)),
        "target_rows_after_cap": int(decisions["accepted"].astype(bool).sum()),
        "target_pnl_usd_after_cap": float(
            decisions.loc[decisions["accepted"].astype(bool), "pnl_usd"].sum()
        ),
        "fee_evidence_complete": bool(
            native["native_fee_evidence_complete"].astype(bool).all()
        ),
    }
    return corrected, decisions, audit


def govern_addons(
    candidates: pd.DataFrame,
    core: pd.DataFrame,
    account: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = candidates.copy()
    for column in ("signal_time", "entry_time", "exit_time"):
        candidates[column] = pd.to_datetime(candidates[column], utc=True, errors="raise")
    if candidates["trade_id"].astype(str).duplicated().any():
        raise ValueError("V57 candidate trade IDs are not unique")
    candidates = candidates.sort_values(
        ["entry_time", "trade_id"], kind="mergesort"
    ).reset_index(drop=True)
    core_exits = list(
        core.sort_values(["exit_time", "trade_id"], kind="mergesort")[[
            "exit_time",
            "pnl_usd",
        ]].itertuples(index=False, name=None)
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
        while core_index < len(core_exits) and core_exits[core_index][0] <= row["entry_time"]:
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
                "trade_id": str(row["trade_id"]),
                "sleeve_id": str(row["sleeve_id"]),
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
    return candidates.loc[accepted].copy().reset_index(drop=True), pd.DataFrame(decisions)


def profit_factor(values: pd.Series) -> float:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


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
        selected.assign(month=selected["entry_time"].dt.tz_localize(None).dt.to_period("M"))
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
    return (
        pd.concat([core[columns], addons[columns]], ignore_index=True)
        .sort_values(["entry_time", "trade_id"], kind="mergesort")
        .reset_index(drop=True)
    )


def rows_for_windows(
    core: pd.DataFrame,
    addons: pd.DataFrame,
    combined: pd.DataFrame,
    windows: Mapping[str, Iterable[str]],
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


def evaluate_gates(metrics: pd.DataFrame, config: Mapping[str, Any]) -> dict[str, Any]:
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
        checks[f"{window}_addon_winner_removed"] = addon["winner_removed_net_usd"] > float(
            gates["minimum_winner_removed_net_usd"]
        )
        checks[f"{window}_combined_pf"] = combined["profit_factor"] >= float(
            gates["minimum_combined_profit_factor"]
        )
        checks[f"{window}_combined_net"] = combined["net_usd"] > float(
            gates["minimum_combined_net_usd"]
        )
        checks[f"{window}_combined_winner_removed"] = combined[
            "winner_removed_net_usd"
        ] > float(gates["minimum_winner_removed_net_usd"])
        checks[f"{window}_combined_drawdown"] = combined["closed_drawdown_usd"] <= float(
            account["maximum_combined_closed_drawdown_usd"]
        )
    final_addon = metrics.loc[
        metrics["window"].eq("final") & metrics["portfolio_id"].eq("ADDON")
    ].iloc[0]
    final_combined = metrics.loc[
        metrics["window"].eq("final") & metrics["portfolio_id"].eq("COMBINED")
    ].iloc[0]
    checks["final_addon_drawdown"] = final_addon["closed_drawdown_usd"] <= float(
        account["maximum_final_addon_closed_drawdown_usd"]
    )
    checks["final_positive_month_share"] = final_combined["positive_month_share"] >= float(
        gates["minimum_final_combined_positive_month_share"]
    )
    return {"checks": checks, "passed": bool(all(checks.values()))}
