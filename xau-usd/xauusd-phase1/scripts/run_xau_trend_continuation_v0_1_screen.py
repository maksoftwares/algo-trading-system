from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_a3_net_cost_deduped_rebaseline import (
    DISCOVERY_MIN_EXPECTANCY_R,
    DISCOVERY_MIN_PF,
    ENTRY_SLIPPAGE_POINTS,
    MAX_DRAWDOWN_R,
    MAX_TRADE_COST_R,
    P95_COST_R_LIMIT,
    STOP_EXIT_SLIPPAGE_POINTS,
    load_cost_model,
    significance_summary,
    spread_from_model,
)
from run_a3_signal_quality_extended_discovery import DISCOVERY_END, DISCOVERY_START, PHASE0_BARS, WARMUP_START, load_phase0_bars
from run_a3_signal_quality_offline_discovery import (
    Bar,
    body_to_range,
    close_location,
    completed_index,
    derive_m15,
    fmt_time,
    max_drawdown,
    parse_time,
    percentile,
    profit_factor,
    with_indicators,
    write_csv,
    write_json,
)


CANDIDATE_ID = "xau_h1_h4_trend_continuation_pullback_v0_1"
SYMBOL = "XAUUSD"
POINT = 0.01
DEFAULT_COST_MODEL = Path("..") / "xauusd-phase0" / "outputs" / "reports" / "cost_model_measured.csv"
DEFAULT_HYPOTHESIS = (
    Path("..")
    / "xauusd-phase0r"
    / "hypotheses"
    / "hypothesis_xau_h1_h4_trend_continuation_pullback_v0_1.md"
)
DEFAULT_HASH_MANIFEST = Path("..") / "xauusd-phase0r" / "outputs" / "hypothesis_hash_manifest.csv"
DEFAULT_OUTPUT_JSON = (
    Path("..")
    / "xauusd-phase0r"
    / "outputs"
    / "reports"
    / "XAU_H1_H4_TREND_CONTINUATION_PULLBACK_V0_1_SCREEN_2026_06_19.json"
)
DEFAULT_OUTPUT_MD = (
    Path("..")
    / "xauusd-phase0r"
    / "outputs"
    / "reports"
    / "XAU_H1_H4_TREND_CONTINUATION_PULLBACK_V0_1_SCREEN_2026_06_19.md"
)
DEFAULT_TRADES_CSV = (
    Path("..")
    / "xauusd-phase0r"
    / "outputs"
    / "reports"
    / "XAU_H1_H4_TREND_CONTINUATION_PULLBACK_V0_1_TRADES_2026_06_19.csv"
)


@dataclass(frozen=True)
class CandidateSignal:
    signal_id: str
    direction: str
    confirmation_index: int
    entry_index: int
    decision_time: datetime
    entry_time: datetime
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_points: float
    estimated_cost_r: float
    session_bucket: str
    market_day_direction: str
    h4_ema50_slope_points: float
    h1_ema20: float
    h1_ema50: float
    h1_atr_points: float
    m15_atr_points: float
    pullback_depth_points: float
    body_to_range: float
    close_location: float
    charged_spread_points: float
    p95_spread_points: float


@dataclass(frozen=True)
class CandidateTrade:
    signal_id: str
    candidate_id: str
    direction: str
    entry_time: str
    exit_time: str
    session_bucket: str
    market_day_direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_points: float
    final_r: float
    net_r: float
    stress_net_r: float
    charged_cost_r: float
    stress_cost_r: float
    outcome: str
    mfe_r: float
    mae_r: float
    estimated_cost_r: float
    h4_ema50_slope_points: float
    h1_atr_points: float
    pullback_depth_points: float
    body_to_range: float
    close_location: float


def run_screen(
    phase1_root: Path,
    *,
    output_json: Path | None = None,
    output_md: Path | None = None,
    trades_csv: Path | None = None,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    phase0_bars = (phase1_root / PHASE0_BARS).resolve()
    cost_model_path = (phase1_root / DEFAULT_COST_MODEL).resolve()
    hypothesis_path = (phase1_root / DEFAULT_HYPOTHESIS).resolve()
    hash_manifest = (phase1_root / DEFAULT_HASH_MANIFEST).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = (output_md or phase1_root / DEFAULT_OUTPUT_MD).resolve()
    trades_csv = (trades_csv or phase1_root / DEFAULT_TRADES_CSV).resolve()

    m5_path = phase0_bars / "M5" / "XAUUSD_dukascopy_M5_20250102_20250701.csv"
    h1_path = phase0_bars / "H1" / "XAUUSD_dukascopy_H1_20160101_20250701_derived_from_m5.csv"
    h4_path = phase0_bars / "H4" / "XAUUSD_dukascopy_H4_20160101_20250701_derived_from_m5.csv"

    m5 = load_phase0_bars(m5_path, DISCOVERY_START, DISCOVERY_END)
    m5_series = with_indicators(m5, ema_periods=(20,))
    m15 = with_indicators(derive_m15(m5), ema_periods=(20,))
    h1 = with_indicators(load_phase0_bars(h1_path, WARMUP_START, DISCOVERY_END), ema_periods=(20, 50))
    h4 = with_indicators(load_phase0_bars(h4_path, WARMUP_START, DISCOVERY_END), ema_periods=(50,))
    h1_atr = atr_values(h1["bars"], 14)
    m15_atr = atr_values(m15["bars"], 14)
    cost_model = load_cost_model(cost_model_path)
    day_directions = market_day_directions(m5)

    signals = generate_signals(m5, m5_series, m15, h1, h4, h1_atr, m15_atr, cost_model, day_directions)
    trades = schedule_and_simulate(signals, m5, cost_model)
    metrics = summarize(trades)
    hypothesis_lock = hypothesis_lock_row(hash_manifest, CANDIDATE_ID)
    metrics["hypothesis_lock"] = hypothesis_lock
    metrics["hypothesis_path"] = str(hypothesis_path)
    metrics["screen_window_status"] = (
        "PASS_BOTH_DIRECTIONS_POPULATED"
        if metrics["long_trades"] >= 25 and metrics["short_trades"] >= 25
        else "INSUFFICIENT_BOTH_DIRECTION_SAMPLE"
    )
    metrics["decision"] = decision(metrics)

    payload = {
        "status": "PASS",
        "decision": metrics["decision"],
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": "Offline Phase 0R screen only. No MT5 terminal, profile, chart, preset, order, position, or broker runtime state was touched.",
        "candidate_id": CANDIDATE_ID,
        "hypothesis": {
            "path": str(hypothesis_path),
            "lock": hypothesis_lock,
        },
        "data_window": {
            "source": "Phase0 Dukascopy XAUUSD bars",
            "start_utc": fmt_time(DISCOVERY_START),
            "end_utc": fmt_time(DISCOVERY_END),
        },
        "cost_model": {
            "source_csv": str(cost_model_path),
            "charged_spread_points": "max(realized entry-bar spread, measured median spread for entry UTC hour)",
            "stress_spread_points": "max(realized entry-bar spread, measured P95 spread for entry UTC hour)",
            "entry_slippage_points": ENTRY_SLIPPAGE_POINTS,
            "stop_exit_slippage_points": STOP_EXIT_SLIPPAGE_POINTS,
            "entry_cost_gate": "estimated (spread + entry slippage + stop-exit slippage) / risk <= 0.12",
        },
        "metrics": metrics,
        "outputs": {
            "json": str(output_json),
            "markdown": str(output_md),
            "trades_csv": str(trades_csv),
        },
    }
    write_json(output_json, payload)
    write_csv(trades_csv, [asdict(row) for row in trades], list(asdict(trades[0]).keys()) if trades else list(CandidateTrade.__dataclass_fields__.keys()))
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def generate_signals(
    m5: list[Bar],
    m5_series: dict[str, Any],
    m15: dict[str, Any],
    h1: dict[str, Any],
    h4: dict[str, Any],
    h1_atr: list[float | None],
    m15_atr: list[float | None],
    cost_model: dict[tuple[str, str], dict[str, float]],
    day_directions: dict[str, str],
) -> list[CandidateSignal]:
    signals: list[CandidateSignal] = []
    m5_ema20 = m5_series["ema20"]
    for i in range(80, len(m5) - 1):
        decision_time = m5[i].end
        entry_bar = m5[i + 1]
        m5_now = m5[i]
        m5_prev3 = i - 3
        if m5_prev3 < 0 or m5_ema20[i] is None or m5_ema20[m5_prev3] is None:
            continue
        body = body_to_range(m5_now)
        loc = close_location(m5_now)
        if body is None or loc is None or body < 0.35:
            continue
        for direction in ("LONG", "SHORT"):
            maybe = build_signal(
                direction,
                i,
                decision_time,
                entry_bar,
                m5,
                m5_ema20,
                body,
                loc,
                m15,
                h1,
                h4,
                h1_atr,
                m15_atr,
                cost_model,
                day_directions,
            )
            if maybe is not None:
                signals.append(maybe)
    return signals


def build_signal(
    direction: str,
    i: int,
    decision_time: datetime,
    entry_bar: Bar,
    m5: list[Bar],
    m5_ema20: list[float | None],
    body: float,
    loc: float,
    m15: dict[str, Any],
    h1: dict[str, Any],
    h4: dict[str, Any],
    h1_atr: list[float | None],
    m15_atr: list[float | None],
    cost_model: dict[tuple[str, str], dict[str, float]],
    day_directions: dict[str, str],
) -> CandidateSignal | None:
    is_long = direction == "LONG"
    if is_long:
        if m5[i].close <= float(m5_ema20[i] or 0.0) or float(m5_ema20[i] or 0.0) - float(m5_ema20[i - 3] or 0.0) <= 0:
            return None
        if loc < 0.65:
            return None
    else:
        if m5[i].close >= float(m5_ema20[i] or 0.0) or float(m5_ema20[i] or 0.0) - float(m5_ema20[i - 3] or 0.0) >= 0:
            return None
        if loc > 0.35:
            return None

    h4_idx = completed_index(h4["bars"], decision_time)
    h1_idx = completed_index(h1["bars"], decision_time)
    m15_idx = completed_index(m15["bars"], decision_time)
    if h4_idx is None or h1_idx is None or m15_idx is None or h4_idx < 3 or h1_idx < 11 or m15_idx < 5:
        return None
    h4_ema50 = h4["ema50"]
    h1_ema20 = h1["ema20"]
    h1_ema50 = h1["ema50"]
    if (
        h4_ema50[h4_idx] is None
        or h4_ema50[h4_idx - 3] is None
        or h1_ema20[h1_idx] is None
        or h1_ema50[h1_idx] is None
        or h1_atr[h1_idx] is None
        or m15_atr[m15_idx] is None
    ):
        return None
    h4_slope_points = (float(h4_ema50[h4_idx]) - float(h4_ema50[h4_idx - 3])) / POINT
    if is_long and not (h4_slope_points > 0 and float(h1_ema20[h1_idx]) > float(h1_ema50[h1_idx])):
        return None
    if not is_long and not (h4_slope_points < 0 and float(h1_ema20[h1_idx]) < float(h1_ema50[h1_idx])):
        return None

    h1_atr_price = float(h1_atr[h1_idx])
    m15_atr_price = float(m15_atr[m15_idx])
    if h1_atr_price <= 0 or m15_atr_price <= 0:
        return None
    m15_bars = m15["bars"]
    last6_m15 = m15_bars[m15_idx - 5 : m15_idx + 1]
    last3_m15 = m15_bars[m15_idx - 2 : m15_idx + 1]
    h1_bars = h1["bars"]
    last12_h1 = h1_bars[h1_idx - 11 : h1_idx + 1]
    h1_ema50_value = float(h1_ema50[h1_idx])
    h1_ema20_value = float(h1_ema20[h1_idx])
    if is_long:
        pullback_extreme = min(bar.low for bar in last6_m15)
        recent_reference = max(bar.high for bar in last12_h1)
        pullback_depth = recent_reference - pullback_extreme
        if m15_bars[m15_idx].close <= h1_ema50_value:
            return None
        if not any(bar.low <= h1_ema20_value + 0.20 * m15_atr_price for bar in last6_m15):
            return None
        if any(bar.close < h1_ema50_value for bar in last3_m15):
            return None
    else:
        pullback_extreme = max(bar.high for bar in last6_m15)
        recent_reference = min(bar.low for bar in last12_h1)
        pullback_depth = pullback_extreme - recent_reference
        if m15_bars[m15_idx].close >= h1_ema50_value:
            return None
        if not any(bar.high >= h1_ema20_value - 0.20 * m15_atr_price for bar in last6_m15):
            return None
        if any(bar.close > h1_ema50_value for bar in last3_m15):
            return None
    if pullback_depth < 0.25 * h1_atr_price or pullback_depth > 1.25 * h1_atr_price:
        return None

    median_spread = spread_from_model(cost_model, "median_spread_points", entry_bar.start)
    p95_spread = spread_from_model(cost_model, "p95_spread_points", entry_bar.start)
    charged_spread = max(0.0, entry_bar.spread, median_spread)
    entry = entry_bar.open + charged_spread * POINT / 2.0 if is_long else entry_bar.open - charged_spread * POINT / 2.0
    spread_risk_points = max(charged_spread, 0.0)
    if is_long:
        pullback_extreme_risk = max(0.0, (entry - pullback_extreme) / POINT + 50.0)
    else:
        pullback_extreme_risk = max(0.0, (pullback_extreme - entry) / POINT + 50.0)
    risk_points = max(0.85 * h1_atr_price / POINT, pullback_extreme_risk, 3.0 * spread_risk_points)
    if risk_points <= 0:
        return None
    estimated_cost_r = (charged_spread + ENTRY_SLIPPAGE_POINTS + STOP_EXIT_SLIPPAGE_POINTS) / risk_points
    if estimated_cost_r > MAX_TRADE_COST_R:
        return None
    risk_price = risk_points * POINT
    if is_long:
        stop = entry - risk_price
        target = entry + 1.5 * risk_price
    else:
        stop = entry + risk_price
        target = entry - 1.5 * risk_price
    signal_id = "|".join(
        [
            CANDIDATE_ID,
            direction,
            fmt_time(m5[i].start),
            f"{entry:.2f}",
            f"{risk_points:.1f}",
        ]
    )
    return CandidateSignal(
        signal_id=signal_id,
        direction=direction,
        confirmation_index=i,
        entry_index=i + 1,
        decision_time=decision_time,
        entry_time=entry_bar.start,
        entry_price=entry,
        stop_loss=stop,
        take_profit=target,
        risk_points=risk_points,
        estimated_cost_r=estimated_cost_r,
        session_bucket=dubai_session(decision_time),
        market_day_direction=day_directions.get(fmt_time(decision_time)[:10], "UNKNOWN"),
        h4_ema50_slope_points=h4_slope_points,
        h1_ema20=h1_ema20_value,
        h1_ema50=h1_ema50_value,
        h1_atr_points=h1_atr_price / POINT,
        m15_atr_points=m15_atr_price / POINT,
        pullback_depth_points=pullback_depth / POINT,
        body_to_range=body,
        close_location=loc,
        charged_spread_points=charged_spread,
        p95_spread_points=max(0.0, entry_bar.spread, p95_spread),
    )


def schedule_and_simulate(
    signals: list[CandidateSignal],
    m5: list[Bar],
    cost_model: dict[tuple[str, str], dict[str, float]],
) -> list[CandidateTrade]:
    trades: list[CandidateTrade] = []
    available_at_index = -1
    for signal in signals:
        if signal.confirmation_index <= available_at_index:
            continue
        trade = simulate_signal(signal, m5, cost_model)
        if trade is None:
            continue
        trades.append(trade)
        exit_idx = completed_index(m5, parse_time(trade.exit_time) or signal.entry_time)
        available_at_index = exit_idx if exit_idx is not None else len(m5)
    return trades


def simulate_signal(
    signal: CandidateSignal,
    m5: list[Bar],
    cost_model: dict[tuple[str, str], dict[str, float]],
) -> CandidateTrade | None:
    is_long = signal.direction == "LONG"
    entry = signal.entry_price
    sl = signal.stop_loss
    tp = signal.take_profit
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    mfe = 0.0
    mae = 0.0
    for index in range(signal.entry_index, len(m5)):
        bar = m5[index]
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
            final_r = -1.0 if hit_sl else 1.5
            charged_spread = max(0.0, bar.spread, spread_from_model(cost_model, "median_spread_points", signal.entry_time))
            stress_spread = max(0.0, bar.spread, spread_from_model(cost_model, "p95_spread_points", signal.entry_time))
            exit_slip = STOP_EXIT_SLIPPAGE_POINTS if final_r < 0 else 0.0
            charged_cost_r = (charged_spread + ENTRY_SLIPPAGE_POINTS + exit_slip) / signal.risk_points
            stress_cost_r = (stress_spread + ENTRY_SLIPPAGE_POINTS + exit_slip) / signal.risk_points
            return CandidateTrade(
                signal_id=signal.signal_id,
                candidate_id=CANDIDATE_ID,
                direction=signal.direction,
                entry_time=fmt_time(signal.entry_time),
                exit_time=fmt_time(bar.end),
                session_bucket=signal.session_bucket,
                market_day_direction=signal.market_day_direction,
                entry_price=round(entry, 5),
                stop_loss=round(sl, 5),
                take_profit=round(tp, 5),
                risk_points=round(signal.risk_points, 4),
                final_r=final_r,
                net_r=round(final_r - charged_cost_r, 6),
                stress_net_r=round(final_r - stress_cost_r, 6),
                charged_cost_r=round(charged_cost_r, 6),
                stress_cost_r=round(stress_cost_r, 6),
                outcome="WIN" if final_r > 0 else "LOSS",
                mfe_r=round(mfe, 4),
                mae_r=round(mae, 4),
                estimated_cost_r=round(signal.estimated_cost_r, 6),
                h4_ema50_slope_points=round(signal.h4_ema50_slope_points, 4),
                h1_atr_points=round(signal.h1_atr_points, 4),
                pullback_depth_points=round(signal.pullback_depth_points, 4),
                body_to_range=round(signal.body_to_range, 4),
                close_location=round(signal.close_location, 4),
            )
    return None


def summarize(trades: list[CandidateTrade]) -> dict[str, Any]:
    net = [trade.net_r for trade in trades]
    stress = [trade.stress_net_r for trade in trades]
    pf = profit_factor(net)
    stress_pf = profit_factor(stress)
    longs = sum(1 for trade in trades if trade.direction == "LONG")
    shorts = sum(1 for trade in trades if trade.direction == "SHORT")
    by_day = group_by_day(trades)
    day_net = {day: sum(trade.net_r for trade in rows) for day, rows in by_day.items()}
    worst_day = min(day_net.values(), default=0.0)
    best_1 = remove_ranked_days(trades, 1, reverse=True)
    best_2 = remove_ranked_days(trades, 2, reverse=True)
    worst_1 = remove_ranked_days(trades, 1, reverse=False)
    up_net = sum(trade.net_r for trade in trades if trade.market_day_direction == "UP")
    down_net = sum(trade.net_r for trade in trades if trade.market_day_direction == "DOWN")
    cost_values = [trade.charged_cost_r for trade in trades]
    sig = significance_summary(net)
    return {
        "closed_trades": len(trades),
        "long_trades": longs,
        "short_trades": shorts,
        "win_rate_pct": pct(sum(1 for trade in trades if trade.net_r > 0), len(trades)),
        "net_profit_factor": round(pf, 4) if pf is not None and math.isfinite(pf) else pf,
        "net_expectancy_r": round(sum(net) / len(net), 4) if net else None,
        "total_net_r": round(sum(net), 4),
        "stress_profit_factor": round(stress_pf, 4) if stress_pf is not None and math.isfinite(stress_pf) else stress_pf,
        "stress_expectancy_r": round(sum(stress) / len(stress), 4) if stress else None,
        "total_stress_r": round(sum(stress), 4),
        "p95_cost_r": percentile(cost_values, 95),
        "max_cost_r": round(max(cost_values), 4) if cost_values else None,
        "over_012_cost_share_pct": pct(sum(1 for value in cost_values if value > MAX_TRADE_COST_R), len(cost_values)),
        "max_drawdown_r": round(max_drawdown(net), 4),
        "worst_day_r": round(worst_day, 4),
        "best_1_day_removed_r": best_1["net_r"],
        "best_2_days_removed_r": best_2["net_r"],
        "worst_1_day_removed_r": worst_1["net_r"],
        "up_day_net_r": round(up_net, 4),
        "down_day_net_r": round(down_net, 4),
        "significance": sig,
        "sample_gate_pass": len(trades) >= 100 and longs >= 25 and shorts >= 25,
        "net_gate_pass": bool(net and (sum(net) / len(net)) >= DISCOVERY_MIN_EXPECTANCY_R and pf is not None and pf >= DISCOVERY_MIN_PF),
        "stress_gate_pass": bool(stress and (sum(stress) / len(stress)) >= DISCOVERY_MIN_EXPECTANCY_R and stress_pf is not None and stress_pf >= DISCOVERY_MIN_PF),
        "cost_gate_pass": bool(cost_values and percentile(cost_values, 95) is not None and percentile(cost_values, 95) <= P95_COST_R_LIMIT and max(cost_values) <= MAX_TRADE_COST_R),
        "drawdown_gate_pass": max_drawdown(net) <= MAX_DRAWDOWN_R,
        "worst_day_gate_pass": worst_day > -4.0 and worst_1["net_r"] > 0,
        "best_days_removed_gate_pass": best_1["net_r"] > 0 and best_2["net_r"] > 0,
        "both_regime_gate_pass": up_net > 0 and down_net > 0,
        "significance_gate_pass": bool(sig.get("passes_t_ge_2")),
    }


def decision(metrics: dict[str, Any]) -> str:
    gate_names = [
        "sample_gate_pass",
        "net_gate_pass",
        "stress_gate_pass",
        "cost_gate_pass",
        "drawdown_gate_pass",
        "worst_day_gate_pass",
        "best_days_removed_gate_pass",
        "both_regime_gate_pass",
        "significance_gate_pass",
    ]
    failures = [name for name in gate_names if not metrics.get(name)]
    metrics["failure_reasons"] = failures
    if metrics["screen_window_status"] == "INSUFFICIENT_BOTH_DIRECTION_SAMPLE":
        return "FAIL_INSUFFICIENT_BOTH_DIRECTION_SAMPLE"
    if failures:
        return "FAIL_STANDARD_BAR"
    return "PASS_DISCOVERY_SCREEN_FORWARD_TICK_VALIDATION_ELIGIBLE"


def render_markdown(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# XAU H1/H4 Trend Continuation Pullback V0.1 Screen - 2026-06-19",
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
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Closed trades | {metrics['closed_trades']} |",
        f"| Long / Short | {metrics['long_trades']} / {metrics['short_trades']} |",
        f"| Win rate | {metrics['win_rate_pct']}% |",
        f"| Net PF | {metrics['net_profit_factor']} |",
        f"| Net expectancy R | {metrics['net_expectancy_r']} |",
        f"| Total net R | {metrics['total_net_r']} |",
        f"| Stress PF | {metrics['stress_profit_factor']} |",
        f"| Stress expectancy R | {metrics['stress_expectancy_r']} |",
        f"| P95 cost R | {metrics['p95_cost_r']} |",
        f"| Max cost R | {metrics['max_cost_r']} |",
        f"| Max DD R | {metrics['max_drawdown_r']} |",
        f"| Worst day R | {metrics['worst_day_r']} |",
        f"| Best 2 days removed R | {metrics['best_2_days_removed_r']} |",
        f"| Up-day / Down-day R | {metrics['up_day_net_r']} / {metrics['down_day_net_r']} |",
        f"| t-stat | {metrics['significance'].get('t_stat')} |",
        "",
        "## Gates",
        "",
        "| Gate | Status |",
        "| --- | --- |",
    ]
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
            f"- Screen-window status: `{metrics['screen_window_status']}`.",
            f"- Failure reasons: `{', '.join(metrics.get('failure_reasons', [])) or 'none'}`.",
            "- This is an offline Phase 0R screen only. Passing would not authorize broker action.",
            "- V0.1 fails discovery and is not forward-validation eligible. Because the sample is only seven trades, this should be read primarily as an insufficient-frequency failure, not as a mature statistical expectancy estimate.",
            "",
            "## Outputs",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def atr_values(bars: list[Bar], period: int) -> list[float | None]:
    values: list[float | None] = [None] * len(bars)
    ranges: list[float] = []
    for index, bar in enumerate(bars):
        if index == 0:
            true_range = bar.high - bar.low
        else:
            previous_close = bars[index - 1].close
            true_range = max(bar.high - bar.low, abs(bar.high - previous_close), abs(bar.low - previous_close))
        ranges.append(max(0.0, true_range))
        if index + 1 >= period:
            values[index] = sum(ranges[index + 1 - period : index + 1]) / period
    return values


def group_by_day(trades: list[CandidateTrade]) -> dict[str, list[CandidateTrade]]:
    output: dict[str, list[CandidateTrade]] = {}
    for trade in trades:
        output.setdefault(trade.entry_time[:10], []).append(trade)
    return output


def remove_ranked_days(trades: list[CandidateTrade], count: int, *, reverse: bool) -> dict[str, Any]:
    by_day = group_by_day(trades)
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


def dubai_session(utc_time: datetime) -> str:
    hour = (utc_time.hour + 4) % 24
    if 6 <= hour < 12:
        return "Morning 06:00-11:59"
    if 12 <= hour < 16:
        return "Afternoon 12:00-15:59"
    if 16 <= hour < 20:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def market_day_directions(m5: list[Bar]) -> dict[str, str]:
    grouped: dict[str, list[Bar]] = {}
    for bar in m5:
        grouped.setdefault(fmt_time(bar.start)[:10], []).append(bar)
    output: dict[str, str] = {}
    for day, rows in grouped.items():
        rows = sorted(rows, key=lambda item: item.start)
        if rows[-1].close > rows[0].open:
            output[day] = "UP"
        elif rows[-1].close < rows[0].open:
            output[day] = "DOWN"
        else:
            output[day] = "FLAT"
    return output


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
    parser = argparse.ArgumentParser(description="Screen the locked XAU trend-continuation pullback V0.1 hypothesis.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    payload = run_screen(args.root)
    print(f"{CANDIDATE_ID}: {payload['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
