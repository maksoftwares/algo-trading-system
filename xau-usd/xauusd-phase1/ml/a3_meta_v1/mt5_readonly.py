from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


READ_ONLY_MT5_CALLS = frozenset(
    {
        "initialize",
        "shutdown",
        "version",
        "last_error",
        "account_info",
        "terminal_info",
        "symbols_get",
        "symbol_info",
        "symbol_info_tick",
        "copy_rates_range",
        "copy_ticks_range",
        "history_orders_get",
        "history_deals_get",
        "positions_get",
        "orders_get",
    }
)

FORBIDDEN_MT5_CALLS = frozenset(
    {
        "login",
        "order_send",
        "order_check",
        "symbol_select",
        "market_book_add",
        "market_book_release",
    }
)


class MT5ReadOnlyError(RuntimeError):
    """Raised when the read-only MT5 facade is used unsafely."""


@dataclass(frozen=True)
class MT5ConnectionSpec:
    terminal_exe: str
    portable: bool


class ReadOnlyMT5Client:
    """Narrow MetaTrader5 facade.

    This is the only C02 module that may load the MetaTrader5 package. It exposes
    read-only methods by name and intentionally has no generic passthrough.
    """

    def __init__(self, mt5_module: Any) -> None:
        self._mt5 = mt5_module

    @classmethod
    def from_installed_package(cls) -> "ReadOnlyMT5Client":
        return cls(importlib.import_module("MetaTrader5"))

    def initialize(self, spec: MT5ConnectionSpec) -> bool:
        return bool(self._mt5.initialize(path=str(Path(spec.terminal_exe)), portable=spec.portable))

    def shutdown(self) -> None:
        self._mt5.shutdown()

    def version(self) -> Any:
        return self._mt5.version()

    def last_error(self) -> Any:
        return self._mt5.last_error()

    def account_info(self) -> Any:
        return self._mt5.account_info()

    def terminal_info(self) -> Any:
        return self._mt5.terminal_info()

    def symbols_get(self, group: str | None = None) -> Any:
        return self._mt5.symbols_get() if group is None else self._mt5.symbols_get(group=group)

    def symbol_info(self, symbol: str) -> Any:
        return self._mt5.symbol_info(symbol)

    def symbol_info_tick(self, symbol: str) -> Any:
        return self._mt5.symbol_info_tick(symbol)

    def copy_rates_range(self, symbol: str, timeframe: int, date_from: datetime, date_to: datetime) -> Any:
        return self._mt5.copy_rates_range(symbol, timeframe, date_from, date_to)

    def copy_ticks_range(self, symbol: str, date_from: datetime, date_to: datetime, flags: int) -> Any:
        return self._mt5.copy_ticks_range(symbol, date_from, date_to, flags)

    def history_orders_get(self, date_from: datetime, date_to: datetime, group: str | None = None) -> Any:
        if group is None:
            return self._mt5.history_orders_get(date_from, date_to)
        return self._mt5.history_orders_get(date_from, date_to, group=group)

    def history_deals_get(self, date_from: datetime, date_to: datetime, group: str | None = None) -> Any:
        if group is None:
            return self._mt5.history_deals_get(date_from, date_to)
        return self._mt5.history_deals_get(date_from, date_to, group=group)

    def positions_get(self, symbol: str | None = None) -> Any:
        return self._mt5.positions_get() if symbol is None else self._mt5.positions_get(symbol=symbol)

    def orders_get(self, symbol: str | None = None) -> Any:
        return self._mt5.orders_get() if symbol is None else self._mt5.orders_get(symbol=symbol)

    def timeframe_value(self, name: str) -> int:
        attr = f"TIMEFRAME_{name.upper()}"
        value = getattr(self._mt5, attr, None)
        if value is None:
            raise MT5ReadOnlyError(f"unsupported MT5 timeframe {name!r}")
        return int(value)

    def copy_ticks_all_flags(self) -> int:
        return int(self._mt5.COPY_TICKS_ALL)


def assert_read_only_method(name: str) -> None:
    if name not in READ_ONLY_MT5_CALLS:
        raise MT5ReadOnlyError(f"MT5 call {name!r} is not in the C02 read-only allowlist")
    if name in FORBIDDEN_MT5_CALLS:
        raise MT5ReadOnlyError(f"MT5 call {name!r} is explicitly forbidden")
