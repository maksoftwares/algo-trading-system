"""Test P1-P5: does positioning or skew predict US500 forward returns?

Protocol per POSITIONING_PREREGISTRATION.md. One deviation, stated: CFTC data
begins 2010-06 rather than 2016, so design runs 2010-2020 and holdout 2021-2026.
The split date is unchanged and both arms are larger than preregistered, which
is stricter, not looser.

Every positioning signal is joined on ``tradable_from`` — the Monday after the
Friday release — never on the Tuesday snapshot date. Volatility indices are
lagged one day.

Significance uses non-overlapping samples (stride = horizon). A shuffled-
positioning null is run for the survivors, exactly as the mega-search null was.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
SPLIT = "2021-01-01"
HORIZONS = {"1w": 5, "2w": 10, "4w": 20}
COST_PCT = 0.02


def load() -> pd.DataFrame:
    spx = pd.read_parquet(CACHE / "index" / "SPX_DAILY.parquet")
    spx = spx[spx["date"] >= "2010-01-01"].reset_index(drop=True)
    # Yahoo stamps SPX at the 14:30 UTC open while the CBOE vol indices are
    # midnight-normalised; without this the join matches ZERO rows and the skew
    # tests silently evaluate on all-NaN.
    spx["date"] = spx["date"].dt.normalize()
    spx = spx.set_index("date")["close"].sort_index()

    cot = pd.read_parquet(CACHE / "positioning" / "CFTC_SP500.parquet")
    vol = pd.read_parquet(CACHE / "positioning" / "CBOE_VOL.parquet")

    frame = pd.DataFrame({"close": spx})
    # positioning: as-of join on tradable_from, so a value is only visible from
    # the Monday after public release
    cot_indexed = cot.set_index("tradable_from").sort_index()
    for column in ("dealer_net_pct_oi", "asset_mgr_net_pct_oi", "lev_money_net_pct_oi"):
        frame[column] = cot_indexed[column].reindex(frame.index, method="ffill")
    # volatility: one-day lag
    for column in ("SKEW", "VIX", "vix_term", "VVIX"):
        if column in vol.columns:
            frame[column] = vol[column].reindex(frame.index).shift(1)

    for name, days in HORIZONS.items():
        frame[f"fwd_{name}"] = (frame["close"].shift(-days) / frame["close"] - 1) * 100 - COST_PCT
    return frame.dropna(subset=["dealer_net_pct_oi"])


def zscore(series: pd.Series, window: int = 252 * 3) -> pd.Series:
    mean = series.rolling(window, min_periods=100).mean()
    std = series.rolling(window, min_periods=100).std()
    return (series - mean) / std


def evaluate(frame: pd.DataFrame, signal: pd.Series, horizon: str, contrarian: bool) -> dict:
    """Long when the z-score is extreme in the favourable direction."""
    stride = HORIZONS[horizon]
    target = frame[f"fwd_{horizon}"]
    direction = -np.sign(signal) if contrarian else np.sign(signal)
    aligned = (direction * target).dropna()
    extreme = aligned[np.abs(signal.reindex(aligned.index)) >= 1.0]
    sample = extreme.iloc[::stride]
    if sample.size < 25:
        return {"n": int(sample.size)}
    mean = float(sample.mean())
    t = mean / (float(sample.std(ddof=1)) / np.sqrt(sample.size))
    return {"n": int(sample.size), "mean_pct": round(mean, 4), "t": round(t, 2),
            "win_pct": round(100.0 * float((sample > 0).mean()), 1),
            "total_pct": round(float(sample.sum()), 1)}


def main() -> int:
    frame = load()
    print(f"panel {frame.index.min().date()} .. {frame.index.max().date()}  "
          f"{len(frame):,} daily rows, {frame['dealer_net_pct_oi'].nunique()} distinct COT reports")
    design = frame[frame.index < SPLIT]
    holdout = frame[frame.index >= SPLIT]
    print(f"design {len(design):,} rows | holdout {len(holdout):,} rows  (split {SPLIT})\n")

    tests = {
        "P1 lev_money crowding (contrarian)": ("lev_money_net_pct_oi", True),
        "P2 dealer net (contrarian)": ("dealer_net_pct_oi", True),
        "P3 asset_mgr net (directional)": ("asset_mgr_net_pct_oi", False),
        "P4a SKEW high -> long": ("SKEW", False),
        "P4b SKEW high -> short": ("SKEW", True),
        "P5 VIX term backwardation": ("vix_term", False),
    }
    report, survivors = {}, []
    print(f"{'hypothesis':36s} {'horizon':>8} | {'DESIGN mean%':>13} {'t':>6} {'n':>5} | "
          f"{'HOLDOUT mean%':>14} {'t':>6} {'n':>5}")
    print("-" * 104)
    for label, (column, contrarian) in tests.items():
        if column not in frame.columns:
            continue
        report[label] = {}
        for horizon in HORIZONS:
            z_design = zscore(frame[column])[frame.index < SPLIT]
            z_holdout = zscore(frame[column])[frame.index >= SPLIT]
            d = evaluate(design, z_design, horizon, contrarian)
            h = evaluate(holdout, z_holdout, horizon, contrarian)
            report[label][horizon] = {"design": d, "holdout": h}
            if "mean_pct" not in d or "mean_pct" not in h:
                print(f"{label:36s} {horizon:>8} | SKIPPED - insufficient sample "
                      f"(design n={d.get('n', 0)}, holdout n={h.get('n', 0)})")
                continue
            flag = ""
            if abs(d["t"]) >= 2.0 and np.sign(d["mean_pct"]) == np.sign(h["mean_pct"]):
                flag = "  <= sign held"
                survivors.append((label, horizon, d, h))
            print(f"{label:36s} {horizon:>8} | {d['mean_pct']:>+12.3f}% {d['t']:>+6.2f} {d['n']:>5} | "
                  f"{h['mean_pct']:>+13.3f}% {h['t']:>+6.2f} {h['n']:>5}{flag}")
        print()

    print(f"survivors (design |t|>=2 AND holdout sign unchanged): {len(survivors)}")
    for label, horizon, d, h in survivors:
        print(f"  {label} @ {horizon}: design {d['mean_pct']:+.3f}% (t{d['t']:+.2f}) "
              f"-> holdout {h['mean_pct']:+.3f}% (t{h['t']:+.2f})")

    (ROOT / "outputs" / "POSITIONING_TEST.json").write_text(
        json.dumps({"schema_version": "positioning_test_v1", "split": SPLIT,
                    "cost_pct": COST_PCT, "results": report,
                    "survivors": len(survivors)}, indent=2, sort_keys=True, default=str),
        encoding="utf-8")
    print(f"\nwrote {ROOT / 'outputs' / 'POSITIONING_TEST.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
