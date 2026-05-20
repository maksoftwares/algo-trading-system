from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, parse_utc_datetime, resolve_symbol
from phase0.costs import (
    CostModel,
    apply_entry_slippage,
    apply_exit_slippage,
    load_cost_model,
    price_from_mid,
)
from phase0.data_contracts import Direction, EntryType, Trade, TradePlan
from phase0.sizing import (
    PositionSize,
    calculate_position_size,
    gross_pnl_usd,
    net_pnl_usd,
    r_multiple,
)


class ExecutionError(ConfigError):
    """Raised when a trade plan cannot be simulated."""


@dataclass(frozen=True)
class Fill:
    time_utc: datetime
    price: float
    bar_index: int
    reason: str


@dataclass(frozen=True)
class ExitFill(Fill):
    ambiguous_exit: bool = False


def simulate_trade(
    config: ProjectConfig,
    bars: pd.DataFrame,
    plan: TradePlan,
    broker: str,
    cost_model_name: str,
    current_equity: float,
    risk_per_trade_pct: float,
) -> Trade:
    """Simulate one trade plan against chronological bars."""

    canonical_symbol = resolve_symbol(config, plan.symbol)
    prepared = prepare_execution_bars(bars)
    if prepared.empty:
        raise ExecutionError("Cannot simulate trade on an empty bar DataFrame.")

    cost_model = load_cost_model(
        config,
        canonical_symbol,
        broker,
        cost_model_name,
        timestamp_utc=plan.signal_time_utc,
    )
    entry = find_entry_fill(prepared, plan, cost_model)
    size = calculate_position_size(
        config=config,
        symbol=canonical_symbol,
        direction=plan.direction,
        entry_price=entry.price,
        stop_loss=plan.stop_loss,
        current_equity=current_equity,
        risk_per_trade_pct=risk_per_trade_pct,
    )
    exit_fill = find_exit_fill(prepared, plan, entry, cost_model)
    symbol_details = config.symbols["symbols"][canonical_symbol]
    gross = gross_pnl_usd(
        plan.direction,
        entry.price,
        exit_fill.price,
        size.lots,
        float(symbol_details["contract_size_per_lot"]),
    )
    net = net_pnl_usd(gross, size.lots, cost_model.commission_usd_per_round_turn_lot)
    return Trade(
        expert=plan.expert,
        symbol=canonical_symbol,
        direction=plan.direction,
        entry_time_utc=entry.time_utc,
        exit_time_utc=exit_fill.time_utc,
        entry_price=entry.price,
        exit_price=exit_fill.price,
        stop_loss=plan.stop_loss,
        take_profit=plan.take_profit,
        lots=size.lots,
        gross_pnl_usd=gross,
        costs_usd=gross - net,
        net_pnl_usd=net,
        r_multiple=r_multiple(net, size.risk_money),
        exit_reason=exit_fill.reason,
        metadata={
            "entry_reason": entry.reason,
            "ambiguous_exit": exit_fill.ambiguous_exit,
            "cost_model": cost_model.name,
            "spread_points": cost_model.spread_points,
            "entry_slippage_price": cost_model.entry_slippage_price,
            "exit_slippage_price": cost_model.exit_slippage_price,
            "risk_money": size.risk_money,
            "actual_risk_usd": size.actual_risk_usd,
            "actual_risk_pct": size.actual_risk_pct,
            "raw_lots": size.raw_lots,
        },
    )


def find_entry_fill(bars: pd.DataFrame, plan: TradePlan, cost_model: CostModel) -> Fill:
    bars = prepare_execution_bars(bars)
    signal_time = _ensure_datetime(plan.signal_time_utc)
    if plan.entry_type == "MARKET":
        candidates = bars[bars["bar_start_utc"] >= signal_time]
        if candidates.empty:
            raise ExecutionError("No bar is available at or after signal time for market entry.")
        index = candidates.index[0]
        row = bars.loc[index]
        base_price = _entry_price_from_bar(row, plan.direction, cost_model)
        price = apply_entry_slippage(base_price, plan.direction, cost_model.entry_slippage_price)
        return Fill(
            time_utc=row["bar_start_utc"],
            price=price,
            bar_index=int(index),
            reason="market_next_bar_open",
        )

    if plan.entry_price is None:
        raise ExecutionError(f"{plan.entry_type} order requires entry_price.")

    candidates = _pending_entry_candidates(bars, plan, signal_time)
    for index, row in candidates.iterrows():
        if _pending_triggered(row, plan.direction, plan.entry_type, float(plan.entry_price)):
            price = apply_entry_slippage(
                float(plan.entry_price),
                plan.direction,
                cost_model.entry_slippage_price,
            )
            return Fill(
                time_utc=row["bar_start_utc"],
                price=price,
                bar_index=int(index),
                reason=f"{plan.entry_type.lower()}_triggered",
            )

    expires_after_bars = _expires_after_bars(plan)
    if expires_after_bars is not None:
        raise ExecutionError(
            f"Pending order expired after {expires_after_bars} bar(s) without triggering."
        )
    raise ExecutionError("Pending order was never triggered before the available bars ended.")


def find_exit_fill(
    bars: pd.DataFrame,
    plan: TradePlan,
    entry: Fill,
    cost_model: CostModel,
) -> ExitFill:
    candidates = bars.loc[entry.bar_index :]
    for index, row in candidates.iterrows():
        sl_hit, tp_hit = _exit_hits(row, plan.direction, plan.stop_loss, plan.take_profit)
        if not sl_hit and not tp_hit:
            continue

        if sl_hit and tp_hit:
            exit_price = apply_exit_slippage(
                _exit_price(plan.stop_loss, row, plan.direction, "stop_loss", cost_model),
                plan.direction,
                cost_model.exit_slippage_price,
            )
            return ExitFill(
                time_utc=row["timestamp_utc"],
                price=exit_price,
                bar_index=int(index),
                reason="stop_loss",
                ambiguous_exit=True,
            )

        if sl_hit:
            exit_price = apply_exit_slippage(
                _exit_price(plan.stop_loss, row, plan.direction, "stop_loss", cost_model),
                plan.direction,
                cost_model.exit_slippage_price,
            )
            return ExitFill(
                time_utc=row["timestamp_utc"],
                price=exit_price,
                bar_index=int(index),
                reason="stop_loss",
            )

        exit_price = apply_exit_slippage(
            _exit_price(plan.take_profit, row, plan.direction, "take_profit", cost_model),
            plan.direction,
            cost_model.exit_slippage_price,
        )
        return ExitFill(
            time_utc=row["timestamp_utc"],
            price=exit_price,
            bar_index=int(index),
            reason="take_profit",
        )

    final = bars.iloc[-1]
    exit_price = apply_exit_slippage(
        _close_exit_price(final, plan.direction, cost_model),
        plan.direction,
        cost_model.exit_slippage_price,
    )
    return ExitFill(
        time_utc=final["timestamp_utc"],
        price=exit_price,
        bar_index=int(bars.index[-1]),
        reason="end_of_test_period",
    )


def prepare_execution_bars(bars: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp_utc", "bar_start_utc", "open", "high", "low", "close"}
    missing = sorted(required - set(bars.columns))
    if missing:
        raise ExecutionError(f"Execution bars missing required column(s): {', '.join(missing)}.")

    prepared = bars.copy().reset_index(drop=True)
    prepared["timestamp_utc"] = pd.to_datetime(prepared["timestamp_utc"], utc=True, errors="coerce")
    prepared["bar_start_utc"] = pd.to_datetime(prepared["bar_start_utc"], utc=True, errors="coerce")
    if prepared["timestamp_utc"].isna().any() or prepared["bar_start_utc"].isna().any():
        raise ExecutionError("Execution bars contain invalid timestamps.")
    return prepared.sort_values("timestamp_utc").reset_index(drop=True)


def _entry_price_from_bar(row: pd.Series, direction: Direction, cost_model: CostModel) -> float:
    if direction == "LONG" and "ask_open" in row and pd.notna(row["ask_open"]):
        return float(row["ask_open"])
    if direction == "SHORT" and "bid_open" in row and pd.notna(row["bid_open"]):
        return float(row["bid_open"])
    mid_open = float(row["mid_open"] if "mid_open" in row and pd.notna(row["mid_open"]) else row["open"])
    return price_from_mid(mid_open, direction, "entry", cost_model.spread_price)


def _close_exit_price(row: pd.Series, direction: Direction, cost_model: CostModel) -> float:
    if direction == "LONG" and "bid_close" in row and pd.notna(row["bid_close"]):
        return float(row["bid_close"])
    if direction == "SHORT" and "ask_close" in row and pd.notna(row["ask_close"]):
        return float(row["ask_close"])
    mid_close = float(row["mid_close"] if "mid_close" in row and pd.notna(row["mid_close"]) else row["close"])
    return price_from_mid(mid_close, direction, "exit", cost_model.spread_price)


def _exit_price(
    target_price: float,
    row: pd.Series,
    direction: Direction,
    reason: str,
    cost_model: CostModel,
) -> float:
    del row, cost_model
    # Stop/target prices in a TradePlan are executable bid/ask-adjusted price levels. Spread is
    # applied during entry planning; here we only apply configured exit slippage.
    return float(target_price)


def _pending_triggered(
    row: pd.Series,
    direction: Direction,
    entry_type: EntryType,
    entry_price: float,
) -> bool:
    high = float(row["high"])
    low = float(row["low"])
    if direction == "LONG" and entry_type == "STOP":
        return high >= entry_price
    if direction == "SHORT" and entry_type == "STOP":
        return low <= entry_price
    if direction == "LONG" and entry_type == "LIMIT":
        return low <= entry_price
    if direction == "SHORT" and entry_type == "LIMIT":
        return high >= entry_price
    raise ExecutionError(f"Unsupported pending order combination: {direction} {entry_type}.")


def _pending_entry_candidates(
    bars: pd.DataFrame,
    plan: TradePlan,
    signal_time: pd.Timestamp,
) -> pd.DataFrame:
    candidates = bars[bars["bar_start_utc"] >= signal_time]
    expires_after_bars = _expires_after_bars(plan)
    if expires_after_bars is None:
        return candidates
    return candidates.iloc[:expires_after_bars]


def _expires_after_bars(plan: TradePlan) -> int | None:
    raw_value = plan.metadata.get("expires_after_bars")
    if raw_value in (None, ""):
        return None
    try:
        expires_after_bars = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ExecutionError("expires_after_bars must be a positive integer.") from exc
    if expires_after_bars <= 0:
        raise ExecutionError("expires_after_bars must be a positive integer.")
    return expires_after_bars


def _exit_hits(
    row: pd.Series,
    direction: Direction,
    stop_loss: float,
    take_profit: float,
) -> tuple[bool, bool]:
    high = float(row["high"])
    low = float(row["low"])
    if direction == "LONG":
        return low <= stop_loss, high >= take_profit
    if direction == "SHORT":
        return high >= stop_loss, low <= take_profit
    raise ExecutionError(f"Unknown direction {direction!r}.")


def _ensure_datetime(value: datetime) -> pd.Timestamp:
    return pd.Timestamp(parse_utc_datetime(value))
