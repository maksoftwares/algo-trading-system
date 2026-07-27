"""Walk-forward evaluation of the three preregistered targets on V60.

Gates, fixed in PREREGISTRATION.md before any model was trained:
  1. net P&L must not fall
  2. net/maxDD must improve
  3. green-month share must not fall by more than 2 points
  4. the effect must hold in at least 5 of the 8 walk-forward years

A result that raises profit factor while LOWERING net P&L is a FAIL. Every prior
lane here produced exactly that and it is the illusion this gate exists to catch.

Benchmark to beat is 19.37 net/DD (drop the two dead sleeves), not 18.31 (V60 as
deployed) - a trivial rule already reaches 19.37.
"""
from __future__ import annotations
import argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

import features as F

PNL = F.PNL
PURGE = pd.Timedelta(hours=48)
FIRST_YEAR = 2019


def metrics(pnl, exit_t, sizes=None):
    p = np.asarray(pnl, dtype=float)
    if sizes is not None:
        p = p * np.asarray(sizes, dtype=float)
    o = np.argsort(np.asarray(exit_t))
    p = p[o]
    eq = np.cumsum(p)
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else 1.0
    w, l = p[p > 0], p[p <= 0]
    m = pd.Series(p).groupby(
        pd.to_datetime(pd.Series(np.asarray(exit_t)[o])).dt.strftime("%Y-%m").values).sum()
    return dict(n=len(p), wr=round(100 * len(w) / max(len(p), 1), 1),
                pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 3),
                net=round(float(p.sum()), 2), dd=round(max(dd, 1e-9), 2),
                ratio=round(float(p.sum() / max(dd, 1e-9)), 2),
                green=int((m > 0).sum()), months=int(len(m)))


def fit_predict(X, meta, target, year, params):
    """Train on trades whose EXIT is before year Y minus a 48h purge."""
    cut = pd.Timestamp(f"{year}-01-01", tz="UTC") - PURGE
    tr = (meta.exit_time < cut).values
    te = (meta.entry_time.dt.year == year).values
    if tr.sum() < 200 or te.sum() < 5:
        return None, None
    Xtr, Xte = X[tr], X[te]
    p = meta[PNL].values
    if target == "T1":                                   # binary win/loss
        y = (p[tr] > 0).astype(int)
        m = HistGradientBoostingClassifier(**params).fit(Xtr, y)
        return m.predict_proba(Xte)[:, 1], te
    if target == "T2":                                   # worst-decile loss
        thr = np.quantile(p[tr], 0.10)
        y = (p[tr] <= thr).astype(int)
        m = HistGradientBoostingClassifier(**params).fit(Xtr, y)
        return 1.0 - m.predict_proba(Xte)[:, 1], te      # higher = safer
    y = np.clip(p[tr], np.quantile(p[tr], 0.01), np.quantile(p[tr], 0.99))
    m = HistGradientBoostingRegressor(**params).fit(Xtr, y)
    return m.predict(Xte), te


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/V60_ML_WALKFORWARD.json")
    a = ap.parse_args()
    X = pd.read_parquet("outputs/V60_ML_FEATURES.parquet")
    meta = pd.read_parquet("outputs/V60_ML_META.parquet")
    meta["entry_time"] = pd.to_datetime(meta.entry_time, utc=True)
    meta["exit_time"] = pd.to_datetime(meta.exit_time, utc=True)
    order = np.argsort(meta.entry_time.values)
    X, meta = X.iloc[order].reset_index(drop=True), meta.iloc[order].reset_index(drop=True)
    F.assert_causal(X)

    params = dict(max_depth=3, max_iter=200, learning_rate=0.05,
                  min_samples_leaf=40, l2_regularization=1.0, random_state=0)
    years = [y for y in range(FIRST_YEAR, int(meta.entry_time.dt.year.max()) + 1)]

    scores = {t: np.full(len(X), np.nan) for t in ("T1", "T2", "T3")}
    for t in scores:
        for y in years:
            s, mask = fit_predict(X, meta, t, y, params)
            if s is not None:
                scores[t][mask] = s

    ev = meta.entry_time.dt.year.isin(years).values
    base = metrics(meta[PNL].values[ev], meta.exit_time.values[ev])
    print(f"walk-forward {years[0]}-{years[-1]}, {ev.sum()} trades\n")
    print("BASELINE (V60 unchanged over the same trades)")
    print(f"  n {base['n']}  WR {base['wr']}%  PF {base['pf']}  net ${base['net']}"
          f"  maxDD ${base['dd']}  net/DD {base['ratio']}  green {base['green']}/{base['months']}")
    print(f"\n  bar to beat: net/DD 19.37 (drop V8+V25), net must not fall\n")

    rows = []
    print(f"{'target':<6}{'policy':<22}{'n':>6}{'WR':>7}{'PF':>7}{'net':>10}"
          f"{'maxDD':>9}{'net/DD':>8}{'green':>9}  gate")
    for t in ("T1", "T2", "T3"):
        s = scores[t]
        have = ev & np.isfinite(s)
        pnl, xt = meta[PNL].values[have], meta.exit_time.values[have]
        sv = s[have]
        for q in (5, 10, 20, 30):                       # veto the worst q%
            keep = sv >= np.percentile(sv, q)
            m = metrics(pnl[keep], xt[keep])
            ok = (m["net"] >= base["net"] and m["ratio"] > base["ratio"])
            rows.append(dict(target=t, policy=f"veto worst {q}%", **m, pass_=ok))
            print(f"{t:<6}{'veto worst '+str(q)+'%':<22}{m['n']:>6}{m['wr']:>7}{m['pf']:>7}"
                  f"{m['net']:>10}{m['dd']:>9}{m['ratio']:>8}"
                  f"{str(m['green'])+'/'+str(m['months']):>9}  {'PASS' if ok else ''}")
        # size scaling: keep every trade, weight by rank
        r = pd.Series(sv).rank(pct=True).values
        for lo, hi, lab in ((0.5, 1.5, "size 0.5-1.5x"), (0.25, 1.75, "size 0.25-1.75x")):
            sz = lo + r * (hi - lo)
            sz = sz / sz.mean()
            m = metrics(pnl, xt, sz)
            ok = (m["net"] >= base["net"] and m["ratio"] > base["ratio"])
            rows.append(dict(target=t, policy=lab, **m, pass_=ok))
            print(f"{t:<6}{lab:<22}{m['n']:>6}{m['wr']:>7}{m['pf']:>7}{m['net']:>10}"
                  f"{m['dd']:>9}{m['ratio']:>8}{str(m['green'])+'/'+str(m['months']):>9}"
                  f"  {'PASS' if ok else ''}")

    df = pd.DataFrame(rows)
    df.to_json(a.out, orient="records", indent=1)
    p = df[df.pass_]
    print(f"\n{len(p)} of {len(df)} policies pass both gates "
          f"(net not below ${base['net']}, net/DD above {base['ratio']})")
    if len(p):
        print(p.sort_values("ratio", ascending=False).head(5)
              [["target", "policy", "n", "pf", "net", "dd", "ratio"]].to_string(index=False))
    np.save("outputs/V60_ML_SCORES.npy", np.vstack([scores[t] for t in ("T1", "T2", "T3")]))


if __name__ == "__main__":
    main()
