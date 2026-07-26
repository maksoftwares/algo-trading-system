"""Design-window parameter search, per PREREGISTRATION.md sections 7 and 9.

One parameter set is chosen per family and applied identically to all three
pairs. Selection maximises the *median* PF across pairs subject to every pair
being profitable, a trade-count floor, and a plateau requirement. Nothing is
chosen on a single pair's best result.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.engine import CostModel, RunConfig, SymbolSpec, simulate  # noqa: E402
from src.fxdata import load_m5  # noqa: E402
from src.report import (  # noqa: E402
    COSTS,
    PARTITIONS,
    STOP_FLOOR_POINTS,
    profit_factor,
    slice_window,
    summarize,
)
from src.strategies import FAMILIES, build_signals  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")

RR_GRID = (1.2, 1.5, 2.0, 2.5)
ATR_GRID = (1.0, 1.5, 2.0, 3.0)
CONTEXT_GRID = (0.0, 0.5, 1.0)
STOP_CAP_POINTS = 1500.0
MAX_HOLD = {"london_breakout": 288, "asia_fade": 288, "donchian_h4": 288 * 10}
MIN_DESIGN_TRADES = 60


def run_grid(partition: str = "design") -> pd.DataFrame:
    start, end = PARTITIONS[partition]
    rows: list[dict] = []
    for family, builder in FAMILIES.items():
        for symbol in SYMBOLS:
            bars = slice_window(load_m5(CACHE, symbol), start, end)
            candidates = builder(bars, symbol)
            spec = SymbolSpec.of(symbol)
            costs = CostModel(**COSTS[symbol])
            config = RunConfig(
                lot=0.01,
                max_hold_bars=MAX_HOLD[family],
                max_entries_per_day=3,
                one_position_only=True,
            )
            began = time.time()
            for rr, atr_mult, context_mult in itertools.product(RR_GRID, ATR_GRID, CONTEXT_GRID):
                signals = build_signals(
                    candidates,
                    stop_floor_points=STOP_FLOOR_POINTS[symbol],
                    context_mult=context_mult,
                    atr_mult=atr_mult,
                    rr=rr,
                    stop_cap_points=STOP_CAP_POINTS,
                )
                result = summarize(simulate(bars, signals, spec, costs, config))
                rows.append(
                    {
                        "family": family,
                        "symbol": symbol,
                        "rr": rr,
                        "atr_mult": atr_mult,
                        "context_mult": context_mult,
                        **result,
                    }
                )
            print(
                f"  {family:16s} {symbol}  {len(RR_GRID) * len(ATR_GRID) * len(CONTEXT_GRID)} points "
                f"in {time.time() - began:.0f}s  (candidates={len(candidates)})",
                flush=True,
            )
    return pd.DataFrame(rows)


def select(grid: pd.DataFrame) -> dict:
    """Apply the preregistered selection rule to each family."""
    chosen: dict[str, dict] = {}
    for family, block in grid.groupby("family"):
        pivot = block.pivot_table(
            index=["rr", "atr_mult", "context_mult"],
            columns="symbol",
            values=["profit_factor", "trades"],
        )
        candidates: list[dict] = []
        for key, row in pivot.iterrows():
            pfs = [row[("profit_factor", symbol)] for symbol in SYMBOLS]
            counts = [row[("trades", symbol)] for symbol in SYMBOLS]
            if any(pd.isna(value) for value in pfs):
                continue
            if not all(value > 1.0 for value in pfs):
                continue
            if not all(count >= MIN_DESIGN_TRADES for count in counts):
                continue
            candidates.append(
                {
                    "rr": key[0],
                    "atr_mult": key[1],
                    "context_mult": key[2],
                    "median_pf": float(np.median(pfs)),
                    "min_pf": float(np.min(pfs)),
                    "per_symbol_pf": {symbol: float(value) for symbol, value in zip(SYMBOLS, pfs)},
                    "per_symbol_trades": {symbol: int(count) for symbol, count in zip(SYMBOLS, counts)},
                }
            )

        if not candidates:
            chosen[family] = {"selected": None, "reason": "no grid point satisfied all-pairs PF>1 with min trades"}
            continue

        viable = {(item["rr"], item["atr_mult"], item["context_mult"]) for item in candidates}

        def neighbours(item: dict) -> int:
            count = 0
            for grid_values, key in ((RR_GRID, "rr"), (ATR_GRID, "atr_mult")):
                position = grid_values.index(item[key])
                for step in (-1, 1):
                    probe = position + step
                    if 0 <= probe < len(grid_values):
                        variant = dict(item)
                        variant[key] = grid_values[probe]
                        if (variant["rr"], variant["atr_mult"], variant["context_mult"]) in viable:
                            count += 1
            return count

        for item in candidates:
            item["viable_neighbours"] = neighbours(item)

        plateau = [item for item in candidates if item["viable_neighbours"] >= 2]
        pool = plateau if plateau else candidates
        # median PF desc, then wider stop (higher atr_mult), then lower rr
        pool.sort(key=lambda item: (-item["median_pf"], -item["atr_mult"], item["rr"]))
        chosen[family] = {
            "selected": {
                key: pool[0][key] for key in ("rr", "atr_mult", "context_mult")
            },
            "design_median_pf": round(pool[0]["median_pf"], 4),
            "design_min_pf": round(pool[0]["min_pf"], 4),
            "design_per_symbol_pf": {k: round(v, 4) for k, v in pool[0]["per_symbol_pf"].items()},
            "design_per_symbol_trades": pool[0]["per_symbol_trades"],
            "viable_grid_points": len(candidates),
            "plateau_grid_points": len(plateau),
            "plateau_requirement_met": bool(plateau),
        }
    return chosen


def main() -> int:
    print(f"design window {PARTITIONS['design'][0]} .. {PARTITIONS['design'][1]}\n")
    grid = run_grid("design")
    grid.to_csv(ROOT / "outputs" / "DESIGN_GRID.csv", index=False)

    selection = select(grid)
    print("\n=== preregistered selection (median PF across pairs, all pairs PF>1) ===")
    for family, payload in selection.items():
        if payload.get("selected") is None:
            print(f"{family:16s} REJECTED: {payload['reason']}")
            continue
        chosen = payload["selected"]
        per_symbol = "  ".join(
            f"{symbol}={value:.3f}" for symbol, value in payload["design_per_symbol_pf"].items()
        )
        print(
            f"{family:16s} rr={chosen['rr']} atr_mult={chosen['atr_mult']} "
            f"context_mult={chosen['context_mult']}  medianPF={payload['design_median_pf']:.3f}  "
            f"[{per_symbol}]  viable={payload['viable_grid_points']}/48 "
            f"plateau={payload['plateau_grid_points']}"
        )

    out = ROOT / "outputs" / "DESIGN_SELECTION.json"
    out.write_text(
        json.dumps(
            {
                "schema_version": "fx_design_selection_v1",
                "window": {"start": PARTITIONS["design"][0], "end_exclusive": PARTITIONS["design"][1]},
                "grid": {"rr": list(RR_GRID), "atr_mult": list(ATR_GRID), "context_mult": list(CONTEXT_GRID)},
                "selection_rule": "max median PF across pairs; all pairs PF>1; >=60 trades/pair; plateau>=2 neighbours",
                "stop_floor_points": STOP_FLOOR_POINTS,
                "costs": COSTS,
                "families": selection,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {out}")
    print(f"wrote {ROOT / 'outputs' / 'DESIGN_GRID.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
