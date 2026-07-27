"""V8 sized in real 0.01-lot increments — the drawdown you would actually get.

Every V8 figure so far assumes a constant $10 risk per trade. That needs
fractional lots: the median trade wants 1.44 lots and the 5th percentile 0.30,
neither of which is a multiple of 0.01. So the reported drawdown (-80% from risk
normalisation) is not a number this account can execute.

Units: 0.01 lot XAUUSD = 1 oz, so a $1 price move = $1 P&L at 0.01 lot. A trade
with stop distance `stop` therefore risks exactly `stop` dollars per 0.01 lot.

    units = max(1, floor(target_risk / stop))      # units of 0.01 lot
    risk  = units * stop                            # actual dollars at risk

Two consequences the idealised model hides:
  1. WIDE STOPS OVER-RISK. When stop > target, the minimum lot is already too
     big and there is no way down. Stops here run to $234.
  2. STREAK SIZING MAY NOT EXIST. Halving or quartering a 0.01-lot position is
     impossible. The rule only bites when the base position is >= 0.02 (half) or
     >= 0.04 (quarter) units.

Both are measured below, along with the option a real risk desk would take:
refuse any trade whose minimum-lot risk exceeds a cap.
"""
import argparse, itertools
import numpy as np, pandas as pd

TRADES = "outputs/GOLD_V8_DUALFEED_TRADES.CSV".replace(".CSV", ".csv")


def size_real(t, target, max_risk):
    """Integer 0.01-lot units, streak multiplier applied where representable."""
    stop = t.stop.values
    base = np.maximum(1, np.floor(target / stop)).astype(int)
    units = np.maximum(1, np.floor(base * t["size"].values)).astype(int)
    risk = units * stop
    keep = np.ones(len(t), bool) if max_risk is None else (stop <= max_risk)
    out = t.assign(units=units, risk=risk, keep=keep)
    out["usd_real"] = out.rc * out.risk          # Capital feed, real sizing
    return out[out.keep].copy(), out


def rep(t, col, mons, lab):
    g = t[t.m.isin(mons)].dropna(subset=["rc"])
    if not len(g):
        return None
    r = (g.rc * g["size"]).values
    w, l = r[r > 0], r[r <= 0]
    m = g.groupby("m")[col].sum().reindex(mons, fill_value=0)
    eq = g.sort_values("exit_t")[col].cumsum()
    d = dict(lab=lab, n=len(g), wr=round(100 * len(w) / len(r), 1),
             pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 2),
             usd=round(float(g[col].sum())),
             dd=round(float((eq.cummax() - eq).max())),
             green=int((m > 0).sum()), tot=len(mons), worst=round(float(m.min())))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", default="outputs/GOLD_V8_DUALFEED_TRADES.csv")
    a_ = ap.parse_args()
    t = pd.read_csv(a_.trades, parse_dates=["dec_t", "entry_t", "exit_t"])
    t["m"] = t.exit_t.dt.to_period("M")
    M5 = pd.period_range("2021-07", "2026-06", freq="M")
    M18 = pd.period_range("2025-01", "2026-06", freq="M")

    print("=== SIZING FEASIBILITY AT 0.01-LOT GRANULARITY ===")
    for target in (10, 20, 50):
        base = np.maximum(1, np.floor(target / t.stop.values)).astype(int)
        forced = (t.stop.values > target)
        print(f"  target ${target:>3}/trade: median {np.median(base):>4.0f} units "
              f"(={np.median(base)*0.01:.2f} lot)   "
              f"trades forced to over-risk: {100*forced.mean():>4.1f}%   "
              f"streak-half representable on {100*(base>=2).mean():>4.1f}%, "
              f"quarter on {100*(base>=4).mean():>4.1f}%")
    print()

    print("=== WHAT YOU ACTUALLY GET (Capital feed, real 0.01-lot sizing) ===")
    print(f"{'config':<34}{'n':>6}{'WR':>7}{'PF':>7}{'USD':>9}{'maxDD':>8}"
          f"{'green':>9}{'worst':>8}")
    rows = []
    for target, cap in itertools.product((10, 20, 50), (None, 20, 30, 50)):
        sel, _ = size_real(t, target, cap)
        d = rep(sel, "usd_real", M5, f"${target}/trade, cap {cap or 'none'}")
        if not d:
            continue
        rows.append((target, cap, d))
        print(f"{d['lab']:<34}{d['n']:>6}{d['wr']:>6}%{d['pf']:>7}{d['usd']:>9}"
              f"{d['dd']:>8}{str(d['green'])+'/'+str(d['tot']):>9}{d['worst']:>8}")

    print("\n=== IDEALISED (what was reported before) vs REAL, 5 years ===")
    t2 = t.copy()
    t2["usd_ideal"] = t2.rc * t2["size"] * 10.0
    di = rep(t2, "usd_ideal", M5, "idealised $10 constant risk")
    print(f"  idealised : PF {di['pf']}  ${di['usd']}  maxDD ${di['dd']}  "
          f"green {di['green']}/{di['tot']}  worst ${di['worst']}")
    best = min(rows, key=lambda x: x[2]["dd"] / max(x[2]["usd"], 1))
    d = best[2]
    print(f"  real      : PF {d['pf']}  ${d['usd']}  maxDD ${d['dd']}  "
          f"green {d['green']}/{d['tot']}  worst ${d['worst']}   [{d['lab']}]")

    print("\n=== ACCOUNT SIZING: drawdown as % of capital ===")
    print(f"{'config':<30}{'maxDD':>8}{'on $1k':>9}{'on $5k':>9}{'on $10k':>9}{'verdict':>26}")
    for target, cap, d in rows:
        p1, p5, p10 = 100*d['dd']/1000, 100*d['dd']/5000, 100*d['dd']/10000
        v = "OK on $10k" if p10 <= 10 else ("needs >$10k" if p10 <= 30 else "too big")
        if p1 <= 10:
            v = "OK even on $1k"
        elif p5 <= 10:
            v = "OK on $5k"
        print(f"{d['lab']:<30}{d['dd']:>8}{p1:>8.0f}%{p5:>8.0f}%{p10:>8.0f}%{v:>26}")

    print("\n=== SEALED 18 MONTHS, most conservative executable config ===")
    sel, _ = size_real(t, 10, 30)
    d = rep(sel, "usd_real", M18, "$10/trade, skip stops > $30")
    print(f"  n {d['n']}  WR {d['wr']}%  PF {d['pf']}  ${d['usd']}  "
          f"maxDD ${d['dd']}  green {d['green']}/{d['tot']}  worst ${d['worst']}")


if __name__ == "__main__":
    main()
