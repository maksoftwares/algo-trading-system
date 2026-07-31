"""US500 family search on measured broker data, design → validation.

Cost is the *measured* Capital.com US500 spread (5 points, p95 6) plus 2 points
entry and 2 points stop slippage = 9 points = 0.9 index points round trip. The
stop floor is 10x that, per the rule the FX lane arrived at the hard way.

Split is chronological inside the 14 months of broker history. That is short —
the Dukascopy 2016+ download is still running and will be the real test — so
anything surviving here is a *candidate*, not a result.
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
from src.report import slice_window, summarize  # noqa: E402
from src.strategies import build_signals  # noqa: E402
from src.us500_strategies import US500_FAMILIES  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SYMBOL = "US500"
SPREAD_POINTS = 5.0
SLIPPAGE = 2.0
STOP_SLIPPAGE = 2.0
ROUND_TRIP = SPREAD_POINTS + SLIPPAGE + STOP_SLIPPAGE  # 9 points = 0.9 index pts
STOP_FLOOR = 10.0 * ROUND_TRIP

PARTITIONS = {
    "design": ("2025-06-06", "2026-02-01"),
    "validation": ("2026-02-01", "2026-08-01"),
}
RR_GRID = (1.0, 1.5, 2.0)
ATR_GRID = (1.0, 1.5, 2.0)
CONTEXT_GRID = (0.0, 0.5, 1.0)
MAX_HOLD = {"opening_range": 78, "overnight_fade": 78, "session_trend": 78}  # ~6.5h session
MIN_TRADES = 40
LOT = 1.0  # 1 index point = $1.00 per lot


def load() -> pd.DataFrame:
    return pd.read_parquet(CACHE / "bars" / f"{SYMBOL}_M5_BIDASK_BROKER.parquet")


def evaluate(bars: pd.DataFrame, family: str, rr: float, atr_mult: float, ctx: float) -> dict:
    candidates = US500_FAMILIES[family](bars, SYMBOL)
    signals = build_signals(
        candidates,
        stop_floor_points=STOP_FLOOR,
        context_mult=ctx,
        atr_mult=atr_mult,
        rr=rr,
        stop_cap_points=2000.0,
    )
    costs = CostModel(
        spread_markup_points=0.0,  # broker quotes already carry the real spread
        slippage_points=SLIPPAGE,
        stop_slippage_points=STOP_SLIPPAGE,
    )
    config = RunConfig(lot=LOT, max_hold_bars=MAX_HOLD[family], max_entries_per_day=2)
    return summarize(simulate(bars, signals, SymbolSpec.of(SYMBOL), costs, config))


def main() -> int:
    bars = load()
    windows = {name: slice_window(bars, *span) for name, span in PARTITIONS.items()}
    for name, frame in windows.items():
        stamps = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
        print(f"{name:11s} {len(frame):>7,} bars  {stamps.iloc[0].date()} .. {stamps.iloc[-1].date()}")
    print(f"\ncost: spread {SPREAD_POINTS} + slip {SLIPPAGE} + stop slip {STOP_SLIPPAGE} "
          f"= {ROUND_TRIP} pts ({ROUND_TRIP / 10:.1f} index pts); stop floor {STOP_FLOOR:.0f} pts\n")

    rows = []
    for family in US500_FAMILIES:
        for rr, atr_mult, ctx in itertools.product(RR_GRID, ATR_GRID, CONTEXT_GRID):
            design = evaluate(windows["design"], family, rr, atr_mult, ctx)
            if design["trades"] < MIN_TRADES:
                continue
            validation = evaluate(windows["validation"], family, rr, atr_mult, ctx)
            rows.append(
                {
                    "family": family, "rr": rr, "atr_mult": atr_mult, "context_mult": ctx,
                    "design_trades": design["trades"],
                    "design_pf": design["profit_factor"],
                    "design_net": design["net_usd"],
                    "design_wr": design["win_rate_pct"],
                    "val_trades": validation["trades"],
                    "val_pf": validation["profit_factor"],
                    "val_net": validation["net_usd"],
                    "val_wr": validation["win_rate_pct"],
                }
            )

    grid = pd.DataFrame(rows)
    grid.to_csv(ROOT / "outputs" / "US500_GRID.csv", index=False)

    print(f"{'family':16s} {'rr':>4} {'atr':>4} {'ctx':>4} | {'dTr':>4} {'dPF':>6} {'dNet$':>9} | "
          f"{'vTr':>4} {'vPF':>6} {'vNet$':>9}")
    print("-" * 88)
    for family, block in grid.groupby("family"):
        best = block.sort_values("design_pf", ascending=False).head(3)
        for _, r in best.iterrows():
            dpf = r["design_pf"] if r["design_pf"] is not None else float("nan")
            vpf = r["val_pf"] if r["val_pf"] is not None else float("nan")
            print(
                f"{family:16s} {r['rr']:>4} {r['atr_mult']:>4} {r['context_mult']:>4} | "
                f"{r['design_trades']:>4} {dpf:>6.3f} {r['design_net']:>9.2f} | "
                f"{r['val_trades']:>4} {vpf:>6.3f} {r['val_net']:>9.2f}"
            )
        print()

    survivors = grid[(grid["design_pf"] > 1.15) & (grid["val_pf"] > 1.15)]
    print(f"grid points profitable in BOTH design and validation (PF>1.15): {len(survivors)} of {len(grid)}")
    if len(survivors):
        print(survivors.sort_values("val_pf", ascending=False).head(8).to_string(index=False))

    (ROOT / "outputs" / "US500_SEARCH.json").write_text(
        json.dumps(
            {
                "schema_version": "us500_search_v1",
                "source": "Capital.com broker M5 (measured spread)",
                "partitions": PARTITIONS,
                "cost_points_round_trip": ROUND_TRIP,
                "grid_points": int(len(grid)),
                "survivors_both_windows": int(len(survivors)),
                "survivors": survivors.to_dict("records"),
            },
            indent=2, sort_keys=True, default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {ROOT / 'outputs' / 'US500_SEARCH.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
