"""Acquire CFTC positioning and CBOE skew/vol data for US500.

Two public sources, no credentials:

* CFTC Traders in Financial Futures, contract 13874+ (S&P 500 Consolidated) —
  weekly dealer / asset-manager / leveraged-fund long, short and spread.
* CBOE ^SKEW, ^VIX, ^VIX3M, ^VVIX, ^VIX9D via the Yahoo chart API — daily.

The publication lag is applied **here**, once, so no downstream test can forget
it: COT snapshots Tuesday and publishes Friday 15:30 ET, so each report is
stamped ``tradable_from`` = the following Monday. Every join downstream uses
that column, never ``report_date``.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\positioning")
CFTC = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
CONTRACT = "13874+"          # S&P 500 Consolidated
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
VOL_INDICES = {"SKEW": "%5ESKEW", "VIX": "%5EVIX", "VIX3M": "%5EVIX3M",
               "VVIX": "%5EVVIX", "VIX9D": "%5EVIX9D"}


def fetch_cot() -> pd.DataFrame:
    fields = [
        "report_date_as_yyyy_mm_dd", "open_interest_all",
        "dealer_positions_long_all", "dealer_positions_short_all",
        "asset_mgr_positions_long", "asset_mgr_positions_short",
        "lev_money_positions_long", "lev_money_positions_short",
    ]
    # '+' must be percent-encoded or Socrata reads it as a space and matches nothing
    where = urllib.parse.quote(f"cftc_contract_market_code='{CONTRACT}'", safe="")
    url = (f"{CFTC}?$select={urllib.parse.quote(','.join(fields), safe=',')}"
           f"&$where={where}"
           f"&$order=report_date_as_yyyy_mm_dd&$limit=5000")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as response:
        rows = json.load(response)
    frame = pd.DataFrame(rows)
    frame["report_date"] = pd.to_datetime(frame["report_date_as_yyyy_mm_dd"]).dt.tz_localize(None)
    for column in fields[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna().sort_values("report_date").reset_index(drop=True)

    # Tuesday snapshot -> Friday 15:30 ET release -> tradable at the NEXT Monday
    # open. weekday(): Tue=1, so +6 days reaches the following Monday.
    frame["tradable_from"] = frame["report_date"] + pd.to_timedelta(
        [(7 - d.weekday()) % 7 or 7 for d in frame["report_date"]], unit="D"
    )

    frame["dealer_net"] = frame["dealer_positions_long_all"] - frame["dealer_positions_short_all"]
    frame["asset_mgr_net"] = frame["asset_mgr_positions_long"] - frame["asset_mgr_positions_short"]
    frame["lev_money_net"] = frame["lev_money_positions_long"] - frame["lev_money_positions_short"]
    for name in ("dealer", "asset_mgr", "lev_money"):
        frame[f"{name}_net_pct_oi"] = frame[f"{name}_net"] / frame["open_interest_all"] * 100
    return frame


def fetch_index(symbol: str) -> pd.Series:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           "?period1=0&period2=1790000000&interval=1d")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as response:
        payload = json.load(response)
    result = payload["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    stamps = pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_localize(None).normalize()
    return pd.Series(closes, index=stamps).dropna()


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    cot = fetch_cot()
    print(f"CFTC S&P 500 Consolidated: {len(cot)} weekly reports  "
          f"{cot['report_date'].min().date()} .. {cot['report_date'].max().date()}")
    print(f"  publication lag applied: report {cot['report_date'].iloc[-1].date()} "
          f"-> tradable {cot['tradable_from'].iloc[-1].date()}")
    print(f"  net positioning as % of open interest (latest):")
    for name in ("dealer", "asset_mgr", "lev_money"):
        series = cot[f"{name}_net_pct_oi"]
        print(f"    {name:10s} {series.iloc[-1]:>+7.2f}%   "
              f"range {series.min():>+7.2f}% .. {series.max():>+7.2f}%")
    cot.to_parquet(CACHE / "CFTC_SP500.parquet", index=False)

    frames = {}
    for name, symbol in VOL_INDICES.items():
        try:
            series = fetch_index(symbol)
            frames[name] = series
            print(f"  {name:6s} {len(series):>6} days  {series.index.min().date()} .. "
                  f"{series.index.max().date()}  last {series.iloc[-1]:.2f}")
        except Exception as error:
            print(f"  {name:6s} failed: {error}")
    vol = pd.DataFrame(frames).sort_index()
    vol["vix_term"] = vol["VIX"] / vol["VIX3M"]
    vol.to_parquet(CACHE / "CBOE_VOL.parquet")
    print(f"\nvol panel: {len(vol)} rows, columns {list(vol.columns)}")
    print(f"wrote {CACHE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
