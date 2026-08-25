# V60 Monthly Quality Risk Overlay V15 Preregistration

## Objective

Test one monotonic, less-aggressive repair to rejected V14 while preserving its
improvement in net P/L, drawdown, and losing-month severity.

## Why V14 was rejected

V14 improved V6 by `$107.99`, reduced closed drawdown by `$7.35`, reduced
equity drawdown by `$10.01`, reduced losing-month P/L from `-$525.26` to
`-$439.65`, and improved the worst month from `-$136.77` to `-$113.13`.

It was still rejected because:

- V60 trade retention was `97.9137%`, below the frozen `98%` floor;
- nominal 2022 was `$0.35` below V6;
- Dukascopy 2023 was `$24.21` below V6; and
- the `+$0.10` stress path was below V6 in 2022 and 2023.

The audit showed that the `0.40` cutoff rejected several profitable medium-rank
recovery trades. The already-exposed development grid included `0.30` as a
fixed monotonic alternative. V15 changes only that cutoff from `0.40` to
`0.30`. It therefore rejects fewer trades and cannot add a new veto relative to
V14 for the same causal state.

## Frozen policy

All V14 and V6 behavior remains fixed except:

```text
maximum_causal_rank_exclusive: 0.30
```

The month trigger remains eight resolved UTC-month trades and less than
`-$20.00` canonical `0.01`-lot-equivalent P/L. Missing ranks remain retained.
There are no source exceptions, year exceptions, cost-specific rules, exit
changes, sizing changes, or post-run threshold changes.

## Evidence limitation

V14's complete outcome and the rank of every V14 veto are exposed. V15 is a
post-result repair and has no independent historical holdout. Passing the replay
can nominate a forward challenger only; it cannot authorize deployment.

## Hard gates

V15 uses every V14 gate unchanged:

- nominal net/PF/drawdown and 3/6/12-month results not worse than V6;
- every annual P/L not worse than V6;
- at least 98% V60 trade and frequency retention;
- no more than 20 losing months, less negative losing-month P/L, and no worse
  worst month than V6;
- `+$0.10` and `+$0.20` cost net/PF/drawdown and every year not worse than V6;
- Dukascopy net/PF/drawdown and every year not worse than V6;
- August remains positive and not worse than V6; and
- no identity failure, open position, or deadlock.

Failure rejects V15 without tuning.

## Authorization

Research only. Broker actions, MT5 changes, runtime changes, demo deployment,
and live deployment are prohibited. Clean prospective evidence remains
mandatory.
