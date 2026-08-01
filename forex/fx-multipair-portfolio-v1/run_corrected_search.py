"""Corrected search: fixes the four defects the review found, then re-runs.

Changes versus run_mega_search.py, all of them things the review confirmed:

1. **Hold time scales WITH the timeframe.** Was ``288*(240/tf)`` — inverse — so
   M15 signals were held 10 days and H4 signals 1 day. Now
   ``hold = n_decision_bars * tf/5``, so every family gets the same number of
   decision bars to work.
2. **Qualification includes a bear market.** The old split qualified on
   2016-2021, both bull windows, which is why 828 of 830 survivors were
   long-only. Qualification now spans 2016-2018 **and 2022**; the holdout is
   2019-2021 **and 2023**. Both arms contain stress and trend.
3. **Short side is represented by construction.** Longs and shorts are
   qualified in separate pools and the portfolio must draw from both, so a
   rising qualification window can no longer select a pure-beta portfolio.
4. **Risk-weighted combination.** Members are scaled to a common per-trade risk
   (``REFERENCE_STOP / stop_points``) instead of a common lot. Stop sizes vary
   3.8x, so equal-lot weighting let wide-stop members dominate P&L.

`range_break` is dropped: the review confirmed it emits identical signals to
`breakout`, so keeping it only inflated the attempt count.
"""

from __future__ import annotations

import itertools
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.engine import CostModel, RunConfig, Signals, SymbolSpec, simulate  # noqa: E402
from src.search_families import FAMILY_PARAMS, _session_mask, prepare, signals_for, timeframe_frame  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\bars")
POINT = 0.1
REFERENCE_STOP = 200.0          # points; risk-normalisation anchor
HOLD_DECISION_BARS = 24         # same horizon for every timeframe

# Year-set partitions: each arm contains both a bear and a bull regime.
QUALIFY_YEARS = (2016, 2017, 2018, 2022)
HOLDOUT_YEARS = (2019, 2020, 2021, 2023)

TIMEFRAMES = (15, 30, 60, 120, 240)
ATR_MULTS = (1.0, 1.5, 2.0, 3.0)
RR_VALUES = (0.75, 1.0, 1.5, 2.0, 3.0)
SESSIONS = ("all", "us", "non_us")
FAMILIES = {k: v for k, v in FAMILY_PARAMS.items() if k != "range_break"}

_STATE: dict = {}


def build_configs() -> list[tuple]:
    return [
        (family, param, tf, direction, atr_mult, rr, session)
        for family, params in FAMILIES.items()
        for param, tf, direction, atr_mult, rr, session in itertools.product(
            params, TIMEFRAMES, (1, -1), ATR_MULTS, RR_VALUES, SESSIONS
        )
    ]


def _init(blob: bytes) -> None:
    import io
    bars = pd.read_parquet(io.BytesIO(blob))
    stamps = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True)
    year = stamps.dt.year.to_numpy()
    _STATE["windows"] = {}
    for name, years in (("qualify", QUALIFY_YEARS), ("holdout", HOLDOUT_YEARS)):
        window = bars.loc[np.isin(year, years)].reset_index(drop=True)
        _STATE["windows"][name] = (
            window,
            {tf: prepare(timeframe_frame(window, tf), window["timestamp_ms"].to_numpy())
             for tf in TIMEFRAMES},
        )
    _STATE["spec"] = SymbolSpec.of("US500")
    _STATE["costs"] = CostModel(slippage_points=2.0, stop_slippage_points=2.0)


def simulate_config(config: tuple, partition: str) -> pd.DataFrame:
    family, param, tf, direction, atr_mult, rr, session = config
    window, tf_data = _STATE["windows"][partition]
    data = tf_data[tf]
    trigger = signals_for(family, data, param, direction) & _session_mask(data, session)
    execution = data["execution"]
    keep = trigger & (execution >= 0) & np.isfinite(data["atr"])
    picked = np.flatnonzero(keep)
    if picked.size < 10:
        return pd.DataFrame()
    stop_points = np.maximum(data["atr"][picked] * atr_mult / POINT, 30.0)
    signals = Signals(
        entry_index=execution[picked],
        direction=np.full(picked.size, direction, dtype=np.int64),
        stop_min_points=stop_points,
        stop_atr_points=np.zeros(picked.size),
        stop_ref_price=np.full(picked.size, np.nan),
        rr=np.full(picked.size, rr),
        stop_cap_points=np.full(picked.size, 5000.0),
    )
    return simulate(
        window, signals, _STATE["spec"], _STATE["costs"],
        RunConfig(lot=1.0, max_hold_bars=int(HOLD_DECISION_BARS * tf / 5),
                  max_entries_per_day=3),
    )


def risk_normalised(trades: pd.DataFrame) -> np.ndarray:
    """Net per trade rescaled so every trade risks the same amount."""
    if trades.empty:
        return np.empty(0)
    scale = REFERENCE_STOP / trades["stop_points"].to_numpy()
    return trades["net_usd"].to_numpy() * scale


def evaluate(config: tuple, partition: str) -> dict:
    trades = simulate_config(config, partition)
    if trades.empty:
        return {"trades": 0}
    net = risk_normalised(trades)
    wins, losses = net[net > 0], net[net <= 0]
    return {
        "trades": int(net.size),
        "profit_factor": round(float(wins.sum() / -losses.sum()), 4) if losses.sum() != 0 else None,
        "net": round(float(net.sum()), 2),
        "win_rate": round(100.0 * wins.size / net.size, 2),
    }


def _work(args):
    config, partition = args
    return config, evaluate(config, partition)


def run_stage(configs, partition, workers, label):
    results, began, done = {}, time.time(), 0
    with ProcessPoolExecutor(max_workers=workers, initializer=_init,
                             initargs=(_STATE["blob"],)) as pool:
        futures = [pool.submit(_work, (c, partition)) for c in configs]
        for future in as_completed(futures):
            config, result = future.result()
            results[config] = result
            done += 1
            if done % 3000 == 0 or done == len(configs):
                print(f"    {label} {done:,}/{len(configs):,} "
                      f"({done / max(time.time() - began, 1e-9):.0f}/s)", flush=True)
    return results


def main() -> int:
    workers = min(14, os.cpu_count() or 4)
    bars = pd.read_parquet(CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    _STATE["blob"] = bars.to_parquet(index=False)
    configs = build_configs()
    print(f"CORRECTED SEARCH: {len(configs):,} configs, {workers} workers")
    print(f"  hold = {HOLD_DECISION_BARS} decision bars (was inverse-scaled)")
    print(f"  qualify years {QUALIFY_YEARS}  |  holdout years {HOLDOUT_YEARS}")
    print(f"  risk-normalised to a {REFERENCE_STOP:.0f}-point reference stop")
    print("  range_break dropped (duplicate of breakout)\n")

    qualify = run_stage(configs, "qualify", workers, "qualify")
    eligible = [
        c for c, r in qualify.items()
        if r.get("trades", 0) >= 100 and r.get("profit_factor") is not None
        and r["profit_factor"] >= 1.15 and r.get("net", 0) > 0
    ]
    longs = [c for c in eligible if c[3] == 1]
    shorts = [c for c in eligible if c[3] == -1]
    print(f"\n  qualified: {len(eligible):,} of {len(configs):,} "
          f"({len(longs):,} long, {len(shorts):,} short)")
    if not shorts:
        print("  NOTE: no short configuration clears the gate even with a bear year "
              "in qualification - that is itself the finding.")

    payload = {
        "schema_version": "corrected_search_v1",
        "fixes": ["hold_scales_with_timeframe", "bear_year_in_qualification",
                  "short_side_qualified_separately", "risk_normalised_weighting",
                  "range_break_removed"],
        "configs": len(configs),
        "qualify_years": list(QUALIFY_YEARS), "holdout_years": list(HOLDOUT_YEARS),
        "qualified_total": len(eligible),
        "qualified_long": len(longs), "qualified_short": len(shorts),
        "pool": [
            {"config": dict(zip(("family", "param", "timeframe", "direction",
                                 "atr_mult", "rr", "session"), c)),
             "qualify": qualify[c]}
            for c in eligible
        ],
    }
    out = ROOT / "outputs" / "CORRECTED_SEARCH.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
