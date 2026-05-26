# Breakout Retest Measured-Cost Revalidation

Overall status: FAIL

## Decision

Measured P95 spread costs invalidate or materially weaken the current breakout-retest evidence package.

## Gate

- Required passing cells: 7
- Observed passing cells: 0
- Cell PF threshold: 1.30
- Minimum trades per cell: 40

## Overall

| Cell | Broker | Trades | PF | Net R | Cost R | Cost % | Fixed PnL | Fixed Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | ALL | 66759 | 0.3865 | -0.6779 | 1.1895 | 232.5268 | -2262912.40 | 2263566.44 |

## Cells

| Cell | Broker | Trades | PF | Net R | Cost R | Cost % | Fixed PnL | Fixed Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | 7287 | 0.2611 | -0.7989 | 1.1628 | 319.5108 | -291079.89 | 291183.68 |
| 2 | capital_com | 7287 | 0.3421 | -0.6456 | 1.1628 | 224.8360 | -235242.48 | 235387.50 |
| 3 | capital_com | 7287 | 0.4630 | -0.4563 | 1.1760 | 163.4054 | -166263.06 | 166448.03 |
| 4 | pepperstone | 7174 | 0.4348 | -0.5158 | 0.7987 | 282.3342 | -185020.53 | 185383.55 |
| 5 | pepperstone | 7174 | 0.5151 | -0.4105 | 0.7987 | 205.7549 | -147253.50 | 147740.94 |
| 6 | pepperstone | 7174 | 0.6264 | -0.2834 | 0.8131 | 153.5022 | -101651.45 | 102269.42 |
| 7 | dukascopy | 7792 | 0.2538 | -1.3705 | 1.8208 | 404.3716 | -533942.92 | 531248.76 |
| 8 | dukascopy | 7792 | 0.3042 | -1.1526 | 1.8208 | 272.5133 | -449061.97 | 446989.47 |
| 9 | dukascopy | 7792 | 0.5776 | -0.3937 | 1.0555 | 159.5005 | -153396.60 | 153419.10 |

## Boundary

This report applies measured P95 spread cost to the existing fixed-risk trade ledger. It does not authorize Phase 2 by itself.
