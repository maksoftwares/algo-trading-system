from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


FEATURE_NAMES = (
    "atr_ratio",
    "rv_1h",
    "rv_24h",
    "slope_atr",
    "ret_1h",
    "ret_4h",
    "ret_24h",
    "dist_hi_24h",
    "dist_lo_24h",
)


def closed_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame["pnl_usd"].to_numpy(dtype=float)
    gross_profit = float(values[values > 0.0].sum())
    gross_loss = -float(values[values < 0.0].sum())
    cumulative = np.concatenate(([0.0], np.cumsum(values)))
    drawdown = np.maximum.accumulate(cumulative) - cumulative
    return {
        "trades": int(len(values)),
        "net_pnl_usd": float(values.sum()),
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "win_rate": float((values > 0.0).mean()) if len(values) else None,
        "closed_drawdown_usd": float(drawdown.max()) if len(drawdown) else 0.0,
    }


def feature_decisions(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if frame["trade_id"].duplicated().any():
        raise ValueError("Causal feature ledger has duplicate trade IDs")
    decisions: dict[str, dict[str, Any]] = {}
    for row in frame.to_dict("records"):
        rank = row.get("rank")
        if rank is None or not np.isfinite(float(rank)):
            continue
        decision: dict[str, Any] = {
            "reason": "SCORE_COMPLETE",
            "rank": float(rank),
            "score": float(row["score"]),
            "candidate_direction": str(row["direction"]).upper(),
        }
        for name in FEATURE_NAMES:
            value = row.get(name)
            decision[name] = (
                float(value)
                if value is not None and np.isfinite(float(value))
                else None
            )
        decisions[str(row["trade_id"])] = decision
    return decisions


def annual_comparison(
    baseline: pd.DataFrame, challenger: pd.DataFrame
) -> list[dict[str, Any]]:
    baseline_year = pd.to_datetime(
        baseline["entry_time_utc"], utc=True, format="mixed"
    ).dt.year
    challenger_year = pd.to_datetime(
        challenger["entry_time_utc"], utc=True, format="mixed"
    ).dt.year
    years = sorted(set(baseline_year.tolist()) | set(challenger_year.tolist()))
    rows: list[dict[str, Any]] = []
    for year in years:
        baseline_net = float(baseline.loc[baseline_year.eq(year), "pnl_usd"].sum())
        challenger_net = float(
            challenger.loc[challenger_year.eq(year), "pnl_usd"].sum()
        )
        rows.append(
            {
                "year": int(year),
                "baseline_net_pnl_usd": baseline_net,
                "challenger_net_pnl_usd": challenger_net,
                "delta_pnl_usd": challenger_net - baseline_net,
            }
        )
    return rows


def replacement_capacity_count(
    baseline_trades: int, vetoes: int, full_dynamic_trades: int
) -> int:
    return int(full_dynamic_trades - (baseline_trades - vetoes))


def exact_set_difference(
    expected: Sequence[str], actual: Sequence[str]
) -> Mapping[str, list[str]]:
    expected_set = set(map(str, expected))
    actual_set = set(map(str, actual))
    return {
        "missing": sorted(expected_set - actual_set),
        "unexpected": sorted(actual_set - expected_set),
    }


def fixed_lifecycle_equity_drawdown(
    candidates: Sequence[Any],
    event_rows: Sequence[Mapping[str, Any]],
    quotes: Mapping[str, np.ndarray],
    retained_trade_ids: Sequence[str],
    *,
    starting_equity_usd: float,
) -> float:
    retained = set(map(str, retained_trade_ids))
    candidate_map = {
        str(candidate.trade_id): candidate
        for candidate in candidates
        if str(candidate.trade_id) in retained
    }
    opens: dict[str, Mapping[str, Any]] = {}
    closes: dict[str, Mapping[str, Any]] = {}
    for row in event_rows:
        trade_id = str(row.get("trade_id", ""))
        if trade_id not in retained:
            continue
        if row["event"] == "ORDER_FILLED":
            if trade_id in opens:
                raise ValueError(f"Duplicate open event: {trade_id}")
            opens[trade_id] = row
        elif row["event"] == "POSITION_CLOSED":
            if trade_id in closes:
                raise ValueError(f"Duplicate close event: {trade_id}")
            closes[trade_id] = row
    if set(candidate_map) != retained or set(opens) != retained or set(closes) != retained:
        raise ValueError("Fixed lifecycle reconstruction lacks a candidate/open/close")

    cycles = np.asarray(quotes["cycle_ms"], dtype=np.int64)
    bid = np.asarray(quotes["bid"], dtype=float)
    ask = np.asarray(quotes["ask"], dtype=float)
    events: dict[int, dict[str, list[str]]] = {}
    for trade_id in sorted(retained):
        for event_name, source in (("close", closes), ("open", opens)):
            timestamp = pd.Timestamp(source[trade_id]["timestamp_utc"])
            timestamp_ms = int(timestamp.timestamp() * 1000)
            index = int(np.searchsorted(cycles, timestamp_ms))
            if index >= len(cycles) or int(cycles[index]) != timestamp_ms:
                raise ValueError(
                    f"Lifecycle event is not on a replay cycle: {trade_id}: {timestamp}"
                )
            events.setdefault(index, {"close": [], "open": []})[event_name].append(
                trade_id
            )

    bid_coefficient = 0.0
    ask_coefficient = 0.0
    open_constant = 0.0
    closed_pnl = 0.0
    peak = float(starting_equity_usd)
    maximum_drawdown = 0.0
    open_terms: dict[str, tuple[float, float, float]] = {}

    def observe(values: np.ndarray) -> None:
        nonlocal peak, maximum_drawdown
        if values.size == 0:
            return
        running_peak = np.maximum(np.maximum.accumulate(values), peak)
        maximum_drawdown = max(
            maximum_drawdown, float(np.max(running_peak - values))
        )
        peak = max(peak, float(np.max(values)))

    previous = 0
    for index in sorted(events):
        values = (
            float(starting_equity_usd)
            + closed_pnl
            + bid_coefficient * bid[previous : index + 1]
            + ask_coefficient * ask[previous : index + 1]
            + open_constant
        )
        observe(values)
        for trade_id in events[index]["close"]:
            bid_term, ask_term, constant = open_terms.pop(trade_id)
            bid_coefficient -= bid_term
            ask_coefficient -= ask_term
            open_constant -= constant
            closed_pnl += float(closes[trade_id]["pnl_usd"])
        for trade_id in events[index]["open"]:
            candidate = candidate_map[trade_id]
            basis_offset = float(opens[trade_id]["basis_offset"])
            if str(candidate.direction).upper() == "LONG":
                bid_term, ask_term = 1.0, 0.0
                constant = (
                    basis_offset
                    - float(candidate.entry_price)
                    - float(candidate.open_cost_usd)
                )
            else:
                bid_term, ask_term = 0.0, -1.0
                constant = (
                    -basis_offset
                    + float(candidate.entry_price)
                    - float(candidate.open_cost_usd)
                )
            open_terms[trade_id] = (bid_term, ask_term, constant)
            bid_coefficient += bid_term
            ask_coefficient += ask_term
            open_constant += constant
        observe(
            np.asarray(
                [
                    float(starting_equity_usd)
                    + closed_pnl
                    + bid_coefficient * float(bid[index])
                    + ask_coefficient * float(ask[index])
                    + open_constant
                ]
            )
        )
        previous = index + 1
    if open_terms:
        raise ValueError(f"Unclosed retained positions: {sorted(open_terms)}")
    observe(
        np.asarray(
            [float(starting_equity_usd) + closed_pnl], dtype=float
        )
    )
    return maximum_drawdown
