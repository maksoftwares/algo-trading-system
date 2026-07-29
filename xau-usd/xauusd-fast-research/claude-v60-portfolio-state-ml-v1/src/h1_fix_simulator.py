"""Model the proposed V60 fixes and measure each one's contribution.

NOTHING HERE MODIFIES THE DEPLOYED SYSTEM. This is a simulator in this research
package. The live config, runtime, terminals and frozen packages are untouched;
the fixes are expressed as parameters to a replay of the real V60 price ledger.

The replay is the live risk state machine:
  - entries and exits are separate time-ordered events
  - suspension blocks new ENTRIES; positions already open run to their exits
  - realised drawdown is measured from the running peak of realised equity
  - drawdown limits take min(absolute, fraction x activation equity), which is
    what `refresh_drawdown_state` does in the executor

Fixes modelled:

  FIX A  capital       raise activation equity so the fractional limits stop
                       binding below the strategy's natural drawdown
  FIX B  resume rule   a flat suspended account currently cannot recover: it
                       needs profit to lift the suspension and cannot trade to
                       earn it. Modelled fix re-baselines the equity peak to
                       current equity after the account has been suspended and
                       flat for `rebaseline_days`, which zeroes the measured
                       drawdown and lifts the suspension. Time-based resumption
                       alone does not work - without re-baselining the very next
                       exit re-suspends, and the account flaps.
  FIX C  sleeve set    drop the two sleeves that earn ~nothing but consume the
                       shared add-on budget
  FIX D  sizing        the validated causal ranking applied in the only
                       direction the 0.01 lot floor permits: 1x or 2x

Fix D's multipliers come from `v4_causal_rank`, matched to ledger rows on
(entry_time, source_id); any row without a score stays at 1x.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import features as F

PNL = F.PNL
LIVE_EQUITY = 987.6623553437713
DEAD_SLEEVES = ["V8_DUKASCOPY_RAW_TICK", "V25_DUKASCOPY_RAW_TICK"]
ABS = {"suspend": 225.0, "resume": 180.0, "hard": 300.0}
FRAC = {"suspend": 0.075, "resume": 0.060, "hard": 0.100}


def limits(activation_equity):
    return {k: min(ABS[k], activation_equity * FRAC[k]) for k in ABS}


def replay(pnl, entry_t, exit_t, lim, rebaseline_days=None):
    """Returns (equity_path, n_taken, n_blocked, suspends, stopped, rebaselines).

    `rebaseline_days` implements FIX B. When set, an account that has been
    suspended with no open positions for that many days resets its peak to
    current equity, which zeroes drawdown and lets it trade again. When None,
    the live rule applies and a flat suspended account stays suspended forever.
    """
    n = len(pnl)
    ev = [(entry_t[i], 0, i) for i in range(n)] + [(exit_t[i], 1, i) for i in range(n)]
    ev.sort(key=lambda e: (e[0], e[1]))
    day = np.timedelta64(1, "D")

    equity = peak = 0.0
    suspended = False
    stopped = None
    open_ct = 0
    susp_since = None
    taken: set[int] = set()
    path, blocked, suspends, rebases = [], 0, 0, 0

    for t, kind, i in ev:
        # FIX B: flat + suspended long enough -> re-baseline the peak
        if (rebaseline_days is not None and suspended and open_ct == 0
                and susp_since is not None
                and (t - susp_since) >= rebaseline_days * day):
            peak = equity
            suspended = False
            susp_since = None
            rebases += 1

        if kind == 0:
            if stopped is not None or suspended:
                blocked += 1
                continue
            taken.add(i)
            open_ct += 1
        else:
            if i not in taken:
                continue
            open_ct -= 1
            equity += pnl[i]
            peak = max(peak, equity)
            path.append((t, equity))
            dd = peak - equity
            if stopped is None and dd >= lim["hard"]:
                stopped = (t, equity, dd)
            elif not suspended and dd >= lim["suspend"]:
                suspended = True
                susp_since = t
                suspends += 1
            elif suspended and dd <= lim["resume"]:
                suspended = False
                susp_since = None
    return path, len(taken), blocked, suspends, stopped, rebases


def stats(path):
    if not path:
        return dict(net=0.0, dd=1.0, ratio=0.0, months=0, green=0)
    t = np.array([p[0] for p in path])
    eq = np.array([p[1] for p in path])
    dd = float(np.max(np.maximum.accumulate(eq) - eq))
    step = np.diff(np.r_[0.0, eq])
    m = pd.Series(step).groupby(pd.to_datetime(pd.Series(t)).dt.strftime("%Y-%m").values).sum()
    return dict(net=float(eq[-1]), dd=max(dd, 1e-9),
                ratio=float(eq[-1] / max(dd, 1e-9)),
                months=len(m), green=int((m > 0).sum()))


def sizing_multipliers(led):
    """FIX D: causal rank -> 1x or 2x. Top `share` of scored trades are doubled."""
    from v4_causal_rank import run as v4run
    from v3_significance_bagging import load as v3load
    X, meta = v3load()
    mu, rank = v4run(X, meta, mode="C", n_bags=40, seed=0)
    key = pd.DataFrame({
        "entry_time": pd.to_datetime(meta.entry_time, utc=True),
        "source_id": meta.source_id.values, "rank": rank})
    key = key[np.isfinite(key["rank"])]
    j = led.merge(key, on=["entry_time", "source_id"], how="left")
    return j["rank"].values


def main():
    led = F.load_ledger()
    led = led[led.entry_time >= "2021-01-01"].reset_index(drop=True)
    print(f"V60 ledger 2021+: {len(led):,} trades, "
          f"unconstrained net ${led[PNL].sum():.0f}\n")
    ranks = sizing_multipliers(led)
    print(f"causal sizing scores matched to {int(np.isfinite(ranks).sum()):,} "
          f"of {len(led):,} ledger rows\n")

    def build(drop_dead=False, size=False, top_share=0.30):
        d = led
        r = ranks
        if drop_dead:
            keep = ~d.source_id.isin(DEAD_SLEEVES).values
            d, r = d[keep], r[keep]
        p = d[PNL].values.copy()
        if size:
            up = np.isfinite(r) & (r >= 1.0 - top_share)
            p = p * np.where(up, 2.0, 1.0)
        return p, d.entry_time.values, d.exit_time.values

    variants = [
        ("AS DEPLOYED  $999, live rules", LIVE_EQUITY, None, False, False),
        ("FIX B only   resume re-baseline", LIVE_EQUITY, 30, False, False),
        ("FIX A only   fund to $3,000", 3000.0, None, False, False),
        ("FIX A+B", 3000.0, 30, False, False),
        ("FIX A+B+C    drop V8/V25", 3000.0, 30, True, False),
        ("FIX A+B+D    sizing, keep V8/V25", 3000.0, 30, False, True),
        ("FIX A+B+C+D  all four", 3000.0, 30, True, True),
    ]

    print("=" * 100)
    print(f"{'configuration':<34}{'taken':>7}{'blocked':>9}{'net $':>10}"
          f"{'maxDD':>8}{'net/DD':>8}{'susp':>6}{'reset':>7}{'green mo':>10}  state")
    print("=" * 100)
    rows = []
    for lab, eq0, reb, dead, size in variants:
        pnl, et, xt = build(dead, size)
        lim = limits(eq0)
        path, taken, blocked, susp, stopped, rebases = replay(pnl, et, xt, lim, reb)
        s = stats(path)
        state = "HARD STOPPED" if stopped else ("frozen" if taken < len(pnl) * 0.5 else "running")
        print(f"{lab:<34}{taken:>7}{blocked:>9}{s['net']:>10.0f}{s['dd']:>8.0f}"
              f"{s['ratio']:>8.2f}{susp:>6}{rebases:>7}"
              f"{str(s['green'])+'/'+str(s['months']):>10}  {state}")
        rows.append((lab, taken, s, susp, rebases, stopped, len(pnl)))
    print("=" * 100)

    base = rows[0]
    full = rows[-1]
    print(f"\nAS DEPLOYED   : {base[1]:,} of {base[6]:,} trades, "
          f"net ${base[2]['net']:.0f}, maxDD ${base[2]['dd']:.0f}")
    print(f"ALL FIXES     : {full[1]:,} of {full[6]:,} trades, "
          f"net ${full[2]['net']:.0f}, maxDD ${full[2]['dd']:.0f}")
    print(f"IMPROVEMENT   : net ${full[2]['net']-base[2]['net']:+,.0f} "
          f"({full[2]['net']/max(base[2]['net'],1):.1f}x), "
          f"{full[1]-base[1]:+,} more trades taken")

    print("\n\nYEAR BY YEAR - as deployed vs the recommended configuration (A+B+D)")
    print("-" * 74)
    pnl0, et0, xt0 = build(False, False)
    p0, *_ = replay(pnl0, et0, xt0, limits(LIVE_EQUITY), None)
    pnl1, et1, xt1 = build(False, True)
    p1, *_ = replay(pnl1, et1, xt1, limits(3000.0), 30)

    def yearly(path):
        if not path:
            return pd.Series(dtype=float)
        t = pd.to_datetime(pd.Series([x[0] for x in path]))
        eq = np.array([x[1] for x in path])
        return pd.Series(np.diff(np.r_[0.0, eq])).groupby(t.dt.year.values).sum()

    y0, y1 = yearly(p0), yearly(p1)
    years = sorted(set(y0.index) | set(y1.index))
    print(f"  {'year':<7}{'as deployed':>14}{'recommended':>14}{'delta':>12}")
    for y in years:
        a, b = float(y0.get(y, 0.0)), float(y1.get(y, 0.0))
        print(f"  {y:<7}{a:>14.0f}{b:>14.0f}{b-a:>+12.0f}")
    print(f"  {'TOTAL':<7}{y0.sum():>14.0f}{y1.sum():>14.0f}"
          f"{y1.sum()-y0.sum():>+12.0f}")

    print("\n\nFIX B side effect - re-baselining forgives drawdown")
    print("-" * 74)
    print("Resetting the peak zeroes the MEASURED drawdown, so the state machine")
    print("tolerates a larger TRUE peak-to-trough loss than the nominal limit.")
    print("That is the price of never deadlocking, and it has to be chosen")
    print("deliberately rather than discovered later.\n")
    print(f"  {'rebaseline':<13}{'taken':>7}{'net $':>10}{'true maxDD':>12}"
          f"{'nominal cap':>13}{'resets':>8}  state")
    for reb in (None, 14, 30, 60, 90):
        pnl, et, xt = build(False, False)
        lim = limits(3000.0)
        path, taken, blocked, susp, stopped, rebases = replay(pnl, et, xt, lim, reb)
        s = stats(path)
        state = "HARD STOPPED" if stopped else ("frozen" if taken < len(pnl) * .5 else "running")
        lab = "off (live)" if reb is None else f"{reb} days"
        print(f"  {lab:<13}{taken:>7}{s['net']:>10.0f}{s['dd']:>12.0f}"
              f"{lim['hard']:>13.0f}{rebases:>8}  {state}")
    print("\n  A longer cooling period means fewer resets and a truer drawdown")
    print("  limit, at the cost of more time spent suspended.")

    print("\n\nFIX C detail - what the add-on budget is being spent on")
    print("-" * 66)
    a = led[led.source_id.isin(
        ["V7_DUKASCOPY_RAW_TICK", "V8_DUKASCOPY_RAW_TICK",
         "V25_DUKASCOPY_RAW_TICK", "V57_OVERLAY_DUKASCOPY_RAW_TICK"])].copy()
    a["d"] = a.entry_time.dt.date
    per_day = a.groupby("d").size()
    at_cap = set(per_day[per_day >= 2].index)
    dead_at_cap = a[(a.source_id.isin(DEAD_SLEEVES)) & (a.d.isin(at_cap))]
    good = a[~a.source_id.isin(DEAD_SLEEVES)]
    gm, dm = good[PNL].mean(), a[a.source_id.isin(DEAD_SLEEVES)][PNL].mean()
    print(f"  days add-ons were at the 2/day cap        : {len(at_cap):,}")
    print(f"  slots on those days taken by V8/V25       : {len(dead_at_cap):,}")
    print(f"  mean $/trade  V7+V57 ${gm:.2f}   vs   V8+V25 ${dm:.2f}")
    print(f"  upper bound if every such slot had gone")
    print(f"    to a V7/V57 candidate instead           : "
          f"${len(dead_at_cap)*(gm-dm):+,.0f}")
    print("  (upper bound only - the ledger records executed trades, not the")
    print("   candidates that were suppressed, so it cannot be confirmed that a")
    print("   V7/V57 candidate existed on each of those days)")


if __name__ == "__main__":
    main()
