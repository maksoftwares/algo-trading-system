from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.forward_residual_mt5_shadow_bridge import (
    load_config,
    load_json_list,
    process,
    verify_lock,
    write_outputs,
)

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-signals", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify_lock()
    config = load_config()
    signals = load_json_list(args.live_signals)
    receipt_path = (
        args.output_dir / "FORWARD_RESIDUAL_MT5_SHADOW_RECEIPTS.json"
    )
    existing = load_json_list(receipt_path)
    mt5_holder: dict[str, Any] = {}

    def quote_provider() -> dict[str, Any]:
        import MetaTrader5 as mt5

        if not mt5_holder:
            if mt5.__version__ != str(
                config["required_metatrader5_python_version"]
            ):
                raise RuntimeError(
                    "MetaTrader5 Python version mismatch: "
                    f"{mt5.__version__}"
                )
            initialized = mt5.initialize(
                path=str(config["terminal_path"]),
                portable=bool(config["terminal_portable"]),
                timeout=10000,
            )
            if not initialized:
                raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
            mt5_holder["module"] = mt5
        account = mt5.account_info()
        if account is None:
            raise RuntimeError(f"MT5 account unavailable: {mt5.last_error()}")
        if not mt5.symbol_select(str(config["symbol"]), True):
            raise RuntimeError(f"MT5 symbol unavailable: {mt5.last_error()}")
        tick = mt5.symbol_info_tick(str(config["symbol"]))
        if tick is None:
            raise RuntimeError(f"MT5 tick unavailable: {mt5.last_error()}")
        return {
            "account_login": account.login,
            "account_server": account.server,
            "account_trade_mode": account.trade_mode,
            "symbol": str(config["symbol"]),
            "tick_time_utc": datetime.fromtimestamp(
                tick.time_msc / 1000.0,
                tz=UTC,
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bid": tick.bid,
            "ask": tick.ask,
        }

    try:
        receipts, summary = process(
            signals,
            existing,
            datetime.now(UTC),
            quote_provider,
            config,
        )
        write_outputs(receipts, summary, args.output_dir)
    finally:
        if mt5_holder:
            mt5_holder["module"].shutdown()
    print(
        f"{summary['status']} "
        f"receipts={summary['receipts']} "
        f"captured={summary['shadow_entries_captured']} "
        "order_api_calls=0 demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
