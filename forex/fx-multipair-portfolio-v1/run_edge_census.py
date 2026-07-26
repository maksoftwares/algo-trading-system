"""Exploratory forward-return census on the design window.

R1 closed bar-geometry families, so before proposing anything else this measures
*where* predictability exists at all. Cost-free mid-to-mid returns answer "is
there signal", separately from "can it be traded".

Discipline:

* Design window only (2016-07-01 .. 2021-12-31). Validation and final-exam
  windows are never read here, so they stay clean for a v2 preregistration.
* Forward returns are normalised by ATR so pairs are comparable.
* t-statistics use **non-overlapping** samples (stride = horizon), because
  overlapping forward windows inflate significance badly.
* A conditioner is only interesting if it has the same sign and comparable size
  on all three pairs. Single-pair findings are treated as noise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import add_time_columns, load_m5, mid  # noqa: E402
from src.indicators import atr, shift  # noqa: E402
from src.report import PARTITIONS, slice_window  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
HORIZONS = {"1h": 12, "4h": 48, "1d": 288}


def build_frame(symbol: str) -> pd.DataFrame:
    bars = slice_window(load_m5(CACHE, symbol), *PARTITIONS["design"])
    timed = add_time_columns(bars)
    close = mid(bars, "close")
    high = mid(bars, "high")
    low = mid(bars, "low")

    # ATR on M5, scaled to a 1h reference so normalisation is stable.
    atr_m5 = atr(high, low, close, 288)
    frame = pd.DataFrame(
        {
            "timestamp_utc": timed["timestamp_utc"],
            "hour": timed["hour"],
            "weekday": timed["weekday"],
            "close": close,
            "atr": atr_m5,
            "tick_count": bars["tick_count"].to_numpy(),
            "spread": bars["ask_close"].to_numpy() - bars["bid_close"].to_numpy(),
        }
    )
    for name, horizon in HORIZONS.items():
        forward = np.full(close.size, np.nan)
        forward[: close.size - horizon] = close[horizon:] - close[: close.size - horizon]
        frame[f"fwd_{name}"] = forward / frame["atr"]
    for name, lookback in (("1h", 12), ("4h", 48), ("1d", 288), ("3d", 864)):
        frame[f"past_{name}"] = (close - shift(close, lookback)) / frame["atr"]
    frame["dist_mean_1d"] = (
        close - pd.Series(close).rolling(288).mean().to_numpy()
    ) / frame["atr"]
    frame["atr_pct"] = frame["atr"].rank(pct=True)
    frame["tick_pct"] = frame["tick_count"].rolling(288, min_periods=50).mean().rank(pct=True)
    month_end = frame["timestamp_utc"].dt.is_month_end
    frame["month_edge"] = np.where(
        month_end | frame["timestamp_utc"].dt.day.le(2), "edge", "middle"
    )
    return frame


def stat(values: np.ndarray) -> dict:
    values = values[np.isfinite(values)]
    if values.size < 30:
        return {"n": int(values.size), "mean_atr": None, "t": None}
    mean = float(values.mean())
    t = mean / (float(values.std(ddof=1)) / np.sqrt(values.size))
    return {"n": int(values.size), "mean_atr": round(mean, 5), "t": round(t, 2)}


def census(frames: dict[str, pd.DataFrame], horizon_name: str) -> dict:
    """Bucket forward returns by each conditioner, on non-overlapping samples."""
    stride = HORIZONS[horizon_name]
    target = f"fwd_{horizon_name}"
    results: dict[str, dict] = {}

    def add(conditioner: str, bucket: object, symbol: str, values: np.ndarray) -> None:
        key = f"{conditioner}={bucket}"
        results.setdefault(key, {})[symbol] = stat(values)

    for symbol, frame in frames.items():
        sample = frame.iloc[::stride]
        add("all", "all", symbol, sample[target].to_numpy())

        for hour, block in sample.groupby("hour"):
            add("hour", int(hour), symbol, block[target].to_numpy())
        for weekday, block in sample.groupby("weekday"):
            add("weekday", int(weekday), symbol, block[target].to_numpy())
        for edge, block in sample.groupby("month_edge"):
            add("month_edge", str(edge), symbol, block[target].to_numpy())

        # Signed conditioners: report forward return *aligned with the signal*,
        # so a positive mean means "follow it" and negative means "fade it".
        for lookback in ("1h", "4h", "1d", "3d"):
            past = sample[f"past_{lookback}"].to_numpy()
            aligned = np.sign(past) * sample[target].to_numpy()
            for label, mask in (
                ("any", np.isfinite(past)),
                ("big", np.abs(past) >= 1.0),
                ("huge", np.abs(past) >= 2.0),
            ):
                add(f"momentum_{lookback}_{label}", "signed", symbol, aligned[mask])

        dist = sample["dist_mean_1d"].to_numpy()
        aligned = np.sign(dist) * sample[target].to_numpy()
        for label, mask in (("any", np.isfinite(dist)), ("big", np.abs(dist) >= 1.0)):
            add(f"revert_from_1d_mean_{label}", "signed", symbol, aligned[mask])

        for label, mask in (
            ("low_vol", sample["atr_pct"] <= 0.33),
            ("high_vol", sample["atr_pct"] >= 0.67),
        ):
            past = sample["past_4h"].to_numpy()
            add(f"momentum_4h_{label}", "signed", symbol, (np.sign(past) * sample[target].to_numpy())[mask.to_numpy()])

    return results


def consistent(entry: dict, min_abs_t: float = 2.0) -> bool:
    """Same sign on all pairs and |t| >= threshold on at least two."""
    means = [entry[symbol]["mean_atr"] for symbol in SYMBOLS if symbol in entry]
    ts = [entry[symbol]["t"] for symbol in SYMBOLS if symbol in entry]
    if len(means) < 3 or any(value is None for value in means):
        return False
    if not (all(value > 0 for value in means) or all(value < 0 for value in means)):
        return False
    return sum(1 for value in ts if value is not None and abs(value) >= min_abs_t) >= 2


def main() -> int:
    print("building design-window frames (2016-07-01 .. 2021-12-31)")
    frames = {symbol: build_frame(symbol) for symbol in SYMBOLS}
    report: dict[str, object] = {
        "schema_version": "fx_edge_census_v1",
        "window": {"start": PARTITIONS["design"][0], "end_exclusive": PARTITIONS["design"][1]},
        "note": "exploratory, design window only; t-stats on non-overlapping samples",
        "horizons": {},
    }

    for horizon in HORIZONS:
        results = census(frames, horizon)
        report["horizons"][horizon] = results
        hits = {key: entry for key, entry in results.items() if consistent(entry)}
        print(f"\n=== horizon {horizon}: {len(hits)} cross-pair consistent of {len(results)} buckets ===")
        ordered = sorted(
            hits.items(),
            key=lambda item: -min(abs(item[1][s]["t"]) for s in SYMBOLS if item[1][s]["t"] is not None),
        )
        for key, entry in ordered[:14]:
            detail = "  ".join(
                f"{symbol}:{entry[symbol]['mean_atr']:+.4f}(t{entry[symbol]['t']:+.1f},n{entry[symbol]['n']})"
                for symbol in SYMBOLS
            )
            print(f"  {key:34s} {detail}")

    out = ROOT / "outputs" / "EDGE_CENSUS.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
