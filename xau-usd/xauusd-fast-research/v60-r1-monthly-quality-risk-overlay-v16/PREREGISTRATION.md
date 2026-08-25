# V60 R1 Monthly Quality Risk Overlay V16 Preregistration

## Objective

Test whether a source-local monthly quality layer can preserve the useful V14
and V15 risk improvement without their cross-feed and cost-path instability.

## Diagnosis behind the change

The frozen V6 losing-month attribution assigns `-$170.35` to R1 pullback and
`-$90.35` to R1 box inside negative months. Together they are the largest
mechanism-level concentration of losing-month damage.

V14 and V15 applied their month-state rule to every source. They improved net,
drawdown, losing-month burden, and the worst month, but were rejected because
V57 trades changed outcome sign between Capital.com and Dukascopy and under the
`+$0.10` cost path. V16 stops using portfolio deterioration as permission to
filter unrelated sleeves.

All cited outcomes are exposed. This is a post-result mechanism repair, not an
independent historical test.

## Frozen policy

V16 preserves V6 completely and adds this one entry rule after normal V60/V6
acceptance:

1. Track resolved portfolio P/L in each UTC calendar month.
2. Do nothing until eight accepted positions have closed in that month.
3. When canonical `0.01`-lot-equivalent month P/L is below `-$20.00`, evaluate
   only `R1_PULLBACK` and `R1_BOX` candidates.
4. Reject an eligible R1 candidate only when causal rank is below `0.20`.
5. Retain all other sources, ranks `>= 0.20`, and missing/non-finite ranks.
6. Continue trading eligible higher-rank R1 candidates so recovery is possible.
7. Reset at the UTC month boundary.

The `0.20` rank boundary was present in the exposed bounded screen before V14.
No source-year exception, cross-feed exception, cost-specific rule, exit change,
sizing change, or threshold grid is allowed.

## Hard gates

The V14/V15 gates remain unchanged:

- nominal net/PF/drawdown, 3/6/12-month values, and every year not worse than V6;
- at least 98% V60 trade and frequency retention;
- no more than 20 losing months, less negative losing-month P/L, and no worse
  worst month than V6;
- `+$0.10` and `+$0.20` net/PF/drawdown and every year not worse than V6;
- Dukascopy net/PF/drawdown and every year not worse than V6;
- August positive and not worse than V6; and
- at least one V16 veto with no identity failure, open position, or deadlock.

Failure rejects V16 without tuning.

## Authorization

Research only. Broker actions, MT5 changes, runtime changes, demo deployment,
and live deployment are prohibited. Clean prospective evidence is mandatory.
