"""Rebuild non-gold M5 datasets WITH the three tick-microstructure features.

The control in amendment A2 showed these features carry most of the edge - gold
falls from PF 1.89 to 1.10 on test without them, landing exactly where the FX
sleeves did. The FX instruments were therefore never given a fair test, and this
removes the handicap.

Definitions were recovered from gold's own raw ticks and verified at correlation
1.0000 with identical medians against the stored gold parquet
(see verify_tick_features.py):

    tick_signed_move          = sum(sign(diff(mid)))          up-ticks - down-ticks
    price_efficiency_5m       = |net move| / sum(|diff(mid)|)
    tick_book_imbalance_mean  = mean((bidVol - askVol)/(bidVol + askVol))
    tick_spread_mean          = mean(ask - bid)
    tick_count                = number of ticks in the bar

Decoding mirrors the existing builder: cumulative integer deltas x multiplier on
a base timestamp/bid/ask. Integer cumsum is exact, so the vectorised form matches
the reference loop.
"""
import argparse, glob, json, os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd

RAW = Path("D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/raw")
OUT = Path("D:/AlgoTradingData/research/regime-teacher-eas-v1")
SCALE = {"EURUSD": 5, "GBPUSD": 5, "USDJPY": 3, "XAGUSD": 3,
         "DOLLARIDXUSD": 3, "USTBONDTRUSD": 3}


def decode(path, nd):
    try:
        with open(path, "rb") as fh:
            p = json.loads(fh.read())
    except Exception:
        return None
    if not p.get("times"):
        return None
    try:
        t0, mult = int(p["timestamp"]), float(p["multiplier"])
        b0, a0 = float(p["bid"]), float(p["ask"])
        ts = t0 + np.cumsum(np.asarray(p["times"], dtype=np.int64))
        bid = np.round(b0 + np.cumsum(np.asarray(p["bids"], dtype=np.int64)) * mult, nd)
        ask = np.round(a0 + np.cumsum(np.asarray(p["asks"], dtype=np.int64)) * mult, nd)
        bv = np.asarray(p["bidVolumes"], dtype=float)
        av = np.asarray(p["askVolumes"], dtype=float)
    except Exception:
        return None
    return ts, bid, ask, bv, av


def bars_from_file(args):
    path, nd = args
    d = decode(path, nd)
    if d is None:
        return None
    ts, bid, ask, bv, av = d
    mid = (bid + ask) / 2.0
    bar = (ts // 300000) * 300000
    df = pd.DataFrame(dict(bar=bar, bid=bid, ask=ask, mid=mid,
                           spread=ask - bid, bv=bv, av=av))
    out = []
    for b, g in df.groupby("bar", sort=True):
        m = g.mid.values
        if len(m) < 2:
            continue
        dm = np.diff(m)
        tot = np.abs(dm).sum()
        s = g.bv.values + g.av.values
        imb = np.divide(g.bv.values - g.av.values, s,
                        out=np.zeros(len(s)), where=s > 0)
        out.append((
            b,
            g.bid.values[0], g.bid.values.max(), g.bid.values.min(), g.bid.values[-1],
            g.ask.values[0], g.ask.values.max(), g.ask.values.min(), g.ask.values[-1],
            m[0], m.max(), m.min(), m[-1],
            float(np.sum(np.sign(dm))),                       # tick_signed_move
            float(np.mean(imb)),                              # book imbalance
            abs(m[-1] - m[0]) / tot if tot > 0 else 0.0,      # price efficiency
            float(g.spread.mean()),                           # spread mean
            len(m)))                                          # tick count
    return out


COLS = ["timestamp_ms", "bid_open", "bid_high", "bid_low", "bid_close",
        "ask_open", "ask_high", "ask_low", "ask_close",
        "mid_open", "mid_high", "mid_low", "mid_close",
        "tick_signed_move", "tick_book_imbalance_mean", "price_efficiency_5m",
        "tick_spread_mean", "tick_count"]


def build(symbol, workers):
    nd = SCALE[symbol]
    files = sorted(glob.glob(str(RAW / symbol / "**" / "*.json"), recursive=True))
    if not files:
        print(f"{symbol}: no raw files"); return None
    print(f"{symbol}: {len(files):,} hourly tick files, {workers} workers", flush=True)
    rows, done = [], 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(bars_from_file, ((f, nd) for f in files), chunksize=64):
            done += 1
            if res:
                rows.extend(res)
            if done % 10000 == 0:
                print(f"   {symbol}: {done:,}/{len(files):,} files, "
                      f"{len(rows):,} bars", flush=True)
    if not rows:
        print(f"{symbol}: decoded nothing"); return None
    df = pd.DataFrame(rows, columns=COLS).drop_duplicates("timestamp_ms")
    df = df.sort_values("timestamp_ms").reset_index(drop=True)
    df["bar_start_utc"] = pd.to_datetime(df.timestamp_ms, unit="ms", utc=True)
    p = OUT / f"{symbol}_M5_FEATURES_V2.parquet"
    df.to_parquet(p, index=False)
    t = df.bar_start_utc
    print(f"{symbol}: {len(df):,} bars {t.min():%Y-%m-%d} -> {t.max():%Y-%m-%d} -> {p.name}",
          flush=True)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="EURUSD,GBPUSD")
    ap.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) - 1))
    a = ap.parse_args()
    for s in a.symbols.split(","):
        build(s.strip(), a.workers)


if __name__ == "__main__":
    main()
