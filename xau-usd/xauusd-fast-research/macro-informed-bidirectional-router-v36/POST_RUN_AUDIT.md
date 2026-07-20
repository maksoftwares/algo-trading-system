# V36 Post-Run Audit

## Decision

`MACRO_ROUTER_V36_NO_ALL_BLOCK_SURVIVOR`

Exactly 1,000 locked policies were evaluated. Zero passed all four chronological
blocks. V36 is retired without threshold, feature, regime, direction, or model
rescue tuning.

## Best cross-block diagnostic policy

`MACRO_Q90__D6__S60__A2__W0P5`

| Block | Combined/day | Expansion trades | Expansion PF | Expansion USD | Combined PF | Combined USD |
|---|---:|---:|---:|---:|---:|---:|
| Development | 1.398 | 414 | 1.751 | 335.80 | 1.628 | 1,003.64 |
| Validation | 1.535 | 224 | 1.358 | 96.24 | 3.297 | 1,677.98 |
| Confirmation | 1.923 | 223 | 2.023 | 285.29 | 2.125 | 3,109.05 |
| Final | 1.755 | 298 | 0.881 | -128.32 | 2.515 | 4,380.47 |

The final Core remained exactly 160 trades, 0.613/day, +$4,508.78, PF 3.492,
and $889.69 closed-trade drawdown. V36 reduced final net and therefore did not
preserve the Core edge.

## Frequency frontier

- 68 policies reached at least 3.0 combined trades/day in all four blocks.
- Zero policies maintained Expansion PF at least 1.20 in all four blocks.
- Zero policies maintained positive Expansion net in all four blocks.
- 474 policies reached at least 3.0 combined trades/day in the final block.
- Zero final-block policies reached Expansion PF 1.20.
- The best final PF among policies with final frequency at least 3.0 was 0.821.
- The best minimum-block PF among policies with all-block frequency at least 3.0
  was 0.754.

This is an economic failure, not a candidate-density failure.

## Regime and direction failure

At the 90th score percentile, selected actions were profitable in the first three
blocks but failed in the final block:

| Block | Selected mean USD | PF | Long share | Flip share |
|---|---:|---:|---:|---:|
| Development | 2.07 | 2.052 | 37.5% | 0.6% |
| Validation | 1.26 | 1.557 | 31.5% | 0.0% |
| Confirmation | 3.16 | 2.331 | 43.7% | 6.8% |
| Final | -1.14 | 0.843 | 85.9% | 42.6% |

The executed final diagnostic sleeve lost primarily in transition and trend
states. It selected 121 transition longs for -$113.20, 29 downtrend longs for
-$202.85, and 57 uptrend longs for -$85.45 before gains elsewhere. The model's
direction allocation was not stationary.

## Integrity audit

- Contract lock SHA-256:
  `8f7831444854995c7b77854c388bfc762c64e1db450d61bb9f1feb69a5b1eaf6`.
- Result SHA-256:
  `41892e5071878cb6bed2f77d5ebdca5add0ce86e19f30b98b438471b04267ef1`.
- Manifest SHA-256:
  `6944d281b52054eec87bb926ba1fb2e01b3a695bb22ec950b9ccbef782e3c80d`.
- 100,780 action rows and 20,331 events were preserved.
- 88,216 action rows had a macro timestamp no later than the signal and no more
  than 15 minutes old; missing macro values used native model missing branches.
- No duplicate event/action pair, future macro timestamp, or infinite feature was
  present.
- Every fit and calibration maximum exit preceded its exclusive boundary.
- Local evaluation output was exactly equal to the frozen baseline evaluator in
  all four blocks.
- Every manifest hash reverified.
- No broker action or execution authority was opened.
