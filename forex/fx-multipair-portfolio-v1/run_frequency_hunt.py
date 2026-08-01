"""Frequency hunt: build a portfolio reaching >=1 trade per active trading day.

The best single strategy from the mega-search trades 30 times a year. The target
is ~252. Three levers, in order of how much they risk the edge:

1. **Portfolio breadth** — combine many independently-qualified configurations.
   Adds frequency without loosening any single rule. Safest.
2. **Lower timeframes** — M15/M30 fire far more often than H4. Costs edge only
   if the effect is horizon-specific (U4 found it was, for daily reversal).
3. **Looser entries** — deliberately NOT used. That is fitting, not frequency.

This records every configuration's trades-per-day alongside its economics, then
greedily assembles a portfolio that maximises frequency subject to each member
independently clearing the design and validation gates.

Guardrail: members are qualified on design+validation only. The holdout and the
broker window are scored once, at the end, by report_frequency_portfolio.py.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import run_mega_search as MS  # noqa: E402

TRADING_DAYS = {"design": 4 * 252, "validation": 2 * 252, "holdout": 2 * 252}
MIN_PF_DESIGN = 1.10
MIN_PF_VALID = 1.05
MIN_TRADES = 60
TARGET_PER_DAY = 1.0


def _work(args):
    config, partition = args
    return config, partition, MS.evaluate(config, partition)


def run_all(configs, partition, workers):
    results = {}
    began, done = time.time(), 0
    with ProcessPoolExecutor(
        max_workers=workers, initializer=MS._init,
        initargs=(MS._STATE["blob"], False),
    ) as pool:
        futures = [pool.submit(_work, (c, partition)) for c in configs]
        for future in as_completed(futures):
            config, _, result = future.result()
            results[config] = result
            done += 1
            if done % 3000 == 0 or done == len(configs):
                print(f"    {partition} {done:,}/{len(configs):,} "
                      f"({done / max(time.time() - began, 1e-9):.0f}/s)", flush=True)
    return results


def main() -> int:
    workers = min(14, os.cpu_count() or 4)
    bars = pd.read_parquet(MS.CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    MS._STATE["blob"] = bars.to_parquet(index=False)
    MS._STATE["null"] = False
    configs = MS.build_configs()
    print(f"evaluating {len(configs):,} configs for FREQUENCY + edge\n")

    design = run_all(configs, "design", workers)
    freq = [
        (c, r["trades"] / TRADING_DAYS["design"], r)
        for c, r in design.items() if r.get("trades", 0) > 0
    ]
    freq.sort(key=lambda x: -x[1])
    print("\n  highest-frequency configs on design (any quality):")
    for c, f, r in freq[:6]:
        print(f"    {f:5.2f}/day  {c[0]:13s} p{c[1]:<3} tf{c[2]:<4} dir{c[3]:>2} "
              f"rr{c[5]:<4} {c[6]:6s}  PF {r.get('profit_factor')}  n={r['trades']}")

    eligible = [
        c for c, r in design.items()
        if r.get("trades", 0) >= MIN_TRADES
        and r.get("profit_factor") is not None
        and r["profit_factor"] >= MIN_PF_DESIGN
        and r.get("net", 0) > 0
    ]
    print(f"\n  {len(eligible):,} configs clear design (PF>={MIN_PF_DESIGN}, n>={MIN_TRADES})")

    validation = run_all(eligible, "validation", workers)
    qualified = [
        c for c in eligible
        if validation[c].get("trades", 0) >= 20
        and validation[c].get("profit_factor") is not None
        and validation[c]["profit_factor"] >= MIN_PF_VALID
    ]
    print(f"  {len(qualified):,} also clear validation (PF>={MIN_PF_VALID})\n")
    if not qualified:
        print("no qualified members - cannot build a portfolio")
        return 1

    qualified.sort(key=lambda c: -design[c]["trades"])
    members, seen, rate = [], set(), 0.0
    for c in qualified:
        key = (c[0], c[2], c[3], c[6])          # family, timeframe, direction, session
        if key in seen:
            continue
        seen.add(key)
        members.append(c)
        rate += design[c]["trades"] / TRADING_DAYS["design"]
        if rate >= TARGET_PER_DAY * 1.2:
            break

    print(f"  portfolio: {len(members)} members, design rate {rate:.2f} trades/day")
    for c in members:
        d, v = design[c], validation[c]
        print(f"    {c[0]:13s} p{c[1]:<3} tf{c[2]:<4} dir{c[3]:>2} atr{c[4]} rr{c[5]:<4} "
              f"{c[6]:6s} | design PF {d['profit_factor']:.3f} n={d['trades']:<4} "
              f"{d['trades'] / TRADING_DAYS['design']:.2f}/d | valid PF {v['profit_factor']:.3f}")

    payload = {
        "schema_version": "frequency_hunt_v1",
        "target_trades_per_day": TARGET_PER_DAY,
        "gates": {"design_pf": MIN_PF_DESIGN, "validation_pf": MIN_PF_VALID, "min_trades": MIN_TRADES},
        "eligible_after_design": len(eligible),
        "qualified_after_validation": len(qualified),
        "members": [
            {
                "config": dict(zip(
                    ("family", "param", "timeframe", "direction", "atr_mult", "rr", "session"), c)),
                "design": design[c], "validation": validation[c],
                "design_trades_per_day": round(design[c]["trades"] / TRADING_DAYS["design"], 3),
            }
            for c in members
        ],
        "portfolio_design_rate": round(rate, 3),
        "qualified_pool": [
            {
                "config": dict(zip(
                    ("family", "param", "timeframe", "direction", "atr_mult", "rr", "session"), c)),
                "design": design[c], "validation": validation[c],
                "design_trades_per_day": round(design[c]["trades"] / TRADING_DAYS["design"], 3),
            }
            for c in qualified
        ],
    }
    out = ROOT / "outputs" / "FREQUENCY_PORTFOLIO.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
