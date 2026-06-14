"""
direction_state.py — market regime / direction-state detector
==============================================================

Purpose
-------
A standalone signal that classifies the CURRENT market state as
up-trend / down-trend / sideways, with a strength score — so other strategies
(EAs) can route themselves: trade momentum in trends, fade in ranges, and never
fight a strong trend.

Honest scope (read this)
------------------------
This DETECTS the regime you are already in. It does NOT predict the future
direction of price. Validation on gold (2026-06-01..12) showed:
  * As a predictor it fails — when it said STRONG_UP, price continued up 0% of
    the time (those were counter-trend blips in a downtrend).
  * As a ROUTER it works — breakout/momentum trades won 54% in trend regimes
    vs 35% in flat regimes. That is its job: tell strategies WHEN their style
    fits, not which way the next candle goes.
Use the output as a FILTER / BIAS input, never as a certainty.

Method
------
Computed on a higher timeframe (H1 recommended) for stability:
  * Trend direction  : sign agreement of EMA(fast) vs EMA(slow) AND EMA-slope.
  * Sideways detector: Kaufman Efficiency Ratio (ER) = |net move| / sum(|bar moves|)
                       over er_n bars. Low ER (< er_flat) = choppy/ranging => FLAT.
  * Strength         : the ER itself (0..1). ER >= 0.5 escalates to STRONG_*.

Output per bar: direction (+1/0/-1), regime label, strength (0..1).
`latest_state()` returns the current value, ready to publish to other EAs
(e.g. write to a GlobalVariable or a file the executors read).

Parameters are defaults from the gold prototype and are meant to be tuned and
re-validated out-of-sample before any live use.
"""
from __future__ import annotations
import pandas as pd
import numpy as np


def efficiency_ratio(close: pd.Series, n: int) -> pd.Series:
    """Kaufman efficiency ratio: 0 = pure chop, 1 = perfectly directional."""
    net = close.diff(n).abs()
    path = close.diff().abs().rolling(n).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan)


def classify_regime(
    df: pd.DataFrame,
    ema_fast: int = 12,
    ema_slow: int = 34,
    slope_k: int = 6,
    er_n: int = 12,
    er_flat: float = 0.30,
    er_strong: float = 0.50,
    close_col: str = "close",
) -> pd.DataFrame:
    """
    Add direction / regime / strength columns to a bar DataFrame.

    df must have a `close` column (one row per bar, chronological).
    Returns a copy with: ema_fast, ema_slow, slope, er, direction, regime, strength.
      direction: +1 up, 0 sideways, -1 down
      regime:    STRONG_UP / UP / FLAT / DOWN / STRONG_DOWN
      strength:  efficiency ratio (0..1)
    """
    d = df.copy()
    c = d[close_col]
    d["ema_fast"] = c.ewm(span=ema_fast, adjust=False).mean()
    d["ema_slow"] = c.ewm(span=ema_slow, adjust=False).mean()
    d["slope"] = d["ema_slow"].diff(slope_k)
    d["er"] = efficiency_ratio(c, er_n)

    dir_ema = np.sign(d["ema_fast"] - d["ema_slow"])
    dir_slope = np.sign(d["slope"])
    direction = np.where(dir_ema * dir_slope > 0, dir_ema, 0)   # both must agree
    direction = np.where(d["er"] < er_flat, 0, direction)       # low efficiency => sideways
    d["direction"] = pd.Series(direction, index=d.index).fillna(0).astype(int)
    d["strength"] = d["er"].round(3)
    d["regime"] = np.select(
        [
            (d["direction"] > 0) & (d["er"] >= er_strong),
            (d["direction"] > 0),
            (d["direction"] < 0) & (d["er"] >= er_strong),
            (d["direction"] < 0),
        ],
        ["STRONG_UP", "UP", "STRONG_DOWN", "DOWN"],
        default="FLAT",
    )
    return d


def latest_state(df_classified: pd.DataFrame) -> dict:
    """Return the most recent regime as a dict ready to publish to other EAs."""
    row = df_classified.dropna(subset=["er"]).iloc[-1]
    return {
        "direction": int(row["direction"]),     # +1 / 0 / -1
        "regime": str(row["regime"]),            # STRONG_UP ... STRONG_DOWN
        "strength": float(row["strength"]),      # 0..1
        "trend_ok": bool(row["direction"] != 0), # True => momentum strategies enabled
    }


def load_bars(path: str, time_col: str = "bar_start_utc") -> pd.DataFrame:
    d = pd.read_csv(path)
    d["t"] = pd.to_datetime(d[time_col])
    for col in ["open", "high", "low", "close"]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")
    return d.dropna(subset=["close"]).sort_values("t").reset_index(drop=True)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD_H1_20260601_to_latest.csv"
    bars = load_bars(path)
    out = classify_regime(bars)
    print(out["regime"].value_counts().to_string())
    print("\nlatest state ->", latest_state(out))
