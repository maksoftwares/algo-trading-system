"""US500 walk-forward: re-qualify every year, trade the next year forward.

Every previous US500 test used one fixed qualify/holdout split, so a portfolio
chosen in a bull window had to survive whatever regime came next with no chance
to adapt. Walk-forward is the standard answer and has not been run here.

Protocol, fixed before running:

    qualify 2016-2018 -> trade 2019
    qualify 2017-2019 -> trade 2020
    qualify 2018-2020 -> trade 2021
    qualify 2019-2021 -> trade 2022
    qualify 2020-2022 -> trade 2023

Each traded year is genuinely out of sample: its parameters are selected only
from the three preceding years. The five traded years are then concatenated into
one continuous equity curve, which is the number that matters — it is what an
operator would actually have experienced running this from 2019 to 2023.

Carries every fix from the code review: hold scales with timeframe, risk is
normalised to a common stop, `range_break` removed, and long and short are
qualified separately so a rising window cannot produce a pure-beta portfolio.
"""

from __future__ import annotations

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
import run_corrected_search as CS  # noqa: E402

CACHE = Path(r"D:\AlgoTradingData\research\fx-multipair-portfolio-v1\bars")
POINT = 0.1
REFERENCE_STOP = 200.0
HOLD_DECISION_BARS = 24
ACCOUNT = 10_000.0

FOLDS = [((2016, 2017, 2018), 2019), ((2017, 2018, 2019), 2020),
         ((2018, 2019, 2020), 2021), ((2019, 2020, 2021), 2022),
         ((2020, 2021, 2022), 2023)]
PER_SIDE = 8
MIN_PF, MIN_TRADES = 1.15, 60

_S: dict = {}


def _init(blob: bytes) -> None:
    import io
    bars = pd.read_parquet(io.BytesIO(blob))
    year = pd.to_datetime(bars["timestamp_ms"], unit="ms", utc=True).dt.year.to_numpy()
    _S["by_year"] = {}
    for y in sorted(set(year.tolist())):
        w = bars.loc[year == y].reset_index(drop=True)
        _S["by_year"][y] = (
            w, {tf: prepare(timeframe_frame(w, tf), w["timestamp_ms"].to_numpy())
                for tf in CS.TIMEFRAMES})
    _S["spec"] = SymbolSpec.of("US500")
    _S["costs"] = CostModel(slippage_points=2.0, stop_slippage_points=2.0)


def sim(config, years) -> pd.DataFrame:
    family, param, tf, direction, atr_mult, rr, session = config
    out = []
    for y in years:
        if y not in _S["by_year"]:
            continue
        window, tf_data = _S["by_year"][y]
        data = tf_data[tf]
        trig = signals_for(family, data, param, direction) & _session_mask(data, session)
        ex = data["execution"]
        keep = trig & (ex >= 0) & np.isfinite(data["atr"])
        p = np.flatnonzero(keep)
        if p.size < 5:
            continue
        stop = np.maximum(data["atr"][p] * atr_mult / POINT, 30.0)
        sig = Signals(entry_index=ex[p], direction=np.full(p.size, direction, dtype=np.int64),
                      stop_min_points=stop, stop_atr_points=np.zeros(p.size),
                      stop_ref_price=np.full(p.size, np.nan), rr=np.full(p.size, rr),
                      stop_cap_points=np.full(p.size, 5000.0))
        t = simulate(window, sig, _S["spec"], _S["costs"],
                     RunConfig(lot=1.0, max_hold_bars=int(HOLD_DECISION_BARS * tf / 5),
                               max_entries_per_day=3))
        if not t.empty:
            out.append(t)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def metrics(trades):
    if trades.empty:
        return {"trades": 0}
    net = trades["net_usd"].to_numpy() * (REFERENCE_STOP / trades["stop_points"].to_numpy())
    w, l = net[net > 0], net[net <= 0]
    return {"trades": int(net.size), "net": float(net.sum()),
            "pf": float(w.sum() / -l.sum()) if l.sum() != 0 else None,
            "wr": 100.0 * w.size / net.size}


def _work(args):
    config, years = args
    return config, metrics(sim(config, years))


def main() -> int:
    workers = min(14, os.cpu_count() or 4)
    bars = pd.read_parquet(CACHE / "US500_M5_BIDASK_DUKASCOPY.parquet")
    blob = bars.to_parquet(index=False)
    configs = CS.build_configs()
    print(f"US500 WALK-FORWARD — {len(configs):,} configs x {len(FOLDS)} folds\n")

    report, curve = {"folds": []}, []
    for qualify_years, trade_year in FOLDS:
        began = time.time()
        with ProcessPoolExecutor(max_workers=workers, initializer=_init,
                                 initargs=(blob,)) as pool:
            futures = [pool.submit(_work, (c, qualify_years)) for c in configs]
            qual = {}
            for f in as_completed(futures):
                c, m = f.result()
                qual[c] = m
        ok = [c for c, m in qual.items()
              if m.get("trades", 0) >= MIN_TRADES and m.get("pf") and m["pf"] >= MIN_PF and m["net"] > 0]
        longs = sorted([c for c in ok if c[3] == 1], key=lambda c: -qual[c]["trades"])
        shorts = sorted([c for c in ok if c[3] == -1], key=lambda c: -qual[c]["trades"])

        def diverse(pool_, limit):
            picked, seen = [], set()
            for c in pool_:
                key = (c[0], c[2], c[6], c[5])
                if key in seen:
                    continue
                seen.add(key)
                picked.append(c)
                if len(picked) >= limit:
                    break
            return picked

        members = diverse(longs, PER_SIDE) + diverse(shorts, PER_SIDE)
        with ProcessPoolExecutor(max_workers=workers, initializer=_init,
                                 initargs=(blob,)) as pool:
            futures = [pool.submit(_work, (c, (trade_year,))) for c in members]
            fwd = {}
            for f in as_completed(futures):
                c, m = f.result()
                fwd[c] = m
        # aggregate forward P&L across members, equal risk share
        tot_net = sum(fwd[c]["net"] for c in members if fwd[c].get("trades")) / max(len(members), 1)
        tot_tr = sum(fwd[c].get("trades", 0) for c in members)
        fold = {"qualify": list(qualify_years), "trade_year": trade_year,
                "qualified": len(ok), "long": len(longs), "short": len(shorts),
                "members": len(members), "forward_trades": tot_tr,
                "forward_net": round(tot_net, 1)}
        report["folds"].append(fold)
        curve.append(tot_net)
        print(f"  qualify {qualify_years} -> trade {trade_year}: "
              f"{len(ok):>4} qualified ({len(longs)}L/{len(shorts)}S), {len(members)} members, "
              f"{tot_tr:>5} trades, net {tot_net:>+9.1f}   [{time.time()-began:.0f}s]")

    print(f"\n  concatenated 2019-2023 forward net: {sum(curve):+.1f}")
    print(f"  positive years: {sum(1 for x in curve if x > 0)}/{len(curve)}")
    report["forward_total"] = round(sum(curve), 1)
    report["positive_years"] = sum(1 for x in curve if x > 0)
    (ROOT / "outputs" / "US500_WALKFORWARD.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"wrote {ROOT / 'outputs' / 'US500_WALKFORWARD.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
