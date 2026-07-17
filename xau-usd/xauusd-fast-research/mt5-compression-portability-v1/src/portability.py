from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SHARED_DATA_PATH = ROOT / "independent-specialists-v1" / "src" / "data.py"


def _load_shared_data() -> Any:
    name = "xau_mt5_compression_shared_data"
    spec = importlib.util.spec_from_file_location(name, SHARED_DATA_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared data module from {SHARED_DATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SHARED_DATA = _load_shared_data()


@dataclass(frozen=True)
class PortabilityRun:
    candidates: pd.DataFrame
    all_trades: pd.DataFrame
    policy_trades: pd.DataFrame
    source_m5: pd.DataFrame
    evidence: dict[str, Any]


def wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["bid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous).abs(),
            (frame["bid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return wilder(true_range, period)


def aggregate_calendar_bars(
    m5: pd.DataFrame,
    minutes: int,
    label: str,
    minimum_rows: int,
) -> pd.DataFrame:
    """Aggregate fixed UTC buckets while retaining scheduled maintenance gaps."""
    source = m5.copy()
    source["_bucket"] = source["bar_start_utc"].dt.floor(f"{minutes}min")
    aggregations: dict[str, str] = {"bar_start_utc": "size"}
    for side in ("bid", "ask", "mid"):
        aggregations.update(
            {
                f"{side}_open": "first",
                f"{side}_high": "max",
                f"{side}_low": "min",
                f"{side}_close": "last",
            }
        )
    grouped = source.groupby("_bucket", sort=True, observed=True).agg(aggregations)
    grouped = grouped.rename(columns={"bar_start_utc": "source_rows"})
    grouped = grouped.loc[grouped["source_rows"] >= minimum_rows].reset_index()
    grouped["bar_start_utc"] = grouped.pop("_bucket")
    grouped["bar_end_utc"] = grouped["bar_start_utc"] + pd.Timedelta(minutes=minutes)
    grouped["timestamp_utc"] = grouped["bar_end_utc"]
    grouped["timeframe"] = label
    return grouped


def _percentile_rank_last(window: np.ndarray) -> float:
    if len(window) == 0 or not np.isfinite(window[-1]):
        return np.nan
    valid = window[np.isfinite(window)]
    if len(valid) != len(window):
        return np.nan
    return float(100.0 * np.count_nonzero(valid <= valid[-1]) / len(valid))


def prepare_signal_bars(
    m5: pd.DataFrame, settings: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    minimum_rows = int(settings["minimum_m5_rows_per_calendar_bucket"])
    d1 = aggregate_calendar_bars(m5, 1440, "D1", minimum_rows)
    h4 = aggregate_calendar_bars(m5, 240, "H4", minimum_rows)

    d1["atr_d1"] = atr(d1, int(settings["d1_atr_period"]))
    d1["range_d1"] = d1["bid_high"] - d1["bid_low"]
    box_days = int(settings["d1_box_days"])
    d1["box_high"] = d1["bid_high"].rolling(box_days, min_periods=box_days).max()
    d1["box_low"] = d1["bid_low"].rolling(box_days, min_periods=box_days).min()
    d1["median_range_d1"] = d1["range_d1"].rolling(
        int(settings["d1_range_median_lookback"]),
        min_periods=int(settings["d1_range_median_lookback"]),
    ).median()
    percentile_lookback = int(settings["d1_atr_percentile_lookback"])
    d1["atr_percentile_d1"] = d1["atr_d1"].rolling(
        percentile_lookback, min_periods=percentile_lookback
    ).apply(_percentile_rank_last, raw=True)
    d1["d1_history_bars"] = np.arange(1, len(d1) + 1)

    h4["atr_h4"] = atr(h4, int(settings["h4_atr_period"]))
    h4_range = (h4["bid_high"] - h4["bid_low"]).replace(0.0, np.nan)
    h4["body_fraction_h4"] = (h4["bid_close"] - h4["bid_open"]).abs() / h4_range

    available = d1[
        [
            "timestamp_utc",
            "box_high",
            "box_low",
            "median_range_d1",
            "atr_percentile_d1",
            "d1_history_bars",
        ]
    ].sort_values("timestamp_utc")
    merged = pd.merge_asof(
        h4.sort_values("timestamp_utc"),
        available,
        on="timestamp_utc",
        direction="backward",
        allow_exact_matches=True,
    )
    return d1, merged


def generate_candidates(
    h4: pd.DataFrame, settings: dict[str, Any]
) -> pd.DataFrame:
    box_width = h4["box_high"] - h4["box_low"]
    box_average = box_width / float(settings["d1_box_days"])
    mask = (
        (h4["d1_history_bars"] >= int(settings["minimum_d1_history_bars"]))
        & (h4["atr_percentile_d1"] <= float(settings["d1_atr_percentile_max"]))
        & (
            box_average
            <= float(settings["d1_box_average_to_median_max"])
            * h4["median_range_d1"]
        )
        & (
            h4["body_fraction_h4"]
            >= float(settings["h4_minimum_body_fraction"])
        )
        & (h4["bid_close"] > h4["box_high"])
        & (h4["bid_close"] > h4["bid_open"])
        & np.isfinite(h4["atr_h4"])
    )
    selected = h4.loc[mask].copy()
    if selected.empty:
        return pd.DataFrame(
            columns=[
                "signal_time",
                "direction",
                "stop_distance",
                "target_r",
            ]
        )
    structural = selected["bid_close"] - selected["box_low"]
    selected["stop_distance"] = pd.concat(
        [
            structural,
            selected["atr_h4"],
            pd.Series(float(settings["stop_floor_price"]), index=selected.index),
        ],
        axis=1,
    ).max(axis=1)
    selected["signal_time"] = selected["timestamp_utc"]
    selected["direction"] = "LONG"
    selected["target_r"] = float(settings["target_r"])
    selected["break_distance_atr"] = (
        selected["bid_close"] - selected["box_high"]
    ) / selected["atr_h4"]
    columns = [
        "signal_time",
        "direction",
        "stop_distance",
        "target_r",
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "atr_h4",
        "body_fraction_h4",
        "box_high",
        "box_low",
        "median_range_d1",
        "atr_percentile_d1",
        "break_distance_atr",
    ]
    return selected[columns].sort_values("signal_time").reset_index(drop=True)


def _simulate_candidate(
    m5: pd.DataFrame,
    starts: np.ndarray,
    bid_open_values: np.ndarray,
    bid_high_values: np.ndarray,
    bid_low_values: np.ndarray,
    bid_close_values: np.ndarray,
    ask_open_values: np.ndarray,
    signal: pd.Series,
    execution: dict[str, Any],
) -> dict[str, Any]:
    signal_time = pd.Timestamp(signal["signal_time"])
    entry_index = int(
        np.searchsorted(starts, np.datetime64(signal_time.tz_convert(None)), side="left")
    )
    if entry_index >= len(m5):
        return {"accepted": False, "rejection_reason": "NO_M5_ENTRY"}
    entry_time = m5["bar_start_utc"].iat[entry_index]
    delay = (entry_time - signal_time).total_seconds() / 60.0
    if delay < 0 or delay > float(execution["maximum_entry_gap_minutes"]):
        return {"accepted": False, "rejection_reason": "NONCONTIGUOUS_M5_ENTRY"}
    entry = float(ask_open_values[entry_index])
    spread = float(ask_open_values[entry_index] - bid_open_values[entry_index])
    risk = float(signal["stop_distance"])
    if risk <= 0 or spread < 0:
        return {"accepted": False, "rejection_reason": "INVALID_ENTRY_OR_RISK"}
    if spread > float(execution["maximum_spread_price"]):
        return {"accepted": False, "rejection_reason": "SPREAD_PRICE_LIMIT"}
    if spread / risk > float(execution["maximum_spread_r"]):
        return {"accepted": False, "rejection_reason": "SPREAD_R_LIMIT"}
    stop = entry - risk
    target = entry + float(signal["target_r"]) * risk
    exit_index = len(m5) - 1
    exit_price = float(bid_close_values[-1])
    exit_reason = "END_OF_DATA"
    ambiguous = False
    exit_at_open = False
    hit_index: int | None = None
    chunk_size = 8192
    for chunk_start in range(entry_index, len(m5), chunk_size):
        chunk_end = min(len(m5), chunk_start + chunk_size)
        hit = (
            (bid_open_values[chunk_start:chunk_end] < stop)
            | (bid_open_values[chunk_start:chunk_end] >= target)
            | (bid_low_values[chunk_start:chunk_end] <= stop)
            | (bid_high_values[chunk_start:chunk_end] >= target)
        )
        positions = np.flatnonzero(hit)
        if len(positions):
            hit_index = chunk_start + int(positions[0])
            break
    if hit_index is not None:
        index = hit_index
        bid_open = float(bid_open_values[index])
        if bid_open < stop:
            exit_index, exit_price, exit_reason, exit_at_open = (
                index,
                bid_open,
                "GAP_THROUGH_STOP",
                True,
            )
        elif bid_open >= target:
            exit_index, exit_price, exit_reason, exit_at_open = (
                index,
                target,
                "TARGET_GAP_FROZEN_TARGET",
                True,
            )
        else:
            stop_hit = float(bid_low_values[index]) <= stop
            target_hit = float(bid_high_values[index]) >= target
            if stop_hit:
                exit_index, exit_price = index, stop
                ambiguous = bool(target_hit)
                exit_reason = "AMBIGUOUS_M5_STOP_FIRST" if ambiguous else "STOP"
            elif target_hit:
                exit_index, exit_price, exit_reason = index, target, "TARGET"
    exit_row = m5.iloc[exit_index]
    exit_time = exit_row["bar_start_utc"] if exit_at_open else exit_row["timestamp_utc"]
    net_r = (exit_price - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    risk_usd = risk * float(execution["ounces_at_0_01_lot"])
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    stress_net_r = net_r - extra_cost_r - float(execution["stress_slippage_r"])
    return {
        "accepted": True,
        "rejection_reason": "",
        "entry_time": entry_time,
        "exit_time": exit_time,
        "entry_price": entry,
        "exit_price": exit_price,
        "stop": stop,
        "target": target,
        "initial_risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread": spread,
        "entry_spread_r": spread / risk,
        "exit_reason": exit_reason,
        "net_r": net_r,
        "stress_net_r": stress_net_r,
        "extra_cost_r": extra_cost_r,
        "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
        "ambiguous_m5": ambiguous,
    }


def simulate_candidates(
    m5: pd.DataFrame,
    candidates: pd.DataFrame,
    execution: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    starts = m5["bar_start_utc"].to_numpy(dtype="datetime64[ns]")
    bid_open_values = m5["bid_open"].to_numpy(dtype=float)
    bid_high_values = m5["bid_high"].to_numpy(dtype=float)
    bid_low_values = m5["bid_low"].to_numpy(dtype=float)
    bid_close_values = m5["bid_close"].to_numpy(dtype=float)
    ask_open_values = m5["ask_open"].to_numpy(dtype=float)
    candidate_rows: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    for candidate_id, signal in candidates.iterrows():
        outcome = _simulate_candidate(
            m5,
            starts,
            bid_open_values,
            bid_high_values,
            bid_low_values,
            bid_close_values,
            ask_open_values,
            signal,
            execution,
        )
        ledger = {"candidate_id": int(candidate_id), **signal.to_dict(), **outcome}
        candidate_rows.append(ledger)
        if outcome["accepted"]:
            trades.append(ledger)
    return pd.DataFrame(candidate_rows), pd.DataFrame(trades)


def apply_policy(
    trades: pd.DataFrame,
    policy_id: str,
    settings: dict[str, Any],
) -> pd.DataFrame:
    if trades.empty:
        return trades.assign(policy_id=pd.Series(dtype=str))
    maximum_concurrent = int(settings["maximum_concurrent_positions"])
    maximum_daily = int(settings["maximum_entries_per_utc_day"])
    active: list[pd.Timestamp] = []
    daily_counts: dict[Any, int] = {}
    accepted: list[pd.Series] = []
    for _, trade in trades.sort_values(["entry_time", "candidate_id"]).iterrows():
        active = [exit_time for exit_time in active if exit_time > trade["entry_time"]]
        day = trade["entry_time"].date()
        if len(active) >= maximum_concurrent:
            continue
        if daily_counts.get(day, 0) >= maximum_daily:
            continue
        accepted.append(trade)
        active.append(trade["exit_time"])
        daily_counts[day] = daily_counts.get(day, 0) + 1
    result = pd.DataFrame(accepted).copy()
    result["policy_id"] = policy_id
    return result


def run_portability(config: dict[str, Any]) -> PortabilityRun:
    m5, evidence = SHARED_DATA.load_m5(config)
    d1, h4 = prepare_signal_bars(m5, config["signal"])
    candidates = generate_candidates(h4, config["signal"])
    candidate_ledger, all_trades = simulate_candidates(
        m5, candidates, config["execution"]
    )
    policies = [
        apply_policy(all_trades, policy_id, settings)
        for policy_id, settings in config["policies"].items()
    ]
    policy_trades = pd.concat(policies, ignore_index=True) if policies else pd.DataFrame()
    evidence = {
        **evidence,
        "d1_rows": int(len(d1)),
        "h4_rows": int(len(h4)),
        "candidate_rows": int(len(candidates)),
        "executable_candidate_rows": int(len(all_trades)),
    }
    return PortabilityRun(candidate_ledger, all_trades, policy_trades, m5, evidence)


def profit_factor(values: pd.Series) -> float | None:
    positive = float(values.loc[values > 0].sum())
    negative = float(-values.loc[values < 0].sum())
    if negative == 0:
        return None if positive == 0 else float("inf")
    return positive / negative


def closed_drawdown(values: pd.Series) -> float:
    equity = values.fillna(0.0).cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def stage_metrics(
    trades: pd.DataFrame,
    source_m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    top_n: int,
) -> dict[str, Any]:
    stage = trades.loc[
        (trades["entry_time"] >= start) & (trades["entry_time"] < end)
    ].copy()
    source_days = int(
        source_m5.loc[
            (source_m5["bar_start_utc"] >= start)
            & (source_m5["bar_start_utc"] < end),
            "bar_start_utc",
        ].dt.date.nunique()
    )
    stress = (
        stage["stress_net_r"].astype(float)
        if not stage.empty
        else pd.Series(dtype=float)
    )
    yearly = (
        stage.assign(year=stage["entry_time"].dt.year)
        .groupby("year", sort=True)["stress_net_r"]
        .sum()
        if not stage.empty
        else pd.Series(dtype=float)
    )
    removed = (
        stress.drop(stress.nlargest(min(top_n, len(stress))).index)
        if len(stress)
        else stress
    )
    return {
        "trades": int(len(stage)),
        "source_days": source_days,
        "trades_per_source_day": len(stage) / source_days if source_days else 0.0,
        "net_r": float(stage["net_r"].sum()) if not stage.empty else 0.0,
        "stress_net_r": float(stress.sum()),
        "stress_pf": profit_factor(stress),
        "average_stress_r": float(stress.mean()) if len(stress) else 0.0,
        "closed_drawdown_r": closed_drawdown(stress),
        "positive_active_year_share": float((yearly > 0).mean()) if len(yearly) else 0.0,
        "active_years": int(len(yearly)),
        "top_winners_removed": int(min(top_n, len(stress))),
        "top_winners_removed_stress_net_r": float(removed.sum()),
    }


def evaluate_gate(
    value: dict[str, Any], gate: dict[str, Any]
) -> tuple[bool, dict[str, bool]]:
    checks = {
        "minimum_trades": value["trades"] >= int(gate["minimum_trades"]),
        "minimum_stress_pf": value["stress_pf"] is not None
        and value["stress_pf"] >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": value["average_stress_r"]
        >= float(gate["minimum_average_stress_r"]),
        "maximum_closed_drawdown_r": value["closed_drawdown_r"]
        <= float(gate["maximum_closed_drawdown_r"]),
        "minimum_positive_active_year_share": value["positive_active_year_share"]
        >= float(gate["minimum_positive_active_year_share"]),
        "top_winners_removed_positive": value[
            "top_winners_removed_stress_net_r"
        ]
        > 0,
    }
    return all(checks.values()), checks
