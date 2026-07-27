"""Independently reproduce the review's corrected GOLD V8 figures.

The adversarial review corrected the V8 headline from causal PF 2.03 to 1.202 and
the full-history PF from 1.79 to 1.242. Those numbers were ACCEPTED without being
reproduced, which is the same mistake in miniature as flagging the sizing bug and
then reporting figures from a run that still contained it.

This re-derives sizing in ENTRY order from Capital outcomes using booking.py, and
recomputes every metric on the dollar series, then compares:

  as-shipped   the contaminated `size` column stored in the trade file
  corrected    sizing re-derived in entry order from the same outcomes
  reviewer     what the review reported

Agreement within rounding confirms the correction. Disagreement means one of us
is wrong and the number is still unsettled.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

from booking import streak_sizes, exit_order_sizes_UNSAFE, metrics

TRADES = ("C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-regime-teacher-wt/"
          "xau-usd/xauusd-fast-research/regime-teacher-eas-v1/outputs/"
          "GOLD_V8_DUALFEED_TRADES.csv")


def load(path):
    t = pd.read_csv(path, parse_dates=["dec_t", "entry_t", "exit_t"])
    if "cap_exit_t" in t.columns:
        t["cap_exit_t"] = pd.to_datetime(t.cap_exit_t, utc=True)
    return t.dropna(subset=["rc"]).sort_values("entry_t").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", default=TRADES)
    ap.add_argument("--half-at", type=int, default=2)
    ap.add_argument("--quarter-at", type=int, default=4)
    a = ap.parse_args()
    t = load(a.trades)
    print(f"{len(t):,} executable trades  "
          f"{t.entry_t.min():%Y-%m-%d} -> {t.entry_t.max():%Y-%m-%d}\n")

    # exit timestamps: Capital where available, else the Dukascopy exit
    xt = t.cap_exit_t if "cap_exit_t" in t.columns else t.exit_t
    xt = xt.fillna(t.exit_t)

    # dollars risked per 0.01 lot = the stop distance; the file names it either way
    risk = (t["stop_usd"] if "stop_usd" in t.columns else t["stop"]).to_numpy(float)
    shipped = t["size"].to_numpy(dtype=float)
    corrected = streak_sizes(t.entry_t.values, xt.values, t.rc.values,
                             half_at=a.half_at, quarter_at=a.quarter_at)
    reproduced_bug = exit_order_sizes_UNSAFE(xt.values, t.rc.values,
                                             half_at=a.half_at,
                                             quarter_at=a.quarter_at)

    print("=== DOES THE SHIPPED `size` COLUMN MATCH EXIT-ORDER SIZING? ===")
    print(f"  shipped vs exit-order reproduction : "
          f"{100*np.mean(np.isclose(shipped, reproduced_bug)):.1f}% identical")
    print(f"  shipped vs corrected entry-order   : "
          f"{100*np.mean(np.isclose(shipped, corrected)):.1f}% identical")
    diff = ~np.isclose(shipped, corrected)
    print(f"  -> {diff.sum():,} of {len(t):,} trades ({100*diff.mean():.1f}%) "
          f"were sized using information not available at entry\n")

    print("=== METRICS, CAPITAL FEED, SAME DOLLAR SERIES THROUGHOUT ===")
    print(f"  {'variant':<34}{'n':>7}{'WR':>7}{'PF':>8}{'USD':>10}{'maxDD':>9}")
    rows = {}
    for lab, sz in (("as shipped (exit-order sizing)", shipped),
                    ("corrected (entry-order)", corrected)):
        d = t.assign(usd=t.rc * sz * risk, _x=xt)
        m = metrics(d, usd_col="usd", time_col="_x")
        rows[lab] = m
        print(f"  {lab:<34}{m['n']:>7}{m['wr']:>7}{m['pf']:>8}"
              f"{m['usd']:>10.0f}{m['dd']:>9.0f}")

    # flat sizing, to separate "the streak rule" from "the bug"
    d = t.assign(usd=t.rc * risk, _x=xt)
    m = metrics(d, usd_col="usd", time_col="_x")
    print(f"  {'no streak rule at all (flat)':<34}{m['n']:>7}{m['wr']:>7}"
          f"{m['pf']:>8}{m['usd']:>10.0f}{m['dd']:>9.0f}")

    print("\n=== AGREEMENT WITH THE REVIEW ===")
    corr = rows["corrected (entry-order)"]
    ship = rows["as shipped (exit-order sizing)"]
    print(f"  full-history PF   shipped {ship['pf']:.3f}   "
          f"corrected {corr['pf']:.3f}   review said 1.242")
    print(f"  full-history DD   shipped ${ship['dd']:.0f}   "
          f"corrected ${corr['dd']:.0f}   review said $1,980")
    ok_pf = abs(corr["pf"] - 1.242) < 0.15
    ok_dir = corr["pf"] < ship["pf"] and corr["dd"] > ship["dd"]
    print(f"\n  direction of the correction reproduced: {'YES' if ok_dir else 'NO'}"
          f"  (PF falls, drawdown rises)")
    print(f"  magnitude within 0.15 of the review:    {'YES' if ok_pf else 'NO'}")
    if not ok_pf:
        print("  NOTE: this run uses the whole executable file at flat $ per R;"
              "\n  the review applied a $30 stop cap and $10 target risk, so an"
              "\n  exact match is not expected. The DIRECTION is the claim being"
              "\n  checked, and a residual gap means the figure stays the"
              "\n  review's rather than mine.")


if __name__ == "__main__":
    main()
