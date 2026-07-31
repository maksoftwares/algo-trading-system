"""Confirm the frozen index reversal system on real CFD bid/ask quotes.

Everything so far was measured on *index levels* (Yahoo ^GSPC/^DJI/^RUT). That is
not what a Capital.com account trades. This replays the frozen rule on the
broker's own M5 bid/ask bars, so every leg pays the real spread:

* entry at the session close pays the **ask**;
* the 0.5% stop is tested against the **bid low** (a long is stopped by selling);
* exit at the next session close receives the **bid**.

No cost model is applied on top — the quotes already contain the spread, which
is the point of the exercise.

The daily anchor is the US cash-session close (20:00 UTC in summer, 21:00 in
winter), because the index "daily close" the rule was built on is the cash close,
not the CFD's own 24-hour roll.
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
SYMBOLS = ("US500", "US30", "US2000")
STOP_PCT = 0.5


def session_frame(symbol: str) -> pd.DataFrame:
    """One row per trading date: the cash-session close quotes plus that
    session's bid low, used to test the stop."""
    bars = pd.read_parquet(CACHE / f"{symbol}_M5_BIDASK_BROKER.parquet")
    minutes, open_minutes, close_minutes = _session_minutes(bars)
    stamps = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
    frame = bars.assign(
        date=stamps.dt.strftime("%Y-%m-%d"),
        minutes=minutes,
        in_session=(minutes >= open_minutes) & (minutes <= close_minutes),
        at_close=(minutes >= close_minutes - 5) & (minutes <= close_minutes),
    )
    session = frame[frame["in_session"]]
    close_rows = frame[frame["at_close"]].groupby("date").last()
    out = pd.DataFrame(
        {
            "bid_close": close_rows["bid_close"],
            "ask_close": close_rows["ask_close"],
            "mid_close": (close_rows["bid_close"] + close_rows["ask_close"]) / 2.0,
            "session_bid_low": session.groupby("date")["bid_low"].min(),
            "session_bid_open": session.groupby("date")["bid_open"].first(),
            "session_ask_open": session.groupby("date")["ask_open"].first(),
        }
    ).dropna()
    out.index = pd.to_datetime(out.index)
    return out.sort_index()


def replay(symbol: str) -> pd.Series:
    """Net % return per trade, priced on real bid/ask."""
    frame = session_frame(symbol)
    mid = frame["mid_close"]
    signal = (mid / mid.shift(1) - 1) < 0

    entry = frame["ask_close"]                       # buy the ask at the close
    stop = entry * (1 - STOP_PCT / 100.0)
    next_low = frame["session_bid_low"].shift(-1)    # next session's bid path
    next_open_bid = frame["session_bid_open"].shift(-1)
    next_close_bid = frame["bid_close"].shift(-1)    # sell the bid at next close

    exit_price = next_close_bid.copy()
    gapped = next_open_bid <= stop                   # gap through -> fill at open
    hit = (~gapped) & (next_low <= stop)
    exit_price = exit_price.where(~gapped, next_open_bid)
    exit_price = exit_price.where(~hit, stop)

    result = (exit_price / entry - 1.0) * 100.0
    keep = signal & result.notna()
    return result[keep]


def metrics(daily: pd.Series, trades: int, label: str) -> dict:
    equity = daily.cumsum()
    drawdown = float((equity.cummax() - equity).max())
    wins, losses = daily[daily > 0], daily[daily <= 0]
    months = daily.groupby(daily.index.strftime("%Y-%m")).sum()
    keep = np.sort(daily.to_numpy())[: max(daily.size - int(np.ceil(daily.size * 0.05)), 1)]
    kw, kl = keep[keep > 0], keep[keep <= 0]
    years = (daily.index[-1] - daily.index[0]).days / 365.25
    result = {
        "trades": int(trades),
        "trades_per_day": round(trades / (years * 252), 2),
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
        f"{label:26s} n={result['trades']:4d} {result['trades_per_day']:5.2f}/d "
        f"PF={result['profit_factor']:6.3f} exTop5={result['pf_excluding_best_5pct']:6.3f} "
        f"ann={result['annual_pct']:+7.2f}% SR={result['sharpe']:5.2f} "
        f"+mo={result['months_positive_pct']:5.1f}% maxDD={result['max_drawdown_pct']:6.2f}% "
        f"t={result['t_stat']:5.2f}"
    )
    return result


def main() -> int:
    print("CFD CONFIRMATION — frozen rule on real Capital.com bid/ask quotes")
    print("entry pays the ask, stop tested on the bid low, exit receives the bid")
    print("no extra cost model: the spread is already in the quotes\n")

    report: dict[str, object] = {
        "schema_version": "cfd_confirmation_v1",
        "basis": "Capital.com demo M5 bid/ask, session-close anchored",
        "stop_pct": STOP_PCT,
        "per_symbol": {},
    }
    series = {}
    for symbol in SYMBOLS:
        s = replay(symbol)
        series[symbol] = s
        report["per_symbol"][symbol] = metrics(s, s.size, f"  {symbol}")

    combined = pd.concat([s.rename(k) for k, s in series.items()], axis=1, sort=True)
    trades = int(combined.notna().sum().sum())
    portfolio = (combined.fillna(0.0).sum(axis=1) / len(SYMBOLS))
    portfolio = portfolio[combined.notna().any(axis=1)].sort_index()
    print()
    report["portfolio"] = metrics(portfolio, trades, "  PORTFOLIO (1/3 each)")

    print("\n=== index-level result for comparison (validation 2016-2026) ===")
    print("  PORTFOLIO (index lvl)      1.37/d PF= 1.396 exTop5= 0.856 ann= +12.50% "
          "SR= 1.69 +mo= 72.4% maxDD= 11.97%")

    p = report["portfolio"]
    report["verdict"] = {
        "cfd_profit_factor": p["profit_factor"],
        "index_profit_factor": 1.396,
        "direction_confirmed": p["profit_factor"] is not None and p["profit_factor"] > 1.0,
        "note": "14 months of CFD history vs 10 years of index history; this checks that "
                "real spread does not destroy the edge, not that the effect size matches.",
    }
    out = ROOT / "outputs" / "CFD_CONFIRMATION.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
