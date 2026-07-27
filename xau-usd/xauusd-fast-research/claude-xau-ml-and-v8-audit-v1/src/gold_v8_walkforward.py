"""Mechanism-causal walk-forward on GOLD V8 - the test that killed the regime family.

V8's headline (WR 40.7%, PF 1.57, maxDD $233, 61% green) is fit on trades closing
by 2024-12-31 and reported on 18 sealed months. That is a fair test of the
CONFIGURATION, but the assembled system was still chosen by comparing ~10
variants on those same sealed months. This removes that.

For each evaluation year Y, using ONLY trades that closed before Y:
  1. the ranker is refit per sleeve,
  2. the selection threshold is a trailing quantile (already causal),
  3. K and the streak trip points are chosen on the prior record,
then the system trades year Y. Nothing from year Y or later informs any decision
made for year Y. Concatenating the years gives an honest record of the whole
approach - parameter choice included.

The twelve sleeves (3 horizons x 4 gates) are NOT selected per year; using all of
them is V8's design, so it is fixed rather than fitted.

Reference points from today: V6 gave back 1.73 -> 1.42 under this test and
survived; the regime family gave back 1.99 -> 0.82 and did not.
"""
import argparse, itertools, json
import numpy as np, pandas as pd
import engine, specialist
from regime_frontier5 import rolling_thr
import gold_v8 as V

FIRST_YEAR = 2019          # needs ~2.5y of prior candidates to fit a ranker
K_GRID = (4, 6, 8)
STREAK_GRID = ((2, 4), (1, 3), (3, 5))


def raw_candidates(C, hz, gate):
    """Enumeration only - no ranking. Independent of the evaluation year, so it
    runs once per sleeve rather than once per sleeve per year."""
    n, t = C["n"], C["t"]
    mc, mh, ml, atr, ema, slope = C["mc"], C["mh"], C["ml"], C["atr"], C["ema"], C["slope"]
    bo, bl, bc, ao, ah, ac = C["bo"], C["bl"], C["bc"], C["ao"], C["ah"], C["ac"]
    csm, cbi, ctc, cts, cpe = C["csm"], C["cbi"], C["ctc"], C["cts"], C["cpe"]
    ok = ((C["minute"] % V.GRID_MIN == 0) & (C["hour"] >= V.HOUR_LO)
          & (C["hour"] < V.HOUR_HI) & np.isfinite(atr) & np.isfinite(slope) & (atr > 0))
    rows = []
    for i in np.flatnonzero(ok):
        if i < 2016 or i + 2 >= n:
            continue
        long = slope[i] >= 0.0
        stop = V.STOP_MULT * atr[i]
        if not stop > 0:
            continue
        e = mc[i]
        i0, i1 = i + 1, min(i + 1 + hz, n)
        if i1 - i0 < 20:
            continue
        up, dn = mh[i0:i1] - e, e - ml[i0:i1]
        cu = np.flatnonzero(up >= V.CONF * stop)
        cd = np.flatnonzero(dn >= V.CONF * stop)
        if long:
            if not len(cu) or (len(cd) and cd[0] < cu[0]):
                continue
            k = int(cu[0])
        else:
            if not len(cd) or (len(cu) and cu[0] < cd[0]):
                continue
            k = int(cd[0])
        if gate is not None:
            pre = (e - mc[i - 24]) / atr[i]
            if long and pre > -gate:
                continue
            if (not long) and pre < gate:
                continue
        j = i0 + k + 1
        if j + 1 >= i1:
            continue
        nb, sgn = k + 1, (1.0 if long else -1.0)
        a, b = i0, i0 + k + 1
        if long:
            fill = ao[j]; slv = fill - stop
            hit = np.flatnonzero(bl[j:i1] <= slv)
            xi = j + hit[0] if len(hit) else i1 - 1
            xp = slv if len(hit) else bc[xi]
            r = (xp - fill) / stop - engine.FEE / stop
        else:
            fill = bo[j]; slv = fill + stop
            hit = np.flatnonzero(ah[j:i1] >= slv)
            xi = j + hit[0] if len(hit) else i1 - 1
            xp = slv if len(hit) else ac[xi]
            r = (fill - xp) / stop - engine.FEE / stop
        rows.append((i, t.iloc[i], t.iloc[j], t.iloc[xi], long, r, stop,
                     nb, sgn * (csm[b] - csm[a]), sgn * (cbi[b] - cbi[a]) / nb,
                     (ctc[b] - ctc[a]) / nb, ((cts[b] - cts[a]) / nb) / stop,
                     (cpe[b] - cpe[a]) / nb,
                     float(max((dn if long else up)[:k + 1].max(), 0.0)) / stop,
                     sgn * (e - ema[i]) / atr[i]))
    c = pd.DataFrame(rows, columns=["i", "dec_t", "entry_t", "exit_t", "long",
                                    "r", "stop"] + V.FEATS)
    return c.sort_values("dec_t").reset_index(drop=True)


def select_before(c, year, keep_pct):
    """Ranker fit on candidates CLOSED before `year`; trailing-quantile threshold."""
    fit = (c.exit_t.dt.year < year).values
    if fit.sum() < 150:
        return None
    X = c[V.FEATS].values.astype(float)
    mu, sd = X[fit].mean(0), X[fit].std(0) + 1e-9
    Z = (X - mu) / sd
    A = Z[fit].T @ Z[fit] + 5.0 * np.eye(len(V.FEATS))
    w = np.linalg.solve(A, Z[fit].T @ c.r.values[fit])
    s = Z @ w
    thr = rolling_thr(s, 100 - keep_pct)
    return c[s >= thr].assign(score=s[s >= thr])


def assemble(parts, K, half, quart):
    a = pd.concat(parts).reset_index(drop=True)
    a = a.sort_values("score", ascending=False).groupby(["i"], as_index=False).first()
    a = a.sort_values("dec_t").reset_index(drop=True)
    oe, keep = [], []
    for row in a.itertuples():
        oe = [e for e in oe if e > row.dec_t]
        if len(oe) >= K:
            continue
        keep.append(row.Index); oe.append(row.exit_t)
    a = a.loc[keep].sort_values("exit_t").reset_index(drop=True)
    size, st = np.ones(len(a)), 0
    for k, r in enumerate(a.r.values):
        size[k] = 0.25 if st >= quart else (0.5 if st >= half else 1.0)
        st = 0 if r > 0 else st + 1
    return a.assign(size=size, usd=a.r * V.RISK_USD * size)


def score_prior(a, year):
    """Rank a parameter set on months that CLOSED before `year`."""
    p = a[a.exit_t.dt.year < year]
    if len(p) < 100:
        return -1e9
    m = p.groupby(p.exit_t.dt.to_period("M")).usd.sum()
    if not len(m):
        return -1e9
    eq = p.usd.cumsum()
    dd = max(float((eq.cummax() - eq).max()), 1.0)
    return float(p.usd.sum()) / dd + 100.0 * float((m > 0).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/GOLD_V8_WALKFORWARD.json")
    a = ap.parse_args()
    C = specialist.load_context()
    print("enumerating 12 sleeves once (year-independent)...", flush=True)
    raw = {}
    for hn, hz in V.HORIZONS.items():
        for gn, gate, pct in V.GATES:
            c = raw_candidates(C, hz, gate)
            if len(c) > 200:
                raw[f"{hn}_{gn}"] = (c, pct)
                print(f"   {hn}_{gn:<6} {len(c):>6}", flush=True)

    last_year = int(max(c.exit_t.dt.year.max() for c, _ in raw.values()))
    kept, picks = [], []
    for year in range(FIRST_YEAR, last_year + 1):
        parts = []
        for name, (c, pct) in raw.items():
            s = select_before(c, year, pct)
            if s is not None and len(s):
                parts.append(s.assign(sleeve=name))
        if not parts:
            continue
        best, bs = None, -1e9
        for K, (h, q) in itertools.product(K_GRID, STREAK_GRID):
            cand = assemble(parts, K, h, q)
            sc = score_prior(cand, year)
            if sc > bs:
                best, bs = (cand, K, h, q), sc
        if best is None:
            continue
        cand, K, h, q = best
        cur = cand[cand.exit_t.dt.year == year]
        if len(cur):
            kept.append(cur)
        picks.append(dict(year=year, K=K, half=h, quarter=q, n=len(cur)))
        print(f"{year}: chose K={K}, streak half@{h}/quarter@{q}  -> {len(cur)} trades",
              flush=True)

    if not kept:
        print("no walk-forward trades"); return
    f = pd.concat(kept).sort_values("exit_t").reset_index(drop=True)
    m = f.groupby(f.exit_t.dt.to_period("M")).usd.sum()
    eq = f.usd.cumsum()
    r = f.r.values; w, l = r[r > 0], r[r <= 0]
    print(f"\n=== V8 WALK-FORWARD {FIRST_YEAR}-{last_year} "
          f"(every parameter chosen from prior data only) ===")
    print(f"trades {len(f)}   WR {100*len(w)/len(r):.1f}%   "
          f"PF {w.sum()/max(-l.sum(),1e-9):.2f}   ${f.usd.sum():.0f}   "
          f"maxDD ${float((eq.cummax()-eq).max()):.0f}")
    print(f"green months {int((m>0).sum())}/{len(m)} = {100*(m>0).mean():.1f}%   "
          f"worst ${m.min():.0f}   best ${m.max():.0f}")
    print("\nper year:")
    f["y"] = f.exit_t.dt.year
    print(f.groupby("y").agg(
        n=("r", "size"), wr=("r", lambda x: round(100 * (x > 0).mean(), 1)),
        pf=("r", lambda x: round(x[x > 0].sum() / max(-x[x <= 0].sum(), 1e-9), 2)),
        usd=("usd", lambda x: round(x.sum()))).to_string())
    print("\nlast 18 months (same window V8 reported on):")
    m18 = m[m.index >= pd.Period("2025-01")]
    print(f"  ${m18.sum():.0f}   green {int((m18>0).sum())}/{len(m18)} "
          f"= {100*(m18>0).mean():.1f}%   worst ${m18.min():.0f}")
    json.dump(dict(picks=picks, n=len(f),
                   wr=round(100 * len(w) / len(r), 1),
                   pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 2),
                   usd=round(float(f.usd.sum())),
                   dd=round(float((eq.cummax() - eq).max())),
                   green=f"{int((m>0).sum())}/{len(m)}",
                   monthly={str(k): round(float(v)) for k, v in m.items()}),
              open(a.out, "w"), indent=1, default=str)
    f.to_csv(a.out.replace(".json", "_TRADES.csv"), index=False)


if __name__ == "__main__":
    main()
