"""Mega-search: >10,000 strategy attempts with a chance benchmark.

Per MEGA_SEARCH_PREREGISTRATION.md. Three staged gates on real US500 CFD M5
bid/ask quotes (full 24h path, so the U11 overnight-bar error cannot recur),
and — the part that actually matters — the survivor count at each stage is
compared against what pure noise produces on sign-flipped data.

Usage:
    python run_mega_search.py                 # real data
    python run_mega_search.py --null          # sign-flipped null run
"""

from __future__ import annotations

import argparse
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
from src.search_families import FAMILY_PARAMS, prepare, signals_for, timeframe_frame, _session_mask  # noqa: E402
from src.report import slice_window  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\bars")
SYMBOL = "US500"
POINT = 0.1
SLIPPAGE, STOP_SLIPPAGE = 2.0, 2.0

PARTITIONS = {
    "design": ("2016-01-01", "2020-01-01"),
    "validation": ("2020-01-01", "2022-01-01"),
    "holdout": ("2022-01-01", "2024-01-01"),
}
TIMEFRAMES = (15, 30, 60, 120, 240)
DIRECTIONS = (1, -1)
ATR_MULTS = (1.0, 1.5, 2.0, 3.0)
RR_VALUES = (0.75, 1.0, 1.5, 2.0, 3.0)
SESSIONS = ("all", "us", "non_us")

GATE1 = {"min_pf": 1.20, "min_trades": 100}
GATE2 = {"min_pf": 1.10, "min_trades": 30}

_STATE: dict = {}


def build_configs() -> list[tuple]:
    configs = []
    for family, params in FAMILY_PARAMS.items():
        for param, tf, direction, atr_mult, rr, session in itertools.product(
            params, TIMEFRAMES, DIRECTIONS, ATR_MULTS, RR_VALUES, SESSIONS
        ):
            configs.append((family, param, tf, direction, atr_mult, rr, session))
    return configs


def _init(bars_blob: bytes, null_mode: bool) -> None:
    import io
    bars = pd.read_parquet(io.BytesIO(bars_blob))
    if null_mode:
        # Sign-flip mid returns, rebuild a synthetic price path with the same
        # volatility structure and no drift, keeping the real spread.
        rng = np.random.default_rng(20260801)
        mid_close = (bars["bid_close"].to_numpy() + bars["ask_close"].to_numpy()) / 2.0
        step = np.diff(mid_close, prepend=mid_close[0])
        flipped = step * rng.choice([-1.0, 1.0], size=step.size)
        synthetic = mid_close[0] + np.cumsum(flipped)
        half = (bars["ask_close"].to_numpy() - bars["bid_close"].to_numpy()) / 2.0
        span_hi = bars["ask_high"].to_numpy() - bars["ask_close"].to_numpy()
        span_lo = bars["bid_close"].to_numpy() - bars["bid_low"].to_numpy()
        bars = bars.assign(
            bid_close=synthetic - half, ask_close=synthetic + half,
            bid_open=synthetic - half, ask_open=synthetic + half,
            bid_high=synthetic - half + span_hi, ask_high=synthetic + half + span_hi,
            bid_low=synthetic - half - span_lo, ask_low=synthetic + half - span_lo,
        )
    _STATE["windows"] = {}
    for name, (lo, hi) in PARTITIONS.items():
        window = slice_window(bars, lo, hi).reset_index(drop=True)
        tf_data = {
            tf: prepare(timeframe_frame(window, tf), window["timestamp_ms"].to_numpy())
            for tf in TIMEFRAMES
        }
        _STATE["windows"][name] = (window, tf_data)
    _STATE["spec"] = SymbolSpec.of(SYMBOL)
    _STATE["costs"] = CostModel(slippage_points=SLIPPAGE, stop_slippage_points=STOP_SLIPPAGE)


def evaluate(config: tuple, partition: str) -> dict:
    family, param, tf, direction, atr_mult, rr, session = config
    window, tf_data = _STATE["windows"][partition]
    data = tf_data[tf]

    trigger = signals_for(family, data, param, direction) & _session_mask(data, session)
    execution = data["execution"]
    keep = trigger & (execution >= 0) & np.isfinite(data["atr"])
    picked = np.flatnonzero(keep)
    if picked.size < 10:
        return {"trades": 0}

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
    hold = int(288 * (240 / tf))
    trades = simulate(
        window, signals, _STATE["spec"], _STATE["costs"],
        RunConfig(lot=1.0, max_hold_bars=min(hold, 288 * 10), max_entries_per_day=3),
    )
    if trades.empty:
        return {"trades": 0}
    net = trades["net_usd"].to_numpy()
    wins, losses = net[net > 0], net[net <= 0]
    pf = float(wins.sum() / -losses.sum()) if losses.size and losses.sum() != 0 else None
    return {
        "trades": int(net.size),
        "profit_factor": None if pf is None else round(pf, 4),
        "net": round(float(net.sum()), 2),
        "win_rate": round(100.0 * wins.size / net.size, 2),
    }


def _work(args):
    config, partition = args
    return config, evaluate(config, partition)


def run_stage(configs, partition, workers, label):
    results = {}
    began, done = time.time(), 0
    with ProcessPoolExecutor(
        max_workers=workers, initializer=_init,
        initargs=(_STATE["blob"], _STATE["null"]),
    ) as pool:
        futures = [pool.submit(_work, (c, partition)) for c in configs]
        for future in as_completed(futures):
            config, result = future.result()
            results[config] = result
            done += 1
            if done % 2000 == 0 or done == len(configs):
                rate = done / max(time.time() - began, 1e-9)
                print(f"    {label} {done:,}/{len(configs):,} ({rate:.0f}/s)", flush=True)
    return results


def passes(result, gate):
    return (
        result.get("trades", 0) >= gate["min_trades"]
        and result.get("profit_factor") is not None
        and result["profit_factor"] >= gate["min_pf"]
        and result.get("net", 0) > 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--null", action="store_true", help="sign-flipped null run")
    parser.add_argument("--workers", type=int, default=min(14, os.cpu_count() or 4))
    args = parser.parse_args()

    bars = pd.read_parquet(CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    _STATE["blob"] = bars.to_parquet(index=False)
    _STATE["null"] = args.null
    configs = build_configs()
    tag = "NULL" if args.null else "REAL"
    print(f"=== {tag} RUN: {len(configs):,} configurations, {args.workers} workers ===")
    print(f"US500 CFD M5 bid/ask, {len(bars):,} bars, full 24h path\n")

    print("  stage 1: design 2016-2019")
    design = run_stage(configs, "design", args.workers, "design")
    s1 = [c for c in configs if passes(design[c], GATE1)]
    print(f"  -> {len(s1):,} of {len(configs):,} pass ({100*len(s1)/len(configs):.2f}%)\n")

    s2, validation = [], {}
    if s1:
        print("  stage 2: validation 2020-2021")
        validation = run_stage(s1, "validation", args.workers, "valid")
        s2 = [c for c in s1 if passes(validation[c], GATE2)]
        print(f"  -> {len(s2):,} of {len(s1):,} pass ({100*len(s2)/max(len(s1),1):.2f}%)\n")

    s3, holdout = [], {}
    if s2:
        print("  stage 3: HOLDOUT 2022-2023 (touched once)")
        holdout = run_stage(s2, "holdout", args.workers, "holdout")
        s3 = [c for c in s2 if passes(holdout[c], GATE2)]
        print(f"  -> {len(s3):,} of {len(s2):,} pass ({100*len(s3)/max(len(s2),1):.2f}%)\n")

    payload = {
        "schema_version": "mega_search_v1",
        "mode": tag,
        "configurations": len(configs),
        "stage1_design_survivors": len(s1),
        "stage2_validation_survivors": len(s2),
        "stage3_holdout_survivors": len(s3),
        "gates": {"stage1": GATE1, "stage2": GATE2},
        "survivors": [
            {
                "config": dict(zip(
                    ("family", "param", "timeframe", "direction", "atr_mult", "rr", "session"), c)),
                "design": design[c], "validation": validation.get(c), "holdout": holdout.get(c),
            }
            for c in s3
        ],
    }
    out = ROOT / "outputs" / f"MEGA_SEARCH_{tag}.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"attempts {len(configs):,} | s1 {len(s1):,} | s2 {len(s2):,} | s3 {len(s3):,}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
