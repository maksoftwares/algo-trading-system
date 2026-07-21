from __future__ import annotations

import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent
BREAK_FAMILY = "SPOT_RETIRED_CLOCKS__SPOT_BREAK_AND_RUN"
RETEST_FAMILY = "SPOT_RETIRED_CLOCKS__SPOT_DOWNSIDE_IMPULSE_RETEST"
POOLS: tuple[dict[str, Any], ...] = (
    {"pool_id": "BREAK_60", "families": (BREAK_FAMILY,), "horizon_minutes": 60},
    {"pool_id": "BREAK_180", "families": (BREAK_FAMILY,), "horizon_minutes": 180},
    {"pool_id": "RETEST_60", "families": (RETEST_FAMILY,), "horizon_minutes": 60},
    {"pool_id": "RETEST_180", "families": (RETEST_FAMILY,), "horizon_minutes": 180},
    {
        "pool_id": "MIXED_60",
        "families": (BREAK_FAMILY, RETEST_FAMILY),
        "horizon_minutes": 60,
    },
)
POOL_BY_ID = {str(item["pool_id"]): item for item in POOLS}
SOURCE_COLUMNS = (
    "event_id",
    "source_id",
    "family_id",
    "signal_time",
    "entry_time",
    "entry_atr",
    "entry_spread_atr",
    "exit_time",
    "horizon_minutes",
    "direction_mode",
    "direction",
    "mid_pnl_usd",
    "side_pnl_before_fees_usd",
    "venue_pnl_usd",
    "stress_pnl_usd",
    "episode_id",
)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V89 = _load_module(
    "causal_health_gated_event_sleeves_v100_metrics",
    RESEARCH_ROOT / "cboe-gvz-routed-intraday-v89" / "src" / "campaign.py",
)
summarize = V89.summarize
benjamini_hochberg = V89.benjamini_hochberg
select_advancers = V89.select_advancers


def resolve(path: str) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _pool_frame(frame: pd.DataFrame, pool_id: str) -> pd.DataFrame:
    spec = POOL_BY_ID[pool_id]
    return frame.loc[
        frame["family_id"].isin(spec["families"])
        & frame["horizon_minutes"].eq(int(spec["horizon_minutes"]))
    ].sort_values(["entry_time", "family_id", "event_id"], kind="mergesort")


def load_source(config: Mapping[str, Any], outcomes: bool = True) -> pd.DataFrame:
    columns: Iterable[str]
    if outcomes:
        columns = SOURCE_COLUMNS
    else:
        columns = (
            "event_id",
            "family_id",
            "signal_time",
            "entry_time",
            "exit_time",
            "horizon_minutes",
            "direction_mode",
            "direction",
            "episode_id",
        )
    path = resolve(str(config["source"]["episode_markouts"]["path"]))
    frame = pd.read_parquet(path, columns=list(columns))
    for column in ("signal_time", "entry_time", "exit_time"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    eligible_families = (BREAK_FAMILY, RETEST_FAMILY)
    frame = frame.loc[
        frame["family_id"].isin(eligible_families)
        & frame["horizon_minutes"].isin((60, 180))
        & frame["direction_mode"].eq(config["policy_grid"]["direction_mode"])
    ].copy()
    if frame.duplicated(["event_id", "horizon_minutes", "direction_mode"]).any():
        raise ValueError("V100 source contains duplicate episode actions")
    if outcomes:
        frame["entry_atr"] = pd.to_numeric(frame["entry_atr"], errors="raise")
        if frame["entry_atr"].le(0.0).any():
            raise ValueError("V100 source contains nonpositive ATR")
        frame["risk_usd"] = frame["entry_atr"] * float(
            config["execution"]["ounces_at_0p01_lot"]
        )
        frame["net_r"] = frame["venue_pnl_usd"] / frame["risk_usd"]
        frame["stress_net_r"] = frame["stress_pnl_usd"] / frame["risk_usd"]
        frame["direction"] = np.where(frame["direction"].astype(int).gt(0), "LONG", "SHORT")
        frame["current_account_feasible"] = True
    return frame.sort_values(
        ["entry_time", "family_id", "horizon_minutes", "event_id"],
        kind="mergesort",
    ).reset_index(drop=True)


def parameter_space(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    grid = config["policy_grid"]
    return [
        {
            "pool_id": str(pool["pool_id"]),
            "anchor_hour_utc": int(anchor),
            "window_hours": int(grid["window_hours"]),
            "health_lookback": int(lookback),
            "minimum_health_pf": float(minimum_pf),
            "cooldown_calendar_days": int(cooldown),
        }
        for pool, anchor, lookback, minimum_pf, cooldown in product(
            POOLS,
            grid["anchor_hours_utc"],
            grid["health_lookback_completed_events"],
            grid["minimum_health_profit_factors"],
            grid["cooldown_calendar_days"],
        )
    ]


def generate_manifest(
    frame: pd.DataFrame,
    config: Mapping[str, Any],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    controls = config["research_controls"]
    first = int(controls["attempt_first"])
    rows: list[dict[str, Any]] = []
    for offset, params in enumerate(parameter_space(config)):
        parameters_json = json.dumps(params, sort_keys=True, separators=(",", ":"))
        pool = _pool_frame(frame, str(params["pool_id"]))
        raw = pool.loc[pool["entry_time"].ge(start) & pool["entry_time"].lt(end)]
        rows.append(
            {
                "attempt_no": first + offset,
                "policy_id": "V100_" + _sha256_text(parameters_json)[:20],
                "mechanic": str(params["pool_id"]),
                "parameters_json": parameters_json,
                "raw_discovery_signal_count": int(len(raw)),
            }
        )
    manifest = pd.DataFrame(rows)
    if manifest["policy_id"].duplicated().any():
        raise ValueError("V100 generated duplicate policy identifiers")
    return manifest


def causal_health_frame(
    pool: pd.DataFrame,
    lookback: int,
    minimum_pf: float,
    cooldown_days: int,
) -> pd.DataFrame:
    if lookback <= 0 or cooldown_days < 0:
        raise ValueError("Invalid V100 health policy")
    candidates = pool.sort_values(
        ["entry_time", "family_id", "event_id"], kind="mergesort"
    ).copy()
    completed = pool.sort_values(
        ["exit_time", "family_id", "event_id"], kind="mergesort"
    )
    exits = completed["exit_time"].to_numpy(dtype="datetime64[ns]")
    entries = candidates["entry_time"].to_numpy(dtype="datetime64[ns]")
    end = np.searchsorted(exits, entries, side="left")
    begin = np.maximum(end - lookback, 0)
    values = completed["stress_net_r"].to_numpy(dtype=float)
    gains = np.where(values > 0.0, values, 0.0)
    losses = np.where(values < 0.0, -values, 0.0)
    gain_prefix = np.concatenate(([0.0], np.cumsum(gains)))
    loss_prefix = np.concatenate(([0.0], np.cumsum(losses)))
    rolling_gains = gain_prefix[end] - gain_prefix[begin]
    rolling_losses = loss_prefix[end] - loss_prefix[begin]
    pf = np.divide(
        rolling_gains,
        rolling_losses,
        out=np.full(len(candidates), np.inf),
        where=rolling_losses > 0.0,
    )
    count = end - begin
    raw_ok = (count >= lookback) & (pf >= minimum_pf)
    active = np.zeros(len(candidates), dtype=bool)
    paused_until: pd.Timestamp | None = None
    for index, (entry, healthy) in enumerate(
        zip(candidates["entry_time"], raw_ok, strict=True)
    ):
        timestamp = pd.Timestamp(entry)
        if paused_until is not None and timestamp < paused_until:
            continue
        if bool(healthy):
            active[index] = True
            paused_until = None
        else:
            paused_until = timestamp + pd.Timedelta(days=cooldown_days)
    candidates["health_completed_events"] = count
    candidates["health_profit_factor"] = pf
    candidates["health_raw_pass"] = raw_ok
    candidates["health_active"] = active
    return candidates


def route_schedule(
    health: pd.DataFrame,
    params: Mapping[str, Any],
    config: Mapping[str, Any],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    grid = config["policy_grid"]
    anchor = int(params["anchor_hour_utc"])
    stop_hour = anchor + int(params["window_hours"])
    eligible = health.loc[
        health["health_active"]
        & health["entry_time"].ge(start)
        & health["entry_time"].lt(end)
        & health["entry_time"].dt.hour.ge(anchor)
        & health["entry_time"].dt.hour.lt(stop_hour)
        & health["entry_spread_atr"].le(float(grid["maximum_entry_spread_atr"]))
    ].sort_values(["entry_time", "family_id", "event_id"], kind="mergesort")
    maximum_daily = int(grid["maximum_entries_per_utc_date"])
    maximum_family_daily = int(grid["maximum_entries_per_family_per_utc_date"])
    maximum_open = int(grid["maximum_open_positions"])
    daily: dict[Any, int] = {}
    family_daily: dict[tuple[Any, str], int] = {}
    open_until: list[pd.Timestamp] = []
    entry_times: set[pd.Timestamp] = set()
    selected: list[dict[str, Any]] = []
    for row in eligible.to_dict(orient="records"):
        entry = pd.Timestamp(row["entry_time"])
        day = entry.date()
        family = str(row["family_id"])
        open_until = [value for value in open_until if value > entry]
        if entry in entry_times or len(open_until) >= maximum_open:
            continue
        if daily.get(day, 0) >= maximum_daily:
            continue
        if family_daily.get((day, family), 0) >= maximum_family_daily:
            continue
        selected.append(row)
        entry_times.add(entry)
        open_until.append(pd.Timestamp(row["exit_time"]))
        daily[day] = daily.get(day, 0) + 1
        family_daily[(day, family)] = family_daily.get((day, family), 0) + 1
    if not selected:
        return eligible.iloc[0:0].copy()
    return pd.DataFrame(selected).sort_values("entry_time", kind="mergesort").reset_index(
        drop=True
    )


def _gate_checks(row: Mapping[str, Any], gate: Mapping[str, Any]) -> dict[str, bool]:
    return V89.gate_checks(row, gate)


def evaluate_policies(
    frame: pd.DataFrame,
    manifest: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    start, end = map(pd.Timestamp, config["windows"][stage])
    pool_cache = {pool_id: _pool_frame(frame, pool_id) for pool_id in POOL_BY_ID}
    health_cache: dict[tuple[str, int, float, int], pd.DataFrame] = {}
    ledger_cache: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    for policy in manifest.itertuples(index=False):
        params = json.loads(policy.parameters_json)
        key = (
            str(params["pool_id"]),
            int(params["health_lookback"]),
            float(params["minimum_health_pf"]),
            int(params["cooldown_calendar_days"]),
        )
        if key not in health_cache:
            health_cache[key] = causal_health_frame(
                pool_cache[key[0]], key[1], key[2], key[3]
            )
        trades = route_schedule(health_cache[key], params, config, start, end)
        if not trades.empty:
            trades = trades.assign(
                attempt_no=int(policy.attempt_no),
                policy_id=str(policy.policy_id),
                mechanic=str(policy.mechanic),
                anchor_hour_utc=int(params["anchor_hour_utc"]),
                health_lookback=int(params["health_lookback"]),
                minimum_health_pf=float(params["minimum_health_pf"]),
                cooldown_calendar_days=int(params["cooldown_calendar_days"]),
            )
        ledger_cache[str(policy.policy_id)] = trades
        rows.append(
            {
                "attempt_no": int(policy.attempt_no),
                "policy_id": str(policy.policy_id),
                "mechanic": str(policy.mechanic),
                "parameters_json": str(policy.parameters_json),
                **summarize(
                    trades,
                    start,
                    end,
                    config["segments"][stage],
                    int(config["gates"][stage]["top_winners_removed"]),
                ),
            }
        )
    metrics = pd.DataFrame(rows).sort_values("attempt_no", kind="mergesort").reset_index(
        drop=True
    )
    metrics["fdr_qvalue"] = benjamini_hochberg(metrics["block_pvalue"])
    checks: list[dict[str, bool]] = []
    passes: list[bool] = []
    for row in metrics.to_dict(orient="records"):
        values = _gate_checks(row, config["gates"][stage])
        checks.append(values)
        passes.append(all(values.values()))
    metrics["gate_checks_json"] = [
        json.dumps(value, sort_keys=True, separators=(",", ":")) for value in checks
    ]
    metrics["gate_pass"] = passes
    return metrics, ledger_cache


def add_execution_prices(
    trades: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    market_source = config["source"]["market"]
    market = pd.read_parquet(
        resolve(str(market_source["path"])),
        columns=["timestamp_ms", "bid_open", "bid_close", "ask_open", "ask_close"],
    )
    market["bar_start_utc"] = pd.to_datetime(market["timestamp_ms"], unit="ms", utc=True)
    market = market.set_index("bar_start_utc", verify_integrity=True)
    result = trades.copy()
    entry_rows = market.reindex(result["entry_time"].tolist())
    exit_starts = result["exit_time"] - pd.Timedelta(minutes=5)
    exit_rows = market.reindex(exit_starts.tolist())
    if entry_rows[["bid_open", "ask_open"]].isna().any().any():
        raise ValueError("V100 entry price reconstruction failed")
    if exit_rows[["bid_close", "ask_close"]].isna().any().any():
        raise ValueError("V100 exit price reconstruction failed")
    long_mask = result["direction"].eq("LONG").to_numpy()
    entry_price = np.where(
        long_mask,
        entry_rows["ask_open"].to_numpy(dtype=float),
        entry_rows["bid_open"].to_numpy(dtype=float),
    )
    exit_price = np.where(
        long_mask,
        exit_rows["bid_close"].to_numpy(dtype=float),
        exit_rows["ask_close"].to_numpy(dtype=float),
    )
    side = np.where(long_mask, exit_price - entry_price, entry_price - exit_price)
    ounces = float(config["execution"]["ounces_at_0p01_lot"])
    if not np.allclose(
        side * ounces,
        result["side_pnl_before_fees_usd"].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-8,
    ):
        raise ValueError("V100 side-price P&L does not reconcile")
    result["entry_price"] = entry_price
    result["exit_price"] = exit_price
    return result


def selected_trade_ledger(
    selected_manifest: pd.DataFrame,
    config: Mapping[str, Any],
    cache: dict[str, pd.DataFrame],
    stage: str,
) -> pd.DataFrame:
    if selected_manifest.empty:
        return pd.DataFrame()
    frames = [
        cache[str(policy_id)]
        for policy_id in selected_manifest["policy_id"].astype(str)
        if str(policy_id) in cache and not cache[str(policy_id)].empty
    ]
    if not frames:
        return pd.DataFrame()
    result = pd.concat(frames, ignore_index=True).assign(stage=stage)
    result = add_execution_prices(result, config)
    keep = [
        "attempt_no",
        "policy_id",
        "mechanic",
        "stage",
        "anchor_hour_utc",
        "health_lookback",
        "minimum_health_pf",
        "cooldown_calendar_days",
        "event_id",
        "episode_id",
        "family_id",
        "signal_time",
        "entry_time",
        "exit_time",
        "direction",
        "entry_price",
        "exit_price",
        "entry_atr",
        "entry_spread_atr",
        "risk_usd",
        "mid_pnl_usd",
        "side_pnl_before_fees_usd",
        "venue_pnl_usd",
        "stress_pnl_usd",
        "net_r",
        "stress_net_r",
        "health_completed_events",
        "health_profit_factor",
        "current_account_feasible",
    ]
    return result.loc[:, keep].sort_values(
        ["entry_time", "attempt_no"], kind="mergesort"
    ).reset_index(drop=True)


__all__ = [
    "POOLS",
    "POOL_BY_ID",
    "load_source",
    "parameter_space",
    "generate_manifest",
    "causal_health_frame",
    "route_schedule",
    "evaluate_policies",
    "selected_trade_ledger",
    "select_advancers",
]
