"""V2 refinement: volatility scaling and an event/stress filter.

Targets the two weaknesses the diagnostic found — 14.7% of trades gap through
the 0.5% stop (average −0.98%, worst −2.04%), and the three sleeves are only
~1.79 independent bets — not the monthly win-rate swing, which is sampling noise
around 51.6% and cannot be engineered away without destroying the payoff ratio.

Anti-overfitting rules, fixed before running:

* **Four variants only.** Baseline, +vol scaling, +VIX-level filter, +VIX-spike
  filter. No sweeps inside them.
* **Every parameter is pre-specified**, not searched: vol scaling targets the
  750-day median of 20-day realised vol, clipped to [0.25, 1.5]; the VIX filters
  use the 90th percentile of a trailing 2-year window and a 20% one-day spike.
  These are conventional values, not tuned.
* **Selection on the design window only** (1996–2015). Validation is read once,
  after the choice is locked.
* VIX is an external, economically meaningful conditioner (the market's own
  forward volatility estimate), not a variable mined from the price series.

A variant is only adopted if it improves design **risk-adjusted** performance.
Higher return alone is not adoption — U2 already showed leverage can buy return
while worsening every risk measure.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
DESIGN_END = "2016-01-01"
STOP_PCT = 0.5
COST_PCT = 0.02
SYMBOLS = {"US500": "%5EGSPC", "US30": "%5EDJI", "US2000": "%5ERUT"}

VOL_LOOKBACK, VOL_TARGET_WINDOW = 20, 750
VOL_CLIP = (0.25, 1.5)
VIX_PCTL_WINDOW, VIX_PCTL = 504, 0.90   # 2 years, 90th percentile
VIX_SPIKE_PCT = 20.0

_cache: dict[str, pd.DataFrame] = {}


def yahoo(symbol: str) -> pd.DataFrame:
    if symbol in _cache:
        return _cache[symbol]
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           "?period1=0&period2=1790000000&interval=1d")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as response:
        payload = json.load(response)
    result = payload["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_localize(None),
            "open": quote["open"], "high": quote["high"],
            "low": quote["low"], "close": quote["close"],
        }
    ).dropna().sort_values("date").reset_index(drop=True)
    _cache[symbol] = frame
    return frame


def vix_conditions() -> pd.DataFrame:
    """VIX level-percentile and one-day-spike flags, both known at the close."""
    frame = yahoo("%5EVIX")
    # Yahoo stamps ^VIX at a different intraday time than the index series,
    # so joining on the raw timestamp matched zero rows. Normalise to dates.
    vix = frame.assign(date=frame["date"].dt.normalize()).set_index("date")["close"]
    threshold = vix.rolling(VIX_PCTL_WINDOW, min_periods=120).quantile(VIX_PCTL)
    spike = (vix / vix.shift(1) - 1) * 100
    return pd.DataFrame({"high_level": vix > threshold, "spiked": spike > VIX_SPIKE_PCT})


def sleeve(symbol: str, vol_scale: bool, skip: pd.Series | None) -> pd.Series:
    frame = yahoo(SYMBOLS[symbol])
    frame = frame[frame["date"] >= "1995-01-01"].reset_index(drop=True)
    ret = (frame["close"] / frame["close"].shift(1) - 1) * 100
    signal = ret < 0

    entry = frame["close"]
    stop = entry * (1 - STOP_PCT / 100.0)
    nxt_open, nxt_low, nxt_close = frame["open"].shift(-1), frame["low"].shift(-1), frame["close"].shift(-1)
    out = (nxt_close / entry - 1) * 100
    gapped = nxt_open <= stop
    hit = (~gapped) & (nxt_low <= stop)
    out = out.where(~gapped, (nxt_open / entry - 1) * 100)
    out = out.where(~hit, -STOP_PCT)
    out = out - COST_PCT

    if vol_scale:
        realised = ret.rolling(VOL_LOOKBACK).std()
        target = realised.rolling(VOL_TARGET_WINDOW, min_periods=100).median()
        out = out * (target / realised).clip(*VOL_CLIP)

    keep = signal & out.notna()
    if skip is not None:
        blocked = (
            frame["date"].dt.normalize().map(skip).fillna(False).astype(bool).to_numpy()
        )
        keep &= ~blocked

    series = out[keep]
    series.index = frame["date"][keep]
    return series[series.index >= "1996-01-01"]


def portfolio(vol_scale: bool, skip: pd.Series | None, lo: str, hi: str) -> tuple[pd.Series, int]:
    cols = []
    for symbol in SYMBOLS:
        s = sleeve(symbol, vol_scale, skip)
        cols.append(s[(s.index >= lo) & (s.index < hi)].rename(symbol))
    frame = pd.concat(cols, axis=1, sort=True)
    daily = (frame.fillna(0.0).sum(axis=1) / len(SYMBOLS))
    daily = daily[frame.notna().any(axis=1)].sort_index()
    return daily, int(frame.notna().sum().sum())


def score(daily: pd.Series, trades: int, label: str) -> dict:
    equity = daily.cumsum()
    drawdown = float((equity.cummax() - equity).max())
    wins, losses = daily[daily > 0], daily[daily <= 0]
    months = daily.groupby(daily.index.strftime("%Y-%m")).sum()
    keep = np.sort(daily.to_numpy())[: max(daily.size - int(np.ceil(daily.size * 0.05)), 1)]
    kw, kl = keep[keep > 0], keep[keep <= 0]
    years = (daily.index[-1] - daily.index[0]).days / 365.25
    annual = float(daily.sum()) / years
    result = {
        "trades": trades, "trades_per_day": round(trades / (years * 252), 2),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4),
        "pf_excluding_best_5pct": round(float(kw.sum() / -kl.sum()), 4) if kl.size else None,
        "annual_pct": round(annual, 2),
        "sharpe": round(float(daily.mean() / daily.std(ddof=1) * np.sqrt(252)), 3),
        "months_positive_pct": round(100.0 * float((months > 0).mean()), 1),
        "max_drawdown_pct": round(drawdown, 2),
        "worst_month_pct": round(float(months.min()), 2),
        "return_over_maxdd": round(annual / drawdown, 3) if drawdown > 0 else None,
    }
    print(
        f"{label:34s} {result['trades_per_day']:5.2f}/d PF={result['profit_factor']:6.3f} "
        f"exTop5={result['pf_excluding_best_5pct']:6.3f} ann={result['annual_pct']:+6.2f}% "
        f"SR={result['sharpe']:5.2f} +mo={result['months_positive_pct']:5.1f}% "
        f"maxDD={result['max_drawdown_pct']:6.2f}% worstMo={result['worst_month_pct']:+6.2f}% "
        f"ret/DD={result['return_over_maxdd']:5.2f}"
    )
    return result


def main() -> int:
    conditions = vix_conditions()
    variants = {
        "A_baseline": (False, None),
        "B_volscale": (True, None),
        "C_volscale_skip_high_vix": (True, conditions["high_level"]),
        "D_volscale_skip_vix_spike": (True, conditions["spiked"]),
    }

    print("SELECTION ON DESIGN ONLY (1996-2015)\n")
    design = {}
    for name, (vol_scale, skip) in variants.items():
        daily, trades = portfolio(vol_scale, skip, "1996-01-01", DESIGN_END)
        design[name] = score(daily, trades, f"  {name}")

    # adoption rule fixed in advance: best design Sharpe, tie-break on return/maxDD
    chosen = max(design, key=lambda k: (design[k]["sharpe"], design[k]["return_over_maxdd"]))
    print(f"\nchosen on design by Sharpe (tie-break return/maxDD): {chosen}")

    print("\nVALIDATION 2016-2026 (read once, after the choice was locked)\n")
    validation = {}
    for name, (vol_scale, skip) in variants.items():
        daily, trades = portfolio(vol_scale, skip, DESIGN_END, "2026-08-01")
        validation[name] = score(daily, trades, f"  {name}" + ("  <- CHOSEN" if name == chosen else ""))

    bar = validation[chosen]
    gates = {
        "profit_factor_ge_1.40": (bar["profit_factor"], bar["profit_factor"] >= 1.40),
        "trades_per_day_ge_0.50": (bar["trades_per_day"], bar["trades_per_day"] >= 0.50),
        "months_positive_ge_55pct": (bar["months_positive_pct"], bar["months_positive_pct"] >= 55.0),
        "pf_ex_best5pct_ge_1.20": (bar["pf_excluding_best_5pct"], bar["pf_excluding_best_5pct"] >= 1.20),
        "max_dd_le_15pct": (bar["max_drawdown_pct"], bar["max_drawdown_pct"] <= 15.0),
    }
    print(f"\nforex-bar gates for {chosen} on validation:")
    for name, (value, passed) in gates.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name:28s} = {value}")

    out = ROOT / "outputs" / "INDEX_SYSTEM_V2.json"
    out.write_text(
        json.dumps(
            {
                "schema_version": "index_system_v2_refinement",
                "parameters_fixed_in_advance": {
                    "vol_lookback": VOL_LOOKBACK, "vol_target_window": VOL_TARGET_WINDOW,
                    "vol_clip": list(VOL_CLIP), "vix_pctl_window": VIX_PCTL_WINDOW,
                    "vix_pctl": VIX_PCTL, "vix_spike_pct": VIX_SPIKE_PCT,
                },
                "selection_rule": "best design Sharpe, tie-break return/maxDD; validation read once",
                "chosen": chosen,
                "design": design,
                "validation": validation,
                "gates": {k: {"value": v, "passed": bool(p)} for k, (v, p) in gates.items()},
            },
            indent=2, sort_keys=True, default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
