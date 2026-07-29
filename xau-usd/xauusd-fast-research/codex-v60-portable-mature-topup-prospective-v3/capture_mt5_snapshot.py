from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import MetaTrader5 as mt5
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "inputs" / "CAPITAL_XAUUSD_M5_20260601_20260724.parquet"
TERMINAL = Path("C:/MT5PortableTier1BestEA/terminal64.exe")


def main() -> int:
    if not mt5.initialize(path=str(TERMINAL), portable=True):
        raise RuntimeError(f"MT5 initialization failed: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        if account is None or int(account.login) != 1033030:
            raise RuntimeError("Unexpected MT5 account")
        symbol = mt5.symbol_info("XAUUSD")
        if symbol is None or float(symbol.point) != 0.01:
            raise RuntimeError("Unexpected XAUUSD point geometry")
        rates = mt5.copy_rates_range(
            "XAUUSD",
            mt5.TIMEFRAME_M5,
            datetime(2026, 6, 1, tzinfo=UTC),
            datetime(2026, 7, 25, tzinfo=UTC),
        )
        if rates is None or len(rates) < 9000:
            raise RuntimeError(f"Insufficient Capital M5 history: {mt5.last_error()}")
        frame = pd.DataFrame(rates)
        frame["bar_start_utc"] = pd.to_datetime(frame["time"], unit="s", utc=True)
        frame = frame.sort_values("bar_start_utc", kind="mergesort")
        frame = frame.drop_duplicates("bar_start_utc", keep="last").reset_index(drop=True)
        if frame["bar_start_utc"].max() >= pd.Timestamp("2026-07-25T00:00:00Z"):
            raise RuntimeError("Snapshot exceeded the preregistered end boundary")
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(OUTPUT, index=False)
        print(f"{OUTPUT} rows={len(frame)}")
    finally:
        mt5.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
