from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy import stats


def _wilder(values: pd.Series, period: int) -> pd.Series:
    return values.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def _atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["mid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["mid_high"] - frame["mid_low"],
            (frame["mid_high"] - previous).abs(),
            (frame["mid_low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return _wilder(true_range, period)


def aggregate_bars(
    m5: pd.DataFrame, minutes: int, label: str, minimum_rows: int
) -> pd.DataFrame:
    required = {
        "bar_start_utc",
        *{
            f"{side}_{field}"
            for side in ("bid", "ask", "mid")
            for field in ("open", "high", "low", "close")
        },
    }
    missing = sorted(required.difference(m5.columns))
    if missing:
        raise ValueError(f"M5 source is missing columns: {missing}")
    source = m5.copy().sort_values("bar_start_utc", kind="mergesort")
    source["bar_start_utc"] = pd.to_datetime(
        source["bar_start_utc"], utc=True, errors="raise"
    )
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
    grouped["bar_end_utc"] = grouped["bar_start_utc"] + pd.Timedelta(
        minutes=minutes
    )
    grouped["timeframe"] = label
    return grouped


def prepare_policy_bars(
    bars: pd.DataFrame, policy: Mapping[str, Any]
) -> pd.DataFrame:
    frame = bars.copy().sort_values("bar_end_utc", kind="mergesort").reset_index(
        drop=True
    )
    frame["atr"] = _atr(frame, int(policy["atr_period"]))
    mechanic = str(policy["mechanic"])
    if mechanic == "DONCHIAN":
        entry = int(policy["entry_lookback"])
        exit_lookback = int(policy["exit_lookback"])
        frame["entry_high"] = (
            frame["mid_high"].shift(1).rolling(entry, min_periods=entry).max()
        )
        frame["entry_low"] = (
            frame["mid_low"].shift(1).rolling(entry, min_periods=entry).min()
        )
        frame["exit_high"] = (
            frame["mid_high"]
            .shift(1)
            .rolling(exit_lookback, min_periods=exit_lookback)
            .max()
        )
        frame["exit_low"] = (
            frame["mid_low"]
            .shift(1)
            .rolling(exit_lookback, min_periods=exit_lookback)
            .min()
        )
        frame["desired_direction"] = np.select(
            [
                frame["mid_close"].gt(frame["entry_high"]),
                frame["mid_close"].lt(frame["entry_low"]),
            ],
            [1, -1],
            default=0,
        ).astype(int)
        frame["exit_long"] = frame["mid_close"].lt(frame["exit_low"])
        frame["exit_short"] = frame["mid_close"].gt(frame["exit_high"])
    elif mechanic == "TSMOM":
        lookback = int(policy["momentum_lookback"])
        momentum = frame["mid_close"] - frame["mid_close"].shift(lookback)
        frame["desired_direction"] = np.sign(momentum.fillna(0.0)).astype(int)
        frame["exit_long"] = frame["desired_direction"].lt(0)
        frame["exit_short"] = frame["desired_direction"].gt(0)
    else:
        raise KeyError(mechanic)
    valid = np.isfinite(frame["atr"]) & frame["atr"].gt(0.0)
    frame.loc[~valid, "desired_direction"] = 0
    frame["exit_long"] = frame["exit_long"].fillna(False)
    frame["exit_short"] = frame["exit_short"].fillna(False)
    return frame


def _record_exit(
    state: dict[str, Any],
    exit_time: pd.Timestamp,
    exit_price: float,
    reason: str,
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    sign = int(state["direction"])
    risk = float(state["initial_risk_price"])
    gross_r = sign * (exit_price - float(state["entry_price"])) / risk
    holding_days = max(
        0.0,
        (exit_time - pd.Timestamp(state["entry_time"])).total_seconds() / 86400.0,
    )
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    extra_cost_r = (
        float(execution["extra_execution_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return {
        "policy_id": str(state["policy_id"]),
        "attempt_no": int(state["attempt_no"]),
        "timeframe": str(state["timeframe"]),
        "mechanic": str(state["mechanic"]),
        "entry_time": pd.Timestamp(state["entry_time"]),
        "exit_time": exit_time,
        "direction": "LONG" if sign > 0 else "SHORT",
        "entry_price": float(state["entry_price"]),
        "exit_price": exit_price,
        "initial_stop": float(state["initial_stop"]),
        "final_stop": float(state["stop"]),
        "initial_risk_price": risk,
        "risk_usd": risk_usd,
        "entry_spread": float(state["entry_spread"]),
        "entry_spread_r": float(state["entry_spread"]) / risk,
        "exit_reason": reason,
        "gross_r": gross_r,
        "extra_cost_r": extra_cost_r,
        "stress_net_r": gross_r
        - extra_cost_r
        - float(execution["stress_slippage_r"]),
        "holding_minutes": (
            exit_time - pd.Timestamp(state["entry_time"])
        ).total_seconds()
        / 60.0,
        "current_account_feasible": risk_usd
        <= float(execution["current_account_risk_usd"]),
    }


def simulate_policy(
    m5: pd.DataFrame,
    prepared_bars: pd.DataFrame,
    policy: Mapping[str, Any],
    execution: Mapping[str, Any],
    stage_start: pd.Timestamp,
    stage_end: pd.Timestamp,
) -> pd.DataFrame:
    source = m5.copy().sort_values("bar_start_utc", kind="mergesort").reset_index(
        drop=True
    )
    for column in ("bar_start_utc", "bar_end_utc"):
        source[column] = pd.to_datetime(source[column], utc=True, errors="raise")
    starts = source["bar_start_utc"].dt.tz_localize(None).to_numpy(
        dtype="datetime64[ns]"
    )
    first = int(
        np.searchsorted(
            starts, np.datetime64(stage_start.tz_convert(None)), side="left"
        )
    )
    final = int(
        np.searchsorted(starts, np.datetime64(stage_end.tz_convert(None)), side="left")
    )
    decisions = prepared_bars.loc[
        prepared_bars["bar_end_utc"].ge(stage_start)
        & prepared_bars["bar_end_utc"].lt(stage_end)
    ].copy()
    decision_map: dict[int, pd.Series] = {}
    for _, row in decisions.iterrows():
        decision_time = pd.Timestamp(row["bar_end_utc"])
        index = int(
            np.searchsorted(
                starts, np.datetime64(decision_time.tz_convert(None)), side="left"
            )
        )
        if index >= final:
            continue
        delay = (
            pd.Timestamp(source["bar_start_utc"].iat[index]) - decision_time
        ).total_seconds() / 60.0
        if 0.0 <= delay <= float(execution["maximum_entry_gap_minutes"]):
            if index in decision_map:
                raise ValueError("Multiple completed signal bars map to one M5 entry")
            decision_map[index] = row

    state: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = []
    cooldown_remaining = 0

    for index in range(first, final):
        m5_row = source.iloc[index]
        bar_start = pd.Timestamp(m5_row["bar_start_utc"])
        bar_end = pd.Timestamp(m5_row["bar_end_utc"])
        exited_this_bar = False

        if state is not None:
            if int(state["direction"]) > 0 and float(m5_row["bid_open"]) <= float(
                state["stop"]
            ):
                rows.append(
                    _record_exit(
                        state,
                        bar_start,
                        float(m5_row["bid_open"]),
                        "GAP_THROUGH_STOP",
                        execution,
                    )
                )
                state = None
                cooldown_remaining = int(policy["cooldown_decisions"])
                exited_this_bar = True
            elif int(state["direction"]) < 0 and float(
                m5_row["ask_open"]
            ) >= float(state["stop"]):
                rows.append(
                    _record_exit(
                        state,
                        bar_start,
                        float(m5_row["ask_open"]),
                        "GAP_THROUGH_STOP",
                        execution,
                    )
                )
                state = None
                cooldown_remaining = int(policy["cooldown_decisions"])
                exited_this_bar = True

        decision = decision_map.get(index)
        if decision is not None:
            if state is not None:
                direction = int(state["direction"])
                signal_exit = bool(
                    decision["exit_long"] if direction > 0 else decision["exit_short"]
                )
                if signal_exit:
                    exit_price = float(
                        m5_row["bid_open"] if direction > 0 else m5_row["ask_open"]
                    )
                    rows.append(
                        _record_exit(
                            state, bar_start, exit_price, "SIGNAL_EXIT", execution
                        )
                    )
                    state = None
                    cooldown_remaining = int(policy["cooldown_decisions"])
                    exited_this_bar = True
                else:
                    atr = float(decision["atr"])
                    if direction > 0:
                        state["stop"] = max(
                            float(state["stop"]),
                            float(state["peak"])
                            - float(policy["trail_stop_atr"]) * atr,
                        )
                        if float(m5_row["bid_open"]) <= float(state["stop"]):
                            rows.append(
                                _record_exit(
                                    state,
                                    bar_start,
                                    float(m5_row["bid_open"]),
                                    "TRAIL_UPDATE_AT_OPEN",
                                    execution,
                                )
                            )
                            state = None
                            cooldown_remaining = int(policy["cooldown_decisions"])
                            exited_this_bar = True
                    else:
                        state["stop"] = min(
                            float(state["stop"]),
                            float(state["trough"])
                            + float(policy["trail_stop_atr"]) * atr,
                        )
                        if float(m5_row["ask_open"]) >= float(state["stop"]):
                            rows.append(
                                _record_exit(
                                    state,
                                    bar_start,
                                    float(m5_row["ask_open"]),
                                    "TRAIL_UPDATE_AT_OPEN",
                                    execution,
                                )
                            )
                            state = None
                            cooldown_remaining = int(policy["cooldown_decisions"])
                            exited_this_bar = True

            desired = int(decision["desired_direction"])
            if state is None and not exited_this_bar and cooldown_remaining > 0:
                cooldown_remaining -= 1
            elif state is None and not exited_this_bar and desired != 0:
                entry = float(
                    m5_row["ask_open"] if desired > 0 else m5_row["bid_open"]
                )
                spread = float(m5_row["ask_open"] - m5_row["bid_open"])
                risk = max(
                    float(execution["minimum_stop_distance_price"]),
                    float(policy["initial_stop_atr"]) * float(decision["atr"]),
                )
                if (
                    spread >= 0.0
                    and spread <= float(execution["maximum_spread_price"])
                    and spread / risk <= float(execution["maximum_spread_r"])
                ):
                    stop = entry - desired * risk
                    state = {
                        "policy_id": policy["policy_id"],
                        "attempt_no": policy["attempt_no"],
                        "timeframe": policy["timeframe"],
                        "mechanic": policy["mechanic"],
                        "direction": desired,
                        "entry_time": bar_start,
                        "entry_price": entry,
                        "entry_spread": spread,
                        "initial_risk_price": risk,
                        "initial_stop": stop,
                        "stop": stop,
                        "peak": entry,
                        "trough": entry,
                    }

        if state is not None:
            direction = int(state["direction"])
            if direction > 0 and float(m5_row["bid_low"]) <= float(state["stop"]):
                rows.append(
                    _record_exit(
                        state,
                        bar_end,
                        float(state["stop"]),
                        "STOP",
                        execution,
                    )
                )
                state = None
                cooldown_remaining = int(policy["cooldown_decisions"])
            elif direction < 0 and float(m5_row["ask_high"]) >= float(state["stop"]):
                rows.append(
                    _record_exit(
                        state,
                        bar_end,
                        float(state["stop"]),
                        "STOP",
                        execution,
                    )
                )
                state = None
                cooldown_remaining = int(policy["cooldown_decisions"])
            elif direction > 0:
                state["peak"] = max(float(state["peak"]), float(m5_row["bid_high"]))
            else:
                state["trough"] = min(
                    float(state["trough"]), float(m5_row["ask_low"])
                )

    if state is not None and final > first:
        last = source.iloc[final - 1]
        direction = int(state["direction"])
        rows.append(
            _record_exit(
                state,
                min(pd.Timestamp(last["bar_end_utc"]), stage_end),
                float(last["bid_close"] if direction > 0 else last["ask_close"]),
                "STAGE_END",
                execution,
            )
        )
    return (
        pd.DataFrame(rows).sort_values("entry_time", kind="mergesort").reset_index(
            drop=True
        )
        if rows
        else pd.DataFrame()
    )


def profit_factor(values: pd.Series) -> float:
    gains = float(values.loc[values > 0.0].sum())
    losses = float(-values.loc[values < 0.0].sum())
    if losses == 0.0:
        return float("inf") if gains > 0.0 else 0.0
    return gains / losses


def closed_drawdown(values: pd.Series) -> float:
    equity = np.concatenate(
        ([0.0], values.fillna(0.0).to_numpy(dtype=float).cumsum())
    )
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity)) if len(equity) else 0.0


def one_sided_trade_pvalue(values: pd.Series) -> float:
    clean = values.dropna().to_numpy(dtype=float)
    if len(clean) < 2 or float(clean.mean()) <= 0.0:
        return 1.0
    standard = float(clean.std(ddof=1))
    if standard == 0.0:
        return 0.0
    result = stats.ttest_1samp(clean, 0.0, alternative="greater")
    return float(result.pvalue) if np.isfinite(result.pvalue) else 1.0


def holm_adjust(pvalues: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=lambda key: (float(pvalues[key]), key))
    count = len(ordered)
    running = 0.0
    adjusted: dict[str, float] = {}
    for rank, key in enumerate(ordered):
        running = max(running, (count - rank) * float(pvalues[key]))
        adjusted[key] = min(1.0, running)
    return adjusted


def summarize(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    stage_start: pd.Timestamp,
    stage_end: pd.Timestamp,
    segments: list[list[str]],
    top_winners: int,
) -> dict[str, Any]:
    values = (
        trades["stress_net_r"].astype(float)
        if not trades.empty
        else pd.Series(dtype=float)
    )
    source_days = int(
        m5.loc[
            m5["bar_start_utc"].ge(stage_start)
            & m5["bar_start_utc"].lt(stage_end),
            "bar_start_utc",
        ].dt.date.nunique()
    )
    yearly = (
        trades.assign(
            year=pd.to_datetime(trades["entry_time"], utc=True).dt.year
        ).groupby("year", sort=True)["stress_net_r"].sum()
        if not trades.empty
        else pd.Series(dtype=float)
    )
    removed = values.drop(values.nlargest(min(top_winners, len(values))).index)
    segment_metrics: list[dict[str, Any]] = []
    for raw_start, raw_end in segments:
        start, end = pd.Timestamp(raw_start), pd.Timestamp(raw_end)
        segment = (
            trades.loc[
                trades["entry_time"].ge(start) & trades["entry_time"].lt(end)
            ]
            if not trades.empty
            else trades
        )
        segment_values = (
            segment["stress_net_r"].astype(float)
            if not segment.empty
            else pd.Series(dtype=float)
        )
        pf = profit_factor(segment_values)
        segment_metrics.append(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "trades": int(len(segment)),
                "net_r": float(segment_values.sum()),
                "stress_pf": pf,
                "profitable": bool(segment_values.sum() > 0.0),
            }
        )
    segment_pfs = [
        float(item["stress_pf"])
        if math.isfinite(float(item["stress_pf"]))
        else (float("inf") if item["net_r"] > 0.0 else 0.0)
        for item in segment_metrics
    ]
    return {
        "trades": int(len(trades)),
        "source_days": source_days,
        "trades_per_source_day": len(trades) / source_days if source_days else 0.0,
        "stress_net_r": float(values.sum()),
        "stress_pf": profit_factor(values),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "closed_drawdown_r": closed_drawdown(values),
        "positive_active_year_share": float((yearly > 0.0).mean())
        if len(yearly)
        else 0.0,
        "top_winners_removed_stress_net_r": float(removed.sum()),
        "trade_pvalue": one_sided_trade_pvalue(values),
        "profitable_segments": int(
            sum(bool(item["profitable"]) for item in segment_metrics)
        ),
        "worst_segment_pf": min(segment_pfs) if segment_pfs else 0.0,
        "segment_metrics": segment_metrics,
        "current_account_feasible_share": float(
            trades["current_account_feasible"].mean()
        )
        if not trades.empty
        else 0.0,
    }


def gate_checks(
    metrics: Mapping[str, Any], gate: Mapping[str, Any], holm_pvalue: float
) -> dict[str, bool]:
    return {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "minimum_trades_per_source_day": float(metrics["trades_per_source_day"])
        >= float(gate["minimum_trades_per_source_day"]),
        "minimum_stress_pf": float(metrics["stress_pf"])
        >= float(gate["minimum_stress_pf"]),
        "minimum_average_stress_r": float(metrics["average_stress_r"])
        >= float(gate["minimum_average_stress_r"]),
        "maximum_closed_drawdown_r": float(metrics["closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "minimum_positive_active_year_share": float(
            metrics["positive_active_year_share"]
        )
        >= float(gate["minimum_positive_active_year_share"]),
        "top_winners_removed_positive": float(
            metrics["top_winners_removed_stress_net_r"]
        )
        > 0.0,
        "minimum_profitable_segments": int(metrics["profitable_segments"])
        >= int(gate["minimum_profitable_segments"]),
        "minimum_worst_segment_pf": float(metrics["worst_segment_pf"])
        >= float(gate["minimum_worst_segment_pf"]),
        "maximum_holm_pvalue": float(holm_pvalue)
        <= float(gate["maximum_holm_pvalue"]),
    }
