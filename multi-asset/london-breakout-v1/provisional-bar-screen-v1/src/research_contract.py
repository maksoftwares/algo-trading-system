from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from statistics import median
from zoneinfo import ZoneInfo


LONDON = ZoneInfo("Europe/London")


def london_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return value.astimezone(LONDON)


def in_overnight(value: datetime) -> bool:
    local = london_time(value)
    return local.hour < 8


def in_entry_window(value: datetime) -> bool:
    local = london_time(value)
    return 8 <= local.hour < 12


def final_completed_h1(bars: list[dict], cutoff: datetime) -> dict:
    eligible = [bar for bar in bars if bar["end"] <= cutoff]
    if not eligible:
        raise ValueError("no completed H1 bar")
    return max(eligible, key=lambda bar: bar["end"])


def directional_bias(close: float, ema_now: float, ema_six_ago: float, atr: float) -> str:
    if atr <= 0:
        return "NONE"
    slope = (ema_now - ema_six_ago) / atr
    if close > ema_now and slope >= 0.10:
        return "LONG"
    if close < ema_now and slope <= -0.10:
        return "SHORT"
    return "NONE"


def breakout(direction: str, o: float, h: float, low: float, close: float, edge: float, atr: float) -> bool:
    span = h - low
    if span <= 0 or atr <= 0:
        return False
    body = abs(close - o) / span
    location = (close - low) / span
    if direction == "LONG":
        return close >= edge + 0.10 * atr and close > o and body >= 0.50 and location >= 0.75
    if direction == "SHORT":
        return close <= edge - 0.10 * atr and close < o and body >= 0.50 and location <= 0.25
    return False


def first_signal(events: list[dict]) -> dict | None:
    accepted = [event for event in events if event.get("qualifies")]
    return min(accepted, key=lambda event: event["time"]) if accepted else None


def spread_price(points: float, point: float, digits: int) -> float:
    if not math.isfinite(points) or points < 0:
        raise ValueError("invalid spread")
    if point <= 0 or not math.isclose(point, 10 ** (-digits), rel_tol=0, abs_tol=1e-12):
        raise ValueError("point/digits inconsistency")
    return points * point


def reconstruct(ohlc: tuple[float, float, float, float], spread: float, basis: str) -> dict[str, tuple[float, ...]]:
    if not math.isfinite(spread) or spread < 0:
        raise ValueError("invalid spread")
    if basis == "BID":
        bid = ohlc
        ask = tuple(value + spread for value in ohlc)
    elif basis == "MID":
        bid = tuple(value - spread / 2 for value in ohlc)
        ask = tuple(value + spread / 2 for value in ohlc)
    else:
        raise ValueError("quote basis unresolved")
    return {"bid": bid, "ask": ask}


def next_exact_bar(bars: list[dict], expected_open: datetime) -> dict:
    matches = [bar for bar in bars if bar["time"] == expected_open]
    if len(matches) != 1:
        raise ValueError("MISSING_NEXT_M5_ENTRY_PATH")
    return matches[0]


@dataclass(frozen=True)
class Exit:
    price: float
    reason: str
    mfe: float
    mae: float


def resolve_bar(direction: str, bar: dict, stop: float, target: float, entry: float) -> Exit | None:
    side = bar["bid"] if direction == "LONG" else bar["ask"]
    o, h, low, _ = side
    if direction == "LONG":
        if o <= stop:
            return Exit(o, "STOP_GAP", max(0, o - entry), min(0, o - entry))
        if o >= target:
            return Exit(target, "TARGET_GAP", target - entry, 0)
        stop_hit, target_hit = low <= stop, h >= target
        if stop_hit:
            return Exit(stop, "AMBIGUOUS_M5_STOP_FIRST" if target_hit else "STOP", max(0, stop - entry), stop - entry)
        if target_hit:
            return Exit(target, "TARGET", target - entry, min(0, low - entry))
    else:
        if o >= stop:
            return Exit(o, "STOP_GAP", max(0, entry - o), min(0, entry - o))
        if o <= target:
            return Exit(target, "TARGET_GAP", entry - target, 0)
        stop_hit, target_hit = h >= stop, low <= target
        if stop_hit:
            return Exit(stop, "AMBIGUOUS_M5_STOP_FIRST" if target_hit else "STOP", max(0, entry - stop), entry - stop)
        if target_hit:
            return Exit(target, "TARGET", entry - target, min(0, entry - h))
    return None


def exit_deadline(entry: datetime) -> datetime:
    local = london_time(entry)
    forced = local.replace(hour=16, minute=0, second=0, microsecond=0)
    return min(entry + timedelta(hours=8), forced.astimezone(entry.tzinfo))


def require_same_day_exit(entry: datetime, exit_time: datetime | None) -> None:
    if exit_time is None or london_time(entry).date() != london_time(exit_time).date():
        raise ValueError("MISSING_SAME_DAY_FORCED_EXIT_PATH")


def nearest_rank_p95(values: list[float]) -> float:
    if not values:
        raise ValueError("no development spreads")
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def instrument_gates(metrics: dict) -> dict[str, bool]:
    return {
        "full_history_trades": metrics["full_history_trades"] >= 200,
        "locked_exam_trades": metrics["locked_exam_trades"] >= 25,
        "baseline_pf": metrics["baseline_pf"] >= 1.10,
        "baseline_expectancy": metrics["baseline_expectancy"] >= 0.04,
        "baseline_net": metrics["baseline_net"] > 0,
        "stress_pf": metrics["stress_pf"] >= 1.00,
        "stress_net": metrics["stress_net"] > 0,
        "worst_segment_pf": metrics["worst_segment_pf"] >= 0.85,
        "drawdown": metrics["drawdown"] <= 20,
        "top_ten_winners": metrics["top_ten_winners"] <= 0.40,
    }


def combined_gates(metrics: dict) -> dict[str, bool]:
    limits = {
        "full_history_trades": metrics["full_history_trades"] >= 1200,
        "average_trades_year": metrics["average_trades_year"] >= 120,
        "median_trades_month": metrics["median_trades_month"] >= 8,
        "locked_exam_trades": metrics["locked_exam_trades"] >= 100,
        "latest_six_months": metrics["latest_six_months"] >= 45,
        "latest_three_months": metrics["latest_three_months"] >= 20,
        "locked_exam_months": metrics["locked_exam_months"] >= 9,
        "baseline_pf": metrics["baseline_pf"] >= 1.20,
        "baseline_expectancy": metrics["baseline_expectancy"] >= 0.07,
        "baseline_net": metrics["baseline_net"] > 0,
        "stress_pf": metrics["stress_pf"] >= 1.05,
        "stress_expectancy": metrics["stress_expectancy"] > 0,
        "stress_net": metrics["stress_net"] > 0,
        "exam_pf": metrics["exam_pf"] >= 1.10,
        "exam_net": metrics["exam_net"] > 0,
        "drawdown": metrics["drawdown"] <= 25,
        "top_ten_winners": metrics["top_ten_winners"] <= 0.30,
        "top_three_days": metrics["top_three_days"] <= 0.20,
        "instrument_contribution": metrics["instrument_contribution"] <= 0.60,
    }
    return limits


def classify(data_valid: bool, instrument_passes: int, combined_pass: bool) -> str:
    if not data_valid:
        return "LONDON_BREAKOUT_V1_PROVISIONAL_DATA_INVALID"
    if instrument_passes >= 2 and combined_pass:
        return "LONDON_BREAKOUT_V1_PROVISIONAL_POSITIVE_TICK_CONFIRMATION_REQUIRED"
    return "LONDON_BREAKOUT_V1_PROVISIONAL_REJECTED_NO_TICK_ACQUISITION"
