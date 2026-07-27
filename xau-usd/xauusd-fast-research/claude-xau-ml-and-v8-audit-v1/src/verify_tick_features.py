"""Recover the EXACT definitions of gold's three tick-microstructure features.

The control experiment showed these features carry most of the edge: gold drops
from PF 1.89 to 1.10 on test without them, which is where the FX instruments
landed. So the FX sleeves were never given a fair test, and rebuilding their
datasets with the same features is the honest re-run.

Rebuilding requires matching the definitions, not approximating them. This
decodes gold's own raw tick files, computes several candidate definitions per
feature, and correlates each against the values stored in the gold parquet. The
definition that matches at ~1.0 is the one the foundation used.
"""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
import engine

RAW = Path("D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/raw")


def decode(path):
    p = json.loads(open(path, "rb").read())
    t0, mult = int(p["timestamp"]), float(p["multiplier"])
    b0, a0 = float(p["bid"]), float(p["ask"])
    ts = t0 + np.cumsum(np.asarray(p["times"], dtype=np.int64))
    bid = b0 + np.cumsum(np.asarray(p["bids"], dtype=np.int64)) * mult
    ask = a0 + np.cumsum(np.asarray(p["asks"], dtype=np.int64)) * mult
    bv = np.asarray(p["bidVolumes"], dtype=float)
    av = np.asarray(p["askVolumes"], dtype=float)
    return ts, bid, ask, bv, av


def main():
    files = sorted(glob.glob(str(RAW / "XAUUSD" / "**" / "*.json"), recursive=True))
    files = [f for f in files if "year=2019" in f][:24]
    if not files:
        print("no gold raw tick files found"); return
    rows = []
    for f in files:
        try:
            ts, bid, ask, bv, av = decode(f)
        except Exception:
            continue
        mid = (bid + ask) / 2.0
        spread = ask - bid
        imb = (bv - av) / np.where(bv + av > 0, bv + av, np.nan)
        bar = (ts // 300000) * 300000            # 5-minute buckets
        df = pd.DataFrame(dict(bar=bar, mid=mid, spread=spread, imb=imb))
        for b, g in df.groupby("bar"):
            m = g.mid.values
            d = np.diff(m)
            if len(m) < 2:
                continue
            rows.append(dict(
                timestamp_ms=b, n=len(m),
                # candidate definitions for tick_signed_move
                sm_net=m[-1] - m[0],
                sm_sumsign=float(np.sum(np.sign(d))),
                sm_sumabs_signed=float(np.sum(d)),
                sm_upminusdown=float((d > 0).sum() - (d < 0).sum()),
                # candidates for price_efficiency
                eff_ratio=abs(m[-1] - m[0]) / max(np.abs(d).sum(), 1e-12),
                # book imbalance
                imb_mean=float(np.nanmean(g.imb.values)),
                spr_mean=float(g.spread.mean())))
    if not rows:
        print("decoded nothing"); return
    mine = pd.DataFrame(rows)
    gold = pd.read_parquet(engine.DUKA, columns=[
        "timestamp_ms", "tick_signed_move", "tick_book_imbalance_mean",
        "price_efficiency_5m", "tick_spread_mean", "xau_tick_count"])
    j = mine.merge(gold, on="timestamp_ms", how="inner")
    print(f"matched {len(j)} five-minute bars against the stored gold features\n")

    def corr(a, b):
        m = np.isfinite(j[a]) & np.isfinite(j[b])
        return np.corrcoef(j.loc[m, a], j.loc[m, b])[0, 1] if m.sum() > 10 else np.nan

    print("tick_signed_move - which definition matches?")
    for c in ("sm_net", "sm_sumsign", "sm_sumabs_signed", "sm_upminusdown"):
        print(f"   {c:<18} corr = {corr(c, 'tick_signed_move'):+.4f}")
    print("\nprice_efficiency_5m")
    print(f"   {'eff_ratio':<18} corr = {corr('eff_ratio', 'price_efficiency_5m'):+.4f}")
    print("\ntick_book_imbalance_mean")
    print(f"   {'imb_mean':<18} corr = {corr('imb_mean', 'tick_book_imbalance_mean'):+.4f}")
    print("\ntick_spread_mean  (sanity check - should be ~1.0)")
    print(f"   {'spr_mean':<18} corr = {corr('spr_mean', 'tick_spread_mean'):+.4f}")
    print("\nxau_tick_count  (sanity check - should be ~1.0)")
    print(f"   {'n':<18} corr = {corr('n', 'xau_tick_count'):+.4f}")
    print("\nscale check (mine vs stored, medians):")
    for a, b in (("sm_sumsign", "tick_signed_move"), ("eff_ratio", "price_efficiency_5m"),
                 ("imb_mean", "tick_book_imbalance_mean"), ("spr_mean", "tick_spread_mean"),
                 ("n", "xau_tick_count")):
        print(f"   {a:<18} {j[a].median():>12.5f}   {b:<26} {j[b].median():>12.5f}")


if __name__ == "__main__":
    main()
