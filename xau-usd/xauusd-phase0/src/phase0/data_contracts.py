from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Direction = Literal["LONG", "SHORT"]
EntryType = Literal["MARKET", "STOP", "LIMIT"]
GateStatus = Literal["PASS", "FAIL", "PENDING", "PASS_WITH_XAU_SPECIFIC_JUSTIFICATION"]


@dataclass(frozen=True)
class Signal:
    expert: str
    timestamp_utc: datetime
    symbol: str
    direction: Direction
    reason_code: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TradePlan:
    expert: str
    symbol: str
    direction: Direction
    signal_time_utc: datetime
    entry_type: EntryType
    entry_price: float | None
    stop_loss: float
    take_profit: float
    invalidation_level: float
    risk_reward: float
    reason_code: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Trade:
    expert: str
    symbol: str
    direction: Direction
    entry_time_utc: datetime
    exit_time_utc: datetime
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    lots: float
    gross_pnl_usd: float
    costs_usd: float
    net_pnl_usd: float
    r_multiple: float
    exit_reason: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class BacktestConfig:
    starting_equity_usd: float
    risk_per_trade_pct: float
    one_trade_at_a_time: bool
    ambiguous_intrabar_policy: str


@dataclass(frozen=True)
class CellConfig:
    cell_id: int
    start_utc: datetime
    end_utc: datetime
    broker: str
    cost_model: str
    symbol: str = "XAUUSD"


@dataclass(frozen=True)
class GateResult:
    name: str
    status: GateStatus
    threshold: str
    observed: str
    message: str


@dataclass(frozen=True)
class TickRecord:
    timestamp_utc: datetime
    broker: str
    symbol: str
    bid: float
    ask: float
    mid: float
    spread_price: float
    spread_points: float
    volume: float
    source_file: str
    row_number: int


@dataclass(frozen=True)
class BarRecord:
    timestamp_utc: datetime
    bar_start_utc: datetime
    bar_end_utc: datetime
    broker: str
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    mid_open: float
    mid_high: float
    mid_low: float
    mid_close: float
    bid_open: float
    bid_high: float
    bid_low: float
    bid_close: float
    ask_open: float
    ask_high: float
    ask_low: float
    ask_close: float
    spread_open_points: float
    spread_close_points: float
    spread_median_points: float
    spread_p95_points: float
    tick_count: int
    volume_sum: float
