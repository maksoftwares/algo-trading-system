"""High-win-rate portfolio: target ~60% wins, accepting lower frequency.

Two levers, applied in the order that risks least:

1. **Target selection.** Win rate is mostly set by the reward:risk target, not by
   trade quality. The qualified pool's rr=0.75 members already show a median 60.2%
   design win rate at PF 1.206 — better than the 33.5% / 1.112 wide-target
   portfolio. This is a structural choice, not a fit.
2. **Entry-quality filter.** An optional overlay that keeps only setups whose
   pre-trade conditions resemble past winners. Fitted on **design trades only**,
   using features knowable before entry, then applied unchanged elsewhere.

The known danger, recorded in this repo: on the XAUUSD V60 lane the worst score
quintiles turned out to be near-zero winners, so every veto raised PF and lowered
net — filtering removed profit, not risk. The filter here is therefore judged on
whether it raises win rate *without* cutting net return, and is dropped if it
does not.

Cost sensitivity matters more at low targets: at rr=0.75 breakeven is a 57.1%
win rate, so a 60% result has only ~3 points of margin. Every window is
re-scored at 2x cost.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from report_frequency_portfolio import trades_for  # noqa: E402
from src.report import slice_window  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\bars")
MAX_RR = 1.0          # only low-target members
MAX_MEMBERS = 30      # more members needed: each fires less often
MIN_DESIGN_WR = 55.0  # selected on design only
ACCOUNT = 10_000.0


def select(pool: list[dict]) -> list[dict]:
    candidates = [
        m for m in pool
        if m["config"]["rr"] <= MAX_RR and m["design"].get("win_rate", 0) >= MIN_DESIGN_WR
    ]
    candidates.sort(key=lambda m: -m["design"]["trades"])
    members, seen, family_count = [], set(), {}
    for m in candidates:
        c = m["config"]
        key = (c["family"], c["timeframe"], c["direction"], c["session"], c["rr"])
        if key in seen or family_count.get(c["family"], 0) >= 6:
            continue
        seen.add(key)
        family_count[c["family"]] = family_count.get(c["family"], 0) + 1
        members.append(m)
        if len(members) >= MAX_MEMBERS:
            break
    return members


def portfolio_trades(members, bars) -> pd.DataFrame:
    frames = []
    for m in members:
        t = trades_for(m["config"], bars)
        if t.empty:
            continue
        frames.append(
            pd.DataFrame({
                "ts": pd.to_datetime(t["exit_ms"], unit="ms", utc=True),
                "net": t["net_usd"].to_numpy() / len(members),
                "stop_points": t["stop_points"].to_numpy(),
                "lot_net": t["net_usd"].to_numpy(),
            })
        )
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames).sort_values("ts").reset_index(drop=True)


def score(trades: pd.DataFrame, bars: pd.DataFrame, label: str, cost_mult: float = 1.0) -> dict:
    if trades.empty:
        print(f"  {label}: no trades")
        return {}
    net = trades["net"].to_numpy()
    if cost_mult != 1.0:
        # Extra round-trip cost per trade. Measured US500 spread is ~6 points at
        # 0.1 per point; the 1/N risk split is already applied to `net`, so the
        # increment is divided the same way.
        members = max(int(round(trades["lot_net"].to_numpy()[0] / net[0])), 1) if net[0] else 1
        extra_index_points = 6.0 * (cost_mult - 1.0) * 0.1
        net = net - extra_index_points / members
    wins, losses = net[net > 0], net[net <= 0]
    level = float(np.median((bars["bid_close"] + bars["ask_close"]) / 2))
    daily = pd.Series(net, index=trades["ts"]).groupby(
        trades["ts"].dt.strftime("%Y-%m-%d").to_numpy()).sum()
    equity = daily.cumsum()
    drawdown = float((equity.cummax() - equity).max())
    months = pd.Series(net, index=trades["ts"]).groupby(
        trades["ts"].dt.strftime("%Y-%m").to_numpy()).sum()
    active = int(pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
                 .dt.strftime("%Y-%m-%d").nunique())
    result = {
        "trades": int(net.size),
        "trades_per_active_day": round(net.size / active, 2),
        "win_rate_pct": round(100.0 * wins.size / net.size, 2),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4) if losses.sum() != 0 else None,
        "net_pct": round(float(net.sum()) / level * 100, 2),
        "net_usd_on_account": round(float(net.sum()) / level * ACCOUNT, 0),
        "max_drawdown_pct": round(drawdown / level * 100, 2),
        "months_positive": int((months > 0).sum()),
        "months": int(months.size),
        "payoff": round(abs(wins.mean() / losses.mean()), 2) if losses.size else None,
    }
    print(
        f"  {label:34s} n={result['trades']:>5} {result['trades_per_active_day']:>5.2f}/d "
        f"WR {result['win_rate_pct']:>5.2f}%  PF {result['profit_factor']:>6.3f}  "
        f"net {result['net_pct']:>+7.2f}%  maxDD {result['max_drawdown_pct']:>5.2f}%  "
        f"+mo {result['months_positive']}/{result['months']}"
    )
    return result


def main() -> int:
    hunt = json.loads((ROOT / "outputs" / "FREQUENCY_PORTFOLIO.json").read_text())
    members = select(hunt["qualified_pool"])
    print(f"HIGH-WIN-RATE PORTFOLIO: {len(members)} members (rr<={MAX_RR}, "
          f"design WR>={MIN_DESIGN_WR}%)\n")
    for m in members[:12]:
        c = m["config"]
        print(f"  {c['family']:13s} p{c['param']:<3} tf{c['timeframe']:<4} rr{c['rr']:<5} "
              f"{c['session']:6s} | design WR {m['design']['win_rate']:.1f}% "
              f"PF {m['design']['profit_factor']:.3f}")
    if len(members) > 12:
        print(f"  ... and {len(members) - 12} more")
    print()

    duka = pd.read_parquet(CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    broker = pd.read_parquet(CACHE / "US500_M5_BIDASK_BROKER.parquet")
    windows = {
        "design 2016-2019": slice_window(duka, "2016-01-01", "2020-01-01").reset_index(drop=True),
        "validation 2020-2021": slice_window(duka, "2020-01-01", "2022-01-01").reset_index(drop=True),
        "HOLDOUT 2022-2023": slice_window(duka, "2022-01-01", "2024-01-01").reset_index(drop=True),
        "BROKER 2025-08..2026-07": broker,
    }
    report = {"members": [m["config"] for m in members], "windows": {}, "cost_stress": {}}
    ledgers = {}
    for label, bars in windows.items():
        trades = portfolio_trades(members, bars)
        ledgers[label] = (trades, bars)
        report["windows"][label] = score(trades, bars, label)

    print("\n  2x cost stress (breakeven at rr=0.75 is a 57.1% win rate):")
    for label, (trades, bars) in ledgers.items():
        report["cost_stress"][label] = score(trades, bars, f"  {label}", cost_mult=2.0)

    (ROOT / "outputs" / "HIGHWR_PORTFOLIO.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    # monthly detail for the most recent broker year
    trades, bars = ledgers["BROKER 2025-08..2026-07"]
    if not trades.empty:
        level = float(np.median((bars["bid_close"] + bars["ask_close"]) / 2))
        trades = trades.assign(month=trades["ts"].dt.strftime("%Y-%m"))
        months = sorted(trades["month"].unique())[-12:]
        print(f"\n  LAST 12 MONTHS (broker quotes, ${ACCOUNT:,.0f} account)\n")
        print(f"  {'month':8s} {'trades':>7} {'wins':>5} {'loss':>5} {'win%':>6} {'PF':>6} {'net$':>9}")
        print("  " + "-" * 54)
        for month in months:
            block = trades[trades["month"] == month]["net"].to_numpy()
            wins, losses = block[block > 0], block[block <= 0]
            pf = wins.sum() / -losses.sum() if losses.sum() != 0 else float("nan")
            print(f"  {month:8s} {block.size:>7} {wins.size:>5} {losses.size:>5} "
                  f"{100 * wins.size / block.size:>5.1f}% {pf:>6.2f} "
                  f"{block.sum() / level * ACCOUNT:>+9.0f}")
    print(f"\nwrote {ROOT / 'outputs' / 'HIGHWR_PORTFOLIO.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
