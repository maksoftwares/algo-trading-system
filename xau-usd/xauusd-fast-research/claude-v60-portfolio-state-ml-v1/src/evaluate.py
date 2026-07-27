"""Evaluate the walk-forward policies against ALL FOUR preregistered gates.

The first pass compared policies on 1,713 scored trades against a baseline on
2,019 trades - different denominators, so the comparison was not valid. This
restricts every variant, the baseline, and the trivial benchmark to the SAME
scored trade set, then applies all four gates:

  1. net P&L must not fall
  2. net/maxDD must improve
  3. green-month share must not fall by more than 2 points
  4. the effect must hold in at least 5 of the 8 walk-forward years

Gate 4 is the one that has killed every prior positive in this repository, so it
is applied here rather than left as a footnote.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import features as F

PNL = F.PNL
DEAD = ["V8_DUKASCOPY_RAW_TICK", "V25_DUKASCOPY_RAW_TICK"]


def stats(pnl, exit_t, sizes=None):
    p = np.asarray(pnl, float)
    if sizes is not None:
        p = p * np.asarray(sizes, float)
    o = np.argsort(np.asarray(exit_t))
    p, xt = p[o], np.asarray(exit_t)[o]
    eq = np.cumsum(p)
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else 1.0
    w, l = p[p > 0], p[p <= 0]
    m = pd.Series(p).groupby(pd.to_datetime(pd.Series(xt)).dt.strftime("%Y-%m").values).sum()
    return dict(n=len(p), pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 3),
                net=round(float(p.sum()), 2), dd=round(max(dd, 1e-9), 2),
                ratio=round(float(p.sum() / max(dd, 1e-9)), 2),
                green=int((m > 0).sum()), months=int(len(m)),
                green_pct=round(100 * float((m > 0).mean()), 1))


def yearly_net(pnl, exit_t, years, sizes=None):
    p = np.asarray(pnl, float)
    if sizes is not None:
        p = p * np.asarray(sizes, float)
    y = pd.to_datetime(pd.Series(np.asarray(exit_t))).dt.year.values
    return {int(yy): float(p[y == yy].sum()) for yy in years}


def main():
    X = pd.read_parquet("outputs/V60_ML_FEATURES.parquet")
    meta = pd.read_parquet("outputs/V60_ML_META.parquet")
    meta["entry_time"] = pd.to_datetime(meta.entry_time, utc=True)
    meta["exit_time"] = pd.to_datetime(meta.exit_time, utc=True)
    o = np.argsort(meta.entry_time.values)
    meta = meta.iloc[o].reset_index(drop=True)
    S = np.load("outputs/V60_ML_SCORES.npy")            # T1, T2, T3
    names = ["T1", "T2", "T3"]

    scored = np.isfinite(S).all(axis=0)                 # the common evaluable set
    m = meta[scored].reset_index(drop=True)
    Ssc = S[:, scored]
    pnl, xt = m[PNL].values, m.exit_time.values
    years = sorted(m.exit_time.dt.year.unique())

    base = stats(pnl, xt)
    base_y = yearly_net(pnl, xt, years)
    keep_dead = ~m.source_id.isin(DEAD).values
    triv = stats(pnl[keep_dead], xt[keep_dead])

    print(f"common scored set: {scored.sum()} trades, "
          f"{m.exit_time.min():%Y-%m} -> {m.exit_time.max():%Y-%m}\n")
    print(f"{'reference':<26}{'n':>6}{'PF':>7}{'net':>10}{'maxDD':>9}{'net/DD':>8}{'green':>11}")
    print(f"{'V60 baseline':<26}{base['n']:>6}{base['pf']:>7}{base['net']:>10}"
          f"{base['dd']:>9}{base['ratio']:>8}{str(base['green'])+'/'+str(base['months']):>11}")
    print(f"{'trivial: drop V8+V25':<26}{triv['n']:>6}{triv['pf']:>7}{triv['net']:>10}"
          f"{triv['dd']:>9}{triv['ratio']:>8}{str(triv['green'])+'/'+str(triv['months']):>11}")
    bar = max(base["ratio"], triv["ratio"])
    print(f"\nbar: net >= ${base['net']}, net/DD > {bar}, "
          f"green >= {base['green_pct']-2}%, >=5 of {len(years)} years improved\n")

    print(f"{'target':<5}{'policy':<20}{'n':>6}{'PF':>7}{'net':>10}{'maxDD':>9}"
          f"{'net/DD':>8}{'green%':>8}{'yrs+':>6}  gates")
    rows = []
    for i, t in enumerate(names):
        s = Ssc[i]
        for q in (5, 10, 20, 30):
            k = s >= np.percentile(s, q)
            st = stats(pnl[k], xt[k])
            yv = yearly_net(pnl[k], xt[k], years)
            yrs = sum(1 for y in years if yv.get(y, 0) >= base_y.get(y, 0))
            g = [st["net"] >= base["net"], st["ratio"] > bar,
                 st["green_pct"] >= base["green_pct"] - 2, yrs >= 5]
            rows.append((t, f"veto worst {q}%", st, yrs, all(g)))
        r = pd.Series(s).rank(pct=True).values
        for lo, hi, lab in ((0.5, 1.5, "size 0.5-1.5x"), (0.25, 1.75, "size 0.25-1.75x")):
            sz = lo + r * (hi - lo)
            sz = sz / sz.mean()
            st = stats(pnl, xt, sz)
            yv = yearly_net(pnl, xt, years, sz)
            yrs = sum(1 for y in years if yv.get(y, 0) >= base_y.get(y, 0))
            g = [st["net"] >= base["net"], st["ratio"] > bar,
                 st["green_pct"] >= base["green_pct"] - 2, yrs >= 5]
            rows.append((t, lab, st, yrs, all(g)))

    for t, lab, st, yrs, ok in rows:
        print(f"{t:<5}{lab:<20}{st['n']:>6}{st['pf']:>7}{st['net']:>10}{st['dd']:>9}"
              f"{st['ratio']:>8}{st['green_pct']:>8}{yrs:>4}/{len(years)}  "
              f"{'PASS' if ok else ''}")

    winners = [(t, lab, st, yrs) for t, lab, st, yrs, ok in rows if ok]
    print(f"\n{len(winners)} of {len(rows)} policies pass ALL FOUR gates")
    if winners:
        for t, lab, st, yrs in sorted(winners, key=lambda x: -x[2]["ratio"]):
            print(f"  {t} {lab}: net ${st['net']} (base ${base['net']}), "
                  f"net/DD {st['ratio']} (bar {bar}), green {st['green_pct']}%, "
                  f"{yrs}/{len(years)} years")
    else:
        print("  -> no policy improves V60 once all four gates are applied")


if __name__ == "__main__":
    main()
