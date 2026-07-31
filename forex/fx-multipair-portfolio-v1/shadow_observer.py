"""Zero-order prospective shadow observer for EURUSD.

Purpose. Every EURUSD candidate in this repository — Codex's V2 included — is
limited by the same thing: its evaluation window is declared *adaptive*, not a
pristine holdout. Replication cannot fix that; only forward time can. This
records the forward data, starting now, so the holdout exists.

What it does each cycle:

* pulls broker ticks read-only and folds them into M15 bid/ask bars;
* appends bars to an append-only Parquet store with a running manifest;
* records the live spread profile, because the frozen contract has a 2.0-pip
  entry guard and spread is what decides whether a signal is executable;
* writes a heartbeat `status.json`.

What it deliberately cannot do. There is no `order_send` anywhere in this file,
and no MT5 trading call is imported. It asserts the account is a demo, refuses
otherwise, writes only inside its own cache directory, and touches no terminal
configuration, chart, profile or preset. Arming the order path is an owner
action performed on the packaged EA, not here.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import MetaTrader5 as mt5  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\shadow")
SYMBOL = "EURUSD"
M15_MS = 900_000
PIP = 0.0001
MAX_SPREAD_PIPS = 2.0  # frozen contract entry guard
POLL_SECONDS = 300

FORBIDDEN_CALLS = frozenset(
    {"order_send", "order_check", "order_calc_margin", "order_calc_profit", "positions_get"}
)


def _assert_no_trading_surface() -> None:
    """Fail loudly if this module ever gains a trading call.

    Parses the AST and looks for *attribute accesses* rather than substrings, so
    the check cannot be tripped by its own documentation or by the name list.
    """
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_CALLS:
            raise RuntimeError(f"trading surface present in shadow observer: {node.attr}")


def m15_from_ticks(ticks: pd.DataFrame) -> pd.DataFrame:
    if ticks.empty:
        return pd.DataFrame()
    stamps = ticks["time_msc"].to_numpy(np.int64)
    slots = stamps - (stamps % M15_MS)
    bid = ticks["bid"].to_numpy(np.float64)
    ask = ticks["ask"].to_numpy(np.float64)
    order = np.argsort(slots, kind="stable")
    slots, bid, ask = slots[order], bid[order], ask[order]
    starts = np.flatnonzero(np.r_[True, slots[1:] != slots[:-1]])
    ends = np.r_[starts[1:] - 1, slots.size - 1]
    spread_pips = (ask - bid) / PIP
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
            "spread_pips_median": [
                float(np.median(spread_pips[s : e + 1])) for s, e in zip(starts, ends)
            ],
            "spread_pips_max": np.maximum.reduceat(spread_pips, starts),
            "tick_count": (ends - starts + 1).astype(np.int32),
        }
    )


def append_store(frame: pd.DataFrame) -> tuple[int, int]:
    path = CACHE / f"{SYMBOL}_M15_SHADOW.parquet"
    if path.is_file():
        existing = pd.read_parquet(path)
        merged = (
            pd.concat([existing, frame], ignore_index=True)
            .drop_duplicates("timestamp_ms", keep="last")
            .sort_values("timestamp_ms", kind="stable", ignore_index=True)
        )
        added = len(merged) - len(existing)
    else:
        merged, added = frame.sort_values("timestamp_ms", ignore_index=True), len(frame)
    merged.to_parquet(path, index=False, compression="zstd")
    return len(merged), added


def cycle() -> dict:
    info = mt5.symbol_info(SYMBOL)
    end = datetime.now(UTC).replace(tzinfo=None)
    start = end - timedelta(hours=6)
    ticks = mt5.copy_ticks_range(SYMBOL, start, end, mt5.COPY_TICKS_INFO)
    if ticks is None or len(ticks) == 0:
        return {"status": "NO_TICKS", "detail": str(mt5.last_error())}
    frame = pd.DataFrame(ticks)
    frame = frame[(frame["bid"] > 0) & (frame["ask"] > 0)]
    bars = m15_from_ticks(frame)
    if bars.empty:
        return {"status": "NO_BARS"}
    total, added = append_store(bars)
    executable = bars["spread_pips_median"] <= MAX_SPREAD_PIPS
    return {
        "status": "OK",
        "ticks_pulled": int(len(frame)),
        "bars_seen": int(len(bars)),
        "bars_added": int(added),
        "bars_total": int(total),
        "latest_bar_utc": datetime.fromtimestamp(
            int(bars["timestamp_ms"].iloc[-1]) / 1000, UTC
        ).isoformat(),
        "spread_pips_median_now": float(bars["spread_pips_median"].iloc[-1]),
        "executable_bar_share_pct": round(100.0 * float(executable.mean()), 2),
        "symbol_spread_points_now": None if info is None else int(info.spread),
    }


def main(once: bool = False) -> int:
    _assert_no_trading_surface()
    CACHE.mkdir(parents=True, exist_ok=True)
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
        started = datetime.now(UTC).isoformat()
        print(f"shadow observer running: {SYMBOL}, account {account.login}, zero orders")
        cycles = 0
        while True:
            result = cycle()
            cycles += 1
            status = {
                "schema_version": "fx_shadow_observer_v1",
                "mode": "ZERO_ORDER_SHADOW_OBSERVATION",
                "broker_action_allowed": False,
                "order_calls_made": 0,
                "symbol": SYMBOL,
                "account_login": account.login,
                "account_server": account.server,
                "started_utc": started,
                "heartbeat_utc": datetime.now(UTC).isoformat(),
                "cycles": cycles,
                "last_cycle": result,
            }
            (CACHE / "status.json").write_text(
                json.dumps(status, indent=2, sort_keys=True), encoding="utf-8"
            )
            print(
                f"[{datetime.now(UTC):%H:%M:%S}] {result.get('status')} "
                f"bars_total={result.get('bars_total')} "
                f"added={result.get('bars_added')} "
                f"spread={result.get('spread_pips_median_now')}",
                flush=True,
            )
            if once:
                return 0
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("stopped")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main(once="--once" in sys.argv))
