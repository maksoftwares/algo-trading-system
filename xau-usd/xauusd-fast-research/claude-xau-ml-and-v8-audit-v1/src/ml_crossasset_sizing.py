"""Cross-asset context as a SIZING control, not a take/skip filter.

ML_FILTER_FINDINGS.md refuted cross-asset ML as a binary filter and named this
as the untested alternative. The distinction matters: a hard cutoff throws away
trades entirely, so a weak-but-real signal gets destroyed by the positive
expectancy it discards. A sizing overlay keeps every trade and only reweights
them - it can extract value from a signal too weak to justify skipping.

Why this input might not be redundant: every feature the frozen ranker uses is
derived from the same XAUUSD M5 bars. SPX, copper, USDCNH, the gold vol index and
weekly CFTC positioning are ORTHOGONAL - the ranker has never seen them.

PREREGISTERED BEFORE RUNNING:
  * fit on trades closing on or before 2024-12-31; 2025-01 onward sealed
  * benchmark is the SAME trades at flat size
  * gate: must improve total P&L AND return-per-dollar-of-drawdown on the sealed
    era, at a mapping chosen from the fit era
  * cross-asset features ONLY in the sizing model - if it merely rediscovers the
    ranker's own signal it has added nothing
  * executability check afterwards: continuous multipliers are not tradeable at
    0.01-lot granularity, so any gain must survive rounding to whole lots
"""
import argparse
import numpy as np, pandas as pd

DATA = "outputs/ML_TRADE_DATASET.parquet"
FIT_END = pd.Timestamp("2024-12-31 23:59:59", tz="UTC")

XA = ["spx_return_15m", "spx_return_60m", "spx_signed_move", "spx_spread_shock_ratio",
      "copper_return_15m", "copper_return_60m", "copper_signed_move",
      "copper_spread_shock_ratio",
      "usdcnh_return_15m", "usdcnh_return_60m", "usdcnh_signed_move",
      "usdcnh_spread_shock_ratio",
      "vol_mid_close", "vol_return_60m",
      "managed_money_futures_net", "mm_net_pct_oi"]


def ridge(X, y, lam=10.0):
    Xs = np.column_stack([np.ones(len(X)), X])
    A = Xs.T @ Xs + lam * np.eye(Xs.shape[1]); A[0, 0] -= lam
    return np.linalg.solve(A, Xs.T @ y)


def summarise(d, size, lab):
    usd = d.R.values * size * d.stop_usd.values
    order = np.argsort(d.exit_time.values)
    eq = np.cumsum(usd[order])
    dd = float(np.maximum.accumulate(eq).max() - eq.min()) if len(eq) else 0.0
    dd = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 0.0
    w, l = usd[usd > 0], usd[usd <= 0]
    pf = float(w.sum() / max(-l.sum(), 1e-9))
    print(f"  {lab:<28}{len(d):>6}{pf:>8.3f}{usd.sum():>10.0f}{dd:>9.0f}"
          f"{usd.sum()/max(dd,1):>9.2f}{size.mean():>8.2f}")
    return dict(n=len(d), pf=pf, usd=float(usd.sum()), dd=dd,
                ratio=usd.sum() / max(dd, 1))


def main():
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    d = pd.read_parquet(DATA)
    d["dec_time"] = pd.to_datetime(d.dec_time, utc=True)
    d["exit_time"] = pd.to_datetime(d.exit_time, utc=True)
    have = d.dropna(subset=XA).copy().sort_values("exit_time").reset_index(drop=True)
    print(f"dataset {len(d):,} setups; {len(have):,} carry cross-asset context "
          f"({have.dec_time.min():%Y-%m} -> {have.dec_time.max():%Y-%m})")

    fit = have[have.exit_time <= FIT_END]
    seal = have[have.exit_time > FIT_END]
    print(f"fit {len(fit):,}   sealed {len(seal):,}\n")
    if len(fit) < 500 or len(seal) < 100:
        print("insufficient data"); return

    X = have[XA].values.astype(float)
    m = (have.exit_time <= FIT_END).values
    mu, sd = X[m].mean(0), X[m].std(0) + 1e-9
    Z = (X - mu) / sd
    w = ridge(Z[m], have.R.values[m])
    have["xa"] = w[0] + Z @ w[1:]

    print("cross-asset ridge weights (fit era only):")
    for f, v in sorted(zip(XA, w[1:]), key=lambda x: -abs(x[1]))[:8]:
        print(f"  {f:<32}{v:+.4f}")

    # does the signal even correlate with outcome out of sample?
    fs, ss = have[m], have[~m]
    print(f"\ncorr(xa score, R):  fit {np.corrcoef(fs.xa, fs.R)[0,1]:+.4f}   "
          f"sealed {np.corrcoef(ss.xa, ss.R)[0,1]:+.4f}")
    print(f"is it just the ranker again?  corr(xa, rank_score) = "
          f"{np.corrcoef(have.xa, have.rank_score)[0,1]:+.4f}")

    print(f"\n=== SIZING OVERLAY, sealed era ===")
    print(f"  {'mapping':<28}{'n':>6}{'PF':>8}{'USD':>10}{'maxDD':>9}{'ret/DD':>9}{'avg x':>8}")
    base = summarise(ss, np.ones(len(ss)), "flat size (benchmark)")

    # map the fit-era score distribution onto a multiplier band
    lo, hi = np.percentile(fs.xa, [10, 90])
    for band, lab in (((0.5, 1.5), "0.5x - 1.5x"),
                      ((0.7, 1.3), "0.7x - 1.3x"),
                      ((0.25, 1.75), "0.25x - 1.75x"),
                      ((0.0, 2.0), "0x - 2x (skip worst)")):
        sc = np.clip((ss.xa.values - lo) / max(hi - lo, 1e-9), 0, 1)
        size = band[0] + sc * (band[1] - band[0])
        size = size / size.mean()            # normalise so average exposure matches
        r = summarise(ss, size, lab)
        if r["usd"] > base["usd"] and r["ratio"] > base["ratio"]:
            print(f"      ^ beats flat on BOTH total and ret/DD")

    print("\n=== EXECUTABILITY: multipliers rounded to whole 0.01 lots ===")
    sc = np.clip((ss.xa.values - lo) / max(hi - lo, 1e-9), 0, 1)
    size = 0.5 + sc * 1.0
    size = size / size.mean()
    for base_units in (1, 2, 4):
        u = np.maximum(1, np.round(size * base_units))
        summarise(ss, u / base_units, f"base {base_units}x0.01 lot, rounded")


if __name__ == "__main__":
    main()
