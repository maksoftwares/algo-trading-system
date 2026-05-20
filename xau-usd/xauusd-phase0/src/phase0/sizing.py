from __future__ import annotations

import math
from dataclasses import dataclass

from phase0.config import ConfigError, ProjectConfig, get_symbol_details, resolve_symbol
from phase0.costs import commission_usd
from phase0.data_contracts import Direction


class SizingError(ConfigError):
    """Raised when a trade cannot be sized under Phase 0 risk rules."""


@dataclass(frozen=True)
class PositionSize:
    lots: float
    raw_lots: float
    risk_money: float
    price_risk: float
    risk_per_lot_usd: float
    actual_risk_usd: float
    actual_risk_pct: float


def calculate_risk_money(current_equity: float, risk_per_trade_pct: float) -> float:
    if current_equity <= 0:
        raise SizingError(f"Current equity must be positive, got {current_equity}.")
    if risk_per_trade_pct <= 0:
        raise SizingError(f"Risk per trade must be positive, got {risk_per_trade_pct}.")
    return current_equity * risk_per_trade_pct


def calculate_price_risk(direction: Direction, entry_price: float, stop_loss: float) -> float:
    if direction == "LONG":
        price_risk = entry_price - stop_loss
    elif direction == "SHORT":
        price_risk = stop_loss - entry_price
    else:
        raise SizingError(f"Unknown direction {direction!r}.")

    if price_risk <= 0:
        raise SizingError(
            f"Invalid {direction} price risk: entry={entry_price}, stop_loss={stop_loss}, "
            f"price_risk={price_risk}."
        )
    return price_risk


def floor_to_lot_step(value: float, lot_step: float) -> float:
    if lot_step <= 0:
        raise SizingError(f"Lot step must be positive, got {lot_step}.")
    floored = math.floor((value / lot_step) + 1e-12) * lot_step
    decimals = max(0, _decimal_places(lot_step))
    return round(floored, decimals)


def calculate_position_size(
    config: ProjectConfig,
    symbol: str,
    direction: Direction,
    entry_price: float,
    stop_loss: float,
    current_equity: float,
    risk_per_trade_pct: float,
) -> PositionSize:
    canonical_symbol = resolve_symbol(config, symbol)
    details = get_symbol_details(config, canonical_symbol)
    contract_size = float(details["contract_size_per_lot"])
    min_lot = float(details["min_lot"])
    lot_step = float(details["lot_step"])

    risk_money = calculate_risk_money(current_equity, risk_per_trade_pct)
    price_risk = calculate_price_risk(direction, entry_price, stop_loss)
    risk_per_lot_usd = price_risk * contract_size
    raw_lots = risk_money / risk_per_lot_usd
    lots = floor_to_lot_step(raw_lots, lot_step)
    if lots < min_lot:
        raise SizingError(
            f"Calculated lots {lots} is below min_lot {min_lot} for {canonical_symbol}. "
            "Rejecting trade rather than resizing above allowed risk."
        )

    actual_risk_usd = lots * risk_per_lot_usd
    return PositionSize(
        lots=lots,
        raw_lots=raw_lots,
        risk_money=risk_money,
        price_risk=price_risk,
        risk_per_lot_usd=risk_per_lot_usd,
        actual_risk_usd=actual_risk_usd,
        actual_risk_pct=actual_risk_usd / current_equity,
    )


def gross_pnl_usd(
    direction: Direction,
    entry_price: float,
    exit_price: float,
    lots: float,
    contract_size_per_lot: float,
) -> float:
    if direction == "LONG":
        return (exit_price - entry_price) * lots * contract_size_per_lot
    if direction == "SHORT":
        return (entry_price - exit_price) * lots * contract_size_per_lot
    raise SizingError(f"Unknown direction {direction!r}.")


def net_pnl_usd(gross_pnl: float, lots: float, commission_usd_per_round_turn_lot: float) -> float:
    return gross_pnl - commission_usd(lots, commission_usd_per_round_turn_lot)


def r_multiple(net_pnl: float, risk_money_at_entry: float) -> float:
    if risk_money_at_entry <= 0:
        raise SizingError(f"Risk money at entry must be positive, got {risk_money_at_entry}.")
    return net_pnl / risk_money_at_entry


def _decimal_places(value: float) -> int:
    text = f"{value:.10f}".rstrip("0")
    return len(text.split(".", maxsplit=1)[1]) if "." in text else 0
