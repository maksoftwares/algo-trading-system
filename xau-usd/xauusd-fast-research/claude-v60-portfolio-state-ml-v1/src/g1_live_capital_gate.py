"""Would V60's own historical record survive the risk limits it is deployed under?

The backtest was built for a $2,998 account. The live demo account holds $999.47
with an activation equity of $987.66. The config carries both absolute and
fractional drawdown limits and applies WHICHEVER IS LOWER, so on this balance the
fractions bind:

    suspend             $225.00  ->  $74.07   (7.5%)
    resume              $180.00  ->  $59.26   (6.0%)
    combined hard stop  $300.00  ->  $98.77   (10.0%)
    floating hard stop  $449.77  -> $148.15   (15.0%)

The scored-set backtest had a maximum drawdown of $298 - three times the
permanent hard stop. This replays the actual ledger through the live state
machine to find out what that means in practice: when the account would first
suspend, when it would first hard-stop, and how much of the historical profit is
still reachable before it does.

Closed drawdown is measured from the running peak of REALISED equity, which is
what the executor tracks in `refresh_drawdown_state`. Suspension blocks new
entries and lifts only after recovery to the resume line; the combined hard stop
does not recover.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import features as F

PNL = F.PNL
ACTIVATION_EQUITY = 987.6623553437713
LIMITS = {
    "suspend": 0.075, "resume": 0.060,
    "combined_hard_stop": 0.100, "floating_hard_stop": 0.150,
}


def replay(pnl, entry_t, exit_t, suspend, resume, hard_stop):
    """Walk the real event stream through the live risk state machine.

    Suspension blocks new ENTRIES only - positions already open keep running to
    their exits, and their realised P&L still moves equity. That distinction
    decides whether a suspended account can ever recover, so entries and exits
    are processed as separate time-ordered events rather than by exit order.
    """
    n = len(pnl)
    events = [(entry_t[i], 0, i) for i in range(n)] + [(exit_t[i], 1, i) for i in range(n)]
    events.sort(key=lambda e: (e[0], e[1]))       # exits settle before same-instant entries
    equity = peak = 0.0
    suspended = False
    stopped_at = first_suspend = None
    taken: set[int] = set()
    path, skipped = [], 0
    for t, kind, i in events:
        if kind == 0:                              # entry decision
            if stopped_at is not None or suspended:
                skipped += 1
                continue
            taken.add(i)
        else:                                      # exit settles
            if i not in taken:
                continue
            equity += pnl[i]
            peak = max(peak, equity)
            path.append((t, pnl[i], equity))
            dd = peak - equity
            if stopped_at is None and dd >= hard_stop:
                stopped_at = (t, equity, dd)
            elif not suspended and dd >= suspend:
                suspended = True
                if first_suspend is None:
                    first_suspend = (t, equity, dd)
            elif suspended and dd <= resume:
                suspended = False
    return path, first_suspend, stopped_at, skipped, len(taken)


def main():
    led = F.load_ledger()
    led = led[led.entry_time >= "2021-01-01"].copy()
    pnl, xt = led[PNL].values, led.exit_time.values

    o = np.argsort(xt)
    eq = np.cumsum(pnl[o])
    raw_dd = np.maximum.accumulate(eq) - eq
    print(f"V60 ledger 2021+: {len(led):,} trades, net ${eq[-1]:.0f}, "
          f"maxDD ${raw_dd.max():.0f}\n")

    print(f"live activation equity ${ACTIVATION_EQUITY:.2f}")
    print(f"{'limit':<22}{'config $':>11}{'fraction':>10}{'effective $':>13}  binding")
    cfg = {"suspend": 225.0, "resume": 180.0,
           "combined_hard_stop": 300.0, "floating_hard_stop": 449.7675}
    eff = {}
    for k, frac in LIMITS.items():
        e = min(cfg[k], ACTIVATION_EQUITY * frac)
        eff[k] = e
        print(f"{k:<22}{cfg[k]:>11.2f}{100*frac:>9.1f}%{e:>13.2f}"
              f"  {'FRACTION' if e < cfg[k] else 'absolute'}")

    print(f"\nhistorical maxDD ${raw_dd.max():.0f} vs combined hard stop "
          f"${eff['combined_hard_stop']:.2f}  ->  "
          f"{raw_dd.max()/eff['combined_hard_stop']:.1f}x the permanent stop\n")

    # how often does the raw equity curve breach each level?
    print("breaches of each level on the UNCONSTRAINED historical curve")
    for k in ("suspend", "combined_hard_stop", "floating_hard_stop"):
        hit = raw_dd >= eff[k]
        if hit.any():
            first = pd.Timestamp(xt[o][np.argmax(hit)])
            print(f"  {k:<22} first breached {first:%Y-%m-%d}  "
                  f"({int(hit.sum())} of {len(hit)} trade-points above it)")
        else:
            print(f"  {k:<22} never breached")

    print("\n" + "=" * 74)
    print("REPLAY through the live state machine")
    print("=" * 74)
    path, first_susp, stopped, skipped, n_taken = replay(
        pnl, led.entry_time.values, xt,
        eff["suspend"], eff["resume"], eff["combined_hard_stop"])
    final = path[-1][2] if path else 0.0
    print(f"  trades actually taken : {n_taken:,} of {len(led):,}")
    print(f"  entries blocked       : {skipped:,}")
    if first_susp:
        print(f"  first SUSPEND         : {pd.Timestamp(first_susp[0]):%Y-%m-%d}  "
              f"equity ${first_susp[1]:.0f}, drawdown ${first_susp[2]:.0f}")
    if stopped:
        print(f"  PERMANENT HARD STOP   : {pd.Timestamp(stopped[0]):%Y-%m-%d}  "
              f"equity ${stopped[1]:.0f}, drawdown ${stopped[2]:.0f}")
        days = (pd.Timestamp(stopped[0]) - pd.Timestamp(xt[o][0])).days
        print(f"  survived              : {days} days "
              f"({days/365.25:.1f} years) of a {len(led):,}-trade record")
        print(f"  profit captured       : ${final:.0f} of ${eq[-1]:.0f} "
              f"({100*final/eq[-1]:.0f}%)")
    else:
        print(f"  never hard-stopped. final equity ${final:.0f}")

    # what balance would be needed for the historical record to survive?
    need = raw_dd.max() / LIMITS["combined_hard_stop"]
    need_fl = raw_dd.max() / LIMITS["floating_hard_stop"]
    print(f"\n  balance needed so maxDD ${raw_dd.max():.0f} stays under the")
    print(f"    10% combined hard stop : ${need:,.0f}")
    print(f"    15% floating hard stop : ${need_fl:,.0f}")
    print(f"  current balance          : $999")

    print("\n  drawdown percentiles on the historical curve (what a $988 account")
    print("  has to absorb):")
    for q in (50, 75, 90, 95, 99, 100):
        v = np.percentile(raw_dd, q)
        print(f"    p{q:<4} ${v:>7.2f}   = {100*v/ACTIVATION_EQUITY:>5.1f}% of activation equity")


if __name__ == "__main__":
    main()
