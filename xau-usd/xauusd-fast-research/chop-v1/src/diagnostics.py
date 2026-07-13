from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from regime import atr


SEGMENTS = {
    "A": (pd.Timestamp("2016-07-01", tz="UTC"), pd.Timestamp("2022-12-31 23:59:59", tz="UTC")),
    "B": (pd.Timestamp("2023-01-01", tz="UTC"), pd.Timestamp("2024-12-31 23:59:59", tz="UTC")),
    "C": (pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2026-06-30 23:59:59", tz="UTC")),
}


def profit_factor(values: pd.Series) -> float | None:
    if values.empty:
        return None
    wins = float(values.loc[values > 0].sum())
    losses = float(-values.loc[values < 0].sum())
    return wins / losses if losses > 0 else (999.0 if wins > 0 else None)


def max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    equity = values.cumsum()
    return float((equity.cummax() - equity).max())


def _segment_rows(trades: pd.DataFrame, strategy: str, timeframe: str) -> list[dict[str, Any]]:
    rows = []
    for name, (start, end) in SEGMENTS.items():
        subset = trades.loc[(trades["entry_time"] >= start) & (trades["entry_time"] <= end)]
        rows.append({
            "strategy_id": strategy, "timeframe": timeframe, "segment": name,
            "start": start.isoformat(), "end": end.isoformat(), "trades": int(len(subset)),
            "net_r": float(subset["net_r"].sum()) if len(subset) else 0.0,
            "profit_factor": profit_factor(subset["net_r"]),
            "stress_net_r": float(subset["stress_net_r"].sum()) if len(subset) else 0.0,
        })
    return rows


def _decision(base: dict[str, Any], segments: dict[str, dict[str, Any]], subtype_rows: list[dict[str, Any]], yearly: pd.DataFrame) -> str:
    if base["baseline_net_r"] <= 0 or base["baseline_expectancy"] <= 0 or (base["baseline_profit_factor"] or 0) <= 1.0:
        return "REJECT"
    minimums = base["accepted_trades"] >= 100 and base["unique_setup_episodes"] >= 60 and base["chop_episodes_traded"] >= 40
    if not minimums:
        return "UNDERPOWERED"
    later_net = segments["B"]["net_r"] + segments["C"]["net_r"]
    later_pf = profit_factor(pd.Series([], dtype=float))
    # Combined later PF is reconstructed from the segment-level aggregate only in the caller's gate fields.
    positive_segments = sum(segments[name]["net_r"] > 0 for name in SEGMENTS)
    bad_subtype = any(row["trades"] >= 30 and (row["profit_factor"] or 0) < 0.85 for row in subtype_rows)
    yearly_positive = yearly.loc[yearly["net_r"] > 0, "net_r"]
    one_year_share = float(yearly_positive.max() / base["baseline_net_r"]) if len(yearly_positive) and base["baseline_net_r"] > 0 else 0.0
    all_gates = (
        (base["baseline_profit_factor"] or 0) >= 1.20
        and base["baseline_expectancy"] >= 0.08
        and later_net > 0
        and (base["later_profit_factor"] or 0) >= 1.10
        and positive_segments >= 2
        and base["stress_net_r"] > 0
        and (base["stress_profit_factor"] or 0) >= 1.05
        and base["max_closed_drawdown_r"] <= 20
        and base["top_ten_winner_share"] <= 0.50
        and one_year_share <= 0.50
        and not bad_subtype
    )
    return "PROMISING_CONFIRMATION_REQUIRED" if all_gates else "BORDERLINE_DO_NOT_ENGINEER"


def summarize_results(
    signals: pd.DataFrame,
    trades: pd.DataFrame,
    strategy_ids: tuple[str, ...],
    timeframes: tuple[str, ...],
    total_episodes: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matrix_rows: list[dict[str, Any]] = []
    subtype_rows: list[dict[str, Any]] = []
    yearly_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, Any]] = []
    subtype_columns = ("volatility_subtype", "range_width_subtype", "drift_subtype")
    for strategy in strategy_ids:
        for timeframe in timeframes:
            sig = signals.loc[(signals["strategy_id"] == strategy) & (signals["timeframe"] == timeframe)].copy()
            cell = trades.loc[(trades["strategy_id"] == strategy) & (trades["timeframe"] == timeframe)].copy()
            segments_list = _segment_rows(cell, strategy, timeframe)
            segment_rows.extend(segments_list)
            segment_map = {row["segment"]: row for row in segments_list}
            if len(cell):
                cell["year"] = cell["entry_time"].dt.year
            years = []
            for year, group in cell.groupby("year", sort=True) if len(cell) else []:
                row = {"strategy_id": strategy, "timeframe": timeframe, "year": int(year), "trades": int(len(group)), "net_r": float(group["net_r"].sum()), "profit_factor": profit_factor(group["net_r"])}
                yearly_rows.append(row); years.append(row)
            yearly = pd.DataFrame(years)
            cell_subtypes: list[dict[str, Any]] = []
            for column in subtype_columns:
                for subtype, group in cell.groupby(column, sort=True) if len(cell) else []:
                    row = {
                        "strategy_id": strategy, "timeframe": timeframe, "subtype_dimension": column,
                        "subtype": subtype, "trades": int(len(group)), "net_r": float(group["net_r"].sum()),
                        "profit_factor": profit_factor(group["net_r"]), "stress_net_r": float(group["stress_net_r"].sum()),
                    }
                    subtype_rows.append(row); cell_subtypes.append(row)
            net = cell["net_r"] if len(cell) else pd.Series(dtype=float)
            stress = cell["stress_net_r"] if len(cell) else pd.Series(dtype=float)
            wins, losses = net[net > 0], net[net < 0]
            gross_profit = float(wins.sum())
            top_five = float(wins.nlargest(5).sum() / gross_profit) if gross_profit > 0 else 0.0
            top_ten = float(wins.nlargest(10).sum() / gross_profit) if gross_profit > 0 else 0.0
            later = cell.loc[cell["entry_time"] >= SEGMENTS["B"][0]] if len(cell) else cell
            setup_count = int(cell[["direction", "setup_episode_id"]].drop_duplicates().shape[0]) if len(cell) else 0
            episode_count = int(cell["chop_episode_id"].nunique()) if len(cell) else 0
            base = {
                "strategy_id": strategy, "timeframe": timeframe,
                "total_raw_signals": int(len(sig)), "rejected_signals": int((~sig.get("signal_accepted", pd.Series(dtype=bool))).sum()) if len(sig) else 0,
                "accepted_trades": int(len(cell)), "unique_setup_episodes": setup_count,
                "chop_episodes_traded": episode_count, "total_chop_episodes": total_episodes,
                "chop_episode_coverage_pct": 100.0 * episode_count / total_episodes if total_episodes else 0.0,
                "long_trades": int((cell.get("direction") == "LONG").sum()) if len(cell) else 0,
                "short_trades": int((cell.get("direction") == "SHORT").sum()) if len(cell) else 0,
                "wins": int((net > 0).sum()), "losses": int((net < 0).sum()), "breakeven_trades": int((net == 0).sum()),
                "win_rate": float((net > 0).mean()) if len(net) else 0.0,
                "average_gross_win_r": float(cell.loc[cell["gross_r"] > 0, "gross_r"].mean()) if len(cell.loc[cell["gross_r"] > 0]) else 0.0,
                "average_gross_loss_r": float(cell.loc[cell["gross_r"] < 0, "gross_r"].mean()) if len(cell.loc[cell["gross_r"] < 0]) else 0.0,
                "realized_win_loss_ratio": float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) else 0.0,
                "baseline_gross_r": float(cell["gross_r"].sum()) if len(cell) else 0.0,
                "baseline_net_r": float(net.sum()), "baseline_profit_factor": profit_factor(net),
                "baseline_expectancy": float(net.mean()) if len(net) else 0.0,
                "expectancy_per_setup_episode": float(net.sum() / setup_count) if setup_count else 0.0,
                "stress_net_r": float(stress.sum()), "stress_profit_factor": profit_factor(stress),
                "max_closed_drawdown_r": max_drawdown(net),
                "approx_max_floating_drawdown_r": max_drawdown(net) + (float(cell["mae_r"].max()) if len(cell) else 0.0),
                "longest_losing_streak": _longest_streak(net < 0),
                "average_holding_minutes": float(cell["holding_minutes"].mean()) if len(cell) else 0.0,
                "median_holding_minutes": float(cell["holding_minutes"].median()) if len(cell) else 0.0,
                "active_weekdays": int(cell["entry_time"].dt.weekday.nunique()) if len(cell) else 0,
                "trades_per_year": float(len(cell) / max(1, cell["entry_time"].dt.year.nunique())) if len(cell) else 0.0,
                "ambiguous_trades": int(cell["ambiguous_bar"].sum()) if len(cell) else 0,
                "rollover_crossing_trades": int(cell["rollover_crossed"].sum()) if len(cell) else 0,
                "top_five_winner_share": top_five, "top_ten_winner_share": top_ten,
                "top_three_winning_days_share": _top_day_share(cell),
                "best_year": int(yearly.loc[yearly["net_r"].idxmax(), "year"]) if len(yearly) else None,
                "worst_year": int(yearly.loc[yearly["net_r"].idxmin(), "year"]) if len(yearly) else None,
                "positive_years": int((yearly.get("net_r", pd.Series(dtype=float)) > 0).sum()),
                "negative_years": int((yearly.get("net_r", pd.Series(dtype=float)) < 0).sum()),
                "segment_a_net_r": segment_map["A"]["net_r"], "segment_b_net_r": segment_map["B"]["net_r"], "segment_c_net_r": segment_map["C"]["net_r"],
                "later_net_r": float(later["net_r"].sum()) if len(later) else 0.0,
                "later_profit_factor": profit_factor(later["net_r"]) if len(later) else None,
                "illustrative_equity_return_pct_at_0p5pct_risk": float(net.sum() * 0.5),
            }
            base["decision_category"] = _decision(base, segment_map, cell_subtypes, yearly)
            for scenario in ("BASELINE", "STRESS"):
                row = dict(base); row["cost_scenario"] = scenario
                row["scenario_net_r"] = base["baseline_net_r"] if scenario == "BASELINE" else base["stress_net_r"]
                row["scenario_profit_factor"] = base["baseline_profit_factor"] if scenario == "BASELINE" else base["stress_profit_factor"]
                matrix_rows.append(row)
    return pd.DataFrame(matrix_rows), pd.DataFrame(subtype_rows), pd.DataFrame(yearly_rows), pd.DataFrame(segment_rows)


def _longest_streak(mask: pd.Series) -> int:
    best = current = 0
    for value in mask:
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def _top_day_share(trades: pd.DataFrame) -> float:
    if trades.empty:
        return 0.0
    by_day = trades.groupby(trades["entry_time"].dt.date)["net_r"].sum()
    positive = float(by_day.loc[by_day > 0].sum())
    return float(by_day.nlargest(3).sum() / positive) if positive > 0 else 0.0


def market_diagnostics(frame: pd.DataFrame, timeframe: str, timeframe_minutes: int, trades: pd.DataFrame, strategy_ids: tuple[str, ...]) -> pd.DataFrame:
    day = 1440 // timeframe_minutes
    equilibrium = frame["mid_close"].rolling(day, min_periods=day).median()
    deviation = frame["mid_close"].rolling(day, min_periods=day).std(ddof=0)
    zscore = (frame["mid_close"] - equilibrium) / deviation.replace(0.0, np.nan)
    atr14 = atr(frame, max(2, 14 * 60 // timeframe_minutes))
    boundary_probabilities = _boundary_return_probabilities(frame, equilibrium, zscore, atr14, timeframe_minutes)
    half_life_bars, variance_ratios = _episode_safe_mean_reversion(frame, equilibrium, timeframe_minutes)

    rows = []
    for strategy in strategy_ids:
        cell = trades.loc[(trades["strategy_id"] == strategy) & (trades["timeframe"] == timeframe)]
        costs = cell["cost_r"] if len(cell) else pd.Series(dtype=float)
        mfe, mae = cell.get("mfe_r", pd.Series(dtype=float)), cell.get("mae_r", pd.Series(dtype=float))
        rows.append({
            "strategy_id": strategy, "timeframe": timeframe,
            "median_cost_r": float(costs.median()) if len(costs) else None, "mean_cost_r": float(costs.mean()) if len(costs) else None,
            "p75_cost_r": float(costs.quantile(0.75)) if len(costs) else None, "p90_cost_r": float(costs.quantile(0.90)) if len(costs) else None,
            "p95_cost_r": float(costs.quantile(0.95)) if len(costs) else None,
            "half_life_bars": half_life_bars if np.isfinite(half_life_bars) else None,
            "half_life_minutes": half_life_bars * timeframe_minutes if np.isfinite(half_life_bars) else None,
            "half_life_hours": half_life_bars * timeframe_minutes / 60.0 if np.isfinite(half_life_bars) else None,
            **variance_ratios,
            "diagnostic_timing_basis": "EX_POST_EPISODE_SAFE_NOT_USED_FOR_TRADING_OR_GATES",
            "median_mfe_r": float(mfe.median()) if len(mfe) else None, "median_mae_r": float(mae.median()) if len(mae) else None,
            "mfe_mae_ratio": float(mfe.median() / mae.median()) if len(mfe) and mae.median() > 0 else None,
            "stopped_before_0p5r_pct": _stopped_before(cell, 0.5), "stopped_before_1r_pct": _stopped_before(cell, 1.0),
            "reached_1r_before_stop_pct": float((mfe >= 1.0).mean() * 100) if len(mfe) else 0.0,
            "reached_1p5r_before_stop_pct": float((mfe >= 1.5).mean() * 100) if len(mfe) else 0.0,
            "median_entry_delay_minutes": float(cell["entry_delay_minutes"].median()) if len(cell) else None,
            "regime_exit_within_3h_pct": _regime_exit_pct(cell, 180), "regime_exit_within_6h_pct": _regime_exit_pct(cell, 360),
            "regime_exit_within_12h_pct": _regime_exit_pct(cell, 720),
            **boundary_probabilities,
            "median_regime_hours_remaining_at_entry": _median_regime_hours_remaining(frame, cell, timeframe_minutes),
            "raw_trade_count": int(len(cell)),
            "setup_episode_count": int(cell[["direction", "setup_episode_id"]].drop_duplicates().shape[0]) if len(cell) else 0,
            "chop_episode_count": int(cell["chop_episode_id"].nunique()) if len(cell) else 0,
            "average_trades_per_setup_episode": float(len(cell) / cell[["direction", "setup_episode_id"]].drop_duplicates().shape[0]) if len(cell) else 0.0,
            "average_trades_per_chop_episode": float(len(cell) / cell["chop_episode_id"].nunique()) if len(cell) else 0.0,
        })
    return pd.DataFrame(rows)


def _episode_safe_mean_reversion(
    frame: pd.DataFrame, equilibrium: pd.Series, timeframe_minutes: int
) -> tuple[float, dict[str, float]]:
    expected = pd.Timedelta(minutes=timeframe_minutes)
    active = frame["chop_active"] & (frame["chop_episode_id"] > 0)
    same_previous = (
        active & active.shift(1, fill_value=False)
        & frame["chop_episode_id"].eq(frame["chop_episode_id"].shift(1))
        & frame["timestamp_utc"].sub(frame["timestamp_utc"].shift(1)).eq(expected)
    )
    x = np.log(frame["mid_close"]) - np.log(equilibrium)
    lag, delta = x.shift(1), x.diff()
    valid = same_previous & np.isfinite(lag) & np.isfinite(delta)
    half_life_bars = np.nan
    if valid.sum() > 20:
        design = np.column_stack([np.ones(valid.sum()), lag.loc[valid].to_numpy()])
        b = float(np.linalg.lstsq(design, delta.loc[valid].to_numpy(), rcond=None)[0][1])
        phi = 1.0 + b
        if 0 < phi < 1:
            half_life_bars = float(-np.log(2) / np.log(phi))
    log_close = np.log(frame["mid_close"])
    returns = log_close.diff().loc[same_previous].dropna()
    variance_ratios = {}
    one_var = float(returns.var(ddof=1))
    for hours in (1, 4, 8):
        q = max(1, hours * 60 // timeframe_minutes)
        same_q = (
            active & active.shift(q, fill_value=False)
            & frame["chop_episode_id"].eq(frame["chop_episode_id"].shift(q))
            & frame["timestamp_utc"].sub(frame["timestamp_utc"].shift(q)).eq(expected * q)
        )
        q_returns = log_close.sub(log_close.shift(q)).loc[same_q].dropna()
        variance_ratios[f"variance_ratio_{hours}h"] = float(q_returns.var(ddof=1) / (q * one_var)) if one_var > 0 and len(q_returns) else np.nan
    return half_life_bars, variance_ratios


def _boundary_return_probabilities(
    frame: pd.DataFrame,
    equilibrium: pd.Series,
    zscore: pd.Series,
    atr14: pd.Series,
    timeframe_minutes: int,
) -> dict[str, float | int | None]:
    """Measure equilibrium return before a further one-ATR extension, with no signal filtering."""
    horizon = max(1, 12 * 60 // timeframe_minutes)
    results: dict[str, float | int | None] = {}
    for threshold, label in ((1.0, "1sd"), (1.5, "1p5sd"), (2.0, "2sd")):
        excursion = (
            frame["chop_active"]
            & (zscore.abs() >= threshold)
            & (zscore.abs().shift(1) < threshold)
            & equilibrium.notna()
            & atr14.notna()
        )
        outcomes: list[bool] = []
        for index in np.flatnonzero(excursion.to_numpy()):
            direction = 1 if zscore.iloc[index] > 0 else -1
            center = float(equilibrium.iloc[index])
            extension = float(frame["mid_close"].iloc[index] + direction * atr14.iloc[index])
            episode = int(frame["chop_episode_id"].iloc[index])
            horizon_end = frame["timestamp_utc"].iloc[index] + pd.Timedelta(hours=12)
            returned = False
            for future in range(index + 1, min(len(frame), index + horizon + 1)):
                if frame["timestamp_utc"].iloc[future] > horizon_end:
                    break
                if not bool(frame["chop_active"].iloc[future]) or int(frame["chop_episode_id"].iloc[future]) != episode:
                    break
                if direction > 0:
                    if float(frame["mid_low"].iloc[future]) <= center:
                        returned = True
                        break
                    if float(frame["mid_high"].iloc[future]) >= extension:
                        break
                else:
                    if float(frame["mid_high"].iloc[future]) >= center:
                        returned = True
                        break
                    if float(frame["mid_low"].iloc[future]) <= extension:
                        break
            outcomes.append(returned)
        results[f"boundary_events_{label}"] = len(outcomes)
        results[f"equilibrium_return_before_1atr_extension_{label}_pct"] = (
            100.0 * float(np.mean(outcomes)) if outcomes else None
        )
    return results


def _median_regime_hours_remaining(frame: pd.DataFrame, cell: pd.DataFrame, timeframe_minutes: int) -> float | None:
    if cell.empty:
        return None
    active = frame.loc[frame["chop_active"], ["timestamp_utc", "chop_episode_id"]].copy()
    active["episode_last_bar"] = active.groupby("chop_episode_id")["timestamp_utc"].transform("max")
    lookup = pd.merge_asof(
        cell[["entry_time"]].sort_values("entry_time"), active.sort_values("timestamp_utc"),
        left_on="entry_time", right_on="timestamp_utc", direction="backward",
    )
    remaining = (lookup["episode_last_bar"] + pd.Timedelta(minutes=timeframe_minutes) - lookup["entry_time"]).dt.total_seconds() / 3600.0
    remaining = remaining.loc[remaining >= 0]
    return float(remaining.median()) if len(remaining) else None


def _stopped_before(cell: pd.DataFrame, threshold: float) -> float:
    if cell.empty:
        return 0.0
    return float(((cell["exit_reason"].isin(["STOP", "AMBIGUOUS_BAR_STOP_FIRST"])) & (cell["mfe_r"] < threshold)).mean() * 100)


def _regime_exit_pct(cell: pd.DataFrame, minutes: int) -> float:
    if cell.empty:
        return 0.0
    return float(((cell["exit_reason"] == "REGIME_EXIT") & (cell["holding_minutes"] <= minutes)).mean() * 100)
