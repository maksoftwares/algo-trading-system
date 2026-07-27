"""Band x shrinkage sweep: does ANY sizing width clear all four gates?

V1 and V2 both improved in 4 of 6 years, failing gate 4 on 2021 and 2022. Both
are the thin-training-data years, so the obvious remaining lever is the width of
the sizing ramp itself: a gentler multiplier should do less damage where the
model is wrong, while still tilting toward the good trades where it is right.

This sweeps that lever to exhaustion. If gate 4 is a tuning problem, some band
here clears it. If the deltas stay negative at every width, the model's RANKING
is wrong in those years and no policy width can fix a sign error.

This is the last configuration test in this lane. The count is declared in
RESULT.md so that a marginal pass, had one appeared, could be discounted for the
search that produced it.
"""
from __future__ import annotations
import numpy as np

from v2_sleeve_shrink import run, report, N_REF
import v2_sleeve_shrink as V2
import features as F

PNL = F.PNL
BANDS = [(0.9, 1.1), (0.8, 1.2), (0.7, 1.3), (0.6, 1.4), (0.5, 1.5)]
NREFS = [1500, 3000]
BAR = 17.91                      # trivial benchmark: drop the two dead sleeves


def year_deltas(meta, mult):
    k = np.isfinite(mult)
    m = meta[k].reset_index(drop=True)
    base = m[PNL].values
    sized = base * mult[k]
    y = m.exit_time.dt.year.values
    return {int(yy): float(sized[y == yy].sum() - base[y == yy].sum())
            for yy in sorted(np.unique(y))}


def main():
    print("band x shrinkage sweep. Gates unchanged from PREREGISTRATION.md.\n")
    # `report` derives the unsized baseline from the same scored set it scores,
    # so any run supplies it; the multiplier is irrelevant to those three fields.
    meta0, _, mult0 = run(use_sleeve=False, use_shrink=False)
    b = report(meta0, mult0, "base")
    print(f"baseline: net ${b['base']}, net/DD {b['base_ratio']}, "
          f"green {b['base_green']}%   bar net/DD > {BAR}\n")

    hdr = f"{'band':<12}{'N_REF':>7}{'net':>9}{'net/DD':>8}{'green%':>8}{'yrs+':>6}"
    years_seen: list[int] = []
    rows = []
    for nref in NREFS:
        V2.N_REF = nref
        for band in BANDS:
            meta, sc, mu = run(use_sleeve=True, use_shrink=True, band=band)
            r = report(meta, mu, f"{band} n{nref}")
            d = year_deltas(meta, mu)
            years_seen = sorted(d)
            g = [r["net"] >= r["base"], r["ratio"] > BAR,
                 r["green"] >= r["base_green"] - 2, r["yrs"] >= 5]
            rows.append((band, nref, r, d, g))
    V2.N_REF = N_REF

    print(hdr + "".join(f"{y:>8}" for y in years_seen) + "  gates")
    for band, nref, r, d, g in rows:
        flag = "PASS" if all(g) else "fail:" + ",".join(
            n for n, ok in zip(["net", "ratio", "green", "years"], g) if not ok)
        print(f"{str(band):<12}{nref:>7}{r['net']:>9}{r['ratio']:>8}{r['green']:>8}"
              f"{r['yrs']:>4}/{r['ny']:<2}"
              + "".join(f"{d.get(y, 0):>+8.0f}" for y in years_seen) + f"  {flag}")

    npass = sum(1 for *_, g in rows if all(g))
    print(f"\n{npass} of {len(rows)} configurations pass ALL FOUR gates")
    neg = [y for y in years_seen
           if all(d.get(y, 0) < 0 for *_, d, _ in rows)]
    if neg:
        print(f"  years negative at EVERY band and shrinkage level: {neg}")
        print("  -> the ranking is directionally wrong there; band width only "
              "scales the damage, it does not change its sign")


if __name__ == "__main__":
    main()
