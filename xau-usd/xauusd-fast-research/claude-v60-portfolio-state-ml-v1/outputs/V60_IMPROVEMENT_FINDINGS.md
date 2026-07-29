# Ways to make the deployed V60 better — findings, ranked

Historical research only. `ml_runtime_authorized: false`. This document
recommends; it changes no runtime, config, EA, terminal or account setting.

Everything below comes from the live config and status of
`v60-canonical-demo-portfolio-v2` (demo `1033030`) replayed against the V60
price ledger, 2021-2026, 1,713 trades.

---

## FINDING 1 — The account is capital-starved by 3x, and will freeze (CRITICAL)

This dominates every other improvement on the list. Nothing else matters until
it is resolved.

The config carries drawdown limits as both absolute dollars and fractions of
activation equity, and applies **whichever is lower**. Live activation equity is
**$987.66**, not the $2,998 the strategy was designed around, so the fractions
bind:

| limit | config absolute | effective on $988 | binding |
|---|---|---|---|
| suspend | $225.00 | **$74.07** | fraction (7.5%) |
| resume | $180.00 | $59.26 | fraction (6.0%) |
| combined hard stop | $300.00 | **$98.77** | fraction (10%) |
| floating hard stop | $449.77 | **$148.15** | fraction (15%) |

V60's historical maximum drawdown is **$298** — **3.0x the permanent hard stop.**
Its drawdown distribution does not fit inside these limits at all:

| percentile | drawdown | as % of $988 activation equity |
|---|---|---|
| p50 | $30.43 | 3.1% |
| p75 | $75.86 | 7.7% — already past suspend |
| p90 | $175.02 | **17.7% — past the floating hard stop** |
| p95 | $202.70 | 20.5% |
| p100 | $298.06 | 30.2% |

The suspend line is breached at 437 of 1,713 trade-points; the combined hard stop
at 302. This is not a tail risk — it is the normal operating range of the
strategy.

### Replayed through the live state machine

Processing entries and exits as separate time-ordered events (suspension blocks
new **entries**; positions already open still run to their exits):

```
trades actually taken : 130 of 1,713
entries blocked       : 1,583
first SUSPEND         : 2021-05-21   equity $181, drawdown $74
final equity          : $175 of a possible $5,082  (3.4%)
```

**It takes 130 trades, suspends after five months, and never trades again.**

### Why it never resumes — a genuine deadlock

```
last exit 2021-05-23   equity $175.03   peak $255.00   drawdown $79.97
resume line $59.26  ->  needs $20.71 more profit to lift the suspension
suspended: true     open positions: 0
```

Resumption requires the drawdown to fall to $59.26. Drawdown falls only when
equity rises. Equity rises only by trading. Trading is what is suspended. With no
open positions left to close, **equity is frozen and the account can never
resume** without manual intervention or a deposit.

An account that suspends while flat is permanently stuck. That is a design flaw
independent of the capital level, and it will recur at any balance.

### What can actually be done

Note that the obvious fix — trade smaller — **is not available**. The fixed lot
is `0.01` and that is the broker minimum (`expected_ounces_at_fixed_lot: 1.0`).
V60 cannot be scaled down to fit a $999 account. The options are:

1. **Fund the demo to ~$3,000.** Restores the design point; the absolute limits
   become binding as intended. $2,981 clears the 10% combined stop against the
   historical maxDD; $1,987 clears the 15% floating stop.
2. **Raise the fractional limits** to match the strategy's real drawdown profile
   (p95 is 20.5% of equity, so a 15% floating stop cannot hold). This accepts
   more risk rather than reducing it, and should be a deliberate decision.
3. **Reduce the number of concurrently active sleeves** so aggregate drawdown
   scales down even though per-trade size cannot.

**Separately, fix the resume rule** so a flat suspended account can recover —
time-based resumption, recomputing peak after a cooling period, or permitting
reduced-frequency probe entries. Without this, option 1 only delays the freeze.

---

## FINDING 2 — Dead sleeves are consuming the shared add-on quota

All four add-on sleeves share **one budget of 2 entries per UTC day**
(`maximum_addon_entries_per_utc_day: 2`) and **2 concurrent positions**. Their
economics are not close:

| sleeve | trades | net | PF | **$/trade** |
|---|---|---|---|---|
| V7_SWING_HEALTH | 381 | $653.03 | 1.61 | **$1.71** |
| V57_BREAK_SWING | 520 | $779.05 | 1.36 | **$1.50** |
| V25_CHOP | 55 | $53.94 | 1.26 | $0.98 |
| V8_RETEST_HEALTH | 152 | $28.77 | **1.07** | **$0.19** |

V8 earns 19 cents a trade at a profit factor of 1.07 — indistinguishable from
noise — yet competes for the same two daily slots as V7, which earns nine times
more per trade.

The quota binds: add-ons hit exactly 2 entries on **426 of 682 active days
(62%)**. And the live log already shows the collision, in only eight days of
operation:

```
V7_SWING_HEALTH   MAXIMUM_ADDON_DAILY_ENTRIES   1
```

A good sleeve was turned away because the daily add-on budget was already spent.

**Proposal:** remove V8 (and probably V25) from the executor's add-on source
list, so the 2/day budget flows to V7 and V57. This differs from the "drop the
dead sleeves" benchmark computed earlier, which only deleted their P&L and
assumed nothing else changed. Here the gain is *reallocation*, which that
benchmark could not capture. **Needs testing before adoption** — it requires
reconstructing which V7/V57 candidates were suppressed on days V8/V25 consumed
the quota.

---

## FINDING 3 — R2_DOWNTREND is the best sleeve per trade and is starved

| sleeve | trades (5.5 yrs) | $/trade | PF |
|---|---|---|---|
| **R2_DOWNTREND** | **35** | **$15.10** | **3.37** |
| R1_NATIVE_POSITION | 444 | $6.12 | 2.03 |
| R3_COMPRESSION | 46 | $3.63 | 1.83 |

R2 earns 2.5x more per trade than R1 at a materially higher profit factor, on
**six trades a year**. Its configured limits are not the constraint (4 open,
4/day) — the signal itself is rare.

If R2's entry condition can be relaxed without degrading its edge, it is worth
more than any overlay tested in this repository. That is a strategy-research
question, not an ML one, and it has not been attempted. It is the single most
promising untried direction.

Caution: 35 trades is a small sample, and PF 3.37 on 35 trades has wide error
bars. Establish whether the edge is real before investing in widening it.

---

## FINDING 4 — The validated sizing signal is now executable, but points the wrong way

Earlier work established a genuine ranking signal on V60 trades (pooled
permutation z 4.21, p < 0.0001) delivering +17.6% net and net/DD 17.05 -> 19.29.
It was thought unexecutable because it sized between 0.5x and 1.5x and 0.01 lots
is the floor.

It *is* executable in one direction: **1x / 2x**, leaving most trades at 0.01 and
doubling only the top-ranked ones. That is a discrete, implementable decision.

**But it should not be deployed now.** Upsizing raises drawdown, and Finding 1
shows drawdown is precisely what this account cannot absorb — the last 12 months
already showed maxDD rising $153 -> $229 under the sizing overlay. Adding it
today accelerates the freeze.

Sequence matters: fix capital, fix the resume deadlock, then revisit this.

---

## Recommended order

1. **Resolve the capital gate** — fund to ~$3,000, or consciously widen the
   fractional limits. Until then the demo cannot produce meaningful forward
   evidence, because it will spend most of its life suspended.
2. **Fix the resume deadlock** — a flat suspended account must have a path back.
3. **Reallocate the add-on quota** away from V8/V25 (test first).
4. **Investigate R2_DOWNTREND frequency** — highest ceiling, entirely untried.
5. **Revisit the 1x/2x sizing overlay** once 1 and 2 are done.

## Reproduce

```
PYTHONPATH=src ../balanced-horizon-ml-v5/.venv/Scripts/python.exe src/g1_live_capital_gate.py
```
