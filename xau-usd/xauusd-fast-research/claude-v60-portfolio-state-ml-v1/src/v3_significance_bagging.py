"""V3: is gate 4 detecting a real failure, or estimator noise? And can bagging fix it?

Two questions the first 32 configurations never asked.

QUESTION 1 - IS THE FAILURE REAL?
Gate 4 counts the SIGN of each year's delta with no tolerance. At the narrow band
2021 fails on a delta of -$1 against a $258 base year. A -$1 delta and a -$96
delta fail the gate identically. Before accepting "the overlay loses money in
2021 and 2022", that has to be tested against the null that the model's ranking
carries no information in those years.

The delta decomposes exactly (see RESULT.md):

    delta_year = width x SUM_i ( pnl_i x (rank_i - mean_rank) )

so the null "rank is independent of pnl in this year" is testable directly by
permuting the ranks within the year. This is a MEASUREMENT of an already-fixed
result, not a search for a better one: the gates do not move, and a year that
fails still fails. It only establishes whether the failure is signal or noise.

QUESTION 2 - CAN A BETTER RANKING FIX IT?
The algebra says band width cannot change a year's sign; only the ranking can.
A single HistGradientBoostingRegressor fitted on ~400 trades (2021) is a
high-variance estimator, so part of that per-year covariance is estimation noise
rather than a real inversion. The standard fix for estimator variance is bagging:
fit many models on bootstrap resamples of the training window and average their
RANKS. Note that varying `random_state` alone would not work here - with these
sample sizes sklearn's early stopping is off and the binning subsample never
triggers, so the seeds return identical models. The diversity has to come from
resampling the training rows.

This is one pre-specified idea with a stated mechanism, not a sweep. It is
reported whichever way it comes out.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import features as F

PNL = F.PNL
PURGE = pd.Timedelta(hours=48)
N_REF = 1500
BAR = 17.91
PARAMS = dict(max_depth=3, max_iter=200, learning_rate=0.05,
              min_samples_leaf=40, l2_regularization=1.0, random_state=0)


def load():
    X = pd.read_parquet("outputs/V60_ML_FEATURES.parquet")
    meta = pd.read_parquet("outputs/V60_ML_META.parquet")
    meta["entry_time"] = pd.to_datetime(meta.entry_time, utc=True)
    meta["exit_time"] = pd.to_datetime(meta.exit_time, utc=True)
    o = np.argsort(meta.entry_time.values)
    X, meta = X.iloc[o].reset_index(drop=True), meta.iloc[o].reset_index(drop=True)
    MK = [c for c in X.columns if c not in F.PORTFOLIO]
    return X[MK], meta


def run(X, meta, n_bags=1, band=(0.5, 1.5), use_shrink=True, seed=0):
    """n_bags=1 reproduces V1/V2 exactly (fit on the full training window)."""
    rng = np.random.default_rng(seed)
    mult = np.full(len(X), np.nan)
    rankv = np.full(len(X), np.nan)
    for y in range(2021, int(meta.entry_time.dt.year.max()) + 1):
        cut = pd.Timestamp(f"{y}-01-01", tz="UTC") - PURGE
        tr = (meta.exit_time < cut).values
        te = (meta.entry_time.dt.year == y).values
        if tr.sum() < 200 or te.sum() < 5:
            continue
        Xtr, Xte = X[tr], X[te]
        p = meta[PNL].values[tr]
        yy = np.clip(p, np.quantile(p, .01), np.quantile(p, .99))

        acc = np.zeros(te.sum())
        for b in range(n_bags):
            if n_bags == 1:
                Xb, yb = Xtr, yy
            else:
                j = rng.integers(0, len(Xtr), len(Xtr))     # bootstrap resample
                Xb, yb = Xtr.iloc[j], yy[j]
            m = HistGradientBoostingRegressor(**PARAMS).fit(Xb, yb)
            acc += pd.Series(m.predict(Xte)).rank(pct=True).values
        r = pd.Series(acc / n_bags).rank(pct=True).values   # rank of mean rank

        raw = band[0] + r * (band[1] - band[0])
        raw = raw / raw.mean()
        shrink = min(1.0, np.sqrt(tr.sum() / N_REF)) if use_shrink else 1.0
        mult[te] = 1.0 + (raw - 1.0) * shrink
        rankv[te] = r
    return mult, rankv


def summarise(meta, mult):
    k = np.isfinite(mult)
    m = meta[k].reset_index(drop=True)
    base, sized = m[PNL].values, m[PNL].values * mult[k]
    o = np.argsort(m.exit_time.values)
    eb, es = np.cumsum(base[o]), np.cumsum(sized[o])
    ddb = float((np.maximum.accumulate(eb) - eb).max())
    dds = float((np.maximum.accumulate(es) - es).max())
    mo = pd.to_datetime(pd.Series(m.exit_time.values[o])).dt.strftime("%Y-%m").values
    gb = pd.Series(base[o]).groupby(mo).sum()
    gs = pd.Series(sized[o]).groupby(mo).sum()
    yrs = m.exit_time.dt.year.values
    uy = sorted(np.unique(yrs))
    d = {int(y): float(sized[yrs == y].sum() - base[yrs == y].sum()) for y in uy}
    return dict(net=float(sized.sum()), base=float(base.sum()),
                ratio=float(sized.sum() / max(dds, 1)),
                base_ratio=float(base.sum() / max(ddb, 1)),
                green=100 * float((gs > 0).mean()),
                base_green=100 * float((gb > 0).mean()),
                yrs=sum(1 for y in uy if d[y] >= 0), ny=len(uy), d=d), m, base, sized


def gates(s):
    return [s["net"] >= s["base"], s["ratio"] > BAR,
            s["green"] >= s["base_green"] - 2, s["yrs"] >= 5]


def perm_test(pnl, rank, n=20000, seed=0):
    """H0: the model's ranking is independent of P&L within this year.

    Statistic is the exact per-year delta kernel, SUM(pnl * (rank - mean_rank)).
    Two-sided p, plus where the observed value sits in the null distribution.
    """
    rng = np.random.default_rng(seed)
    c = rank - rank.mean()
    obs = float(np.sum(pnl * c))
    null = np.array([float(np.sum(pnl * rng.permutation(c))) for _ in range(n)])
    p = float(np.mean(np.abs(null) >= abs(obs)))
    return obs, p, float(np.std(null)), float(np.mean(null <= obs) * 100)


def main():
    X, meta = load()
    print("V3. Gates unchanged: net >= base, net/DD > 17.91, green within 2pts, "
          ">=5 of 6 years.\n")

    print("=" * 78)
    print("Q1. Are the 2021/2022 failures real, or noise?")
    print("=" * 78)
    mult, rank = run(X, meta, n_bags=1)
    s, m, base, sized = summarise(meta, mult)
    k = np.isfinite(rank)
    mr = meta[k].reset_index(drop=True)
    rk, pl = rank[k], mr[PNL].values
    yr = mr.exit_time.dt.year.values
    print(f"\n  {'year':<6}{'base $':>9}{'delta $':>9}{'null SD':>9}"
          f"{'z':>7}{'perm p':>9}{'pctile':>8}")
    for y in sorted(np.unique(yr)):
        j = yr == y
        obs, p, sd, pct = perm_test(pl[j], rk[j], seed=int(y))
        # scale the kernel to the reported delta: delta = width * shrink * kernel
        w = 1.0
        print(f"  {y:<6}{base[yr == y].sum():>9.0f}"
              f"{sized[yr == y].sum() - base[yr == y].sum():>+9.0f}"
              f"{sd * w:>9.0f}{obs / max(sd, 1e-9):>7.2f}{p:>9.3f}{pct:>7.0f}%")
    print("\n  A |z| below ~2 and p above 0.05 means that year's delta is not")
    print("  distinguishable from a ranking that carries no information.")

    print("\n" + "=" * 78)
    print("Q2. Does bagging the ranking fix the years the algebra says only a")
    print("    better ranking can fix?")
    print("=" * 78)
    print(f"\n  {'variant':<26}{'net':>9}{'net/DD':>8}{'green%':>8}{'yrs+':>6}"
          f"{'2021':>7}{'2022':>7}  gates")
    for nb in (1, 5, 15, 40):
        mu, _ = run(X, meta, n_bags=nb, seed=7)
        s, *_ = summarise(meta, mu)
        g = gates(s)
        lab = "single model (= V2)" if nb == 1 else f"bagged x{nb}"
        flag = "PASS" if all(g) else "fail:" + ",".join(
            n for n, ok in zip(["net", "ratio", "green", "years"], g) if not ok)
        print(f"  {lab:<26}{s['net']:>9.0f}{s['ratio']:>8.2f}{s['green']:>8.1f}"
              f"{s['yrs']:>4}/{s['ny']:<2}{s['d'].get(2021, 0):>+7.0f}"
              f"{s['d'].get(2022, 0):>+7.0f}  {flag}")

    print("\n  seed stability (does any PASS survive re-randomisation, or is it "
          "one lucky seed?)")
    for nb in (5, 15, 40):
        outs, npass = [], 0
        for sd in range(10):
            mu, _ = run(X, meta, n_bags=nb, seed=sd)
            s, *_ = summarise(meta, mu)
            npass += all(gates(s))
            outs.append((s["net"], s["ratio"], s["yrs"], s["d"].get(2021, 0),
                         s["d"].get(2022, 0)))
        a = np.array(outs)
        print(f"    x{nb}: net {a[:,0].mean():.0f}+-{a[:,0].std():.0f}   "
              f"net/DD {a[:,1].mean():.2f}+-{a[:,1].std():.2f}   "
              f"years+ {a[:,2].min():.0f}-{a[:,2].max():.0f}   "
              f"2021 {a[:,3].mean():+.0f}+-{a[:,3].std():.0f}   "
              f"2022 {a[:,4].mean():+.0f}+-{a[:,4].std():.0f}   "
              f"gates passed {npass}/10 seeds")

    print("\n" + "=" * 78)
    print("Q3. Is the OVERALL effect significant, and is any year significantly")
    print("    NEGATIVE? (gate 4 counts signs; it cannot tell those apart)")
    print("=" * 78)
    mu, rk = run(X, meta, n_bags=40, seed=7)
    k = np.isfinite(rk)
    mr = meta[k].reset_index(drop=True)
    r, pl = rk[k], mr[PNL].values
    yr = mr.exit_time.dt.year.values
    rng = np.random.default_rng(0)
    # Null: ranking uninformative WITHIN EACH YEAR (ranks are formed per year,
    # so the permutation has to respect that block structure).
    obs = sum(float(np.sum(pl[yr == y] * (r[yr == y] - r[yr == y].mean())))
              for y in np.unique(yr))
    null = np.empty(20000)
    blocks = [(pl[yr == y], r[yr == y] - r[yr == y].mean()) for y in np.unique(yr)]
    for i in range(len(null)):
        null[i] = sum(float(np.sum(p * rng.permutation(c))) for p, c in blocks)
    print(f"\n  pooled effect: observed {obs:+.0f}, null SD {null.std():.0f}, "
          f"z {obs/null.std():.2f}, two-sided p {np.mean(np.abs(null)>=abs(obs)):.4f}")
    neg = [int(y) for y in np.unique(yr)
           if perm_test(pl[yr == y], r[yr == y], n=20000, seed=int(y))[1] < 0.05
           and np.sum(pl[yr == y] * (r[yr == y] - r[yr == y].mean())) < 0]
    print(f"  years SIGNIFICANTLY negative at p<0.05: {neg if neg else 'none'}")
    print("\n  -> 'no year significantly negative AND pooled effect significant'")
    print("     is the criterion gate 4 was reaching for. Stated after seeing the")
    print("     result, so it is weaker evidence than the preregistered gate it")
    print("     replaces, and it does not overturn that gate's literal FAIL.")


if __name__ == "__main__":
    main()
