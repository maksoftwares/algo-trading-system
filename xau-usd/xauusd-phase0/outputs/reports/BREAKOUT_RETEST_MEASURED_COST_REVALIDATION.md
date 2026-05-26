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
| ALL | ALL | 66759 | 0.3128 | -0.9268 | 1.4384 | 281.1838 | -3093736.86 | 3094390.90 |

## Cells

| Cell | Broker | Trades | PF | Net R | Cost R | Cost % | Fixed PnL | Fixed Max DD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | 7287 | 0.2459 | -0.8561 | 1.2200 | 335.2259 | -311918.60 | 312022.40 |
| 2 | capital_com | 7287 | 0.3206 | -0.7028 | 1.2200 | 235.8944 | -256081.20 | 256226.21 |
| 3 | capital_com | 7287 | 0.4318 | -0.5107 | 1.2304 | 170.9618 | -186077.53 | 186262.50 |
| 4 | pepperstone | 7174 | 0.4136 | -0.5542 | 0.8371 | 295.9087 | -198794.96 | 199157.98 |
| 5 | pepperstone | 7174 | 0.4887 | -0.4489 | 0.8371 | 215.6475 | -161027.92 | 161515.37 |
| 6 | pepperstone | 7174 | 0.5932 | -0.3204 | 0.8501 | 160.4886 | -114925.28 | 115543.25 |
| 7 | dukascopy | 7792 | 0.1762 | -2.1642 | 2.6144 | 580.6385 | -843158.73 | 840464.58 |
| 8 | dukascopy | 7792 | 0.2043 | -1.9463 | 2.6144 | 391.3028 | -758277.78 | 756205.28 |
| 9 | dukascopy | 7792 | 0.4409 | -0.6763 | 1.3380 | 202.1984 | -263474.86 | 263497.36 |

## Boundary

This report applies measured P95 spread cost to the existing fixed-risk trade ledger. It does not authorize Phase 2 by itself.
