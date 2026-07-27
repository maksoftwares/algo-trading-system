# V6 Cross-Asset Early Exit V5 Post-Run Decision

## Decision

`HISTORICAL_GATE_FAIL_QUARANTINED`

The exact V5 policy must not be tuned in place or deployed.

## Economic Comparison

| Policy | V6 net | V6 PF | V6 closed DD | Shared net | Shared PF | Shared floating DD |
|---|---:|---:|---:|---:|---:|---:|
| Frozen V1, no early exit | $293.99 | 1.221 | $199.12 | $5,752.38 | 1.591 | $401.99 |
| Utility V4 | $102.96 | 1.084 | $269.96 | $5,561.35 | 1.578 | $413.60 |
| Cross-asset V5 | $100.01 | 1.082 | $253.30 | $5,558.40 | 1.578 | $413.60 |

V5 made 54 early exits. Only 68.5% were beneficial, and their total
pre-routing benefit was `-$252.84`. Only 2022 had positive annual action
benefit.

## Model Comparison

| Measure | V4 | V5 |
|---|---:|---:|
| Mean annual Spearman | 0.0558 | 0.0509 |
| Years with positive Spearman | 3/5 | 3/5 |
| Beneficial-exit precision | 70.4% | 68.5% |
| Total action benefit | -$245.37 | -$252.84 |

Coverage was not the problem: DXY 1-hour availability was 97.7%, Treasury was
96.2%, and the common-dollar factor was 100% on target snapshots.

## Finding

These coarse cross-asset returns do not identify the rare, high-value gold
recoveries that dominate the cost of premature exits. They slightly changed
which trades were closed but did not improve the asymmetric economic decision.

The defensible next research lane is not another threshold search over V5.
It should model the two competing outcomes separately:

1. probability and magnitude of recovery before the original exit;
2. probability and magnitude of continued loss.

An early exit should require conservative positive expected utility after both
outcomes and costs, with a leave-one-episode-out or embargoed event grouping so
correlated checkpoints cannot inflate evidence.
