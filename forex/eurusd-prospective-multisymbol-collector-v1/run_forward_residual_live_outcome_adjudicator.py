from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.forward_residual_live_outcome_adjudicator import (
    load_config,
    load_json_list,
    process,
    verify_lock,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-signals", type=Path, required=True)
    parser.add_argument("--mt5-receipts", type=Path, required=True)
    parser.add_argument("--terminal-decisions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    verify_lock()
    config = load_config()
    signals = load_json_list(args.live_signals)
    receipts = load_json_list(args.mt5_receipts)
    terminal_records = load_json_list(args.terminal_decisions)
    outcomes = load_json_list(
        args.output_dir / "FORWARD_RESIDUAL_LIVE_OUTCOMES.json"
    )
    parity_rows = load_json_list(
        args.output_dir / "FORWARD_RESIDUAL_SELECTION_PARITY.json"
    )
    mt5_holder: dict[str, Any] = {}

    def tick_provider(start: datetime, end: datetime) -> list[dict[str, Any]]:
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
            account = mt5.account_info()
            if account is None:
                raise RuntimeError(
                    f"MT5 account unavailable: {mt5.last_error()}"
                )
            if (
                account.login != int(config["required_account_login"])
                or account.server != str(config["required_account_server"])
                or account.trade_mode
                != int(config["required_account_trade_mode"])
            ):
                raise RuntimeError("MT5 live-outcome account boundary mismatch")
            if not mt5.symbol_select(str(config["symbol"]), True):
                raise RuntimeError(
                    f"MT5 symbol unavailable: {mt5.last_error()}"
                )
            mt5_holder["module"] = mt5
        ticks = mt5.copy_ticks_range(
            str(config["symbol"]),
            start,
            end,
            mt5.COPY_TICKS_ALL,
        )
        if ticks is None:
            raise RuntimeError(f"MT5 tick copy failed: {mt5.last_error()}")
        return [
            {
                "time_msc": int(row["time_msc"]),
                "bid": float(row["bid"]),
                "ask": float(row["ask"]),
                "last": float(row["last"]),
                "flags": int(row["flags"]),
            }
            for row in ticks
        ]

    try:
        outcomes, parity_rows, summary, raw_artifacts = process(
            signals,
            receipts,
            terminal_records,
            outcomes,
            parity_rows,
            datetime.now(UTC),
            tick_provider,
            config,
        )
        write_outputs(
            outcomes,
            parity_rows,
            summary,
            raw_artifacts,
            args.output_dir,
        )
    finally:
        if mt5_holder:
            mt5_holder["module"].shutdown()
    print(
        f"{summary['status']} "
        f"outcomes={summary['resolved_live_outcomes']} "
        f"invalid={summary['invalid_outcomes']} "
        f"parity_mismatch={summary['selection_mismatches']} "
        "order_api_calls=0 demo_order_authorized=false"
    )


if __name__ == "__main__":
    main()
