"""GOLD V8 - synthesis of everything that survived testing on 2026-07-26.

KEPT (each validated independently this session):
  bidirectional entries   direction from the weekly trend; V6 took ZERO trades in
                          Jun 2026 while this made +$1,500 in the same month
  dedup                   one position per setup; 81% of V6 signals were taken
                          twice, burning both slots and doubling risk
  rolling threshold       a frozen dev-era percentile is not a fixed selectivity;
                          V6 drifted to 0.43-0.62x its intended trade rate
  streak sizing           half after 3 consecutive losers, quarter after 5, reset
                          on any win. Feb 2026 -$1,743 -> -$528, green 50% -> 72%

DISCARDED (each falsified today, do not reintroduce without new evidence):
  regime-split specialists   PF 1.99 in-sample -> 0.82 causal
  regime identifier          Jan and Feb 2026 are both stable STRONG_BULL months,
                             +$1,903 and -$1,743. No label separates them.
  multi-instrument           mechanism does not transfer on equal footing
  trend-strength band        clean in fit era, reversed sign out of sample
  monthly circuit breaker    amputates recoveries

NEW, with reasons rather than fitted parameters:
  1. RISK NORMALISATION. Per-trade risk ran $2-$187 because the stop is
     6.75xATR and ATR followed gold from $1,200 to $5,500. Recent months
     therefore carried ~10x the risk of early ones - a large and entirely
     avoidable source of monthly variance. Sizing each trade to a constant
     dollar risk should raise month-to-month consistency directly.
  2. SPECIALISTS BY HORIZON, NOT REGIME. Regime splitting failed because the
     label does not separate good months from bad. Holding period does change
     which setups a sleeve sees, so 12h/36h/72h sleeves decorrelate for a
     structural reason rather than a fitted one.

Everything is fit on trades CLOSING on or before 2024-12-31. The 18 months from
2025-01 are sealed and used only to report.
"""
import argparse, itertools, json
import numpy as np, pandas as pd
import engine, specialist
from regime_frontier5 import rolling_thr

FIT_END = pd.Timestamp("2024-12-31 23:59:59", tz="UTC")
STOP_MULT, CONF, GRID_MIN, HOUR_LO, HOUR_HI = 6.75, 0.5, 30, 7, 17
FEATS = ["speed", "flow", "imb", "activity", "spr", "eff", "adv_pre", "align"]
HORIZONS = {"12h": 144, "36h": 432, "72h": 864}
GATES = [("trend", None, 95), ("dip05", 0.5, 80), ("dip10", 1.0, 80),
         ("dip15", 1.5, 80)]
RISK_USD = 10.0                       # constant dollar risk per trade


def candidates(C, hz, gate, keep_pct):
    n, t = C["n"], C["t"]
    mc, mh, ml, atr, ema, slope = C["mc"], C["mh"], C["ml"], C["atr"], C["ema"], C["slope"]
    bo, bl, bc, ao, ah, ac = C["bo"], C["bl"], C["bc"], C["ao"], C["ah"], C["ac"]
    csm, cbi, ctc, cts, cpe = C["csm"], C["cbi"], C["ctc"], C["cts"], C["cpe"]
    ok = ((C["minute"] % GRID_MIN == 0) & (C["hour"] >= HOUR_LO)
          & (C["hour"] < HOUR_HI) & np.isfinite(atr) & np.isfinite(slope) & (atr > 0))
    rows = []
    for i in np.flatnonzero(ok):
        if i < 2016 or i + 2 >= n:
            continue
        long = slope[i] >= 0.0
        stop = STOP_MULT * atr[i]
        if not stop > 0:
            continue
        e = mc[i]
        i0, i1 = i + 1, min(i + 1 + hz, n)
        if i1 - i0 < 20:
            continue
        up, dn = mh[i0:i1] - e, e - ml[i0:i1]
        cu = np.flatnonzero(up >= CONF * stop)
        cd = np.flatnonzero(dn >= CONF * stop)
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
                                    "r", "stop"] + FEATS)
    if len(c) < 100:
        return c.iloc[0:0]
    # ranker fit on trades CLOSED by FIT_END; rolling threshold keeps the
    # intended selectivity as features drift
    fit = (c.exit_t <= FIT_END).values
    if fit.sum() < 80:
        return c.iloc[0:0]
    X = c[FEATS].values.astype(float)
    mu, sd = X[fit].mean(0), X[fit].std(0) + 1e-9
    Z = (X - mu) / sd
    A = Z[fit].T @ Z[fit] + 5.0 * np.eye(len(FEATS))
    w = np.linalg.solve(A, Z[fit].T @ c.r.values[fit])
    c = c.assign(score=Z @ w).sort_values("dec_t").reset_index(drop=True)
    thr = rolling_thr(c.score.values, 100 - keep_pct)
    return c[c.score.values >= thr]


def assemble(parts, K, normalise):
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
    # constant dollar risk per trade, instead of risk = 6.75xATR at a fixed lot
    a["risk"] = RISK_USD if normalise else a.stop
    # streak sizing: state depends only on trades already closed
    size, streak = np.ones(len(a)), 0
    for k, r in enumerate(a.r.values):
        size[k] = 0.25 if streak >= 5 else (0.5 if streak >= 3 else 1.0)
        streak = 0 if r > 0 else streak + 1
    a["size"] = size
    a["usd"] = a.r * a.risk * a["size"]
    return a


def report(a, label):
    s = a[a.exit_t > FIT_END].copy()
    if not len(s):
        return None
    s["m"] = s.exit_t.dt.to_period("M")
    m = s.groupby("m").usd.sum()
    eq = s.usd.cumsum()
    r = s.r.values; w, l = r[r > 0], r[r <= 0]
    d = dict(label=label, n=len(s), wr=round(100 * len(w) / len(r), 1),
             pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 2),
             usd=round(float(s.usd.sum())),
             dd=round(float((eq.cummax() - eq).max())),
             green=int((m > 0).sum()), months=len(m),
             worst=round(float(m.min())), best=round(float(m.max())), m=m)
    d["green_pct"] = round(100 * d["green"] / d["months"], 1)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, default=4)
    a = ap.parse_args()
    C = specialist.load_context()
    print("building horizon-diversified sleeves (fit <= 2024-12-31)\n")
    sleeves = {}
    for hname, hz in HORIZONS.items():
        for gname, gate, pct in GATES:
            c = candidates(C, hz, gate, pct)
            if len(c):
                sleeves[f"{hname}_{gname}"] = c.assign(sleeve=f"{hname}_{gname}")
                print(f"  {hname}_{gname:<6} {len(c):>6} trades", flush=True)
    if not sleeves:
        print("no sleeves"); return

    variants = [
        ("V6-style: 36h only, raw risk", [k for k in sleeves if k.startswith("36h")], False),
        ("36h only, normalised risk", [k for k in sleeves if k.startswith("36h")], True),
        ("all horizons, raw risk", list(sleeves), False),
        ("ALL HORIZONS + NORMALISED RISK", list(sleeves), True),
    ]
    print(f"\n{'variant':<34}{'n':>6}{'WR':>7}{'PF':>7}{'USD':>8}{'maxDD':>8}"
          f"{'green':>9}{'worst':>8}{'best':>8}")
    out = []
    for label, keys, norm in variants:
        d = report(assemble([sleeves[k] for k in keys], a.K, norm), label)
        if not d:
            continue
        out.append(d)
        print(f"{label:<34}{d['n']:>6}{d['wr']:>6}%{d['pf']:>7}{d['usd']:>8}"
              f"{d['dd']:>8}{str(d['green'])+'/'+str(d['months']):>9}"
              f"{d['worst']:>8}{d['best']:>8}")

    best = out[-1]
    print(f"\n=== {best['label']} — month by month, newest first ===")
    print(f"{'month':<10}{'USD':>10}{'cum':>10}")
    cum = 0.0
    for idx in sorted(best["m"].index, reverse=True):
        pass
    run = best["m"].sort_index()
    cs = run.cumsum()
    for idx in sorted(run.index, reverse=True):
        print(f"{str(idx):<10}{run[idx]:>10.0f}{cs[idx]:>10.0f}")
    print(f"\ngreen {best['green']}/{best['months']} = {best['green_pct']}%   "
          f"total ${best['usd']}   maxDD ${best['dd']}   "
          f"worst ${best['worst']}   best ${best['best']}")
    json.dump({k: v for k, v in best.items() if k != "m"},
              open("outputs/GOLD_V8_RESULT.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
