from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import MetaTrader5 as mt5


PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE / "src"))

from step_3_common import write_json  # noqa: E402


TERMINAL = Path(r"C:\MT5PortableTier1BestEA\terminal64.exe")
EXPECTED_LOGIN = 1033030
EXPECTED_SERVER = "Capital.ComMena-Demo"
EXPECTED_CURRENCY = "AED"
SYMBOL = "XAUUSD"
REFERENCE_LOT = 0.01


def main() -> None:
    if not TERMINAL.is_file():
        raise FileNotFoundError(TERMINAL)
    if not mt5.initialize(path=str(TERMINAL), portable=True):
        raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        symbol = mt5.symbol_info(SYMBOL)
        tick = mt5.symbol_info_tick(SYMBOL)
        if account is None or terminal is None or symbol is None or tick is None:
            raise RuntimeError(f"MT5 metadata unavailable: {mt5.last_error()}")
        if account.login != EXPECTED_LOGIN:
            raise ValueError(f"Wrong MT5 login: {account.login}")
        if account.server != EXPECTED_SERVER or account.currency != EXPECTED_CURRENCY:
            raise ValueError("Unexpected MT5 server or account currency")
        positions = mt5.positions_get() or ()
        orders = mt5.orders_get() or ()
        if positions or orders:
            raise ValueError("Broker snapshot requires no open positions or pending orders")
        if not terminal.connected:
            raise ValueError("MT5 terminal is not connected")
        price = float(tick.ask)
        plus = mt5.order_calc_profit(
            mt5.ORDER_TYPE_BUY, SYMBOL, REFERENCE_LOT, price, price + 1.0
        )
        minus = mt5.order_calc_profit(
            mt5.ORDER_TYPE_BUY, SYMBOL, REFERENCE_LOT, price, price - 1.0
        )
        buy_margin = mt5.order_calc_margin(
            mt5.ORDER_TYPE_BUY, SYMBOL, REFERENCE_LOT, price
        )
        if plus is None or minus is None or buy_margin is None:
            raise RuntimeError(f"MT5 calculation probe failed: {mt5.last_error()}")
        ticks_per_price_unit = 1.0 / float(symbol.trade_tick_size)
        profit_rate = (
            float(symbol.trade_tick_value_profit)
            * ticks_per_price_unit
            * REFERENCE_LOT
        )
        loss_rate = (
            float(symbol.trade_tick_value_loss)
            * ticks_per_price_unit
            * REFERENCE_LOT
        )
        payload = {
            "schema_version": "xauusd_step_5_1_broker_snapshot_v1",
            "captured_utc": datetime.now(UTC).isoformat(),
            "read_only": True,
            "terminal_path": TERMINAL.as_posix(),
            "terminal": {
                "connected": bool(terminal.connected),
                "trade_allowed": bool(terminal.trade_allowed),
                "build": int(terminal.build),
                "data_path": str(terminal.data_path),
            },
            "account": {
                "login": int(account.login),
                "server": str(account.server),
                "name": str(account.name),
                "currency": str(account.currency),
                "trade_mode": int(account.trade_mode),
                "leverage": int(account.leverage),
                "balance": float(account.balance),
                "equity": float(account.equity),
                "margin": float(account.margin),
                "margin_free": float(account.margin_free),
                "trade_allowed": bool(account.trade_allowed),
                "trade_expert": bool(account.trade_expert),
            },
            "symbol": {
                "name": str(symbol.name),
                "description": str(symbol.description),
                "currency_base": str(symbol.currency_base),
                "currency_profit": str(symbol.currency_profit),
                "currency_margin": str(symbol.currency_margin),
                "trade_contract_size": float(symbol.trade_contract_size),
                "trade_tick_size": float(symbol.trade_tick_size),
                "trade_tick_value_profit": float(symbol.trade_tick_value_profit),
                "trade_tick_value_loss": float(symbol.trade_tick_value_loss),
                "volume_min": float(symbol.volume_min),
                "volume_step": float(symbol.volume_step),
                "trade_mode": int(symbol.trade_mode),
                "bid": float(tick.bid),
                "ask": float(tick.ask),
            },
            "conversion": {
                "source_currency": "USD",
                "account_currency": str(account.currency),
                "reference_lot": REFERENCE_LOT,
                "profit_account_per_source_usd": profit_rate,
                "loss_account_per_source_usd": loss_rate,
                "profit_probe_account_for_plus_1_usd": float(plus),
                "loss_probe_account_for_minus_1_usd": float(minus),
                "broker_margin_probe_account": float(buy_margin),
                "rate_source": "MT5_SYMBOL_TICK_VALUES_AT_CAPTURE",
            },
            "open_positions": 0,
            "pending_orders": 0,
            "broker_action_performed": False,
        }
        output = PACKAGE / "outputs/step_5_1/STEP_5_1_BROKER_SNAPSHOT.json"
        write_json(output, payload)
        print(output)
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
