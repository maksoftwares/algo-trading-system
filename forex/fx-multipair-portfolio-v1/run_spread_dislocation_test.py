"""R10: the fixed-spread structural advantage, tested rather than assumed.

The one genuine asymmetry this lane measured and never exploited. The broker
quotes a **fixed** spread (EURUSD 0.70 pips at every hour), while the true
interbank spread in the Dukascopy quotes reaches 3.0 pips at its 99th percentile.
In those moments the account is being offered materially better-than-market
execution.

That matters because liquidity withdrawal is exactly when transient price
dislocations are largest, and R7 already established a real mean-reversion effect
in signed tick flow (t = -9.3 / -7.8 / -6.3). R8 conditioned on *realised
volatility* and failed; **quoted spread is a different variable** — it measures
market-maker inventory stress specifically, not the size of moves.

So: measure the R7 effects inside the widest-true-spread bars, and charge the
broker's FIXED cost rather than the true spread.

Multiple-testing control, learned from R8. The grid is pre-specified and small:
2 signals x 4 horizons x 3 pairs x (top spread decile only) = **24 cells**, versus
R8's 300. Design-window selection is then replicated on validation with the same
cell, sign and cost bar. Nothing is reported as a candidate without replication.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import INSTRUMENTS, load_m5, mid  # noqa: E402
from src.report import (  # noqa: E402
    MEASURED_ROUND_TRIP_POINTS,
    PARTITIONS,
    slice_window,
)

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
SIGNALS = ("signed_flow", "micro_dev_points")
HORIZONS = {"5m": 1, "15m": 3, "30m": 6, "60m": 12}
STRESS_DECILE = 0.90  # top 10% of bars by quoted spread
SIGNAL_DECILES = 10


def build(symbol: str, partition: str) -> pd.DataFrame:
    bars = slice_window(load_m5(CACHE, symbol), *PARTITIONS[partition])
    micro = pd.read_parquet(CACHE / "micro" / f"{symbol}_M5_MICRO.parquet")
    frame = bars.merge(micro, on="timestamp_ms", how="inner", suffixes=("", "_micro"))
    point = float(INSTRUMENTS[symbol]["point_size"])
    close = mid(frame, "close")
    for name, horizon in HORIZONS.items():
        forward = np.full(close.size, np.nan)
        forward[: close.size - horizon] = close[horizon:] - close[: close.size - horizon]
        frame[f"fwd_{name}"] = forward / point
    # Liquidity stress must be known at decision time, so lag it one bar.
    frame["stress"] = pd.Series(frame["spread_mean_points"].to_numpy()).shift(1).to_numpy()
    return frame


def evaluate(frame: pd.DataFrame, signal: str, horizon: str, cost: float) -> dict:
    stride = HORIZONS[horizon]
    sample = frame.iloc[::stride]
    values = sample[signal].to_numpy(dtype=float)
    target = sample[f"fwd_{horizon}"].to_numpy(dtype=float)
    stress = sample["stress"].to_numpy(dtype=float)
    ok = np.isfinite(values) & np.isfinite(target) & np.isfinite(stress)
    values, target, stress = values[ok], target[ok], stress[ok]
    if values.size < 2000:
        return {}

    threshold = np.quantile(stress, STRESS_DECILE)
    mask = stress >= threshold
    if mask.sum() < 400:
        return {}
    block_values, block_target = values[mask], target[mask]

    edges = np.quantile(block_values, np.linspace(0, 1, SIGNAL_DECILES + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    decile = np.clip(np.searchsorted(edges, block_values, side="right") - 1, 0, SIGNAL_DECILES - 1)
    top, bottom = block_target[decile == SIGNAL_DECILES - 1], block_target[decile == 0]
    if top.size < 40 or bottom.size < 40:
        return {}

    def side(values_: np.ndarray) -> tuple[float, float]:
        mean = float(values_.mean())
        return mean, mean / (float(values_.std(ddof=1)) / np.sqrt(values_.size))

    top_mean, top_t = side(top)
    bottom_mean, bottom_t = side(bottom)
    best = max(abs(top_mean), abs(bottom_mean))
    return {
        "n_stress_bars": int(mask.sum()),
        "stress_threshold_points": round(float(threshold), 1),
        "top_mean_points": round(top_mean, 2),
        "top_t": round(top_t, 2),
        "bottom_mean_points": round(bottom_mean, 2),
        "bottom_t": round(bottom_t, 2),
        "best_abs_edge_points": round(best, 2),
        "fixed_broker_cost_points": cost,
        "edge_over_cost": round(best / cost, 3),
        "clears_cost": bool(best > cost),
        "signed_edge": top_mean if abs(top_mean) >= abs(bottom_mean) else bottom_mean,
        "signed_t": top_t if abs(top_mean) >= abs(bottom_mean) else bottom_t,
    }


def main() -> int:
    print("R10 spread-dislocation test — trade only the widest-true-spread bars,")
    print("     pay the broker's FIXED cost instead of the true spread.\n")
    for symbol in SYMBOLS:
        raw = load_m5(CACHE, symbol)
        point = float(INSTRUMENTS[symbol]["point_size"])
        spread = (raw["ask_close"] - raw["bid_close"]) / point
        print(
            f"   {symbol}: true spread p90 {np.quantile(spread,0.90):.0f} / "
            f"p99 {np.quantile(spread,0.99):.0f} pts vs fixed broker cost "
            f"{MEASURED_ROUND_TRIP_POINTS[symbol]:.0f} pts"
        )
    print()

    report: dict[str, object] = {
        "schema_version": "fx_spread_dislocation_v1",
        "hypothesis": "fixed broker spread is a structural edge inside liquidity-stress bars",
        "grid_cells": len(SIGNALS) * len(HORIZONS) * len(SYMBOLS),
        "stress_definition": f"lagged quoted spread >= its {STRESS_DECILE:.0%} quantile",
        "design": {},
        "validation": {},
    }

    design_frames = {symbol: build(symbol, "design") for symbol in SYMBOLS}
    selected = []
    print(f"{'signal':17s} {'hz':>4} {'sym':7s} {'edge':>8} {'cost':>6} {'x':>6} {'t':>7}")
    print("-" * 60)
    for signal in SIGNALS:
        for horizon in HORIZONS:
            for symbol in SYMBOLS:
                cost = MEASURED_ROUND_TRIP_POINTS[symbol]
                result = evaluate(design_frames[symbol], signal, horizon, cost)
                if not result:
                    continue
                report["design"].setdefault(signal, {}).setdefault(horizon, {})[symbol] = result
                flag = ""
                if result["clears_cost"] and abs(result["signed_t"]) > 2.0:
                    selected.append((signal, horizon, symbol))
                    flag = "  <== selected"
                print(
                    f"{signal:17s} {horizon:>4} {symbol:7s} {result['best_abs_edge_points']:>8.2f} "
                    f"{cost:>6.0f} {result['edge_over_cost']:>6.2f} {result['signed_t']:>7.2f}{flag}"
                )

    print(f"\ndesign cells selected: {len(selected)} of {report['grid_cells']} "
          f"(expected by chance at 5%: ~{0.05*report['grid_cells']:.1f})")

    if not selected:
        report["verdict"] = "R10_REJECTED_NOTHING_CLEARED_COST"
        print("\nverdict: R10_REJECTED_NOTHING_CLEARED_COST")
    else:
        print("\nreplicating on validation (same cell, sign and cost bar)...")
        validation_frames = {symbol: build(symbol, "validation") for symbol in SYMBOLS}
        replicated = 0
        print(f"\n{'signal':17s} {'hz':>4} {'sym':7s} {'design':>9} {'valid':>9} {'valid_t':>8} {'same_sign':>10}")
        print("-" * 68)
        for signal, horizon, symbol in selected:
            cost = MEASURED_ROUND_TRIP_POINTS[symbol]
            design_edge = report["design"][signal][horizon][symbol]["signed_edge"]
            result = evaluate(validation_frames[symbol], signal, horizon, cost)
            report["validation"].setdefault(signal, {}).setdefault(horizon, {})[symbol] = result
            if not result:
                print(f"{signal:17s} {horizon:>4} {symbol:7s} {design_edge:>9.2f} {'absent':>9}")
                continue
            same_sign = (design_edge > 0) == (result["signed_edge"] > 0)
            holds = same_sign and result["clears_cost"] and abs(result["signed_t"]) > 2.0
            replicated += int(holds)
            print(
                f"{signal:17s} {horizon:>4} {symbol:7s} {design_edge:>9.2f} "
                f"{result['signed_edge']:>9.2f} {result['signed_t']:>8.2f} {str(same_sign):>10}"
                f"{'   <== REPLICATES' if holds else ''}"
            )
        report["replicated"] = replicated
        report["verdict"] = (
            "R10_REPLICATED_BUILD_CANDIDATE" if replicated else "R10_REJECTED_DID_NOT_REPLICATE"
        )
        print(f"\nreplicated: {replicated} of {len(selected)}")
        print(f"verdict: {report['verdict']}")

    out = ROOT / "outputs" / "SPREAD_DISLOCATION_TEST.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
