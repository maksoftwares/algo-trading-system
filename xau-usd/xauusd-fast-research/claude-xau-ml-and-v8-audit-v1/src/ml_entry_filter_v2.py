"""Does an ML entry filter add anything ON TOP of the deployed V6 book?

The previous attempt (ML_FILTER_FINDINGS.md) was refuted for a specific reason:
it was benchmarked against the frozen ranker ALONE (+0.202R on the raw
population) instead of against the real incumbent - the full family with its
ranker, macro filter, dip gates and session specialisation (+0.531R). Measured
correctly it lost at every cutoff.

So this asks the only question that matters for deployment: take the trades V6
ACTUALLY TAKES, and see whether a model can identify which of them to skip.

Design:
  * train on the full confirmed-setup population (more data than the selected
    book) using only trades that CLOSED on or before 2024-12-31
  * apply to the V6 selected book, drop the worst X% by predicted outcome
  * benchmark = the same book unfiltered, on the same dollar series
  * report the sealed era (2025-01 onward) separately - it decides

Preregistered before running: the filter must improve BOTH profit factor and
total P&L on the sealed era at a cutoff chosen from the fit era. Improving one
while degrading the other is a fail; so is needing a sealed-era cutoff to work.
"""
import argparse
import numpy as np, pandas as pd
import engine, specialist, v6_fix as V

FIT_END = pd.Timestamp("2024-12-31 23:59:59", tz="UTC")
HOLD = engine.HOLDOUT_START
FEATS = ["speed", "flow", "imb", "activity", "spr", "eff", "adv_pre", "align"]


def ridge(X, y, lam=5.0):
    Xs = np.column_stack([np.ones(len(X)), X])
    A = Xs.T @ Xs + lam * np.eye(Xs.shape[1]); A[0, 0] -= lam
    return np.linalg.solve(A, Xs.T @ y)


def outcome(u, C):
    """Realised R for every candidate under V6 mechanics."""
    bl, bc, ao, ah, ac, bo = C["bl"], C["bc"], C["ao"], C["ah"], C["ac"], C["bo"]
    out = []
    for r in u.itertuples():
        j, i1, long, stop = int(r.j), int(r.i1), bool(r.long), float(r.stop)
        if long:
            fill = ao[j]; slv = fill - stop
            hit = np.flatnonzero(bl[j:i1] <= slv)
            xi = j + hit[0] if len(hit) else i1 - 1
            xp = slv if len(hit) else bc[xi]
            out.append((xp - fill) / stop - engine.FEE / stop)
        else:
            fill = bo[j]; slv = fill + stop
            hit = np.flatnonzero(ah[j:i1] >= slv)
            xi = j + hit[0] if len(hit) else i1 - 1
            xp = slv if len(hit) else ac[xi]
            out.append((fill - xp) / stop - engine.FEE / stop)
    return np.array(out)


def stats(d, col="usd"):
    if not len(d):
        return None
    w, l = d[d[col] > 0], d[d[col] <= 0]
    eq = d.sort_values("exit_t")[col].cumsum()
    return dict(n=len(d), wr=round(100 * len(w) / len(d), 1),
                pf=round(float(w[col].sum() / max(-l[col].sum(), 1e-9)), 3),
                usd=round(float(d[col].sum())),
                dd=round(float((eq.cummax() - eq).max())))


def main():
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    C = specialist.load_context()
    cands, fam = V.scored_candidates()

    # training population: every confirmed setup that passed the gates, deduped
    pop = pd.concat(cands.values()).reset_index(drop=True)
    pop = pop.sort_values(["i", "score"], ascending=[True, False]).groupby(
        "i", as_index=False).first()
    pop["r"] = outcome(pop, C)
    fit = pop[pop.dec_time <= FIT_END]
    print(f"training population {len(pop):,} deduped setups, "
          f"{len(fit):,} in the fit era")

    X = pop[FEATS].values.astype(float)
    mu, sd = X[(pop.dec_time <= FIT_END).values].mean(0), \
             X[(pop.dec_time <= FIT_END).values].std(0) + 1e-9
    Z = (X - mu) / sd
    m = (pop.dec_time <= FIT_END).values
    w = ridge(Z[m], pop.r.values[m])
    pop["ml"] = w[0] + Z @ w[1:]
    print(f"ridge on {FEATS}\n  weights " +
          "  ".join(f"{f}{v:+.3f}" for f, v in zip(FEATS, w[1:])))

    # the incumbent: the V6 book exactly as it runs
    frozen = pd.concat([V.select(c, "frozen") for c in cands.values()]).reset_index(drop=True)
    bk = V.book(V.execute(frozen, C), 2, False, False)
    bk = bk.merge(pop[["i", "ml"]], on="i", how="left").dropna(subset=["ml"])
    bk["usd"] = bk.rc * bk.stop_usd
    bk = bk.dropna(subset=["usd"])
    print(f"\nincumbent V6 book: {len(bk)} trades with an ML score")

    fitb = bk[bk.exit_t <= FIT_END]
    selb = bk[bk.cap_exit_t >= HOLD]
    print(f"  fit era {len(fitb)}   sealed {len(selb)}\n")

    print("=== DROP THE WORST X% OF THE V6 BOOK BY ML SCORE ===")
    print(f"{'cutoff':<10}{'FIT n':>7}{'PF':>8}{'USD':>9}   {'SEALED n':>9}{'PF':>8}{'USD':>9}{'maxDD':>8}")
    base_f, base_s = stats(fitb), stats(selb)
    print(f"{'none':<10}{base_f['n']:>7}{base_f['pf']:>8}{base_f['usd']:>9}   "
          f"{base_s['n']:>9}{base_s['pf']:>8}{base_s['usd']:>9}{base_s['dd']:>8}")
    for q in (5, 10, 15, 20, 25, 30, 40):
        thr = np.percentile(fitb.ml.values, q)      # cutoff from the FIT era only
        f_ = stats(fitb[fitb.ml >= thr]); s_ = stats(selb[selb.ml >= thr])
        if not f_ or not s_:
            continue
        print(f"drop {q:>2}%   {f_['n']:>7}{f_['pf']:>8}{f_['usd']:>9}   "
              f"{s_['n']:>9}{s_['pf']:>8}{s_['usd']:>9}{s_['dd']:>8}")

    print("\n=== VERDICT ===")
    best = None
    for q in (5, 10, 15, 20, 25, 30, 40):
        thr = np.percentile(fitb.ml.values, q)
        f_ = stats(fitb[fitb.ml >= thr])
        if f_ and (best is None or f_["pf"] > best[1]["pf"]):
            best = (q, f_, thr)
    q, f_, thr = best
    s_ = stats(selb[selb.ml >= thr])
    print(f"  best cutoff on the FIT era: drop {q}%  (fit PF {f_['pf']} vs {base_f['pf']})")
    print(f"  that same cutoff on the SEALED era: PF {s_['pf']} vs {base_s['pf']},"
          f"  ${s_['usd']} vs ${base_s['usd']}")
    ok = s_["pf"] > base_s["pf"] and s_["usd"] > base_s["usd"]
    print(f"  {'PASS - improves both PF and P&L out of sample' if ok else 'FAIL - does not improve both out of sample'}")


if __name__ == "__main__":
    main()
