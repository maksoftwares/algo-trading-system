"""What actually makes a V8 month red? Forensic on the losing months.

V8 is green 40/60 months over five years. The question is whether the 20 red
months share a fixable defect, or whether they are simply the months in which no
large winner happened to land - because this edge is tail-carried (top 5% of
trades = 45% of gross profit, largest single trade 27.3R).

Those two possibilities need opposite responses:
  DEFECT      red months trade systematically worse - a condition exists, find it
  TAIL TIMING red months trade the same and just miss the tail - no entry rule
              fixes it, and chasing it is how you overfit

Tested here: win rate, loss profile, direction mix, sleeve mix, and the decisive
one - what each month looks like once its single best trade is removed.
"""
import numpy as np, pandas as pd

TRADES = "outputs/GOLD_V8_FINAL_TRADES.csv"
FIT_END = pd.Period("2024-12")


def main():
    t = pd.read_csv(TRADES, parse_dates=["dec_t", "entry_t", "exit_t"])
    t["m"] = t.exit_t.dt.to_period("M")
    t["sr"] = t.r * t["size"]
    M = pd.period_range("2021-07", "2026-06", freq="M")
    t = t[t.m.isin(M)]

    rows = []
    for m, g in t.groupby("m"):
        r = g.sr.values
        w, l = r[r > 0], r[r <= 0]
        top = np.sort(w)[::-1] if len(w) else np.array([0.0])
        rows.append(dict(
            m=m, n=len(g), usd=g.usd.sum(),
            wr=100 * len(w) / max(len(r), 1),
            gross_win=w.sum(), gross_loss=-l.sum(),
            best=top[0] if len(top) else 0.0,
            top3=top[:3].sum(),
            worst=r.min(),
            n_big=(r >= 3).sum(),                 # trades of 3R or more
            long_n=int(g.long.sum()), short_n=int((~g.long).sum()),
            long_usd=g[g.long].usd.sum(), short_usd=g[~g.long].usd.sum()))
    M_ = pd.DataFrame(rows).set_index("m")
    M_["green"] = M_.usd > 0

    g_, r_ = M_[M_.green], M_[~M_.green]
    print(f"=== GREEN ({len(g_)}) vs RED ({len(r_)}) MONTHS, five years ===")
    print(f"{'metric':<28}{'GREEN':>10}{'RED':>10}   read")
    def cmp(lab, col, fmt="{:.1f}", note=""):
        print(f"{lab:<28}{fmt.format(g_[col].mean()):>10}"
              f"{fmt.format(r_[col].mean()):>10}   {note}")
    cmp("trades per month", "n")
    cmp("win rate %", "wr")
    cmp("gross win (R)", "gross_win")
    cmp("gross loss (R)", "gross_loss")
    cmp("biggest winner (R)", "best")
    cmp("top-3 winners (R)", "top3")
    cmp("worst single trade (R)", "worst")
    cmp("trades >= 3R", "n_big", "{:.2f}")
    cmp("long trades", "long_n")
    cmp("short trades", "short_n")

    print("\n=== THE DECISIVE TEST: remove each month's single best trade ===")
    kept = []
    for m, g in t.groupby("m"):
        if m not in M_.index:
            continue
        gg = g.sort_values("usd", ascending=False)
        kept.append(dict(m=m, full=g.usd.sum(), minus1=gg.usd.iloc[1:].sum(),
                         minus3=gg.usd.iloc[3:].sum()))
    K = pd.DataFrame(kept).set_index("m")
    print(f"  green months, as reported          : {int((K.full>0).sum())}/{len(K)}")
    print(f"  green after removing 1 best trade  : {int((K.minus1>0).sum())}/{len(K)}")
    print(f"  green after removing 3 best trades : {int((K.minus3>0).sum())}/{len(K)}")
    flip = K[(K.full > 0) & (K.minus1 <= 0)]
    print(f"  -> {len(flip)} of {int((K.full>0).sum())} green months "
          f"({100*len(flip)/max(int((K.full>0).sum()),1):.0f}%) depend on ONE trade")

    print("\n=== ARE RED MONTHS JUST MISSING THE TAIL? ===")
    print(f"  months with at least one >=3R trade : "
          f"{int((M_.n_big>0).sum())}/{len(M_)}, of which green "
          f"{int(M_[M_.n_big>0].green.sum())} "
          f"({100*M_[M_.n_big>0].green.mean():.0f}%)")
    print(f"  months with NO >=3R trade           : "
          f"{int((M_.n_big==0).sum())}/{len(M_)}, of which green "
          f"{int(M_[M_.n_big==0].green.sum())} "
          f"({100*M_[M_.n_big==0].green.mean():.0f}%)")

    print("\n=== DIRECTION: does one side bleed? ===")
    print(f"  all months  long ${M_.long_usd.sum():.0f}   short ${M_.short_usd.sum():.0f}")
    print(f"  red months  long ${r_.long_usd.sum():.0f}   short ${r_.short_usd.sum():.0f}")
    lt, st = t[t.long], t[~t.long]
    for lab, x in (("LONG", lt), ("SHORT", st)):
        r = x.sr.values; w, l = r[r > 0], r[r <= 0]
        print(f"  {lab:<6} n={len(x):>5}  WR {100*len(w)/len(r):>5.1f}%  "
              f"PF {w.sum()/max(-l.sum(),1e-9):>5.2f}  ${x.usd.sum():>7.0f}")

    print("\n=== SLEEVE CONTRIBUTION (all 60 months) ===")
    s = t.groupby("sleeve").agg(
        n=("r", "size"), wr=("sr", lambda x: round(100 * (x > 0).mean(), 1)),
        pf=("sr", lambda x: round(x[x > 0].sum() / max(-x[x <= 0].sum(), 1e-9), 2)),
        usd=("usd", lambda x: round(x.sum()))).sort_values("usd")
    print(s.to_string())

    print("\n=== THE 8 WORST MONTHS ===")
    print(f"{'month':<9}{'n':>5}{'WR':>7}{'best':>8}{'worst':>8}{'>=3R':>6}"
          f"{'longUSD':>9}{'shortUSD':>10}{'USD':>8}")
    for m, x in M_.nsmallest(8, "usd").iterrows():
        print(f"{str(m):<9}{int(x.n):>5}{x.wr:>6.1f}%{x.best:>8.1f}{x.worst:>8.1f}"
              f"{int(x.n_big):>6}{x.long_usd:>9.0f}{x.short_usd:>10.0f}{x.usd:>8.0f}")


if __name__ == "__main__":
    main()
