"""Pure, market-only R6 opportunity detector.

R6-C2 intentionally exposes no command-line entry point and performs no file I/O.
The real evidence build belongs to the separately reviewed R6-C3 phase.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
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
FROM_INCLUSIVE = datetime(2016, 7, 1)
HALF_BOUNDARY = datetime(2021, 7, 1)
TO_EXCLUSIVE = datetime(2026, 7, 1)


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
    source_h1_bar_time: datetime | None = None


@dataclass(frozen=True)
class Contract:
    account_currency: str
    account_leverage: int
    margin_mode: int
    server: str
    symbol: str
    point: float
    digits: int
    tick_size: float
    tick_value: float
    tick_value_loss: float
    volume_min: float
    volume_step: float
    volume_max: float
    contract_size: float
    stops_level: int
    freeze_level: int


@dataclass(frozen=True)
class Detection:
    rows: tuple[dict[str, object], ...]
    funnel: dict[str, int]
    anchors: tuple["TerminalAnchor", ...]
    incidence: dict[str, object]
    final_status: str
    contexts: dict[str, "RowContext"]


@dataclass(frozen=True)
class TerminalAnchor:
    anchor_time: datetime
    horizon_end: datetime | None
    status: str


@dataclass(frozen=True)
class RowContext:
    impulse: tuple[Bar, ...]
    distribution: tuple[Bar, ...]
    breakdown: Bar
    reclaim: Bar
    decision_time: datetime
    entry_tick: Tick
    contract: Contract
    a_impulse: float
    a_box: float
    a_reclaim: float
    last_reclaim_tick_sequence: int = -1
    causal_ticks: tuple[Tick, ...] = ()
    router_h1: tuple[Bar, ...] = ()
    router_h4: tuple[Bar, ...] = ()
    router_d1: tuple[Bar, ...] = ()


def broker_time(value: datetime) -> str:
    if value.tzinfo is not None:
        raise ValueError("broker wall-clock timestamps must be timezone-naive")
    return value.strftime("%Y-%m-%dT%H:%M:%S")


def validate_bars(bars: Sequence[Bar]) -> None:
    for index, bar in enumerate(bars):
        values = (bar.open, bar.high, bar.low, bar.close)
        if any(not math.isfinite(value) or value <= 0 for value in values):
            raise ValueError("invalid OHLC")
        if bar.high <= bar.low or bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close):
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


def _last_completed_index(bars: Sequence[Bar], decision: datetime) -> int:
    """Mirror native shift 1: a bar is completed only at the next native open."""
    return max(index for index in range(len(bars) - 1) if bars[index + 1].time <= decision)


def classify_router(*, h1: Sequence[Bar], h4: Sequence[Bar], d1: Sequence[Bar], decision: datetime) -> str:
    """Port the pinned market-only Router V1 priority using completed native bars."""
    try:
        h1_i = _last_completed_index(h1, decision)
        h4_i = _last_completed_index(h4, decision)
        d1_i = _last_completed_index(d1, decision)
        # MQL iBars includes the current native bar in addition to completed shift 1.
        h1_available, h4_available, d1_available = h1_i + 2, h4_i + 2, d1_i + 2
        h1_atr, d1_atr = wilder_atr(h1), wilder_atr(d1)
        # Exact RegimeRouterDataAvailable guards from the pinned Router V1 source.
        if (
            d1_available < 50 + 5 + 2 + 5
            or h4_available < 50 + 5 + 1 + 5
            or h1_available <= 14 + 10
            or d1_available <= 60 + 14 + 10
            or d1_available <= 252 + 14 + 10
            or h1_atr[h1_i] is None
            or d1_atr[d1_i] is None
            or h1[h1_i].high <= h1[h1_i].low
        ):
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
        five_day = d1[d1_i - 4 : d1_i + 1]
        box_width = max(bar.high for bar in five_day) - min(bar.low for bar in five_day)
        box_average = box_width / 5
        range_median = median(ranges[d1_i - 19 : d1_i + 1])
        if box_width <= 0 or range_median <= 0:
            return "UNKNOWN"
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
        contract.tick_value,
        contract.tick_value_loss,
        contract.volume_min,
        contract.volume_step,
        contract.volume_max,
        contract.contract_size,
    )
    if any(not math.isfinite(value) or value <= 0 for value in finite_positive):
        raise ValueError("invalid contract metadata")
    if (
        contract.digits < 0
        or contract.stops_level < 0
        or contract.freeze_level < 0
        or contract.account_leverage <= 0
        or contract.margin_mode < 0
        or contract.volume_max < contract.volume_min
        or not contract.account_currency
        or not contract.server
        or contract.symbol != "XAUUSD"
    ):
        raise ValueError("invalid contract metadata")


def minimum_contract_risk(entry_bid: float, risk_price: float, contract: Contract) -> float:
    """Captured-contract equivalent of short-side OrderCalcProfit magnitude."""
    validate_contract(contract)
    if not (math.isfinite(entry_bid) and math.isfinite(risk_price) and risk_price > entry_bid > 0):
        raise ValueError("invalid risk prices")
    ticks = (Decimal(str(risk_price)) - Decimal(str(entry_bid))) / Decimal(str(contract.tick_size))
    risk = ticks * Decimal(str(contract.tick_value_loss)) * Decimal(str(contract.volume_min))
    return float(risk)


def risk_at_or_below(value: float, boundary: float) -> bool:
    return Decimal(str(value)) <= Decimal(str(boundary))


def validate_order_calc_profit_fixture(
    entry_bid: float, risk_price: float, captured_loss: float, contract: Contract, *, tolerance: float = 1e-9,
) -> None:
    """Require the Python equivalent to match an immutable broker capture."""
    calculated = minimum_contract_risk(entry_bid, risk_price, contract)
    if not math.isfinite(captured_loss) or captured_loss <= 0 or not math.isclose(calculated, captured_loss, abs_tol=tolerance):
        raise ValueError("captured OrderCalcProfit parity failure")


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


def _half_counts(values: Sequence[datetime]) -> tuple[int, int]:
    return (
        sum(FROM_INCLUSIVE <= value < HALF_BOUNDARY for value in values),
        sum(HALF_BOUNDARY <= value < TO_EXCLUSIVE for value in values),
    )


def incidence_report(rows: Sequence[dict[str, object]]) -> dict[str, object]:
    """Evaluate every frozen incidence gate without using post-entry outcomes."""
    raw_times = [datetime.fromisoformat(str(row["entry_tick_time"])) for row in rows]
    if any(not (FROM_INCLUSIVE <= value < TO_EXCLUSIVE) for value in raw_times):
        raise ValueError("entry tick outside locked interval")
    reference_times = [
        value for value, row in zip(raw_times, rows) if bool(row["reference_risk_feasible"])
    ]
    deployment_times = [
        value for value, row in zip(raw_times, rows) if bool(row["deployment_risk_feasible"])
    ]

    def risk_summary(values: Sequence[datetime], minimum: int) -> dict[str, object]:
        early, late = _half_counts(values)
        report = concentration(values)
        buckets_with_events = sum(count > 0 for count in report["july_june"].values())
        return {
            "opportunities": len(values),
            "early_half": early,
            "late_half": late,
            "july_june_buckets_with_events": buckets_with_events,
            "passes": len(values) >= minimum and early >= 35 and late >= 35 and buckets_with_events >= 8,
        }

    raw_concentration = concentration(raw_times)
    raw_early, raw_late = _half_counts(raw_times)
    raw_counts = list(raw_concentration["july_june"].values())
    raw_total = len(raw_times)
    raw = {
        "opportunities": raw_total,
        "early_half": raw_early,
        "late_half": raw_late,
        "qualifying_july_june_buckets": sum(count >= 5 for count in raw_counts),
        "largest_july_june_bucket_share": max(raw_counts, default=0) / raw_total if raw_total else 0.0,
        "best_contiguous_24_month_share": raw_concentration["best_24_month_share"],
    }
    raw["passes"] = (
        raw_total >= 120
        and raw_early >= 40
        and raw_late >= 40
        and raw["qualifying_july_june_buckets"] >= 8
        and raw["largest_july_june_bucket_share"] <= 0.25
        and raw["best_contiguous_24_month_share"] <= 0.40
    )
    reference = risk_summary(reference_times, 100)
    deployment = risk_summary(deployment_times, 100)
    deployment["feasible_share"] = len(deployment_times) / raw_total if raw_total else 0.0
    deployment["passes"] = bool(deployment["passes"] and deployment["feasible_share"] >= 0.80)
    return {"raw": raw, "reference_risk": reference, "deployment_risk": deployment}


def locked_final_status(report: dict[str, object], *, evidence_valid: bool = True) -> str:
    if not evidence_valid:
        return "R6_CENSUS_EVIDENCE_INVALID"
    if not bool(report["raw"]["passes"]):
        return "R6_CENSUS_INSUFFICIENT_INCIDENCE"
    if not bool(report["reference_risk"]["passes"]):
        return "R6_CENSUS_REFERENCE_RISK_UNDERPOWERED"
    if not bool(report["deployment_risk"]["passes"]):
        return "R6_SMALL_ACCOUNT_CONTRACT_INFEASIBLE"
    return "R6_CENSUS_PASS"


def _body_fraction(bar: Bar) -> float:
    return abs(bar.close - bar.open) / (bar.high - bar.low)


def _close_location(bar: Bar) -> float:
    return (bar.close - bar.low) / (bar.high - bar.low)


def _overlap_ratio(first: Bar, second: Bar) -> float:
    overlap = max(0.0, min(first.high, second.high) - max(first.low, second.low))
    return overlap / min(first.high - first.low, second.high - second.low)


def _validate_tick_row(tick: Tick, previous: Tick | None) -> None:
    if (
        tick.sequence < 0
        or not all(math.isfinite(value) and value > 0 for value in (tick.bid, tick.ask))
        or tick.ask < tick.bid
        or (tick.source_h1_bar_time is not None and tick.source_h1_bar_time > tick.time)
    ):
        raise ValueError("invalid tick source row")
    if previous is not None and (previous.sequence >= tick.sequence or previous.time > tick.time):
        raise ValueError("ticks must be monotonic in absolute source sequence and time")


def select_entry_tick(
    ticks: Sequence[Tick], *, reclaim_time: datetime, decision_time: datetime,
) -> tuple[Tick | None, str, int, tuple[Tick, ...], bool]:
    """Consume ticks causally and stop at the first non-reclaim tick."""
    expiry = decision_time + timedelta(minutes=15)
    previous: Tick | None = None
    last_reclaim_sequence = -1
    consumed: list[Tick] = []
    horizon_proven = False
    for tick in ticks:
        _validate_tick_row(tick, previous)
        previous = tick
        if tick.time < decision_time:
            consumed.append(tick)
            if tick.source_h1_bar_time == reclaim_time:
                last_reclaim_sequence = tick.sequence
            continue
        if tick.time > expiry:
            horizon_proven = True
            break
        consumed.append(tick)
        if tick.source_h1_bar_time == reclaim_time:
            last_reclaim_sequence = tick.sequence
            continue
        if tick.source_h1_bar_time is not None and tick.source_h1_bar_time != decision_time:
            return None, "DATA_UNAVAILABLE", last_reclaim_sequence, tuple(consumed), True
        if tick.time == decision_time and tick.source_h1_bar_time is None:
            return None, "DATA_UNAVAILABLE", last_reclaim_sequence, tuple(consumed), True
        if not tick.session_open:
            return None, "ENTRY_TICK_UNAVAILABLE", last_reclaim_sequence, tuple(consumed), True
        return tick, "RAW_OPPORTUNITY_AVAILABLE", last_reclaim_sequence, tuple(consumed), True
    if horizon_proven:
        return None, "ENTRY_TICK_UNAVAILABLE", last_reclaim_sequence, tuple(consumed), True
    return None, "DATA_UNAVAILABLE", last_reclaim_sequence, tuple(consumed), False


def _causal_bars(bars: Sequence[Bar], decision_time: datetime) -> tuple[Bar, ...]:
    return tuple(bar for bar in bars if bar.time <= decision_time)


def detect(
    *, h4: Sequence[Bar], h1: Sequence[Bar], d1: Sequence[Bar], ticks: Sequence[Tick],
    contract: Contract, symbol: str = "XAUUSD",
) -> Detection:
    """Detect raw available opportunities and a deterministic terminal funnel."""
    validate_bars(h4)
    validate_bars(h1)
    validate_bars(d1)
    validate_contract(contract)
    if symbol != contract.symbol:
        raise ValueError("detector symbol does not match contract snapshot")
    h4_atr, h1_atr = wilder_atr(h4), wilder_atr(h1)
    tick_rows = list(ticks)
    funnel = {status: 0 for status in TERMINAL_STATUSES}
    rows: list[dict[str, object]] = []
    contexts: dict[str, RowContext] = {}
    anchors: list[TerminalAnchor] = []

    def finish(anchor_time: datetime, status: str, horizon_end: datetime | None) -> None:
        funnel[status] += 1
        anchors.append(TerminalAnchor(anchor_time, horizon_end, status))

    suppression: tuple[float, datetime, int] | None = None
    for index in range(14, len(h4) - 1):
        bar = h4[index]
        boundary = h4[index + 1].time
        if not (FROM_INCLUSIVE <= bar.time < TO_EXCLUSIVE):
            continue
        if suppression is not None:
            box_mid, _, count = suppression
            count += 1
            if bar.close >= box_mid or count >= 12:
                suppression = None
            else:
                suppression = (box_mid, bar.time, count)
                finish(bar.time, "SUPPRESSION_ACTIVE", boundary)
                continue
        impulse, distribution = h4[index - 12 : index - 6], h4[index - 6 : index]
        a_impulse, a_box = h4_atr[index - 7], h4_atr[index - 1]
        if a_impulse is None or a_box is None or a_impulse <= 0 or a_box <= 0:
            finish(bar.time, "DATA_UNAVAILABLE", boundary)
            continue
        impulse_low, impulse_high = min(x.low for x in impulse), max(x.high for x in impulse)
        impulse_range = impulse_high - impulse_low
        impulse_net = impulse[-1].close - impulse[0].open
        bullish = sum(x.close > x.open for x in impulse)
        location = (impulse[-1].close - impulse_low) / impulse_range
        if not (impulse_net >= 1.5 * a_impulse and impulse_range >= 2 * a_impulse and bullish >= 4 and location >= 0.75):
            finish(bar.time, "IMPULSE_REJECTED", boundary)
            continue
        box_low, box_high = min(x.low for x in distribution), max(x.high for x in distribution)
        width, box_mid = box_high - box_low, (box_high + box_low) / 2
        inner = sum(box_low + 0.2 * width <= x.close <= box_high - 0.2 * width for x in distribution)
        overlap = sum(_overlap_ratio(a, b) >= 0.25 for a, b in zip(distribution, distribution[1:]))
        drift = abs(distribution[-1].close - distribution[0].open)
        if not (a_box <= width <= 3 * a_box and inner >= 4 and overlap >= 4 and drift <= 0.75 * a_box):
            finish(bar.time, "BOX_REJECTED", boundary)
            continue
        router = classify_router(h1=h1, h4=h4, d1=d1, decision=boundary)
        if router not in {"UPTREND", "CHOP"}:
            finish(bar.time, f"ROUTER_BLOCKED_{router}", boundary)
            continue
        if not (
            distribution[-1].close >= box_low and bar.close <= box_low - 0.1 * a_box
            and bar.close < bar.open and _body_fraction(bar) >= 0.5 and _close_location(bar) <= 0.25
        ):
            finish(bar.time, "BREAKDOWN_REJECTED", boundary)
            continue
        suppression = (box_mid, bar.time, 0)
        eligible_h1 = [j for j in range(len(h1) - 1) if h1[j].time >= boundary]
        if len(eligible_h1) < 6:
            finish(bar.time, "DATA_UNAVAILABLE", None)
            continue
        eligible_h1 = eligible_h1[:6]
        six_h1_horizon = h1[eligible_h1[-1] + 1].time
        if six_h1_horizon >= TO_EXCLUSIVE:
            finish(bar.time, "DATA_UNAVAILABLE", six_h1_horizon)
            continue
        attempt: int | None = None
        for h1_index in eligible_h1:
            a_reclaim = h1_atr[h1_index]
            if a_reclaim is None or a_reclaim <= 0:
                finish(bar.time, "DATA_UNAVAILABLE", h1[h1_index + 1].time)
                attempt = -1
                break
            if h1[h1_index].high >= box_low - 0.1 * a_reclaim:
                attempt = h1_index
                break
        if attempt == -1:
            continue
        if attempt is None:
            finish(bar.time, "NO_RECLAIM_WITHIN_SIX_H1", six_h1_horizon)
            continue
        reclaim, a_reclaim = h1[attempt], h1_atr[attempt]
        assert a_reclaim is not None
        if not (
            reclaim.close <= box_low - 0.05 * a_reclaim and reclaim.close < reclaim.open
            and _body_fraction(reclaim) >= 0.35 and _close_location(reclaim) <= 0.35
        ):
            finish(bar.time, "FIRST_RECLAIM_NOT_REJECTED", h1[attempt + 1].time)
            continue
        decision = h1[attempt + 1].time
        if decision >= TO_EXCLUSIVE:
            finish(bar.time, "DATA_UNAVAILABLE", decision)
            continue
        entry, tick_status, last_reclaim_sequence, causal_ticks, tick_horizon_complete = select_entry_tick(
            tick_rows, reclaim_time=reclaim.time, decision_time=decision,
        )
        if entry is None:
            finish(
                bar.time, tick_status,
                decision + timedelta(minutes=15) if tick_status == "ENTRY_TICK_UNAVAILABLE"
                else decision if tick_horizon_complete else None,
            )
            continue
        if not (FROM_INCLUSIVE <= entry.time < TO_EXCLUSIVE):
            finish(bar.time, "DATA_UNAVAILABLE", entry.time)
            continue
        raw_stop = max(reclaim.high, box_low) + 0.25 * a_reclaim
        structural_stop = normalize_up(raw_stop, contract)
        risk_price = normalize_up(structural_stop + contract.tick_size, contract)
        if structural_stop <= entry.ask or risk_price - entry.ask < max(contract.stops_level, contract.freeze_level) * contract.point:
            finish(bar.time, "DATA_UNAVAILABLE", entry.time)
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
            "reference_risk_feasible": risk_at_or_below(risk, 25.0),
            "deployment_risk_feasible": risk_at_or_below(risk, 2.5),
            "availability_status": "RAW_OPPORTUNITY_AVAILABLE", "exclusion_reason": "",
        }
        rows.append(row)
        contexts[candidate_id] = RowContext(
            tuple(impulse), tuple(distribution), bar, reclaim, decision, entry, contract,
            a_impulse, a_box, a_reclaim, last_reclaim_sequence, causal_ticks,
            _causal_bars(h1, boundary), _causal_bars(h4, boundary), _causal_bars(d1, boundary),
        )
        finish(bar.time, "RAW_OPPORTUNITY_AVAILABLE", entry.time)
    incidence = incidence_report(rows)
    return Detection(tuple(rows), funnel, tuple(anchors), incidence, locked_final_status(incidence), contexts)
