from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ACCOUNT = "1033669"
SYMBOL = "XAUUSD"
POINT = 0.01
DEFAULT_BARS_DIR = Path("outputs") / "reports" / "m5_replay_bars"
DEFAULT_MFE_MAE = Path("outputs") / "reports" / "MFE_MAE_2026_06_16.csv"
DEFAULT_OUTPUT_JSON = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_2026_06_18.json"
DEFAULT_OUTPUT_MD = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_2026_06_18.md"
DEFAULT_DECISIONS_CSV = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_DECISIONS_2026_06_18.csv"
DEFAULT_TRADES_CSV = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_TRADES_2026_06_18.csv"
DEFAULT_DATA_MANIFEST = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_SQ03_OFFLINE_DISCOVERY_DATA_MANIFEST_2026_06_18.json"

CANDIDATE_IDS = [
    "B0_RAW_ALL_SESSION",
    "B1_EVENING_BASELINE",
    "F_LOOSE_CT_VETO",
    "F_H1_ALIGN",
    "F_H1_M15_ALIGN",
    "F_RETEST_LIGHT",
    "F_LOOSE_CT_PLUS_RETEST_LIGHT",
    "A3_SQ_MTF_ONLY_V1",
    "A3_SQ_RETEST_ONLY_V1",
    "A3_SQ_COMBINED_V1",
]


@dataclass(frozen=True)
class Bar:
    start: datetime
    end: datetime
    open: float
    high: float
    low: float
    close: float
    spread: float


@dataclass(frozen=True)
class RawSignal:
    signal_id: str
    direction: str
    decision_time: datetime
    confirmation_index: int
    retest_index: int
    break_index: int
    break_shift: int
    level_kind: str
    level_price: float
    entry_price: float
    stop_loss: float
    take_profit: float
    stop_distance_points: float
    cost_r: float
    session_bucket: str
    h1_slope_points: float | None
    h1_regime: str


@dataclass
class VirtualTrade:
    signal_id: str
    candidate_id: str
    direction: str
    entry_time: str
    exit_time: str
    entry_price: float
    stop_loss: float
    take_profit: float
    final_r: float
    outcome: str
    mfe_r: float
    mae_r: float
    cost_r: float
    loss_class: str
    session_bucket: str
    h1_regime: str


@dataclass
class DecisionRow:
    signal_id: str
    candidate_id: str
    decision_time: str
    direction: str
    keep: bool
    opened: bool
    reason: str
    session_bucket: str
    h1_regime: str
    final_r_if_raw: float | None


def run_offline_discovery(
    phase1_root: Path,
    *,
    bars_dir: Path | None = None,
    mfe_mae_csv: Path | None = None,
    output_json: Path | None = None,
    output_md: Path | None = None,
    decisions_csv: Path | None = None,
    trades_csv: Path | None = None,
    data_manifest_json: Path | None = None,
) -> dict[str, Any]:
    phase1_root = phase1_root.resolve()
    bars_dir = (bars_dir or phase1_root / DEFAULT_BARS_DIR).resolve()
    mfe_mae_csv = (mfe_mae_csv or phase1_root / DEFAULT_MFE_MAE).resolve()
    output_json = (output_json or phase1_root / DEFAULT_OUTPUT_JSON).resolve()
    output_md = (output_md or phase1_root / DEFAULT_OUTPUT_MD).resolve()
    decisions_csv = (decisions_csv or phase1_root / DEFAULT_DECISIONS_CSV).resolve()
    trades_csv = (trades_csv or phase1_root / DEFAULT_TRADES_CSV).resolve()
    data_manifest_json = (data_manifest_json or phase1_root / DEFAULT_DATA_MANIFEST).resolve()

    m5 = load_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")
    h1 = with_indicators(load_bars(bars_dir / "XAUUSD_H1_20260601_to_latest.csv"), ema_periods=(20,))
    d1 = with_indicators(load_bars(bars_dir / "XAUUSD_D1_20260601_to_latest.csv"), ema_periods=(20, 50))
    m15 = with_indicators(derive_m15(m5), ema_periods=(20,))
    weekly = derive_weekly(d1["bars"])
    mfe_rows = read_csv(mfe_mae_csv)

    raw_signals = generate_breakout_retest_signals(m5, h1, d1, weekly)
    raw_outcomes = {signal.signal_id: simulate_trade(signal, m5) for signal in raw_signals}
    decisions, trades, metrics = evaluate_candidates(raw_signals, raw_outcomes, m5, h1, m15, d1)
    data_manifest = build_data_manifest(
        [
            bars_dir / "XAUUSD_M5_20260601_to_latest.csv",
            bars_dir / "XAUUSD_H1_20260601_to_latest.csv",
            bars_dir / "XAUUSD_D1_20260601_to_latest.csv",
            mfe_mae_csv,
        ],
        extra={
            "derived_m15_rows": len(m15["bars"]),
            "derived_weekly_rows": len(weekly),
            "mfe_mae_rows": len(mfe_rows),
            "mfe_mae_path_snapshot_rows": sum(1 for row in mfe_rows if row.get("source") == "PATH_SNAPSHOTS"),
        },
    )
    decision = discovery_decision(metrics)
    payload = {
        "status": "PASS",
        "decision": decision,
        "created_at_utc": now_utc(),
        "boundary": "Offline discovery only. M5 bar replay is not promotion evidence. No MT5 runtime, profile, preset, order, position, or broker action touched.",
        "account": ACCOUNT,
        "symbol": SYMBOL,
        "data_status": "DATA_LIMITED_M5_BAR_REPLAY_NOT_PROMOTION_EVIDENCE",
        "raw_signals": len(raw_signals),
        "closed_raw_outcomes": sum(1 for item in raw_outcomes.values() if item is not None),
        "candidate_metrics": metrics,
        "data_manifest": data_manifest,
        "outputs": {
            "json": str(output_json),
            "markdown": str(output_md),
            "decisions_csv": str(decisions_csv),
            "trades_csv": str(trades_csv),
            "data_manifest": str(data_manifest_json),
        },
    }
    write_decisions(decisions_csv, decisions)
    write_trades(trades_csv, trades)
    write_json(data_manifest_json, data_manifest)
    write_json(output_json, payload)
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def generate_breakout_retest_signals(
    m5: list[Bar],
    h1: dict[str, Any],
    d1: dict[str, Any],
    weekly: list[Bar],
) -> list[RawSignal]:
    signals: list[RawSignal] = []
    for confirmation_index in range(79, len(m5) - 1):
        confirmation = m5[confirmation_index]
        if confirmation.close == confirmation.open:
            continue
        is_long = confirmation.close > confirmation.open
        signal = evaluate_breakout_retest_at(m5, h1, d1, weekly, confirmation_index, is_long)
        if signal is not None:
            signals.append(signal)
    return signals


def evaluate_breakout_retest_at(
    m5: list[Bar],
    h1: dict[str, Any],
    d1: dict[str, Any],
    weekly: list[Bar],
    i: int,
    is_long: bool,
) -> RawSignal | None:
    retest_index = shift_index(i, 2)
    if retest_index < 0:
        return None
    retest = m5[retest_index]
    retest_atr = average_range(m5, i, 2, 14)
    if retest_atr <= 0.0:
        return None

    best: dict[str, Any] | None = None
    for break_shift in range(3, 23):
        break_index = shift_index(i, break_shift)
        if break_index < 0:
            continue
        break_bar = m5[break_index]
        break_atr = average_range(m5, i, break_shift, 14)
        if break_atr <= 0.0:
            continue
        for level_kind, level_price in candidate_levels(m5, d1["bars"], weekly, i, break_shift, is_long):
            if not break_valid(break_bar.close, break_atr, level_price, is_long):
                continue
            if not retest_valid(retest, level_price, 5.0 * POINT, is_long):
                continue
            plan = build_plan(retest, retest_atr, is_long)
            if plan["stop_distance_points"] <= 0.0:
                continue
            candidate = {
                **plan,
                "level_kind": level_kind,
                "level_price": level_price,
                "break_shift": break_shift,
                "break_index": break_index,
            }
            if best is None or candidate["stop_distance_points"] < best["stop_distance_points"]:
                best = candidate
    if best is None:
        return None

    direction = "LONG" if is_long else "SHORT"
    h1_slope = htf_slope(h1, m5[i].end, 20)
    session = dubai_session(m5[i].end)
    level = float(best["level_price"])
    signal_id = "|".join(
        [
            ACCOUNT,
            SYMBOL,
            "breakout_retest",
            direction,
            fmt_time(m5[int(best["break_index"])].start),
            fmt_time(m5[retest_index].start),
            fmt_time(m5[i].start),
            f"{level:.2f}",
        ]
    )
    spread_points = max(0.0, m5[i].spread)
    cost_r = spread_points / float(best["stop_distance_points"]) if best["stop_distance_points"] else math.inf
    return RawSignal(
        signal_id=signal_id,
        direction=direction,
        decision_time=m5[i].end,
        confirmation_index=i,
        retest_index=retest_index,
        break_index=int(best["break_index"]),
        break_shift=int(best["break_shift"]),
        level_kind=str(best["level_kind"]),
        level_price=level,
        entry_price=float(best["entry_price"]),
        stop_loss=float(best["stop_loss"]),
        take_profit=float(best["take_profit"]),
        stop_distance_points=float(best["stop_distance_points"]),
        cost_r=cost_r,
        session_bucket=session,
        h1_slope_points=h1_slope,
        h1_regime=regime_from_slope(h1_slope),
    )


def evaluate_candidates(
    raw_signals: list[RawSignal],
    raw_outcomes: dict[str, VirtualTrade | None],
    m5: list[Bar],
    h1: dict[str, Any],
    m15: dict[str, Any],
    d1: dict[str, Any],
) -> tuple[list[DecisionRow], list[VirtualTrade], list[dict[str, Any]]]:
    decisions: list[DecisionRow] = []
    trades: list[VirtualTrade] = []
    metrics_rows: list[dict[str, Any]] = []
    b0_closed = [trade for trade in raw_outcomes.values() if trade is not None]
    b0_expectancy = avg([trade.final_r for trade in b0_closed])
    b0_pf = profit_factor([trade.final_r for trade in b0_closed])
    b0_bad_share = bad_signal_share(b0_closed)
    for candidate_id in CANDIDATE_IDS:
        opened_trades: list[VirtualTrade] = []
        accepted = 0
        blocked_raw_final_rs: list[float] = []
        candidate_available_at_index = -1
        for signal in raw_signals:
            keep, reason = candidate_decision(candidate_id, signal, m5, h1, m15, d1)
            raw_trade = raw_outcomes.get(signal.signal_id)
            raw_final_r = raw_trade.final_r if raw_trade else None
            opened = False
            if keep:
                accepted += 1
                if raw_trade is not None and signal.confirmation_index > candidate_available_at_index:
                    clone = VirtualTrade(**asdict(raw_trade))
                    clone.candidate_id = candidate_id
                    opened_trades.append(clone)
                    trades.append(clone)
                    opened = True
                    candidate_available_at_index = exit_index_for_trade(raw_trade, m5)
                elif raw_trade is None:
                    reason = "NO_CLOSED_M5_OUTCOME"
                else:
                    reason = "VIRTUAL_POSITION_ALREADY_OPEN"
            elif raw_final_r is not None:
                blocked_raw_final_rs.append(raw_final_r)
            decisions.append(
                DecisionRow(
                    signal_id=signal.signal_id,
                    candidate_id=candidate_id,
                    decision_time=fmt_time(signal.decision_time),
                    direction=signal.direction,
                    keep=keep,
                    opened=opened,
                    reason=reason,
                    session_bucket=signal.session_bucket,
                    h1_regime=signal.h1_regime,
                    final_r_if_raw=raw_final_r,
                )
            )
        metrics = candidate_metrics(
            candidate_id,
            raw_signals,
            accepted,
            opened_trades,
            blocked_raw_final_rs,
            b0_pf,
            b0_expectancy,
            b0_bad_share,
        )
        trades_for_candidate = [trade for trade in opened_trades if trade.candidate_id == candidate_id]
        metrics["sample_rows"] = [asdict(row) for row in trades_for_candidate[:5]]
        metrics["blocked_bucket_expectancy_r"] = round(avg(blocked_raw_final_rs), 4) if blocked_raw_final_rs else None
        metrics["kept_bucket_expectancy_r"] = metrics["expectancy_r"]
        metrics["blocked_bucket_worse_than_kept"] = (
            metrics["blocked_bucket_expectancy_r"] is not None
            and metrics["expectancy_r"] is not None
            and metrics["blocked_bucket_expectancy_r"] < metrics["expectancy_r"]
        )
        metrics["bad_signal_loss_share_improvement_pct"] = improvement_pct(
            b0_bad_share,
            metrics["bad_signal_loss_share_pct"],
        )
        metrics["v2_registration_eligible"] = v2_registration_eligible(metrics)
        metrics["candidate_role"] = candidate_role(candidate_id)
        metrics["promotion_evidence"] = False
        metrics["data_limitation"] = "M5 bar replay only; not forward tick-level promotion evidence."
        metrics_rows.append(metrics)
    return decisions, trades, metrics_rows


def candidate_metrics(
    candidate_id: str,
    raw_signals: list[RawSignal],
    accepted: int,
    opened_trades: list[VirtualTrade],
    blocked_raw_final_rs: list[float],
    b0_pf: float | None,
    b0_expectancy: float | None,
    b0_bad_share: float | None,
) -> dict[str, Any]:
    final_rs = [trade.final_r for trade in opened_trades]
    closed = len(final_rs)
    wins = sum(1 for value in final_rs if value > 0)
    losses = sum(1 for value in final_rs if value < 0)
    pf = profit_factor(final_rs)
    expectancy = avg(final_rs)
    bad_share = bad_signal_share(opened_trades)
    giveback_share = giveback_share_pct(opened_trades)
    net = sum(final_rs)
    by_week: dict[str, list[float]] = {}
    by_day_positive: dict[str, float] = {}
    regimes = {trade.h1_regime for trade in opened_trades if trade.h1_regime in {"RISING", "FALLING"}}
    for trade in opened_trades:
        dt = parse_time(trade.entry_time)
        week = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}" if dt else "UNKNOWN"
        by_week.setdefault(week, []).append(trade.final_r)
        day = trade.entry_time[:10]
        if trade.final_r > 0:
            by_day_positive[day] = by_day_positive.get(day, 0.0) + trade.final_r
    positive = [value for value in final_rs if value > 0]
    largest = max(positive, default=0.0)
    top5 = sum(sorted(positive, reverse=True)[:5])
    positive_sum = sum(positive)
    best_day = max(by_day_positive.values(), default=0.0)
    return {
        "candidate_id": candidate_id,
        "raw_base_signals": len(raw_signals),
        "accepted_signals": accepted,
        "signal_retention_pct": pct(accepted, len(raw_signals)),
        "opened_virtual_trades": len(opened_trades),
        "virtual_trade_retention_pct": pct(len(opened_trades), len(raw_signals)),
        "closed_trades": closed,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": pct(wins, closed) if closed else None,
        "profit_factor": round(pf, 4) if pf is not None else None,
        "profit_factor_delta_vs_b0": round(pf - b0_pf, 4) if pf is not None and b0_pf is not None else None,
        "expectancy_r": round(expectancy, 4) if expectancy is not None else None,
        "expectancy_delta_vs_b0": round(expectancy - b0_expectancy, 4) if expectancy is not None and b0_expectancy is not None else None,
        "net_r": round(net, 4),
        "max_drawdown_r": round(max_drawdown(final_rs), 4),
        "max_consecutive_losses": max_consecutive_losses(final_rs),
        "p50_cost_r": percentile([trade.cost_r for trade in opened_trades], 50),
        "p95_cost_r": percentile([trade.cost_r for trade in opened_trades], 95),
        "largest_trade_contribution_pct": pct(largest, net) if net > 0 else None,
        "top_five_contribution_pct": pct(top5, net) if net > 0 else None,
        "best_day_contribution_pct": pct(best_day, positive_sum) if positive_sum > 0 else None,
        "weekly_pf": {week: round(profit_factor(values) or 0.0, 4) for week, values in sorted(by_week.items())},
        "weeks_with_15_trades": sum(1 for values in by_week.values() if len(values) >= 15),
        "median_weekly_trades": median([len(values) for values in by_week.values()]),
        "regime_coverage": sorted(regimes),
        "both_rising_and_falling_regimes": {"RISING", "FALLING"}.issubset(regimes),
        "bad_signal_loss_share_pct": bad_share,
        "giveback_loss_share_pct": giveback_share,
        "blocked_raw_count": len(blocked_raw_final_rs),
    }


def candidate_decision(
    candidate_id: str,
    signal: RawSignal,
    m5: list[Bar],
    h1: dict[str, Any],
    m15: dict[str, Any],
    d1: dict[str, Any],
) -> tuple[bool, str]:
    if candidate_id == "B0_RAW_ALL_SESSION":
        return True, "KEEP_RAW"
    if candidate_id == "B1_EVENING_BASELINE":
        return (signal.session_bucket == "Evening 16:00-19:59", "KEEP_EVENING" if signal.session_bucket == "Evening 16:00-19:59" else "BLOCK_NOT_EVENING")
    if candidate_id == "F_LOOSE_CT_VETO":
        return loose_ct_veto(signal)
    if candidate_id == "F_H1_ALIGN":
        return htf_align(signal, h1, "H1")
    if candidate_id == "F_H1_M15_ALIGN":
        h1_keep, h1_reason = htf_align(signal, h1, "H1")
        if not h1_keep:
            return False, h1_reason
        return htf_align(signal, m15, "M15")
    if candidate_id == "F_RETEST_LIGHT":
        return retest_light(signal, m5)
    if candidate_id == "F_LOOSE_CT_PLUS_RETEST_LIGHT":
        trend_keep, trend_reason = loose_ct_veto(signal)
        if not trend_keep:
            return False, trend_reason
        return retest_light(signal, m5)
    if candidate_id == "A3_SQ_MTF_ONLY_V1":
        return mtf_v1(signal, h1, m15, d1)
    if candidate_id == "A3_SQ_RETEST_ONLY_V1":
        return retest_strict_v1(signal, m5)
    if candidate_id == "A3_SQ_COMBINED_V1":
        mtf_keep, mtf_reason = mtf_v1(signal, h1, m15, d1)
        if not mtf_keep:
            return False, mtf_reason
        return retest_strict_v1(signal, m5)
    return False, "UNKNOWN_CANDIDATE"


def loose_ct_veto(signal: RawSignal) -> tuple[bool, str]:
    if signal.h1_slope_points is None:
        return False, "DATA_UNAVAILABLE_H1"
    if signal.direction == "LONG" and signal.h1_slope_points <= -50.0:
        return False, "BLOCK_STRONG_H1_COUNTER_TREND"
    if signal.direction == "SHORT" and signal.h1_slope_points >= 50.0:
        return False, "BLOCK_STRONG_H1_COUNTER_TREND"
    return True, "KEEP_LOOSE_CT"


def htf_align(signal: RawSignal, series: dict[str, Any], label: str) -> tuple[bool, str]:
    idx = completed_index(series["bars"], signal.decision_time)
    if idx is None or idx < 3:
        return False, f"DATA_UNAVAILABLE_{label}"
    ema20 = series["ema20"]
    if ema20[idx] is None or ema20[idx - 3] is None:
        return False, f"DATA_UNAVAILABLE_{label}_EMA20"
    close = series["bars"][idx].close
    if signal.direction == "LONG" and close > ema20[idx] and ema20[idx] > ema20[idx - 3]:
        return True, f"KEEP_{label}_ALIGN"
    if signal.direction == "SHORT" and close < ema20[idx] and ema20[idx] < ema20[idx - 3]:
        return True, f"KEEP_{label}_ALIGN"
    return False, f"BLOCK_{label}_NOT_ALIGNED"


def mtf_v1(signal: RawSignal, h1: dict[str, Any], m15: dict[str, Any], d1: dict[str, Any]) -> tuple[bool, str]:
    d1_idx = completed_index(d1["bars"], signal.decision_time)
    if d1_idx is None:
        return False, "DATA_UNAVAILABLE_D1"
    if d1["ema20"][d1_idx] is None or d1["ema50"][d1_idx] is None:
        return False, "DATA_UNAVAILABLE_D1_EMA"
    d1_bar = d1["bars"][d1_idx]
    if signal.direction == "LONG":
        if not (d1_bar.close > d1["ema20"][d1_idx] > d1["ema50"][d1_idx]):
            return False, "BLOCK_D1_BIAS"
    else:
        if not (d1_bar.close < d1["ema20"][d1_idx] < d1["ema50"][d1_idx]):
            return False, "BLOCK_D1_BIAS"
    h1_slope = htf_slope(h1, signal.decision_time, 20)
    m15_slope = htf_slope(m15, signal.decision_time, 20)
    if h1_slope is None:
        return False, "DATA_UNAVAILABLE_H1"
    if m15_slope is None:
        return False, "DATA_UNAVAILABLE_M15"
    if signal.direction == "LONG" and h1_slope >= 50.0 and m15_slope >= 50.0:
        return True, "KEEP_MTF_V1"
    if signal.direction == "SHORT" and h1_slope <= -50.0 and m15_slope <= -50.0:
        return True, "KEEP_MTF_V1"
    return False, "BLOCK_MTF_V1"


def retest_light(signal: RawSignal, m5: list[Bar]) -> tuple[bool, str]:
    bars_after_break = signal.retest_index - signal.break_index
    if bars_after_break < 1 or bars_after_break > 10:
        return False, "BLOCK_RETEST_LIGHT_WINDOW"
    if invalid_close_between(m5, signal, include_retest=True):
        return False, "BLOCK_RETEST_LIGHT_INVALID_CLOSE"
    confirmation = m5[signal.confirmation_index]
    body_range = body_to_range(confirmation)
    if body_range is None or body_range < 0.40:
        return False, "BLOCK_RETEST_LIGHT_BODY"
    close_loc = close_location(confirmation)
    if close_loc is None:
        return False, "BLOCK_RETEST_LIGHT_CLOSE_LOCATION_DATA"
    if signal.direction == "LONG":
        if close_loc < 0.65 or confirmation.close <= signal.level_price:
            return False, "BLOCK_RETEST_LIGHT_CLOSE_LOCATION"
    else:
        if close_loc > 0.35 or confirmation.close >= signal.level_price:
            return False, "BLOCK_RETEST_LIGHT_CLOSE_LOCATION"
    return True, "KEEP_RETEST_LIGHT"


def retest_strict_v1(signal: RawSignal, m5: list[Bar]) -> tuple[bool, str]:
    bars_after_break = signal.retest_index - signal.break_index
    if bars_after_break < 1 or bars_after_break > 5:
        return False, "BLOCK_RETEST_V1_WINDOW"
    if not first_retest_only(m5, signal):
        return False, "BLOCK_RETEST_V1_NOT_FIRST_RETEST"
    retest = m5[signal.retest_index]
    confirmation = m5[signal.confirmation_index]
    retest_atr = average_range(m5, signal.confirmation_index, 2, 14)
    if retest_atr <= 0.0:
        return False, "DATA_UNAVAILABLE_RETEST_ATR"
    penetration = max(0.0, signal.level_price - retest.low) if signal.direction == "LONG" else max(0.0, retest.high - signal.level_price)
    if penetration > 0.15 * retest_atr:
        return False, "BLOCK_RETEST_V1_PENETRATION"
    if signal.direction == "LONG" and retest.close < signal.level_price + 0.05 * retest_atr:
        return False, "BLOCK_RETEST_V1_RETEST_CLOSE"
    if signal.direction == "SHORT" and retest.close > signal.level_price - 0.05 * retest_atr:
        return False, "BLOCK_RETEST_V1_RETEST_CLOSE"
    if invalid_close_between(m5, signal, include_retest=True):
        return False, "BLOCK_RETEST_V1_INVALID_CLOSE"
    body_range = body_to_range(confirmation)
    if body_range is None or body_range < 0.60:
        return False, "BLOCK_RETEST_V1_BODY"
    loc = close_location(confirmation)
    if loc is None:
        return False, "BLOCK_RETEST_V1_CLOSE_LOCATION_DATA"
    rng = confirmation.high - confirmation.low
    if signal.direction == "LONG":
        lower_wick = min(confirmation.open, confirmation.close) - confirmation.low
        if loc < 0.80 or lower_wick > 0.25 * rng or confirmation.close <= retest.high:
            return False, "BLOCK_RETEST_V1_CONFIRMATION"
    else:
        upper_wick = confirmation.high - max(confirmation.open, confirmation.close)
        if loc > 0.20 or upper_wick > 0.25 * rng or confirmation.close >= retest.low:
            return False, "BLOCK_RETEST_V1_CONFIRMATION"
    return True, "KEEP_RETEST_V1"


def simulate_trade(signal: RawSignal, m5: list[Bar]) -> VirtualTrade | None:
    is_long = signal.direction == "LONG"
    entry = signal.entry_price
    sl = signal.stop_loss
    tp = signal.take_profit
    risk = abs(entry - sl)
    if risk <= 0.0:
        return None
    mfe = 0.0
    mae = 0.0
    for index in range(signal.confirmation_index + 1, len(m5)):
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
            outcome = "LOSS" if final_r < 0 else "WIN"
            trade = VirtualTrade(
                signal_id=signal.signal_id,
                candidate_id="B0_RAW_ALL_SESSION",
                direction=signal.direction,
                entry_time=fmt_time(signal.decision_time),
                exit_time=fmt_time(bar.end),
                entry_price=entry,
                stop_loss=sl,
                take_profit=tp,
                final_r=final_r,
                outcome=outcome,
                mfe_r=round(mfe, 4),
                mae_r=round(mae, 4),
                cost_r=round(signal.cost_r, 4),
                loss_class=loss_class(final_r, mfe, mae),
                session_bucket=signal.session_bucket,
                h1_regime=signal.h1_regime,
            )
            return trade
    return None


def loss_class(final_r: float, mfe_r: float, mae_r: float) -> str:
    if final_r > 0:
        return "WIN"
    if mae_r >= 0.50 and mfe_r < 0.50:
        return "BAD_SIGNAL"
    if mfe_r < 0.50:
        return "BAD_SIGNAL"
    if mfe_r < 0.75:
        return "MIXED"
    if mfe_r >= 1.25:
        return "NEAR_TP_GIVEBACK"
    return "BAD_EXIT_GIVEBACK"


def v2_registration_eligible(metrics: dict[str, Any]) -> bool:
    pf = metrics.get("profit_factor")
    exp = metrics.get("expectancy_r")
    pf_delta = metrics.get("profit_factor_delta_vs_b0")
    exp_delta = metrics.get("expectancy_delta_vs_b0")
    return bool(
        metrics.get("signal_retention_pct", 0.0) >= 40.0
        and metrics.get("virtual_trade_retention_pct", 0.0) >= 35.0
        and metrics.get("closed_trades", 0) >= 100
        and pf is not None
        and pf >= 1.20
        and exp is not None
        and exp >= 0.10
        and ((pf_delta is not None and pf_delta >= 0.15) or (exp_delta is not None and exp_delta >= 0.05))
        and metrics.get("blocked_bucket_worse_than_kept") is True
        and (metrics.get("bad_signal_loss_share_improvement_pct") or 0.0) >= 20.0
        and metrics.get("both_rising_and_falling_regimes") is True
    )


def discovery_decision(metrics: list[dict[str, Any]]) -> str:
    eligible = [row["candidate_id"] for row in metrics if row.get("v2_registration_eligible")]
    if not eligible:
        return "STOP_NO_CANDIDATE"
    return "PROCEED_TO_FORWARD_APPARATUS_CANDIDATE_" + eligible[0]


def candidate_role(candidate_id: str) -> str:
    if candidate_id == "A3_SQ_COMBINED_V1":
        return "LOCKED_V1_PROMOTION_ELIGIBLE_AFTER_FORWARD_EVIDENCE_ONLY"
    if candidate_id.startswith("A3_SQ_"):
        return "LOCKED_V1_DIAGNOSTIC"
    if candidate_id.startswith("B"):
        return "BASELINE"
    return "DIAGNOSTIC_DISCOVERY_ONLY"


def candidate_levels(
    m5: list[Bar],
    d1: list[Bar],
    weekly: list[Bar],
    i: int,
    break_shift: int,
    is_long: bool,
) -> list[tuple[str, float]]:
    decision_time = m5[i].end
    levels: list[tuple[str, float]] = []
    daily = completed_bar(d1, decision_time)
    if daily:
        levels.append(("previous_daily_high" if is_long else "previous_daily_low", daily.high if is_long else daily.low))
    week = completed_bar(weekly, decision_time)
    if week:
        levels.append(("previous_weekly_high" if is_long else "previous_weekly_low", week.high if is_long else week.low))
    swing = swing_level(m5, i, is_long, break_shift)
    if swing > 0:
        levels.append(("latest_swing_high" if is_long else "latest_swing_low", swing))
    deduped: list[tuple[str, float]] = []
    for kind, price in levels:
        if price <= 0:
            continue
        if all(abs(price - existing_price) > 10.0 * POINT for _, existing_price in deduped):
            deduped.append((kind, price))
    return deduped


def swing_level(m5: list[Bar], i: int, is_long: bool, start_shift: int) -> float:
    for shift in range(max(start_shift, 6), start_shift + 80):
        idx = shift_index(i, shift)
        if idx < 4 or idx + 4 >= len(m5):
            continue
        price = m5[idx].high if is_long else m5[idx].low
        confirmed = True
        for offset in range(1, 5):
            newer = m5[idx + offset].high if is_long else m5[idx + offset].low
            older = m5[idx - offset].high if is_long else m5[idx - offset].low
            if is_long and (price <= newer or price <= older):
                confirmed = False
            if not is_long and (price >= newer or price >= older):
                confirmed = False
        if confirmed:
            return price
    return 0.0


def shift_index(confirmation_index: int, shift: int) -> int:
    return confirmation_index - shift + 1


def average_range(bars: list[Bar], confirmation_index: int, start_shift: int, periods: int) -> float:
    values: list[float] = []
    for shift in range(start_shift, start_shift + periods):
        idx = shift_index(confirmation_index, shift)
        if idx < 0 or idx >= len(bars):
            continue
        values.append(max(0.0, bars[idx].high - bars[idx].low))
    return sum(values) / len(values) if values else 0.0


def break_valid(close: float, atr: float, level: float, is_long: bool) -> bool:
    return close >= level + 0.30 * atr if is_long else close <= level - 0.30 * atr


def retest_valid(bar: Bar, level: float, tolerance: float, is_long: bool) -> bool:
    if is_long:
        return bar.low <= level + tolerance and bar.close >= level
    return bar.high >= level - tolerance and bar.close <= level


def build_plan(retest: Bar, retest_atr: float, is_long: bool) -> dict[str, float]:
    if is_long:
        entry = retest.high + POINT
        stop = retest.low - 0.10 * retest_atr
        risk = entry - stop
        tp = entry + 1.50 * risk
    else:
        entry = retest.low - POINT
        stop = retest.high + 0.10 * retest_atr
        risk = stop - entry
        tp = entry - 1.50 * risk
    return {
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit": tp,
        "stop_distance_points": risk / POINT if POINT else 0.0,
    }


def first_retest_only(m5: list[Bar], signal: RawSignal) -> bool:
    for idx in range(signal.break_index + 1, signal.retest_index):
        bar = m5[idx]
        if signal.direction == "LONG" and bar.low <= signal.level_price:
            return False
        if signal.direction == "SHORT" and bar.high >= signal.level_price:
            return False
    return True


def invalid_close_between(m5: list[Bar], signal: RawSignal, *, include_retest: bool) -> bool:
    end = signal.confirmation_index if include_retest else signal.retest_index
    for idx in range(signal.break_index + 1, end):
        close = m5[idx].close
        if signal.direction == "LONG" and close < signal.level_price:
            return True
        if signal.direction == "SHORT" and close > signal.level_price:
            return True
    return False


def body_to_range(bar: Bar) -> float | None:
    rng = bar.high - bar.low
    if rng <= 0:
        return None
    return abs(bar.close - bar.open) / rng


def close_location(bar: Bar) -> float | None:
    rng = bar.high - bar.low
    if rng <= 0:
        return None
    return (bar.close - bar.low) / rng


def load_bars(path: Path) -> list[Bar]:
    rows = read_csv(path)
    bars: list[Bar] = []
    for row in rows:
        bars.append(
            Bar(
                start=parse_time(row.get("bar_start_utc", "")) or parse_time(row.get("time", "")) or datetime.min,
                end=parse_time(row.get("bar_end_utc", "")) or parse_time(row.get("bar_start_utc", "")) or datetime.min,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                spread=float(row.get("spread") or 0.0),
            )
        )
    return [bar for bar in bars if bar.start != datetime.min]


def with_indicators(bars: list[Bar], *, ema_periods: tuple[int, ...]) -> dict[str, Any]:
    output: dict[str, Any] = {"bars": bars}
    closes = [bar.close for bar in bars]
    for period in ema_periods:
        output[f"ema{period}"] = ema(closes, period)
    return output


def ema(values: list[float], period: int) -> list[float | None]:
    output: list[float | None] = [None] * len(values)
    if len(values) < period:
        return output
    seed = sum(values[:period]) / period
    output[period - 1] = seed
    alpha = 2.0 / (period + 1.0)
    previous = seed
    for index in range(period, len(values)):
        previous = alpha * values[index] + (1.0 - alpha) * previous
        output[index] = previous
    return output


def derive_m15(m5: list[Bar]) -> list[Bar]:
    grouped: dict[datetime, list[Bar]] = {}
    for bar in m5:
        minute = (bar.start.minute // 15) * 15
        start = bar.start.replace(minute=minute, second=0, microsecond=0)
        grouped.setdefault(start, []).append(bar)
    output: list[Bar] = []
    for start, bars in sorted(grouped.items()):
        if len(bars) < 3:
            continue
        bars = sorted(bars, key=lambda row: row.start)
        output.append(
            Bar(
                start=start,
                end=start + timedelta(minutes=15),
                open=bars[0].open,
                high=max(bar.high for bar in bars),
                low=min(bar.low for bar in bars),
                close=bars[-1].close,
                spread=bars[-1].spread,
            )
        )
    return output


def derive_weekly(d1: list[Bar]) -> list[Bar]:
    grouped: dict[datetime, list[Bar]] = {}
    for bar in d1:
        week_start = (bar.start - timedelta(days=bar.start.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        grouped.setdefault(week_start, []).append(bar)
    output: list[Bar] = []
    for start, bars in sorted(grouped.items()):
        if len(bars) < 2:
            continue
        bars = sorted(bars, key=lambda row: row.start)
        output.append(
            Bar(
                start=start,
                end=start + timedelta(days=7),
                open=bars[0].open,
                high=max(bar.high for bar in bars),
                low=min(bar.low for bar in bars),
                close=bars[-1].close,
                spread=bars[-1].spread,
            )
        )
    return output


def completed_index(bars: list[Bar], decision_time: datetime) -> int | None:
    ends = [bar.end for bar in bars]
    idx = bisect.bisect_right(ends, decision_time) - 1
    return idx if idx >= 0 else None


def completed_bar(bars: list[Bar], decision_time: datetime) -> Bar | None:
    idx = completed_index(bars, decision_time)
    return bars[idx] if idx is not None else None


def htf_slope(series: dict[str, Any], decision_time: datetime, ema_period: int) -> float | None:
    idx = completed_index(series["bars"], decision_time)
    if idx is None or idx < 3:
        return None
    values = series[f"ema{ema_period}"]
    if values[idx] is None or values[idx - 3] is None:
        return None
    return (values[idx] - values[idx - 3]) / POINT


def regime_from_slope(value: float | None) -> str:
    if value is None:
        return "DATA_UNAVAILABLE"
    if value > 0:
        return "RISING"
    if value < 0:
        return "FALLING"
    return "FLAT"


def dubai_session(utc_time: datetime) -> str:
    hour = (utc_time + timedelta(hours=4)).hour
    if 6 <= hour < 12:
        return "Morning 06:00-11:59"
    if 12 <= hour < 16:
        return "Afternoon 12:00-15:59"
    if 16 <= hour < 20:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def exit_index_for_trade(trade: VirtualTrade, m5: list[Bar]) -> int:
    exit_time = parse_time(trade.exit_time)
    if exit_time is None:
        return len(m5)
    idx = completed_index(m5, exit_time)
    return idx if idx is not None else len(m5)


def profit_factor(values: list[float]) -> float | None:
    wins = sum(value for value in values if value > 0)
    losses = sum(value for value in values if value < 0)
    if losses == 0:
        return math.inf if wins > 0 else None
    return wins / abs(losses)


def avg(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def median(values: list[int]) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    middle = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return float(sorted_values[middle])
    return (sorted_values[middle - 1] + sorted_values[middle]) / 2.0


def pct(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator * 100.0, 2)


def percentile(values: list[float], p: int) -> float | None:
    cleaned = sorted(value for value in values if math.isfinite(value))
    if not cleaned:
        return None
    rank = (len(cleaned) - 1) * p / 100.0
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return round(cleaned[int(rank)], 4)
    return round(cleaned[lower] + (cleaned[upper] - cleaned[lower]) * (rank - lower), 4)


def max_drawdown(values: list[float]) -> float:
    peak = 0.0
    equity = 0.0
    worst = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        worst = min(worst, equity - peak)
    return abs(worst)


def max_consecutive_losses(values: list[float]) -> int:
    current = 0
    best = 0
    for value in values:
        if value < 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def bad_signal_share(trades: list[VirtualTrade]) -> float | None:
    losses = [trade for trade in trades if trade.final_r < 0]
    if not losses:
        return None
    return pct(sum(1 for trade in losses if trade.loss_class == "BAD_SIGNAL"), len(losses))


def giveback_share_pct(trades: list[VirtualTrade]) -> float | None:
    losses = [trade for trade in trades if trade.final_r < 0]
    if not losses:
        return None
    return pct(sum(1 for trade in losses if trade.loss_class in {"BAD_EXIT_GIVEBACK", "NEAR_TP_GIVEBACK"}), len(losses))


def improvement_pct(base: float | None, candidate: float | None) -> float | None:
    if base is None or candidate is None or base == 0:
        return None
    return round((base - candidate) / base * 100.0, 2)


def build_data_manifest(paths: list[Path], *, extra: dict[str, Any]) -> dict[str, Any]:
    files = []
    for path in paths:
        rows = read_csv(path)
        time_keys = ("bar_start_utc", "entry_time", "entry_time_utc")
        timestamps = [row.get(key, "") for row in rows for key in time_keys if row.get(key)]
        files.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256(path) if path.exists() else "",
                "rows": len(rows),
                "first_timestamp": min(timestamps) if timestamps else "",
                "last_timestamp": max(timestamps) if timestamps else "",
            }
        )
    return {
        "status": "PASS",
        "created_at_utc": now_utc(),
        "timezone": "Input bar timestamps treated as UTC; Dubai session = UTC+04:00 fixed.",
        "files": files,
        "extra": extra,
    }


def write_decisions(path: Path, rows: list[DecisionRow]) -> None:
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(DecisionRow("", "", "", "", False, False, "", "", "", None).__dict__.keys())
    write_csv(path, [asdict(row) for row in rows], fieldnames)


def write_trades(path: Path, rows: list[VirtualTrade]) -> None:
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(VirtualTrade("", "", "", "", "", 0, 0, 0, 0, "", 0, 0, 0, "", "", "").__dict__.keys())
    write_csv(path, [asdict(row) for row in rows], fieldnames)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# A3 Signal Quality Offline Discovery - 2026-06-18",
        "",
        f"Status: `{payload['status']}`",
        f"Decision: `{payload['decision']}`",
        "",
        payload["boundary"],
        "",
        f"Raw signals: `{payload['raw_signals']}`",
        f"Closed raw outcomes: `{payload['closed_raw_outcomes']}`",
        f"Data status: `{payload['data_status']}`",
        "",
        "## Candidate Metrics",
        "",
        "| Candidate | Role | Signals | Signal Ret. | Trades | Trade Ret. | Closed | WR | PF | Exp R | Net R | Bad Signal | Giveback | Eligible |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["candidate_metrics"]:
        lines.append(
            "| {candidate_id} | {candidate_role} | {accepted_signals} | {signal_retention_pct} | "
            "{opened_virtual_trades} | {virtual_trade_retention_pct} | {closed_trades} | {win_rate_pct} | "
            "{profit_factor} | {expectancy_r} | {net_r} | {bad_signal_loss_share_pct} | "
            "{giveback_loss_share_pct} | {v2_registration_eligible} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a cheap offline discovery screen, not promotion evidence.",
            "- M5 bar replay is conservative/coarse and does not replace forward tick-level validation.",
            "- Any selected diagnostic would need a new locked V2 and a fresh validation window.",
            "- If the decision is `STOP_NO_CANDIDATE`, A3 remains paused and the MQL5 forward apparatus should not be built from this discovery window.",
            "",
            "## Outputs",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def parse_time(value: str) -> datetime | None:
    text = str(value or "").strip().replace("T", " ").replace("Z", "")
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text[:19], fmt).replace(tzinfo=None)
        except ValueError:
            pass
    return None


def fmt_time(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run A3 signal-quality offline discovery sweep.")
    parser.add_argument("--phase1-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--bars-dir", type=Path, default=None)
    parser.add_argument("--mfe-mae-csv", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--decisions-csv", type=Path, default=None)
    parser.add_argument("--trades-csv", type=Path, default=None)
    parser.add_argument("--data-manifest-json", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_offline_discovery(
        args.phase1_root,
        bars_dir=args.bars_dir,
        mfe_mae_csv=args.mfe_mae_csv,
        output_json=args.output_json,
        output_md=args.output_md,
        decisions_csv=args.decisions_csv,
        trades_csv=args.trades_csv,
        data_manifest_json=args.data_manifest_json,
    )
    print(f"A3 offline discovery: {payload['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
