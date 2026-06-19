from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from run_a3_signal_quality_extended_discovery import (
    DISCOVERY_END,
    DISCOVERY_START,
    PHASE0_BARS,
    WARMUP_START,
    load_phase0_bars,
    soft_retest_v2,
)
from run_a3_signal_quality_offline_discovery import (
    Bar,
    RawSignal,
    VirtualTrade,
    build_data_manifest,
    derive_m15,
    derive_weekly,
    exit_index_for_trade,
    fmt_time,
    generate_breakout_retest_signals,
    load_bars,
    max_drawdown,
    parse_time,
    percentile,
    profit_factor,
    simulate_trade,
    trade_net_r,
    with_indicators,
    write_csv,
    write_json,
)


SYMBOL = "XAUUSD"
POINT = 0.01
DEFAULT_COST_MODEL = Path("..") / "xauusd-phase0" / "outputs" / "reports" / "cost_model_measured.csv"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A3_NET_COST_DEDUPED_REBASELINE_2026_06_19.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "A3_NET_COST_DEDUPED_REBASELINE_2026_06_19.md"
DEFAULT_TRADES_CSV = Path("outputs") / "reports" / "A3_NET_COST_DEDUPED_REBASELINE_TRADES_2026_06_19.csv"

ENTRY_SLIPPAGE_POINTS = 10.0
STOP_EXIT_SLIPPAGE_POINTS = 50.0
MAX_TRADE_COST_R = 0.12
P95_COST_R_LIMIT = 0.10
MAX_DRAWDOWN_R = 8.0
DISCOVERY_MIN_EXPECTANCY_R = 0.10
DISCOVERY_MIN_PF = 1.25
PROMOTION_MIN_EXPECTANCY_R = 0.15
PROMOTION_MIN_PF = 1.30
MIN_CLOSED_TRADES = 100
MIN_LONG_TRADES = 25
MIN_SHORT_TRADES = 25
MIN_WEEKS = 4
MIN_WEEKS_WITH_15 = 3
MIN_B0_RETENTION_PCT = 40.0


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    description: str
    predicate: Callable[[RawSignal, list[Bar]], bool]
    risk_floor_points: float


@dataclass
class CostedTrade:
    signal_id: str
    candidate_id: str
    direction: str
    entry_time: str
    exit_time: str
    session_bucket: str
    h1_regime: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_points: float
    gross_r: float
    charged_spread_points: float
    median_spread_points: float
    p95_spread_points: float
    realized_spread_points: float
    entry_slippage_points: float
    stop_exit_slippage_points: float
    charged_cost_r: float
    p95_spread_cost_r: float
    stress_cost_r: float
    net_r: float
    stress_net_r: float
    cost_guard_pass: bool
    market_day_direction: str
    loss_class: str


def run_net_cost_rebaseline(
    phase1_root: Path,
    *,
    cost_model_csv: Path | None = None,
    output_json: Path | None = None,
    output_md: Path | None = None,
    trades_csv: Path | None = None,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    cost_model_csv = (cost_model_csv or phase1_root / DEFAULT_COST_MODEL).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = (output_md or phase1_root / DEFAULT_OUTPUT_MD).resolve()
    trades_csv = (trades_csv or phase1_root / DEFAULT_TRADES_CSV).resolve()
    phase0_bars = (phase1_root / PHASE0_BARS).resolve()

    m5_path = phase0_bars / "M5" / "XAUUSD_dukascopy_M5_20250102_20250701.csv"
    h1_path = phase0_bars / "H1" / "XAUUSD_dukascopy_H1_20160101_20250701_derived_from_m5.csv"
    d1_path = phase0_bars / "D1" / "XAUUSD_dukascopy_D1_20160101_20250701_derived_from_m5.csv"

    m5 = load_phase0_bars(m5_path, DISCOVERY_START, DISCOVERY_END)
    h1 = with_indicators(load_phase0_bars(h1_path, WARMUP_START, DISCOVERY_END), ema_periods=(20,))
    d1 = with_indicators(load_phase0_bars(d1_path, WARMUP_START, DISCOVERY_END), ema_periods=(20, 50))
    weekly = derive_weekly(d1["bars"])
    cost_model = load_cost_model(cost_model_csv)
    day_directions = market_day_directions(m5)

    raw_signals = generate_breakout_retest_signals(m5, h1, d1, weekly)
    specs = [
        CandidateSpec(
            "B0_RAW_ALL_SESSION",
            "Original breakout-retest signal book, one virtual position at a time.",
            lambda _signal, _m5: True,
            0.0,
        ),
        CandidateSpec(
            "A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2",
            "Soft-retest V2 filter from the A3 signal-quality repair screen, original stop plan.",
            soft_retest_v2,
            0.0,
        ),
        CandidateSpec(
            "A3_WIDE_STOP_800PT_SOFT_RETEST_V0",
            "Soft-retest V2 entries with an A2-style 800-point minimum stop floor and unchanged 1.5R target.",
            soft_retest_v2,
            800.0,
        ),
    ]

    all_trades: list[CostedTrade] = []
    metrics: list[dict[str, Any]] = []
    for spec in specs:
        trades = evaluate_spec(spec, raw_signals, m5, cost_model, day_directions)
        all_trades.extend(trades)
        metrics.append(summarize_candidate(spec, trades))

    b0_screen_closed = next(row for row in metrics if row["candidate_id"] == "B0_RAW_ALL_SESSION")["screen_closed_trades"]
    for row in metrics:
        row["screen_trade_retention_vs_b0_pct"] = pct(row["screen_closed_trades"], b0_screen_closed)
        row["discovery_screen_pass"] = discovery_pass(row)
        row["promotion_threshold_pass"] = promotion_pass(row)
        row["failure_reasons"] = failure_reasons(row)

    payload = {
        "status": "PASS",
        "decision": screen_decision(metrics),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "boundary": (
            "Analysis-only net-of-cost deduped rebaseline. No MT5 terminal, profile, chart, preset, "
            "order, position, or broker runtime state was touched."
        ),
        "data_window": {
            "source": "Phase0 Dukascopy XAUUSD bars",
            "start_utc": fmt_time(DISCOVERY_START),
            "end_utc": fmt_time(DISCOVERY_END),
        },
        "cost_model": {
            "source_csv": str(cost_model_csv),
            "charged_spread_points": "max(realized bar spread, measured median spread for entry UTC hour)",
            "p95_sensitivity_points": "max(realized bar spread, measured P95 spread for entry UTC hour)",
            "entry_slippage_points": ENTRY_SLIPPAGE_POINTS,
            "stop_exit_slippage_points": STOP_EXIT_SLIPPAGE_POINTS,
            "cost_guard": f"trade rejected from screen metrics when charged_cost_R > {MAX_TRADE_COST_R:.2f}",
            "cost_r_note": "Winning trades pay spread + entry slippage; losing trades also pay stop-exit slippage. Default stop-exit slippage is conservative at 50 points after Claude Round 3.",
            "stress_model": "P95 spread plus the same 50-point stop-exit slippage.",
        },
        "provenance": {
            "A3_WIDE_STOP_800PT_SOFT_RETEST_V0": (
                "POST_HOC_EXPLORATORY_ONLY. No pre-registration or hash-lock evidence was found before this "
                "2026-06-19 screen; the 800-point floor was introduced as an A2-style exploratory cost-feasibility floor."
            )
        },
        "acceptance_thresholds": acceptance_thresholds(),
        "raw_signals": len(raw_signals),
        "candidate_metrics": metrics,
        "data_manifest": build_data_manifest([m5_path, h1_path, d1_path, cost_model_csv], extra={"raw_signals": len(raw_signals)}),
        "outputs": {
            "json": str(output_json),
            "markdown": str(output_md),
            "trades_csv": str(trades_csv),
        },
    }
    write_json(output_json, payload)
    write_csv(trades_csv, [asdict(row) for row in all_trades], list(asdict(all_trades[0]).keys()) if all_trades else [])
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def evaluate_spec(
    spec: CandidateSpec,
    raw_signals: list[RawSignal],
    m5: list[Bar],
    cost_model: dict[tuple[str, str], dict[str, float]],
    day_directions: dict[str, str],
) -> list[CostedTrade]:
    trades: list[CostedTrade] = []
    available_at_index = -1
    for signal in raw_signals:
        if not spec.predicate(signal, m5):
            continue
        planned = apply_risk_floor(signal, spec.risk_floor_points)
        raw_trade = simulate_trade(planned, m5)
        if raw_trade is None or planned.confirmation_index <= available_at_index:
            continue
        costed = apply_cost_model(spec.candidate_id, planned, raw_trade, m5, cost_model, day_directions)
        trades.append(costed)
        available_at_index = exit_index_for_trade(raw_trade, m5)
    return trades


def apply_risk_floor(signal: RawSignal, risk_floor_points: float) -> RawSignal:
    if risk_floor_points <= 0 or signal.stop_distance_points >= risk_floor_points:
        return signal
    risk_price = risk_floor_points * POINT
    if signal.direction == "LONG":
        stop = signal.entry_price - risk_price
        target = signal.entry_price + 1.5 * risk_price
    else:
        stop = signal.entry_price + risk_price
        target = signal.entry_price - 1.5 * risk_price
    return replace(
        signal,
        stop_loss=stop,
        take_profit=target,
        stop_distance_points=risk_floor_points,
        cost_r=0.0,
    )


def apply_cost_model(
    candidate_id: str,
    signal: RawSignal,
    trade: VirtualTrade,
    m5: list[Bar],
    cost_model: dict[tuple[str, str], dict[str, float]],
    day_directions: dict[str, str],
) -> CostedTrade:
    entry_time = parse_time(trade.entry_time) or signal.decision_time
    realized_spread = max(0.0, spread_at_signal(signal, m5))
    median_spread = spread_from_model(cost_model, "median_spread_points", entry_time)
    p95_spread = spread_from_model(cost_model, "p95_spread_points", entry_time)
    charged_spread = max(realized_spread, median_spread)
    p95_spread_charged = max(realized_spread, p95_spread)
    stop_exit_slippage = STOP_EXIT_SLIPPAGE_POINTS if trade.final_r < 0 else 0.0
    charged_cost_points = charged_spread + ENTRY_SLIPPAGE_POINTS + stop_exit_slippage
    p95_cost_points = p95_spread_charged + ENTRY_SLIPPAGE_POINTS + stop_exit_slippage
    risk_points = max(signal.stop_distance_points, 0.000001)
    charged_cost_r = charged_cost_points / risk_points
    p95_spread_cost_r = p95_cost_points / risk_points
    stress_cost_r = p95_spread_cost_r
    net_r = trade.final_r - charged_cost_r
    stress_net_r = trade.final_r - stress_cost_r
    entry_day = trade.entry_time[:10]
    return CostedTrade(
        signal_id=trade.signal_id,
        candidate_id=candidate_id,
        direction=trade.direction,
        entry_time=trade.entry_time,
        exit_time=trade.exit_time,
        session_bucket=trade.session_bucket,
        h1_regime=trade.h1_regime,
        entry_price=round(trade.entry_price, 5),
        stop_loss=round(trade.stop_loss, 5),
        take_profit=round(trade.take_profit, 5),
        risk_points=round(risk_points, 2),
        gross_r=round(trade.final_r, 6),
        charged_spread_points=round(charged_spread, 2),
        median_spread_points=round(median_spread, 2),
        p95_spread_points=round(p95_spread, 2),
        realized_spread_points=round(realized_spread, 2),
        entry_slippage_points=ENTRY_SLIPPAGE_POINTS,
        stop_exit_slippage_points=stop_exit_slippage,
        charged_cost_r=round(charged_cost_r, 6),
        p95_spread_cost_r=round(p95_spread_cost_r, 6),
        stress_cost_r=round(stress_cost_r, 6),
        net_r=round(net_r, 6),
        stress_net_r=round(stress_net_r, 6),
        cost_guard_pass=charged_cost_r <= MAX_TRADE_COST_R,
        market_day_direction=day_directions.get(entry_day, "UNKNOWN"),
        loss_class=trade.loss_class,
    )


def summarize_candidate(spec: CandidateSpec, trades: list[CostedTrade]) -> dict[str, Any]:
    screen = [trade for trade in trades if trade.cost_guard_pass]
    raw_net = [trade.net_r for trade in trades]
    raw_stress_net = [trade.stress_net_r for trade in trades]
    screen_net = [trade.net_r for trade in screen]
    screen_stress_net = [trade.stress_net_r for trade in screen]
    gross = [trade.gross_r for trade in trades]
    screen_gross = [trade.gross_r for trade in screen]
    raw_by_day: dict[str, list[CostedTrade]] = {}
    by_week: dict[str, list[CostedTrade]] = {}
    by_day: dict[str, list[CostedTrade]] = {}
    for trade in trades:
        raw_by_day.setdefault(trade.entry_time[:10], []).append(trade)
    for trade in screen:
        dt = parse_time(trade.entry_time)
        week = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}" if dt else "UNKNOWN"
        by_week.setdefault(week, []).append(trade)
        by_day.setdefault(trade.entry_time[:10], []).append(trade)
    raw_day_net = {day: sum(trade.net_r for trade in rows) for day, rows in raw_by_day.items()}
    day_net = {day: sum(trade.net_r for trade in rows) for day, rows in by_day.items()}
    best_days = sorted(day_net.items(), key=lambda item: item[1], reverse=True)
    up_net = sum(trade.net_r for trade in screen if trade.market_day_direction == "UP")
    down_net = sum(trade.net_r for trade in screen if trade.market_day_direction == "DOWN")
    raw_up_net = sum(trade.net_r for trade in trades if trade.market_day_direction == "UP")
    raw_down_net = sum(trade.net_r for trade in trades if trade.market_day_direction == "DOWN")
    longs = sum(1 for trade in screen if trade.direction == "LONG")
    shorts = sum(1 for trade in screen if trade.direction == "SHORT")
    raw_longs = sum(1 for trade in trades if trade.direction == "LONG")
    raw_shorts = sum(1 for trade in trades if trade.direction == "SHORT")
    screen_pf = profit_factor(screen_net)
    raw_pf = profit_factor(raw_net)
    raw_stress_pf = profit_factor(raw_stress_net)
    raw_best_1 = remove_best_days(trades, 1)
    raw_best_2 = remove_best_days(trades, 2)
    raw_worst_1 = remove_worst_days(trades, 1)
    raw_worst_day = min((sum(trade.net_r for trade in rows) for rows in raw_by_day.values()), default=0.0)
    best_1 = remove_best_days(screen, 1)
    best_2 = remove_best_days(screen, 2)
    worst_1 = remove_worst_days(screen, 1)
    worst_day = min((sum(trade.net_r for trade in rows) for rows in by_day.values()), default=0.0)
    stress_pf = profit_factor(screen_stress_net)
    raw_p95_cost = percentile([trade.charged_cost_r for trade in trades], 95)
    raw_max_cost = round(max((trade.charged_cost_r for trade in trades), default=0.0), 4)
    raw_net_exp = round(avg(raw_net), 4) if raw_net else None
    raw_stress_exp = round(avg(raw_stress_net), 4) if raw_stress_net else None
    raw_net_pf = round(raw_pf, 4) if raw_pf is not None and math.isfinite(raw_pf) else raw_pf
    raw_stress_net_pf = round(raw_stress_pf, 4) if raw_stress_pf is not None and math.isfinite(raw_stress_pf) else raw_stress_pf
    raw_significance = significance_summary(raw_net)
    raw_cost_rejects = len(trades) - len(screen)
    raw_cost_gate_pass = (
        bool(trades)
        and raw_p95_cost is not None
        and raw_p95_cost <= P95_COST_R_LIMIT
        and raw_max_cost <= MAX_TRADE_COST_R
        and raw_cost_rejects == 0
    )
    raw_net_gate_pass = (
        raw_net_exp is not None
        and raw_net_exp >= DISCOVERY_MIN_EXPECTANCY_R
        and raw_pf is not None
        and raw_pf >= DISCOVERY_MIN_PF
    )
    raw_stress_gate_pass = (
        raw_stress_exp is not None
        and raw_stress_exp >= DISCOVERY_MIN_EXPECTANCY_R
        and raw_stress_pf is not None
        and raw_stress_pf >= DISCOVERY_MIN_PF
    )
    raw_drawdown_gate_pass = max_drawdown(raw_net) <= MAX_DRAWDOWN_R
    raw_worst_day_gate_pass = raw_worst_1["net_r"] > 0 and raw_worst_1["pf"] > 1.0 and raw_worst_day > -4.0
    raw_robustness_gate_pass = (
        raw_best_1["net_r"] > 0
        and raw_best_2["net_r"] > 0
        and raw_best_1["pf"] > 1.0
        and raw_best_2["pf"] > 1.0
        and raw_up_net > 0
        and raw_down_net > 0
        and raw_drawdown_gate_pass
        and raw_worst_day_gate_pass
    )
    return {
        "candidate_id": spec.candidate_id,
        "description": spec.description,
        "risk_floor_points": spec.risk_floor_points,
        "dedupe_model": "one virtual open position per candidate; raw book first, cost-guard survivor slice shown only as diagnostic unless pre-registered",
        "raw_closed_trades": len(trades),
        "raw_long_trades": raw_longs,
        "raw_short_trades": raw_shorts,
        "raw_cost_rejected_trades": raw_cost_rejects,
        "raw_cost_reject_rate_pct": pct(raw_cost_rejects, len(trades)),
        "raw_max_charged_cost_r": raw_max_cost,
        "raw_p95_charged_cost_r": raw_p95_cost,
        "raw_net_expectancy_r": raw_net_exp,
        "raw_net_pf": raw_net_pf,
        "raw_net_r": round(sum(raw_net), 4),
        "raw_stress_net_expectancy_r": raw_stress_exp,
        "raw_stress_net_pf": raw_stress_net_pf,
        "raw_stress_net_r": round(sum(raw_stress_net), 4),
        "raw_max_drawdown_r": round(max_drawdown(raw_net), 4),
        "raw_worst_day_net_r": round(raw_worst_day, 4),
        "raw_best_2_days_removed_net_r": raw_best_2["net_r"],
        "raw_up_day_net_r": round(raw_up_net, 4),
        "raw_down_day_net_r": round(raw_down_net, 4),
        "raw_significance": raw_significance,
        "raw_net_gate_pass": raw_net_gate_pass,
        "raw_cost_gate_pass": raw_cost_gate_pass,
        "raw_stress_gate_pass": raw_stress_gate_pass,
        "raw_drawdown_gate_pass": raw_drawdown_gate_pass,
        "raw_worst_day_gate_pass": raw_worst_day_gate_pass,
        "raw_robustness_gate_pass": raw_robustness_gate_pass,
        "raw_gross_expectancy_r": round(avg(gross), 4) if gross else None,
        "screen_closed_trades": len(screen),
        "screen_long_trades": longs,
        "screen_short_trades": shorts,
        "screen_weeks": len(by_week),
        "screen_weeks_with_15_trades": sum(1 for rows in by_week.values() if len(rows) >= 15),
        "screen_trade_retention_vs_b0_pct": None,
        "screen_win_rate_pct": pct(sum(1 for value in screen_net if value > 0), len(screen_net)),
        "screen_net_profit_factor": round(screen_pf, 4) if screen_pf is not None and math.isfinite(screen_pf) else screen_pf,
        "screen_net_expectancy_r": round(avg(screen_net), 4) if screen_net else None,
        "screen_net_r": round(sum(screen_net), 4),
        "stress_net_profit_factor": round(stress_pf, 4) if stress_pf is not None and math.isfinite(stress_pf) else stress_pf,
        "stress_net_expectancy_r": round(avg(screen_stress_net), 4) if screen_stress_net else None,
        "stress_net_r": round(sum(screen_stress_net), 4),
        "screen_gross_expectancy_r": round(avg(screen_gross), 4) if screen_gross else None,
        "screen_gross_r": round(sum(screen_gross), 4),
        "screen_max_drawdown_r": round(max_drawdown(screen_net), 4),
        "screen_p50_charged_cost_r": percentile([trade.charged_cost_r for trade in screen], 50),
        "screen_p95_charged_cost_r": percentile([trade.charged_cost_r for trade in screen], 95),
        "screen_p95_spread_sensitivity_cost_r": percentile([trade.p95_spread_cost_r for trade in screen], 95),
        "screen_max_charged_cost_r": round(max((trade.charged_cost_r for trade in screen), default=0.0), 4),
        "screen_up_day_net_r": round(up_net, 4),
        "screen_down_day_net_r": round(down_net, 4),
        "best_1_day_removed_net_r": best_1["net_r"],
        "best_1_day_removed_pf": best_1["pf"],
        "best_2_days_removed_net_r": best_2["net_r"],
        "best_2_days_removed_pf": best_2["pf"],
        "worst_day_net_r": round(worst_day, 4),
        "worst_1_day_removed_net_r": worst_1["net_r"],
        "worst_1_day_removed_pf": worst_1["pf"],
        "best_days": [{"day": day, "net_r": round(value, 4)} for day, value in best_days[:5]],
        "significance": significance_summary(screen_net),
        "sample_gate_pass": len(screen) >= MIN_CLOSED_TRADES and longs >= MIN_LONG_TRADES and shorts >= MIN_SHORT_TRADES,
        "week_gate_pass": len(by_week) >= MIN_WEEKS and sum(1 for rows in by_week.values() if len(rows) >= 15) >= MIN_WEEKS_WITH_15,
        "cost_gate_pass": len(screen) > 0 and percentile([trade.charged_cost_r for trade in screen], 95) is not None and percentile([trade.charged_cost_r for trade in screen], 95) <= P95_COST_R_LIMIT and all(trade.charged_cost_r <= MAX_TRADE_COST_R for trade in screen),
        "drawdown_gate_pass": max_drawdown(screen_net) <= MAX_DRAWDOWN_R,
        "worst_day_gate_pass": worst_1["net_r"] > 0 and worst_1["pf"] > 1.0 and worst_day > -4.0,
        "stress_gate_pass": (
            avg(screen_stress_net) is not None
            and avg(screen_stress_net) >= DISCOVERY_MIN_EXPECTANCY_R
            and stress_pf is not None
            and stress_pf >= DISCOVERY_MIN_PF
        ),
        "robustness_gate_pass": (
            best_1["net_r"] > 0
            and best_2["net_r"] > 0
            and best_1["pf"] > 1.0
            and best_2["pf"] > 1.0
            and up_net > 0
            and down_net > 0
            and max_drawdown(screen_net) <= MAX_DRAWDOWN_R
            and worst_1["net_r"] > 0
            and worst_1["pf"] > 1.0
            and worst_day > -4.0
        ),
    }


def remove_best_days(trades: list[CostedTrade], count: int) -> dict[str, Any]:
    by_day: dict[str, list[CostedTrade]] = {}
    for trade in trades:
        by_day.setdefault(trade.entry_time[:10], []).append(trade)
    ranked = sorted(by_day.items(), key=lambda item: sum(trade.net_r for trade in item[1]), reverse=True)
    remove = {day for day, _rows in ranked[:count]}
    kept = [trade.net_r for trade in trades if trade.entry_time[:10] not in remove]
    pf = profit_factor(kept)
    return {
        "net_r": round(sum(kept), 4),
        "pf": round(pf, 4) if pf is not None and math.isfinite(pf) else pf,
    }


def remove_worst_days(trades: list[CostedTrade], count: int) -> dict[str, Any]:
    by_day: dict[str, list[CostedTrade]] = {}
    for trade in trades:
        by_day.setdefault(trade.entry_time[:10], []).append(trade)
    ranked = sorted(by_day.items(), key=lambda item: sum(trade.net_r for trade in item[1]))
    remove = {day for day, _rows in ranked[:count]}
    kept = [trade.net_r for trade in trades if trade.entry_time[:10] not in remove]
    pf = profit_factor(kept)
    return {
        "net_r": round(sum(kept), 4),
        "pf": round(pf, 4) if pf is not None and math.isfinite(pf) else pf,
    }


def significance_summary(values: list[float]) -> dict[str, Any]:
    if len(values) < 2:
        return {"n": len(values), "mean_r": None, "std_r": None, "t_stat": None, "passes_t_ge_2": False}
    mean = avg(values) or 0.0
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    std = math.sqrt(variance)
    t_stat = mean / (std / math.sqrt(len(values))) if std > 0 else math.inf
    return {
        "n": len(values),
        "mean_r": round(mean, 4),
        "std_r": round(std, 4),
        "t_stat": round(t_stat, 4) if math.isfinite(t_stat) else "inf",
        "passes_t_ge_2": bool(t_stat >= 2.0),
    }


def discovery_pass(row: dict[str, Any]) -> bool:
    return bool(
        row["screen_net_expectancy_r"] is not None
        and row["screen_net_expectancy_r"] >= DISCOVERY_MIN_EXPECTANCY_R
        and row["screen_net_profit_factor"] is not None
        and row["screen_net_profit_factor"] >= DISCOVERY_MIN_PF
        and row["raw_net_gate_pass"]
        and row["raw_cost_gate_pass"]
        and row["raw_stress_gate_pass"]
        and row["raw_drawdown_gate_pass"]
        and row["raw_robustness_gate_pass"]
        and row["raw_significance"]["passes_t_ge_2"]
        and row["sample_gate_pass"]
        and row["week_gate_pass"]
        and row["cost_gate_pass"]
        and row["robustness_gate_pass"]
        and row["stress_gate_pass"]
        and row["significance"]["passes_t_ge_2"]
        and (row["screen_trade_retention_vs_b0_pct"] or 0.0) >= MIN_B0_RETENTION_PCT
    )


def promotion_pass(row: dict[str, Any]) -> bool:
    return bool(
        discovery_pass(row)
        and row["screen_net_expectancy_r"] >= PROMOTION_MIN_EXPECTANCY_R
        and row["screen_net_profit_factor"] >= PROMOTION_MIN_PF
    )


def failure_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not row.get("raw_net_gate_pass"):
        reasons.append("raw_deduped_net_gate_failed")
    if not row.get("raw_cost_gate_pass"):
        reasons.append("raw_cost_discipline_failed")
    if not row.get("raw_stress_gate_pass"):
        reasons.append("raw_p95_spread_50pt_stop_slip_stress_failed")
    if not row.get("raw_drawdown_gate_pass"):
        reasons.append("raw_max_drawdown_above_8R")
    if not row.get("raw_robustness_gate_pass"):
        reasons.append("raw_robustness_failed")
    if not row.get("raw_significance", {}).get("passes_t_ge_2"):
        reasons.append("raw_significance_t_below_2")
    if row["screen_net_expectancy_r"] is None or row["screen_net_expectancy_r"] < DISCOVERY_MIN_EXPECTANCY_R:
        reasons.append("net_expectancy_below_0.10R")
    if row["screen_net_profit_factor"] is None or row["screen_net_profit_factor"] < DISCOVERY_MIN_PF:
        reasons.append("net_pf_below_1.25")
    if not row["sample_gate_pass"]:
        reasons.append("sample_or_direction_floor_failed")
    if not row["week_gate_pass"]:
        reasons.append("week_coverage_failed")
    if not row["cost_gate_pass"]:
        reasons.append("cost_gate_failed")
    if not row.get("stress_gate_pass"):
        reasons.append("p95_spread_50pt_stop_slip_stress_failed")
    if not row["robustness_gate_pass"]:
        reasons.append("robustness_failed")
    if not row.get("drawdown_gate_pass"):
        reasons.append("max_drawdown_above_8R")
    if not row.get("worst_day_gate_pass"):
        reasons.append("worst_day_gate_failed")
    if not row.get("significance", {}).get("passes_t_ge_2"):
        reasons.append("significance_t_below_2")
    if (row["screen_trade_retention_vs_b0_pct"] or 0.0) < MIN_B0_RETENTION_PCT:
        reasons.append("frequency_retention_below_40pct_b0")
    if row.get("discovery_screen_pass") and not row.get("promotion_threshold_pass"):
        reasons.append("discovery_pass_but_promotion_threshold_not_met")
    return reasons


def screen_decision(metrics: list[dict[str, Any]]) -> str:
    eligible = [row["candidate_id"] for row in metrics if row.get("discovery_screen_pass")]
    if not eligible:
        return "NO_CANDIDATE_CLEARS_NET_COST_DISCOVERY_SCREEN"
    return "FORWARD_TICK_VALIDATION_ELIGIBLE: " + ", ".join(eligible)


def acceptance_thresholds() -> dict[str, Any]:
    return {
        "discovery_min_net_expectancy_r": DISCOVERY_MIN_EXPECTANCY_R,
        "discovery_min_net_profit_factor": DISCOVERY_MIN_PF,
        "promotion_min_net_expectancy_r": PROMOTION_MIN_EXPECTANCY_R,
        "promotion_min_net_profit_factor": PROMOTION_MIN_PF,
        "min_closed_net_trades": MIN_CLOSED_TRADES,
        "min_long_trades": MIN_LONG_TRADES,
        "min_short_trades": MIN_SHORT_TRADES,
        "min_weeks": MIN_WEEKS,
        "min_weeks_with_15_trades": MIN_WEEKS_WITH_15,
        "min_trade_retention_vs_b0_pct": MIN_B0_RETENTION_PCT,
        "max_trade_cost_r": MAX_TRADE_COST_R,
        "max_p95_cost_r": P95_COST_R_LIMIT,
        "max_drawdown_r": MAX_DRAWDOWN_R,
        "min_t_stat": 2.0,
        "robustness": "positive after best 1 and best 2 days removed; positive after worst day removed; worst day > -4R; positive aggregate on both up and down market days",
    }


def load_cost_model(path: Path) -> dict[tuple[str, str], dict[str, float]]:
    model: dict[tuple[str, str], dict[str, float]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            symbol = row.get("symbol", "")
            scope = row.get("scope", "")
            bucket = row.get("bucket", "")
            if symbol != SYMBOL:
                continue
            key = (symbol, "global" if scope == "global" else f"{scope}:{bucket}")
            model[key] = {
                "median_spread_points": to_float(row.get("median_spread_points"), 50.0),
                "p95_spread_points": to_float(row.get("p95_spread_points"), 75.0),
            }
    return model


def spread_from_model(model: dict[tuple[str, str], dict[str, float]], field: str, timestamp: datetime) -> float:
    hour_key = (SYMBOL, f"hour_utc:{timestamp.hour}")
    global_key = (SYMBOL, "global")
    row = model.get(hour_key) or model.get(global_key) or {}
    return float(row.get(field, 50.0 if "median" in field else 75.0))


def spread_at_signal(signal: RawSignal, m5: list[Bar]) -> float:
    if 0 <= signal.confirmation_index < len(m5):
        return max(0.0, m5[signal.confirmation_index].spread)
    return 0.0


def market_day_directions(m5: list[Bar]) -> dict[str, str]:
    by_day: dict[str, list[Bar]] = {}
    for bar in m5:
        by_day.setdefault(fmt_time(bar.start)[:10], []).append(bar)
    output: dict[str, str] = {}
    for day, rows in by_day.items():
        rows = sorted(rows, key=lambda item: item.start)
        if rows[-1].close > rows[0].open:
            output[day] = "UP"
        elif rows[-1].close < rows[0].open:
            output[day] = "DOWN"
        else:
            output[day] = "FLAT"
    return output


def pct(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator * 100.0, 2)


def avg(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def to_float(value: str | None, default: float) -> float:
    try:
        return float(str(value or "").strip())
    except ValueError:
        return default


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A3 Net-Of-Cost Deduped Rebaseline - 2026-06-19",
        "",
        f"Status: `{payload['status']}`",
        f"Decision: `{payload['decision']}`",
        "",
        payload["boundary"],
        "",
        "## Cost Model",
        "",
    ]
    for key, value in payload["cost_model"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Thresholds",
            "",
            "| Gate | Value |",
            "| --- | ---: |",
        ]
    )
    for key, value in payload["acceptance_thresholds"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Raw Deduped Gate",
            "",
            "| Candidate | Raw trades | Long | Short | Cost rejects | Reject rate | Raw PF | Raw exp R | Raw R | Raw stress PF | Raw stress exp R | Raw P95 cost R | Raw max DD R | Raw worst day R | Raw t-stat | Raw net | Raw cost | Raw stress | Raw DD | Raw robust |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["candidate_metrics"]:
        raw_sig = row.get("raw_significance", {})
        lines.append(
            "| {candidate_id} | {raw_closed_trades} | {raw_long_trades} | {raw_short_trades} | "
            "{raw_cost_rejected_trades} | {raw_cost_reject_rate_pct}% | {raw_net_pf} | {raw_net_expectancy_r} | "
            "{raw_net_r} | {raw_stress_net_pf} | {raw_stress_net_expectancy_r} | {raw_p95_charged_cost_r} | "
            "{raw_max_drawdown_r} | {raw_worst_day_net_r} | {raw_t_stat} | {raw_net_gate_pass} | "
            "{raw_cost_gate_pass} | {raw_stress_gate_pass} | {raw_drawdown_gate_pass} | {raw_robustness_gate_pass} |".format(
                **row,
                raw_t_stat=raw_sig.get("t_stat"),
            )
        )
    lines.extend(
        [
            "",
            "## Cost-Guard Survivor Diagnostics",
            "",
            "These rows are diagnostic only. They show what remains after `cost_R <= 0.12`, but they do not by themselves prove edge because the cost filter was not pre-registered as an entry rule for these candidates.",
            "",
            "| Candidate | Raw trades | Cost rejects | Screen trades | Long | Short | Ret. vs B0 | WR | Net PF | Net exp R | Net R | P95 cost R | Raw P95 cost R | Best 2 days removed R | Up-day R | Down-day R | Discovery pass | Promotion pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in payload["candidate_metrics"]:
        lines.append(
            "| {candidate_id} | {raw_closed_trades} | {raw_cost_rejected_trades} | {screen_closed_trades} | "
            "{screen_long_trades} | {screen_short_trades} | {screen_trade_retention_vs_b0_pct}% | "
            "{screen_win_rate_pct}% | {screen_net_profit_factor} | {screen_net_expectancy_r} | {screen_net_r} | "
            "{screen_p95_charged_cost_r} | {raw_p95_charged_cost_r} | {best_2_days_removed_net_r} | "
            "{screen_up_day_net_r} | {screen_down_day_net_r} | {discovery_screen_pass} | {promotion_threshold_pass} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Cost-Guard Survivor Stress Diagnostics",
            "",
            "Diagnostic only; these numbers are after dropping high-cost trades and are not the approval gate.",
            "",
            "| Candidate | Stress PF | Stress exp R | Max DD R | Worst day R | Worst-day removed R | t-stat | 800-floor provenance |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    provenance = payload.get("provenance", {})
    for row in payload["candidate_metrics"]:
        sig = row.get("significance", {})
        lines.append(
            "| {candidate_id} | {stress_net_profit_factor} | {stress_net_expectancy_r} | "
            "{screen_max_drawdown_r} | {worst_day_net_r} | {worst_1_day_removed_net_r} | "
            "{t_stat} | {provenance} |".format(
                **row,
                t_stat=sig.get("t_stat"),
                provenance=provenance.get(row["candidate_id"], ""),
            )
        )
    lines.extend(
        [
            "",
            "## Gate Diagnostics",
            "",
            "| Candidate | Raw net | Raw cost | Raw stress | Raw DD | Raw robust | Raw sig | Screen sample | Screen weeks | Survivor cost | Discovery | Failure reasons |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["candidate_metrics"]:
        lines.append(
            "| {candidate_id} | {raw_net_gate_pass} | {raw_cost_gate_pass} | {raw_stress_gate_pass} | "
            "{raw_drawdown_gate_pass} | {raw_robustness_gate_pass} | {raw_significance_pass} | "
            "{sample_gate_pass} | {week_gate_pass} | {cost_gate_pass} | {discovery_screen_pass} | "
            "{failure_reasons} |".format(
                **row,
                raw_significance_pass=row.get("raw_significance", {}).get("passes_t_ge_2"),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is the first A3 screen that charges a non-zero measured spread floor plus slippage.",
            "- Raw deduped metrics are now the primary gate; survivor metrics after `cost_R <= 0.12` are diagnostic only unless the filter is pre-registered.",
            "- Round 3 raised default stop-exit slippage to 50 points and added stress, max-drawdown, worst-day, and t-stat gates.",
            "- Raw cost rejection count is not hidden; it shows how much of each candidate is structurally too tight for the measured cost floor.",
            "- The 800-point wide-stop variant remains exploratory/post-hoc and does not clear the updated screen.",
            "- A candidate must pass on the raw deduped net book and the P95-stress book before it can earn forward tick-level validation.",
            "",
            "## Outputs",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run A3 net-of-cost deduped discovery rebaseline.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cost-model-csv", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_net_cost_rebaseline(args.root, cost_model_csv=args.cost_model_csv)
    print(f"A3 net-cost rebaseline: {payload['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
