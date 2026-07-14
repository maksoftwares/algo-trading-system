from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import math
from statistics import median
from zoneinfo import ZoneInfo


LONDON = ZoneInfo("Europe/London")


def sort_ticks(rows: list[dict]) -> list[dict]:
    return [row for _, row in sorted(enumerate(rows), key=lambda item: (item[1]["time_msc"], item[0]))]


def tick_integrity(rows: list[dict]) -> dict:
    identities = [tuple(row.get(k) for k in ("time_msc", "bid", "ask", "last", "volume", "flags")) for row in rows]
    return {"duplicates": len(identities) - len(set(identities)),
            "duplicate_time_msc": len(rows) - len({row["time_msc"] for row in rows}),
            "decreasing": sum(rows[i]["time_msc"] < rows[i-1]["time_msc"] for i in range(1, len(rows))),
            "crossed": sum(row["ask"] < row["bid"] for row in rows),
            "zero": sum(row["ask"] <= 0 or row["bid"] <= 0 for row in rows),
            "nonfinite": sum(not all(math.isfinite(float(row[k])) for k in ("bid", "ask")) for row in rows)}


def aggregate(rows: list[dict], seconds: int) -> dict[int, dict]:
    groups = defaultdict(list)
    for row in sort_ticks(rows):
        groups[row["time_msc"] // (seconds * 1000) * (seconds * 1000)].append(row)
    result = {}
    for start, ticks in groups.items():
        candidate = {}
        for basis in ("bid", "ask", "mid"):
            values = [row[basis] if basis != "mid" else (row["bid"] + row["ask"]) / 2 for row in ticks]
            candidate[basis] = (values[0], max(values), min(values), values[-1])
        result[start] = {"start": start, "end": start + seconds * 1000, "ticks": ticks, **candidate}
    return result


def complete_bar(bar: dict, export_start: int, export_end: int) -> bool:
    return bar["start"] >= export_start and bar["end"] <= export_end


def london(value: datetime) -> datetime:
    return value.astimezone(LONDON)


def overnight(value: datetime) -> bool:
    local = london(value); return local.hour < 8


def final_completed(bars: list[dict], cutoff: datetime) -> dict:
    eligible = [bar for bar in bars if bar["end"] <= cutoff]
    if not eligible: raise ValueError("missing completed H1")
    return max(eligible, key=lambda bar: bar["end"])


def bias(close: float, ema: float, ema_old: float, atr: float) -> str:
    if atr <= 0: return "NONE"
    slope = (ema - ema_old) / atr
    if close > ema and slope >= .10: return "LONG"
    if close < ema and slope <= -.10: return "SHORT"
    return "NONE"


def range_quality(width: float, atr: float) -> bool:
    return atr > 0 and .5 * atr <= width <= 2 * atr


def breakout(direction: str, o: float, h: float, low: float, close: float, edge: float, atr: float) -> bool:
    span = h - low
    if span <= 0: return False
    body, location = abs(close-o)/span, (close-low)/span
    if direction == "LONG": return close >= edge + .1*atr and close > o and body >= .5 and location >= .75
    if direction == "SHORT": return close <= edge - .1*atr and close < o and body >= .5 and location <= .25
    return False


def first_qualifying(events: list[dict]) -> dict | None:
    rows = [row for row in events if row.get("qualifies")]
    return min(rows, key=lambda row: row["time"]) if rows else None


def first_execution_tick(rows: list[dict], signal_close_msc: int, next_m5_end_msc: int) -> dict:
    valid = [row for row in sort_ticks(rows) if signal_close_msc < row["time_msc"] < next_m5_end_msc and row["bid"] > 0 and row["ask"] >= row["bid"]]
    if not valid: raise ValueError("MISSING_NEXT_M5_EXECUTION")
    return valid[0]


def executable_side(direction: str, tick: dict, purpose: str) -> float:
    if direction == "LONG": return tick["ask"] if purpose == "ENTRY" else tick["bid"]
    return tick["bid"] if purpose == "ENTRY" else tick["ask"]


def resolve_tick(direction: str, tick: dict, stop: float, target: float, first: bool = False) -> tuple | None:
    px = executable_side(direction, tick, "EXIT")
    if direction == "LONG":
        if px <= stop: return px, "STOP_GAP" if first and px < stop else "STOP"
        if px >= target: return target, "TARGET_GAP" if first and px > target else "TARGET"
    else:
        if px >= stop: return px, "STOP_GAP" if first and px > stop else "STOP"
        if px <= target: return target, "TARGET_GAP" if first and px < target else "TARGET"
    return None


def identical_time_resolution(stop_hit: bool, target_hit: bool) -> str | None:
    if stop_hit: return "IDENTICAL_TIMESTAMP_STOP_FIRST" if target_hit else "STOP"
    return "TARGET" if target_hit else None


def exit_deadline(entry: datetime) -> datetime:
    forced = london(entry).replace(hour=16, minute=0, second=0, microsecond=0).astimezone(entry.tzinfo)
    return min(entry + timedelta(hours=8), forced)


def same_london_day(a: datetime, b: datetime) -> bool:
    return london(a).date() == london(b).date()


def nearest_rank_p95(values: list[float]) -> float:
    rows = sorted(values)
    if not rows: raise ValueError("no development spreads")
    return rows[math.ceil(.95 * len(rows)) - 1]


def stress_increment(actual_entry: float, actual_exit: float, p95: float, risk: float) -> float:
    return (max(0, p95-actual_entry) + max(0, p95-actual_exit)) / risk


def baseline_net(gross_r: float, commission_r: float = 0) -> float:
    return gross_r - commission_r


def stress_net(baseline_r: float, incremental_spread_r: float) -> float:
    return baseline_r - incremental_spread_r - .05


def convert_profit(value: float, conversion_rate: float) -> float:
    return value * conversion_rate


def minimum_volume_loss(calculator, *args) -> float:
    return abs(float(calculator(*args)))


def required_margin(calculator, *args) -> float:
    return float(calculator(*args))


def account_feasible(min_loss: float, margin: float, equity: float = 1000) -> bool:
    return min_loss <= 5 and margin <= .2*equity and equity-margin >= .8*equity


def sizing_gate(rejected: int, total: int) -> bool:
    return total > 0 and rejected / total <= .10


def excursions_until_exit(prices: list[float], entry: float, exit_index: int, direction: str) -> tuple[float, float]:
    values = prices[:exit_index+1]
    moves = [price-entry if direction == "LONG" else entry-price for price in values]
    return max(moves), min(moves)


def admit(signals: list[dict], risk_cap: float = 5) -> list[dict]:
    result=[]; open_risk=0
    for row in sorted(signals, key=lambda x:(x["time_msc"],x["instrument"])):
        if open_risk + row["risk"] <= risk_cap: result.append(row); open_risk += row["risk"]
    return result


def instrument_frequency(full: int, exam: int) -> bool: return full >= 80 and exam >= 20


def portfolio_frequency(m: dict) -> bool:
    return m["full"] >= 360 and m["annualized"] >= 280 and m["median_month"] >= 20 and m["exam"] >= 80 and m["latest3"] >= 60 and m["every_exam_month"]


def instrument_profit(m: dict) -> bool:
    return m["pf"] >= 1.10 and m["expectancy"] >= .04 and m["net"] > 0 and m["stress_pf"] >= 1.02 and m["stress_expectancy"] > 0 and m["stress_net"] > 0 and m["exam_net"] > 0 and m["drawdown"] <= 15 and m["top10"] <= .40


def portfolio_profit(m: dict) -> bool:
    return m["pf"] >= 1.25 and m["expectancy"] >= .08 and m["net"] > 0 and m["stress_pf"] >= 1.10 and m["stress_expectancy"] >= .03 and m["stress_net"] > 0 and m["exam_pf"] >= 1.15 and m["exam_expectancy"] >= .05 and m["exam_net"] > 0 and m["drawdown"] <= 20 and m["stress_drawdown"] <= 25 and m["top10"] <= .30 and m["top3days"] <= .20 and m["contribution"] <= .60


def classify(data_valid: bool, gates_pass: bool) -> str:
    if not data_valid: return "LONDON_NATIVE_TICK_V1_DATA_INVALID"
    if gates_pass: return "LONDON_NATIVE_TICK_V1_POSITIVE_FORWARD_SHADOW_REQUIRED"
    return "LONDON_NATIVE_TICK_V1_REJECTED_CLOSE_HYPOTHESIS"
