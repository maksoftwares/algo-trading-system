"""Can a model pick WHICH open V60 positions to cut before they reach the stop?

e1 established the unconditional answer is no: positions that are down have
significantly POSITIVE forward P&L (+$3.57 at 0.5h, t 4.79), so cutting losers as
a class destroys money. That is a base rate, not a verdict on modelling - a model
conditions on far more than unrealised P&L, and the question the user asked is
whether the recoverers can be told apart from the non-recoverers.

So: build a proper mid-flight decision dataset and train on it.

  observation  (trade, checkpoint) for every position still open at that time
  target       forward P&L from the checkpoint to the position's actual exit
  policy       close now if predicted forward P&L < -threshold
  execution    sequential - walk checkpoints in order, close at the FIRST trigger
  pricing      exact. Implied size is 1.0 unit on every trade, so closing at the
               checkpoint mid realises (mid - entry) * sign. Round-trip cost is
               unchanged by exiting early (still one open, one close), so the
               baseline cost already in fee_stress_pnl_usd carries over.

Walk-forward is causal: train only on trades that CLOSED before the test year
minus a 48h purge. Gates are the ones that matter for the stated goal - net P&L
must not fall, and max drawdown must actually improve, since reducing drawdown is
the entire point of asking.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import features as F

PNL = F.PNL
PURGE = pd.Timedelta(hours=48)
CHECKS = [0.5, 1, 2, 4, 8, 24]
PARAMS = dict(max_depth=3, max_iter=250, learning_rate=0.05,
              min_samples_leaf=40, l2_regularization=1.0, random_state=0)
FEATS = ["unreal", "mae", "mfe", "h", "unreal_minus_mae", "ret_since",
         "atr_ratio", "rv_now", "ret_1h_now", "ret_4h_now", "dist_hi", "dist_lo",
         "ms_flow_now", "ms_eff_now", "hour", "is_long", "is_core", "dur_so_far"]


def build():
    led = F.load_ledger()
    mkt = F.load_market()
    t = mkt.t.values.astype("datetime64[ns]")
    mc, mh, ml = mkt.mid_close.values, mkt.mid_high.values, mkt.mid_low.values
    atr, ema = mkt.atr144.values, mkt.ema144.values
    csm = np.concatenate([[0.], np.nancumsum(np.nan_to_num(mkt.tick_signed_move.values))])
    cpe = np.concatenate([[0.], np.nancumsum(np.nan_to_num(mkt.price_efficiency_5m.values))])
    atr_med = pd.Series(atr).rolling(2016, min_periods=500).median().shift(1).values
    hi24 = pd.Series(mh).rolling(288, min_periods=20).max().values
    lo24 = pd.Series(ml).rolling(288, min_periods=20).min().values

    e_idx = np.searchsorted(t, led.entry_time.values.astype("datetime64[ns]"), "right") - 1
    x_idx = np.searchsorted(t, led.exit_time.values.astype("datetime64[ns]"), "right") - 1
    ep, sgn = led.entry_price.values, led.direction_sign.values
    xp = led.exit_price.values
    rows = []
    for k in np.flatnonzero((e_idx >= 2016) & (x_idx > e_idx)):
        i0, i1 = e_idx[k], x_idx[k]
        a0 = atr[i0]
        if not np.isfinite(a0) or a0 <= 0:
            continue
        s, e = sgn[k], ep[k]
        for h in CHECKS:
            j = i0 + int(h * 12)
            if j >= i1:
                continue
            seg_lo, seg_hi = ml[i0:j + 1], mh[i0:j + 1]
            worst = seg_lo.min() if s > 0 else seg_hi.max()
            best = seg_hi.max() if s > 0 else seg_lo.min()
            a = atr[j] if np.isfinite(atr[j]) and atr[j] > 0 else a0
            rows.append(dict(
                k=k, h=h,
                unreal=(mc[j] - e) * s / a0,
                mae=(worst - e) * s / a0,
                mfe=(best - e) * s / a0,
                unreal_minus_mae=((mc[j] - worst) * s) / a0,
                ret_since=(mc[j] - mc[max(j - 12, 0)]) * s / a,
                atr_ratio=a / atr_med[j] if np.isfinite(atr_med[j]) and atr_med[j] > 0 else np.nan,
                rv_now=float(np.std(np.diff(mc[max(j - 12, 0):j + 1]))) / a,
                ret_1h_now=(mc[j] - mc[max(j - 12, 0)]) / a,
                ret_4h_now=(mc[j] - mc[max(j - 48, 0)]) / a,
                dist_hi=(hi24[j] - mc[j]) / a,
                dist_lo=(mc[j] - lo24[j]) / a,
                ms_flow_now=s * (csm[j + 1] - csm[max(j - 12, 0)]) / 12,
                ms_eff_now=(cpe[j + 1] - cpe[max(j - 12, 0)]) / 12,
                hour=int(pd.Timestamp(t[j]).hour),
                is_long=float(s > 0), is_core=float(led.is_core.values[k]),
                dur_so_far=h,
                cut_usd=(mc[j] - e) * s,                    # gross if we cut now
                fwd_usd=(xp[k] - mc[j]) * s,                # what cutting forfeits
                final_pnl=led[PNL].values[k],
                entry_time=led.entry_time.values[k],
                exit_time=led.exit_time.values[k],
                sleeve=led.source_id.values[k]))
    d = pd.DataFrame(rows)
    d["entry_time"] = pd.to_datetime(d.entry_time, utc=True)
    d["exit_time"] = pd.to_datetime(d.exit_time, utc=True)
    return d, led


def metrics(pnl, exit_t):
    p = np.asarray(pnl, float)
    o = np.argsort(np.asarray(exit_t))
    eq = np.cumsum(p[o])
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else 1.0
    w, l = p[p > 0], p[p <= 0]
    return dict(n=len(p), net=float(p.sum()), dd=max(dd, 1e-9),
                ratio=float(p.sum() / max(dd, 1e-9)),
                wr=100 * len(w) / max(len(p), 1),
                pf=float(w.sum() / max(-l.sum(), 1e-9)))


def main():
    d, led = build()
    print(f"{d.k.nunique():,} trades, {len(d):,} mid-flight decision points\n")

    # causal walk-forward on the checkpoint set
    pred = np.full(len(d), np.nan)
    for y in range(2021, int(d.exit_time.dt.year.max()) + 1):
        cut = pd.Timestamp(f"{y}-01-01", tz="UTC") - PURGE
        tr = (d.exit_time < cut).values
        te = (d.entry_time.dt.year == y).values
        if tr.sum() < 300 or te.sum() < 20:
            continue
        yy = np.clip(d.fwd_usd.values[tr], *np.quantile(d.fwd_usd.values[tr], [.01, .99]))
        m = HistGradientBoostingRegressor(**PARAMS).fit(d[FEATS][tr], yy)
        pred[te] = m.predict(d[FEATS][te])
    d = d.assign(pred=pred)
    ev = d[np.isfinite(d.pred)].copy()
    print(f"scored decision points: {len(ev):,} on {ev.k.nunique():,} trades")
    print(f"corr(pred, actual forward $) = {ev.pred.corr(ev.fwd_usd):.4f}\n")

    # baseline: every trade runs to its natural exit
    tr_all = led.loc[sorted(ev.k.unique())]
    base = metrics(tr_all[PNL].values, tr_all.exit_time.values)
    print(f"BASELINE  n {base['n']}  net ${base['net']:.0f}  maxDD ${base['dd']:.0f}"
          f"  net/DD {base['ratio']:.2f}  WR {base['wr']:.1f}%  PF {base['pf']:.2f}\n")

    print("policy: close at the FIRST checkpoint where predicted forward $ < -thr")
    print(f"\n{'thr':>7}{'cuts':>7}{'net':>10}{'maxDD':>9}{'net/DD':>8}"
          f"{'WR':>7}{'PF':>7}{'vs base':>10}")
    ev = ev.sort_values(["k", "h"])
    for thr in (0.0, 1.0, 2.0, 4.0, 8.0, 16.0):
        trig = ev[ev.pred < -thr]
        first = trig.groupby("k").first()
        pnl, xt = [], []
        for k, r in led.loc[sorted(ev.k.unique())].iterrows():
            if k in first.index:
                f = first.loc[k]
                # realised = gross at cut, minus the same round-trip cost
                cost = r[PNL] - (r.exit_price - r.entry_price) * r.direction_sign
                pnl.append(f.cut_usd + cost)
                xt.append(r.entry_time + pd.Timedelta(hours=float(f.h)))
            else:
                pnl.append(r[PNL])
                xt.append(r.exit_time)
        m = metrics(pnl, np.array(xt, dtype="datetime64[ns]"))
        print(f"{thr:>7.1f}{len(first):>7}{m['net']:>10.0f}{m['dd']:>9.0f}"
              f"{m['ratio']:>8.2f}{m['wr']:>7.1f}{m['pf']:>7.2f}"
              f"{m['net']-base['net']:>+10.0f}")

    print("\nwhat the model actually forecasts, by predicted decile")
    q = pd.qcut(ev.pred, 10, labels=False, duplicates="drop")
    g = ev.groupby(q).agg(n=("fwd_usd", "size"), pred=("pred", "mean"),
                          actual=("fwd_usd", "mean"),
                          pct_neg=("fwd_usd", lambda s: 100 * float((s < 0).mean())))
    print(f"{'decile':>7}{'n':>7}{'predicted $':>13}{'actual $':>11}{'% negative':>12}")
    for i, r in g.iterrows():
        print(f"{int(i):>7}{int(r.n):>7}{r.pred:>13.2f}{r.actual:>11.2f}{r.pct_neg:>12.1f}")
    # The one result that favours cutting: maxDD falls a lot. Is that robust, or
    # is it one lucky path? maxDD is a single order statistic and very noisy, so
    # check it per year, and ask whether levering the cut book back up to the
    # baseline's drawdown would beat the baseline.
    print("\n" + "=" * 72)
    print("Is the drawdown reduction robust enough to lever back up?")
    print("=" * 72)
    sub = led.loc[sorted(ev.k.unique())]
    for thr in (0.0, 1.0, 2.0):
        first = ev[ev.pred < -thr].groupby("k").first()
        pnl, xt = [], []
        for k, r in sub.iterrows():
            if k in first.index:
                f = first.loc[k]
                cost = r[PNL] - (r.exit_price - r.entry_price) * r.direction_sign
                pnl.append(f.cut_usd + cost)
                xt.append(r.entry_time + pd.Timedelta(hours=float(f.h)))
            else:
                pnl.append(r[PNL]); xt.append(r.exit_time)
        cut_df = pd.DataFrame({"pnl": pnl, "xt": pd.to_datetime(pd.Series(xt), utc=True)})
        cut_df["y"] = cut_df.xt.dt.year
        b = pd.DataFrame({"pnl": sub[PNL].values,
                          "xt": pd.to_datetime(sub.exit_time.values, utc=True)})
        b["y"] = b.xt.dt.year
        mb, mc_ = metrics(b.pnl.values, b.xt.values), metrics(cut_df.pnl.values, cut_df.xt.values)
        lever = mb["dd"] / mc_["dd"]
        print(f"\n  threshold {thr}: cuts {len(first)}")
        print(f"    net ${mc_['net']:.0f} vs ${mb['net']:.0f}   "
              f"maxDD ${mc_['dd']:.0f} vs ${mb['dd']:.0f}   "
              f"net/DD {mc_['ratio']:.2f} vs {mb['ratio']:.2f}")
        print(f"    levered {lever:.2f}x to match baseline drawdown: "
              f"${mc_['net']*lever:.0f} vs ${mb['net']:.0f} "
              f"({mc_['net']*lever-mb['net']:+.0f})")
        print(f"    {'year':<6}{'base net':>10}{'cut net':>10}{'delta':>9}"
              f"{'base DD':>9}{'cut DD':>8}")
        for y in sorted(b.y.unique()):
            bb, cc = b[b.y == y], cut_df[cut_df.y == y]
            if not len(bb) or not len(cc):
                continue
            m1, m2 = metrics(bb.pnl.values, bb.xt.values), metrics(cc.pnl.values, cc.xt.values)
            print(f"    {y:<6}{m1['net']:>10.0f}{m2['net']:>10.0f}"
                  f"{m2['net']-m1['net']:>+9.0f}{m1['dd']:>9.0f}{m2['dd']:>8.0f}")

    d.to_parquet("outputs/V60_EARLY_EXIT_DECISIONS.parquet")


if __name__ == "__main__":
    main()
