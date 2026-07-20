# Historical Core Single-Exposure Risk Control V50

## Status

This is a retrospective risk-control successor to V43. The USD 889.69 closed
drawdown and its R1 stacking attribution were known before this package was
created. V50 makes no untouched-alpha claim and grants no execution authority.

## Fixed question

Does the smallest non-zero broker-expressible R1 exposure policy, one open R1
box position and one new R1 box entry per UTC day, reduce the known drawdown
enough to fit the frozen 15% equity ceiling with the frozen 25% capital buffer?

The one-position rule is selected from account-risk logic, not from a parameter
search. There are no alternative thresholds, stop changes, signal changes, or
post-result substitutions in this version.

## Frozen comparisons

1. Original historical Core ledger.
2. V43 two-position R1 box cap with one entry per UTC day.
3. V50 one-position R1 box cap with one entry per UTC day.

All non-target specialists and their historical rows remain unchanged.

## Measurements

For 1Y, 2Y, 5Y, and 10Y windows ending before 2026-07-01, report trades,
trades per weekday, net P/L, profit factor, and closed drawdown. Independently
replay the one-position R1 policy on the frozen ten-year Dukascopy M5 cache and
verify the global stress drawdown peak and trough with exact raw ticks.

## Pass/fail rule

The R1 risk lane passes only if all of the following hold:

- exact stress floating drawdown times 1.25 is at most 15% of USD 2,998.45;
- the broker's 0.01 minimum lot is expressible under that buffered limit;
- one-year PF remains at least 1.50;
- one-year closed drawdown is below the V43 two-position result; and
- exact tick peak/trough hours match the global M5 stress curve.

Passing this lane does not establish whole-Core account readiness because the
historical normalized ledger has no intratrade marks for every specialist.
The sealed shared-account forward evaluator remains mandatory.
