# Historical Core Single-Exposure Risk Control V50

Decision: **V50_SINGLE_R1_EXPOSURE_RISK_GATE_PASS**

This is retrospective risk governance, not untouched alpha evidence and not order authority.

## Historical Comparison

| Window | Policy | Trades | Trades/day | Net USD | PF | Closed DD USD |
|---|---|---:|---:|---:|---:|---:|
| 1Y | `ORIGINAL` | 160 | 0.613 | 4508.78 | 3.492 | 889.69 |
| 1Y | `V43_TWO_POSITION` | 142 | 0.544 | 2478.19 | 3.195 | 259.53 |
| 1Y | `V50_SINGLE_POSITION` | 138 | 0.529 | 1997.98 | 3.047 | 106.71 |
| 2Y | `ORIGINAL` | 439 | 0.841 | 7332.55 | 2.708 | 889.69 |
| 2Y | `V43_TWO_POSITION` | 379 | 0.726 | 3811.63 | 2.459 | 278.05 |
| 2Y | `V50_SINGLE_POSITION` | 365 | 0.699 | 3180.98 | 2.472 | 212.14 |
| 5Y | `ORIGINAL` | 930 | 0.713 | 9582.12 | 2.622 | 889.69 |
| 5Y | `V43_TWO_POSITION` | 839 | 0.643 | 4920.23 | 2.268 | 289.53 |
| 5Y | `V50_SINGLE_POSITION` | 818 | 0.627 | 3985.70 | 2.185 | 252.68 |
| 10Y | `ORIGINAL` | 1165 | 0.447 | 9827.24 | 2.560 | 889.69 |
| 10Y | `V43_TWO_POSITION` | 1074 | 0.412 | 5165.35 | 2.209 | 289.53 |
| 10Y | `V50_SINGLE_POSITION` | 1053 | 0.404 | 4230.82 | 2.127 | 252.68 |

## Exact Floating Drawdown

The ten-year one-position R1 replay has exact stress floating drawdown of USD 335.58.
That is 11.19% of USD 2998.45, or 13.99% after the frozen 25% capital buffer.
The buffered minimum equity is USD 2796.48; the reference account has USD 201.97 above that minimum.

## Locked Control

- Maximum one open R1 box position.
- Maximum one new R1 box entry per UTC day.
- Reject a second R1 box entry while the first remains open.
- Keep the 15% account ceiling and 25% capital buffer.
- Keep execution fail-closed until whole-account forward evidence passes.

The R1 lane now fits its risk gate. Whole-Core floating drawdown remains unproven because the historical ledger lacks intratrade marks for every specialist.
