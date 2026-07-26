# ML Experiment Comparison Through V17

V14 is the locked prospective lane and has no distinct exact historical replay, so it is listed in the registry but not duplicated in these tables.

## 3M

| Approach | Trades | P&L | Delta vs raw | Win rate | PF | DD | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| RAW | 64 | $349.73 | $0.00 | 46.88% | 1.655 | $137.17 | `BENCHMARK` |
| B123 | 60 | $331.40 | $-18.32 | 46.67% | 1.646 | $140.85 | `HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL` |
| V15 | 61 | $317.88 | $-31.84 | 45.90% | 1.604 | $140.85 | `V15_HISTORICAL_GATE_FAIL` |
| V16 | 63 | $325.59 | $-24.14 | 46.03% | 1.610 | $140.85 | `V16_HISTORICAL_GATE_FAIL` |
| V17 | 64 | $349.73 | $0.00 | 46.88% | 1.655 | $137.17 | `V17_HISTORICAL_GATE_FAIL` |

## 6M

| Approach | Trades | P&L | Delta vs raw | Win rate | PF | DD | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| RAW | 147 | $1669.95 | $0.00 | 42.86% | 2.317 | $137.17 | `BENCHMARK` |
| B123 | 141 | $1677.83 | $7.87 | 43.26% | 2.374 | $140.85 | `HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL` |
| V15 | 141 | $1678.32 | $8.37 | 43.26% | 2.375 | $140.85 | `V15_HISTORICAL_GATE_FAIL` |
| V16 | 146 | $1645.81 | $-24.14 | 42.47% | 2.298 | $140.85 | `V16_HISTORICAL_GATE_FAIL` |
| V17 | 147 | $1669.95 | $0.00 | 42.86% | 2.317 | $137.17 | `V17_HISTORICAL_GATE_FAIL` |

## 1Y

| Approach | Trades | P&L | Delta vs raw | Win rate | PF | DD | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| RAW | 356 | $2502.72 | $0.00 | 44.10% | 1.984 | $208.41 | `BENCHMARK` |
| B123 | 335 | $2569.45 | $66.72 | 44.78% | 2.079 | $191.67 | `HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL` |
| V15 | 334 | $2576.04 | $73.32 | 44.91% | 2.085 | $191.67 | `V15_HISTORICAL_GATE_FAIL` |
| V16 | 347 | $2547.17 | $44.44 | 44.67% | 2.034 | $191.67 | `V16_HISTORICAL_GATE_FAIL` |
| V17 | 348 | $2547.77 | $45.05 | 44.54% | 2.029 | $191.67 | `V17_HISTORICAL_GATE_FAIL` |

## 2Y

| Approach | Trades | P&L | Delta vs raw | Win rate | PF | DD | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| RAW | 787 | $3717.07 | $0.00 | 45.24% | 1.828 | $279.04 | `BENCHMARK` |
| B123 | 743 | $3803.86 | $86.79 | 45.76% | 1.898 | $270.87 | `HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL` |
| V15 | 744 | $3813.25 | $96.18 | 45.83% | 1.901 | $263.15 | `V15_HISTORICAL_GATE_FAIL` |
| V16 | 778 | $3761.51 | $44.44 | 45.50% | 1.853 | $276.87 | `V16_HISTORICAL_GATE_FAIL` |
| V17 | 759 | $3793.78 | $76.71 | 45.72% | 1.876 | $263.15 | `V17_HISTORICAL_GATE_FAIL` |

## 5Y

| Approach | Trades | P&L | Delta vs raw | Win rate | PF | DD | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| RAW | 1512 | $4800.89 | $0.00 | 45.37% | 1.726 | $279.04 | `BENCHMARK` |
| B123 | 1468 | $4887.68 | $86.79 | 45.64% | 1.769 | $270.87 | `HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL` |
| V15 | 1469 | $4897.08 | $96.18 | 45.68% | 1.770 | $263.15 | `V15_HISTORICAL_GATE_FAIL` |
| V16 | 1503 | $4845.34 | $44.44 | 45.51% | 1.742 | $276.87 | `V16_HISTORICAL_GATE_FAIL` |
| V17 | 1484 | $4877.60 | $76.71 | 45.62% | 1.755 | $263.15 | `V17_HISTORICAL_GATE_FAIL` |

## 10Y

| Approach | Trades | P&L | Delta vs raw | Win rate | PF | DD | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| RAW | 2069 | $5199.00 | $0.00 | 45.09% | 1.653 | $279.04 | `BENCHMARK` |
| B123 | 2025 | $5285.79 | $86.79 | 45.28% | 1.685 | $270.87 | `HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL` |
| V15 | 1994 | $5281.62 | $82.62 | 45.34% | 1.692 | $263.15 | `V15_HISTORICAL_GATE_FAIL` |
| V16 | 2060 | $5243.44 | $44.44 | 45.19% | 1.665 | $276.87 | `V16_HISTORICAL_GATE_FAIL` |
| V17 | 2041 | $5275.71 | $76.71 | 45.27% | 1.676 | $263.15 | `V17_HISTORICAL_GATE_FAIL` |

## ALL

| Approach | Trades | P&L | Delta vs raw | Win rate | PF | DD | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| RAW | 2153 | $5432.47 | $0.00 | 44.73% | 1.659 | $279.04 | `BENCHMARK` |
| B123 | 2109 | $5519.26 | $86.79 | 44.90% | 1.691 | $270.87 | `HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL` |
| V15 | 2078 | $5515.09 | $82.62 | 44.95% | 1.698 | $263.15 | `V15_HISTORICAL_GATE_FAIL` |
| V16 | 2144 | $5476.91 | $44.44 | 44.82% | 1.671 | $276.87 | `V16_HISTORICAL_GATE_FAIL` |
| V17 | 2125 | $5509.18 | $76.71 | 44.89% | 1.682 | $263.15 | `V17_HISTORICAL_GATE_FAIL` |
