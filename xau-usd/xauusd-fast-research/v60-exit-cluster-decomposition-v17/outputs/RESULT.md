# V60 Exit And Cluster Decomposition V17 Result

Decision: **DIAGNOSTIC_SUPPORTS_TARGETED_PROTECTION_RESEARCH**

Read-only exposed diagnostic. No trading or deployment change is authorized.

## Portfolio attribution

| View | Trades | Net P/L | Profit factor | Win rate | Closed DD | Net/DD |
|---|---:|---:|---:|---:|---:|---:|
| Frozen source endpoints on V60 accepted set | 1390 | $3636.89 | 1.6368 | 44.60% | $253.18 | 14.36 |
| Deployed protected closes | 1390 | $3603.57 | 1.7107 | 48.49% | $223.28 | 16.14 |

Protection attribution delta on the fixed accepted set: **$-33.32**.
This is attribution, not a no-protection counterfactual; removing protection can change later capacity and fills.

Protection improves profit factor, closed drawdown, net/DD, and losing-month severity overall despite the lower fixed-set net P/L.

## Eligible follow-up lanes

- Protection sources: V7_SWING_HEALTH
- Cluster cohorts: none

| Source | Protection actions | Delta | Negative folds |
|---|---:|---:|---:|
| V7_SWING_HEALTH | 40 | $-19.46 | 2 |

## Cluster finding

Later same-source/direction/day trades made **$1097.97** at PF **1.8218** across 355 trades and were positive in every historical fold.
Trades after a resolved same-day directional loss made **$369.02** at PF **1.8115** across 116 trades.
The July/August cluster losses are therefore not a stable control mechanism.

## Recent exposed periods

| Period | Trades | Net P/L | PF | Win rate |
|---|---:|---:|---:|---:|
| July protected | 25 | $-45.00 | 0.7335 | 40.00% |
| August V60 through 25 | 24 | $-24.87 | 0.8346 | 41.67% |

## July integrity

Independent reconstruction: `FROZEN_RECONSTRUCTION_CONFIRMS_ZERO_CORE_CANDIDATES`.
The failed confirmation harnesses were read-only and are not treated as the cause of candidate silence.

## Governance

- No threshold search or veto simulation was performed.
- July and August are exposed diagnostics.
- Any eligible lane needs a separate preregistration, full path-dependent replay, cross-feed and cost stress, then clean forward confirmation.
- V60 remains the only broker-action policy.
