# EURUSD Neutral Validated Consensus Result

Status: `REJECTED_NEUTRAL_VALIDATED_CONSENSUS`

## Outcome

Requiring the prior composite consensus to pass its own admission gates reduced the sample but worsened forward results. More in-sample filtering did not create a transferable Regime 1 edge.

| Scope | Trades | Win rate | Payoff | PF | Stressed PF | Net R | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full 2020-2026 H1 | 76 | 35.53% | 1.488 | 0.820 | 0.787 | -8.87 | 13.09R |
| Latest 12 months | 3 | 33.33% | 1.488 | 0.744 | 0.714 | -0.51 | 1.01R |
| Latest 6 months | 0 | N/A | N/A | 0.000 | 0.000 | 0.00 | 0.00R |

## Chronology

| Window | Trades | Win rate | PF | Net R |
|---|---:|---:|---:|---:|
| 2020-2021 | 13 | 15.38% | 0.270 | -8.06 |
| 2022-2023 | 31 | 41.94% | 1.077 | +1.38 |
| 2024-2025 | 32 | 37.50% | 0.891 | -2.19 |
| 2026 H1 | 0 | N/A | 0.000 | 0.00 |

LONG PF was 0.817 and SHORT PF was 0.822. Only subregimes 1 and 2 were positive, but selecting them now would be post-outcome overfitting and is prohibited.

## Conclusion

Close the H4 Neutral subregime/expert-selection family. The progression was:

- generic H4 model: PF 0.882;
- rolling single-best expert: PF 0.975;
- cross-mechanism consensus: PF 1.129;
- extra composite in-sample validation: PF 0.820.

The consensus improvement was real but insufficient and disappeared under stronger in-sample filtering. A legitimate next approach needs genuinely different historical information or a different regime horizon, not another threshold or selector on this same ledger. No demo or broker action is authorized.
