from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from run_a3_net_cost_deduped_rebaseline import significance_summary
from run_a3_signal_quality_offline_discovery import (
    Bar,
    body_to_range,
    close_location,
    fmt_time,
    max_drawdown,
    parse_time,
    percentile,
    profit_factor,
    write_csv,
    write_json,
)


CANDIDATE_ID = "eurusd_h4_swing_trend_continuation_pullback_v0"
SYMBOL = "EURUSD"
BROKER = "capital_com"
POINT = 0.00001
ENTRY_SLIPPAGE_POINTS = 1.0
STOP_OR_TIME_EXIT_SLIPPAGE_POINTS = 3.0
STRESS_ENTRY_SLIPPAGE_POINTS = 2.0
STRESS_STOP_OR_TIME_EXIT_SLIPPAGE_POINTS = 5.0
LONG_SWAP_PERCENT = -0.00813
SHORT_SWAP_PERCENT = -0.00009
SWAP_STRESS_MULTIPLIER = 1.25
MAX_TRADE_COST_R = 0.12
P95_TOTAL_COST_R_LIMIT = 0.05
DISCOVERY_MIN_EXPECTANCY_R = 0.10
DISCOVERY_MIN_PF = 1.25
MAX_DRAWDOWN_R = 8.0
MIN_CLOSED_TRADES = 100
MIN_LONG_TRADES = 25
MIN_SHORT_TRADES = 25

DEFAULT_H4 = Path("..") / "xauusd-phase0" / "data" / "processed" / "bars" / BROKER / SYMBOL / "H4" / "EURUSD_capital_com_H4_20160104_20250701.csv"
DEFAULT_D1 = Path("..") / "xauusd-phase0" / "data" / "processed" / "bars" / BROKER / SYMBOL / "D1" / "EURUSD_capital_com_D1_20160104_20250701.csv"
DEFAULT_DUKASCOPY_H4 = Path("..") / "xauusd-phase0" / "data" / "processed" / "bars" / "dukascopy" / SYMBOL / "H4" / "EURUSD_dukascopy_H4_20160101_20250630_derived_from_m5.csv"
DEFAULT_DUKASCOPY_D1 = Path("..") / "xauusd-phase0" / "data" / "processed" / "bars" / "dukascopy" / SYMBOL / "D1" / "EURUSD_dukascopy_D1_20160101_20250630_derived_from_m5.csv"
DEFAULT_HYPOTHESIS = Path("..") / "xauusd-phase0r" / "hypotheses" / "hypothesis_eurusd_h4_swing_trend_continuation_pullback_v0.md"
DEFAULT_HASH_MANIFEST = Path("..") / "xauusd-phase0r" / "outputs" / "hypothesis_hash_manifest.csv"
DEFAULT_SWAP_JSON = Path("..") / "xauusd-phase0r" / "outputs" / "reports" / "EURUSD_CAPITAL_COM_SWAP_MODEL_2026_06_19.json"
DEFAULT_OUTPUT_JSON = Path("..") / "xauusd-phase0r" / "outputs" / "reports" / "EURUSD_H4_SWING_TREND_CONTINUATION_PULLBACK_V0_SCREEN_2026_06_19.json"
DEFAULT_OUTPUT_MD = Path("..") / "xauusd-phase0r" / "outputs" / "reports" / "EURUSD_H4_SWING_TREND_CONTINUATION_PULLBACK_V0_SCREEN_2026_06_19.md"
DEFAULT_TRADES_CSV = Path("..") / "xauusd-phase0r" / "outputs" / "reports" / "EURUSD_H4_SWING_TREND_CONTINUATION_PULLBACK_V0_TRADES_2026_06_19.csv"


@dataclass(frozen=True)
class Signal:
    signal_id: str
    direction: str
    decision_index: int
    entry_index: int
    decision_time: datetime
    entry_time: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_points: float
    risk_price: float
    pullback_depth_points: float
    body_to_range: float
    close_location: float
    d1_ema50_slope_points: float
    h4_atr_points: float
    charged_spread_points: float
    p95_spread_points: float
    market_day_direction: str


@dataclass(frozen=True)
class Trade:
    signal_id: str
    candidate_id: str
    direction: str
    entry_time: str
    exit_time: str
    exit_reason: str
    market_day_direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    exit_price: float
    risk_points: float
    hold_h4_bars: int
    weighted_swap_events: int
    gross_r: float
    spread_cost_r: float
    slippage_cost_r: float
    swap_cost_r: float
    total_cost_r: float
    net_r: float
    stress_spread_cost_r: float
    stress_slippage_cost_r: float
    stress_swap_cost_r: float
    stress_total_cost_r: float
    stress_net_r: float
    mfe_r: float
    mae_r: float
    pullback_depth_points: float
    body_to_range: float
    close_location: float
    d1_ema50_slope_points: float
    h4_atr_points: float


@dataclass(frozen=True)
class Funnel:
    candidate_direction_checks: int
    trend_eligible: int
    pullback_eligible: int
    trigger_eligible: int
    raw_signals: int
    opened_after_one_position_scheduling: int
    scheduled_out_by_one_position: int
    long_raw_signals: int
    short_raw_signals: int
    long_opened: int
    short_opened: int


def run_screen(phase1_root: Path) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    h4_path = (phase1_root / DEFAULT_H4).resolve()
    d1_path = (phase1_root / DEFAULT_D1).resolve()
    dukascopy_h4_path = (phase1_root / DEFAULT_DUKASCOPY_H4).resolve()
    dukascopy_d1_path = (phase1_root / DEFAULT_DUKASCOPY_D1).resolve()
    hypothesis_path = (phase1_root / DEFAULT_HYPOTHESIS).resolve()
    hash_manifest = (phase1_root / DEFAULT_HASH_MANIFEST).resolve()
    swap_json = (phase1_root / DEFAULT_SWAP_JSON).resolve()
    output_json = (phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = (phase1_root / DEFAULT_OUTPUT_MD).resolve()
    trades_csv = (phase1_root / DEFAULT_TRADES_CSV).resolve()

    h4 = load_processed_bars(h4_path)
    d1 = load_processed_bars(d1_path)
    h4_series = with_indicators(h4, ema_periods=(20, 50), atr_period=14)
    d1_series = with_indicators(d1, ema_periods=(50,), atr_period=14)
    spread_model = spread_by_hour(h4)
    day_directions = market_day_directions(d1)
    swap_model = json.loads(swap_json.read_text(encoding="utf-8"))

    signals, funnel_unscheduled = generate_signals(h4, h4_series, d1_series, spread_model, day_directions)
    trades = schedule_and_simulate(signals, h4, spread_model)
    funnel = build_funnel(funnel_unscheduled, signals, trades)
    metrics = summarize(trades, h4, d1, dukascopy_h4_path)
    metrics["decision"] = decision(metrics)
    metrics["hypothesis_lock"] = hypothesis_lock_row(hash_manifest, CANDIDATE_ID)
    metrics["stage_funnel"] = asdict(funnel)

    comparison = run_comparison_dataset(dukascopy_h4_path, dukascopy_d1_path, spread_model)

    payload = {
        "status": "PASS",
        "decision": metrics["decision"],
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": "Offline Phase 0R screen only. No MT5 terminal, profile, chart, preset, order, position, or broker runtime state was touched.",
        "candidate_id": CANDIDATE_ID,
        "hypothesis": {
            "path": str(hypothesis_path),
            "lock": metrics["hypothesis_lock"],
        },
        "data_window": {
            "primary_broker": BROKER,
            "primary_symbol": SYMBOL,
            "primary_timeframe": "H4",
            "h4_path": str(h4_path),
            "d1_path": str(d1_path),
            "start_utc": fmt_time(h4[0].start) if h4 else "",
            "end_utc": fmt_time(h4[-1].end) if h4 else "",
            "h4_rows": len(h4),
            "d1_rows": len(d1),
            "dukascopy_h4_comparison_path": str(dukascopy_h4_path),
            "dukascopy_d1_comparison_path": str(dukascopy_d1_path),
            "dukascopy_h4_rows": count_rows(dukascopy_h4_path),
        },
        "cost_model": {
            "swap_source": str(swap_json),
            "swap_source_url": swap_model.get("source_url"),
            "long_overnight_funding_percent": swap_model.get("long_overnight_funding_percent"),
            "short_overnight_funding_percent": swap_model.get("short_overnight_funding_percent"),
            "funding_time_utc": swap_model.get("funding_time_utc"),
            "wednesday_triple_swap": swap_model.get("wednesday_triple_swap"),
            "entry_slippage_points": ENTRY_SLIPPAGE_POINTS,
            "stop_or_time_exit_slippage_points": STOP_OR_TIME_EXIT_SLIPPAGE_POINTS,
            "stress_entry_slippage_points": STRESS_ENTRY_SLIPPAGE_POINTS,
            "stress_stop_or_time_exit_slippage_points": STRESS_STOP_OR_TIME_EXIT_SLIPPAGE_POINTS,
            "stress_swap_multiplier": SWAP_STRESS_MULTIPLIER,
        },
        "metrics": metrics,
        "supplemental_comparison": comparison,
        "outputs": {
            "json": str(output_json),
            "markdown": str(output_md),
            "trades_csv": str(trades_csv),
        },
    }
    write_json(output_json, payload)
    write_csv(trades_csv, [asdict(trade) for trade in trades], list(Trade.__dataclass_fields__.keys()))
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def run_comparison_dataset(
    h4_path: Path,
    d1_path: Path,
    capital_spread_model: dict[int, dict[str, float]],
) -> dict[str, Any]:
    if not h4_path.exists() or not d1_path.exists():
        return {"status": "MISSING_COMPARISON_DATA"}
    h4 = load_processed_bars(h4_path)
    d1 = load_processed_bars(d1_path)
    h4_series = with_indicators(h4, ema_periods=(20, 50), atr_period=14)
    d1_series = with_indicators(d1, ema_periods=(50,), atr_period=14)
    day_directions = market_day_directions(d1)
    signals, funnel_unscheduled = generate_signals(h4, h4_series, d1_series, capital_spread_model, day_directions)
    trades = schedule_and_simulate(signals, h4, capital_spread_model)
    metrics = summarize(trades, h4, d1, h4_path)
    metrics["decision"] = decision(metrics)
    metrics["stage_funnel"] = asdict(build_funnel(funnel_unscheduled, signals, trades))
    return {
        "status": "COMPARISON_ONLY_CANNOT_APPROVE_OR_OVERRULE_CAPITAL_COM",
        "broker": "dukascopy",
        "cost_model": "Capital.com spread/slippage/swap proxy",
        "h4_path": str(h4_path),
        "d1_path": str(d1_path),
        "metrics": metrics,
    }


def load_processed_bars(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            start = parse_time(row.get("bar_start_utc", "")) or parse_time(row.get("timestamp_utc", ""))
            end = parse_time(row.get("bar_end_utc", "")) or parse_time(row.get("timestamp_utc", ""))
            if start is None or end is None:
                continue
            spread = first_float(
                row,
                ("spread_median_points", "spread_close_points", "spread_open_points", "spread"),
                0.0,
            )
            bars.append(
                Bar(
                    start=start,
                    end=end,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    spread=max(0.0, spread),
                )
            )
    return sorted(bars, key=lambda item: item.start)


def first_float(row: dict[str, str], fields: tuple[str, ...], default: float) -> float:
    for field in fields:
        value = row.get(field)
        if value not in {None, ""}:
            try:
                return float(value)
            except ValueError:
                continue
    return default


def with_indicators(bars: list[Bar], *, ema_periods: tuple[int, ...], atr_period: int) -> dict[str, Any]:
    output: dict[str, Any] = {"bars": bars, "atr14": atr_values(bars, atr_period)}
    closes = [bar.close for bar in bars]
    for period in ema_periods:
        output[f"ema{period}"] = ema(closes, period)
    return output


def ema(values: list[float], period: int) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) < period:
        return output
    previous = sum(values[:period]) / period
    output[period - 1] = previous
    alpha = 2.0 / (period + 1.0)
    for index in range(period, len(values)):
        previous = alpha * values[index] + (1.0 - alpha) * previous
        output[index] = previous
    return output


def atr_values(bars: list[Bar], period: int) -> list[float | None]:
    output: list[float | None] = [None] * len(bars)
    ranges: list[float] = []
    for index, bar in enumerate(bars):
        if index == 0:
            true_range = bar.high - bar.low
        else:
            previous_close = bars[index - 1].close
            true_range = max(bar.high - bar.low, abs(bar.high - previous_close), abs(bar.low - previous_close))
        ranges.append(max(0.0, true_range))
        if index + 1 >= period:
            output[index] = sum(ranges[index + 1 - period : index + 1]) / period
    return output


def spread_by_hour(bars: list[Bar]) -> dict[int, dict[str, float]]:
    by_hour: dict[int, list[float]] = {}
    for bar in bars:
        if bar.spread > 0:
            by_hour.setdefault(bar.start.hour, []).append(bar.spread)
    model: dict[int, dict[str, float]] = {}
    global_spreads = [bar.spread for bar in bars if bar.spread > 0]
    global_median = percentile(global_spreads, 50) or 8.0
    global_p95 = percentile(global_spreads, 95) or 12.0
    for hour in range(24):
        values = by_hour.get(hour, global_spreads)
        model[hour] = {
            "median": percentile(values, 50) or global_median,
            "p95": percentile(values, 95) or global_p95,
        }
    return model


def completed_index(bars: list[Bar], decision_time: datetime) -> int | None:
    idx = bisect.bisect_right([bar.end for bar in bars], decision_time) - 1
    return idx if idx >= 0 else None


def generate_signals(
    h4: list[Bar],
    h4_series: dict[str, Any],
    d1_series: dict[str, Any],
    spread_model: dict[int, dict[str, float]],
    day_directions: dict[str, str],
) -> tuple[list[Signal], dict[str, int]]:
    signals: list[Signal] = []
    counts = {
        "candidate_direction_checks": 0,
        "trend_eligible": 0,
        "pullback_eligible": 0,
        "trigger_eligible": 0,
    }
    for index in range(80, len(h4) - 1):
        for direction in ("LONG", "SHORT"):
            counts["candidate_direction_checks"] += 1
            signal, stage = build_signal(direction, index, h4, h4_series, d1_series, spread_model, day_directions)
            for name, passed in stage.items():
                if passed:
                    counts[name] += 1
            if signal is not None:
                signals.append(signal)
    return signals, counts


def build_signal(
    direction: str,
    index: int,
    h4: list[Bar],
    h4_series: dict[str, Any],
    d1_series: dict[str, Any],
    spread_model: dict[int, dict[str, float]],
    day_directions: dict[str, str],
) -> tuple[Signal | None, dict[str, bool]]:
    stage = {"trend_eligible": False, "pullback_eligible": False, "trigger_eligible": False}
    is_long = direction == "LONG"
    decision = h4[index]
    entry_bar = h4[index + 1]
    d1_index = completed_index(d1_series["bars"], decision.end)
    if d1_index is None or d1_index < 5 or index < 9:
        return None, stage
    h4_ema20 = h4_series["ema20"]
    h4_ema50 = h4_series["ema50"]
    h4_atr = h4_series["atr14"]
    d1_ema50 = d1_series["ema50"]
    if any(value is None for value in (h4_ema20[index], h4_ema50[index], h4_atr[index], d1_ema50[d1_index], d1_ema50[d1_index - 5])):
        return None, stage
    h4_ema20_value = float(h4_ema20[index])
    h4_ema50_value = float(h4_ema50[index])
    h4_atr_price = float(h4_atr[index])
    d1_slope_points = (float(d1_ema50[d1_index]) - float(d1_ema50[d1_index - 5])) / POINT
    trend_ok = d1_slope_points > 0 and h4_ema20_value > h4_ema50_value if is_long else d1_slope_points < 0 and h4_ema20_value < h4_ema50_value
    if not trend_ok:
        return None, stage
    stage["trend_eligible"] = True

    pullback_window = h4[index - 5 : index + 1]
    last3 = h4[index - 2 : index + 1]
    last10 = h4[index - 9 : index + 1]
    if is_long:
        pullback_extreme = min(bar.low for bar in pullback_window)
        reference = max(bar.high for bar in last10)
        pullback_depth = reference - pullback_extreme
        pullback_ok = (
            any(bar.low <= h4_ema20_value + 0.20 * h4_atr_price for bar in pullback_window)
            and not any(bar.close < h4_ema50_value for bar in last3)
        )
    else:
        pullback_extreme = max(bar.high for bar in pullback_window)
        reference = min(bar.low for bar in last10)
        pullback_depth = pullback_extreme - reference
        pullback_ok = (
            any(bar.high >= h4_ema20_value - 0.20 * h4_atr_price for bar in pullback_window)
            and not any(bar.close > h4_ema50_value for bar in last3)
        )
    if not pullback_ok or pullback_depth < 0.50 * h4_atr_price or pullback_depth > 2.00 * h4_atr_price:
        return None, stage
    stage["pullback_eligible"] = True

    body = body_to_range(decision)
    loc = close_location(decision)
    if body is None or loc is None or body < 0.25:
        return None, stage
    trigger_ok = decision.close > h4_ema20_value and loc >= 0.60 if is_long else decision.close < h4_ema20_value and loc <= 0.40
    if not trigger_ok:
        return None, stage
    stage["trigger_eligible"] = True

    median_spread = spread_model[entry_bar.start.hour]["median"]
    p95_spread = spread_model[entry_bar.start.hour]["p95"]
    charged_spread = max(entry_bar.spread, median_spread)
    entry = entry_bar.open + charged_spread * POINT / 2.0 if is_long else entry_bar.open - charged_spread * POINT / 2.0
    if is_long:
        pullback_extreme_risk = max(0.0, (entry - pullback_extreme) / POINT + 0.25 * h4_atr_price / POINT)
    else:
        pullback_extreme_risk = max(0.0, (pullback_extreme - entry) / POINT + 0.25 * h4_atr_price / POINT)
    risk_points = max(3.0 * h4_atr_price / POINT, pullback_extreme_risk, 3.0 * charged_spread)
    risk_price = risk_points * POINT
    stop = entry - risk_price if is_long else entry + risk_price
    target = entry + 1.5 * risk_price if is_long else entry - 1.5 * risk_price
    signal_id = "|".join([CANDIDATE_ID, direction, fmt_time(decision.start), f"{entry:.5f}", f"{risk_points:.1f}"])
    return Signal(
        signal_id=signal_id,
        direction=direction,
        decision_index=index,
        entry_index=index + 1,
        decision_time=decision.end,
        entry_time=entry_bar.start,
        entry_price=entry,
        stop_loss=stop,
        take_profit=target,
        risk_points=risk_points,
        risk_price=risk_price,
        pullback_depth_points=pullback_depth / POINT,
        body_to_range=body,
        close_location=loc,
        d1_ema50_slope_points=d1_slope_points,
        h4_atr_points=h4_atr_price / POINT,
        charged_spread_points=charged_spread,
        p95_spread_points=max(entry_bar.spread, p95_spread),
        market_day_direction=day_directions.get(fmt_time(decision.start)[:10], "UNKNOWN"),
    ), stage


def schedule_and_simulate(signals: list[Signal], h4: list[Bar], spread_model: dict[int, dict[str, float]]) -> list[Trade]:
    trades: list[Trade] = []
    available_index = -1
    for signal in signals:
        if signal.decision_index <= available_index:
            continue
        trade = simulate(signal, h4, spread_model)
        if trade is None:
            continue
        trades.append(trade)
        exit_time = parse_time(trade.exit_time)
        exit_index = completed_index(h4, exit_time or signal.entry_time)
        available_index = exit_index if exit_index is not None else len(h4)
    return trades


def simulate(signal: Signal, h4: list[Bar], spread_model: dict[int, dict[str, float]]) -> Trade | None:
    is_long = signal.direction == "LONG"
    entry = signal.entry_price
    sl = signal.stop_loss
    tp = signal.take_profit
    risk = signal.risk_price
    mfe = 0.0
    mae = 0.0
    max_index = min(len(h4) - 1, signal.entry_index + 29)
    for index in range(signal.entry_index, max_index + 1):
        bar = h4[index]
        if is_long:
            mfe = max(mfe, (bar.high - entry) / risk)
            mae = max(mae, (entry - bar.low) / risk)
            hit_sl = bar.low <= sl
            hit_tp = bar.high >= tp
        else:
            mfe = max(mfe, (entry - bar.low) / risk)
            mae = max(mae, (bar.high - entry) / risk)
            hit_sl = bar.high >= sl
            hit_tp = bar.low <= tp
        if hit_sl or hit_tp:
            exit_reason = "SL" if hit_sl else "TP"
            exit_price = sl if hit_sl else tp
            gross_r = -1.0 if hit_sl else 1.5
            return costed_trade(signal, bar.end, exit_price, gross_r, exit_reason, index - signal.entry_index + 1, mfe, mae, spread_model)
        if index == max_index:
            exit_price = bar.close
            gross_r = (exit_price - entry) / risk if is_long else (entry - exit_price) / risk
            return costed_trade(signal, bar.end, exit_price, gross_r, "TIME_STOP", index - signal.entry_index + 1, mfe, mae, spread_model)
    return None


def costed_trade(
    signal: Signal,
    exit_time: datetime,
    exit_price: float,
    gross_r: float,
    exit_reason: str,
    hold_bars: int,
    mfe: float,
    mae: float,
    spread_model: dict[int, dict[str, float]],
) -> Trade:
    non_tp_exit = exit_reason != "TP"
    spread_cost_r = signal.charged_spread_points / signal.risk_points
    stress_spread_cost_r = signal.p95_spread_points / signal.risk_points
    slippage_points = ENTRY_SLIPPAGE_POINTS + (STOP_OR_TIME_EXIT_SLIPPAGE_POINTS if non_tp_exit else 0.0)
    stress_slippage_points = STRESS_ENTRY_SLIPPAGE_POINTS + (STRESS_STOP_OR_TIME_EXIT_SLIPPAGE_POINTS if non_tp_exit else 0.0)
    slippage_cost_r = slippage_points / signal.risk_points
    stress_slippage_cost_r = stress_slippage_points / signal.risk_points
    weighted_swaps = weighted_funding_events(signal.entry_time, exit_time)
    rate_percent = LONG_SWAP_PERCENT if signal.direction == "LONG" else SHORT_SWAP_PERCENT
    swap_cost_r = abs(rate_percent / 100.0) * signal.entry_price / signal.risk_price * weighted_swaps
    stress_swap_cost_r = swap_cost_r * SWAP_STRESS_MULTIPLIER
    total_cost_r = spread_cost_r + slippage_cost_r + swap_cost_r
    stress_total_cost_r = stress_spread_cost_r + stress_slippage_cost_r + stress_swap_cost_r
    return Trade(
        signal_id=signal.signal_id,
        candidate_id=CANDIDATE_ID,
        direction=signal.direction,
        entry_time=fmt_time(signal.entry_time),
        exit_time=fmt_time(exit_time),
        exit_reason=exit_reason,
        market_day_direction=signal.market_day_direction,
        entry_price=round(signal.entry_price, 5),
        stop_loss=round(signal.stop_loss, 5),
        take_profit=round(signal.take_profit, 5),
        exit_price=round(exit_price, 5),
        risk_points=round(signal.risk_points, 4),
        hold_h4_bars=hold_bars,
        weighted_swap_events=weighted_swaps,
        gross_r=round(gross_r, 6),
        spread_cost_r=round(spread_cost_r, 6),
        slippage_cost_r=round(slippage_cost_r, 6),
        swap_cost_r=round(swap_cost_r, 6),
        total_cost_r=round(total_cost_r, 6),
        net_r=round(gross_r - total_cost_r, 6),
        stress_spread_cost_r=round(stress_spread_cost_r, 6),
        stress_slippage_cost_r=round(stress_slippage_cost_r, 6),
        stress_swap_cost_r=round(stress_swap_cost_r, 6),
        stress_total_cost_r=round(stress_total_cost_r, 6),
        stress_net_r=round(gross_r - stress_total_cost_r, 6),
        mfe_r=round(mfe, 4),
        mae_r=round(mae, 4),
        pullback_depth_points=round(signal.pullback_depth_points, 4),
        body_to_range=round(signal.body_to_range, 4),
        close_location=round(signal.close_location, 4),
        d1_ema50_slope_points=round(signal.d1_ema50_slope_points, 4),
        h4_atr_points=round(signal.h4_atr_points, 4),
    )


def weighted_funding_events(entry_time: datetime, exit_time: datetime) -> int:
    current = entry_time.replace(hour=21, minute=0, second=0, microsecond=0)
    if current <= entry_time:
        current += timedelta(days=1)
    events = 0
    while current <= exit_time:
        events += 3 if current.weekday() == 2 else 1
        current += timedelta(days=1)
    return events


def build_funnel(counts: dict[str, int], signals: list[Signal], trades: list[Trade]) -> Funnel:
    return Funnel(
        candidate_direction_checks=counts["candidate_direction_checks"],
        trend_eligible=counts["trend_eligible"],
        pullback_eligible=counts["pullback_eligible"],
        trigger_eligible=counts["trigger_eligible"],
        raw_signals=len(signals),
        opened_after_one_position_scheduling=len(trades),
        scheduled_out_by_one_position=max(0, len(signals) - len(trades)),
        long_raw_signals=sum(1 for signal in signals if signal.direction == "LONG"),
        short_raw_signals=sum(1 for signal in signals if signal.direction == "SHORT"),
        long_opened=sum(1 for trade in trades if trade.direction == "LONG"),
        short_opened=sum(1 for trade in trades if trade.direction == "SHORT"),
    )


def summarize(trades: list[Trade], h4: list[Bar], d1: list[Bar], dukascopy_h4_path: Path) -> dict[str, Any]:
    net = [trade.net_r for trade in trades]
    stress = [trade.stress_net_r for trade in trades]
    total_cost = [trade.total_cost_r for trade in trades]
    stress_cost = [trade.stress_total_cost_r for trade in trades]
    pf = profit_factor(net)
    stress_pf = profit_factor(stress)
    by_day = group_by(trades, lambda trade: trade.entry_time[:10])
    by_week = group_by(trades, lambda trade: week_key(trade.entry_time))
    day_net = {day: sum(trade.net_r for trade in rows) for day, rows in by_day.items()}
    worst_day = min(day_net.values(), default=0.0)
    best_1 = remove_ranked_days(trades, 1, reverse=True)
    best_2 = remove_ranked_days(trades, 2, reverse=True)
    worst_1 = remove_ranked_days(trades, 1, reverse=False)
    up_net = sum(trade.net_r for trade in trades if trade.market_day_direction == "UP")
    down_net = sum(trade.net_r for trade in trades if trade.market_day_direction == "DOWN")
    time_stop_trades = [trade for trade in trades if trade.exit_reason == "TIME_STOP"]
    years = sorted({trade.entry_time[:4] for trade in trades})
    metrics = {
        "closed_trades": len(trades),
        "long_trades": sum(1 for trade in trades if trade.direction == "LONG"),
        "short_trades": sum(1 for trade in trades if trade.direction == "SHORT"),
        "calendar_years": ", ".join(years),
        "calendar_year_count": len(years),
        "weeks_with_closed_trade": len(by_week),
        "average_trades_per_year": round(len(trades) / len(years), 2) if years else 0.0,
        "median_h4_bars_held": percentile([float(trade.hold_h4_bars) for trade in trades], 50),
        "median_weighted_swap_events": percentile([float(trade.weighted_swap_events) for trade in trades], 50),
        "win_rate_pct": pct(sum(1 for value in net if value > 0), len(net)),
        "net_profit_factor": round(pf, 4) if pf is not None and math.isfinite(pf) else pf,
        "net_expectancy_r": round(sum(net) / len(net), 4) if net else None,
        "total_net_r": round(sum(net), 4),
        "stress_profit_factor": round(stress_pf, 4) if stress_pf is not None and math.isfinite(stress_pf) else stress_pf,
        "stress_expectancy_r": round(sum(stress) / len(stress), 4) if stress else None,
        "total_stress_r": round(sum(stress), 4),
        "p50_total_cost_r": percentile(total_cost, 50),
        "p95_total_cost_r": percentile(total_cost, 95),
        "max_total_cost_r": round(max(total_cost), 4) if total_cost else None,
        "p95_stress_total_cost_r": percentile(stress_cost, 95),
        "max_drawdown_r": round(max_drawdown(net), 4),
        "worst_day_r": round(worst_day, 4),
        "best_1_day_removed_r": best_1["net_r"],
        "best_2_days_removed_r": best_2["net_r"],
        "worst_1_day_removed_r": worst_1["net_r"],
        "up_day_net_r": round(up_net, 4),
        "down_day_net_r": round(down_net, 4),
        "significance": significance_summary(net),
        "time_stop_count": len(time_stop_trades),
        "time_stop_total_net_r": round(sum(trade.net_r for trade in time_stop_trades), 4),
        "time_stop_avg_net_r": round(sum(trade.net_r for trade in time_stop_trades) / len(time_stop_trades), 4) if time_stop_trades else None,
        "exit_reason_counts": {reason: sum(1 for trade in trades if trade.exit_reason == reason) for reason in ("TP", "SL", "TIME_STOP")},
        "capital_com_h4_rows": len(h4),
        "capital_com_d1_rows": len(d1),
        "dukascopy_h4_rows": count_rows(dukascopy_h4_path),
    }
    metrics.update(gate_status(metrics))
    return metrics


def gate_status(metrics: dict[str, Any]) -> dict[str, Any]:
    net_pf = metrics["net_profit_factor"]
    stress_pf = metrics["stress_profit_factor"]
    p95_cost = metrics["p95_total_cost_r"]
    max_cost = metrics["max_total_cost_r"]
    sample_gate = metrics["closed_trades"] >= MIN_CLOSED_TRADES and metrics["long_trades"] >= MIN_LONG_TRADES and metrics["short_trades"] >= MIN_SHORT_TRADES
    net_gate = metrics["net_expectancy_r"] is not None and metrics["net_expectancy_r"] >= DISCOVERY_MIN_EXPECTANCY_R and net_pf is not None and net_pf >= DISCOVERY_MIN_PF
    stress_gate = metrics["stress_expectancy_r"] is not None and metrics["stress_expectancy_r"] >= DISCOVERY_MIN_EXPECTANCY_R and stress_pf is not None and stress_pf >= DISCOVERY_MIN_PF
    cost_gate = p95_cost is not None and p95_cost <= P95_TOTAL_COST_R_LIMIT and max_cost is not None and max_cost <= MAX_TRADE_COST_R
    dd_gate = metrics["max_drawdown_r"] <= MAX_DRAWDOWN_R
    worst_day_gate = metrics["worst_day_r"] > -4.0 and metrics["worst_1_day_removed_r"] > 0
    best_days_gate = metrics["best_1_day_removed_r"] > 0 and metrics["best_2_days_removed_r"] > 0
    regime_gate = metrics["up_day_net_r"] > 0 and metrics["down_day_net_r"] > 0
    sig_gate = bool(metrics["significance"].get("passes_t_ge_2"))
    failures = []
    for name, passed in {
        "sample_gate": sample_gate,
        "net_gate": net_gate,
        "stress_gate": stress_gate,
        "cost_gate": cost_gate,
        "drawdown_gate": dd_gate,
        "worst_day_gate": worst_day_gate,
        "best_days_removed_gate": best_days_gate,
        "both_regime_gate": regime_gate,
        "significance_gate": sig_gate,
    }.items():
        if not passed:
            failures.append(name)
    return {
        "sample_gate_pass": sample_gate,
        "net_gate_pass": net_gate,
        "stress_gate_pass": stress_gate,
        "cost_gate_pass": cost_gate,
        "drawdown_gate_pass": dd_gate,
        "worst_day_gate_pass": worst_day_gate,
        "best_days_removed_gate_pass": best_days_gate,
        "both_regime_gate_pass": regime_gate,
        "significance_gate_pass": sig_gate,
        "failure_reasons": failures,
    }


def decision(metrics: dict[str, Any]) -> str:
    if metrics["closed_trades"] < MIN_CLOSED_TRADES or metrics["long_trades"] < MIN_LONG_TRADES or metrics["short_trades"] < MIN_SHORT_TRADES:
        return "FAIL_INSUFFICIENT_SAMPLE"
    if metrics["failure_reasons"]:
        return "FAIL_STANDARD_BAR"
    return "PASS_DISCOVERY_SCREEN_FORWARD_TICK_VALIDATION_ELIGIBLE"


def render_markdown(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    funnel = metrics["stage_funnel"]
    lines = [
        "# EURUSD H4 Swing Trend Continuation Pullback V0 Screen - 2026-06-19",
        "",
        f"Status: `{payload['status']}`",
        f"Decision: `{payload['decision']}`",
        "",
        payload["boundary"],
        "",
        "## Hypothesis Lock",
        "",
        f"- Path: `{payload['hypothesis']['path']}`",
        f"- Manifest status: `{payload['hypothesis']['lock'].get('status', 'UNKNOWN')}`",
        f"- SHA256: `{payload['hypothesis']['lock'].get('sha256', 'UNKNOWN')}`",
        "",
        "## Data Window",
        "",
        f"- Primary: `{payload['data_window']['primary_broker']} / {payload['data_window']['primary_symbol']} / {payload['data_window']['primary_timeframe']}`",
        f"- Start UTC: `{payload['data_window']['start_utc']}`",
        f"- End UTC: `{payload['data_window']['end_utc']}`",
        f"- Capital.com H4 rows: `{payload['data_window']['h4_rows']}`",
        f"- Capital.com D1 rows: `{payload['data_window']['d1_rows']}`",
        f"- Dukascopy H4 comparison rows: `{payload['data_window']['dukascopy_h4_rows']}`",
        "",
        "## Cost Model",
        "",
        f"- Swap source URL: `{payload['cost_model']['swap_source_url']}`",
        f"- Long funding: `{payload['cost_model']['long_overnight_funding_percent']}%`",
        f"- Short funding: `{payload['cost_model']['short_overnight_funding_percent']}%`",
        f"- Funding time UTC: `{payload['cost_model']['funding_time_utc']}`",
        f"- Wednesday triple swap: `{payload['cost_model']['wednesday_triple_swap']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Closed trades | {metrics['closed_trades']} |",
        f"| Long / Short | {metrics['long_trades']} / {metrics['short_trades']} |",
        f"| Calendar years | {metrics['calendar_years']} |",
        f"| Weeks with closed trade | {metrics['weeks_with_closed_trade']} |",
        f"| Avg trades/year | {metrics['average_trades_per_year']} |",
        f"| Median H4 bars held | {metrics['median_h4_bars_held']} |",
        f"| Median weighted swap events | {metrics['median_weighted_swap_events']} |",
        f"| Win rate | {metrics['win_rate_pct']}% |",
        f"| Net PF | {metrics['net_profit_factor']} |",
        f"| Net expectancy R | {metrics['net_expectancy_r']} |",
        f"| Total net R | {metrics['total_net_r']} |",
        f"| Stress PF | {metrics['stress_profit_factor']} |",
        f"| Stress expectancy R | {metrics['stress_expectancy_r']} |",
        f"| P95 total cost R | {metrics['p95_total_cost_r']} |",
        f"| Max total cost R | {metrics['max_total_cost_r']} |",
        f"| P95 stress total cost R | {metrics['p95_stress_total_cost_r']} |",
        f"| Max DD R | {metrics['max_drawdown_r']} |",
        f"| Worst day R | {metrics['worst_day_r']} |",
        f"| Best 2 days removed R | {metrics['best_2_days_removed_r']} |",
        f"| Up-day / Down-day R | {metrics['up_day_net_r']} / {metrics['down_day_net_r']} |",
        f"| t-stat | {metrics['significance'].get('t_stat')} |",
        f"| Time-stop exits | {metrics['time_stop_count']} |",
        f"| Time-stop total net R | {metrics['time_stop_total_net_r']} |",
        f"| Time-stop avg net R | {metrics['time_stop_avg_net_r']} |",
        "",
        "## Stage Funnel",
        "",
        "| Stage | Count |",
        "| --- | ---: |",
        f"| Candidate direction checks | {funnel['candidate_direction_checks']} |",
        f"| Trend-eligible | {funnel['trend_eligible']} |",
        f"| Pullback-eligible | {funnel['pullback_eligible']} |",
        f"| H4-trigger-eligible / raw signals | {funnel['trigger_eligible']} |",
        f"| Opened after one-position scheduling | {funnel['opened_after_one_position_scheduling']} |",
        f"| Scheduled out by one-position rule | {funnel['scheduled_out_by_one_position']} |",
        "",
        "| Direction Split | Raw Signals | Opened |",
        "| --- | ---: | ---: |",
        f"| LONG | {funnel['long_raw_signals']} | {funnel['long_opened']} |",
        f"| SHORT | {funnel['short_raw_signals']} | {funnel['short_opened']} |",
        "",
        "## Exit Reasons",
        "",
        "| Exit Reason | Count |",
        "| --- | ---: |",
    ]
    for reason, count in metrics["exit_reason_counts"].items():
        lines.append(f"| `{reason}` | {count} |")
    comparison = payload.get("supplemental_comparison", {})
    comparison_metrics = comparison.get("metrics", {}) if isinstance(comparison, dict) else {}
    lines.extend(
        [
            "",
            "## Supplemental Dukascopy Comparison",
            "",
            "Comparison-only. This uses Dukascopy EURUSD H4/D1 bars with Capital.com cost proxy. It cannot approve the candidate and cannot overrule a Capital.com primary failure.",
            "",
            f"- Status: `{comparison.get('status', 'UNKNOWN') if isinstance(comparison, dict) else 'UNKNOWN'}`",
            f"- Decision: `{comparison_metrics.get('decision', 'UNKNOWN')}`",
            f"- Closed trades: `{comparison_metrics.get('closed_trades', 'n/a')}`",
            f"- Long / Short: `{comparison_metrics.get('long_trades', 'n/a')} / {comparison_metrics.get('short_trades', 'n/a')}`",
            f"- Net PF: `{comparison_metrics.get('net_profit_factor', 'n/a')}`",
            f"- Net expectancy R: `{comparison_metrics.get('net_expectancy_r', 'n/a')}`",
            f"- P95 total cost R: `{comparison_metrics.get('p95_total_cost_r', 'n/a')}`",
            f"- Failure reasons: `{', '.join(comparison_metrics.get('failure_reasons', [])) if comparison_metrics else 'n/a'}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            "| Gate | Status |",
            "| --- | --- |",
        ]
    )
    for name in [
        "sample_gate_pass",
        "net_gate_pass",
        "stress_gate_pass",
        "cost_gate_pass",
        "drawdown_gate_pass",
        "worst_day_gate_pass",
        "best_days_removed_gate_pass",
        "both_regime_gate_pass",
        "significance_gate_pass",
    ]:
        lines.append(f"| `{name}` | `{metrics[name]}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Failure reasons: `{', '.join(metrics['failure_reasons']) or 'none'}`.",
            "- This is the first EURUSD H4 swing screen after the XAU reallocation decision.",
            "- The screen includes measured Capital.com direction-specific overnight financing and reports time-stop exits separately.",
            "- Passing this screen would only authorize reviewer discussion and forward/tick validation; it would not authorize MT5 runtime or broker action.",
            "",
            "## Outputs",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def market_day_directions(d1: list[Bar]) -> dict[str, str]:
    output: dict[str, str] = {}
    for bar in d1:
        if bar.close > bar.open:
            output[fmt_time(bar.start)[:10]] = "UP"
        elif bar.close < bar.open:
            output[fmt_time(bar.start)[:10]] = "DOWN"
        else:
            output[fmt_time(bar.start)[:10]] = "FLAT"
    return output


def group_by(rows: list[Trade], key_fn: Any) -> dict[str, list[Trade]]:
    output: dict[str, list[Trade]] = {}
    for row in rows:
        output.setdefault(str(key_fn(row)), []).append(row)
    return output


def week_key(value: str) -> str:
    parsed = parse_time(value)
    if parsed is None:
        return "UNKNOWN"
    iso = parsed.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def remove_ranked_days(trades: list[Trade], count: int, *, reverse: bool) -> dict[str, Any]:
    by_day = group_by(trades, lambda trade: trade.entry_time[:10])
    ranked = sorted(by_day.items(), key=lambda item: sum(trade.net_r for trade in item[1]), reverse=reverse)
    remove = {day for day, _rows in ranked[:count]}
    kept = [trade.net_r for trade in trades if trade.entry_time[:10] not in remove]
    pf = profit_factor(kept)
    return {
        "net_r": round(sum(kept), 4),
        "pf": round(pf, 4) if pf is not None and math.isfinite(pf) else pf,
    }


def pct(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator * 100.0, 2)


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(0, sum(1 for _row in csv.reader(handle)) - 1)


def hypothesis_lock_row(path: Path, candidate_id: str) -> dict[str, str]:
    if not path.exists():
        return {"status": "MISSING_MANIFEST", "candidate_id": candidate_id, "sha256": ""}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if clean_manifest_value(row.get("candidate_id", "")) == candidate_id:
                return {**row, "status": "FOUND" if row.get("status") == "LOCKED" else row.get("status", "UNKNOWN")}
    return {"status": "MISSING_CANDIDATE", "candidate_id": candidate_id, "sha256": ""}


def clean_manifest_value(value: str) -> str:
    return value.strip().strip("`").strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Screen locked EURUSD H4 swing trend-continuation pullback V0.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    payload = run_screen(args.root)
    print(f"{CANDIDATE_ID}: {payload['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
