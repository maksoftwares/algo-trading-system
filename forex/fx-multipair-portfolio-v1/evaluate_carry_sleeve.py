"""The one positive-expectancy FX position set on this account, quantified.

R7 showed the predictable component of FX returns is smaller than the spread, so
no trading signal survives. Carry does not need a signal — it is paid for holding
— so it is the only remaining candidate.

Method, and its honest limits:

* **Accrual** uses the *measured, current* broker swap in points/day from
  `outputs/BROKER_COSTS.json`. Only sides the broker actually pays are taken;
  the gouged side of each pair is discarded. Swap rates move with policy rates,
  so this is today's carry, not a historical series — that is a real limitation
  and it is why the accrual figure is labelled forward-looking.
* **Risk** uses realised historical spot volatility and drawdown from FRED daily
  rates, which is the part that actually kills carry trades.
* **Entry cost** uses the measured fixed spread, amortised over the hold.

Output is an expected annual accrual against historical spot risk — deliberately
not presented as a backtested equity curve, because mixing today's swap with
historical spot would be exactly that kind of fiction.
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

from src.report import MEASURED_SPREAD_POINTS  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1")
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

# side: +1 = hold long the pair, -1 = hold short. Chosen as the side the broker
# PAYS, from the measured swap_long / swap_short.
SLEEVE = {
    "USDJPY": {"side": +1, "swap_points_per_day": 9.402, "point": 0.001, "fred": "DEXJPUS", "invert_fred": False},
    "USDCHF": {"side": +1, "swap_points_per_day": 6.080, "point": 0.00001, "fred": "DEXSZUS", "invert_fred": False},
    "USDMXN": {"side": -1, "swap_points_per_day": 105.347, "point": 0.00001, "fred": "DEXMXUS", "invert_fred": False},
    "USDZAR": {"side": -1, "swap_points_per_day": 61.479, "point": 0.00001, "fred": "DEXSFUS", "invert_fred": False},
}
LOT = 0.01
CONTRACT = 100_000.0
SWAP_DAYS_PER_YEAR = 365.0


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


def main() -> int:
    print("Carry sleeve on measured Capital.com demo swap rates")
    print(f"lot {LOT}, notional {CONTRACT * LOT:,.0f} base units per position\n")

    prices, legs = {}, {}
    print(f"{'symbol':8s} {'side':>5} {'swap/d':>9} {'accrual%/yr':>12} {'spread%':>8} {'spot vol%':>10} {'spot maxDD%':>12}")
    print("-" * 72)

    for symbol, spec in SLEEVE.items():
        series = fred_series(spec["fred"]).loc["1999":]
        if spec["invert_fred"]:
            series = 1.0 / series
        prices[symbol] = series
        spot_price = float(series.iloc[-1])

        # USD value of one point for this position at the current rate.
        point_value = CONTRACT * LOT * spec["point"]
        if symbol.startswith("USD"):  # quote currency is the foreign one
            point_value /= spot_price
        notional_usd = CONTRACT * LOT  # base is USD for all four

        annual_points = spec["swap_points_per_day"] * SWAP_DAYS_PER_YEAR
        accrual_usd = annual_points * point_value
        accrual_pct = 100.0 * accrual_usd / notional_usd
        spread_pct = 100.0 * MEASURED_SPREAD_POINTS[symbol] * point_value / notional_usd

        # spot risk of holding the chosen side
        returns = np.log(series).diff().dropna() * spec["side"]
        vol = float(returns.std(ddof=1) * np.sqrt(252) * 100)
        equity = returns.cumsum()
        drawdown = float((equity.cummax() - equity).max() * 100)

        legs[symbol] = {
            "side": spec["side"],
            "swap_points_per_day": spec["swap_points_per_day"],
            "expected_accrual_pct_per_year": round(accrual_pct, 3),
            "entry_spread_pct_of_notional": round(spread_pct, 4),
            "spread_payback_days": round(
                MEASURED_SPREAD_POINTS[symbol] / spec["swap_points_per_day"], 2
            ),
            "historical_spot_vol_pct": round(vol, 2),
            "historical_spot_max_drawdown_pct": round(drawdown, 2),
        }
        print(
            f"{symbol:8s} {spec['side']:>5} {spec['swap_points_per_day']:>9.2f} "
            f"{accrual_pct:>12.2f} {spread_pct:>8.4f} {vol:>10.2f} {drawdown:>12.1f}"
        )

    # Equal-weight basket: accrual adds, spot risk diversifies only partly.
    aligned = pd.DataFrame(
        {
            symbol: np.log(prices[symbol]).diff() * SLEEVE[symbol]["side"]
            for symbol in SLEEVE
        }
    ).dropna()
    basket = aligned.mean(axis=1)
    basket_vol = float(basket.std(ddof=1) * np.sqrt(252) * 100)
    basket_equity = basket.cumsum()
    basket_drawdown = float((basket_equity.cummax() - basket_equity).max() * 100)
    basket_accrual = float(np.mean([legs[s]["expected_accrual_pct_per_year"] for s in SLEEVE]))
    basket_spot = float(basket.mean() * 252 * 100)

    print(f"\nequal-weight basket ({len(SLEEVE)} positions, {len(aligned):,} daily obs)")
    print(f"  expected accrual         {basket_accrual:+7.2f} %/yr   (today's swap rates)")
    print(f"  historical spot drift    {basket_spot:+7.2f} %/yr   (the part that is a coin flip)")
    print(f"  historical spot vol      {basket_vol:7.2f} %/yr")
    print(f"  historical spot maxDD    {basket_drawdown:7.1f} %")
    print(f"  accrual / spot vol       {basket_accrual / basket_vol:7.2f}   (Sharpe if spot drift were zero)")
    print("\n  pairwise spot correlation of the chosen sides:")
    print(aligned.corr().round(2).to_string(max_colwidth=12))

    report = {
        "schema_version": "fx_carry_sleeve_v1",
        "basis": "measured broker swap (current) + historical FRED spot risk",
        "limitation": (
            "Swap is today's measured rate, not a historical series, so this is expected forward "
            "accrual rather than a backtest. Spot drift is historically ~0 and is the coin flip that "
            "carry trades lose on; the drawdown column is the real risk."
        ),
        "lot": LOT,
        "legs": legs,
        "basket": {
            "positions": len(SLEEVE),
            "expected_accrual_pct_per_year": round(basket_accrual, 3),
            "historical_spot_drift_pct_per_year": round(basket_spot, 3),
            "historical_spot_vol_pct": round(basket_vol, 3),
            "historical_spot_max_drawdown_pct": round(basket_drawdown, 2),
            "accrual_over_vol": round(basket_accrual / basket_vol, 3),
        },
    }
    out = ROOT / "outputs" / "CARRY_SLEEVE.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
