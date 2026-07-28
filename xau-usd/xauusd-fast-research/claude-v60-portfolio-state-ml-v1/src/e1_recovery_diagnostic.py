"""Can a losing V60 position be identified mid-flight, before it reaches its stop?

Before training anything, measure whether the question has an answer. Early exit
can only pay if positions that are down at time t tend to STAY down. If they
recover as often as not, there is nothing to cut, and any model will just be
selling the bottom of noise.

The V60 ledger makes this exact: implied position size is identically 1.0 unit on
all 2,194 trades, so gross P&L equals the signed price move, and the value of
closing at any intermediate price is known without assumption. Round-trip cost
(~$1.17) is unchanged by exiting early - still one open and one close - so early
exit is cost-neutral and only the close price matters.

Reports, per checkpoint, for positions still open at that time:
  - recovery rate: P(final gross > 0 | unrealised at checkpoint in bucket)
  - what the position actually goes on to earn from that point
The last column is the decisive one. Cutting at the checkpoint is worth doing
only where FORWARD P&L from the checkpoint is reliably negative.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import features as F

CHECKS = [0.5, 1, 2, 4, 8, 24]          # hours after entry
BUCKETS = [-np.inf, -1.5, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, np.inf]


def build():
    led = F.load_ledger()
    mkt = F.load_market()
    t = mkt.t.values.astype("datetime64[ns]")
    mc, mh, ml = mkt.mid_close.values, mkt.mid_high.values, mkt.mid_low.values
    atr = mkt.atr144.values

    e_idx = np.searchsorted(t, led.entry_time.values.astype("datetime64[ns]"), "right") - 1
    x_idx = np.searchsorted(t, led.exit_time.values.astype("datetime64[ns]"), "right") - 1
    ok = (e_idx >= 200) & (x_idx > e_idx)
    ep = led.entry_price.values
    sgn = led.direction_sign.values
    a0 = atr[np.clip(e_idx, 0, len(atr) - 1)]

    rows = []
    for k in np.flatnonzero(ok):
        i0, i1 = e_idx[k], x_idx[k]
        if not np.isfinite(a0[k]) or a0[k] <= 0:
            continue
        s, e = sgn[k], ep[k]
        final = (led.exit_price.values[k] - e) * s          # gross, units = 1
        for h in CHECKS:
            j = i0 + int(h * 12)                            # 12 M5 bars per hour
            if j >= i1:                                     # already closed
                continue
            seg_lo, seg_hi = ml[i0:j + 1], mh[i0:j + 1]
            worst = seg_lo.min() if s > 0 else seg_hi.max()
            rows.append(dict(
                k=k, h=h,
                unreal=(mc[j] - e) * s / a0[k],             # ATR units
                mae=(worst - e) * s / a0[k],
                final=final / a0[k],                        # ATR units
                fwd=(led.exit_price.values[k] - mc[j]) * s / a0[k],
                final_usd=led[F.PNL].values[k],
                fwd_usd=(led.exit_price.values[k] - mc[j]) * s,
                year=led.exit_time.dt.year.values[k]))
    return pd.DataFrame(rows), led


def main():
    d, led = build()
    print(f"{d.k.nunique():,} trades with reconstructable paths, "
          f"{len(d):,} (trade, checkpoint) observations\n")

    print("Positions still open at each checkpoint, bucketed by unrealised P&L")
    print("(ATR units at entry). 'fwd' is what the position earns FROM the")
    print("checkpoint onward - the quantity an early exit forfeits.\n")
    for h in CHECKS:
        g = d[d.h == h]
        if len(g) < 50:
            continue
        b = pd.cut(g.unreal, BUCKETS)
        agg = g.groupby(b, observed=True).agg(
            n=("final", "size"),
            win=("final", lambda s: 100 * float((s > 0).mean())),
            mean_final=("final", "mean"),
            mean_fwd=("fwd", "mean"),
            fwd_usd=("fwd_usd", "mean"))
        print(f"--- checkpoint t = {h}h   ({len(g):,} still open) ---")
        print(f"{'unrealised (ATR)':<20}{'n':>6}{'win%':>7}{'final':>9}"
              f"{'fwd':>8}{'fwd $':>9}")
        for iv, r in agg.iterrows():
            print(f"{str(iv):<20}{int(r.n):>6}{r.win:>7.1f}{r.mean_final:>9.2f}"
                  f"{r.mean_fwd:>8.2f}{r.fwd_usd:>9.2f}")
        print()

    print("=" * 66)
    print("THE TEST: is forward P&L from the checkpoint reliably negative for")
    print("losing positions? If not, there is nothing for a model to cut.")
    print("=" * 66)
    print(f"\n{'checkpoint':<12}{'n down':>8}{'win%':>7}{'mean fwd $':>12}"
          f"{'SE':>8}{'t':>7}")
    for h in CHECKS:
        g = d[(d.h == h) & (d.unreal < 0)]
        if len(g) < 30:
            continue
        m, se = g.fwd_usd.mean(), g.fwd_usd.std() / np.sqrt(len(g))
        print(f"{str(h)+'h':<12}{len(g):>8}{100*(g.final>0).mean():>7.1f}"
              f"{m:>12.2f}{se:>8.2f}{m/se:>7.2f}")

    print(f"\n{'checkpoint':<12}{'n < -0.5 ATR':>14}{'win%':>7}{'mean fwd $':>12}"
          f"{'SE':>8}{'t':>7}")
    for h in CHECKS:
        g = d[(d.h == h) & (d.unreal < -0.5)]
        if len(g) < 30:
            continue
        m, se = g.fwd_usd.mean(), g.fwd_usd.std() / np.sqrt(len(g))
        print(f"{str(h)+'h':<12}{len(g):>14}{100*(g.final>0).mean():>7.1f}"
              f"{m:>12.2f}{se:>8.2f}{m/se:>7.2f}")

    d.to_parquet("outputs/V60_PATH_CHECKPOINTS.parquet")
    print("\nwrote outputs/V60_PATH_CHECKPOINTS.parquet")


if __name__ == "__main__":
    main()
