"""Balanced long/short portfolio from the corrected search, scored on holdout.

Builds three portfolios from the same qualified pool so the effect of forcing
short representation is visible rather than asserted:

* LONG-ONLY  — what the old pipeline produced by default
* BALANCED   — equal member counts long and short
* ALL        — every qualified member

All are risk-normalised to a common per-trade stop, and all are scored on the
holdout years (2019, 2020, 2021, 2023) which the search never saw, plus the
live broker window as a second untouched feed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import run_corrected_search as CS  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\bars")
ACCOUNT = 10_000.0
PER_SIDE = 10


def pick(pool, direction, limit):
    """Highest-frequency qualified members of one side, diversified."""
    side = [m for m in pool if m["config"]["direction"] == direction]
    side.sort(key=lambda m: -m["qualify"]["trades"])
    out, seen, family_count = [], set(), {}
    for m in side:
        c = m["config"]
        key = (c["family"], c["timeframe"], c["session"], c["rr"])
        if key in seen or family_count.get(c["family"], 0) >= 4:
            continue
        seen.add(key)
        family_count[c["family"]] = family_count.get(c["family"], 0) + 1
        out.append(m)
        if len(out) >= limit:
            break
    return out


def ledger(members, partition):
    frames = []
    for m in members:
        config = tuple(m["config"][k] for k in
                       ("family", "param", "timeframe", "direction", "atr_mult", "rr", "session"))
        trades = CS.simulate_config(config, partition)
        if trades.empty:
            continue
        net = CS.risk_normalised(trades) / len(members)
        frames.append(pd.Series(net, index=pd.to_datetime(trades["exit_ms"], unit="ms", utc=True)))
    return pd.concat(frames).sort_index() if frames else pd.Series(dtype=float)


def score(series, bars, label):
    if series.empty:
        print(f"  {label:26s} no trades")
        return {}
    net = series.to_numpy()
    wins, losses = net[net > 0], net[net <= 0]
    level = float(np.median((bars["bid_close"] + bars["ask_close"]) / 2))
    daily = series.groupby(series.index.strftime("%Y-%m-%d")).sum()
    equity = daily.cumsum()
    drawdown = float((equity.cummax() - equity).max())
    months = series.groupby(series.index.strftime("%Y-%m")).sum()
    active = int(pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
                 .dt.strftime("%Y-%m-%d").nunique())
    result = {
        "trades": int(net.size),
        "per_day": round(net.size / active, 2),
        "win_rate": round(100.0 * wins.size / net.size, 2),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4) if losses.sum() != 0 else None,
        "net_pct": round(float(net.sum()) / level * 100, 2),
        "net_usd": round(float(net.sum()) / level * ACCOUNT, 0),
        "max_dd_pct": round(drawdown / level * 100, 2),
        "months_pos": int((months > 0).sum()), "months": int(months.size),
    }
    print(f"  {label:26s} n={result['trades']:>5} {result['per_day']:>5.2f}/d  "
          f"WR {result['win_rate']:>5.2f}%  PF {result['profit_factor']:>6.3f}  "
          f"net {result['net_pct']:>+7.2f}%  maxDD {result['max_dd_pct']:>5.2f}%  "
          f"+mo {result['months_pos']}/{result['months']}")
    return result


def main() -> int:
    search = json.loads((ROOT / "outputs" / "CORRECTED_SEARCH.json").read_text())
    pool = search["pool"]
    longs, shorts = pick(pool, 1, PER_SIDE), pick(pool, -1, PER_SIDE)
    print(f"pool: {search['qualified_long']} long / {search['qualified_short']} short qualified")
    print(f"selected: {len(longs)} long, {len(shorts)} short\n")
    print("  short members (the ones the old pipeline could not find):")
    for m in shorts:
        c = m["config"]
        print(f"    {c['family']:13s} p{c['param']:<3} tf{c['timeframe']:<4} rr{c['rr']:<5} "
              f"{c['session']:6s} | qualify PF {m['qualify']['profit_factor']:.3f} "
              f"WR {m['qualify']['win_rate']:.1f}% n={m['qualify']['trades']}")

    bars = pd.read_parquet(CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    CS._STATE["blob"] = bars.to_parquet(index=False)
    CS._init(CS._STATE["blob"])

    portfolios = {
        "LONG-ONLY": longs,
        "BALANCED": longs + shorts,
        "ALL QUALIFIED": [
            m for m in pool
            if tuple(m["config"][k] for k in ("family", "timeframe", "session", "rr"))
        ][:60],
    }
    report = {"fixes": search["fixes"], "windows": {}}
    for partition in ("qualify", "holdout"):
        window = CS._STATE["windows"][partition][0]
        print(f"\n=== {partition.upper()} "
              f"{'(2016,2017,2018,2022)' if partition == 'qualify' else '(2019,2020,2021,2023)'} ===")
        report["windows"][partition] = {}
        for name, members in portfolios.items():
            if not members:
                continue
            report["windows"][partition][name] = score(ledger(members, partition), window, name)

    (ROOT / "outputs" / "BALANCED_PORTFOLIO.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"\nwrote {ROOT / 'outputs' / 'BALANCED_PORTFOLIO.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
