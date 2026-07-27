"""Multi-instrument portfolio MI-V1. Config is FROZEN by
PREREGISTRATION_MULTI_INSTRUMENT.md - read it before changing anything here.

The gold V6 mechanism is transplanted unchanged to each instrument: same
confirmation entry, same 6.75xATR stop, same 36h horizon, same session, same
seven specialists with the same gates and percentiles, dedup on, K=4. There is
deliberately no per-instrument tuning knob in this file - that absence is the
whole point, because hindsight in choosing was measured today at 0.3-0.6 PF.

Three deviations are forced by data and were declared in the preregistration:
a 5-feature ranker off gold (3 tick features do not exist there), a per-
instrument ridge refit on dev only (gold's frozen coefficients are unitless
elsewhere), and regime="ALL" off gold (the H4 ledger is XAUUSD-only).

Non-gold sleeves are Dukascopy-only. They are research evidence, not deployment
evidence, no matter how they look.
"""
import argparse, json
import numpy as np, pandas as pd
from pathlib import Path
import engine

FX = Path("D:/AlgoTradingData/research/regime-teacher-eas-v1")


def _fx(sym):
    """Prefer the V2 rebuild (full 8-feature set, amendment A2) when it exists;
    fall back to the 5-feature V1 file otherwise. feats is decided by which file
    is actually present, so a half-finished rebuild cannot silently mix them."""
    v2 = FX / f"{sym}_M5_FEATURES_V2.parquet"
    if v2.exists():
        return dict(path=v2, feats=8)
    return dict(path=FX / f"{sym}_M5_BIDASK_V1.parquet", feats=5)


INSTRUMENTS = {
    "XAUUSD": dict(path=None, feats=8),                       # native, dual-feed
    "EURUSD": _fx("EURUSD"),
    "GBPUSD": _fx("GBPUSD"),
    "USDJPY": _fx("USDJPY"),
    "XAGUSD": _fx("XAGUSD"),
}
# frozen by preregistration section 2
STOP_MULT, HZ, CONF, GRID_MIN, HOUR_LO, HOUR_HI, K_SLOTS = 6.75, 432, 0.5, 30, 7, 17, 4
DEV_END = engine.DEV_END
TEST_END = engine.TEST_END
FEAT5 = ["speed", "activity", "spr", "adv_pre", "align"]
FEAT8 = ["speed", "flow", "imb", "activity", "spr", "eff", "adv_pre", "align"]
# the seven V6 specialists, verbatim
MEMBERS = [
    dict(name="trend_long_core",  gate=None, pct=95),
    dict(name="trend_long_exSh",  gate=None, pct=95),
    dict(name="dipbuy_NY_p75",    gate=0.5,  pct=75, hour_lo=12),
    dict(name="dipbuy_NY_p80",    gate=0.5,  pct=80, hour_lo=12),
    dict(name="dipbuy_day_deep",  gate=1.5,  pct=80),
    dict(name="dipbuy_day_p80",   gate=1.0,  pct=80),
    dict(name="dipbuy_day_p90",   gate=1.0,  pct=90),
]


def load(sym):
    """M5 bid/ask + ATR144 + EMAs, in the layout the mechanism expects."""
    if sym == "XAUUSD":
        f = engine._prep_duka()
        t = pd.to_datetime(f["time"], utc=True)
        d = {k: f[k].values for k in ("mid_high", "mid_low", "mid_close",
                                      "bid_open", "bid_low", "bid_close",
                                      "ask_open", "ask_high", "ask_close")}
        d["atr"] = f["atr144"].values
        d["ema"] = f["ema144"].values
        d["flow"] = np.nan_to_num(f["tick_signed_move"].values)
        d["imb"] = np.nan_to_num(f["tick_book_imbalance_mean"].values)
        d["act"] = np.nan_to_num(f["xau_tick_count"].values)
        d["spr"] = np.nan_to_num(f["tick_spread_mean"].values)
        d["eff"] = np.nan_to_num(f["price_efficiency_5m"].values)
    else:
        df = pd.read_parquet(INSTRUMENTS[sym]["path"]).sort_values("timestamp_ms")
        t = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
        d = {k: df[k].values.astype(float) for k in
             ("mid_high", "mid_low", "mid_close", "bid_open", "bid_low",
              "bid_close", "ask_open", "ask_high", "ask_close")}
        mc = d["mid_close"]
        pc = np.r_[mc[0], mc[:-1]]                      # previous close
        tr = np.maximum.reduce([d["mid_high"] - d["mid_low"],
                                np.abs(d["mid_high"] - pc),
                                np.abs(d["mid_low"] - pc)])
        d["atr"] = pd.Series(tr).rolling(144, min_periods=50).mean().values
        d["ema"] = pd.Series(mc).ewm(span=144, adjust=False).mean().values
        d["act"] = np.nan_to_num(df["tick_count"].values.astype(float))
        spr_col = "tick_spread_mean" if "tick_spread_mean" in df.columns else "spread_mean"
        d["spr"] = np.nan_to_num(df[spr_col].values.astype(float))
        if INSTRUMENTS[sym]["feats"] == 8:      # V2 rebuild, amendment A2
            d["flow"] = np.nan_to_num(df["tick_signed_move"].values.astype(float))
            d["imb"] = np.nan_to_num(df["tick_book_imbalance_mean"].values.astype(float))
            d["eff"] = np.nan_to_num(df["price_efficiency_5m"].values.astype(float))
        else:
            d["flow"] = d["imb"] = d["eff"] = None
    n = len(t)
    mc = d["mid_close"]
    # Amendment A1: commission as a constant fraction of notional. engine.FEE is
    # $0.30 on gold at ~$2,000, i.e. 1.5bp; applying that absolute number to
    # EURUSD at 1.10 charged ~444R per trade and voided run 1. The bid/ask
    # spread is charged separately via ask-fills and bid-exits.
    # Gold keeps its historical constant so the sleeve stays byte-comparable to
    # V6; the scaled rule would have made gold 10% cheaper, flattering the one
    # instrument that is already validated.
    d["fee"] = engine.FEE if sym == "XAUUSD" else 1.5e-4 * float(np.nanmedian(mc))
    ema_slow = pd.Series(mc).ewm(span=2016, adjust=False).mean().shift(1).values
    slope = np.full(n, np.nan)
    slope[288:] = ema_slow[288:] - ema_slow[:-288]
    d["slope"] = slope / np.where(d["atr"] > 0, d["atr"], np.nan)
    d["t"], d["n"] = t, n
    d["hour"], d["minute"] = t.dt.hour.values, t.dt.minute.values
    for k in ("flow", "imb", "eff", "act", "spr"):
        v = d.get(k)
        d["c" + k] = np.concatenate([[0.0], np.cumsum(v)]) if v is not None else None
    return d


def candidates(d, member, nfeat):
    """Confirmed long impulses passing the dip gate and the macro filter, with
    ranker features and realised R. Long-only, exactly as V6."""
    n, mc, atr, ema = d["n"], d["mid_close"], d["atr"], d["ema"]
    mh, ml = d["mid_high"], d["mid_low"]
    bl, bc, ao = d["bid_low"], d["bid_close"], d["ask_open"]
    slope = d["slope"]
    fee = d["fee"]
    lo = member.get("hour_lo", HOUR_LO)
    ok = ((d["minute"] % GRID_MIN == 0) & (d["hour"] >= lo) & (d["hour"] < HOUR_HI)
          & np.isfinite(atr) & np.isfinite(slope) & (atr > 0))
    gate = member["gate"]
    rows = []
    for i in np.flatnonzero(ok):
        if i < 2016 or i + 2 >= n:
            continue
        stop = STOP_MULT * atr[i]
        if not stop > 0:
            continue
        e = mc[i]
        i0, i1 = i + 1, min(i + 1 + HZ, n)
        if i1 - i0 < 20:
            continue
        up, dn = mh[i0:i1] - e, e - ml[i0:i1]
        cu = np.flatnonzero(up >= CONF * stop)
        cd = np.flatnonzero(dn >= CONF * stop)
        if not len(cu) or (len(cd) and cd[0] < cu[0]):
            continue                                   # long-only, as V6
        if gate is not None:                           # dip gate
            pre = (e - mc[i - 24]) / atr[i]
            if pre > -gate:
                continue
        if slope[i] < 0.0:                             # macro uptrend filter
            continue
        k = int(cu[0]); j = i0 + k + 1
        if j + 1 >= i1:
            continue
        nb = k + 1
        a, b = i0, i0 + k + 1
        fe = {"speed": nb,
              "activity": (d["cact"][b] - d["cact"][a]) / nb,
              "spr": ((d["cspr"][b] - d["cspr"][a]) / nb) / stop,
              "adv_pre": float(max(dn[:k + 1].max(), 0.0)) / stop,
              "align": (e - ema[i]) / atr[i]}
        if nfeat == 8:
            fe["flow"] = d["cflow"][b] - d["cflow"][a]
            fe["imb"] = (d["cimb"][b] - d["cimb"][a]) / nb
            fe["eff"] = (d["ceff"][b] - d["ceff"][a]) / nb
        fill = ao[j]; slv = fill - stop
        hit = np.flatnonzero(bl[j:i1] <= slv)
        xi = j + hit[0] if len(hit) else i1 - 1
        xp = slv if len(hit) else bc[xi]
        r = (xp - fill) / stop - fee / stop
        rows.append(dict(i=i, dec_t=d["t"].iloc[i], entry_t=d["t"].iloc[j],
                         exit_t=d["t"].iloc[xi], r=r, stop=stop, **fe))
    return pd.DataFrame(rows)


def rank_and_select(c, feats, pct):
    """Ridge fit on DEV candidates only; threshold at the DEV percentile."""
    if len(c) < 60:
        return c.iloc[0:0]
    dev = (c.dec_t <= DEV_END).values
    if dev.sum() < 40:
        return c.iloc[0:0]
    X = c[feats].values.astype(float)
    mu, sd = X[dev].mean(0), X[dev].std(0) + 1e-9
    Z = (X - mu) / sd
    A = Z[dev].T @ Z[dev] + 5.0 * np.eye(len(feats))
    w = np.linalg.solve(A, Z[dev].T @ c.r.values[dev])
    c = c.assign(score=Z @ w)
    thr = float(np.percentile(c.score.values[dev], pct))
    return c[c.score >= thr]


def sleeve(sym):
    d = load(sym)
    nf = INSTRUMENTS[sym]["feats"]
    feats = FEAT8 if nf == 8 else FEAT5
    parts = []
    for m in MEMBERS:
        c = candidates(d, m, nf)
        if not len(c):
            continue
        s = rank_and_select(c, feats, m["pct"])
        if len(s):
            s = s.assign(spec=m["name"], sym=sym)
            parts.append(s)
    if not parts:
        return pd.DataFrame()
    a = pd.concat(parts).reset_index(drop=True)
    # dedup: one position per distinct setup, best-scored specialist wins
    a = a.sort_values("score", ascending=False).groupby(["i"], as_index=False).first()
    return a.sort_values("dec_t").reset_index(drop=True)


def stats(r):
    if not len(r):
        return dict(n=0, wr=0.0, pf=0.0)
    w, l = r[r > 0], r[r <= 0]
    return dict(n=len(r), wr=round(100 * len(w) / len(r), 1),
                pf=round(float(w.sum() / max(-l.sum(), 1e-9)), 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/MULTI_INSTRUMENT_SLEEVES.parquet")
    a = ap.parse_args()
    print("MI-V1: gold config transplanted unchanged. "
          "Per-instrument gate (preregistered): PF>=1.20 dev AND test, n>=100.\n")
    print(f"{'sym':<8}{'era':<7}{'n':>7}{'WR':>8}{'PF':>7}{'meanR':>8}   verdict")
    keep = []
    for sym in INSTRUMENTS:
        s = sleeve(sym)
        if not len(s):
            print(f"{sym:<8} no trades"); continue
        s["era"] = np.where(s.dec_t <= DEV_END, "dev",
                            np.where(s.dec_t <= TEST_END, "test", "hold"))
        row = {}
        for era in ("dev", "test", "hold"):
            g = s[s.era == era]
            st = stats(g.r.values)
            row[era] = st
            mr = round(float(g.r.mean()), 3) if len(g) else 0.0
            print(f"{sym if era=='dev' else '':<8}{era:<7}{st['n']:>7}"
                  f"{st['wr']:>7}%{st['pf']:>7}{mr:>8}")
        ok = (row["dev"]["pf"] >= 1.20 and row["test"]["pf"] >= 1.20
              and row["dev"]["n"] >= 100 and row["test"]["n"] >= 100)
        print(f"{'':<8}{'':<7}{'':>7}{'':>8}{'':>7}{'':>8}   "
              f"{'PASS - included' if ok else 'FAIL - excluded by preregistered gate'}\n")
        s["included"] = ok
        keep.append(s)
    if keep:
        allt = pd.concat(keep).reset_index(drop=True)
        allt.to_parquet(a.out)
        inc = sorted(allt[allt.included].sym.unique())
        print(f"included by their own record: {inc}")
        print(f"excluded: {sorted(set(allt.sym.unique()) - set(inc))}")


if __name__ == "__main__":
    main()
