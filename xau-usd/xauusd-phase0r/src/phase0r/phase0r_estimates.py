from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from phase0r.candidate_registry import selected_candidates
from phase0r.cost_feasibility import DEFAULT_SPREAD_ASSUMPTIONS


CELL_WINDOWS = {
    1: ("2016-01-01T00:00:00Z", "2018-12-31T23:59:59Z", "capital_com", "best_case"),
    2: ("2016-01-01T00:00:00Z", "2018-12-31T23:59:59Z", "capital_com", "median"),
    3: ("2016-01-01T00:00:00Z", "2018-12-31T23:59:59Z", "capital_com", "p95"),
    4: ("2019-01-01T00:00:00Z", "2021-12-31T23:59:59Z", "pepperstone", "best_case"),
    5: ("2019-01-01T00:00:00Z", "2021-12-31T23:59:59Z", "pepperstone", "median"),
    6: ("2019-01-01T00:00:00Z", "2021-12-31T23:59:59Z", "pepperstone", "p95"),
    7: ("2022-01-01T00:00:00Z", "2024-12-31T23:59:59Z", "dukascopy", "best_case"),
    8: ("2022-01-01T00:00:00Z", "2024-12-31T23:59:59Z", "dukascopy", "median"),
    9: ("2022-01-01T00:00:00Z", "2024-12-31T23:59:59Z", "dukascopy", "p95"),
}

POINT_SIZE = 0.01
FIXED_RISK_USD = 50.0
MEASURED_MEDIAN_SPREAD_POINTS = DEFAULT_SPREAD_ASSUMPTIONS.measured_median_spread_points
MEASURED_P95_SPREAD_POINTS = DEFAULT_SPREAD_ASSUMPTIONS.measured_p95_spread_points


@dataclass(frozen=True)
class Phase0REstimateOutput:
    report_path: Path
    summary_path: Path
    trade_paths: tuple[Path, ...]
    summary_rows: tuple[dict[str, Any], ...]


def run_phase0r_estimates(
    phase0r_root: Path,
    phase0_root: Path,
    candidate_id: str = "all",
    measured_cost: str = "p95",
) -> Phase0REstimateOutput:
    phase0r_root = phase0r_root.resolve()
    phase0_root = phase0_root.resolve()
    output_dir = phase0r_root / "outputs" / "estimate_results"
    report_dir = phase0r_root / "outputs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    cost_spread_points = _cost_spread_points(measured_cost)
    summary_rows: list[dict[str, Any]] = []
    trade_paths: list[Path] = []
    for candidate in selected_candidates(candidate_id):
        candidate_trades: list[dict[str, Any]] = []
        for cell_id, (start_text, end_text, broker, cost_model) in CELL_WINDOWS.items():
            start = pd.Timestamp(start_text)
            end = pd.Timestamp(end_text)
            context = _load_context(phase0_root, broker)
            signals = _generate_signals(candidate.candidate_id, context, start, end)
            trades = _simulate_signals(
                candidate.candidate_id,
                signals,
                context["H4"],
                cell_id=cell_id,
                broker=broker,
                cost_model=cost_model,
                measured_cost=measured_cost,
                cost_spread_points=cost_spread_points,
            )
            candidate_trades.extend(trades)
            summary_rows.append(
                _summary_row(
                    candidate.candidate_id,
                    trades,
                    cell_id=cell_id,
                    broker=broker,
                    cost_model=cost_model,
                    period=f"{start.date()} to {end.date()}",
                    measured_cost=measured_cost,
                    level="cell",
                )
            )

        trade_path = output_dir / f"{candidate.candidate_id}_estimate_trades.csv"
        _write_trades(trade_path, candidate_trades)
        trade_paths.append(trade_path)
        unique_candidate_trades = _dedupe_trades(candidate_trades)
        summary_rows.append(
            _summary_row(
                candidate.candidate_id,
                unique_candidate_trades,
                cell_id="all",
                broker="mixed",
                cost_model="measured",
                period="2016-01-01 to 2024-12-31",
                measured_cost=measured_cost,
                level="overall",
            )
        )

    summary_path = output_dir / "phase0r_estimate_summary.csv"
    _write_summary(summary_path, summary_rows)
    report_path = report_dir / "PHASE0R_ESTIMATE_REPORT.md"
    report_path.write_text(_render_report(summary_rows, trade_paths, measured_cost), encoding="utf-8")
    return Phase0REstimateOutput(
        report_path=report_path,
        summary_path=summary_path,
        trade_paths=tuple(trade_paths),
        summary_rows=tuple(summary_rows),
    )


def _load_context(phase0_root: Path, broker: str) -> dict[str, pd.DataFrame]:
    return {
        "H4": _load_bars(phase0_root, broker, "H4"),
        "D1": _load_bars(phase0_root, broker, "D1"),
    }


def _load_bars(phase0_root: Path, broker: str, timeframe: str) -> pd.DataFrame:
    bars_dir = phase0_root / "data" / "processed" / "bars" / broker / "XAUUSD" / timeframe
    files = sorted(bars_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No {broker} XAUUSD {timeframe} processed bars found in {bars_dir}")
    frame = pd.concat((pd.read_csv(path) for path in files), ignore_index=True)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "open", "high", "low", "close"])
    frame = frame.sort_values("timestamp_utc").drop_duplicates("timestamp_utc").reset_index(drop=True)
    return frame


def _generate_signals(
    candidate_id: str,
    context: dict[str, pd.DataFrame],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> list[dict[str, Any]]:
    h4 = _with_h4_features(context["H4"])
    d1 = _with_d1_features(context["D1"])
    if candidate_id == "d1_compression_h4_expansion_v0":
        return _signals_d1_compression_h4_expansion(h4, d1, start, end)
    if candidate_id == "h4_trend_pullback_d1_bias_v0":
        return _signals_h4_trend_pullback_d1_bias(h4, d1, start, end)
    if candidate_id == "weekly_level_h4_rejection_v0":
        weekly = _weekly_from_d1(d1)
        return _signals_weekly_level_h4_rejection(h4, weekly, start, end)
    raise KeyError(f"Unsupported estimate candidate {candidate_id!r}")


def _with_h4_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["atr14"] = _atr(result, 14)
    result["ema21"] = result["close"].ewm(span=21, adjust=False, min_periods=21).mean()
    result["ema50"] = result["close"].ewm(span=50, adjust=False, min_periods=50).mean()
    result["range"] = result["high"] - result["low"]
    result["body"] = (result["close"] - result["open"]).abs()
    result["close_position"] = (result["close"] - result["low"]) / result["range"].replace(0, pd.NA)
    return result


def _with_d1_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["atr14"] = _atr(result, 14)
    result["atr14_percentile_252"] = result["atr14"].rolling(252, min_periods=252).apply(
        lambda values: float((values <= values[-1]).sum()) / float(len(values)) * 100.0,
        raw=True,
    )
    result["range"] = result["high"] - result["low"]
    result["range20_median"] = result["range"].rolling(20, min_periods=20).median()
    result["box_high_5"] = result["high"].rolling(5, min_periods=5).max()
    result["box_low_5"] = result["low"].rolling(5, min_periods=5).min()
    result["range5_average"] = (result["box_high_5"] - result["box_low_5"]) / 5.0
    result["ema50"] = result["close"].ewm(span=50, adjust=False, min_periods=50).mean()
    result["ema200"] = result["close"].ewm(span=200, adjust=False, min_periods=200).mean()
    result["ema50_slope_20"] = result["ema50"] - result["ema50"].shift(20)
    return result


def _atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous_close = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(period, min_periods=period).mean()


def _signals_d1_compression_h4_expansion(
    h4: pd.DataFrame,
    d1: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    d1_times = d1["timestamp_utc"].astype("int64").to_numpy()
    used_boxes: set[tuple[int, str]] = set()
    for h4_index, row in h4.iterrows():
        timestamp = row["timestamp_utc"]
        if timestamp < start or timestamp > end:
            continue
        d1_index = _latest_index(d1_times, timestamp)
        if d1_index is None:
            continue
        d1_row = d1.iloc[d1_index]
        required = (
            d1_row["atr14_percentile_252"],
            d1_row["range5_average"],
            d1_row["range20_median"],
            d1_row["box_high_5"],
            d1_row["box_low_5"],
            row["atr14"],
            row["range"],
            row["body"],
        )
        if not _available(*required):
            continue
        if float(d1_row["atr14_percentile_252"]) > 30.0:
            continue
        if float(d1_row["range5_average"]) > float(d1_row["range20_median"]):
            continue
        if float(row["range"]) <= 0.0 or float(row["body"]) / float(row["range"]) < 0.50:
            continue

        box_high = float(d1_row["box_high_5"])
        box_low = float(d1_row["box_low_5"])
        close = float(row["close"])
        direction = ""
        if close > box_high and close > float(row["open"]):
            direction = "LONG"
        elif close < box_low and close < float(row["open"]):
            direction = "SHORT"
        if not direction:
            continue
        box_key = (int(d1_index), direction)
        if box_key in used_boxes:
            continue
        used_boxes.add(box_key)

        h4_atr = float(row["atr14"])
        if direction == "LONG":
            risk = max(close - box_low, h4_atr)
            sl = close - risk
            tp15 = close + 1.5 * risk
            tp20 = close + 2.0 * risk
        else:
            risk = max(box_high - close, h4_atr)
            sl = close + risk
            tp15 = close - 1.5 * risk
            tp20 = close - 2.0 * risk
        signals.append(
            _signal(
                "d1_compression_h4_expansion_v0",
                h4_index,
                timestamp,
                direction,
                close,
                sl,
                tp15,
                tp20,
                "D1_COMPRESSION_H4_EXPANSION",
                d1_atr_percentile=float(d1_row["atr14_percentile_252"]),
                box_high=box_high,
                box_low=box_low,
            )
        )
    return signals


def _signals_h4_trend_pullback_d1_bias(
    h4: pd.DataFrame,
    d1: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    d1_times = d1["timestamp_utc"].astype("int64").to_numpy()
    for h4_index, row in h4.iterrows():
        timestamp = row["timestamp_utc"]
        if timestamp < start or timestamp > end:
            continue
        d1_index = _latest_index(d1_times, timestamp)
        if d1_index is None:
            continue
        d1_row = d1.iloc[d1_index]
        required = (
            d1_row["ema50"],
            d1_row["ema200"],
            d1_row["ema50_slope_20"],
            row["ema21"],
            row["ema50"],
            row["atr14"],
            row["range"],
            row["close_position"],
        )
        if not _available(*required):
            continue
        long_bias = float(d1_row["ema50"]) > float(d1_row["ema200"]) and float(d1_row["ema50_slope_20"]) > 0
        short_bias = float(d1_row["ema50"]) < float(d1_row["ema200"]) and float(d1_row["ema50_slope_20"]) < 0
        if not long_bias and not short_bias:
            continue

        h4_atr = float(row["atr14"])
        close = float(row["close"])
        low = float(row["low"])
        high = float(row["high"])
        distance_ref = low if long_bias else high
        pullback_distance = min(abs(distance_ref - float(row["ema21"])), abs(distance_ref - float(row["ema50"])))
        if pullback_distance > 0.5 * h4_atr:
            continue
        if long_bias and close <= float(d1_row["ema200"]):
            continue
        if short_bias and close >= float(d1_row["ema200"]):
            continue

        close_position = float(row["close_position"])
        long_confirmation = long_bias and close > float(row["open"]) and close_position >= 0.65
        short_confirmation = short_bias and close < float(row["open"]) and close_position <= 0.35
        if not long_confirmation and not short_confirmation:
            continue

        recent = h4.iloc[max(0, h4_index - 4) : h4_index + 1]
        if long_confirmation:
            direction = "LONG"
            sl = float(recent["low"].min()) - 0.25 * h4_atr
            risk = close - sl
            tp15 = close + 1.5 * risk
            tp20 = close + 2.0 * risk
        else:
            direction = "SHORT"
            sl = float(recent["high"].max()) + 0.25 * h4_atr
            risk = sl - close
            tp15 = close - 1.5 * risk
            tp20 = close - 2.0 * risk
        if risk <= 0.0:
            continue
        signals.append(
            _signal(
                "h4_trend_pullback_d1_bias_v0",
                h4_index,
                timestamp,
                direction,
                close,
                sl,
                tp15,
                tp20,
                "H4_TREND_PULLBACK_D1_BIAS",
                d1_ema50=float(d1_row["ema50"]),
                d1_ema200=float(d1_row["ema200"]),
                h4_atr=h4_atr,
            )
        )
    return signals


def _signals_weekly_level_h4_rejection(
    h4: pd.DataFrame,
    weekly: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    weekly_times = weekly["timestamp_utc"].astype("int64").to_numpy()
    for h4_index, row in h4.iterrows():
        timestamp = row["timestamp_utc"]
        if timestamp < start or timestamp > end:
            continue
        weekly_index = _latest_index(weekly_times, timestamp)
        if weekly_index is None or weekly_index < 0:
            continue
        weekly_row = weekly.iloc[weekly_index]
        prior4 = weekly.iloc[max(0, weekly_index - 3) : weekly_index + 1]
        levels = (
            ("previous_week_high", float(weekly_row["high"]), "SHORT"),
            ("previous_week_low", float(weekly_row["low"]), "LONG"),
            ("prior_4_week_high", float(prior4["high"].max()), "SHORT"),
            ("prior_4_week_low", float(prior4["low"].min()), "LONG"),
        )
        required = (row["atr14"], row["range"], row["open"], row["high"], row["low"], row["close"])
        if not _available(*required):
            continue
        h4_atr = float(row["atr14"])
        high = float(row["high"])
        low = float(row["low"])
        open_price = float(row["open"])
        close = float(row["close"])
        body = max(abs(close - open_price), POINT_SIZE)
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low
        zone = 0.25 * h4_atr
        for level_name, level_price, direction in levels:
            if direction == "SHORT":
                touched = high >= level_price - zone and low <= level_price + zone
                rejected = upper_wick >= 1.5 * body and close < level_price
                if not touched or not rejected:
                    continue
                sl = high + 0.25 * h4_atr
                risk = sl - close
                tp15 = close - 1.5 * risk
                tp20 = close - 2.0 * risk
            else:
                touched = low <= level_price + zone and high >= level_price - zone
                rejected = lower_wick >= 1.5 * body and close > level_price
                if not touched or not rejected:
                    continue
                sl = low - 0.25 * h4_atr
                risk = close - sl
                tp15 = close + 1.5 * risk
                tp20 = close + 2.0 * risk
            if risk <= 0.0:
                continue
            signals.append(
                _signal(
                    "weekly_level_h4_rejection_v0",
                    h4_index,
                    timestamp,
                    direction,
                    close,
                    sl,
                    tp15,
                    tp20,
                    "WEEKLY_LEVEL_H4_REJECTION",
                    level_name=level_name,
                    level_price=level_price,
                    h4_atr=h4_atr,
                )
            )
            break
    return signals


def _weekly_from_d1(d1: pd.DataFrame) -> pd.DataFrame:
    temp = d1.copy()
    temp["week"] = temp["timestamp_utc"].dt.tz_convert(None).dt.to_period("W-SUN")
    grouped = temp.groupby("week", sort=True)
    weekly = grouped.agg(
        timestamp_utc=("timestamp_utc", "max"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
    ).reset_index(drop=True)
    weekly["timestamp_utc"] = pd.to_datetime(weekly["timestamp_utc"], utc=True)
    return weekly


def _signal(
    candidate_id: str,
    h4_index: int,
    timestamp: pd.Timestamp,
    direction: str,
    entry: float,
    sl: float,
    tp15: float,
    tp20: float,
    reason_code: str,
    **metadata: float | str,
) -> dict[str, Any]:
    stop_distance_points = abs(entry - sl) / POINT_SIZE
    return {
        "candidate_id": candidate_id,
        "h4_index": int(h4_index),
        "signal_time_utc": timestamp,
        "direction": direction,
        "entry_price": entry,
        "stop_loss": sl,
        "take_profit_1_5r": tp15,
        "take_profit_2_0r": tp20,
        "stop_distance_points": stop_distance_points,
        "reason_code": reason_code,
        "metadata": metadata,
    }


def _simulate_signals(
    candidate_id: str,
    signals: list[dict[str, Any]],
    h4: pd.DataFrame,
    *,
    cell_id: int,
    broker: str,
    cost_model: str,
    measured_cost: str,
    cost_spread_points: float,
) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    open_until_index = -1
    max_hold_bars = _max_hold_bars(candidate_id)
    for signal in signals:
        start_index = int(signal["h4_index"]) + 1
        if start_index <= open_until_index:
            continue
        if start_index >= len(h4):
            continue
        entry = float(signal["entry_price"])
        sl = float(signal["stop_loss"])
        tp = float(signal["take_profit_1_5r"])
        direction = str(signal["direction"])
        risk = abs(entry - sl)
        if risk <= 0.0:
            continue
        exit_index = min(start_index + max_hold_bars - 1, len(h4) - 1)
        gross_r = 0.0
        exit_reason = "MAX_HOLD_EXIT"
        exit_price = float(h4.iloc[exit_index]["close"])
        for row_index in range(start_index, exit_index + 1):
            row = h4.iloc[row_index]
            high = float(row["high"])
            low = float(row["low"])
            if direction == "LONG":
                stop_hit = low <= sl
                target_hit = high >= tp
                if stop_hit and target_hit:
                    gross_r = -1.0
                    exit_price = sl
                    exit_reason = "STOP_ADVERSE_FIRST"
                    exit_index = row_index
                    break
                if stop_hit:
                    gross_r = -1.0
                    exit_price = sl
                    exit_reason = "STOP"
                    exit_index = row_index
                    break
                if target_hit:
                    gross_r = 1.5
                    exit_price = tp
                    exit_reason = "TARGET_1_5R"
                    exit_index = row_index
                    break
            else:
                stop_hit = high >= sl
                target_hit = low <= tp
                if stop_hit and target_hit:
                    gross_r = -1.0
                    exit_price = sl
                    exit_reason = "STOP_ADVERSE_FIRST"
                    exit_index = row_index
                    break
                if stop_hit:
                    gross_r = -1.0
                    exit_price = sl
                    exit_reason = "STOP"
                    exit_index = row_index
                    break
                if target_hit:
                    gross_r = 1.5
                    exit_price = tp
                    exit_reason = "TARGET_1_5R"
                    exit_index = row_index
                    break
        else:
            if direction == "LONG":
                gross_r = (exit_price - entry) / risk
            else:
                gross_r = (entry - exit_price) / risk

        stop_points = float(signal["stop_distance_points"])
        cost_r_median = MEASURED_MEDIAN_SPREAD_POINTS / stop_points if stop_points > 0 else 0.0
        cost_r_p95 = MEASURED_P95_SPREAD_POINTS / stop_points if stop_points > 0 else 0.0
        applied_cost_r = cost_spread_points / stop_points if stop_points > 0 else 0.0
        net_r = gross_r - applied_cost_r
        open_until_index = exit_index
        trades.append(
            {
                "candidate_id": candidate_id,
                "cell_id": cell_id,
                "broker": broker,
                "cost_model": cost_model,
                "measured_cost": measured_cost,
                "signal_time_utc": _iso(signal["signal_time_utc"]),
                "entry_time_utc": _iso(h4.iloc[start_index]["timestamp_utc"]),
                "exit_time_utc": _iso(h4.iloc[exit_index]["timestamp_utc"]),
                "direction": direction,
                "entry_price": round(entry, 5),
                "stop_loss": round(sl, 5),
                "take_profit_1_5r": round(tp, 5),
                "take_profit_2_0r": round(float(signal["take_profit_2_0r"]), 5),
                "exit_price": round(exit_price, 5),
                "stop_distance_points": round(stop_points, 2),
                "gross_r": round(gross_r, 6),
                "cost_r_median": round(cost_r_median, 6),
                "cost_r_p95": round(cost_r_p95, 6),
                "applied_cost_r": round(applied_cost_r, 6),
                "net_r": round(net_r, 6),
                "estimated_net_pnl_usd": round(net_r * FIXED_RISK_USD, 2),
                "exit_reason": exit_reason,
                "reason_code": signal["reason_code"],
            }
        )
    return trades


def _summary_row(
    candidate_id: str,
    trades: list[dict[str, Any]],
    *,
    cell_id: int | str,
    broker: str,
    cost_model: str,
    period: str,
    measured_cost: str,
    level: str,
) -> dict[str, Any]:
    net_values = [float(trade["net_r"]) for trade in trades]
    gross_values = [float(trade["gross_r"]) for trade in trades]
    wins = [value for value in net_values if value > 0]
    losses = [value for value in net_values if value < 0]
    profit_sum = sum(wins)
    loss_sum = abs(sum(losses))
    pf = None if loss_sum == 0 else profit_sum / loss_sum
    max_dd = _max_drawdown(net_values)
    trade_count = len(trades)
    return {
        "candidate_id": candidate_id,
        "level": level,
        "cell_id": cell_id,
        "broker": broker,
        "cost_model": cost_model,
        "period": period,
        "measured_cost": measured_cost,
        "trade_count": trade_count,
        "win_rate_pct": round((len(wins) / trade_count * 100.0), 2) if trade_count else 0.0,
        "gross_expectancy_r": round(sum(gross_values) / trade_count, 6) if trade_count else 0.0,
        "net_expectancy_r": round(sum(net_values) / trade_count, 6) if trade_count else 0.0,
        "total_net_r": round(sum(net_values), 6),
        "estimated_net_pnl_usd": round(sum(net_values) * FIXED_RISK_USD, 2),
        "profit_factor": None if pf is None else round(pf, 6),
        "max_drawdown_r": round(max_dd, 6),
        "median_stop_points": round(_median([float(trade["stop_distance_points"]) for trade in trades]), 2)
        if trades
        else 0.0,
        "median_applied_cost_r": round(_median([float(trade["applied_cost_r"]) for trade in trades]), 6)
        if trades
        else 0.0,
    }


def _write_trades(path: Path, trades: list[dict[str, Any]]) -> None:
    fields = [
        "candidate_id",
        "cell_id",
        "broker",
        "cost_model",
        "measured_cost",
        "signal_time_utc",
        "entry_time_utc",
        "exit_time_utc",
        "direction",
        "entry_price",
        "stop_loss",
        "take_profit_1_5r",
        "take_profit_2_0r",
        "exit_price",
        "stop_distance_points",
        "gross_r",
        "cost_r_median",
        "cost_r_p95",
        "applied_cost_r",
        "net_r",
        "estimated_net_pnl_usd",
        "exit_reason",
        "reason_code",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(trades)


def _dedupe_trades(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[object, ...]] = set()
    for trade in trades:
        key = (
            trade["candidate_id"],
            trade["broker"],
            trade["signal_time_utc"],
            trade["direction"],
            trade["entry_price"],
            trade["stop_loss"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(trade)
    return deduped


def _write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "candidate_id",
        "level",
        "cell_id",
        "broker",
        "cost_model",
        "period",
        "measured_cost",
        "trade_count",
        "win_rate_pct",
        "gross_expectancy_r",
        "net_expectancy_r",
        "total_net_r",
        "estimated_net_pnl_usd",
        "profit_factor",
        "max_drawdown_r",
        "median_stop_points",
        "median_applied_cost_r",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _render_report(rows: list[dict[str, Any]], trade_paths: list[Path], measured_cost: str) -> str:
    overall = [row for row in rows if row["level"] == "overall"]
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [
        "# Phase 0R Estimate Report",
        "",
        f"Generated at UTC: {generated_at}",
        f"Measured cost applied: {measured_cost}",
        "",
        "Status: ESTIMATE_ONLY_NOT_PHASE0R_GATE",
        "",
        "These results are draft estimates from existing processed bars. They are not Phase 0R promotion results, not paper-mode authorization, and not live-trading evidence.",
        "",
        "Assumptions:",
        "",
        f"- Fixed risk for estimated P/L: ${FIXED_RISK_USD:.2f} per 1R",
        "- Execution: theoretical H4 close entry, H4 adverse-first stop/target simulation",
        "- Target used for scoring: 1.5R",
        "- Cost model: measured spread cost subtracted in R",
        "- Overall rows dedupe repeated Phase 0 matrix cost-cell labels when the same measured cost is applied",
        "",
        "## Overall Estimates",
        "",
        "| candidate_id | trades | win_rate_pct | net_expectancy_R | total_net_R | estimated_net_PnL_USD | profit_factor | max_drawdown_R | median_stop_points | median_cost_R |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in overall:
        lines.append(
            "| "
            f"{row['candidate_id']} | "
            f"{row['trade_count']} | "
            f"{row['win_rate_pct']:.2f} | "
            f"{row['net_expectancy_r']:.4f} | "
            f"{row['total_net_r']:.2f} | "
            f"{row['estimated_net_pnl_usd']:.2f} | "
            f"{_display(row['profit_factor'])} | "
            f"{row['max_drawdown_r']:.2f} | "
            f"{row['median_stop_points']:.2f} | "
            f"{row['median_applied_cost_r']:.4f} |"
        )
    lines.extend(["", "## Cell Estimates", ""])
    lines.extend(
        [
            "| candidate_id | cell | broker | period | trades | win_rate_pct | net_expectancy_R | total_net_R | profit_factor | max_drawdown_R |",
            "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        if row["level"] != "cell":
            continue
        lines.append(
            "| "
            f"{row['candidate_id']} | "
            f"{row['cell_id']} | "
            f"{row['broker']} | "
            f"{row['period']} | "
            f"{row['trade_count']} | "
            f"{row['win_rate_pct']:.2f} | "
            f"{row['net_expectancy_r']:.4f} | "
            f"{row['total_net_r']:.2f} | "
            f"{_display(row['profit_factor'])} | "
            f"{row['max_drawdown_r']:.2f} |"
        )
    lines.extend(["", "## Trade Ledgers", ""])
    for path in trade_paths:
        lines.append(f"- {path}")
    lines.append("")
    return "\n".join(lines)


def _latest_index(times: Any, timestamp: pd.Timestamp) -> int | None:
    position = int(times.searchsorted(pd.Timestamp(timestamp).value, side="right")) - 1
    if position < 0:
        return None
    return position


def _available(*values: object) -> bool:
    return all(pd.notna(value) for value in values)


def _max_hold_bars(candidate_id: str) -> int:
    if candidate_id == "h4_trend_pullback_d1_bias_v0":
        return 18
    if candidate_id == "weekly_level_h4_rejection_v0":
        return 30
    return 36


def _cost_spread_points(measured_cost: str) -> float:
    if measured_cost == "median":
        return MEASURED_MEDIAN_SPREAD_POINTS
    if measured_cost == "p95":
        return MEASURED_P95_SPREAD_POINTS
    raise ValueError("measured_cost must be 'median' or 'p95'")


def _max_drawdown(values: list[float]) -> float:
    peak = 0.0
    equity = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _iso(value: pd.Timestamp) -> str:
    return pd.Timestamp(value).isoformat().replace("+00:00", "Z")


def _display(value: object) -> str:
    if value is None or value == "":
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
