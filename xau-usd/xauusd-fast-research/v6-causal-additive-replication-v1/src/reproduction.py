from __future__ import annotations

import hashlib
import heapq
import importlib
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[4]
LANE_ROOT = Path(__file__).resolve().parents[1]
V59_CORE = "V59_BROKER_CORE"
V6_SLEEVE = "V6_CAUSAL_ADDITIVE"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_repo_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def resolve_external_root(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()


def verify_sources(config: Mapping[str, Any]) -> dict[str, str]:
    expected: list[tuple[str, Path, str]] = []
    package = config["external_package"]
    package_root = resolve_external_root(package["root"])
    for name, item in package["sources"].items():
        expected.append((f"external_package.{name}", package_root / item["path"], item["sha256"]))
    for name, item in config["external_data"].items():
        expected.append((f"external_data.{name}", Path(item["path"]), item["sha256"]))
    for name, item in config["canonical_v60"].items():
        expected.append((f"canonical_v60.{name}", resolve_repo_path(item["path"]), item["sha256"]))

    observed: dict[str, str] = {}
    for name, path, digest in expected:
        if not path.is_file():
            raise FileNotFoundError(f"Missing locked source: {name}: {path}")
        actual = sha256_file(path)
        if actual != digest:
            raise ValueError(f"Locked source drift: {name}: expected {digest}, got {actual}")
        observed[name] = actual
    return observed


def load_external_modules(config: Mapping[str, Any]) -> dict[str, Any]:
    source_dir = resolve_external_root(config["external_package"]["root"]) / "src"
    source_text = str(source_dir)
    if source_text not in sys.path:
        sys.path.insert(0, source_text)
    modules = {}
    for name in ("engine", "specialist", "v6_walkforward"):
        modules[name] = importlib.import_module(name)
    return modules


def profit_factor(values: pd.Series | np.ndarray) -> float:
    numeric = pd.Series(values, dtype=float)
    gains = float(numeric[numeric > 0.0].sum())
    losses = float(-numeric[numeric < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series | np.ndarray) -> float:
    equity = pd.Series(values, dtype=float).cumsum()
    if equity.empty:
        return 0.0
    return float((equity.cummax().clip(lower=0.0) - equity).max())


def dollar_selection_score(
    trades: pd.DataFrame, pf_weight: float = 20.0, pf_cap: float = 3.0
) -> tuple[float, dict[str, float]]:
    dollars = trades["rc"].astype(float) * trades["stop_usd"].astype(float)
    wr = 100.0 * float(dollars.gt(0.0).mean())
    pf = profit_factor(dollars)
    score = wr + pf_weight * min(pf, pf_cap)
    return score, {"n": int(len(dollars)), "win_rate_pct": wr, "profit_factor": pf}


def choose_annual_members(
    pool: Mapping[str, pd.DataFrame],
    year: int,
    minimum_prior_trades: int,
    members_per_year: int,
    pf_weight: float,
    pf_cap: float,
) -> tuple[list[str], list[dict[str, Any]]]:
    cutoff = pd.Timestamp(f"{year}-01-01", tz="UTC")
    scored: list[tuple[float, str, dict[str, float]]] = []
    for name, frame in pool.items():
        prior = frame.loc[
            frame["cap_exit_t"].notna() & frame["cap_exit_t"].lt(cutoff)
        ].copy()
        if len(prior) < minimum_prior_trades:
            continue
        score, metrics = dollar_selection_score(prior, pf_weight, pf_cap)
        scored.append((score, name, metrics))
    scored.sort(key=lambda row: (-row[0], row[1]))
    chosen = scored[:members_per_year]
    log = [
        {
            "rank": rank,
            "member": name,
            "selection_score": score,
            **metrics,
        }
        for rank, (score, name, metrics) in enumerate(chosen, start=1)
    ]
    return [name for _, name, _ in chosen], log


def deduplicate_by_prior_rank(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    ordered = trades.sort_values(
        ["i", "long", "pick_rank", "spec"], kind="mergesort"
    )
    return ordered.drop_duplicates(["i", "long"], keep="first").reset_index(drop=True)


def internal_capital_lock(trades: pd.DataFrame, maximum_open: int) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    ordered = trades.sort_values(
        ["entry_t", "pick_rank", "spec"], kind="mergesort"
    ).reset_index(drop=True)
    open_exits: list[pd.Timestamp] = []
    keep: list[int] = []
    for row in ordered.itertuples():
        while open_exits and open_exits[0] <= row.entry_t:
            heapq.heappop(open_exits)
        if len(open_exits) >= maximum_open:
            continue
        keep.append(row.Index)
        heapq.heappush(open_exits, row.cap_exit_t)
    return ordered.loc[keep].reset_index(drop=True)


def add_capital_outcomes(
    candidates: pd.DataFrame, context: Mapping[str, Any], fee_usd: float
) -> pd.DataFrame:
    frame = candidates.copy()
    market_time = context["t"].values.astype("datetime64[ns]")
    capital = context["cap"]
    capital_time = context["cap_t"]
    bid_low = capital["bid_low"].to_numpy(dtype=float)
    bid_close = capital["bid_close"].to_numpy(dtype=float)
    ask_open = capital["ask_open"].to_numpy(dtype=float)
    ask_high = capital["ask_high"].to_numpy(dtype=float)
    ask_close = capital["ask_close"].to_numpy(dtype=float)
    bid_open = capital["bid_open"].to_numpy(dtype=float)
    returns: list[float] = []
    exits: list[Any] = []
    fills: list[float] = []
    exit_prices: list[float] = []
    for row in frame.itertuples():
        horizon_end = market_time[int(row.i1) - 1]
        entry_time = market_time[int(row.j)]
        entry_index = int(np.searchsorted(capital_time, entry_time))
        if (
            entry_index >= len(capital_time)
            or capital_time[entry_index] != entry_time
        ):
            returns.append(np.nan)
            exits.append(pd.NaT)
            fills.append(np.nan)
            exit_prices.append(np.nan)
            continue
        end_index = max(
            int(np.searchsorted(capital_time, horizon_end, side="right")),
            entry_index + 1,
        )
        stop = float(row.stop)
        if bool(row.long):
            fill = ask_open[entry_index]
            stop_price = fill - stop
            hit = np.flatnonzero(bid_low[entry_index:end_index] <= stop_price)
            exit_index = entry_index + int(hit[0]) if len(hit) else end_index - 1
            exit_price = stop_price if len(hit) else bid_close[exit_index]
            net_r = (exit_price - fill) / stop - fee_usd / stop
        else:
            fill = bid_open[entry_index]
            stop_price = fill + stop
            hit = np.flatnonzero(ask_high[entry_index:end_index] >= stop_price)
            exit_index = entry_index + int(hit[0]) if len(hit) else end_index - 1
            exit_price = stop_price if len(hit) else ask_close[exit_index]
            net_r = (fill - exit_price) / stop - fee_usd / stop
        returns.append(float(net_r))
        exits.append(capital_time[exit_index])
        fills.append(float(fill))
        exit_prices.append(float(exit_price))
    frame["rc"] = returns
    frame["cap_exit_t"] = pd.to_datetime(exits, utc=True)
    frame["cap_entry_price"] = fills
    frame["cap_exit_price"] = exit_prices
    return frame


def build_variant_pool(modules: Mapping[str, Any]) -> dict[str, pd.DataFrame]:
    walk = modules["v6_walkforward"]
    context = modules["specialist"].load_context()
    fee_usd = float(modules["engine"].FEE)
    pool: dict[str, pd.DataFrame] = {}
    for side, session, regime in itertools.product(
        walk.SIDES, walk.SESSIONS, walk.REGIMES
    ):
        candidates = walk.enumerate_pool(side, session, regime)
        if candidates is None:
            continue
        for gate, macro, percentile in itertools.product(
            walk.GATES, walk.MACROS, walk.PCTS
        ):
            selected = walk.variant(candidates, gate, macro, percentile)
            if selected is None:
                continue
            name = (
                f"{side[:5]}_{session}_{regime}_"
                f"g{gate}_m{macro}_p{percentile}"
            )
            pool[name] = add_capital_outcomes(selected, context, fee_usd)
    if not pool:
        raise ValueError("External V6 pool produced no variants")
    return pool


def build_annual_candidates(
    pool: Mapping[str, pd.DataFrame],
    selection: Mapping[str, Any],
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    executions: list[pd.DataFrame] = []
    selection_log: list[dict[str, Any]] = []
    for year in range(int(selection["first_year"]), int(selection["last_year"]) + 1):
        chosen, log = choose_annual_members(
            pool,
            year,
            int(selection["minimum_prior_trades"]),
            int(selection["members_per_year"]),
            float(selection["score_pf_weight"]),
            float(selection["score_pf_cap"]),
        )
        selection_log.append({"year": year, "members": log})
        current: list[pd.DataFrame] = []
        for rank, name in enumerate(chosen, start=1):
            frame = pool[name]
            selected = frame.loc[frame["entry_t"].dt.year.eq(year)].copy()
            if selected.empty:
                continue
            selected["spec"] = name
            selected["pick_rank"] = rank
            selected["selection_year"] = year
            current.append(selected)
        if not current:
            continue
        selected = deduplicate_by_prior_rank(pd.concat(current, ignore_index=True))
        selected = selected.loc[
            selected["rc"].notna() & selected["cap_exit_t"].notna()
        ].copy()
        executions.append(selected)
    if not executions:
        raise ValueError("Annual chooser produced no executable Capital trades")
    combined = pd.concat(executions, ignore_index=True)
    combined = internal_capital_lock(
        combined, int(selection["internal_max_open_positions"])
    )
    return combined, selection_log


def prepare_candidate_ledger(
    executed: pd.DataFrame,
    stress: Mapping[str, Any],
) -> pd.DataFrame:
    frame = executed.copy()
    for column in ("entry_t", "cap_exit_t", "dec_time"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    entry_prices = frame["cap_entry_price"].to_numpy(dtype=float)
    if np.isnan(entry_prices).any():
        raise ValueError("Capital entry price missing for an executed candidate")
    risk = frame["stop_usd"].to_numpy(dtype=float)
    net_r = frame["rc"].to_numpy(dtype=float)
    base_fee = float(stress["base_fee_usd"])
    exit_prices = frame["cap_exit_price"].to_numpy(dtype=float)
    holding_days = (
        (frame["cap_exit_t"] - frame["entry_t"]).dt.total_seconds().to_numpy()
        / 86400.0
    )
    extra_cost = (
        float(stress["additional_fixed_cost_usd"])
        + float(stress["holding_cost_usd_per_24h"]) * holding_days
        + float(stress["slippage_r"]) * risk
    )
    result = frame.rename(
        columns={
            "entry_t": "entry_time",
            "cap_exit_t": "exit_time",
            "dec_time": "scan_time",
        }
    )
    result["signal_time"] = result["entry_time"] - pd.Timedelta(minutes=5)
    result["direction"] = np.where(result["long"], "LONG", "SHORT")
    result["entry_price"] = entry_prices
    result["exit_price"] = exit_prices
    result["risk_usd"] = risk
    result["net_r"] = net_r
    result["stress_net_r"] = net_r - extra_cost / risk
    result["pnl_usd"] = result["net_r"] * risk
    result["fee_stress_pnl_usd"] = result["stress_net_r"] * risk
    result["open_cost_usd"] = base_fee
    result["fee_stress_open_cost_usd"] = base_fee + extra_cost
    result["policy_id"] = result["spec"]
    result["mechanic"] = "V6_CONFIRMED_IMPULSE_ANNUAL_PRIOR_RANK"
    result["trade_id"] = (
        "V6_"
        + result["selection_year"].astype(str)
        + "_"
        + result["i"].astype(str)
        + "_"
        + result["direction"].str[0]
        + "_"
        + result["entry_time"].astype("int64").astype(str)
    )
    result["sleeve_id"] = V6_SLEEVE
    result["is_core"] = False
    if result.duplicated("trade_id").any():
        raise ValueError("Duplicate V6 trade ID after causal deduplication")
    if result["exit_time"].lt(result["entry_time"]).any():
        raise ValueError("V6 Capital exit precedes entry")
    direction_sign = np.where(result["direction"].eq("LONG"), 1.0, -1.0)
    endpoint = direction_sign * (
        result["exit_price"] - result["entry_price"]
    ) - result["fee_stress_open_cost_usd"]
    if not np.allclose(endpoint, result["fee_stress_pnl_usd"], atol=1e-9):
        raise ValueError("Candidate price/P&L reconciliation failed")
    return result.sort_values(["entry_time", "trade_id"], kind="mergesort").reset_index(
        drop=True
    )


def active_addons(ledger: pd.DataFrame, timestamp: pd.Timestamp) -> pd.DataFrame:
    return ledger.loc[
        ledger["entry_time"].le(timestamp) & ledger["exit_time"].gt(timestamp)
    ]


def drawdown_state_at(
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


def route_candidates(
    baseline: pd.DataFrame,
    candidates: pd.DataFrame,
    limits: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = baseline.copy()
    for column in ("entry_time", "exit_time"):
        base[column] = pd.to_datetime(base[column], utc=True)
    base_addons = base.loc[base["sleeve_id"].ne(V59_CORE)].copy()
    prepared = candidates.sort_values(
        ["entry_time", "pick_rank", "policy_id"], kind="mergesort"
    ).reset_index(drop=True)
    accepted_rows: list[pd.Series] = []
    decisions: list[dict[str, Any]] = []
    accepted_times: set[pd.Timestamp] = set()
    daily: dict[pd.Timestamp, int] = {}
    for order, row in enumerate(prepared.itertuples(index=False), start=1):
        entry = pd.Timestamp(row.entry_time)
        accepted_frame = (
            pd.DataFrame(accepted_rows)
            if accepted_rows
            else prepared.iloc[0:0].copy()
        )
        active = pd.concat(
            [active_addons(base_addons, entry), active_addons(accepted_frame, entry)],
            ignore_index=True,
        )
        concurrent_risk = float(active["risk_usd"].sum())
        closed_ledger = pd.concat([base, accepted_frame], ignore_index=True)
        drawdown, suspended = drawdown_state_at(
            closed_ledger,
            entry,
            float(limits["drawdown_suspend_usd"]),
            float(limits["drawdown_resume_usd"]),
        )
        day = entry.floor("D")
        reason = "ACCEPTED"
        if entry in accepted_times:
            reason = "DUPLICATE_CANDIDATE_ENTRY_TIME"
        elif suspended:
            reason = "ACCOUNT_DRAWDOWN_SUSPENDED"
        elif daily.get(day, 0) >= int(limits["maximum_candidate_entries_per_utc_date"]):
            reason = "MAXIMUM_CANDIDATE_ENTRIES_PER_UTC_DATE"
        elif len(active) >= int(limits["maximum_addon_open_positions"]):
            reason = "MAXIMUM_ADDON_OPEN_POSITIONS"
        elif concurrent_risk + float(row.risk_usd) > (
            float(limits["maximum_addon_concurrent_initial_risk_usd"]) + 1e-12
        ):
            reason = "MAXIMUM_ADDON_CONCURRENT_INITIAL_RISK_USD"
        accepted = reason == "ACCEPTED"
        decisions.append(
            {
                "routing_order": order,
                "trade_id": row.trade_id,
                "policy_id": row.policy_id,
                "entry_time": entry,
                "accepted": accepted,
                "reason": reason,
                "active_addons_before": int(len(active)),
                "active_addon_risk_before_usd": concurrent_risk,
                "candidate_risk_usd": float(row.risk_usd),
                "closed_drawdown_before_usd": drawdown,
                "drawdown_suspended": suspended,
            }
        )
        if accepted:
            accepted_rows.append(pd.Series(row._asdict()))
            accepted_times.add(entry)
            daily[day] = daily.get(day, 0) + 1
    accepted = (
        pd.DataFrame(accepted_rows).loc[:, prepared.columns]
        if accepted_rows
        else prepared.iloc[0:0].copy()
    )
    return accepted.reset_index(drop=True), pd.DataFrame(decisions)


def calendar_weekdays(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return len(
        pd.bdate_range(
            start.tz_localize(None).normalize(),
            (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).normalize(),
        )
    )


def daily_pnl_correlation(
    baseline: pd.DataFrame, addon: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> float:
    index = pd.bdate_range(
        start.tz_localize(None).normalize(),
        (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).normalize(),
        tz="UTC",
    )

    def totals(frame: pd.DataFrame) -> pd.Series:
        selected = frame.loc[
            frame["exit_time"].ge(start) & frame["exit_time"].lt(end)
        ]
        grouped = selected.groupby(selected["exit_time"].dt.floor("D"))[
            "fee_stress_pnl_usd"
        ].sum()
        return grouped.reindex(index, fill_value=0.0).astype(float)

    left, right = totals(baseline), totals(addon)
    if left.std(ddof=0) == 0.0 or right.std(ddof=0) == 0.0:
        return 0.0
    value = float(left.corr(right))
    return value if math.isfinite(value) else 0.0


def evaluate_windows(
    baseline: pd.DataFrame,
    addon: pd.DataFrame,
    windows: Mapping[str, list[str]],
    gates: Mapping[str, Any],
    limits: Mapping[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for name, bounds in windows.items():
        start, end = map(pd.Timestamp, bounds)
        base = baseline.loc[
            baseline["entry_time"].ge(start) & baseline["entry_time"].lt(end)
        ].copy()
        add = addon.loc[
            addon["entry_time"].ge(start) & addon["entry_time"].lt(end)
        ].copy()
        combined = pd.concat([base, add], ignore_index=True).sort_values(
            ["exit_time", "trade_id"], kind="mergesort"
        )
        base_values = base["fee_stress_pnl_usd"].astype(float)
        add_values = add["fee_stress_pnl_usd"].astype(float)
        combined_values = combined["fee_stress_pnl_usd"].astype(float)
        top = min(int(gates["top_candidate_winners_removed"]), len(add_values))
        removed = add_values.drop(add_values.nlargest(top).index)
        weekdays = calendar_weekdays(start, end)
        correlation = daily_pnl_correlation(baseline, addon, start, end)
        checks = {
            "minimum_candidate_trades": len(add) >= int(gates["minimum_candidate_trades"]),
            "minimum_candidate_stress_profit_factor": profit_factor(add_values)
            >= float(gates["minimum_candidate_stress_profit_factor"]),
            "minimum_candidate_stress_net_usd": float(add_values.sum())
            > float(gates["minimum_candidate_stress_net_usd"]),
            "minimum_winner_removed_stress_net_usd": float(removed.sum())
            > float(gates["minimum_winner_removed_stress_net_usd"]),
            "minimum_combined_stress_profit_factor": profit_factor(combined_values)
            >= float(gates["minimum_combined_stress_profit_factor"]),
            "minimum_combined_stress_net_usd": float(combined_values.sum())
            > float(gates["minimum_combined_stress_net_usd"]),
            "minimum_combined_trades_per_weekday": len(combined) / weekdays
            >= float(gates["minimum_combined_trades_per_weekday"]),
            "maximum_absolute_daily_pnl_correlation": abs(correlation)
            <= float(gates["maximum_absolute_daily_pnl_correlation"]),
            "maximum_combined_closed_drawdown_usd": closed_drawdown(combined_values)
            <= float(limits["maximum_combined_closed_drawdown_usd"]),
        }
        rows.append(
            {
                "window": name,
                "calendar_weekdays": weekdays,
                "baseline_trades": len(base),
                "candidate_trades": len(add),
                "combined_trades": len(combined),
                "baseline_stress_net_usd": float(base_values.sum()),
                "candidate_stress_net_usd": float(add_values.sum()),
                "combined_stress_net_usd": float(combined_values.sum()),
                "baseline_stress_profit_factor": profit_factor(base_values),
                "candidate_stress_profit_factor": profit_factor(add_values),
                "combined_stress_profit_factor": profit_factor(combined_values),
                "baseline_closed_drawdown_usd": closed_drawdown(base_values),
                "candidate_closed_drawdown_usd": closed_drawdown(add_values),
                "combined_closed_drawdown_usd": closed_drawdown(combined_values),
                "baseline_trades_per_weekday": len(base) / weekdays,
                "combined_trades_per_weekday": len(combined) / weekdays,
                "candidate_winner_removed_stress_net_usd": float(removed.sum()),
                "daily_pnl_correlation": correlation,
                "checks": checks,
                "passed": all(checks.values()),
            }
        )
    return pd.DataFrame(rows)


def annual_metrics(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, group in trades.groupby(trades["entry_time"].dt.year):
        values = group.sort_values(["exit_time", "trade_id"])[
            "fee_stress_pnl_usd"
        ].astype(float)
        rows.append(
            {
                "year": int(year),
                "trades": len(group),
                "win_rate_pct": 100.0 * float(values.gt(0.0).mean()),
                "stress_profit_factor": profit_factor(values),
                "stress_net_usd": float(values.sum()),
                "stress_closed_drawdown_usd": closed_drawdown(values),
            }
        )
    return pd.DataFrame(rows)
