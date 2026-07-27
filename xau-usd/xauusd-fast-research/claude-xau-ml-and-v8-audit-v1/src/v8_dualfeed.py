"""Dual-feed validation of GOLD V8 — the gate the work order requires.

Every V8 number so far is Dukascopy-only. The work order is explicit: single-feed
discovery is invalid, and every gate must pass on BOTH the Dukascopy M5 signal
feed and the Capital.com execution feed. V6 cleared that bar; V8 has never been
tested against it.

Method: signals are generated exactly as V8 generates them (Dukascopy decides
WHEN and WHICH WAY), then the trade is executed a second time against Capital
bars — Capital fill, Capital stop hit, Capital horizon exit — with the same stop
distance. Any trade whose entry bar has no Capital match is DROPPED and counted,
because in live trading that is a signal the execution venue could not act on.

What would fail V8:
  - Capital PF materially below Dukascopy PF (the edge is a data artifact)
  - a large share of dropped bars (signals unexecutable at the venue)
  - the two feeds disagreeing on individual trade outcomes more than spread
    differences can explain
"""
import argparse
import numpy as np, pandas as pd
import engine, specialist
import gold_v8 as V
import gold_v9_partial as P


def build_with_horizon_end():
    """V8 sleeves, additionally recording each trade's horizon-end timestamp so
    the Capital leg can be bounded identically."""
    C = specialist.load_context()
    t = C["t"]
    parts = []
    for hn, hz in V.HORIZONS.items():
        for gn, gate, pct in V.GATES:
            c = V.candidates(C, hz, gate, pct)
            if not len(c):
                continue
            i1 = np.minimum(c.i.values + 1 + hz, C["n"]) - 1
            c = c.assign(sleeve=f"{hn}_{gn}", hz=hz,
                         hz_end=t.iloc[i1].values)
            parts.append(c)
    a = P.assemble(parts)
    a["hz_end"] = pd.to_datetime(a.hz_end, utc=True)
    return a, C


def capital_leg(a, C):
    """Re-execute each trade on Capital bars: Capital fill, Capital stop, Capital
    horizon close. Stop distance is unchanged (it is set by Dukascopy ATR at the
    decision bar, which both venues observe)."""
    cap, cap_t = C["cap"], C["cap_t"]
    cbo, cbl, cbc = cap["bid_open"].values, cap["bid_low"].values, cap["bid_close"].values
    cao, cah, cac = cap["ask_open"].values, cap["ask_high"].values, cap["ask_close"].values
    rc, dropped = [], 0
    ent = a.entry_t.values.astype("datetime64[ns]")
    end = a.hz_end.values.astype("datetime64[ns]")
    for k, row in enumerate(a.itertuples()):
        ei = np.searchsorted(cap_t, ent[k])
        if ei >= len(cap_t) or cap_t[ei] != ent[k]:
            rc.append(np.nan); dropped += 1; continue
        e2 = max(np.searchsorted(cap_t, end[k], side="right"), ei + 1)
        stop = row.stop
        if row.long:
            fill = cao[ei]; slv = fill - stop
            hit = np.flatnonzero(cbl[ei:e2] <= slv)
            xi = ei + hit[0] if len(hit) else e2 - 1
            xp = slv if len(hit) else cbc[xi]
            r = (xp - fill) / stop - engine.FEE / stop
        else:
            fill = cbo[ei]; slv = fill + stop
            hit = np.flatnonzero(cah[ei:e2] >= slv)
            xi = ei + hit[0] if len(hit) else e2 - 1
            xp = slv if len(hit) else cac[xi]
            r = (fill - xp) / stop - engine.FEE / stop
        rc.append(r)
    a = a.assign(rc=rc)
    a["src"] = a.r * a["size"]                       # Dukascopy, sized
    a["crc"] = a.rc * a["size"]                      # Capital, sized
    a["usd_cap"] = a.crc * V.RISK_USD
    return a, dropped


def stat(x, col, usd):
    g = x.dropna(subset=[col])
    if not len(g):
        return None
    r = g[col].values
    w, l = r[r > 0], r[r <= 0]
    m = g.groupby(g.exit_t.dt.to_period("M"))[usd].sum()
    eq = g.sort_values("exit_t")[usd].cumsum()
    return dict(n=len(g), wr=round(100 * len(w) / len(r), 1),
                pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 2),
                usd=round(float(g[usd].sum())),
                dd=round(float((eq.cummax() - eq).max())),
                green=f"{int((m>0).sum())}/{len(m)}")


def main():
    ap = argparse.ArgumentParser()
    a_ = ap.parse_args()
    a, C = build_with_horizon_end()
    a, dropped = capital_leg(a, C)
    print("GOLD V8 — DUAL-FEED VALIDATION\n")
    print(f"signals generated on Dukascopy, executed on BOTH feeds")
    print(f"trades: {len(a)}   Capital bar missing for {dropped} "
          f"({100*dropped/len(a):.1f}%) -> dropped as unexecutable\n")

    wins = [("last 12 months", pd.period_range("2025-07", "2026-06", freq="M")),
            ("sealed 18 months", pd.period_range("2025-01", "2026-06", freq="M")),
            ("last 5 years", pd.period_range("2021-07", "2026-06", freq="M")),
            ("full 2016-2026", pd.period_range("2016-08", "2026-06", freq="M"))]
    a["m"] = a.exit_t.dt.to_period("M")
    print(f"{'window':<20}{'feed':<12}{'n':>6}{'WR':>7}{'PF':>7}{'USD':>9}{'maxDD':>8}{'green':>9}")
    for lab, mons in wins:
        g = a[a.m.isin(mons)]
        d = stat(g, "src", "usd")
        c = stat(g, "crc", "usd_cap")
        if d:
            print(f"{lab:<20}{'Dukascopy':<12}{d['n']:>6}{d['wr']:>6}%{d['pf']:>7}"
                  f"{d['usd']:>9}{d['dd']:>8}{d['green']:>9}")
        if c:
            print(f"{'':<20}{'CAPITAL':<12}{c['n']:>6}{c['wr']:>6}%{c['pf']:>7}"
                  f"{c['usd']:>9}{c['dd']:>8}{c['green']:>9}")
        print()

    g = a.dropna(subset=["crc"])
    print("=== AGREEMENT BETWEEN FEEDS (matched trades) ===")
    agree = np.sign(g.src) == np.sign(g.crc)
    print(f"  same win/loss outcome : {100*agree.mean():.1f}% of {len(g)} trades")
    print(f"  correlation of R      : {np.corrcoef(g.src, g.crc)[0,1]:.4f}")
    print(f"  mean R  Duka {g.src.mean():+.4f}   Capital {g.crc.mean():+.4f}   "
          f"gap {g.crc.mean()-g.src.mean():+.4f}")
    big = g[g.src >= 3]
    print(f"  on the >=3R winners   : Duka {big.src.mean():.2f}R  "
          f"Capital {big.crc.mean():.2f}R  ({len(big)} trades)")
    print()
    print("=== VERDICT ===")
    c5 = stat(a[a.m.isin(wins[2][1])], "crc", "usd_cap")
    d5 = stat(a[a.m.isin(wins[2][1])], "src", "usd")
    ratio = c5["pf"] / d5["pf"] if d5["pf"] else 0
    print(f"  5-year PF: Dukascopy {d5['pf']}  Capital {c5['pf']}  "
          f"(Capital retains {100*ratio:.0f}%)")
    ok = (c5["pf"] >= 1.5 and dropped / len(a) < 0.05 and agree.mean() > 0.9)
    print(f"  {'PASS - V8 survives on the execution feed' if ok else 'FAIL - see numbers above'}")
    a.to_csv("outputs/GOLD_V8_DUALFEED_TRADES.csv", index=False)


if __name__ == "__main__":
    main()
