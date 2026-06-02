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
| ALL | ALL | 66759 | 0.4125 | -0.6150 | 1.1265 | 220.2144 | -2052677.40 | 2053331.44 |

## Cells

| Cell | Broker | Trades | PF | Net R | Cost R | Cost % | Fixed PnL | Fixed Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | 7287 | 0.2660 | -0.7854 | 1.1494 | 315.8132 | -286176.66 | 286280.46 |
| 2 | capital_com | 7287 | 0.3489 | -0.6322 | 1.1494 | 222.2340 | -230339.26 | 230484.27 |
| 3 | capital_com | 7287 | 0.4725 | -0.4435 | 1.1632 | 161.6275 | -161600.84 | 161785.80 |
| 4 | pepperstone | 7174 | 0.4486 | -0.4967 | 0.7795 | 275.5647 | -178151.23 | 178531.78 |
| 5 | pepperstone | 7174 | 0.5315 | -0.3914 | 0.7795 | 200.8215 | -140384.19 | 140889.17 |
| 6 | pepperstone | 7174 | 0.6460 | -0.2649 | 0.7946 | 150.0093 | -95014.99 | 95655.73 |
| 7 | dukascopy | 7792 | 0.2844 | -1.1803 | 1.6306 | 362.1323 | -459844.74 | 457150.59 |
| 8 | dukascopy | 7792 | 0.3451 | -0.9624 | 1.6306 | 244.0475 | -374963.79 | 372891.29 |
| 9 | dukascopy | 7792 | 0.6259 | -0.3239 | 0.9856 | 148.9520 | -126201.70 | 126224.21 |

## Boundary

This report applies measured P95 spread cost to the existing fixed-risk trade ledger. It does not authorize Phase 2 by itself.
