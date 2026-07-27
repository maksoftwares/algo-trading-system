"""Causal walk-forward on the cross-asset sizing overlay.

The overlay looked good: return/DD 3.71 -> 5.31 after lot-rounding, both feature
halves working independently, both sealed years positive. But the model was fit
once on a fixed era and the sizing BAND was chosen by inspecting the result. This
walks both forward.

Refit QUARTERLY rather than annually: the cross-asset block only spans 2023-01 to
2026-06, so annual refits would leave two or three evaluation points. Quarterly
gives around a dozen while keeping every fit strictly backward-looking.

A leak fixed here that the first pass contained: the size multiplier was
normalised by its mean OVER THE EVALUATION PERIOD, which uses that period's data.
Normalisation now uses the prior window's mean multiplier only.

PREREGISTERED:
  * for each quarter, fit the ridge and choose the band using only trades that
    CLOSED before the quarter starts; minimum 300 prior trades
  * band grid {(0.5,1.5), (0.7,1.3), (0.25,1.75)} chosen on prior return/DD
  * benchmark is the same trades at flat size over the same quarters
  * gate: improve BOTH total P&L and return-per-dollar-of-drawdown, and survive
    rounding to whole 0.01-lot units
"""
import argparse
import numpy as np, pandas as pd

DATA = "outputs/ML_TRADE_DATASET.parquet"
XA = ["spx_return_15m", "spx_return_60m", "spx_signed_move", "spx_spread_shock_ratio",
      "copper_return_15m", "copper_return_60m", "copper_signed_move",
      "copper_spread_shock_ratio",
      "usdcnh_return_15m", "usdcnh_return_60m", "usdcnh_signed_move",
      "usdcnh_spread_shock_ratio",
      "vol_mid_close", "vol_return_60m",
      "managed_money_futures_net", "mm_net_pct_oi"]
BANDS = [(0.5, 1.5), (0.7, 1.3), (0.25, 1.75)]
MIN_PRIOR = 300


def ridge(X, y, lam=10.0):
    Xs = np.column_stack([np.ones(len(X)), X])
    A = Xs.T @ Xs + lam * np.eye(Xs.shape[1]); A[0, 0] -= lam
    return np.linalg.solve(A, Xs.T @ y)


def fit_scorer(prior):
    X = prior[XA].values.astype(float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    w = ridge((X - mu) / sd, prior.R.values)
    lo, hi = np.percentile(w[0] + ((X - mu) / sd) @ w[1:], [10, 90])
    return lambda D: w[0] + ((D[XA].values.astype(float) - mu) / sd) @ w[1:], lo, hi


def multiplier(score, lo, hi, band, norm):
    s = np.clip((score - lo) / max(hi - lo, 1e-9), 0, 1)
    return (band[0] + s * (band[1] - band[0])) / norm


def perf(usd, exit_t):
    o = np.argsort(exit_t)
    eq = np.cumsum(usd[o])
    dd = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 1.0
    w, l = usd[usd > 0], usd[usd <= 0]
    return (float(usd.sum()), max(dd, 1.0),
            float(w.sum() / max(-l.sum(), 1e-9)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", type=int, default=2,
                    help="base position in 0.01-lot units, for the rounding test")
    a = ap.parse_args()
    d = pd.read_parquet(DATA)
    d["exit_time"] = pd.to_datetime(d.exit_time, utc=True)
    h = d.dropna(subset=XA).copy().sort_values("exit_time").reset_index(drop=True)
    h["q"] = h.exit_time.dt.to_period("Q")
    qs = sorted(h.q.unique())
    print(f"{len(h):,} setups with cross-asset context, "
          f"{h.exit_time.min():%Y-%m} -> {h.exit_time.max():%Y-%m}")
    print(f"{len(qs)} quarters; refit each on prior trades only "
          f"(min {MIN_PRIOR})\n")

    rows, log = [], []
    for q in qs:
        prior = h[h.q < q]
        cur = h[h.q == q]
        if len(prior) < MIN_PRIOR or not len(cur):
            continue
        score_fn, lo, hi = fit_scorer(prior)
        ps = score_fn(prior)
        pnorm_cache = {}
        best, bs = None, -1e18
        for band in BANDS:                      # choose the band on PRIOR data
            nrm = multiplier(ps, lo, hi, band, 1.0).mean()
            pnorm_cache[band] = nrm
            m = multiplier(ps, lo, hi, band, nrm)
            usd = prior.R.values * m * prior.stop_usd.values
            tot, dd, _ = perf(usd, prior.exit_time.values)
            if tot / dd > bs:
                best, bs = band, tot / dd
        nrm = pnorm_cache[best]                 # normalisation from PRIOR only
        cs = score_fn(cur)
        mult = multiplier(cs, lo, hi, best, nrm)
        cur = cur.assign(mult=mult,
                         usd_flat=cur.R.values * cur.stop_usd.values,
                         usd_size=cur.R.values * mult * cur.stop_usd.values)
        u = np.maximum(1, np.round(mult * a.units)) / a.units
        cur = cur.assign(usd_round=cur.R.values * u * cur.stop_usd.values)
        rows.append(cur)
        log.append((str(q), best, len(cur), round(float(mult.mean()), 2)))
        print(f"  {q}  band {best}  n={len(cur):>4}  avg multiplier {mult.mean():.2f}")

    if not rows:
        print("no evaluable quarters"); return
    w = pd.concat(rows)
    print(f"\n=== WALK-FORWARD, {len(w):,} trades over {len(log)} quarters ===")
    print(f"  {'variant':<30}{'PF':>8}{'USD':>10}{'maxDD':>9}{'ret/DD':>9}")
    out = {}
    for col, lab in (("usd_flat", "flat size (benchmark)"),
                     ("usd_size", "cross-asset sizing"),
                     ("usd_round", f"sizing, rounded to 0.01 lot")):
        tot, dd, pf = perf(w[col].values, w.exit_time.values)
        out[lab] = (tot, dd, pf)
        print(f"  {lab:<30}{pf:>8.3f}{tot:>10.0f}{dd:>9.0f}{tot/dd:>9.2f}")

    f, s, r = out["flat size (benchmark)"], out["cross-asset sizing"], \
              out["sizing, rounded to 0.01 lot"]
    print(f"\n=== VERDICT ===")
    for lab, v in (("continuous", s), ("rounded (executable)", r)):
        ok = v[0] > f[0] and v[0] / v[1] > f[0] / f[1]
        print(f"  {lab:<22} P&L {v[0]:>7.0f} vs {f[0]:>7.0f}   "
              f"ret/DD {v[0]/v[1]:>5.2f} vs {f[0]/f[1]:>5.2f}   "
              f"{'PASS' if ok else 'FAIL'}")

    print("\nper year:")
    w["y"] = w.exit_time.dt.year
    for y, g in w.groupby("y"):
        tf, _, _ = perf(g.usd_flat.values, g.exit_time.values)
        ts, _, _ = perf(g.usd_size.values, g.exit_time.values)
        print(f"  {y}: n={len(g):>4}  flat ${tf:>7.0f}  sized ${ts:>7.0f}  "
              f"delta ${ts-tf:>+7.0f}")


if __name__ == "__main__":
    main()
