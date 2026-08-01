"""Month-by-month backtest of the best mega-search survivor.

Two windows, both reported:

* **2023** — the most recent 12 months inside the search's own holdout.
* **2025-08 → 2026-07** — the most recent 12 months of *live broker* quotes,
  which the search never touched at all. This is the harder and more honest
  test: the strategy was selected on Dukascopy 2016–2023 and has never seen
  this data or this feed.

The caveat travels with the numbers: this is the best of 14,400 attempts, and
the same pipeline run on sign-flipped noise produced 29 survivors with a *higher*
median holdout profit factor (1.283 vs 1.190). Being best-of-14,400 is not
evidence of edge. This report exists so the candidate can be inspected, not
because it is recommended.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.engine import CostModel, RunConfig, Signals, SymbolSpec, simulate  # noqa: E402
from src.report import slice_window  # noqa: E402
from src.search_families import _session_mask, prepare, signals_for, timeframe_frame  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\bars")
POINT = 0.1
CONFIG = json.loads((ROOT / "outputs" / "_best_config.json").read_text())["config"]


def run(bars: pd.DataFrame) -> pd.DataFrame:
    data = prepare(
        timeframe_frame(bars, CONFIG["timeframe"]), bars["timestamp_ms"].to_numpy()
    )
    trigger = signals_for(CONFIG["family"], data, CONFIG["param"], CONFIG["direction"])
    trigger &= _session_mask(data, CONFIG["session"])
    execution = data["execution"]
    keep = trigger & (execution >= 0) & np.isfinite(data["atr"])
    picked = np.flatnonzero(keep)
    if picked.size == 0:
        return pd.DataFrame()

    stop_points = np.maximum(data["atr"][picked] * CONFIG["atr_mult"] / POINT, 30.0)
    signals = Signals(
        entry_index=execution[picked],
        direction=np.full(picked.size, CONFIG["direction"], dtype=np.int64),
        stop_min_points=stop_points,
        stop_atr_points=np.zeros(picked.size),
        stop_ref_price=np.full(picked.size, np.nan),
        rr=np.full(picked.size, CONFIG["rr"]),
        stop_cap_points=np.full(picked.size, 5000.0),
    )
    return simulate(
        bars, signals, SymbolSpec.of("US500"),
        CostModel(slippage_points=2.0, stop_slippage_points=2.0),
        RunConfig(lot=1.0, max_hold_bars=288 * 10, max_entries_per_day=3),
    )


def monthly(trades: pd.DataFrame, level: float, label: str) -> dict:
    if trades.empty:
        print(f"{label}: no trades")
        return {}
    stamps = pd.to_datetime(trades["exit_ms"], unit="ms", utc=True)
    trades = trades.assign(month=stamps.dt.strftime("%Y-%m"))
    months = sorted(trades["month"].unique())[-12:]
    trades = trades[trades["month"].isin(months)]

    print(f"\n{label}")
    print(f"  1 index point = $1.00 per 1.0 lot; '%' is of the index level (~{level:,.0f})\n")
    header = (f"  {'month':8s} {'trades':>7} {'wins':>5} {'loss':>5} {'win%':>6} "
              f"{'net$':>9} {'net%':>7} {'PF':>6} {'avgW$':>7} {'avgL$':>7}")
    print(header); print("  " + "-" * (len(header) - 2))
    for month in months:
        block = trades[trades["month"] == month]
        net = block["net_usd"].to_numpy()
        wins, losses = net[net > 0], net[net <= 0]
        pf = wins.sum() / -losses.sum() if losses.sum() != 0 else float("nan")
        print(f"  {month:8s} {net.size:>7} {wins.size:>5} {losses.size:>5} "
              f"{100 * wins.size / net.size:>5.1f}% {net.sum():>+9.1f} "
              f"{net.sum() / level * 100:>+6.2f}% {pf:>6.2f} "
              f"{(wins.mean() if wins.size else 0):>7.1f} {(losses.mean() if losses.size else 0):>7.1f}")

    net = trades["net_usd"].to_numpy()
    wins, losses = net[net > 0], net[net <= 0]
    equity = np.cumsum(net)
    drawdown = float(np.max(np.maximum.accumulate(equity) - equity))
    by_month = trades.groupby("month")["net_usd"].sum()
    print("  " + "-" * (len(header) - 2))
    print(f"  {'TOTAL':8s} {net.size:>7} {wins.size:>5} {losses.size:>5} "
          f"{100 * wins.size / net.size:>5.1f}% {net.sum():>+9.1f} "
          f"{net.sum() / level * 100:>+6.2f}% {wins.sum() / -losses.sum():>6.2f}")
    result = {
        "trades": int(net.size),
        "win_rate_pct": round(100.0 * wins.size / net.size, 2),
        "net_usd": round(float(net.sum()), 2),
        "net_pct_of_index": round(float(net.sum()) / level * 100, 2),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4),
        "max_drawdown_usd": round(drawdown, 2),
        "max_drawdown_pct": round(drawdown / level * 100, 2),
        "positive_months": int((by_month > 0).sum()),
        "months": int(by_month.size),
        "avg_win_usd": round(float(wins.mean()), 2),
        "avg_loss_usd": round(float(losses.mean()), 2),
    }
    print(f"\n  win rate {result['win_rate_pct']}%   PF {result['profit_factor']}   "
          f"net {result['net_pct_of_index']:+.2f}%   maxDD {result['max_drawdown_pct']:.2f}%   "
          f"positive months {result['positive_months']}/{result['months']}")
    return result


def main() -> int:
    print("BEST OF 14,400 ATTEMPTS")
    print(f"  {CONFIG['family']} lookback {CONFIG['param']}, H{CONFIG['timeframe'] // 60} bars, "
          f"long only, stop {CONFIG['atr_mult']}xATR, target {CONFIG['rr']}R, "
          f"{CONFIG['session']} session")

    report = {"config": CONFIG, "windows": {}}

    duka = pd.read_parquet(CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    window = slice_window(duka, "2023-01-01", "2024-01-01").reset_index(drop=True)
    level = float(np.median((window["bid_close"] + window["ask_close"]) / 2))
    report["windows"]["2023_search_holdout"] = monthly(
        run(window), level, "A) 2023 — last 12 months inside the search's own holdout"
    )

    broker = pd.read_parquet(CACHE / "US500_M5_BIDASK_BROKER.parquet")
    level = float(np.median((broker["bid_close"] + broker["ask_close"]) / 2))
    report["windows"]["broker_untouched"] = monthly(
        run(broker), level,
        "B) 2025-08 -> 2026-07 — live broker quotes, NEVER touched by the search"
    )

    (ROOT / "outputs" / "BEST_STRATEGY_12M.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    print(f"\nwrote {ROOT / 'outputs' / 'BEST_STRATEGY_12M.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
