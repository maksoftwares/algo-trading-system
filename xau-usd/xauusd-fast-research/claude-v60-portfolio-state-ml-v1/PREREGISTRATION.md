# Claude V60 Portfolio-State ML V1 — Preregistration

**Written 2026-07-28 BEFORE any model was trained or any result observed.**

## Question

Can a model reduce V60's loss tail using information the nine sleeves cannot see —
the state of the portfolio itself and the market microstructure at entry — without
removing the winners that carry the book?

## Why the previous attempts failed, and what changes here

Four prior ML lanes on the V6 mechanism failed, and my own four on XAUUSD failed.
The failure was always the same shape and it is worth stating precisely:

> A binary veto on a positive-expectancy population removes trades. Profit factor
> rises because the ratio improves; net P&L falls because expectancy was positive.
> `v6-causal-ml-veto-v1`: PF 1.177 -> 1.221, net $303.59 -> $293.99. My own
> replication: PF up at every cutoff, dollars down at every cutoff.

Three deliberate departures:

1. **Target the loss TAIL, not the binary outcome.** V60's losses are
   concentrated: the worst 10% of losing trades carry 31% of all losses ($2,611
   of $8,406), median loss $4.77 against a worst of $122.78. Large losses plausibly
   have structural causes — volatility expansion, spread blowout, adverse regime —
   whereas win/loss on a 44.7% base rate is close to noise (prior lanes measured
   AUC 0.52-0.54).
2. **Use PORTFOLIO STATE as a feature.** Each of the nine sleeves decides
   independently; none knows what the others hold, how many positions are open, or
   whether the account is in drawdown. That is genuinely orthogonal information and
   it has never been tested here.
3. **Prefer risk reduction to removal.** A veto is one option among several; the
   lane also tests size reduction, which keeps expectancy while cutting exposure.

## Population and split

- Ledger: `ONE_TRADE_PER_DAY_FLOATING_EQUITY_V60_PRICE_LEDGER.parquet`, 2,194
  fee-stressed trades, 2010-01 to 2026-06.
- 96.2% (2,110) fall on or after 2016-07-01 where the Dukascopy M5 feed exists.
  Trades before that are **excluded from training and from every reported metric**,
  and the exclusion is declared here rather than discovered later.
- Walk-forward by entry year, 2019 through 2026. For target year Y the model sees
  only trades whose **exit** is before Y-01-01, with a 48-hour purge.
- P&L is always `fee_stress_pnl_usd`. PF, net and drawdown all come from that one
  column.

## Features

Market state at entry, from completed M5 bars only: ATR and ATR ratio, realised
volatility, EMA slope, returns over 1h/4h/24h in ATR units, distance from recent
extremes, session hour, and microstructure over the trailing window (signed tick
move, book imbalance, price efficiency, spread per unit risk, tick activity).

Portfolio state at entry, from closed trades and open positions only: number of
positions currently open, concurrent open risk, count of the same sleeve open,
realised P&L over the trailing 5 and 20 closed trades, current drawdown from the
running equity peak, and time since the last loss.

Trade descriptors: direction, risk_usd, sleeve identity, core/add-on flag.

**Forbidden as inputs:** exit time, exit price, realised P&L, duration, or any
quantity derived from the trade's own outcome.

## Targets tested (all three, reported together)

- `T1` binary win/loss — the target prior lanes used, included as the control.
- `T2` **large loss**: the trade lands in the worst decile of the training window's
  P&L distribution. This is the lane's primary hypothesis.
- `T3` P&L regression, for a size-scaling policy.

## Pass conditions

Measured on the walk-forward, versus V60 unchanged over the same trades:

1. **net P&L must not fall**, and
2. **net/maxDD must improve**, and
3. green-month share must not fall by more than 2 percentage points, and
4. the effect must hold in at least 5 of the 8 walk-forward years.

A result that raises profit factor while lowering net P&L is a **FAIL**. That is
the specific illusion this lane exists to avoid.

## Benchmarks the model must beat

| variant | net | maxDD | net/DD |
|---|---|---|---|
| V60 as deployed | $5,458.39 | $298.06 | 18.31 |
| drop V8 + V25 (dead sleeves) | $5,408.19 | $279.16 | **19.37** |
| core sleeves only | $3,951.06 | $272.81 | 14.48 |

**19.37 is the bar**, not 18.31 — a trivial rule already achieves it, so the model
must beat the trivial rule.

## Governance

`ml_runtime_authorized: false` and `ml_shadow_authorized: false` in the V60 config.
This lane is historical research and authorizes no runtime, EA, demo, live or
broker change. No parameter may be altered after observing the walk-forward.
Failure quarantines the lane.
