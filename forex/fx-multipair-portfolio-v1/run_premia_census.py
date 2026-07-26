"""R5/R6: cross-sectional FX premia and carry on 7 majors, 1999-2026.

After the intraday and swing paths closed, this tests the documented FX risk
premia at a horizon where transaction cost is ~1.4bp rather than 16-22 points:
time-series momentum, cross-sectional momentum, long-run value reversal, the
dollar factor, and carry using real OECD 3-month interbank rates.

Carry is reported *decomposed* into interest accrual and spot, because that
decomposition decides whether a retail account can capture it.
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
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

RATE_SERIES = {
    "USD": "IR3TIB01USM156N",
    "EUR": "IR3TIB01EZM156N",
    "JPY": "IR3TIB01JPM156N",
    "GBP": "IR3TIB01GBM156N",
    "CAD": "IR3TIB01CAM156N",
    "CHF": "IR3TIB01CHM156N",
    "AUD": "IR3TIB01AUM156N",
    "NZD": "IR3TIB01NZM156N",
}
# pair -> currency held long when long the *foreign* currency against USD
LONG_FOREIGN = {"EURUSD": "EUR", "GBPUSD": "GBP", "AUDUSD": "AUD", "NZDUSD": "NZD"}
SHORT_PAIR = {"USDJPY": "JPY", "USDCAD": "CAD", "USDCHF": "CHF"}
SUBPERIODS = (("1999", "2007"), ("2008", "2014"), ("2015", "2020"), ("2021", "2026"))


def fred_series(series: str) -> pd.Series:
    request = urllib.request.Request(
        FRED_CSV.format(series=series), headers={"User-Agent": "fx-multipair-research/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        frame = pd.read_csv(io.BytesIO(response.read()))
    frame[frame.columns[1]] = pd.to_numeric(frame[frame.columns[1]], errors="coerce")
    return pd.Series(
        frame[frame.columns[1]].to_numpy(), index=pd.to_datetime(frame[frame.columns[0]])
    ).dropna()


def monthly_excess_returns() -> pd.DataFrame:
    panel = pd.read_parquet(CACHE / "fred" / "FX_DAILY_MAJORS.parquet")
    columns = {}
    for pair, currency in LONG_FOREIGN.items():
        columns[currency] = np.log(panel[pair]).diff()
    for pair, currency in SHORT_PAIR.items():
        columns[currency] = -np.log(panel[pair]).diff()
    return pd.DataFrame(columns).dropna().resample("ME").sum()


def describe(series: pd.Series, name: str) -> dict:
    series = series.dropna()
    annual = float(series.mean() * 12)
    volatility = float(series.std(ddof=1) * np.sqrt(12))
    equity = series.cumsum()
    result = {
        "annual_return_pct": round(100.0 * annual, 3),
        "annual_vol_pct": round(100.0 * volatility, 3),
        "sharpe": round(annual / volatility, 3) if volatility > 0 else None,
        "t": round(float(series.mean() / (series.std(ddof=1) / np.sqrt(series.size))), 3),
        "max_drawdown_pct": round(100.0 * float((equity.cummax() - equity).max()), 2),
        "months": int(series.size),
        "subperiod_annual_pct": {
            f"{a}-{b}": round(100.0 * float(series.loc[a:b].mean() * 12), 2)
            for a, b in SUBPERIODS
            if series.loc[a:b].size > 12
        },
    }
    print(
        f"{name:26s} ann={result['annual_return_pct']:+6.2f}% vol={result['annual_vol_pct']:5.2f}% "
        f"SR={result['sharpe']:+5.2f} t={result['t']:+5.2f} maxDD={result['max_drawdown_pct']:5.1f}% "
        f"n={result['months']:4d}"
    )
    return result


def long_short_weights(signal: pd.DataFrame, take: int, ascending: bool = False) -> pd.DataFrame:
    ranks = signal.rank(axis=1)
    count = signal.shape[1]
    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    top, bottom = (1.0 / take, -1.0 / take) if not ascending else (-1.0 / take, 1.0 / take)
    weights[ranks >= count - take + 1] = top
    weights[ranks <= take] = bottom
    return weights


def main() -> int:
    monthly = monthly_excess_returns()
    currencies = list(monthly.columns)
    print(
        f"panel: {monthly.shape[0]} months x {len(currencies)} currencies  "
        f"{monthly.index[0].date()} .. {monthly.index[-1].date()}\n"
    )
    results: dict[str, dict] = {}

    results["dollar_factor"] = describe(monthly.mean(axis=1), "dollar_factor")
    for lookback in (1, 3, 6, 12):
        signal = np.sign(monthly.rolling(lookback).sum().shift(1))
        results[f"TSMOM_{lookback}m"] = describe((signal * monthly).mean(axis=1), f"TSMOM_{lookback}m")
    for lookback in (1, 3, 6, 12):
        weights = long_short_weights(monthly.rolling(lookback).sum().shift(1), take=2)
        results[f"XSMOM_{lookback}m"] = describe((weights * monthly).sum(axis=1), f"XSMOM_{lookback}m")
    for lookback in (36, 60):
        weights = long_short_weights(
            monthly.rolling(lookback).sum().shift(1), take=2, ascending=True
        )
        results[f"VALUE_rev_{lookback}m"] = describe(
            (weights * monthly).sum(axis=1), f"VALUE_rev_{lookback}m"
        )

    print("\n--- carry (OECD 3-month interbank, signal lagged one month) ---")
    rates = pd.DataFrame(
        {currency: fred_series(series) for currency, series in RATE_SERIES.items()}
    )
    rates = rates.resample("ME").last().ffill(limit=3)
    index = monthly.index.intersection(rates.index)
    spot = monthly.loc[index]
    differential = rates.loc[index, currencies].sub(rates.loc[index, "USD"], axis=0) / 100.0
    accrual = differential.shift(1) / 12.0
    total = spot + accrual

    for take in (1, 2, 3):
        weights = long_short_weights(differential.shift(1), take=take)
        results[f"CARRY_top{take}bot{take}"] = describe(
            (weights * total).sum(axis=1), f"CARRY_top{take}bot{take}"
        )

    weights = long_short_weights(differential.shift(1), take=2)
    results["CARRY_top2_spot_only"] = describe((weights * spot).sum(axis=1), "CARRY_top2_spot_only")
    results["CARRY_top2_accrual_only"] = describe(
        (weights * accrual).sum(axis=1), "CARRY_top2_accrual_only"
    )

    results["carry_decomposition_note"] = (
        "The accrual leg carries essentially all of the return and none of the risk; the spot leg "
        "carries all the risk and no return. On a retail MT5 account the accrual arrives as broker "
        "swap, marked up against the client, so the component that is the edge is the component the "
        "broker keeps."
    )
    out = ROOT / "outputs" / "PREMIA_CENSUS.json"
    out.write_text(
        json.dumps(
            {
                "schema_version": "fx_premia_census_v1",
                "panel": {
                    "months": int(monthly.shape[0]),
                    "currencies": currencies,
                    "first": str(monthly.index[0].date()),
                    "last": str(monthly.index[-1].date()),
                },
                "results": results,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
