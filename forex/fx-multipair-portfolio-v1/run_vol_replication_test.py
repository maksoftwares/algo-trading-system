"""R8 replication: do the 4h high-volatility candidates survive new data?

`run_vol_conditioned_census.py` searched ~300 buckets (4 signals x 5 horizons x
3 symbols x 5 volatility quintiles) and reported 8 clearing the cost bar with
|t| > 2. At a 5% false-positive rate, ~15 such hits are expected from pure noise,
so those 8 are consistent with finding nothing. Three further warning signs: the
winning volatility quintiles are scattered (Q2/Q3/Q4/Q5) with no monotone
pattern, the sign flips between pairs, and a 50-point "edge" is an implausibly
large fraction of a 4h EURUSD move.

Rather than cherry-pick one and test it, this re-runs the *identical measurement*
on the validation window and asks whether the same cells reproduce: same signal,
same horizon, same symbol, same volatility quintile, same sign, still clearing
cost. That is a replication test, not a new search, so it cannot manufacture a
result.

A real effect replicates. Multiple-testing noise does not.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_vol_conditioned_census import HORIZONS, SIGNALS, SYMBOLS, build, evaluate  # noqa: E402
from src.report import MEASURED_ROUND_TRIP_POINTS  # noqa: E402


def cells(partition: str) -> dict[tuple, dict]:
    frames = {symbol: build(symbol, partition) for symbol in SYMBOLS}
    out: dict[tuple, dict] = {}
    for signal in SIGNALS:
        for horizon in HORIZONS:
            for symbol in SYMBOLS:
                cost = MEASURED_ROUND_TRIP_POINTS[symbol]
                for row in evaluate(frames[symbol], signal, horizon, cost):
                    out[(signal, horizon, symbol, row["vol_quintile"])] = row
    return out


def signed_edge(row: dict) -> float:
    """The decile side the design window would have traded, with its sign."""
    return (
        row["top_mean_points"]
        if abs(row["top_mean_points"]) >= abs(row["bottom_mean_points"])
        else row["bottom_mean_points"]
    )


def main() -> int:
    print("building design cells...")
    design = cells("design")
    print("building validation cells...")
    validation = cells("validation")

    selected = [
        key
        for key, row in design.items()
        if row["clears_cost"] and max(abs(row["top_t"]), abs(row["bottom_t"])) > 2.0
    ]
    print(f"\ndesign cells clearing cost with |t|>2: {len(selected)}")
    print(f"total cells searched: {len(design)}  (expected false positives at 5%: ~{0.05*len(design):.0f})\n")

    header = (
        f"{'signal':17s} {'hz':>4} {'sym':7s} {'Q':>2} "
        f"{'design_edge':>12} {'valid_edge':>11} {'valid_t':>8} {'same_sign':>10} {'clears':>7}"
    )
    print(header)
    print("-" * len(header))

    replicated = 0
    records = []
    for key in sorted(selected, key=lambda k: (k[0], k[1], k[2], k[3])):
        signal, horizon, symbol, quintile = key
        design_edge = signed_edge(design[key])
        row = validation.get(key)
        if row is None:
            print(f"{signal:17s} {horizon:>4} {symbol:7s} {quintile:>2} {design_edge:>12.2f} {'absent':>11}")
            records.append({"cell": list(key), "design_edge": design_edge, "validation": None})
            continue
        valid_edge = signed_edge(row)
        valid_t = row["top_t"] if abs(row["top_mean_points"]) >= abs(row["bottom_mean_points"]) else row["bottom_t"]
        same_sign = (design_edge > 0) == (valid_edge > 0)
        clears = abs(valid_edge) > MEASURED_ROUND_TRIP_POINTS[symbol]
        holds = same_sign and clears and abs(valid_t) > 2.0
        replicated += int(holds)
        print(
            f"{signal:17s} {horizon:>4} {symbol:7s} {quintile:>2} {design_edge:>12.2f} "
            f"{valid_edge:>11.2f} {valid_t:>8.2f} {str(same_sign):>10} {str(clears):>7}"
            f"{'   <== REPLICATES' if holds else ''}"
        )
        records.append(
            {
                "cell": list(key),
                "design_edge_points": round(design_edge, 2),
                "validation_edge_points": round(valid_edge, 2),
                "validation_t": valid_t,
                "same_sign": bool(same_sign),
                "validation_clears_cost": bool(clears),
                "replicates": bool(holds),
            }
        )

    verdict = (
        "R8_REPLICATED_INVESTIGATE_FURTHER"
        if replicated > 0
        else "R8_REJECTED_MULTIPLE_TESTING_NOISE"
    )
    print(f"\nreplicated: {replicated} of {len(selected)}")
    print(f"verdict: {verdict}")

    out = ROOT / "outputs" / "VOL_REPLICATION_TEST.json"
    out.write_text(
        json.dumps(
            {
                "schema_version": "fx_vol_replication_v1",
                "method": "identical measurement re-run on validation; same cell, sign, and cost bar",
                "cells_searched": len(design),
                "expected_false_positives_at_5pct": round(0.05 * len(design), 1),
                "design_selected": len(selected),
                "replicated": replicated,
                "records": records,
                "verdict": verdict,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
