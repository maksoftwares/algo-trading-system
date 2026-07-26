"""R8: does a FIXED broker spread become affordable in high volatility?

The overlooked implication of the measured cost structure. This broker quotes a
*fixed* spread (EURUSD 0.70 pips at every hour bar the 21:00 rollover), while the
size of predictable moves scales with volatility. R7 measured microstructure
effects averaged over all conditions and found ~1.6 points against a 7-point
spread — but that average mixes calm hours, where cost dominates, with volatile
hours, where it may not.

So: bucket by realised volatility, then measure the signal inside each bucket in
points, against the same fixed cost.

Scoring. A single-sided strategy (long when the signal is in its bottom decile,
short when in its top decile) earns roughly the absolute mean forward return of
that decile per trade. The bar is therefore
``max(|top_mean|, |bottom_mean|) > measured round-trip cost`` — 11 points on
EURUSD, 17 on GBPUSD, 16 on USDJPY. That is a *weaker* and more honest bar than
R7's two-sided version, which double-counted cost.

Design window only.
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
from src.report import MEASURED_ROUND_TRIP_POINTS, PARTITIONS, slice_window  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
SIGNALS = ("signed_flow", "depth_imbalance", "micro_dev_points", "combo")
HORIZONS = {"5m": 1, "15m": 3, "30m": 6, "60m": 12, "4h": 48}
VOL_BUCKETS = 5  # quintiles of trailing realised volatility
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

    directional = ["depth_imbalance", "micro_dev_points", "quote_asym", "signed_flow"]
    stacked = []
    for name in directional:
        values = frame[name].to_numpy(dtype=float)
        stacked.append((values - np.nanmean(values)) / np.nanstd(values))
    frame["combo"] = np.nanmean(np.vstack(stacked), axis=0)

    # Trailing realised volatility, strictly backward-looking (shifted by 1).
    trailing = pd.Series(frame["rv_points"].to_numpy()).rolling(48).mean().shift(1)
    frame["vol_trailing"] = trailing.to_numpy()
    return frame


def evaluate(frame: pd.DataFrame, signal: str, horizon: str, cost: float) -> list[dict]:
    stride = HORIZONS[horizon]
    sample = frame.iloc[::stride]
    values = sample[signal].to_numpy(dtype=float)
    target = sample[f"fwd_{horizon}"].to_numpy(dtype=float)
    vol = sample["vol_trailing"].to_numpy(dtype=float)
    ok = np.isfinite(values) & np.isfinite(target) & np.isfinite(vol)
    values, target, vol = values[ok], target[ok], vol[ok]
    if values.size < 2000:
        return []

    vol_edges = np.quantile(vol, np.linspace(0, 1, VOL_BUCKETS + 1))
    vol_edges[0], vol_edges[-1] = -np.inf, np.inf
    vol_bucket = np.clip(np.searchsorted(vol_edges, vol, side="right") - 1, 0, VOL_BUCKETS - 1)

    rows = []
    for bucket in range(VOL_BUCKETS):
        mask = vol_bucket == bucket
        if mask.sum() < 400:
            continue
        block_values, block_target = values[mask], target[mask]
        edges = np.quantile(block_values, np.linspace(0, 1, SIGNAL_DECILES + 1))
        edges[0], edges[-1] = -np.inf, np.inf
        decile = np.clip(np.searchsorted(edges, block_values, side="right") - 1, 0, SIGNAL_DECILES - 1)
        top = block_target[decile == SIGNAL_DECILES - 1]
        bottom = block_target[decile == 0]
        if top.size < 40 or bottom.size < 40:
            continue

        def side(values_: np.ndarray) -> tuple[float, float]:
            mean = float(values_.mean())
            t = mean / (float(values_.std(ddof=1)) / np.sqrt(values_.size))
            return mean, t

        top_mean, top_t = side(top)
        bottom_mean, bottom_t = side(bottom)
        best = max(abs(top_mean), abs(bottom_mean))
        rows.append(
            {
                "vol_quintile": bucket + 1,
                "median_vol_points": round(float(np.median(vol[mask])), 1),
                "n": int(mask.sum()),
                "top_mean_points": round(top_mean, 2),
                "top_t": round(top_t, 2),
                "bottom_mean_points": round(bottom_mean, 2),
                "bottom_t": round(bottom_t, 2),
                "best_abs_edge_points": round(best, 2),
                "cost_points": cost,
                "edge_over_cost": round(best / cost, 3),
                "clears_cost": bool(best > cost),
            }
        )
    return rows


def main() -> int:
    print("R8 volatility-conditioned census — design window only")
    print("bar: |decile mean| > measured round-trip cost (single-sided strategy)")
    for symbol in SYMBOLS:
        print(f"   {symbol}: cost {MEASURED_ROUND_TRIP_POINTS[symbol]:.0f} pts")
    print()

    frames = {symbol: build(symbol, "design") for symbol in SYMBOLS}
    report: dict[str, object] = {
        "schema_version": "fx_vol_conditioned_census_v1",
        "window": dict(zip(("start", "end_exclusive"), PARTITIONS["design"])),
        "scoring_bar": "max(|top decile mean|, |bottom decile mean|) > measured round-trip cost",
        "results": {},
    }
    winners = []

    for signal in SIGNALS:
        print(f"===== {signal}")
        for horizon in HORIZONS:
            for symbol in SYMBOLS:
                cost = MEASURED_ROUND_TRIP_POINTS[symbol]
                rows = evaluate(frames[symbol], signal, horizon, cost)
                report["results"].setdefault(signal, {}).setdefault(horizon, {})[symbol] = rows
                if not rows:
                    continue
                best = max(rows, key=lambda row: row["best_abs_edge_points"])
                flag = "  <== CLEARS" if best["clears_cost"] else ""
                print(
                    f"  {horizon:>4} {symbol}  best vol-Q{best['vol_quintile']} "
                    f"(vol {best['median_vol_points']:>5.0f}pt): edge {best['best_abs_edge_points']:>6.2f}pt "
                    f"/ cost {cost:.0f} = {best['edge_over_cost']:>5.2f}"
                    f"  [top {best['top_mean_points']:+6.2f} t{best['top_t']:+5.1f} | "
                    f"bot {best['bottom_mean_points']:+6.2f} t{best['bottom_t']:+5.1f}]{flag}"
                )
                for row in rows:
                    if row["clears_cost"] and abs(row["top_t"]) > 2 or (row["clears_cost"] and abs(row["bottom_t"]) > 2):
                        winners.append({"signal": signal, "horizon": horizon, "symbol": symbol, **row})
        print()

    report["candidates_clearing_cost_with_t_over_2"] = winners
    out = ROOT / "outputs" / "VOL_CONDITIONED_CENSUS.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"candidates clearing cost with |t| > 2: {len(winners)}")
    for winner in winners[:20]:
        print(
            f"   {winner['signal']:16s} {winner['horizon']:>4} {winner['symbol']} "
            f"volQ{winner['vol_quintile']}  edge {winner['best_abs_edge_points']:.2f}pt "
            f"(x{winner['edge_over_cost']:.2f} cost)  n={winner['n']}"
        )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
