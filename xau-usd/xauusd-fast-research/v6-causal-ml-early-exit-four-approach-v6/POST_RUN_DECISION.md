# V6 Four-Approach Post-Run Decision

## Decision

`ALL_HISTORICAL_GATES_FAIL_QUARANTINED`

No arm is authorized for Python prediction, EA consumption, demo, or live
trading. Frozen V1 without ML early exits remains the historical benchmark.

## Comparison

| Arm | Exits | Beneficial | Action benefit | V6 net | V6 PF | V6 DD | Shared net | Floating DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Frozen V1 | 0 | - | $0.00 | $293.99 | 1.221 | $199.12 | $5,752.38 | $401.99 |
| A: competing utility | 2 | 50.0% | -$19.56 | $267.24 | 1.205 | $199.12 | $5,725.63 | $401.99 |
| B: regime competing | 8 | 87.5% | +$14.64 | $308.63 | 1.236 | $199.12 | $5,767.02 | $401.99 |
| C: path sequence | 56 | 69.6% | -$238.45 | $109.88 | 1.091 | $253.30 | $5,568.26 | $413.60 |
| D: unanimous ensemble | 0 | - | $0.00 | $293.99 | 1.221 | $199.12 | $5,752.38 | $401.99 |

## Findings

### Arm A

The global competing-outcome model was too conservative and still chose the
wrong two trades overall. It failed model quality, action coverage, annual
stability, and economic gates.

### Arm B

This was the only economically positive arm. Seven of eight first exits were
beneficial. Full-history V6 net improved by `$14.64`, PF improved from `1.221`
to `1.236`, and shared-account net improved by the same amount without
increasing full-history closed or floating drawdown.

It is not approved because:

- mean annual Spearman was only `0.0308`, below `0.05`;
- only two of five years had positive rank correlation;
- only 2022 and 2024 had positive action benefit;
- it made no first exits in 2025 or 2026;
- development-window V6 drawdown increased from `$90.15` to `$91.04`.

The result is useful mechanism evidence, not deployment evidence.

### Arm C

The ordered M5 path did not solve the rare-recovery problem. Its 56 exits lost
`$238.45` of benefit and worsened V6 and shared-account economics and drawdown.

### Arm D

The three member policies never agreed at the same checkpoint. It therefore
reproduced frozen V1 exactly but failed minimum action coverage, benefit, and
model-quality gates.

## Conclusion

Trying all four planned structures did not produce an approved ML early-exit
policy. The evidence now favors leaving exits unchanged rather than adding ML
management. Approach B may justify a future independently locked prospective
observer, but its historical predictions must not control trades.
