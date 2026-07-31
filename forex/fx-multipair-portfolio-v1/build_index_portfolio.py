"""Multi-index short-term reversal portfolio.

The single-index US500 system is real but misses the forex bar on frequency
(0.45/day), concentration (`exTop5` 0.845) and drawdown (21.4%). All three are
addressed by the same move, and it is evidence-led rather than a new hypothesis:
the effect already reproduced on 9 of 10 world indices, and Capital.com lists 12
index CFDs. Running one confirmed signal across many markets multiplies
frequency and diversifies the fat right tail that the concentration test
punishes.

Discipline:

* the universe is chosen on the **design window only** (1996–2015). An index is
  included if its design-window effect is positive; validation is never used to
  pick members.
* one rule for every index — long after a down close, exit next close. No
  per-index parameters.
* cost is a uniform 0.02% round trip, ~2.5x the measured US500 spread (0.008%),
  because most index spreads could not be measured with markets closed. Stressed
  at 2x again.
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

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
COST_PCT = 0.02
DESIGN_END = "2016-01-01"
ACCOUNT_USD = 10_000.0

# broker symbol -> Yahoo proxy. CH50 has no clean free proxy and is omitted.
UNIVERSE = {
    "US500": "%5EGSPC", "US30": "%5EDJI", "US2000": "%5ERUT", "DE40": "%5EGDAXI",
    "UK100": "%5EFTSE", "JP225": "%5EN225", "FR40": "%5EFCHI", "EU50": "%5ESTOXX50E",
    "HK50": "%5EHSI", "IT40": "FTSEMIB.MI", "NL25": "%5EAEX",
}


def yahoo_daily(symbol: str) -> pd.DataFrame | None:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           "?period1=0&period2=1790000000&interval=1d")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as response:
            payload = json.load(response)
        result = payload["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_localize(None),
                "close": quote["close"],
            }
        ).dropna()
        return frame.sort_values("date").reset_index(drop=True)
    except Exception:
        return None


def trade_series(frame: pd.DataFrame, cost: float) -> pd.Series:
    """Net % return of: long at close after a down close, exit next close."""
    ret = (frame["close"] / frame["close"].shift(1) - 1) * 100
    signal = ret < 0
    forward = ret.shift(-1)
    out = (forward - cost)[signal & forward.notna()]
    out.index = frame["date"][signal & forward.notna()]
    return out


def metrics(daily: pd.Series, trade_count: int, years: float, label: str) -> dict:
    equity = daily.cumsum()
    drawdown = float((equity.cummax() - equity).max())
    wins, losses = daily[daily > 0], daily[daily <= 0]
    months = daily.groupby(daily.index.strftime("%Y-%m")).sum()
    keep = np.sort(daily.to_numpy())[: max(daily.size - int(np.ceil(daily.size * 0.05)), 1)]
    kw, kl = keep[keep > 0], keep[keep <= 0]
    result = {
        "label": label,
        "active_days": int(daily.size),
        "trades": int(trade_count),
        "trades_per_day": round(trade_count / (years * 252), 2),
        "win_rate_pct": round(100.0 * float((daily > 0).mean()), 2),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4) if losses.size else None,
        "pf_excluding_best_5pct": round(float(kw.sum() / -kl.sum()), 4) if kl.size else None,
        "annual_pct": round(float(daily.sum()) / years, 2),
        "sharpe": round(float(daily.mean() / daily.std(ddof=1) * np.sqrt(252)), 3),
        "months_positive_pct": round(100.0 * float((months > 0).mean()), 1),
        "max_drawdown_pct": round(drawdown, 2),
        "t_stat": round(float(daily.mean() / (daily.std(ddof=1) / np.sqrt(daily.size))), 2),
    }
    print(
        f"{label:28s} days={result['active_days']:5d} trades={result['trades']:5d} "
        f"{result['trades_per_day']:>5.2f}/d PF={result['profit_factor']:>6.3f} "
        f"exTop5={result['pf_excluding_best_5pct']:>6.3f} ann={result['annual_pct']:>+7.2f}% "
        f"SR={result['sharpe']:>5.2f} +mo={result['months_positive_pct']:>5.1f}% "
        f"maxDD={result['max_drawdown_pct']:>6.2f}% t={result['t_stat']:>5.2f}"
    )
    return result


def main() -> int:
    print("fetching index history...")
    series = {}
    for symbol, proxy in UNIVERSE.items():
        frame = yahoo_daily(proxy)
        if frame is None or len(frame) < 2500:
            print(f"  {symbol:7s} unavailable")
            continue
        frame = frame[frame["date"] >= "1996-01-01"].reset_index(drop=True)
        series[symbol] = trade_series(frame, COST_PCT)
        print(f"  {symbol:7s} {len(frame):5d} days from {frame['date'].iloc[0].date()}")

    # --- universe selection on DESIGN ONLY ---
    print(f"\nuniverse selection on design window (< {DESIGN_END}), validation never used:")
    members = []
    for symbol, trades in series.items():
        design = trades[trades.index < DESIGN_END]
        keep = design.size > 200 and design.mean() > 0
        print(f"  {symbol:7s} design mean={design.mean():+.4f}% n={design.size:4d} -> "
              f"{'INCLUDE' if keep else 'EXCLUDE'}")
        if keep:
            members.append(symbol)
    print(f"\nmembers ({len(members)}): {members}")

    report = {"schema_version": "index_reversal_portfolio_v1", "cost_pct": COST_PCT,
              "members": members, "windows": {}}

    for window, lo, hi in (("design", "1996-01-01", DESIGN_END), ("validation", DESIGN_END, "2026-08-01")):
        print(f"\n=== {window} ===")
        frames = []
        for symbol in members:
            trades = series[symbol]
            frames.append(trades[(trades.index >= lo) & (trades.index < hi)].rename(symbol))
        combined = pd.concat(frames, axis=1)
        trade_count = int(combined.notna().sum().sum())
        # equal-weight across whichever indices signalled that day
        daily = combined.mean(axis=1).dropna().sort_index()
        years = (daily.index[-1] - daily.index[0]).days / 365.25
        report["windows"][window] = {
            "portfolio": metrics(daily, trade_count, years, f"PORTFOLIO ({len(members)} idx)"),
            "per_index": {},
        }
        for symbol in members:
            single = combined[symbol].dropna()
            if single.size > 50:
                report["windows"][window]["per_index"][symbol] = metrics(
                    single, single.size, years, f"  {symbol}"
                )

    print("\n=== cost stress on the portfolio (validation) ===")
    stress = {}
    for multiple in (1, 2, 4):
        frames = []
        for symbol in members:
            frame = yahoo_daily(UNIVERSE[symbol])
            frame = frame[frame["date"] >= "1996-01-01"].reset_index(drop=True)
            t = trade_series(frame, COST_PCT * multiple)
            frames.append(t[t.index >= DESIGN_END].rename(symbol))
        combined = pd.concat(frames, axis=1)
        daily = combined.mean(axis=1).dropna().sort_index()
        years = (daily.index[-1] - daily.index[0]).days / 365.25
        stress[f"{multiple}x"] = metrics(daily, int(combined.notna().sum().sum()), years,
                                         f"  {multiple}x cost ({COST_PCT*multiple:.3f}%)")
    report["cost_stress_validation"] = stress

    bar = report["windows"]["validation"]["portfolio"]
    gates = {
        "profit_factor_ge_1.40": (bar["profit_factor"], bar["profit_factor"] >= 1.40),
        "trades_per_day_ge_0.50": (bar["trades_per_day"], bar["trades_per_day"] >= 0.50),
        "months_positive_ge_55pct": (bar["months_positive_pct"], bar["months_positive_pct"] >= 55.0),
        "pf_ex_best5pct_ge_1.20": (bar["pf_excluding_best_5pct"], bar["pf_excluding_best_5pct"] >= 1.20),
        "pf_at_2x_cost_ge_1.15": (stress["2x"]["profit_factor"], stress["2x"]["profit_factor"] >= 1.15),
        "max_dd_le_15pct": (bar["max_drawdown_pct"], bar["max_drawdown_pct"] <= 15.0),
    }
    print("\n=== forex-bar gates on the VALIDATION portfolio ===")
    for name, (value, passed) in gates.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name:30s} = {value}")
    report["forex_bar_gates"] = {k: {"value": v, "passed": bool(p)} for k, (v, p) in gates.items()}
    report["gates_passed"] = sum(1 for _, p in gates.values() if p)
    report["all_gates_passed"] = all(p for _, p in gates.values())
    print(f"\ngates passed: {report['gates_passed']}/6   ALL: {report['all_gates_passed']}")

    out = ROOT / "outputs" / "INDEX_PORTFOLIO.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
