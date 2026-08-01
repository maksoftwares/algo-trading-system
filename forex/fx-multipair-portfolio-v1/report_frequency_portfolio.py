"""Assemble and score a >=1 trade/day portfolio.

Members are drawn only from configurations that already cleared design and
validation in `run_frequency_hunt.py`. Diversity is enforced across family,
timeframe, direction and session so frequency does not come from ten copies of
one rule.

Scored on two windows never used for member selection:

* holdout 2022-2023 (Dukascopy CFD quotes, includes the 2022 bear year)
* 2025-08 -> 2026-07 (live broker quotes, a different feed entirely)

Risk is split equally across members, so adding members buys frequency and
diversification rather than leverage — the mistake U5 made.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import run_mega_search as MS  # noqa: E402
from src.engine import CostModel, RunConfig, Signals, SymbolSpec, simulate  # noqa: E402
from src.report import slice_window  # noqa: E402
from src.search_families import _session_mask, prepare, signals_for, timeframe_frame  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\bars")
POINT = 0.1
MAX_MEMBERS = 12


def trades_for(config: dict, bars: pd.DataFrame) -> pd.DataFrame:
    data = prepare(timeframe_frame(bars, config["timeframe"]), bars["timestamp_ms"].to_numpy())
    trigger = signals_for(config["family"], data, config["param"], config["direction"])
    trigger &= _session_mask(data, config["session"])
    execution = data["execution"]
    keep = trigger & (execution >= 0) & np.isfinite(data["atr"])
    picked = np.flatnonzero(keep)
    if picked.size == 0:
        return pd.DataFrame()
    stop_points = np.maximum(data["atr"][picked] * config["atr_mult"] / POINT, 30.0)
    signals = Signals(
        entry_index=execution[picked],
        direction=np.full(picked.size, config["direction"], dtype=np.int64),
        stop_min_points=stop_points,
        stop_atr_points=np.zeros(picked.size),
        stop_ref_price=np.full(picked.size, np.nan),
        rr=np.full(picked.size, config["rr"]),
        stop_cap_points=np.full(picked.size, 5000.0),
    )
    return simulate(
        bars, signals, SymbolSpec.of("US500"),
        CostModel(slippage_points=2.0, stop_slippage_points=2.0),
        RunConfig(lot=1.0, max_hold_bars=288 * 10, max_entries_per_day=3),
    )


def select_members(payload: dict) -> list[dict]:
    """Diverse, high-frequency members from the qualified pool."""
    pool = payload["qualified_pool"]
    pool.sort(key=lambda m: -m["design"]["trades"])
    members, seen_family_tf, seen_family = [], set(), {}
    for m in pool:
        c = m["config"]
        key = (c["family"], c["timeframe"], c["direction"], c["session"])
        if key in seen_family_tf:
            continue
        if seen_family.get(c["family"], 0) >= 3:      # cap any one family
            continue
        seen_family_tf.add(key)
        seen_family[c["family"]] = seen_family.get(c["family"], 0) + 1
        members.append(m)
        if len(members) >= MAX_MEMBERS:
            break
    return members


def score(daily: pd.Series, trades: int, days: int, level: float, label: str) -> dict:
    wins, losses = daily[daily > 0], daily[daily <= 0]
    equity = daily.cumsum()
    drawdown = float((equity.cummax() - equity).max())
    months = daily.groupby(daily.index.strftime("%Y-%m")).sum()
    result = {
        "trades": trades,
        "trades_per_active_day": round(trades / days, 2),
        "active_days": days,
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4) if losses.sum() != 0 else None,
        "net_usd": round(float(daily.sum()), 1),
        "net_pct_of_index": round(float(daily.sum()) / level * 100, 2),
        "max_drawdown_pct": round(drawdown / level * 100, 2),
        "months_positive": int((months > 0).sum()),
        "months": int(months.size),
        "win_rate_days_pct": round(100.0 * float((daily > 0).mean()), 1),
    }
    print(
        f"  {label:36s} {result['trades']:>5} trades  {result['trades_per_active_day']:>4.2f}/day  "
        f"PF {result['profit_factor']:>6.3f}  net {result['net_pct_of_index']:>+7.2f}%  "
        f"maxDD {result['max_drawdown_pct']:>5.2f}%  +mo {result['months_positive']}/{result['months']}"
    )
    return result


def evaluate_window(members, bars, label):
    ledgers, total = [], 0
    for m in members:
        t = trades_for(m["config"], bars)
        if t.empty:
            continue
        stamps = pd.to_datetime(t["exit_ms"], unit="ms", utc=True)
        # equal risk per member
        ledgers.append(pd.Series(t["net_usd"].to_numpy() / len(members), index=stamps))
        total += len(t)
    if not ledgers:
        return None, None
    combined = pd.concat(ledgers).sort_index()
    daily = combined.groupby(combined.index.strftime("%Y-%m-%d")).sum()
    daily.index = pd.to_datetime(daily.index)
    level = float(np.median((bars["bid_close"] + bars["ask_close"]) / 2))
    stamps = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
    days = int(stamps.dt.strftime("%Y-%m-%d").nunique())
    return score(daily.sort_index(), total, days, level, label), daily.sort_index()


def main() -> int:
    hunt = json.loads((ROOT / "outputs" / "FREQUENCY_PORTFOLIO.json").read_text())
    if "qualified_pool" not in hunt:
        print("re-running the hunt to capture the full qualified pool...")
        return 2
    members = select_members(hunt)
    print(f"PORTFOLIO: {len(members)} diverse members\n")
    for m in members:
        c = m["config"]
        print(f"  {c['family']:13s} p{c['param']:<3} tf{c['timeframe']:<4} dir{c['direction']:>2} "
              f"atr{c['atr_mult']} rr{c['rr']:<4} {c['session']:6s} | "
              f"design {m['design_trades_per_day']:.2f}/d PF {m['design']['profit_factor']:.3f}")
    print()

    duka = pd.read_parquet(CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    broker = pd.read_parquet(CACHE / "US500_M5_BIDASK_BROKER.parquet")
    report = {"members": [m["config"] for m in members], "windows": {}}
    for label, bars in (
        ("design 2016-2019", slice_window(duka, "2016-01-01", "2020-01-01")),
        ("validation 2020-2021", slice_window(duka, "2020-01-01", "2022-01-01")),
        ("HOLDOUT 2022-2023", slice_window(duka, "2022-01-01", "2024-01-01")),
        ("BROKER 2025-08..2026-07", broker),
    ):
        result, daily = evaluate_window(members, bars.reset_index(drop=True), label)
        if result:
            report["windows"][label] = result
            if label.startswith(("HOLDOUT", "BROKER")):
                months = daily.groupby(daily.index.strftime("%Y-%m")).agg(["sum", "size"])
                report["windows"][label]["monthly"] = {
                    str(k): {"net": round(float(v["sum"]), 1), "days": int(v["size"])}
                    for k, v in months.iterrows()
                }
    (ROOT / "outputs" / "FREQUENCY_PORTFOLIO_RESULT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    print(f"\nwrote {ROOT / 'outputs' / 'FREQUENCY_PORTFOLIO_RESULT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
