"""US500 short-term reversal system — build and score against the forex bar.

Signal, deliberately minimal: after N consecutive down closes, go long at the
close and exit at the next close. One parameter (N). No thresholds, no hour
masks, no per-year tuning — the FX lane's four overfit candidates all came from
richer parameterisations than this.

Why this signal is trusted more than anything the FX lane produced:

* it is monotonic in N (dose-response), not a single lucky cell;
* it is independently significant in 1996-2015 *and* 2016-2026, and the later
  window is *stronger*, not decayed;
* it reproduces on 9 of 10 world indices (6 of 10 at t > 2 after three down
  days), so it is not a US500 data artifact;
* short-term reversal in equity indices is a long-documented effect.

Cost is the measured Capital.com US500 spread: 6 points at p95, point 0.1, so
0.6 index points round trip = 0.008% at current levels. Stress at 2x and 4x.
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
COST_PCT = 0.0080          # 0.6 index points at ~7,468
ACCOUNT_USD = 10_000.0
RISK_PCT_PER_TRADE = 1.0   # notional sized so 1% of account moves per 1% index move

PARTITIONS = {
    "design": ("1996-01-01", "2016-01-01"),
    "validation": ("2016-01-01", "2026-08-01"),
}


def load_spx() -> pd.DataFrame:
    frame = pd.read_parquet(CACHE / "index" / "SPX_DAILY.parquet")
    frame = frame[frame["date"] >= "1996-01-01"].reset_index(drop=True)
    frame["ret"] = (frame["close"] / frame["close"].shift(1) - 1) * 100
    return frame


def signals(frame: pd.DataFrame, down_days: int) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for k in range(down_days):
        mask &= frame["ret"].shift(k) < 0
    return mask & frame["ret"].shift(-1).notna()


def trades(frame: pd.DataFrame, mask: pd.Series, cost_pct: float) -> pd.DataFrame:
    forward = frame["ret"].shift(-1)
    rows = frame.loc[mask, ["date", "close"]].copy()
    rows["gross_pct"] = forward[mask].to_numpy()
    rows["net_pct"] = rows["gross_pct"] - cost_pct
    rows["pnl_usd"] = rows["net_pct"] / 100.0 * ACCOUNT_USD * RISK_PCT_PER_TRADE
    return rows.reset_index(drop=True)


def score(rows: pd.DataFrame, years: float) -> dict:
    if rows.empty:
        return {"trades": 0}
    net = rows["net_pct"].to_numpy()
    wins, losses = net[net > 0], net[net <= 0]
    equity = np.cumsum(net)
    drawdown = float(np.max(np.maximum.accumulate(equity) - equity))
    months = rows.groupby(rows["date"].dt.strftime("%Y-%m"))["net_pct"].sum()
    # PF after dropping the best 5% of trades
    keep = np.sort(net)[: max(net.size - int(np.ceil(net.size * 0.05)), 1)]
    kw, kl = keep[keep > 0], keep[keep <= 0]
    return {
        "trades": int(net.size),
        "trades_per_year": round(net.size / years, 1),
        "trades_per_trading_day": round(net.size / (years * 252), 3),
        "win_rate_pct": round(100.0 * wins.size / net.size, 2),
        "mean_net_pct": round(float(net.mean()), 4),
        "total_net_pct": round(float(net.sum()), 1),
        "annual_net_pct": round(float(net.sum()) / years, 2),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4) if losses.size else None,
        "pf_excluding_best_5pct": round(float(kw.sum() / -kl.sum()), 4) if kl.size else None,
        "sharpe": round(float(net.mean() / net.std(ddof=1) * np.sqrt(252)), 3),
        "max_drawdown_pct_of_account": round(drawdown, 2),
        "months_active": int(months.size),
        "months_positive_pct": round(100.0 * float((months > 0).mean()), 1),
        "t_stat": round(float(net.mean() / (net.std(ddof=1) / np.sqrt(net.size))), 2),
    }


def main() -> int:
    frame = load_spx()
    print(f"^SPX daily {frame['date'].iloc[0].date()} .. {frame['date'].iloc[-1].date()}  n={len(frame):,}")
    print(f"cost {COST_PCT}%/trade; account ${ACCOUNT_USD:,.0f}; 1x notional\n")

    report: dict[str, object] = {"schema_version": "us500_reversal_system_v1", "cost_pct": COST_PCT}
    print(f"{'N':>2} {'window':11s} {'trades':>7} {'/day':>6} {'WR%':>6} {'PF':>7} "
          f"{'exTop5':>7} {'ann%':>7} {'SR':>6} {'+mo%':>6} {'t':>6}")
    print("-" * 86)
    for down_days in (1, 2, 3):
        report[f"N{down_days}"] = {}
        for window, (start, end) in PARTITIONS.items():
            sub = frame[(frame["date"] >= start) & (frame["date"] < end)].reset_index(drop=True)
            sub["ret"] = (sub["close"] / sub["close"].shift(1) - 1) * 100
            years = (sub["date"].iloc[-1] - sub["date"].iloc[0]).days / 365.25
            result = score(trades(sub, signals(sub, down_days), COST_PCT), years)
            report[f"N{down_days}"][window] = result
            if result["trades"]:
                print(
                    f"{down_days:>2} {window:11s} {result['trades']:>7} "
                    f"{result['trades_per_trading_day']:>6.2f} {result['win_rate_pct']:>6.2f} "
                    f"{result['profit_factor']:>7.3f} {result['pf_excluding_best_5pct']:>7.3f} "
                    f"{result['annual_net_pct']:>7.2f} {result['sharpe']:>6.3f} "
                    f"{result['months_positive_pct']:>6.1f} {result['t_stat']:>6.2f}"
                )
        print()

    print("cost stress on N=1, full sample:")
    full_years = (frame["date"].iloc[-1] - frame["date"].iloc[0]).days / 365.25
    stress = {}
    for multiple in (1, 2, 4):
        result = score(trades(frame, signals(frame, 1), COST_PCT * multiple), full_years)
        stress[f"{multiple}x"] = result
        print(
            f"  {multiple}x cost ({COST_PCT * multiple:.4f}%): PF {result['profit_factor']:.3f}  "
            f"ann {result['annual_net_pct']:+.2f}%  SR {result['sharpe']:.3f}"
        )
    report["cost_stress_N1"] = stress

    # Forex-bar comparison, judged on the validation window
    bar = report["N1"]["validation"]
    gates = {
        "profit_factor_ge_1.40": (bar["profit_factor"], bar["profit_factor"] >= 1.40),
        "trades_per_day_ge_0.50": (bar["trades_per_trading_day"], bar["trades_per_trading_day"] >= 0.50),
        "months_positive_ge_55pct": (bar["months_positive_pct"], bar["months_positive_pct"] >= 55.0),
        "pf_ex_best5pct_ge_1.20": (bar["pf_excluding_best_5pct"], bar["pf_excluding_best_5pct"] >= 1.20),
        "pf_at_2x_cost_ge_1.15": (stress["2x"]["profit_factor"], stress["2x"]["profit_factor"] >= 1.15),
        "max_dd_le_15pct": (bar["max_drawdown_pct_of_account"], bar["max_drawdown_pct_of_account"] <= 15.0),
    }
    print("\n=== forex-bar gates, judged on validation (N=1) ===")
    for name, (value, passed) in gates.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {name:30s} = {value}")
    report["forex_bar_gates"] = {k: {"value": v, "passed": bool(p)} for k, (v, p) in gates.items()}
    report["all_gates_passed"] = all(p for _, p in gates.values())
    print(f"\nALL GATES PASSED: {report['all_gates_passed']}")

    out = ROOT / "outputs" / "US500_SYSTEM.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
