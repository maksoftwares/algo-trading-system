"""Construct EURGBP / EURJPY / GBPJPY M5 bid/ask bars from the USD majors.

The remaining untested gap. Crosses are less efficient than majors (less
arbitrage attention), EURJPY and GBPJPY are the classic trending carry crosses,
and EURGBP is persistently range-bound — genuinely different dynamics from the
three USD majors that R1-R8 closed. They are tradeable on the account
(``trade_mode`` FULL) but the terminal holds no tick history for them, so they
are built here instead.

Construction is arbitrage-exact on the quote sides:

    EURGBP_bid = EURUSD_bid / GBPUSD_ask      EURGBP_ask = EURUSD_ask / GBPUSD_bid
    EURJPY_bid = EURUSD_bid * USDJPY_bid      EURJPY_ask = EURUSD_ask * USDJPY_ask
    GBPJPY_bid = GBPUSD_bid * USDJPY_bid      GBPJPY_ask = GBPUSD_ask * USDJPY_ask

Two approximations, both recorded rather than hidden:

* **Intrabar extremes are outer bounds.** The true high of a ratio is not the
  ratio of the legs' extremes, so high/low use the arbitrage-bounding
  combination. This makes the modelled range slightly *wider* than reality,
  which makes stops marginally easier to hit — the conservative direction for a
  stop-first engine.
* **Spread is the sum of the legs' spreads**, which is what synthesising the
  cross would actually cost. A broker quoting the cross directly is usually
  tighter, so this is pessimistic. Using measured majors, that implies EURGBP
  2.0 pips, EURJPY 1.9, GBPJPY 2.5.

Open/close combine the legs' own open/close and are exact up to the legs' first
and last tick landing at slightly different instants inside the bar.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.fxdata import cache_path, iso, load_m5, sha256_file  # noqa: E402
from src.report import MEASURED_SPREAD_POINTS  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")

# cross -> (numerator leg, denominator leg or None, second multiply leg or None)
# "ratio": a / b ; "product": a * b
CROSSES = {
    "EURGBP": {"kind": "ratio", "a": "EURUSD", "b": "GBPUSD", "point": 0.00001, "scale": 5},
    "EURJPY": {"kind": "product", "a": "EURUSD", "b": "USDJPY", "point": 0.001, "scale": 3},
    "GBPJPY": {"kind": "product", "a": "GBPUSD", "b": "USDJPY", "point": 0.001, "scale": 3},
}
FIELDS = ("open", "high", "low", "close")


def build_cross(name: str, spec: dict, legs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    a = legs[spec["a"]].set_index("timestamp_ms")
    b = legs[spec["b"]].set_index("timestamp_ms")
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    scale = spec["scale"]
    out = {"timestamp_ms": common.to_numpy(np.int64)}

    if spec["kind"] == "ratio":
        # bid = a_bid / b_ask (sell a, buy b); ask = a_ask / b_bid
        for field in FIELDS:
            if field in ("open", "close"):
                out[f"bid_{field}"] = a[f"bid_{field}"].to_numpy() / b[f"ask_{field}"].to_numpy()
                out[f"ask_{field}"] = a[f"ask_{field}"].to_numpy() / b[f"bid_{field}"].to_numpy()
        # bounding extremes: max of a/b is a_high / b_low
        out["bid_high"] = a["bid_high"].to_numpy() / b["ask_low"].to_numpy()
        out["bid_low"] = a["bid_low"].to_numpy() / b["ask_high"].to_numpy()
        out["ask_high"] = a["ask_high"].to_numpy() / b["bid_low"].to_numpy()
        out["ask_low"] = a["ask_low"].to_numpy() / b["bid_high"].to_numpy()
    else:
        for field in FIELDS:
            if field in ("open", "close"):
                out[f"bid_{field}"] = a[f"bid_{field}"].to_numpy() * b[f"bid_{field}"].to_numpy()
                out[f"ask_{field}"] = a[f"ask_{field}"].to_numpy() * b[f"ask_{field}"].to_numpy()
        out["bid_high"] = a["bid_high"].to_numpy() * b["bid_high"].to_numpy()
        out["bid_low"] = a["bid_low"].to_numpy() * b["bid_low"].to_numpy()
        out["ask_high"] = a["ask_high"].to_numpy() * b["ask_high"].to_numpy()
        out["ask_low"] = a["ask_low"].to_numpy() * b["ask_low"].to_numpy()

    out["tick_count"] = np.minimum(a["tick_count"].to_numpy(), b["tick_count"].to_numpy())
    frame = pd.DataFrame(out)
    for column in frame.columns:
        if column.startswith(("bid_", "ask_")):
            frame[column] = frame[column].round(scale)
    # Enforce OHLC containment after rounding so the engine's invariants hold.
    for side in ("bid", "ask"):
        frame[f"{side}_high"] = frame[[f"{side}_high", f"{side}_open", f"{side}_close"]].max(axis=1)
        frame[f"{side}_low"] = frame[[f"{side}_low", f"{side}_open", f"{side}_close"]].min(axis=1)
    return frame.sort_values("timestamp_ms", kind="stable", ignore_index=True)


def main() -> int:
    legs = {symbol: load_m5(CACHE, symbol) for symbol in ("EURUSD", "GBPUSD", "USDJPY")}
    manifest: dict[str, object] = {
        "schema_version": "fx_synthetic_crosses_v1",
        "construction": "arbitrage-exact quote sides; intrabar extremes are outer bounds",
        "spread_assumption": "sum of the legs' measured spreads (pessimistic vs a direct quote)",
        "crosses": {},
    }
    print(f"{'cross':8s} {'bars':>9} {'first':>12} {'last':>12} {'spread_pts':>11} {'spread_pips':>12} {'neg':>5}")
    print("-" * 76)

    for name, spec in CROSSES.items():
        frame = build_cross(name, spec, legs)
        spread_points = (
            MEASURED_SPREAD_POINTS[spec["a"]] + MEASURED_SPREAD_POINTS[spec["b"]]
        )
        realised = (frame["ask_close"] - frame["bid_close"]) / spec["point"]
        negative = int((realised < 0).sum())
        path = cache_path(CACHE, name)
        frame.to_parquet(path, index=False, compression="zstd")
        manifest["crosses"][name] = {
            "bars": int(len(frame)),
            "first_utc": iso(int(frame["timestamp_ms"].iloc[0])),
            "last_utc": iso(int(frame["timestamp_ms"].iloc[-1])),
            "point": spec["point"],
            "assumed_spread_points": spread_points,
            "assumed_spread_pips": round(spread_points / 10.0, 2),
            "synthetic_spread_points_median": round(float(realised.median()), 2),
            "negative_spread_bars": negative,
            "legs": [spec["a"], spec["b"]],
            "path": str(path),
            "sha256": sha256_file(path),
        }
        print(
            f"{name:8s} {len(frame):>9,} {frame['timestamp_ms'].iloc[0]:>12} "
            f"{frame['timestamp_ms'].iloc[-1]:>12} {spread_points:>11.0f} "
            f"{spread_points/10:>12.2f} {negative:>5}"
        )

    out = ROOT / "outputs" / "CROSSES_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
