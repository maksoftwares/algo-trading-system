"""Causal walk-forward on V6.1's one remaining free parameter: selectivity level.

Fixes A (dedup) and C (entry-time slot locking) are correctness repairs and are
always on. Fix B replaces the frozen dev-era percentile with a rolling quantile -
also correctness, since a frozen threshold keeps drifting. What B leaves behind is
a genuine parameter: HOW selective to be. `shrink` scales the spec's keep-rate,
so shrink=1.0 trades at the documented rate and 0.5 trades half as often.

Picking shrink=0.70 by comparing five values on the full sample is selection. This
walks it forward instead.

OBJECTIVE, DECLARED BEFORE RUNNING: for evaluation year Y, choose the shrink with
the best prior-window return per dollar of drawdown (dollars/maxDD), requiring at
least 50 prior trades. Not green months, not PF - the review criticised an
objective chosen after inspecting the sample, so this is the plain risk-desk
metric and it is fixed here in writing.

CAUSALITY, per the review's required standard:
  * the ranker is the FROZEN V8 model trained through 2021, so evaluation starts
    at 2022 - earlier years would use a ranker that saw them
  * the rolling threshold is backward-looking by construction (verified elsewhere
    against a naive loop, exact match)
  * trades are assigned to years by ENTRY time, never exit time, so a position
    already open when year Y's parameter was chosen is not credited to Y
  * ONE continuous position book across the whole span - slot state is carried
    along the path actually traded, never rebuilt retrospectively per year
  * slots are reserved at ENTRY and released from a heap of actual exits
  * Capital P&L is attributed to Capital exit timestamps
  * profit factor is computed on the same dollar series as P&L and drawdown
"""
import argparse, heapq, json
import numpy as np, pandas as pd
import engine, specialist, v6_fix as V
from regime_frontier5 import rolling_thr

FIRST_YEAR = 2022                      # frozen ranker trained through 2021
SHRINKS = (1.0, 0.85, 0.70, 0.55, 0.40)
MIN_PRIOR = 50


def build_universe(C, cands):
    """Every candidate, executed once, with a per-shrink selection flag. The
    rolling threshold is causal so a single pass covers all years."""
    parts = []
    for lbl, c in cands.items():
        c = c.sort_values("dec_time").reset_index(drop=True)
        keep_spec = 100 - c.pct.iloc[0]
        flags = {}
        for s in SHRINKS:
            thr = rolling_thr(c.score.values, keep_spec * s)
            flags[s] = c.score.values >= thr
        d = V.execute(c, C)
        for s in SHRINKS:
            d[f"sel{int(round(s*100))}"] = flags[s]   # int key: itertuples cannot
                                                      # reach an attribute with a dot
        parts.append(d)
    u = pd.concat(parts).reset_index(drop=True)
    u["entry_year"] = u.entry_t.dt.year
    return u


def run_book(u, shrink_for_year, K=2):
    """One continuous entry-order book. shrink_for_year maps year -> shrink; a
    candidate is eligible only under the shrink active in its own entry year."""
    u = u.sort_values(["entry_t", "i"]).reset_index(drop=True)
    # dedup is deterministic per decision bar once eligibility is known
    elig = np.zeros(len(u), bool)
    for k, row in enumerate(u.itertuples()):
        s = shrink_for_year.get(row.entry_year)
        if s is None:
            continue
        elig[k] = bool(getattr(row, f"sel{int(round(s*100))}"))
    d = u[elig].copy()
    if not len(d):
        return d
    # one position per decision bar: keep the strongest-scoring specialist
    d = d.sort_values(["i", "r"], ascending=[True, False]).groupby("i", as_index=False).first()
    d = d.sort_values("entry_t").reset_index(drop=True)
    pend, keep = [], []
    for row in d.itertuples():
        while pend and pend[0] <= row.entry_t:
            heapq.heappop(pend)
        if len(pend) >= K:
            continue
        keep.append(row.Index)
        heapq.heappush(pend, row.exit_t)
    return d.loc[keep].reset_index(drop=True)


def score_prior(b, year):
    """Return per dollar of drawdown on trades that CLOSED before `year`."""
    p = b[b.cap_exit_t.dt.year < year].dropna(subset=["rc"])
    if len(p) < MIN_PRIOR:
        return -1e9
    usd = (p.rc * p.stop_usd)
    eq = usd.cumsum()
    dd = max(float((eq.cummax() - eq).max()), 1.0)
    return float(usd.sum()) / dd


def report(b, lab, mons=None):
    g = b.dropna(subset=["rc"]).copy()
    if not len(g):
        print(f"  {lab:<34} no trades"); return None
    g["usd"] = g.rc * g.stop_usd
    g = g.sort_values("cap_exit_t")
    if mons is not None:
        g = g[g.cap_exit_t.dt.to_period("M").isin(mons)]
        if not len(g):
            print(f"  {lab:<34} no trades"); return None
    w, l = g[g.usd > 0], g[g.usd <= 0]
    eq = g.usd.cumsum()
    m = g.groupby(g.cap_exit_t.dt.to_period("M")).usd.sum()
    d = dict(n=len(g), wr=round(100 * len(w) / len(g), 1),
             pf=round(float(w.usd.sum() / max(-l.usd.sum(), 1e-9)), 3),
             usd=round(float(g.usd.sum())), dd=round(float((eq.cummax() - eq).max())),
             green=int((m > 0).sum()), months=len(m), worst=round(float(m.min())))
    print(f"  {lab:<34}{d['n']:>6}{d['wr']:>7}%{d['pf']:>8}{d['usd']:>9}"
          f"{d['dd']:>8}{str(d['green'])+'/'+str(d['months']):>9}{d['worst']:>8}")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, default=2)
    a = ap.parse_args()
    C = specialist.load_context()
    cands, fam = V.scored_candidates()
    u = build_universe(C, cands)
    last = int(u.entry_year.max())
    print(f"universe {len(u)} candidate-legs, entry years {int(u.entry_year.min())}-{last}")
    print(f"objective: prior return/drawdown, min {MIN_PRIOR} prior trades, "
          f"shrinks {SHRINKS}\n")

    # fixed-shrink books, used only to score PRIOR windows
    fixed = {s: run_book(u, {y: s for y in range(1900, 2100)}, a.K) for s in SHRINKS}

    chosen, log = {}, []
    for year in range(FIRST_YEAR, last + 1):
        best, bs = None, -1e18
        for s in SHRINKS:
            sc = score_prior(fixed[s], year)
            if sc > bs:
                best, bs = s, sc
        chosen[year] = best if best is not None else 1.0
        log.append((year, chosen[year], round(bs, 2)))
        print(f"  {year}: chose shrink {chosen[year]}  (prior return/DD {bs:.2f})")

    wf = run_book(u, chosen, a.K)
    wf = wf[wf.entry_year >= FIRST_YEAR]

    print(f"\n=== WALK-FORWARD {FIRST_YEAR}-{last}, Capital feed, entry-year attribution ===")
    print(f"  {'variant':<34}{'n':>6}{'WR':>7}{'PF':>8}{'USD':>9}{'maxDD':>8}"
          f"{'green':>9}{'worst':>8}")
    wfd = report(wf, "walk-forward (shrink chosen causally)")
    for s in SHRINKS:
        b = fixed[s]
        report(b[b.entry_year >= FIRST_YEAR], f"fixed shrink {s}")
    # and V6 exactly as it runs, over the same window
    frozen = pd.concat([V.select(c, "frozen") for c in cands.values()]).reset_index(drop=True)
    fd = V.execute(frozen, C)
    fb = V.book(fd, a.K, False, False)
    fb["entry_year"] = fb.entry_t.dt.year
    report(fb[fb.entry_year >= FIRST_YEAR], "V6 as it runs today (no fixes)")

    print("\n=== PER YEAR (walk-forward) ===")
    wf = wf.copy(); wf["usd"] = wf.rc * wf.stop_usd
    py = wf.dropna(subset=["rc"]).groupby(wf.entry_year).agg(
        n=("usd", "size"), wr=("usd", lambda x: round(100 * (x > 0).mean(), 1)),
        pf=("usd", lambda x: round(x[x > 0].sum() / max(-x[x <= 0].sum(), 1e-9), 2)),
        usd=("usd", lambda x: round(x.sum())))
    print(py.to_string())
    json.dump(dict(picks=log, walkforward=wfd,
                   fixed={str(s): report(fixed[s][fixed[s].entry_year >= FIRST_YEAR],
                                         f"_{s}") for s in SHRINKS}),
              open("outputs/V6_SHRINK_WALKFORWARD.json", "w"), indent=1, default=str)
    wf.to_csv("outputs/V6_SHRINK_WALKFORWARD_TRADES.csv", index=False)


if __name__ == "__main__":
    main()
