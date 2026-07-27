"""Intra-trade panel + feasibility test for an EARLY-EXIT model on XAUUSD.

Two separate questions, and only one of them is new.

  ENTRY FILTER — already built and REFUTED (ML_FILTER_FINDINGS.md). Cross-asset
  ML beat the frozen ranker alone (+0.28R vs +0.20R on the top 20%) and then lost
  to the real incumbent at every cutoff ($1,309 vs a $2,891 baseline). The signal
  was real but redundant with the hand-built gates. Retesting is cheap but the
  prior is failure.

  EARLY EXIT — new. The stop is 6.75xATR, so every loser costs a full -1.0R, and
  the red-month forensic found green and red months carry IDENTICAL gross losses
  (16.8R each). Cutting the loss side is the one lever that has never been tried.

Why early exit might work where entry prediction does not: direction at entry is
unpredictable here (AUC 0.49-0.52), but this is prediction DURING the trade, from
a different information set - how far the path has gone against us, how long it
has taken, whether volatility has expanded, and what the tick flow has done since
entry.

PREREGISTERED BEFORE RUNNING:
  * Fit on trades ENTERED on or before 2024-12-31. 2025-01 onward is sealed.
  * Feasibility gate: the model must beat the mechanical baseline "exit when
    unrealised R is worse than -X" by a clear margin on the sealed era. If it only
    reproduces "already near the stop", it has learned nothing and is rejected.
  * Success is measured on TOTAL R and profit factor of the whole book, not on
    classification accuracy. A model that predicts losses perfectly but exits
    winners early is a failure.
  * Benchmark is the real incumbent: the same trades held to stop-or-horizon.

Step 1 (this file): build the panel and answer the feasibility question - is the
eventual outcome predictable from the path, beyond what current unrealised R
already tells you?
"""
import argparse, json
import numpy as np, pandas as pd
import engine, specialist, v6_fix as V

FIT_END = pd.Timestamp("2024-12-31 23:59:59", tz="UTC")
CHECK_EVERY = 12          # panel row every 12 bars (1 hour)
MIN_BARS = 6              # no exit decision before this many bars


def trade_universe(C):
    """Deduplicated confirmed setups from the V6 specialists, BEFORE ranker
    selection - the exit decision does not depend on which specialist selected
    the trade, so the larger population is the right training set."""
    cands, fam = V.scored_candidates()
    a = pd.concat(cands.values()).reset_index(drop=True)
    a = a.sort_values(["i", "score"], ascending=[True, False]).groupby(
        "i", as_index=False).first()
    return a.sort_values("i").reset_index(drop=True), fam


def build_panel(u, C, max_trades=None):
    """One row per (trade, checkpoint). Everything is computable at that instant."""
    mh, ml, mc, atr = C["mh"], C["ml"], C["mc"], C["atr"]
    bl, bc, ao = C["bl"], C["bc"], C["ao"]
    ah, ac, bo = C["ah"], C["ac"], C["bo"]
    csm, cbi, ctc, cts, cpe = C["csm"], C["cbi"], C["ctc"], C["cts"], C["cpe"]
    slope, t = C["slope"], C["t"]
    if max_trades:
        u = u.iloc[:max_trades]
    rows = []
    for r in u.itertuples():
        i, j, i1 = int(r.i), int(r.j), int(r.i1)
        long, stop = bool(r.long), float(r.stop)
        if i1 - j < MIN_BARS * 2:
            continue
        fill = ao[j] if long else bo[j]
        # realised outcome under the CURRENT rule (hold to stop or horizon)
        if long:
            slv = fill - stop
            hit = np.flatnonzero(bl[j:i1] <= slv)
            xi = j + hit[0] if len(hit) else i1 - 1
            xp = slv if len(hit) else bc[xi]
            final = (xp - fill) / stop - engine.FEE / stop
        else:
            slv = fill + stop
            hit = np.flatnonzero(ah[j:i1] >= slv)
            xi = j + hit[0] if len(hit) else i1 - 1
            xp = slv if len(hit) else ac[xi]
            final = (fill - xp) / stop - engine.FEE / stop
        stopped = bool(len(hit))
        atr0 = atr[i] if atr[i] > 0 else np.nan
        for k in range(MIN_BARS, min(i1 - j, 100000), CHECK_EVERY):
            b = j + k
            if b >= xi:                      # trade already closed by then
                break
            # unrealised R at the current exitable price (bid for long, ask short)
            px = bc[b] if long else ac[b]
            r_now = ((px - fill) if long else (fill - px)) / stop
            seg = slice(j, b + 1)
            if long:
                mae = -((fill - ml[seg].min()) / stop)
                mfe = (mh[seg].max() - fill) / stop
            else:
                mae = -((mh[seg].max() - fill) / stop)
                mfe = (fill - ml[seg].min()) / stop
            nb = max(b - j, 1)
            rows.append((
                int(r.i), t.iloc[i], t.iloc[b], long, stop, k,
                r_now, mae, mfe,
                k / max(i1 - j, 1),                      # fraction of horizon used
                atr[b] / atr0 if atr0 == atr0 else 1.0,  # vol expansion since entry
                (1.0 if long else -1.0) * (csm[b] - csm[j]) / nb,   # tick flow since entry
                (1.0 if long else -1.0) * (cbi[b] - cbi[j]) / nb,   # book imbalance
                (ctc[b] - ctc[j]) / nb,                            # activity
                ((cts[b] - cts[j]) / nb) / stop,                   # spread
                (cpe[b] - cpe[j]) / nb,                            # efficiency
                (1.0 if long else -1.0) * (slope[b] if np.isfinite(slope[b]) else 0.0),
                r_now - mae,                              # give-back from the worst point
                mfe - r_now,                              # give-back from the best point
                final, stopped))
    cols = ["i", "dec_t", "now_t", "long", "stop", "bars", "r_now", "mae", "mfe",
            "frac_t", "vol_exp", "flow", "imb", "activity", "spr", "eff",
            "slope", "off_mae", "off_mfe", "final_r", "stopped"]
    p = pd.DataFrame(rows, columns=cols)
    p["dec_t"] = pd.to_datetime(p.dec_t, utc=True)
    p["now_t"] = pd.to_datetime(p.now_t, utc=True)
    return p


FEATS = ["r_now", "mae", "mfe", "bars", "frac_t", "vol_exp", "flow", "imb",
         "activity", "spr", "eff", "slope", "off_mae", "off_mfe"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-trades", type=int, default=None)
    ap.add_argument("--out", default="outputs/ML_EARLY_EXIT_PANEL.parquet")
    a = ap.parse_args()
    C = specialist.load_context()
    u, fam = trade_universe(C)
    print(f"trade universe: {len(u)} deduplicated confirmed setups "
          f"({fam['family']} gates)")
    p = build_panel(u, C, a.max_trades)
    p.to_parquet(a.out)
    print(f"panel: {len(p):,} rows over {p.i.nunique():,} trades "
          f"({p.dec_t.min():%Y-%m-%d} -> {p.dec_t.max():%Y-%m-%d})\n")

    fit = p[p.dec_t <= FIT_END]
    seal = p[p.dec_t > FIT_END]
    print(f"fit {len(fit):,} rows / {fit.i.nunique():,} trades   "
          f"sealed {len(seal):,} rows / {seal.i.nunique():,} trades\n")

    print("=== FEASIBILITY: is the outcome predictable from the path? ===")
    print("base rate of eventual stop-out, by current unrealised R (fit era):")
    print(f"  {'r_now bucket':<18}{'rows':>8}{'P(stop)':>10}{'mean final R':>14}")
    b = pd.cut(fit.r_now, [-99, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 1.0, 99])
    g = fit.groupby(b, observed=True).agg(n=("stopped", "size"),
                                          p=("stopped", "mean"),
                                          fr=("final_r", "mean"))
    for idx, row in g.iterrows():
        print(f"  {str(idx):<18}{int(row.n):>8}{row.p:>10.3f}{row.fr:>14.3f}")

    print("\nThe question that matters: beyond r_now, does anything add signal?")
    print("correlation of each feature with eventual stop-out, controlling for r_now")
    print("(partial correlation via residuals of a linear fit on r_now):")
    x = fit.r_now.values
    A = np.column_stack([np.ones(len(x)), x])
    for f in FEATS:
        if f == "r_now":
            continue
        y = fit[f].values.astype(float)
        y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
        by = np.linalg.lstsq(A, y, rcond=None)[0]
        ry = y - A @ by
        s = fit.stopped.values.astype(float)
        bs = np.linalg.lstsq(A, s, rcond=None)[0]
        rs = s - A @ bs
        if ry.std() < 1e-12:
            continue
        print(f"  {f:<12}{np.corrcoef(ry, rs)[0,1]:+.4f}")


if __name__ == "__main__":
    main()
