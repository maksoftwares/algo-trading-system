"""End-to-end CFD re-validation, with the overnight path modelled correctly.

U10 showed the index-level backtest is optimistic because the cash daily bar
hides the overnight path. This corrects the remaining known-adverse detail: a
position held from one cash close to the next is **live overnight**, so its stop
must be tested against every bid printed in between — not just the next cash
session's low, which is what the earlier test used.

Three stop models are reported side by side so the size of each bias is visible:

* ``cash_low``   — stop tested on the next cash session's low only (what the
  index backtest effectively assumed; optimistic).
* ``full_path``  — stop tested on every M5 bid between the two closes, including
  the overnight session. This is what actually happens to a CFD position.
* ``no_stop``    — hold to the next close regardless, as a control.

Years available on CFD quotes are whichever Dukascopy years are complete;
2018/2020/2022 are the stress years and 2016 is a calm control.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.us500_strategies import _session_minutes  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\bars")
STOP_PCT = 0.5


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    bars = pd.read_parquet(CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    minutes, open_minutes, close_minutes = _session_minutes(bars)
    stamps = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
    frame = bars.assign(
        stamp=stamps,
        date=stamps.dt.strftime("%Y-%m-%d"),
        minutes=minutes,
        in_session=(minutes >= open_minutes) & (minutes <= close_minutes),
        at_close=(minutes >= close_minutes - 5) & (minutes <= close_minutes),
    )
    close_rows = frame[frame["at_close"]].groupby("date").last()
    session = frame[frame["in_session"]]
    daily = pd.DataFrame(
        {
            "close_stamp": close_rows["stamp"],
            "ask": close_rows["ask_close"],
            "bid": close_rows["bid_close"],
            "mid": (close_rows["bid_close"] + close_rows["ask_close"]) / 2.0,
            "cash_low": session.groupby("date")["bid_low"].min(),
        }
    ).dropna()
    daily.index = pd.to_datetime(daily.index)
    return frame, daily.sort_index()


def path_low(frame: pd.DataFrame, start, end) -> float:
    """Lowest bid strictly between two session closes — the overnight path."""
    window = frame[(frame["stamp"] > start) & (frame["stamp"] <= end)]
    return float(window["bid_low"].min()) if len(window) else np.nan


def evaluate(frame: pd.DataFrame, daily: pd.DataFrame, model: str) -> pd.Series:
    signal = (daily["mid"] / daily["mid"].shift(1) - 1) < 0
    entry = daily["ask"]
    stop = entry * (1 - STOP_PCT / 100.0)
    next_close_bid = daily["bid"].shift(-1)
    next_stamp = daily["close_stamp"].shift(-1)

    if model == "no_stop":
        result = (next_close_bid / entry - 1) * 100
        return result[signal & result.notna()]

    if model == "cash_low":
        lows = daily["cash_low"].shift(-1)
    else:  # full_path — every bid between the two closes
        lows = pd.Series(
            [
                path_low(frame, daily["close_stamp"].iloc[i], next_stamp.iloc[i])
                if pd.notna(next_stamp.iloc[i]) else np.nan
                for i in range(len(daily))
            ],
            index=daily.index,
        )

    hit = lows <= stop
    exit_price = next_close_bid.where(~hit, stop)
    result = (exit_price / entry - 1) * 100
    keep = signal & result.notna() & lows.notna()
    return result[keep]


def score(series: pd.Series, label: str) -> dict:
    wins, losses = series[series > 0], series[series <= 0]
    equity = series.cumsum()
    drawdown = float((equity.cummax() - equity).max())
    result = {
        "trades": int(series.size),
        "win_rate_pct": round(100.0 * float((series > 0).mean()), 2),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4) if losses.size else None,
        "net_pct": round(float(series.sum()), 2),
        "max_drawdown_pct": round(drawdown, 2),
        "worst_trade_pct": round(float(series.min()), 2),
    }
    print(
        f"    {label:12s} n={result['trades']:4d} WR={result['win_rate_pct']:5.1f}% "
        f"PF={result['profit_factor']:6.3f} net={result['net_pct']:+8.2f}% "
        f"maxDD={result['max_drawdown_pct']:6.2f}% worst={result['worst_trade_pct']:+6.2f}%"
    )
    return result


def main() -> int:
    frame, daily = load()
    years = sorted(set(daily.index.year))
    print(f"US500 CFD quotes available for: {years}")
    print(f"stop {STOP_PCT}%; 'full_path' tests every bid between the two cash closes\n")

    report: dict[str, object] = {"schema_version": "cfd_full_validation_v1", "years": {}}
    pooled: dict[str, list[pd.Series]] = {"cash_low": [], "full_path": [], "no_stop": []}

    for year in years:
        sub_daily = daily[daily.index.year == year]
        if len(sub_daily) < 100:
            print(f"  {year}: only {len(sub_daily)} session days, skipped")
            continue
        sub_frame = frame[frame["stamp"].dt.year == year]
        print(f"  {year}  ({len(sub_daily)} session days)")
        report["years"][str(year)] = {}
        for model in ("cash_low", "full_path", "no_stop"):
            series = evaluate(sub_frame, sub_daily, model)
            report["years"][str(year)][model] = score(series, model)
            pooled[model].append(series)
        print()

    print("POOLED across all CFD years:")
    report["pooled"] = {}
    for model in ("cash_low", "full_path", "no_stop"):
        combined = pd.concat(pooled[model]).sort_index()
        report["pooled"][model] = score(combined, model)

    cash = report["pooled"]["cash_low"]
    full = report["pooled"]["full_path"]
    report["overnight_path_bias"] = {
        "profit_factor_cash_low": cash["profit_factor"],
        "profit_factor_full_path": full["profit_factor"],
        "net_pct_difference": round(cash["net_pct"] - full["net_pct"], 2),
        "note": "cash_low is what the index-level backtest effectively assumed; "
                "full_path is what a 24h CFD position actually experiences.",
    }
    print(
        f"\novernight-path bias: PF {cash['profit_factor']} -> {full['profit_factor']}, "
        f"net {cash['net_pct']:+.2f}% -> {full['net_pct']:+.2f}% "
        f"({cash['net_pct'] - full['net_pct']:+.2f}pp of hidden loss)"
    )

    out = ROOT / "outputs" / "CFD_FULL_VALIDATION.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
