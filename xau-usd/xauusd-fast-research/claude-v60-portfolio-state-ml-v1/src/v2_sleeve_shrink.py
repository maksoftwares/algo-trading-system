"""V2: sleeve identity + confidence shrinkage. Same four gates as V1.

V1 diagnosis: the sizing overlay improved in 4 of 6 years, failing gate 4. The
two failures were 2021 and 2022 — the years with the thinnest training data
(~400 and ~500 prior trades) — while correlation was strongest in the most recent
year. Two omissions plausibly cause that:

  1. THE MODEL DOES NOT KNOW WHICH SLEEVE A TRADE CAME FROM. It sees only
     `is_core`. Sleeve quality ranges from PF 1.04 (V8_RETEST_HEALTH, $18 net on
     204 trades) to 2.03 (R1_NATIVE_POSITION, $2,716 on 444). That is the single
     most informative variable available and V1 omitted it. Encoded here as the
     sleeve's mean P&L over PRIOR trades only — never its own outcome, never a
     later one.

  2. THE POLICY SIZES AS AGGRESSIVELY ON 400 TRAINING TRADES AS ON 1,500. A
     policy should respect its own uncertainty. The multiplier is shrunk toward
     flat by sqrt(n_train / n_reference), so early years trade near 1.0x and the
     ramp only opens as evidence accumulates.

This is post-V1 iteration and says so. The gates are unchanged from
PREREGISTRATION.md, including the literal 5-of-6 year count. If V2 passes only by
moving a gate, it has not passed.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import features as F

PNL = F.PNL
PURGE = pd.Timedelta(hours=48)
N_REF = 1500          # training size at which the ramp reaches full width


def sleeve_encoding(meta, upto_idx, sleeves):
    """Mean P&L per sleeve over trades that CLOSED before the cutoff. Sleeves
    with no prior history get the global prior, not zero."""
    prior = meta.iloc[:upto_idx]
    if not len(prior):
        return {s: 0.0 for s in sleeves}, 0.0
    g = prior.groupby("source_id")[PNL].agg(["mean", "count"])
    glob = float(prior[PNL].mean())
    # shrink each sleeve mean toward the global mean by its own sample size
    enc = {}
    for s in sleeves:
        if s in g.index and g.loc[s, "count"] >= 20:
            k = g.loc[s, "count"] / (g.loc[s, "count"] + 30.0)
            enc[s] = float(k * g.loc[s, "mean"] + (1 - k) * glob)
        else:
            enc[s] = glob
    return enc, glob


def run(use_sleeve=True, use_shrink=True, band=(0.25, 1.75)):
    X = pd.read_parquet("outputs/V60_ML_FEATURES.parquet")
    meta = pd.read_parquet("outputs/V60_ML_META.parquet")
    meta["entry_time"] = pd.to_datetime(meta.entry_time, utc=True)
    meta["exit_time"] = pd.to_datetime(meta.exit_time, utc=True)
    o = np.argsort(meta.entry_time.values)
    X, meta = X.iloc[o].reset_index(drop=True), meta.iloc[o].reset_index(drop=True)
    MK = [c for c in X.columns if c not in F.PORTFOLIO]     # market only, per V1
    sleeves = sorted(meta.source_id.unique())

    score = np.full(len(X), np.nan)
    mult = np.full(len(X), np.nan)
    for y in range(2021, int(meta.entry_time.dt.year.max()) + 1):
        cut = pd.Timestamp(f"{y}-01-01", tz="UTC") - PURGE
        tr = (meta.exit_time < cut).values
        te = (meta.entry_time.dt.year == y).values
        if tr.sum() < 200 or te.sum() < 5:
            continue
        Xtr, Xte = X[MK][tr].copy(), X[MK][te].copy()
        if use_sleeve:
            enc, glob = sleeve_encoding(meta, int(np.flatnonzero(tr)[-1]) + 1, sleeves)
            Xtr["sleeve_q"] = meta.source_id[tr].map(enc).fillna(glob).values
            Xte["sleeve_q"] = meta.source_id[te].map(enc).fillna(glob).values
        p = meta[PNL].values[tr]
        yy = np.clip(p, np.quantile(p, .01), np.quantile(p, .99))
        m = HistGradientBoostingRegressor(max_depth=3, max_iter=200,
                                          learning_rate=0.05, min_samples_leaf=40,
                                          l2_regularization=1.0,
                                          random_state=0).fit(Xtr, yy)
        s = m.predict(Xte)
        score[te] = s
        r = pd.Series(s).rank(pct=True).values
        raw = band[0] + r * (band[1] - band[0])
        raw = raw / raw.mean()
        shrink = min(1.0, np.sqrt(tr.sum() / N_REF)) if use_shrink else 1.0
        mult[te] = 1.0 + (raw - 1.0) * shrink
    return meta, score, mult


def report(meta, mult, lab, base_ref=None):
    k = np.isfinite(mult)
    m = meta[k].reset_index(drop=True)
    base = m[PNL].values
    sized = base * mult[k]
    o = np.argsort(m.exit_time.values)
    eb, es = np.cumsum(base[o]), np.cumsum(sized[o])
    ddb = float((np.maximum.accumulate(eb) - eb).max())
    dds = float((np.maximum.accumulate(es) - es).max())
    yrs = m.exit_time.dt.year.values
    uy = sorted(np.unique(yrs))
    up = sum(1 for y in uy if sized[yrs == y].sum() >= base[yrs == y].sum())
    gb = pd.Series(base[o]).groupby(pd.to_datetime(pd.Series(m.exit_time.values[o])).dt.strftime("%Y-%m").values).sum()
    gs = pd.Series(sized[o]).groupby(pd.to_datetime(pd.Series(m.exit_time.values[o])).dt.strftime("%Y-%m").values).sum()
    w, l = sized[sized > 0], sized[sized <= 0]
    out = dict(lab=lab, n=len(m), pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 3),
               base=round(float(base.sum()), 0), net=round(float(sized.sum()), 0),
               dd=round(dds, 0), ratio=round(float(sized.sum() / max(dds, 1)), 2),
               base_ratio=round(float(base.sum() / max(ddb, 1)), 2),
               green=round(100 * float((gs > 0).mean()), 1),
               base_green=round(100 * float((gb > 0).mean()), 1),
               yrs=up, ny=len(uy))
    return out


def main():
    print("V2: sleeve identity + confidence shrinkage. Gates unchanged from V1.\n")
    rows = []
    for us, uh, lab in ((False, False, "V1 reproduction (market only)"),
                        (True, False, "+ sleeve identity"),
                        (False, True, "+ shrinkage only"),
                        (True, True, "V2: sleeve + shrinkage")):
        meta, sc, mu = run(use_sleeve=us, use_shrink=uh)
        rows.append(report(meta, mu, lab))
    b = rows[0]
    bar = max(b["base_ratio"], 17.91)
    print(f"baseline: net ${b['base']}, net/DD {b['base_ratio']}, green {b['base_green']}%")
    print(f"gates: net >= ${b['base']}, net/DD > {bar}, green >= {b['base_green']-2}%, "
          f">= 5 of {b['ny']} years\n")
    print(f"{'variant':<32}{'n':>6}{'PF':>7}{'net':>9}{'maxDD':>8}{'net/DD':>8}"
          f"{'green%':>8}{'yrs+':>6}  gates")
    for r in rows:
        g = [r["net"] >= r["base"], r["ratio"] > bar,
             r["green"] >= r["base_green"] - 2, r["yrs"] >= 5]
        r["pass"] = all(g)
        flag = "PASS" if all(g) else "fail:" + ",".join(
            n for n, ok in zip(["net", "ratio", "green", "years"], g) if not ok)
        print(f"{r['lab']:<32}{r['n']:>6}{r['pf']:>7}{r['net']:>9}{r['dd']:>8}"
              f"{r['ratio']:>8}{r['green']:>8}{r['yrs']:>4}/{r['ny']:<2}  {flag}")

    meta, sc, mu = run(True, True)
    k = np.isfinite(mu)
    m = meta[k].reset_index(drop=True)
    base, sized = m[PNL].values, m[PNL].values * mu[k]
    m = m.assign(base=base, sized=sized, y=m.exit_time.dt.year, mult=mu[k])
    print("\nV2 year by year:")
    print(f"  {'year':<6}{'n':>5}{'base':>10}{'sized':>10}{'delta':>9}{'avg mult':>10}")
    for y, g in m.groupby("y"):
        print(f"  {y:<6}{len(g):>5}{g.base.sum():>10.0f}{g.sized.sum():>10.0f}"
              f"{g.sized.sum()-g.base.sum():>+9.0f}{g['mult'].mean():>10.2f}")


if __name__ == "__main__":
    main()
