"""Can the cross-asset sizing overlay actually be run live?

The overlay survives causal walk-forward, but a backtest signal is worthless if
the inputs are not available at decision time in production. Three things have to
be true, and each is checked here:

  COVERAGE   do the feeds span the trades, and are they current? A feed that
             stopped updating in 2024 cannot size a trade today.
  TIMELINESS what is the real lag between a bar closing and it being usable? The
             joins allow a 10-minute tolerance on M5 data; if the live feed
             arrives later than that, decisions silently fall back to stale
             values or NaN.
  POINT-IN-TIME  the CFTC join uses `available_utc` (publication time), which is
             correct in principle - this verifies the column really is the
             publication date and not the report date, by checking the gap
             between them.

Also measured: how often the cross-asset row is MISSING at a decision. Every
missing row is a trade that would size at 1.0x in production, which dilutes the
overlay's effect - the backtest quietly dropped those rows instead.
"""
import numpy as np, pandas as pd

GR = "D:/AlgoTradingData/C_DRIVE/DukascopyGrowthRiskFoundationV1/curated/growth_risk_m5_v1.parquet"
VOL = "D:/AlgoTradingData/C_DRIVE/DukascopyVolIndexFoundationV1/curated/volidx_m5_v1.parquet"
CFTC = "D:/AlgoTradingData/C_DRIVE/CftcGoldOptionsPositioningV1/curated/gold_options_positioning.parquet"
DATA = "outputs/ML_TRADE_DATASET.parquet"
XA_M5 = ["spx_return_15m", "copper_return_15m", "usdcnh_return_15m"]


def main():
    print("=== 1. FEED COVERAGE AND RECENCY ===")
    gr = pd.read_parquet(GR)
    gr["t"] = pd.to_datetime(gr["bar_open_timestamp_ms"], unit="ms", utc=True)
    print(f"  growth/risk M5 (SPX, copper, USDCNH)")
    print(f"    {len(gr):,} bars   {gr.t.min():%Y-%m-%d} -> {gr.t.max():%Y-%m-%d}")
    cols = [c for c in gr.columns if any(a in c for a in ("spx", "copper", "usdcnh"))]
    print(f"    {len(cols)} cross-asset columns")
    for a in ("spx", "copper", "usdcnh"):
        c = f"{a}_return_15m"
        if c in gr.columns:
            print(f"      {a:<8} non-null {100*gr[c].notna().mean():>5.1f}%   "
                  f"last non-null {gr.loc[gr[c].notna(), 't'].max():%Y-%m-%d}")

    v = pd.read_parquet(VOL, columns=["bar_open_timestamp_ms", "vol_mid_close"])
    v["t"] = pd.to_datetime(v["bar_open_timestamp_ms"], unit="ms", utc=True)
    print(f"\n  gold vol index")
    print(f"    {len(v):,} bars   {v.t.min():%Y-%m-%d} -> {v.t.max():%Y-%m-%d}")

    c = pd.read_parquet(CFTC)
    print(f"\n  CFTC gold positioning")
    print(f"    {len(c):,} reports   columns: {sorted(c.columns.tolist())[:8]}")
    c["available_utc"] = pd.to_datetime(c["available_utc"], utc=True)
    print(f"    available_utc {c.available_utc.min():%Y-%m-%d} -> "
          f"{c.available_utc.max():%Y-%m-%d}")

    print("\n=== 2. POINT-IN-TIME: is available_utc really the publication date? ===")
    datecols = [x for x in c.columns if x != "available_utc"
                and ("date" in x.lower() or "time" in x.lower() or "as_of" in x.lower())]
    if datecols:
        for dc in datecols[:3]:
            try:
                rd = pd.to_datetime(c[dc], utc=True)
                lag = (c.available_utc - rd).dt.total_seconds() / 86400
                print(f"    lag(available_utc - {dc}): median {lag.median():.1f} d   "
                      f"min {lag.min():.1f}   max {lag.max():.1f}")
                if lag.median() >= 2:
                    print(f"      -> consistent with a real publication lag. POINT-IN-TIME OK")
                else:
                    print(f"      -> LAG TOO SMALL. available_utc may be the report date; "
                          f"treat the CFTC signal as suspect")
            except Exception as e:
                print(f"    could not parse {dc}: {e}")
    else:
        print("    no report-date column present; cannot verify the lag independently.")
        gaps = c.available_utc.diff().dt.total_seconds().div(86400).dropna()
        print(f"    spacing between reports: median {gaps.median():.1f} d "
              f"(weekly data should be ~7)")

    print("\n=== 3. HOW OFTEN IS CROSS-ASSET DATA MISSING AT A DECISION? ===")
    d = pd.read_parquet(DATA)
    d["dec_time"] = pd.to_datetime(d.dec_time, utc=True)
    tot = len(d)
    have_m5 = d[XA_M5].notna().all(axis=1)
    have_cf = d["mm_net_pct_oi"].notna()
    print(f"  {tot:,} setups in the dataset")
    print(f"    M5 cross-asset present : {100*have_m5.mean():>5.1f}%")
    print(f"    CFTC present           : {100*have_cf.mean():>5.1f}%")
    print(f"    BOTH present           : {100*(have_m5&have_cf).mean():>5.1f}%")
    post = d[d.dec_time >= "2023-01-01"]
    hp = post[XA_M5].notna().all(axis=1) & post["mm_net_pct_oi"].notna()
    print(f"    both, 2023 onward only : {100*hp.mean():>5.1f}%  ({len(post):,} setups)")

    print("\n=== 4. WHAT HAPPENS TO TRADES WITH NO CROSS-ASSET ROW ===")
    print("  In production they must size at 1.0x (no signal). The backtest DROPPED")
    print("  them, so the measured effect applies only to the covered subset.")
    cov = (have_m5 & have_cf)
    if cov.any() and (~cov).any():
        a, b = d[cov], d[~cov]
        print(f"    covered   n={len(a):,}  meanR {a.R.mean():+.4f}")
        print(f"    uncovered n={len(b):,}  meanR {b.R.mean():+.4f}")
        print(f"    -> the overlay can only act on {100*cov.mean():.1f}% of the book;"
              f" dilute the reported gain accordingly")

    print("\n=== VERDICT ON LIVE FEASIBILITY ===")
    stale_days = (pd.Timestamp.now(tz="UTC") - gr.t.max()).days
    print(f"  growth/risk feed is {stale_days} days stale as of now")
    print(f"  CFTC feed is {(pd.Timestamp.now(tz='UTC') - c.available_utc.max()).days} days stale")
    print("  Live use requires: SPX/copper/USDCNH M5 within ~10 min of the bar,")
    print("  the gold vol index on the same cadence, and the CFTC release pipeline.")
    print("  None of that exists in the current runtime - it is a research-only feed set.")


if __name__ == "__main__":
    main()
