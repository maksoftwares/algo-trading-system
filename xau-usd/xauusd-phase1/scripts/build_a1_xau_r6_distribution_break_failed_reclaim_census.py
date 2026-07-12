"""Pure, market-only R6 opportunity detector.

R6-C2 intentionally exposes no command-line entry point and performs no file I/O.
The real evidence build belongs to the separately reviewed R6-C3 phase.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median
from typing import Iterable, Sequence


RULE_VERSION = "R6_H4_DISTRIBUTION_BREAK_FAILED_RECLAIM_SHORT_V1"
RULE_SHA256 = "456b3a1d153110cf55906d1b4ab82c18cf65d733fcdfe8498f0f768ef06a8181"
TIMESTAMP_BASIS = "BROKER_SERVER_WALL_CLOCK"
TERMINAL_STATUSES = (
    "DATA_UNAVAILABLE",
    "IMPULSE_REJECTED",
    "BOX_REJECTED",
    "ROUTER_BLOCKED_UNKNOWN",
    "ROUTER_BLOCKED_SHOCK",
    "ROUTER_BLOCKED_COMPRESSION",
    "ROUTER_BLOCKED_DOWNTREND",
    "BREAKDOWN_REJECTED",
    "SUPPRESSION_ACTIVE",
    "FIRST_RECLAIM_NOT_REJECTED",
    "NO_RECLAIM_WITHIN_SIX_H1",
    "ENTRY_TICK_UNAVAILABLE",
    "RAW_OPPORTUNITY_AVAILABLE",
)


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Tick:
    time: datetime
    sequence: int
    bid: float
    ask: float
    session_open: bool = True


@dataclass(frozen=True)
class Contract:
    point: float
    digits: int
    tick_size: float
    tick_value_loss: float
    volume_min: float
    volume_step: float
    contract_size: float
    stops_level: int
    freeze_level: int


@dataclass(frozen=True)
class Detection:
    rows: tuple[dict[str, object], ...]
    funnel: dict[str, int]


def broker_time(value: datetime) -> str:
    if value.tzinfo is not None:
        raise ValueError("broker wall-clock timestamps must be timezone-naive")
    return value.strftime("%Y-%m-%dT%H:%M:%S")


def validate_bars(bars: Sequence[Bar]) -> None:
    for index, bar in enumerate(bars):
        values = (bar.open, bar.high, bar.low, bar.close)
        if any(not math.isfinite(value) or value <= 0 for value in values):
            raise ValueError("invalid OHLC")
        if bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close):
            raise ValueError("invalid OHLC range")
        if index and bar.time <= bars[index - 1].time:
            raise ValueError("bar timestamps must be unique and increasing")


def true_ranges(bars: Sequence[Bar]) -> list[float | None]:
    output: list[float | None] = [None]
    for previous, current in zip(bars, bars[1:]):
        output.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    return output


def wilder_atr(bars: Sequence[Bar], period: int = 14) -> list[float | None]:
    validate_bars(bars)
    tr = true_ranges(bars)
    output: list[float | None] = [None] * len(bars)
    if len(bars) <= period:
        return output
    seed = sum(value for value in tr[1 : period + 1] if value is not None) / period
    output[period] = seed
    for index in range(period + 1, len(bars)):
        assert tr[index] is not None and output[index - 1] is not None
        output[index] = ((period - 1) * output[index - 1] + tr[index]) / period
    return output


def ema(values: Sequence[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    output = [values[0]]
    for value in values[1:]:
        output.append(alpha * value + (1.0 - alpha) * output[-1])
    return output


def percentile_rank(values: Sequence[float], current: float) -> float:
    if not values:
        raise ValueError("percentile window unavailable")
    return 100.0 * sum(value <= current for value in values) / len(values)


def _trend_stack(bars: Sequence[Bar], index: int, up: bool) -> bool:
    if index < 55:
        raise ValueError("trend history unavailable")
    closes = [bar.close for bar in bars[: index + 1]]
    fast, slow = ema(closes, 20), ema(closes, 50)
    if up:
        return closes[index] > fast[index] > slow[index] and fast[index] >= fast[index - 5] and slow[index] >= slow[index - 5]
    return closes[index] < fast[index] < slow[index] and fast[index] <= fast[index - 5] and slow[index] <= slow[index - 5]


def classify_router(*, h1: Sequence[Bar], h4: Sequence[Bar], d1: Sequence[Bar], decision: datetime) -> str:
    """Port the pinned market-only Router V1 priority using completed native bars."""
    try:
        h1_i = max(index for index in range(len(h1) - 1) if h1[index + 1].time <= decision)
        h4_i = max(index for index in range(len(h4) - 1) if h4[index + 1].time <= decision)
        d1_i = max(index for index in range(len(d1) - 1) if d1[index + 1].time <= decision)
        h1_atr, d1_atr = wilder_atr(h1), wilder_atr(d1)
        if h1_atr[h1_i] is None or d1_atr[d1_i] is None or d1_i < 253:
            return "UNKNOWN"
        if h1[h1_i].high - h1[h1_i].low >= 3.0 * h1_atr[h1_i]:
            return "SHOCK"
        d1_window = [value for value in d1_atr[d1_i - 59 : d1_i + 1] if value is not None]
        if len(d1_window) != 60:
            return "UNKNOWN"
        if percentile_rank(d1_window, d1_atr[d1_i]) >= 95.0:
            return "SHOCK"
        if _trend_stack(d1, d1_i, True) and _trend_stack(d1, d1_i - 1, True) and _trend_stack(h4, h4_i, True):
            return "UPTREND"
        if _trend_stack(d1, d1_i, False) and _trend_stack(d1, d1_i - 1, False) and _trend_stack(h4, h4_i, False):
            return "DOWNTREND"
        d1_window_252 = [value for value in d1_atr[d1_i - 251 : d1_i + 1] if value is not None]
        ranges = [bar.high - bar.low for bar in d1]
        box_average = sum(ranges[d1_i - 4 : d1_i + 1]) / 5
        range_median = median(ranges[d1_i - 19 : d1_i + 1])
        if percentile_rank(d1_window_252, d1_atr[d1_i]) <= 30.0 and box_average <= range_median:
            return "COMPRESSION"
        return "CHOP"
    except (ValueError, IndexError):
        return "UNKNOWN"


def normalize_up(price: float, contract: Contract) -> float:
    validate_contract(contract)
    return round(math.ceil(price / contract.tick_size - 1e-12) * contract.tick_size, contract.digits)


def validate_contract(contract: Contract) -> None:
    finite_positive = (
        contract.point,
        contract.tick_size,
        contract.tick_value_loss,
        contract.volume_min,
        contract.volume_step,
        contract.contract_size,
    )
    if any(not math.isfinite(value) or value <= 0 for value in finite_positive):
        raise ValueError("invalid contract metadata")
    if contract.digits < 0 or contract.stops_level < 0 or contract.freeze_level < 0:
        raise ValueError("invalid contract metadata")


def minimum_contract_risk(entry_bid: float, risk_price: float, contract: Contract) -> float:
    """Captured-contract equivalent of short-side OrderCalcProfit magnitude."""
    validate_contract(contract)
    if not (math.isfinite(entry_bid) and math.isfinite(risk_price) and risk_price > entry_bid > 0):
        raise ValueError("invalid risk prices")
    ticks = (risk_price - entry_bid) / contract.tick_size
    return ticks * contract.tick_value_loss * contract.volume_min


def canonical_hash(fields: Iterable[str]) -> str:
    return hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()


def canonical_ids(
    *, symbol: str, distribution: Sequence[Bar], box_low: float, box_high: float,
    breakdown_time: datetime, reclaim_time: datetime, entry_tick: Tick, contract: Contract,
) -> tuple[str, str, str]:
    def price(value: float) -> str:
        return f"{value:.{contract.digits}f}"
    box_id = canonical_hash(
        [RULE_VERSION, symbol, *(broker_time(bar.time) for bar in distribution), price(box_low), price(box_high)]
    )
    episode_id = canonical_hash([RULE_VERSION, symbol, "SHORT", box_id, broker_time(breakdown_time)])
    candidate_id = canonical_hash(
        [RULE_VERSION, episode_id, broker_time(reclaim_time), broker_time(entry_tick.time), str(entry_tick.sequence)]
    )
    return box_id, episode_id, candidate_id


def annual_bucket(value: datetime) -> int:
    return value.year if value.month >= 7 else value.year - 1


def concentration(values: Sequence[datetime]) -> dict[str, object]:
    buckets = {year: 0 for year in range(2016, 2026)}
    normalized_months: list[tuple[int, int]] = []
    year, month = 2016, 7
    for _ in range(120):
        normalized_months.append((year, month))
        month += 1
        if month == 13:
            year, month = year + 1, 1
    month_counts = {key: 0 for key in normalized_months}
    for value in values:
        buckets[annual_bucket(value)] += 1
        month_counts[(value.year, value.month)] += 1
    counts = [month_counts[key] for key in normalized_months]
    windows = [sum(counts[index : index + 24]) for index in range(97)]
    total = len(values)
    return {
        "july_june": buckets,
        "months": counts,
        "best_24_month_share": max(windows, default=0) / total if total else 0.0,
    }


def _body_fraction(bar: Bar) -> float:
    return abs(bar.close - bar.open) / (bar.high - bar.low)


def _close_location(bar: Bar) -> float:
    return (bar.close - bar.low) / (bar.high - bar.low)


def _overlap_ratio(first: Bar, second: Bar) -> float:
    overlap = max(0.0, min(first.high, second.high) - max(first.low, second.low))
    return overlap / min(first.high - first.low, second.high - second.low)


def detect(
    *, h4: Sequence[Bar], h1: Sequence[Bar], d1: Sequence[Bar], ticks: Sequence[Tick],
    contract: Contract, symbol: str = "XAUUSD",
) -> Detection:
    """Detect raw available opportunities and a deterministic terminal funnel."""
    validate_bars(h4)
    validate_bars(h1)
    validate_bars(d1)
    validate_contract(contract)
    h4_atr, h1_atr = wilder_atr(h4), wilder_atr(h1)
    tick_rows = sorted(ticks, key=lambda item: item.sequence)
    if any(tick_rows[index].sequence >= tick_rows[index + 1].sequence for index in range(len(tick_rows) - 1)):
        raise ValueError("tick sequences must be unique and increasing")
    funnel = {status: 0 for status in TERMINAL_STATUSES}
    rows: list[dict[str, object]] = []
    suppression: tuple[float, datetime, int] | None = None
    for index in range(14, len(h4) - 1):
        bar = h4[index]
        if not (datetime(2016, 7, 1) <= bar.time < datetime(2026, 7, 1)):
            continue
        if suppression is not None:
            box_mid, _, count = suppression
            count += 1
            if bar.close >= box_mid or count >= 12:
                suppression = None
            else:
                suppression = (box_mid, bar.time, count)
                funnel["SUPPRESSION_ACTIVE"] += 1
                continue
        impulse, distribution = h4[index - 12 : index - 6], h4[index - 6 : index]
        a_impulse, a_box = h4_atr[index - 7], h4_atr[index - 1]
        if a_impulse is None or a_box is None or a_impulse <= 0 or a_box <= 0:
            funnel["DATA_UNAVAILABLE"] += 1
            continue
        impulse_low, impulse_high = min(x.low for x in impulse), max(x.high for x in impulse)
        impulse_range = impulse_high - impulse_low
        impulse_net = impulse[-1].close - impulse[0].open
        bullish = sum(x.close > x.open for x in impulse)
        location = (impulse[-1].close - impulse_low) / impulse_range
        if not (impulse_net >= 1.5 * a_impulse and impulse_range >= 2 * a_impulse and bullish >= 4 and location >= 0.75):
            funnel["IMPULSE_REJECTED"] += 1
            continue
        box_low, box_high = min(x.low for x in distribution), max(x.high for x in distribution)
        width, box_mid = box_high - box_low, (box_high + box_low) / 2
        inner = sum(box_low + 0.2 * width <= x.close <= box_high - 0.2 * width for x in distribution)
        overlap = sum(_overlap_ratio(a, b) >= 0.25 for a, b in zip(distribution, distribution[1:]))
        drift = abs(distribution[-1].close - distribution[0].open)
        if not (a_box <= width <= 3 * a_box and inner >= 4 and overlap >= 4 and drift <= 0.75 * a_box):
            funnel["BOX_REJECTED"] += 1
            continue
        boundary = h4[index + 1].time
        router = classify_router(h1=h1, h4=h4, d1=d1, decision=boundary)
        if router not in {"UPTREND", "CHOP"}:
            funnel[f"ROUTER_BLOCKED_{router}"] += 1
            continue
        if not (
            distribution[-1].close >= box_low and bar.close <= box_low - 0.1 * a_box
            and bar.close < bar.open and _body_fraction(bar) >= 0.5 and _close_location(bar) <= 0.25
        ):
            funnel["BREAKDOWN_REJECTED"] += 1
            continue
        suppression = (box_mid, bar.time, 0)
        eligible_h1 = [j for j in range(len(h1) - 1) if h1[j].time >= boundary][:6]
        attempt: int | None = None
        for h1_index in eligible_h1:
            a_reclaim = h1_atr[h1_index]
            if a_reclaim is None or a_reclaim <= 0:
                continue
            if h1[h1_index].high >= box_low - 0.1 * a_reclaim:
                attempt = h1_index
                break
        if attempt is None:
            funnel["NO_RECLAIM_WITHIN_SIX_H1"] += 1
            continue
        reclaim, a_reclaim = h1[attempt], h1_atr[attempt]
        assert a_reclaim is not None
        if not (
            reclaim.close <= box_low - 0.05 * a_reclaim and reclaim.close < reclaim.open
            and _body_fraction(reclaim) >= 0.35 and _close_location(reclaim) <= 0.35
        ):
            funnel["FIRST_RECLAIM_NOT_REJECTED"] += 1
            continue
        decision = h1[attempt + 1].time
        eligible_ticks = [
            tick for tick in tick_rows
            if tick.time >= decision and tick.time <= decision + timedelta(minutes=15)
            and tick.session_open and tick.ask >= tick.bid > 0
        ]
        if not eligible_ticks:
            funnel["ENTRY_TICK_UNAVAILABLE"] += 1
            continue
        entry = eligible_ticks[0]
        raw_stop = max(reclaim.high, box_low) + 0.25 * a_reclaim
        structural_stop = normalize_up(raw_stop, contract)
        risk_price = normalize_up(structural_stop + contract.tick_size, contract)
        if structural_stop <= entry.ask or risk_price - entry.ask < max(contract.stops_level, contract.freeze_level) * contract.point:
            funnel["DATA_UNAVAILABLE"] += 1
            continue
        risk = minimum_contract_risk(entry.bid, risk_price, contract)
        box_id, episode_id, candidate_id = canonical_ids(
            symbol=symbol, distribution=distribution, box_low=normalize_up(box_low, contract),
            box_high=normalize_up(box_high, contract), breakdown_time=bar.time,
            reclaim_time=reclaim.time, entry_tick=entry, contract=contract,
        )
        row = {
            "schema_version": "a1_xau_r6_outcome_blind_census_row_v1",
            "rule_version": RULE_VERSION,
            "rule_sha256": RULE_SHA256,
            "candidate_id": candidate_id, "box_id": box_id, "episode_id": episode_id,
            "symbol": symbol, "router_state": router, "timestamp_basis": TIMESTAMP_BASIS,
            "impulse_start_h4_time": broker_time(impulse[0].time), "impulse_end_h4_time": broker_time(impulse[-1].time),
            "box_start_h4_time": broker_time(distribution[0].time), "box_end_h4_time": broker_time(distribution[-1].time),
            "breakdown_h4_time": broker_time(bar.time), "reclaim_h1_time": broker_time(reclaim.time),
            "decision_time": broker_time(decision), "entry_tick_time": broker_time(entry.time), "entry_tick_sequence": entry.sequence,
            "A_impulse": a_impulse, "A_box": a_box, "A_reclaim": a_reclaim,
            "impulse_low": impulse_low, "impulse_high": impulse_high,
            "impulse_range_atr": impulse_range / a_impulse, "impulse_net_advance_atr": impulse_net / a_impulse,
            "impulse_bullish_bars": bullish, "impulse_final_location": location,
            "box_low": box_low, "box_high": box_high, "box_width_atr": width / a_box,
            "box_inner_close_count": inner, "box_overlap_pair_count": overlap, "box_net_drift_atr": drift / a_box,
            "breakdown_distance_atr": (box_low - bar.close) / a_box,
            "breakdown_body_fraction": _body_fraction(bar), "breakdown_close_location": _close_location(bar),
            "reclaim_touch_distance_atr": (reclaim.high - box_low) / a_reclaim,
            "reclaim_body_fraction": _body_fraction(reclaim), "reclaim_close_location": _close_location(reclaim),
            "entry_bid": entry.bid, "entry_ask": entry.ask, "spread_points": (entry.ask - entry.bid) / contract.point,
            "raw_structural_stop": raw_stop, "structural_stop": structural_stop, "risk_exit_price": risk_price,
            "stop_points": (risk_price - entry.bid) / contract.point,
            "volume_min": contract.volume_min, "volume_step": contract.volume_step,
            "contract_size": contract.contract_size, "tick_size": contract.tick_size,
            "tick_value_loss": contract.tick_value_loss, "point": contract.point, "digits": contract.digits,
            "minimum_contract_risk_usd": risk,
            "reference_risk_feasible": risk <= 25.0, "deployment_risk_feasible": risk <= 2.5,
            "availability_status": "RAW_OPPORTUNITY_AVAILABLE", "exclusion_reason": "",
        }
        rows.append(row)
        funnel["RAW_OPPORTUNITY_AVAILABLE"] += 1
    return Detection(tuple(rows), funnel)
