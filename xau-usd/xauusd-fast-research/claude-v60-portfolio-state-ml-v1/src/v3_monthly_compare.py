"""Month-by-month side-by-side: V60 as deployed vs the ML sizing overlay.

Both columns are the SAME trades on the SAME dates. The overlay never adds,
removes or reverses a trade - it only changes size - so trade count and win rate
are identical by construction in every row. The whole effect is in the dollars.

Sizing is bagged x40 and averaged over 10 seeds, so the ML column is the central
estimate of the overlay rather than one lucky draw; the per-month seed spread is
reported alongside so the noise is visible rather than hidden.
"""
from __future__ import annotations
import argparse
import numpy as np
import pandas as pd

import features as F
from v3_significance_bagging import load, run

PNL = F.PNL
SEEDS = 10
BAGS = 40


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=12)
    a = ap.parse_args()

    X, meta = load()
    mults = []
    for sd in range(SEEDS):
        mu, _ = run(X, meta, n_bags=BAGS, seed=sd)
        mults.append(mu)
    M = np.vstack(mults)                       # seeds x trades

    k = np.isfinite(M[0])
    m = meta[k].reset_index(drop=True)
    base = m[PNL].values
    sized_all = base[None, :] * M[:, k]        # seeds x trades
    sized = sized_all.mean(axis=0)

    m = m.assign(base=base, sized=sized,
                 month=m.exit_time.dt.strftime("%Y-%m"))
    per_seed_month = pd.DataFrame(
        {f"s{i}": pd.Series(sized_all[i]).groupby(m.month.values).sum()
         for i in range(SEEDS)})

    g = m.groupby("month").agg(n=("base", "size"),
                               base=("base", "sum"),
                               sized=("sized", "sum"),
                               wins=("base", lambda s: int((s > 0).sum())))
    g["sd"] = per_seed_month.std(axis=1)
    g = g.tail(a.months)

    print(f"V60 vs ML sizing overlay - last {len(g)} months "
          f"({g.index[0]} to {g.index[-1]})")
    print("Same trades, same dates, same win rate. Only the size differs.\n")
    print(f"{'month':<9}{'trades':>7}{'WR':>7}{'V60 $':>10}{'ML $':>10}"
          f"{'delta':>9}{'delta%':>8}{'ML sd':>8}")
    print("-" * 68)
    for mo, r in g.iterrows():
        d = r.sized - r.base
        pct = (f"{100 * d / abs(r.base):+.0f}%" if abs(r.base) > 1e-9 else "n/a")
        print(f"{mo:<9}{int(r.n):>7}{100*r.wins/r.n:>6.0f}%{r.base:>10.0f}"
              f"{r.sized:>10.0f}{d:>+9.0f}{pct:>8}{r.sd:>8.0f}")
    print("-" * 68)
    tb, ts = g.base.sum(), g.sized.sum()
    print(f"{'TOTAL':<9}{int(g.n.sum()):>7}{100*g.wins.sum()/g.n.sum():>6.0f}%"
          f"{tb:>10.0f}{ts:>10.0f}{ts-tb:>+9.0f}{100*(ts-tb)/abs(tb):>+7.0f}%")

    print(f"\ngreen months   V60 {int((g.base > 0).sum())}/{len(g)}"
          f"    ML {int((g.sized > 0).sum())}/{len(g)}")
    print(f"best month     V60 ${g.base.max():.0f}   ML ${g.sized.max():.0f}")
    print(f"worst month    V60 ${g.base.min():.0f}   ML ${g.sized.min():.0f}")

    # drawdown over the same window, trade-by-trade in exit order
    w = m[m.month.isin(g.index)].sort_values("exit_time")
    for lab, col in (("V60", "base"), ("ML ", "sized")):
        eq = np.cumsum(w[col].values)
        dd = float((np.maximum.accumulate(eq) - eq).max())
        print(f"{lab} window: net ${eq[-1]:.0f}   maxDD ${dd:.0f}   "
              f"net/DD {eq[-1]/max(dd,1):.2f}")


if __name__ == "__main__":
    main()
