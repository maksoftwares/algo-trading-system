"""V6 defect repair. Two measured bugs, fixed and measured in isolation.

V6 is the only line in this repository with a clean causal validation (PF 1.73
in-sample -> 1.42 walk-forward) AND a proper dual-feed pass, and it informs the
live demo at 0.6x weight. Two defects found 2026-07-26 are independent of the
V8 work that an independent review demolished:

  A  DOUBLE-BOOKING. 42 of 46 recent signals are taken by TWO specialists at the
     same moment - identical entry, exit and R. That is 2x the intended risk on
     one trade (up to $237 on a single signal) and it also burns both K slots, so
     a nominal K=2 book has effective capacity ~1.1.

  B  STARVED THRESHOLD. The ranker cut is a FIXED percentile of 2016-2021
     scores, which is a fixed NUMBER and not a fixed selectivity. Measured
     admission: 0.43x intended in the test era, 0.62x in holdout. The spec asks
     for the top 20%; it delivers ~13%.

  C  DECISION-TIME SLOT LOCKING (found by the review, S2). Slots are reserved at
     the decision bar using confirmation and exit information that does not exist
     yet. Locking belongs at entry.

Discipline imposed by the review, applied here from the start:
  * candidates are processed in ENTRY order, slots settled from a heap of actual
    exits - no state derived from trades that close later
  * Capital P&L is attributed to CAPITAL exit timestamps, never Dukascopy's
  * profit factor is computed on the SAME series as the dollars and the drawdown
  * one frozen configuration, no per-run defaults drifting between callers

Each fix is reported alone and in combination so its individual effect is visible.
"""
import argparse, heapq, itertools, json
import numpy as np, pandas as pd
import engine, specialist
from regime_frontier5 import rolling_thr

FAM = "outputs/SPECIALIST_FAMILY_V6_DEPLOYABLE.json"
DEV_END, TEST_END = engine.DEV_END, engine.TEST_END
HOLD_START = engine.HOLDOUT_START


def scored_candidates():
    """Every V6 specialist's scored candidate population, gates already applied."""
    fam = json.load(open(FAM))
    out = {}
    for lbl, sp in fam["members"].items():
        q = dict(sp); q["_return_candidates"] = True
        c = specialist.run_specialist(q).get("cand")
        if c is None or not len(c):
            continue
        c = c.copy()
        c["spec"] = lbl
        c["pct"] = sp["pct"]
        out[lbl] = c
    return out, fam


def select(c, mode):
    """Threshold the ranker score. frozen = V6 today. rolling = fix B."""
    c = c.sort_values("dec_time").reset_index(drop=True)
    dev = (c.dec_time <= DEV_END).values
    if dev.sum() < 40:
        return c.iloc[0:0]
    if mode == "frozen":
        thr = np.full(len(c), float(np.percentile(c.score.values[dev], c.pct.iloc[0])))
    else:
        thr = rolling_thr(c.score.values, 100 - c.pct.iloc[0])
    return c[c.score.values >= thr]


def execute(sel, C):
    """Realised R on both feeds. V6 mechanics: single stop, horizon close exit.
    Capital exit TIMESTAMP is recorded from the Capital bar, not Dukascopy's."""
    t = C["t"]
    bl, bc, ao = C["bl"], C["bc"], C["ao"]
    ah, ac, bo = C["ah"], C["ac"], C["bo"]
    cap, cap_t = C["cap"], C["cap_t"]
    cbl, cbc, cao = cap["bid_low"].values, cap["bid_close"].values, cap["ask_open"].values
    cah, cac, cbo = cap["ask_high"].values, cap["ask_close"].values, cap["bid_open"].values
    tv = t.values.astype("datetime64[ns]")
    rows = []
    for r in sel.itertuples():
        i1, j, long, stop = int(r.i1), int(r.j), bool(r.long), float(r.stop)
        if long:
            fill = ao[j]; slv = fill - stop
            hit = np.flatnonzero(bl[j:i1] <= slv)
            xi = j + hit[0] if len(hit) else i1 - 1
            xp = slv if len(hit) else bc[xi]
            rd = (xp - fill) / stop - engine.FEE / stop
        else:
            fill = bo[j]; slv = fill + stop
            hit = np.flatnonzero(ah[j:i1] >= slv)
            xi = j + hit[0] if len(hit) else i1 - 1
            xp = slv if len(hit) else ac[xi]
            rd = (fill - xp) / stop - engine.FEE / stop
        rc, cx = np.nan, None
        ei = np.searchsorted(cap_t, tv[j])
        if ei < len(cap_t) and cap_t[ei] == tv[j]:
            e2 = max(np.searchsorted(cap_t, tv[i1 - 1], side="right"), ei + 1)
            if long:
                f2 = cao[ei]; s2 = f2 - stop
                h2 = np.flatnonzero(cbl[ei:e2] <= s2)
                k2 = ei + h2[0] if len(h2) else e2 - 1
                p2 = s2 if len(h2) else cbc[k2]
                rc = (p2 - f2) / stop - engine.FEE / stop
            else:
                f2 = cbo[ei]; s2 = f2 + stop
                h2 = np.flatnonzero(cah[ei:e2] >= s2)
                k2 = ei + h2[0] if len(h2) else e2 - 1
                p2 = s2 if len(h2) else cac[k2]
                rc = (f2 - p2) / stop - engine.FEE / stop
            cx = cap_t[k2]
        rows.append(dict(i=int(r.i), spec=r.spec, long=long, stop=stop,
                         dec_t=r.dec_time, entry_t=t.iloc[j], exit_t=t.iloc[xi],
                         cap_exit_t=cx, r=rd, rc=rc,
                         stop_usd=stop * engine.XAU_USD_PER_PRICE_PER_LOT))
    d = pd.DataFrame(rows)
    if len(d):
        d["cap_exit_t"] = pd.to_datetime(d.cap_exit_t, utc=True)
    return d


def book(d, K, dedup, entry_lock):
    """Portfolio construction. entry_lock=True reserves the slot at ENTRY and
    settles prior positions from a heap of their actual exits - no look-ahead."""
    if dedup:
        # one position per decision bar; V6 has no per-trade score preference
        # beyond the ranker, so keep the highest-scoring specialist
        d = d.sort_values("r", ascending=False).groupby("i", as_index=False).first()
    key = "entry_t" if entry_lock else "dec_t"
    d = d.sort_values(key).reset_index(drop=True)
    pend, keep = [], []
    for row in d.itertuples():
        now = getattr(row, key)
        while pend and pend[0] <= now:
            heapq.heappop(pend)
        if len(pend) >= K:
            continue
        keep.append(row.Index)
        heapq.heappush(pend, row.exit_t)
    return d.loc[keep].reset_index(drop=True)


def stats(d, rcol, tcol, risk=None):
    """PF computed on the SAME dollar series as the P&L and the drawdown."""
    g = d.dropna(subset=[rcol]).copy()
    if not len(g):
        return None
    g["usd"] = g[rcol] * (g.stop_usd if risk is None else risk)
    g = g.sort_values(tcol)
    w, l = g[g.usd > 0], g[g.usd <= 0]
    eq = g.usd.cumsum()
    m = g.groupby(g[tcol].dt.to_period("M")).usd.sum()
    return dict(n=len(g), wr=round(100 * len(w) / len(g), 1),
                pf=round(float(w.usd.sum() / max(-l.usd.sum(), 1e-9)), 3),
                usd=round(float(g.usd.sum())),
                dd=round(float((eq.cummax() - eq).max())),
                green=int((m > 0).sum()), months=len(m),
                worst=round(float(m.min())))


def line(lab, s):
    if not s:
        print(f"  {lab:<30} no trades"); return
    print(f"  {lab:<30}{s['n']:>6}{s['wr']:>7}%{s['pf']:>8}{s['usd']:>9}"
          f"{s['dd']:>8}{str(s['green'])+'/'+str(s['months']):>9}{s['worst']:>8}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, default=2)
    a = ap.parse_args()
    C = specialist.load_context()
    cands, fam = scored_candidates()
    print(f"{fam['family']}  —  {len(cands)} specialists, family K={a.K}\n")

    variants = [
        ("V6 as it runs today", "frozen", False, False),
        ("+ fix A: dedup only", "frozen", True, False),
        ("+ fix B: rolling only", "rolling", False, False),
        ("+ fix C: entry-lock only", "frozen", False, True),
        ("A+B", "rolling", True, False),
        ("A+B+C  (all fixes)", "rolling", True, True),
    ]
    keep_all = {}
    for lab, mode, dedup, elock in variants:
        sel = pd.concat([select(c, mode) for c in cands.values()]).reset_index(drop=True)
        d = execute(sel, C)
        b = book(d, a.K, dedup, elock)
        keep_all[lab] = b

    for feed, rcol, tcol in (("DUKASCOPY", "r", "exit_t"), ("CAPITAL", "rc", "cap_exit_t")):
        print(f"=== {feed}, full history 2016-2026 (PF on the dollar series) ===")
        print(f"  {'variant':<30}{'n':>6}{'WR':>7}{'PF':>8}{'USD':>9}{'maxDD':>8}"
              f"{'green':>9}{'worst':>8}")
        for lab, _, _, _ in variants:
            line(lab, stats(keep_all[lab], rcol, tcol))
        print()

    print("=== CAPITAL, sealed holdout 2025-01 onward ===")
    print(f"  {'variant':<30}{'n':>6}{'WR':>7}{'PF':>8}{'USD':>9}{'maxDD':>8}"
          f"{'green':>9}{'worst':>8}")
    for lab, _, _, _ in variants:
        b = keep_all[lab]
        line(lab, stats(b[b.cap_exit_t >= HOLD_START], "rc", "cap_exit_t"))

    print("\n=== DEFECT A: how much double-booking was there? ===")
    base = keep_all["V6 as it runs today"]
    g = base.groupby("i").size()
    print(f"  {len(base)} executed legs over {len(g)} distinct signals")
    print(f"  signals taken more than once: {int((g>1).sum())} "
          f"({100*(g>1).mean():.1f}%)  max legs on one signal: {int(g.max())}")
    dupes = base[base.i.isin(g[g > 1].index)]
    print(f"  peak risk on a single signal: ${dupes.groupby('i').stop_usd.sum().max():.2f}")

    print("\n=== DEFECT B: realised selectivity, frozen vs rolling ===")
    print(f"  {'specialist':<26}{'pct':>5}{'intended':>10}{'frozen dev/test/hold':>24}"
          f"{'rolling dev/test/hold':>24}")
    for lbl, c in cands.items():
        row = [lbl, int(c.pct.iloc[0]), 100 - int(c.pct.iloc[0])]
        cells = []
        for mode in ("frozen", "rolling"):
            s = select(c, mode)
            era = lambda x: np.where(x <= DEV_END, "dev",
                                     np.where(x <= TEST_END, "test", "hold"))
            tot = pd.Series(era(c.dec_time)).value_counts()
            got = pd.Series(era(s.dec_time)).value_counts() if len(s) else pd.Series(dtype=int)
            cells.append("/".join(f"{100*got.get(e,0)/max(tot.get(e,1),1):.0f}%"
                                  for e in ("dev", "test", "hold")))
        print(f"  {row[0]:<26}{row[1]:>5}{row[2]:>9}%{cells[0]:>24}{cells[1]:>24}")

    for lab, b in keep_all.items():
        b.to_csv(f"outputs/V6FIX_{lab.split(':')[0].strip().replace(' ','_').replace('+','')}"
                 f".csv", index=False)
    print("\ntrade files written to outputs/V6FIX_*.csv")


if __name__ == "__main__":
    main()
