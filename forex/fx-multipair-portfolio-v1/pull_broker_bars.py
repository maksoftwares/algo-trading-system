"""Pull broker-native H1 bars *including the spread field*. Read-only.

Two problems this solves at once:

1. `measure_broker_costs.py` had to run with the market closed, so its live
   spread readings are weekend-wide and unusable. MT5 bars carry a per-bar
   ``spread`` in points, which gives the real *trading-hours* spread history
   without waiting for the open.
2. The prior EURUSD lane recorded that Dukascopy-first candidates "did not
   transfer to Capital.com". Broker-native bars remove that objection for any
   follow-up test.

Safety contract: ``initialize``, ``account_info``, ``symbol_select``,
``symbol_info`` and ``copy_rates_range`` only. No orders, no modifications,
demo-only, writes solely to the research cache and this package's outputs.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
START = datetime(2015, 1, 1, tzinfo=UTC)
END = datetime(2026, 7, 27, tzinfo=UTC)

SYMBOLS = (
    # USD majors
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
    # crosses (less efficient than majors; never tested in this lane)
    "EURGBP", "EURJPY", "GBPJPY", "EURAUD", "AUDJPY", "EURCHF", "CADJPY",
    "AUDNZD", "GBPAUD", "EURCAD", "CHFJPY", "NZDJPY", "GBPCHF",
    # EM / high-carry
    "USDMXN", "USDZAR", "USDTRY", "USDPLN", "USDHUF", "USDCNH", "USDSEK", "USDNOK",
)


def main() -> int:
    if not mt5.initialize():
        print(f"initialize failed: {mt5.last_error()}")
        return 1
    try:
        account = mt5.account_info()
        if account is None or account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            print("REFUSING: not a demo account.")
            return 2
        print(f"account {account.login} @ {account.server} (read-only)\n")

        (CACHE / "broker_h1").mkdir(parents=True, exist_ok=True)
        report: dict[str, object] = {
            "schema_version": "fx_broker_h1_bars_v1",
            "access": "READ_ONLY_COPY_RATES_NO_ORDERS",
            "account": {"login": account.login, "server": account.server},
            "request_window": {"start": START.isoformat(), "end": END.isoformat()},
            "symbols": {},
        }
        print(
            f"{'symbol':9s} {'bars':>7} {'first':>11} {'last':>11} "
            f"{'sprd_med':>9} {'sprd_p95':>9} {'pips_med':>9}"
        )
        print("-" * 74)

        for symbol in SYMBOLS:
            if not mt5.symbol_select(symbol, True):
                print(f"{symbol:9s} not selectable")
                continue
            info = mt5.symbol_info(symbol)
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, START, END)
            if rates is None or len(rates) == 0:
                print(f"{symbol:9s} no bars ({mt5.last_error()})")
                continue
            frame = pd.DataFrame(rates)
            frame["timestamp_utc"] = pd.to_datetime(frame["time"], unit="s", utc=True)
            # Trading-hours only: weekend bars carry an artificially wide spread.
            weekday = frame["timestamp_utc"].dt.weekday
            trading = frame[(weekday < 5) & (frame["spread"] > 0)]
            pip_points = 10.0 if info.digits in (3, 5) else 1.0
            median = float(trading["spread"].median()) if len(trading) else float("nan")
            p95 = float(trading["spread"].quantile(0.95)) if len(trading) else float("nan")

            path = CACHE / "broker_h1" / f"{symbol}_H1.parquet"
            frame.to_parquet(path, index=False, compression="zstd")
            report["symbols"][symbol] = {
                "bars": int(len(frame)),
                "trading_hour_bars": int(len(trading)),
                "first_utc": str(frame["timestamp_utc"].iloc[0]),
                "last_utc": str(frame["timestamp_utc"].iloc[-1]),
                "spread_points_median": median,
                "spread_points_p95": p95,
                "spread_pips_median": round(median / pip_points, 3),
                "digits": info.digits,
                "point": info.point,
                "swap_long": info.swap_long,
                "swap_short": info.swap_short,
                "path": str(path),
            }
            print(
                f"{symbol:9s} {len(frame):>7} {str(frame['timestamp_utc'].iloc[0].date()):>11} "
                f"{str(frame['timestamp_utc'].iloc[-1].date()):>11} {median:>9.1f} {p95:>9.1f} "
                f"{median / pip_points:>9.2f}"
            )

        out = ROOT / "outputs" / "BROKER_H1_INVENTORY.json"
        out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\nwrote {out}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
