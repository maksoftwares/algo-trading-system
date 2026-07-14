from __future__ import annotations

import calendar
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from statistics import median
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

UTC = timezone.utc
LONDON = ZoneInfo("Europe/London")


def last_sunday(year: int, month: int) -> date:
    last = calendar.monthrange(year, month)[1]
    value = date(year, month, last)
    return value - timedelta(days=(value.weekday() + 1) % 7)


def london_dst_bounds(year: int) -> tuple[datetime, datetime]:
    return (
        datetime.combine(last_sunday(year, 3), datetime.min.time(), UTC) + timedelta(hours=1),
        datetime.combine(last_sunday(year, 10), datetime.min.time(), UTC) + timedelta(hours=1),
    )


def london_offset_hours(at_utc: datetime) -> int:
    at_utc = at_utc.astimezone(UTC)
    start, end = london_dst_bounds(at_utc.year)
    return int(start <= at_utc < end)


def broker_offset_hours(at_utc: datetime) -> int:
    """Frozen Capital.com tester mapping: EET/EEST using EU DST boundaries."""
    return 2 + london_offset_hours(at_utc)


def utc_to_broker(at_utc: datetime) -> datetime:
    at_utc = at_utc.astimezone(UTC)
    return (at_utc + timedelta(hours=broker_offset_hours(at_utc))).replace(tzinfo=None)


def broker_to_utc(at_broker: datetime) -> datetime:
    if at_broker.tzinfo is not None:
        at_broker = at_broker.replace(tzinfo=None)
    for offset in (2, 3):
        candidate = (at_broker - timedelta(hours=offset)).replace(tzinfo=UTC)
        if broker_offset_hours(candidate) == offset:
            return candidate
    raise ValueError("ambiguous broker-to-UTC mapping")


def utc_to_london(at_utc: datetime) -> datetime:
    return at_utc.astimezone(UTC).astimezone(LONDON)


def london_session_bucket(at_utc: datetime) -> str:
    hour = utc_to_london(at_utc).hour
    if 0 <= hour < 8:
        return "OVERNIGHT_RANGE"
    if 8 <= hour < 12:
        return "ENTRY_WINDOW"
    if hour >= 16:
        return "FORCED_EXIT_OR_LATER"
    return "OTHER"


def completed_before(bar_close: datetime, decision: datetime) -> bool:
    return bar_close <= decision


def h1_bias(close: float, ema: float, ema_six_back: float, atr: float) -> str:
    if atr <= 0 or not all(math.isfinite(v) for v in (close, ema, ema_six_back, atr)):
        return "NO_DIRECTIONAL_BIAS"
    slope = (ema - ema_six_back) / atr
    if close > ema and slope >= 0.10:
        return "LONG"
    if close < ema and slope <= -0.10:
        return "SHORT"
    return "NO_DIRECTIONAL_BIAS"


def range_quality(width: float, h1_atr: float) -> bool:
    return h1_atr > 0 and 0.50 * h1_atr <= width <= 2.00 * h1_atr


def breakout_signal(direction: str, o: float, h: float, l: float, c: float, atr: float, overnight_high: float, overnight_low: float) -> bool:
    span = h - l
    if span <= 0 or atr <= 0:
        return False
    body = abs(c - o) / span
    location = (c - l) / span
    if direction == "LONG":
        return c >= overnight_high + 0.10 * atr and c > o and body >= 0.50 and location >= 0.75
    if direction == "SHORT":
        return c <= overnight_low - 0.10 * atr and c < o and body >= 0.50 and location <= 0.25
    return False


def executable_entry(direction: str, bid: float, ask: float) -> float:
    if ask < bid or bid <= 0 or ask <= 0:
        raise ValueError("invalid executable quote")
    return ask if direction == "LONG" else bid


def stop_price(direction: str, signal_low: float, signal_high: float, atr: float) -> float:
    return signal_low - 0.10 * atr if direction == "LONG" else signal_high + 0.10 * atr


def stop_distance_valid(distance: float, atr: float) -> bool:
    return atr > 0 and 0.75 * atr <= distance <= 1.50 * atr


def target_price(direction: str, entry: float, risk_distance: float) -> float:
    return entry + 2.0 * risk_distance if direction == "LONG" else entry - 2.0 * risk_distance


def next_tick_valid(signal_close_msc: int, entry_msc: int) -> bool:
    return signal_close_msc < entry_msc <= signal_close_msc + 5 * 60 * 1000


def hold_expired(entry_msc: int, now_msc: int) -> bool:
    return now_msc - entry_msc >= 8 * 60 * 60 * 1000


def same_london_date(first: datetime, second: datetime) -> bool:
    return utc_to_london(first).date() == utc_to_london(second).date()


def round_volume_down(raw: float, minimum: float, maximum: float, step: float) -> float:
    if step <= 0 or raw < minimum:
        return 0.0
    value = math.floor((min(raw, maximum) - minimum + 1e-12) / step) * step + minimum
    return round(value, 10)


def minimum_volume_feasible(total_loss: float, equity: float = 1000.0) -> bool:
    return total_loss <= equity * 0.005 + 1e-12


def margin_feasible(required_margin: float, free_margin_after: float, equity: float = 1000.0) -> bool:
    return required_margin <= equity * 0.20 + 1e-12 and free_margin_after >= equity * 0.80 - 1e-12


def admit_overlaps(rows: Sequence[dict], max_risk: float = 5.0) -> list[dict]:
    ordered = sorted(rows, key=lambda r: (r["entry_msc"], r["symbol"]))
    admitted: list[dict] = []
    open_risk = 0.0
    for row in ordered:
        if open_risk + float(row["risk"]) <= max_risk + 1e-12:
            admitted.append(row)
            open_risk += float(row["risk"])
    return admitted


def p95(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("empty spread sample")
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def incremental_stress(actual_entry: float, actual_exit: float, frozen_p95: float, risk: float) -> float:
    if risk <= 0:
        raise ValueError("risk must be positive")
    return (max(0.0, frozen_p95 - actual_entry) + max(0.0, frozen_p95 - actual_exit)) / risk + 0.05


def baseline_net_r(gross_r: float, commission_r: float) -> float:
    return gross_r - commission_r


def profit_factor(values: Sequence[float]) -> float:
    gains = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    if losses == 0:
        return math.inf if gains > 0 else 0.0
    return gains / losses


def expectancy(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def max_closed_drawdown(values: Sequence[float]) -> float:
    equity = peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def winner_share(values: Sequence[float], count: int) -> float:
    winners = sorted((v for v in values if v > 0), reverse=True)
    gross = sum(winners)
    return sum(winners[:count]) / gross if gross else 0.0


def annualized_trades(trades: int, complete_months: int) -> float:
    return trades * 12.0 / complete_months if complete_months else 0.0


def instrument_frequency_pass(annualized: float, exam_trades: int) -> bool:
    return annualized >= 60 and exam_trades >= 50


def portfolio_frequency_pass(annualized: float, monthly: Sequence[int], exam: int, latest6: int, latest3: int) -> bool:
    return bool(monthly) and annualized >= 280 and median(monthly) >= 20 and exam >= 240 and latest6 >= 120 and latest3 >= 60 and all(v > 0 for v in monthly[-12:])


def standalone_profit_pass(baseline: Sequence[float], stress: Sequence[float], exam: Sequence[float], floating_dd: float) -> bool:
    return (
        profit_factor(baseline) >= 1.10 and expectancy(baseline) >= 0.04 and sum(baseline) > 0
        and profit_factor(stress) >= 1.02 and expectancy(stress) > 0 and sum(stress) > 0
        and profit_factor(exam) >= 1.05 and sum(exam) > 0 and floating_dd <= 15
        and winner_share(baseline, 10) <= 0.40
    )


def portfolio_profit_pass(baseline: Sequence[float], stress: Sequence[float], exam: Sequence[float], baseline_dd: float, stress_dd: float, top3_day_share: float, best_instrument_share: float) -> bool:
    return (
        profit_factor(baseline) >= 1.25 and expectancy(baseline) >= 0.08 and sum(baseline) > 0
        and profit_factor(stress) >= 1.10 and expectancy(stress) >= 0.03 and sum(stress) > 0
        and profit_factor(exam) >= 1.15 and expectancy(exam) >= 0.05 and sum(exam) > 0
        and baseline_dd <= 20 and stress_dd <= 25 and winner_share(baseline, 10) <= 0.30
        and top3_day_share <= 0.20 and best_instrument_share <= 0.60
    )


def sizing_rejection_pass(rejections: int, opportunities: int) -> bool:
    return opportunities > 0 and rejections / opportunities <= 0.10


def complete_month_keys(start: date, end_exclusive: date) -> list[str]:
    current = date(start.year, start.month, 1)
    if start != current:
        current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    keys: list[str] = []
    while current < end_exclusive:
        nxt = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        if nxt <= end_exclusive:
            keys.append(current.strftime("%Y-%m"))
        current = nxt
    return keys


def longest_common_contiguous(months_by_symbol: dict[str, set[str]]) -> list[str]:
    if set(months_by_symbol) != {"EURUSD", "GBPUSD", "USDJPY"}:
        return []
    common = set.intersection(*(months_by_symbol[s] for s in sorted(months_by_symbol)))
    ordered = sorted(common)
    best: list[str] = []
    current: list[str] = []
    previous: date | None = None
    for key in ordered:
        value = datetime.strptime(key + "-01", "%Y-%m-%d").date()
        expected = None if previous is None else (previous.replace(day=28) + timedelta(days=4)).replace(day=1)
        current = current + [key] if expected == value else [key]
        if len(current) > len(best):
            best = list(current)
        previous = value
    return best


def chronological_split(common_months: Sequence[str]) -> dict[str, list[str]]:
    if len(common_months) < 36:
        raise ValueError("at least 36 complete months required")
    exam = list(common_months[-12:])
    pre = list(common_months[:-12])
    dev_count = math.floor(len(pre) * 0.70)
    return {"DEVELOPMENT": pre[:dev_count], "VALIDATION": pre[dev_count:], "LOCKED_EXAM": exam}


class Cells(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cells: list[str] = []
        self._inside = False
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"td", "th"}:
            self._inside = True
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._inside:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"td", "th"} and self._inside:
            self.cells.append(" ".join("".join(self._text).split()))
            self._inside = False


def parse_tester_report(text: str) -> dict[str, str]:
    parser = Cells()
    parser.feed(text)
    result: dict[str, str] = {}
    for index, cell in enumerate(parser.cells[:-1]):
        if cell.endswith(":"):
            result[cell[:-1].strip()] = parser.cells[index + 1]
    return result


def proves_real_ticks(fields: dict[str, str]) -> bool:
    quality = fields.get("History Quality", "")
    model = fields.get("Model", "")
    return bool(re.fullmatch(r"100(?:\.0+)?%\s+real ticks", quality.strip(), re.I)) and (not model or "real tick" in model.lower())


def no_credentials_or_absolute_paths(text: str) -> bool:
    forbidden = ("Password=", "InvestorPassword=", "C:\\Users\\", "C:/Users/", "/home/")
    return not any(token.lower() in text.lower() for token in forbidden)


def classify(*, base_ok: bool = True, evidence_valid: bool, commercial_pass: bool) -> str:
    if not base_ok:
        return "LONDON_MT5_REAL_TICK_V1_BASE_IDENTITY_MISMATCH"
    if not evidence_valid:
        return "LONDON_MT5_REAL_TICK_V1_DATA_INVALID"
    if not commercial_pass:
        return "LONDON_MT5_REAL_TICK_V1_REJECTED_CLOSE_HYPOTHESIS"
    return "LONDON_MT5_REAL_TICK_V1_POSITIVE_FORWARD_SHADOW_REQUIRED"


@dataclass(frozen=True)
class FileIdentity:
    path: str
    size_bytes: int
    sha256: str


def repository_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()
