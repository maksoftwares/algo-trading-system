"""R7: does tick microstructure predict moves larger than real broker cost?

Every earlier test read OHLC bars. This reads order-book depth, microprice
deviation and quote-update asymmetry — information bars do not contain — and is
scored against the *measured* Capital.com fixed spread rather than an assumption.

Scoring bar. A strategy that goes long in a feature's top decile and short in
its bottom decile earns roughly ``(top_mean - bottom_mean) / 2`` points per
trade before cost. To be tradeable that decile spread must therefore exceed
**twice** the measured round-trip cost (22 points on EURUSD, 34 on GBPUSD, 32 on
USDJPY). Anything below that is a real but unbankable regularity.

Design window only; validation and final exam stay untouched unless something
clears the bar here.
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
FEATURES = (
    "depth_imbalance",
    "micro_dev_points",
    "quote_asym",
    "signed_flow",
    "rv_points",
    "spread_mean_points",
)
HORIZONS = {"5m": 1, "15m": 3, "30m": 6, "60m": 12}
DECILES = 10


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
    # combined signal: mean of z-scored directional features
    directional = ["depth_imbalance", "micro_dev_points", "quote_asym", "signed_flow"]
    stacked = []
    for name in directional:
        values = frame[name].to_numpy(dtype=float)
        stacked.append((values - np.nanmean(values)) / np.nanstd(values))
    frame["combo"] = np.nanmean(np.vstack(stacked), axis=0)
    return frame


def decile_spread(frame: pd.DataFrame, feature: str, horizon: str) -> dict:
    stride = HORIZONS[horizon]
    sample = frame.iloc[::stride]
    values = sample[feature].to_numpy(dtype=float)
    target = sample[f"fwd_{horizon}"].to_numpy(dtype=float)
    ok = np.isfinite(values) & np.isfinite(target)
    values, target = values[ok], target[ok]
    if values.size < 500:
        return {"n": int(values.size)}
    edges = np.quantile(values, np.linspace(0, 1, DECILES + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    bucket = np.clip(np.searchsorted(edges, values, side="right") - 1, 0, DECILES - 1)
    top, bottom = target[bucket == DECILES - 1], target[bucket == 0]
    if top.size < 50 or bottom.size < 50:
        return {"n": int(values.size)}
    difference = float(top.mean() - bottom.mean())
    standard_error = np.sqrt(top.var(ddof=1) / top.size + bottom.var(ddof=1) / bottom.size)
    return {
        "n": int(values.size),
        "top_mean_points": round(float(top.mean()), 2),
        "bottom_mean_points": round(float(bottom.mean()), 2),
        "decile_spread_points": round(difference, 2),
        "t": round(difference / standard_error, 2) if standard_error > 0 else None,
    }


def main() -> int:
    print("R7 microstructure census — design window only\n")
    print("required decile spread = 2x measured round-trip cost:")
    for symbol in SYMBOLS:
        print(f"  {symbol}: cost {MEASURED_ROUND_TRIP_POINTS[symbol]:.0f} pts -> need > {2*MEASURED_ROUND_TRIP_POINTS[symbol]:.0f} pts")
    print()

    frames = {symbol: build(symbol, "design") for symbol in SYMBOLS}
    report: dict[str, object] = {
        "schema_version": "fx_micro_census_v1",
        "window": dict(zip(("start", "end_exclusive"), PARTITIONS["design"])),
        "scoring_bar": "decile spread must exceed 2x measured round-trip cost",
        "measured_round_trip_points": {s: MEASURED_ROUND_TRIP_POINTS[s] for s in SYMBOLS},
        "results": {},
    }

    any_pass = False
    for feature in (*FEATURES, "combo"):
        print(f"--- {feature}")
        for horizon in HORIZONS:
            cells, passes = [], []
            for symbol in SYMBOLS:
                result = decile_spread(frames[symbol], feature, horizon)
                report["results"].setdefault(feature, {}).setdefault(horizon, {})[symbol] = result
                spread = result.get("decile_spread_points")
                t = result.get("t")
                if spread is None:
                    cells.append(f"{symbol}:n/a")
                    continue
                need = 2 * MEASURED_ROUND_TRIP_POINTS[symbol]
                ok = abs(spread) > need
                passes.append(ok)
                cells.append(f"{symbol}:{spread:+7.2f}(t{t:+5.1f}){'*' if ok else ' '}")
            if any(passes):
                any_pass = True
            print(f"   {horizon:>4}  " + "  ".join(cells))
        print()

    report["any_feature_cleared_cost_bar"] = any_pass
    out = ROOT / "outputs" / "MICRO_CENSUS.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"* = decile spread exceeds 2x measured cost")
    print(f"any feature cleared the cost bar on any pair: {any_pass}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
