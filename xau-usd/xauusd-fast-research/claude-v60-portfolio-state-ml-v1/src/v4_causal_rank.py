"""V4: remove the look-ahead in how scores are turned into position sizes.

DEFECT FOUND IN V1-V3. The sizing multiplier was built like this:

    r   = pd.Series(scores_for_the_whole_test_year).rank(pct=True)
    raw = lo + r * (hi - lo)
    raw = raw / raw.mean()

Both lines use the entire test year at once. A trade taken in January is ranked
against trades from the following December, and the normaliser is the mean over
all of them. No P&L is involved, so this is not outcome leakage - but the policy
is not implementable live, because at the January trade you do not yet know the
score distribution of the rest of the year. It is the same class of defect as the
fixed dev-era percentile threshold that faked an alpha decay earlier in this
research.

Three mappings are compared here, all on identical model scores:

  A  within-year rank      - what V1-V3 used. NOT causal.
  B  train-distribution    - percentile against the model's predictions on its
                             own training window, fixed at fit time. Causal and
                             implementable: the mapping is known before the year
                             starts.
  C  expanding OOS         - percentile against every previously scored
                             out-of-sample trade, updated trade by trade. Causal
                             and implementable; falls back to B until it has
                             MIN_HIST observations.

The normaliser is also fixed causally. For ranks uniform on [0,1] the mean of
lo + r*(hi-lo) is (lo+hi)/2, so dividing by that constant reproduces a mean
multiplier of ~1 without consulting the test set.

If the headline result only survives under A, it is an artefact and the lane is
dead. Reported either way.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import features as F
from v3_significance_bagging import load, summarise, gates, perm_test, PARAMS

PNL = F.PNL
PURGE = pd.Timedelta(hours=48)
N_REF = 1500
MIN_HIST = 150


def run(X, meta, mode="C", n_bags=40, band=(0.5, 1.5), use_shrink=True, seed=0):
    rng = np.random.default_rng(seed)
    mult = np.full(len(X), np.nan)
    rankv = np.full(len(X), np.nan)
    lo, hi = band
    hist: list[float] = []                      # prior OOS scores, causal
    for y in range(2021, int(meta.entry_time.dt.year.max()) + 1):
        cut = pd.Timestamp(f"{y}-01-01", tz="UTC") - PURGE
        tr = (meta.exit_time < cut).values
        te = (meta.entry_time.dt.year == y).values
        if tr.sum() < 200 or te.sum() < 5:
            continue
        Xtr, Xte = X[tr], X[te]
        p = meta[PNL].values[tr]
        yy = np.clip(p, np.quantile(p, .01), np.quantile(p, .99))

        s_te = np.zeros(te.sum())
        s_tr = np.zeros(tr.sum())
        for b in range(n_bags):
            j = rng.integers(0, len(Xtr), len(Xtr)) if n_bags > 1 else np.arange(len(Xtr))
            m = HistGradientBoostingRegressor(**PARAMS).fit(Xtr.iloc[j], yy[j])
            s_te += m.predict(Xte)
            s_tr += m.predict(Xtr)
        s_te /= n_bags
        s_tr /= n_bags

        if mode == "A":                         # NOT causal - the original
            r = pd.Series(s_te).rank(pct=True).values
        elif mode == "B":                        # causal: fixed at fit time
            r = np.searchsorted(np.sort(s_tr), s_te, side="right") / len(s_tr)
        else:                                    # causal: expanding OOS window
            r = np.empty(len(s_te))
            ref = np.sort(s_tr)
            for i, v in enumerate(s_te):
                if len(hist) >= MIN_HIST:
                    h = np.sort(np.asarray(hist))
                    r[i] = np.searchsorted(h, v, side="right") / len(h)
                else:
                    r[i] = np.searchsorted(ref, v, side="right") / len(ref)
                hist.append(float(v))            # only after using it

        raw = lo + r * (hi - lo)
        if mode == "A":
            raw = raw / raw.mean()               # test-set normaliser, not causal
        else:
            raw = raw / ((lo + hi) / 2.0)        # constant, causal
        shrink = min(1.0, np.sqrt(tr.sum() / N_REF)) if use_shrink else 1.0
        mult[te] = 1.0 + (raw - 1.0) * shrink
        rankv[te] = r
    return mult, rankv


def main():
    X, meta = load()
    print("V4: does the result survive a causally implementable rank mapping?\n")
    print(f"  {'mapping':<34}{'net':>9}{'net/DD':>8}{'green%':>8}{'yrs+':>6}"
          f"{'mean mult':>10}  gates")
    store = {}
    for mode, lab in (("A", "A within-year rank (NOT causal)"),
                      ("B", "B train-distribution (causal)"),
                      ("C", "C expanding OOS (causal)")):
        nets, ratios, greens, yrs, mm, passes = [], [], [], [], [], 0
        for sd in range(5):
            mu, rk = run(X, meta, mode=mode, seed=sd)
            s, *_ = summarise(meta, mu)
            nets.append(s["net"]); ratios.append(s["ratio"])
            greens.append(s["green"]); yrs.append(s["yrs"])
            mm.append(float(np.nanmean(mu)))
            passes += all(gates(s))
            if sd == 0:
                store[mode] = (mu, rk, s)
        print(f"  {lab:<34}{np.mean(nets):>9.0f}{np.mean(ratios):>8.2f}"
              f"{np.mean(greens):>8.1f}{min(yrs)}-{max(yrs)}/6{np.mean(mm):>10.3f}"
              f"  {passes}/5 seeds")

    b = store["A"][2]
    print(f"\n  V60 baseline: net ${b['base']:.0f}, net/DD {b['base_ratio']:.2f}, "
          f"green {b['base_green']:.1f}%   trivial bar net/DD 17.91")

    print("\n  per-year delta by mapping")
    print(f"  {'year':<6}" + "".join(f"{m:>12}" for m in ("A", "B", "C")))
    yrs = sorted(store["A"][2]["d"])
    for y in yrs:
        print(f"  {y:<6}" + "".join(f"{store[m][2]['d'][y]:>+12.0f}" for m in ("A", "B", "C")))

    print("\n  pooled permutation test on the causal mapping (C)")
    mu, rk, _ = store["C"]
    k = np.isfinite(rk)
    mr = meta[k].reset_index(drop=True)
    r, pl = rk[k], mr[PNL].values
    yr = mr.exit_time.dt.year.values
    rng = np.random.default_rng(0)
    blocks = [(pl[yr == y], r[yr == y] - r[yr == y].mean()) for y in np.unique(yr)]
    obs = sum(float(np.sum(p * c)) for p, c in blocks)
    null = np.array([sum(float(np.sum(p * rng.permutation(c))) for p, c in blocks)
                     for _ in range(20000)])
    print(f"    observed {obs:+.0f}, null SD {null.std():.0f}, "
          f"z {obs/null.std():.2f}, two-sided p {np.mean(np.abs(null)>=abs(obs)):.4f}")


if __name__ == "__main__":
    main()
