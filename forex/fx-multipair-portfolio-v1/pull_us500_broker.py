"""Build US500 M5 bid/ask bars from Capital.com broker tick history. Read-only.

Two independent US500 sources are being assembled:

* this one — the broker's own ticks, i.e. exactly the venue that would be
  traded, roughly one year deep;
* `acquire_us500.py` — Dukascopy from 2016, for regime depth.

Having both matters. The Forex lane's most expensive lesson was that a candidate
tuned on one venue need not survive on another, so any US500 result will be
required to hold on both.

Ticks are pulled in slices because a year of index ticks is large. Bars use the
same schema as the FX M5 cache, so the existing engine, indicators and report
helpers work unchanged.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SYMBOL = "US500"
M5_MS = 300_000
SLICE_DAYS = 7
LOOKBACK_DAYS = 420


def bars_from_ticks(frame: pd.DataFrame) -> pd.DataFrame:
    stamps = frame["time_msc"].to_numpy(np.int64)
    order = np.argsort(stamps, kind="stable")
    stamps = stamps[order]
    bid = frame["bid"].to_numpy(np.float64)[order]
    ask = frame["ask"].to_numpy(np.float64)[order]
    slots = stamps - (stamps % M5_MS)
    starts = np.flatnonzero(np.r_[True, slots[1:] != slots[:-1]])
    ends = np.r_[starts[1:] - 1, slots.size - 1]
    return pd.DataFrame(
        {
            "timestamp_ms": slots[starts],
            "bid_open": bid[starts],
            "bid_high": np.maximum.reduceat(bid, starts),
            "bid_low": np.minimum.reduceat(bid, starts),
            "bid_close": bid[ends],
            "ask_open": ask[starts],
            "ask_high": np.maximum.reduceat(ask, starts),
            "ask_low": np.minimum.reduceat(ask, starts),
            "ask_close": ask[ends],
            "tick_count": (ends - starts + 1).astype(np.int32),
        }
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
        if not mt5.symbol_select(SYMBOL, True):
            print(f"cannot select {SYMBOL}")
            return 3
        info = mt5.symbol_info(SYMBOL)
        print(f"account {account.login} @ {account.server} (read-only)")
        print(f"{SYMBOL}: point={info.point} digits={info.digits} "
              f"contract={info.trade_contract_size} min_lot={info.volume_min}")

        end = datetime.now().replace(tzinfo=None)
        start = end - timedelta(days=LOOKBACK_DAYS)
        chunks, empty_slices = [], 0
        cursor = start
        while cursor < end:
            stop = min(cursor + timedelta(days=SLICE_DAYS), end)
            ticks = mt5.copy_ticks_range(SYMBOL, cursor, stop, mt5.COPY_TICKS_INFO)
            if ticks is not None and len(ticks):
                frame = pd.DataFrame(ticks)
                frame = frame[(frame["bid"] > 0) & (frame["ask"] > 0)]
                if not frame.empty:
                    chunks.append(bars_from_ticks(frame))
                    print(f"  {cursor.date()} .. {stop.date()}: {len(frame):>9,} ticks", flush=True)
                else:
                    empty_slices += 1
            else:
                empty_slices += 1
            cursor = stop

        if not chunks:
            print("no ticks returned for any slice")
            return 4

        bars = (
            pd.concat(chunks, ignore_index=True)
            .drop_duplicates("timestamp_ms", keep="last")
            .sort_values("timestamp_ms", kind="stable", ignore_index=True)
        )
        (CACHE / "bars").mkdir(parents=True, exist_ok=True)
        path = CACHE / "bars" / f"{SYMBOL}_M5_BIDASK_BROKER.parquet"
        bars.to_parquet(path, index=False, compression="zstd")

        spread = (bars["ask_close"] - bars["bid_close"]).to_numpy() / info.point
        stamps = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
        manifest = {
            "schema_version": "us500_broker_m5_v1",
            "source": "Capital.com demo via MT5 copy_ticks_range (read-only)",
            "account": {"login": account.login, "server": account.server},
            "symbol": SYMBOL,
            "point": info.point,
            "digits": info.digits,
            "contract_size": info.trade_contract_size,
            "volume_min": info.volume_min,
            "m5_bars": int(len(bars)),
            "first_bar_utc": str(stamps.iloc[0]),
            "last_bar_utc": str(stamps.iloc[-1]),
            "distinct_dates": int(stamps.dt.strftime("%Y-%m-%d").nunique()),
            "spread_points_median": float(np.median(spread)),
            "spread_points_p95": float(np.quantile(spread, 0.95)),
            "negative_spread_bars": int((spread < 0).sum()),
            "empty_slices": empty_slices,
            "path": str(path),
        }
        (CACHE / "bars" / f"{SYMBOL}_BROKER_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(
            f"\n{SYMBOL}: {len(bars):,} M5 bars  {stamps.iloc[0]} .. {stamps.iloc[-1]}"
            f"\n  dates={manifest['distinct_dates']}  spread median={manifest['spread_points_median']:.0f} pts"
            f"  p95={manifest['spread_points_p95']:.0f}  neg={manifest['negative_spread_bars']}"
        )
        print(f"wrote {path}")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
