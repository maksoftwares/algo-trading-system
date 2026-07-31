"""H1: the overnight effect on the S&P 500, tested on decades of daily OHLC.

Daily open/high/low/close is all H1 needs — overnight is prev_close → open and
intraday is open → close — so this runs immediately instead of waiting on the
tick download, and over a far longer history than any tick source offers.

Source: Stooq free daily bars for ^SPX (no key, no entitlement). Index levels,
not a tradeable CFD quote, so cost is applied explicitly from the *measured*
Capital.com US500 spread rather than being assumed away.

The comparison that matters is not "is overnight positive" — in a rising market
everything is positive — but "does overnight beat buy-and-hold per unit of risk
and per unit of exposure, net of cost, and does it survive bear years".
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
YAHOO = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
         "?period1=0&period2=1790000000&interval=1d")
# measured: 5 pts spread + 2 entry + 2 stop slippage, point = 0.1 -> 0.9 index pts
COST_INDEX_POINTS = 0.9
BEAR_YEARS = (2018, 2020, 2022)


def load() -> pd.DataFrame:
    """Daily OHLC from Yahoo's chart API (v7 download now requires auth)."""
    request = urllib.request.Request(
        YAHOO, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read())
    result = payload["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_localize(None),
            "open": quote["open"],
            "high": quote["high"],
            "low": quote["low"],
            "close": quote["close"],
        }
    ).dropna()
    frame = frame.sort_values("date").reset_index(drop=True)
    (CACHE / "index").mkdir(parents=True, exist_ok=True)
    frame.to_parquet(CACHE / "index" / "SPX_DAILY.parquet", index=False)
    return frame


def stats(series: pd.Series, price: pd.Series, label: str, exposure: float) -> dict:
    series = series.dropna()
    pct = series / price.reindex(series.index)
    mean = float(series.mean())
    t = mean / (float(series.std(ddof=1)) / np.sqrt(series.size))
    sharpe = float(pct.mean() / pct.std(ddof=1) * np.sqrt(252))
    equity = series.cumsum()
    drawdown = float((equity.cummax() - equity).max())
    result = {
        "label": label,
        "n": int(series.size),
        "mean_points": round(mean, 4),
        "total_points": round(float(series.sum()), 1),
        "t": round(t, 2),
        "win_pct": round(100.0 * float((series > 0).mean()), 2),
        "sharpe": round(sharpe, 3),
        "max_drawdown_points": round(drawdown, 1),
        "exposure_share": exposure,
        "sharpe_per_exposure": round(sharpe / exposure, 3) if exposure else None,
    }
    print(
        f"{label:34s} n={result['n']:5d} mean={result['mean_points']:+8.4f} "
        f"tot={result['total_points']:+10.1f} t={result['t']:+6.2f} "
        f"win={result['win_pct']:5.1f}% SR={result['sharpe']:+6.3f} "
        f"maxDD={result['max_drawdown_points']:9.1f}"
    )
    return result


def main() -> int:
    frame = load()
    frame = frame[frame["date"] >= "1996-01-01"].reset_index(drop=True)
    print(f"^SPX daily: {len(frame):,} rows  {frame['date'].iloc[0].date()} .. {frame['date'].iloc[-1].date()}\n")

    close, open_ = frame["close"], frame["open"]
    prev_close = close.shift(1)
    intraday = close - open_
    overnight = open_ - prev_close
    full = close - prev_close

    print(f"GROSS (no cost).  Cost per round trip = {COST_INDEX_POINTS} index points\n")
    results = {
        "buy_and_hold": stats(full, close, "BUY & HOLD (close->close)", 1.0),
        "intraday": stats(intraday, close, "INTRADAY (open->close)", 0.27),
        "overnight": stats(overnight, close, "OVERNIGHT (prev close->open)", 0.73),
    }

    print(f"\nNET of {COST_INDEX_POINTS} pts per round trip (one trade per day):")
    net_night = overnight - COST_INDEX_POINTS
    net_day = intraday - COST_INDEX_POINTS
    results["overnight_net"] = stats(net_night, close, "OVERNIGHT net of cost", 0.73)
    results["intraday_net"] = stats(net_day, close, "INTRADAY net of cost", 0.27)

    print("\nper calendar year, net of cost (index points):")
    year = frame["date"].dt.year
    rows = []
    for value in sorted(year.unique()):
        mask = year == value
        bh = float(full[mask].sum())
        on = float(net_night[mask].sum())
        rows.append({"year": int(value), "buy_hold": round(bh, 1), "overnight_net": round(on, 1)})
        flag = "  <-- bear" if value in BEAR_YEARS else ""
        print(f"  {value}: buy&hold {bh:+9.1f}   overnight_net {on:+9.1f}{flag}")

    positive_years = sum(1 for r in rows if r["overnight_net"] > 0)
    recent = [r for r in rows if r["year"] >= 2016]
    positive_recent = sum(1 for r in recent if r["overnight_net"] > 0)

    verdict = {
        "overnight_beats_intraday": results["overnight"]["mean_points"] > results["intraday"]["mean_points"],
        "overnight_sharpe_beats_buy_hold_net": results["overnight_net"]["sharpe"] > results["buy_and_hold"]["sharpe"],
        "positive_years_all": f"{positive_years}/{len(rows)}",
        "positive_years_2016plus": f"{positive_recent}/{len(recent)}",
        "bear_years": {
            str(y): {
                "buy_hold": next(r["buy_hold"] for r in rows if r["year"] == y),
                "overnight_net": next(r["overnight_net"] for r in rows if r["year"] == y),
            }
            for y in BEAR_YEARS
            if any(r["year"] == y for r in rows)
        },
    }
    print("\n=== H1 verdict inputs ===")
    for key, value in verdict.items():
        print(f"  {key}: {value}")

    out = ROOT / "outputs" / "US500_OVERNIGHT_H1.json"
    out.write_text(
        json.dumps(
            {
                "schema_version": "us500_overnight_h1_v1",
                "source": "Stooq ^SPX daily",
                "cost_index_points": COST_INDEX_POINTS,
                "results": results,
                "per_year": rows,
                "verdict_inputs": verdict,
            },
            indent=2, sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
