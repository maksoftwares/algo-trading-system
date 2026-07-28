# V60 ML Sizing Causal Retest V1 Result

Decision: **HISTORICAL_OR_EXECUTION_GATES_FAIL_KEEP_ML_OFF_DEMO**

Historical research only. No MT5 or runtime authorization is granted.

## Feature audit

- Current V60 population after R5 exclusion and V57 cooldown: 2069 rows.
- Feature-complete rows: 2069.
- Incomplete bars used: 0.

## Corrected result

| policy | trades | net | PF | win rate | closed DD | floating DD | net/floating DD | delta years >= 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V60 baseline | 1676 | $5045.67 | 1.721 | 45.58% | $298.06 | $335.34 | 15.05 | 6/6 |
| Continuous ML | 1676 | $5916.82 | 1.839 | 45.58% | $286.26 | $389.01 | 15.21 | 3/6 |
| Broker ML | 1429 | $4827.58 | 1.793 | 45.21% | $306.95 | $354.22 | 13.63 | 2/6 |

## Gates

- Continuous historical gates: FAIL.
- Broker historical gates: FAIL.
- Broker risk gates: FAIL.
- Continuous delta versus baseline: $871.14; mean multiplier 1.0232.
- Broker delta versus baseline: $-218.09; 247 trades skipped and 128 trades doubled.
- Continuous weekly-block lower bound: $445.90.
- Broker weekly-block lower bound: $-777.42.

## Demo verdict

Do not apply this ML overlay to demo orders. Keep deterministic V60 unchanged while a different prospective ML candidate is evaluated.
