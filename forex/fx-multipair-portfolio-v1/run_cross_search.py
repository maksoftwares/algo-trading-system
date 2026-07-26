"""R9: the same searches that closed the majors, run on the crosses.

Closes the last gap. EURGBP / EURJPY / GBPJPY are tradeable on the account, are
less efficient than the USD majors, and have genuinely different dynamics — the
JPY crosses trend (classic carry crosses), EURGBP ranges. R1-R8 never touched
them because the terminal holds no tick history for them; `build_crosses.py`
constructs them from the majors instead.

Three tests, deliberately the *same* ones that closed the majors so the
comparison is apples to apples:

1. the R1 bar-geometry family grid (breakout / channel / fade), 48 points each;
2. a zero-cost rerun of the best grid point, to separate "no edge" from
   "cost-killed" exactly as R1 did;
3. a multi-day momentum census, because trend is the specific reason to expect
   crosses to differ.

Costs are the arbitrage-implied sum of the legs' measured spreads — pessimistic
relative to a direct broker quote: EURGBP 24, EURJPY 23, GBPJPY 29 points round
trip.

Design window only. Validation and final exam stay sealed unless something here
clears.
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.engine import CostModel, RunConfig, SymbolSpec, simulate  # noqa: E402
from src.fxdata import INSTRUMENTS, SYNTHETIC_CROSSES, load_m5, mid, resample_from_m5  # noqa: E402
from src.report import (  # noqa: E402
    MEASURED_SPREAD_POINTS,
    PARTITIONS,
    SLIPPAGE_POINTS,
    STOP_SLIPPAGE_POINTS,
    slice_window,
    summarize,
)
from src.strategies import FAMILIES, build_signals  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
RR_GRID = (1.2, 1.5, 2.0, 2.5)
ATR_GRID = (1.0, 1.5, 2.0, 3.0)
CONTEXT_GRID = (0.0, 0.5, 1.0)
MAX_HOLD = {"london_breakout": 288, "asia_fade": 288, "donchian_h4": 2880}
LEGS = {"EURGBP": ("EURUSD", "GBPUSD"), "EURJPY": ("EURUSD", "USDJPY"), "GBPJPY": ("GBPUSD", "USDJPY")}


def cross_spread_points(cross: str) -> float:
    a, b = LEGS[cross]
    return MEASURED_SPREAD_POINTS[a] + MEASURED_SPREAD_POINTS[b]


def cross_costs(cross: str, raw_median: float) -> CostModel:
    """Widen Dukascopy-derived quotes up to the arbitrage-implied broker spread."""
    return CostModel(
        spread_markup_points=max(cross_spread_points(cross) - raw_median, 0.0),
        slippage_points=SLIPPAGE_POINTS,
        stop_slippage_points=STOP_SLIPPAGE_POINTS,
    )


def main() -> int:
    start, end = PARTITIONS["design"]
    print(f"R9 cross search — design window {start} .. {end}")
    for cross in SYNTHETIC_CROSSES:
        rt = cross_spread_points(cross) + SLIPPAGE_POINTS + STOP_SLIPPAGE_POINTS
        print(f"   {cross}: assumed spread {cross_spread_points(cross):.0f} pts, round trip {rt:.0f} pts")
    print()

    report: dict[str, object] = {
        "schema_version": "fx_cross_search_v1",
        "window": {"start": start, "end_exclusive": end},
        "cost_basis": "sum of legs' measured spreads (pessimistic vs a direct quote)",
        "grid": {"rr": list(RR_GRID), "atr_mult": list(ATR_GRID), "context_mult": list(CONTEXT_GRID)},
        "families": {},
        "momentum": {},
    }
    rows: list[dict] = []

    for cross in SYNTHETIC_CROSSES:
        bars = slice_window(load_m5(CACHE, cross), start, end)
        point = float(INSTRUMENTS[cross]["point_size"])
        raw_median = float(((bars["ask_close"] - bars["bid_close"]) / point).median())
        spec = SymbolSpec.of(cross)
        costs = cross_costs(cross, raw_median)
        floor = 10.0 * (cross_spread_points(cross) + SLIPPAGE_POINTS + STOP_SLIPPAGE_POINTS)
        print(f"--- {cross}  raw median spread {raw_median:.1f} pts -> markup {costs.spread_markup_points:.0f}, stop floor {floor:.0f}")

        for family, builder in FAMILIES.items():
            candidates = builder(bars, cross)
            config = RunConfig(lot=0.01, max_hold_bars=MAX_HOLD[family], max_entries_per_day=3)
            best = None
            for rr, atr_mult, context_mult in itertools.product(RR_GRID, ATR_GRID, CONTEXT_GRID):
                signals = build_signals(
                    candidates,
                    stop_floor_points=floor,
                    context_mult=context_mult,
                    atr_mult=atr_mult,
                    rr=rr,
                    stop_cap_points=3000.0,
                )
                result = summarize(simulate(bars, signals, spec, costs, config))
                rows.append({"cross": cross, "family": family, "rr": rr, "atr_mult": atr_mult,
                             "context_mult": context_mult, **result})
                pf = result.get("profit_factor")
                if pf is not None and result["trades"] >= 60 and (best is None or pf > best[0]):
                    best = (pf, rr, atr_mult, context_mult, result)

            if best is None:
                print(f"    {family:16s} no grid point reached 60 trades")
                continue
            pf, rr, atr_mult, context_mult, result = best
            # zero-cost rerun of that same point: edge, or cost?
            signals = build_signals(candidates, stop_floor_points=floor, context_mult=context_mult,
                                    atr_mult=atr_mult, rr=rr, stop_cap_points=3000.0)
            free = summarize(simulate(bars, signals, spec, CostModel(), config))
            report["families"].setdefault(cross, {})[family] = {
                "best_pf_costed": pf,
                "best_params": {"rr": rr, "atr_mult": atr_mult, "context_mult": context_mult},
                "trades": result["trades"],
                "win_rate_pct": result["win_rate_pct"],
                "avg_stop_points": result["avg_stop_points"],
                "pf_zero_cost": free.get("profit_factor"),
            }
            print(
                f"    {family:16s} best PF {pf:.3f} (rr={rr} atr={atr_mult} ctx={context_mult}) "
                f"n={result['trades']:>5} WR={result['win_rate_pct']:.1f}% "
                f"stop={result['avg_stop_points']:.0f}pt | zero-cost PF {free.get('profit_factor'):.3f}"
            )

        # multi-day momentum: the specific reason to expect crosses to differ
        daily = resample_from_m5(bars, 1440)
        close = mid(daily, "close") / point
        for lookback in (5, 10, 20, 60):
            for forward in (5, 10, 20):
                past = close[lookback:] - close[:-lookback]
                ahead = np.full(close.size, np.nan)
                ahead[: close.size - forward] = close[forward:] - close[: close.size - forward]
                aligned = (np.sign(past) * ahead[lookback:])
                aligned = aligned[np.isfinite(aligned)][::forward]
                if aligned.size < 30:
                    continue
                mean = float(aligned.mean())
                t = mean / (float(aligned.std(ddof=1)) / np.sqrt(aligned.size))
                report["momentum"].setdefault(cross, {})[f"mom{lookback}d_fwd{forward}d"] = {
                    "mean_points": round(mean, 1), "t": round(t, 2), "n": int(aligned.size)
                }
        best_mom = max(
            report["momentum"][cross].items(), key=lambda item: abs(item[1]["t"])
        )
        print(f"    momentum: strongest {best_mom[0]} mean {best_mom[1]['mean_points']:+.0f}pt t={best_mom[1]['t']:+.2f}\n")

    grid = pd.DataFrame(rows)
    grid.to_csv(ROOT / "outputs" / "CROSS_GRID.csv", index=False)

    # verdict: any cross/family with costed PF > 1.10 and zero-cost PF > 1.10
    survivors = [
        {"cross": cross, "family": family, **payload}
        for cross, families in report["families"].items()
        for family, payload in families.items()
        if (payload["best_pf_costed"] or 0) > 1.10 and (payload["pf_zero_cost"] or 0) > 1.10
    ]
    report["survivors"] = survivors
    report["verdict"] = "R9_CROSS_CANDIDATE_FOUND" if survivors else "R9_REJECTED_NO_CROSS_EDGE"

    out = ROOT / "outputs" / "CROSS_SEARCH.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"survivors (costed PF>1.10 AND zero-cost PF>1.10): {len(survivors)}")
    for survivor in survivors:
        print(f"   {survivor['cross']} {survivor['family']}: PF {survivor['best_pf_costed']:.3f}")
    print(f"verdict: {report['verdict']}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
