"""Build the feature matrix for V60 trades: market state + PORTFOLIO state.

The portfolio-state block is the point of this lane. V60's nine sleeves each
decide independently — none of them knows how many positions are already open,
what the concurrent risk is, or whether the account is in drawdown. That is
information the system provably does not use, which makes it the only place a
model can add something the sleeves have not already priced in.

Every feature is computed from completed bars and from trades that have already
CLOSED at the moment of entry. Nothing derived from the trade's own outcome is
allowed in, and `assert_causal()` enforces that against the forbidden list.
"""
from __future__ import annotations
import heapq
import numpy as np
import pandas as pd

LEDGER = ("C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system/xau-usd/"
          "xauusd-fast-research/one-trade-per-day-floating-equity-v60/outputs/"
          "ONE_TRADE_PER_DAY_FLOATING_EQUITY_V60_PRICE_LEDGER.parquet")
DUKA = ("D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/research/"
        "xau-confirmed-event-specialists-v1/m5_bidask_features_v1.parquet")
PNL = "fee_stress_pnl_usd"
FEED_START = pd.Timestamp("2016-07-01", tz="UTC")

FORBIDDEN = ["exit_time", "exit_price", "pnl_usd", PNL, "source_pnl_usd",
             "gross_endpoint_pnl_usd", "endpoint_error_usd", "source_exit_time",
             "implied_cost_usd", "open_cost_usd", "fee_stress_implied_cost_usd",
             "fee_stress_open_cost_usd", "duration"]

MARKET = ["atr_ratio", "rv_1h", "rv_24h", "slope_atr", "ret_1h", "ret_4h",
          "ret_24h", "dist_hi_24h", "dist_lo_24h", "hour", "dow",
          "ms_flow", "ms_imb", "ms_eff", "ms_spread_per_risk", "ms_activity"]
# `same_sleeve_open` is dropped: V60 caps almost every sleeve at one position, so
# it is identically zero. `risk_usd` is dropped as a per-trade feature: the
# R1_NATIVE_POSITION sleeve records none (444 of 444 NaN) and it is the single
# most profitable sleeve, so keeping it would silently discard 21% of the book
# and 52% of the profit.
PORTFOLIO = ["open_positions", "open_risk_usd", "pnl_last5", "pnl_last20",
             "dd_from_peak", "hours_since_loss", "trades_today"]
TRADE = ["is_long", "is_core"]


def load_ledger():
    d = pd.read_parquet(LEDGER)
    for c in ("entry_time", "exit_time", "signal_time"):
        d[c] = pd.to_datetime(d[c], utc=True)
    d = d[d.entry_time >= FEED_START].copy()
    return d.sort_values("entry_time").reset_index(drop=True)


def load_market():
    """The raw foundation parquet carries `atr` but not the 144-bar ATR/EMA the
    engine derives, so derive them here rather than importing the engine from
    another worktree."""
    f = pd.read_parquet(DUKA, columns=[
        "timestamp_ms", "mid_close", "mid_high", "mid_low", "atr",
        "tick_signed_move", "tick_book_imbalance_mean", "price_efficiency_5m",
        "tick_spread_mean", "xau_tick_count"])
    f["t"] = pd.to_datetime(f.timestamp_ms, unit="ms", utc=True)
    f = f.sort_values("t").reset_index(drop=True)
    mc = f.mid_close.values
    prev = np.r_[mc[0], mc[:-1]]
    tr = np.maximum.reduce([f.mid_high.values - f.mid_low.values,
                            np.abs(f.mid_high.values - prev),
                            np.abs(f.mid_low.values - prev)])
    f["atr144"] = pd.Series(tr).rolling(144, min_periods=50).mean().values
    f["ema144"] = pd.Series(mc).ewm(span=144, adjust=False).mean().values
    return f


def market_features(led, mkt):
    """Values at the last COMPLETED bar at or before each entry."""
    t = mkt.t.values.astype("datetime64[ns]")
    idx = np.searchsorted(t, led.entry_time.values.astype("datetime64[ns]"),
                          side="right") - 1
    ok = idx >= 2016
    idx = np.clip(idx, 0, len(mkt) - 1)

    mc = mkt.mid_close.values
    mh, ml = mkt.mid_high.values, mkt.mid_low.values
    atr = mkt.atr144.values
    ema = mkt.ema144.values
    csm = np.concatenate([[0.0], np.nancumsum(np.nan_to_num(mkt.tick_signed_move.values))])
    cbi = np.concatenate([[0.0], np.nancumsum(np.nan_to_num(mkt.tick_book_imbalance_mean.values))])
    cpe = np.concatenate([[0.0], np.nancumsum(np.nan_to_num(mkt.price_efficiency_5m.values))])
    cts = np.concatenate([[0.0], np.nancumsum(np.nan_to_num(mkt.tick_spread_mean.values))])
    ctc = np.concatenate([[0.0], np.nancumsum(np.nan_to_num(mkt.xau_tick_count.values))])

    atr_med = pd.Series(atr).rolling(2016, min_periods=500).median().shift(1).values
    a = atr[idx]
    a_safe = np.where(a > 0, a, np.nan)

    def ret(bars):
        j = np.maximum(idx - bars, 0)
        return (mc[idx] - mc[j]) / a_safe

    def rv(bars):
        j = np.maximum(idx - bars, 0)
        out = np.empty(len(idx))
        for k in range(len(idx)):
            seg = mc[j[k]:idx[k] + 1]
            out[k] = np.std(np.diff(seg)) / a_safe[k] if len(seg) > 2 else np.nan
        return out

    W = 12                                        # 1h microstructure window
    lo = np.maximum(idx - W, 0)
    nb = np.maximum(idx - lo, 1)
    sgn = led.direction_sign.values

    out = pd.DataFrame(index=led.index)
    out["atr_ratio"] = a / np.where(atr_med[idx] > 0, atr_med[idx], np.nan)
    out["rv_1h"] = rv(12)
    out["rv_24h"] = rv(288)
    out["slope_atr"] = (ema[idx] - ema[np.maximum(idx - 288, 0)]) / a_safe
    out["ret_1h"] = ret(12)
    out["ret_4h"] = ret(48)
    out["ret_24h"] = ret(288)
    hi = pd.Series(mh).rolling(288, min_periods=20).max().values[idx]
    lw = pd.Series(ml).rolling(288, min_periods=20).min().values[idx]
    out["dist_hi_24h"] = (hi - mc[idx]) / a_safe
    out["dist_lo_24h"] = (mc[idx] - lw) / a_safe
    out["hour"] = led.entry_time.dt.hour.values
    out["dow"] = led.entry_time.dt.dayofweek.values
    # microstructure signed by the trade's own direction
    out["ms_flow"] = sgn * (csm[idx + 1] - csm[lo]) / nb
    out["ms_imb"] = sgn * (cbi[idx + 1] - cbi[lo]) / nb
    out["ms_eff"] = (cpe[idx + 1] - cpe[lo]) / nb
    out["ms_spread_per_risk"] = ((cts[idx + 1] - cts[lo]) / nb) / a_safe
    out["ms_activity"] = (ctc[idx + 1] - ctc[lo]) / nb
    out["_bar_ok"] = ok
    return out


def portfolio_features(led):
    """State of the book at each entry, from trades that have already closed.

    Walks entries in time order, settling prior positions from a min-heap. A
    trade can only see positions opened before it and outcomes realised before
    it — never its own result, never a later one.
    """
    n = len(led)
    cols = {c: np.zeros(n) for c in PORTFOLIO}
    open_heap: list = []                 # (exit_time, risk, sleeve)
    closed_pnl: list = []                # realised, in close order
    equity = 0.0
    peak = 0.0
    last_loss_t = None
    day_count: dict = {}

    et = led.entry_time.values
    xt = led.exit_time.values
    risk = led.risk_usd.values
    pnl = led[PNL].values
    sleeve = led.source_id.values

    for k in range(n):
        now = et[k]
        while open_heap and open_heap[0][0] <= now:
            _, _, _, p = heapq.heappop(open_heap)
            equity += p
            closed_pnl.append(p)
            peak = max(peak, equity)
            if p <= 0:
                last_loss_t = now
        cols["open_positions"][k] = len(open_heap)
        # nansum: the R1 sleeve reports no risk, and a missing risk must
        # contribute zero rather than poison the whole aggregate
        cols["open_risk_usd"][k] = float(np.nansum([h[1] for h in open_heap])) if open_heap else 0.0
        cols["pnl_last5"][k] = sum(closed_pnl[-5:]) if closed_pnl else 0.0
        cols["pnl_last20"][k] = sum(closed_pnl[-20:]) if closed_pnl else 0.0
        cols["dd_from_peak"][k] = peak - equity
        cols["hours_since_loss"][k] = (
            (now - last_loss_t) / np.timedelta64(1, "h") if last_loss_t is not None else 999.0)
        day = str(now)[:10]
        cols["trades_today"][k] = day_count.get(day, 0)
        day_count[day] = day_count.get(day, 0) + 1
        heapq.heappush(open_heap, (xt[k], float(risk[k]), sleeve[k], float(pnl[k])))
    return pd.DataFrame(cols, index=led.index)


def assert_causal(X):
    """Nothing derived from a trade's own outcome may reach the model."""
    bad = [c for c in X.columns if c in FORBIDDEN]
    if bad:
        raise ValueError(f"outcome-derived features leaked into X: {bad}")
    return True


def build():
    led = load_ledger()
    mkt = load_market()
    M = market_features(led, mkt)
    P = portfolio_features(led)
    X = pd.concat([M.drop(columns=["_bar_ok"]), P], axis=1)
    X["is_long"] = (led.direction_sign.values > 0).astype(float)
    X["is_core"] = led.is_core.values.astype(float)
    assert_causal(X)
    meta = led[["entry_time", "exit_time", "source_id", "specialist_id",
                "is_core", PNL, "risk_usd"]].copy()
    meta["bar_ok"] = M["_bar_ok"].values
    return X.replace([np.inf, -np.inf], np.nan), meta


if __name__ == "__main__":
    X, meta = build()
    keep = meta.bar_ok.values & X.notna().all(axis=1).values
    print(f"trades {len(X):,}   usable {keep.sum():,} ({100*keep.mean():.1f}%)")
    print(f"span {meta.entry_time.min():%Y-%m-%d} -> {meta.entry_time.max():%Y-%m-%d}")
    print(f"features {len(X.columns)}: market {len(MARKET)}, "
          f"portfolio {len(PORTFOLIO)}, trade {len(TRADE)}")
    X[keep].to_parquet("outputs/V60_ML_FEATURES.parquet")
    meta[keep].to_parquet("outputs/V60_ML_META.parquet")
    print("\nportfolio-state block, describe():")
    print(X.loc[keep, PORTFOLIO].describe().T[["mean", "std", "min", "max"]].round(3).to_string())
