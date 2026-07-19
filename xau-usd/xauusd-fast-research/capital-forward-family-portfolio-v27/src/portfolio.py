from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
REQUIRED_TRADE_COLUMNS = (
    "evidence_partition",
    "date_utc",
    "candidate_time_utc",
    "candidate_time_msc",
    "side",
    "entry_time_msc",
    "exit_time_msc",
    "base_pnl_dollars",
    "stress_pnl_dollars",
    "reference_lot",
)


def load_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / "config" / "capital_forward_family_portfolio_v27.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any], omitted_key: str) -> str:
    work = dict(payload)
    work.pop(omitted_key, None)
    encoded = json.dumps(
        work,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def profit_factor(values: pd.Series | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    gains = float(array[array > 0.0].sum())
    losses = float(-array[array < 0.0].sum())
    if losses <= 0.0:
        return 999999.0 if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    equity = np.concatenate(([0.0], np.cumsum(array)))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity))


def closed_drawdown_by_exit(times: pd.Series, values: pd.Series) -> float:
    frame = pd.DataFrame(
        {
            "exit_time": pd.to_datetime(times, utc=True),
            "pnl": values.astype(float).to_numpy(),
        }
    )
    realized = frame.groupby("exit_time", sort=True)["pnl"].sum()
    return closed_drawdown(realized)


def circular_block_bootstrap_pvalue(
    values: np.ndarray,
    *,
    samples: int,
    seed: int,
    block_length: int,
) -> float:
    daily = np.asarray(values, dtype=float)
    if len(daily) < block_length or not np.isfinite(daily).all():
        raise ValueError("V27 daily values cannot support the locked block bootstrap")
    observed_mean = float(daily.mean())
    centered = daily - observed_mean
    block_count = int(np.ceil(len(daily) / block_length))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(daily), size=(samples, block_count))
    offsets = np.arange(block_length, dtype=np.int64)
    indexes = (starts[..., None] + offsets) % len(daily)
    means = centered[indexes].reshape(samples, -1)[:, : len(daily)].mean(axis=1)
    return float((1 + int(np.count_nonzero(means >= observed_mean))) / (samples + 1))


def daily_pnl(trades: pd.DataFrame, stage_dates: list[str]) -> pd.DataFrame:
    observed = (
        trades.groupby("date_utc", as_index=False)
        .agg(
            trades=("date_utc", "size"),
            base_pnl_dollars=("base_pnl_dollars", "sum"),
            stress_pnl_dollars=("stress_pnl_dollars", "sum"),
        )
        .sort_values("date_utc", kind="mergesort")
    )
    daily = pd.DataFrame({"date_utc": stage_dates}).merge(
        observed, on="date_utc", how="left", validate="one_to_one"
    )
    for column in ("trades", "base_pnl_dollars", "stress_pnl_dollars"):
        daily[column] = daily[column].fillna(0)
    daily["trades"] = daily["trades"].astype(int)
    return daily


def component_pvalue(
    trades: pd.DataFrame,
    stage_dates: list[str],
    config: Mapping[str, Any],
    seed: int,
) -> float:
    daily = daily_pnl(trades, stage_dates)
    multiple = config["multiple_testing"]
    return circular_block_bootstrap_pvalue(
        daily["base_pnl_dollars"].to_numpy(dtype=float),
        samples=int(multiple["bootstrap_samples"]),
        seed=seed,
        block_length=int(multiple["block_length_weekdays"]),
    )


def verify_core_reference(
    core: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    expected = config["core"]
    required = {"exit_time_utc", "pnl_usd_0p01_equiv"}
    if missing := required.difference(core.columns):
        raise ValueError(f"V27 Core ledger is missing columns: {sorted(missing)}")
    if len(core) != int(expected["expected_total_rows"]):
        raise ValueError("V27 Core ledger row count changed")
    frame = core.copy()
    frame["exit_time_utc"] = pd.to_datetime(frame["exit_time_utc"], utc=True)
    start = pd.Timestamp(expected["reference_start_inclusive_utc"])
    end = pd.Timestamp(expected["reference_end_exclusive_utc"])
    reference = frame.loc[
        frame["exit_time_utc"].ge(start) & frame["exit_time_utc"].lt(end)
    ].sort_values("exit_time_utc", kind="mergesort")
    values = reference["pnl_usd_0p01_equiv"].astype(float)
    weekdays = int(np.busday_count(start.date(), end.date()))
    metrics = {
        "rows": int(len(reference)),
        "weekdays": weekdays,
        "trades_per_weekday": float(len(reference) / weekdays),
        "net_dollars": float(values.sum()),
        "profit_factor": profit_factor(values),
        "closed_drawdown_dollars": closed_drawdown_by_exit(
            reference["exit_time_utc"], values
        ),
    }
    checks = (
        metrics["rows"] == int(expected["expected_reference_rows"]),
        metrics["weekdays"] == int(expected["expected_reference_weekdays"]),
        np.isclose(
            metrics["trades_per_weekday"],
            float(expected["reference_trades_per_weekday"]),
            rtol=0.0,
            atol=1e-12,
        ),
        np.isclose(
            metrics["net_dollars"],
            float(expected["expected_reference_net_dollars"]),
            rtol=0.0,
            atol=1e-9,
        ),
        np.isclose(
            metrics["profit_factor"],
            float(expected["expected_reference_profit_factor"]),
            rtol=0.0,
            atol=1e-12,
        ),
        np.isclose(
            metrics["closed_drawdown_dollars"],
            float(expected["expected_reference_closed_drawdown_dollars"]),
            rtol=0.0,
            atol=1e-9,
        ),
    )
    if not all(checks):
        raise ValueError(f"V27 Core reference identity changed: {metrics}")
    return reference, metrics


def validate_trade_frame(frame: pd.DataFrame, lane: str) -> None:
    if missing := set(REQUIRED_TRADE_COLUMNS).difference(frame.columns):
        raise ValueError(f"V27 {lane} trades are missing columns: {sorted(missing)}")
    if frame["candidate_time_msc"].duplicated().any():
        raise ValueError(f"V27 {lane} has duplicate candidate milliseconds")
    if not frame["side"].isin(("LONG", "SHORT")).all():
        raise ValueError(f"V27 {lane} has an unknown side")
    if not np.isfinite(
        frame[["base_pnl_dollars", "stress_pnl_dollars"]].to_numpy(dtype=float)
    ).all():
        raise ValueError(f"V27 {lane} has non-finite economics")


def route_fixed_union(
    v24: pd.DataFrame,
    v26: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    validate_trade_frame(v24, "V24_1")
    validate_trade_frame(v26, "V26")
    priorities = {
        lane: int(config["components"][lane]["priority"])
        for lane in config["router"]["fixed_priority"]
    }
    tagged = []
    for lane, frame in (("V24_1", v24), ("V26", v26)):
        work = frame.copy()
        work.insert(0, "source_lane", lane)
        work.insert(1, "router_priority", priorities[lane])
        tagged.append(work)
    family = pd.concat(tagged, ignore_index=True, sort=False).sort_values(
        ["date_utc", "candidate_time_msc", "router_priority", "entry_time_msc"],
        kind="mergesort",
    )
    maximum = int(config["router"]["maximum_selected_satellite_trades_per_utc_day"])
    selected_rows: list[dict[str, Any]] = []
    overlap_rejections = 0
    cap_rejections = 0
    selected_by_date: dict[str, int] = {}
    last_exit_by_date: dict[str, int] = {}
    for _, row in family.iterrows():
        date = str(row["date_utc"])
        count = selected_by_date.get(date, 0)
        candidate = int(row["candidate_time_msc"])
        if candidate < last_exit_by_date.get(date, -1):
            overlap_rejections += 1
            continue
        if count >= maximum:
            cap_rejections += 1
            continue
        record = row.to_dict()
        record["route_rank_utc_day"] = count + 1
        selected_rows.append(record)
        selected_by_date[date] = count + 1
        last_exit_by_date[date] = int(row["exit_time_msc"])
    columns = ["source_lane", "router_priority", "route_rank_utc_day"] + [
        column
        for column in family.columns
        if column not in {"source_lane", "router_priority"}
    ]
    selected = pd.DataFrame(selected_rows, columns=columns)
    raw_count = int(len(family))
    audit = {
        "raw_family_trades": raw_count,
        "raw_v24_1_trades": int(len(v24)),
        "raw_v26_trades": int(len(v26)),
        "selected_family_trades": int(len(selected)),
        "selected_v24_1_trades": int(selected["source_lane"].eq("V24_1").sum()),
        "selected_v26_trades": int(selected["source_lane"].eq("V26").sum()),
        "overlap_rejections": int(overlap_rejections),
        "daily_cap_rejections": int(cap_rejections),
        "overlap_rejection_share": float(overlap_rejections / raw_count)
        if raw_count
        else 0.0,
        "maximum_selected_on_one_utc_day": int(
            selected.groupby("date_utc").size().max()
        )
        if len(selected)
        else 0,
    }
    return selected, audit


def evaluate_fixed_union(
    selected: pd.DataFrame,
    stage_dates: list[str],
    partition: str,
    core_reference: pd.DataFrame,
    core_metrics: Mapping[str, Any],
    route_audit: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    if len(stage_dates) != int(config["stages"]["required_full_weekdays_per_stage"]):
        raise ValueError("V27 stage does not contain exactly 20 locked weekdays")
    trades = selected.loc[
        selected["evidence_partition"].eq(partition)
        & selected["date_utc"].isin(stage_dates)
    ].sort_values("entry_time_msc", kind="mergesort")
    daily = daily_pnl(trades, stage_dates)
    base = trades["base_pnl_dollars"].astype(float)
    stress = trades["stress_pnl_dollars"].astype(float)
    base_net = float(base.sum())
    stress_net = float(stress.sum())
    satellite_drawdown = (
        closed_drawdown_by_exit(
            pd.to_datetime(trades["exit_time_msc"], unit="ms", utc=True), base
        )
        if len(trades)
        else 0.0
    )
    recovery = (
        base_net / satellite_drawdown
        if satellite_drawdown > 0.0
        else (999999.0 if base_net > 0.0 else 0.0)
    )
    midpoint = len(stage_dates) // 2
    first = trades.loc[trades["date_utc"].isin(stage_dates[:midpoint])]
    second = trades.loc[trades["date_utc"].isin(stage_dates[midpoint:])]
    multiple = config["multiple_testing"]
    portfolio_pvalue = circular_block_bootstrap_pvalue(
        daily["base_pnl_dollars"].to_numpy(dtype=float),
        samples=int(multiple["bootstrap_samples"]),
        seed=int(multiple["portfolio_bootstrap_seed"]),
        block_length=int(multiple["block_length_weekdays"]),
    )
    satellite_frequency = float(len(trades) / len(stage_dates))
    projected_frequency = satellite_frequency + float(
        core_metrics["trades_per_weekday"]
    )
    long_share = float(trades["side"].eq("LONG").mean()) if len(trades) else 0.0
    short_share = float(trades["side"].eq("SHORT").mean()) if len(trades) else 0.0
    v24_share = float(trades["source_lane"].eq("V24_1").mean()) if len(trades) else 0.0
    v26_share = float(trades["source_lane"].eq("V26").mean()) if len(trades) else 0.0
    core_values = core_reference["pnl_usd_0p01_equiv"].astype(float)
    combined_values = pd.concat([core_values, base], ignore_index=True)
    combined_times = pd.concat(
        [
            core_reference["exit_time_utc"].reset_index(drop=True),
            pd.Series(
                pd.to_datetime(trades["exit_time_msc"], unit="ms", utc=True),
                name="exit_time_utc",
            ),
        ],
        ignore_index=True,
    )
    combined_net = float(combined_values.sum())
    combined_pf = profit_factor(combined_values)
    combined_drawdown = closed_drawdown_by_exit(combined_times, combined_values)
    metrics = {
        "evidence_partition": partition,
        "stage_dates": stage_dates,
        "full_weekdays": int(len(stage_dates)),
        "satellite_trades": int(len(trades)),
        "satellite_trades_per_weekday": satellite_frequency,
        "projected_core_plus_satellite_trades_per_weekday": projected_frequency,
        "long_share": long_share,
        "short_share": short_share,
        "v24_1_share": v24_share,
        "v26_share": v26_share,
        "base_net_pnl_dollars": base_net,
        "base_profit_factor": profit_factor(base),
        "stress_net_pnl_dollars": stress_net,
        "stress_profit_factor": profit_factor(stress),
        "profitable_day_share": float(daily["base_pnl_dollars"].gt(0.0).mean()),
        "satellite_closed_drawdown_dollars": satellite_drawdown,
        "satellite_recovery_factor": float(recovery),
        "first_half_profit_factor": profit_factor(first["base_pnl_dollars"]),
        "second_half_profit_factor": profit_factor(second["base_pnl_dollars"]),
        "portfolio_block_bootstrap_pvalue": portfolio_pvalue,
        "core_reference_net_dollars": float(core_metrics["net_dollars"]),
        "core_plus_satellite_net_dollars": combined_net,
        "core_plus_satellite_profit_factor": combined_pf,
        "core_plus_satellite_closed_drawdown_dollars": combined_drawdown,
        **dict(route_audit),
    }
    gates = config["gates"]
    alpha = float(multiple["maximum_one_sided_pvalue"])
    checks = {
        "minimum_satellite_frequency": satellite_frequency
        >= float(gates["minimum_satellite_trades_per_weekday"]),
        "maximum_satellite_frequency": satellite_frequency
        <= float(gates["maximum_satellite_trades_per_weekday"]),
        "minimum_projected_total_frequency": projected_frequency
        >= float(gates["minimum_projected_total_trades_per_weekday"]),
        "maximum_projected_total_frequency": projected_frequency
        <= float(gates["maximum_projected_total_trades_per_weekday"]),
        "direction_balance": min(long_share, short_share)
        >= float(gates["minimum_direction_share"]),
        "component_balance": min(v24_share, v26_share)
        >= float(gates["minimum_component_share"]),
        "positive_base_net": (not gates["require_positive_base_net"] or base_net > 0.0),
        "minimum_base_profit_factor": metrics["base_profit_factor"]
        >= float(gates["minimum_base_profit_factor"]),
        "positive_stress_net": (
            not gates["require_positive_stress_net"] or stress_net > 0.0
        ),
        "minimum_stress_profit_factor": metrics["stress_profit_factor"]
        >= float(gates["minimum_stress_profit_factor"]),
        "minimum_profitable_day_share": metrics["profitable_day_share"]
        >= float(gates["minimum_profitable_day_share"]),
        "maximum_satellite_closed_drawdown": satellite_drawdown
        <= float(gates["maximum_satellite_closed_drawdown_dollars"]),
        "minimum_satellite_recovery_factor": recovery
        >= float(gates["minimum_satellite_recovery_factor"]),
        "first_half_profit_factor": metrics["first_half_profit_factor"]
        >= float(gates["minimum_half_profit_factor"]),
        "second_half_profit_factor": metrics["second_half_profit_factor"]
        >= float(gates["minimum_half_profit_factor"]),
        "selection_adjusted_portfolio_pvalue": portfolio_pvalue <= alpha,
        "maximum_overlap_rejection_share": float(route_audit["overlap_rejection_share"])
        <= float(gates["maximum_overlap_rejection_share"]),
        "core_plus_satellite_net_additive": combined_net
        > float(gates["minimum_core_plus_satellite_net_dollars"]),
        "minimum_core_plus_satellite_profit_factor": combined_pf
        >= float(gates["minimum_core_plus_satellite_profit_factor"]),
        "maximum_core_plus_satellite_closed_drawdown": combined_drawdown
        <= float(gates["maximum_core_plus_satellite_closed_drawdown_dollars"]),
    }
    audit = {
        "schema_version": "xauusd_capital_forward_family_v27_stage_audit",
        "evidence_partition": partition,
        "stage_dates": stage_dates,
        "metrics": metrics,
        "gate_checks": checks,
        "gate_passed": bool(all(checks.values())),
        "floating_equity_drawdown_calculated": False,
        "same_period_core_shadow_required": True,
    }
    return audit, daily
