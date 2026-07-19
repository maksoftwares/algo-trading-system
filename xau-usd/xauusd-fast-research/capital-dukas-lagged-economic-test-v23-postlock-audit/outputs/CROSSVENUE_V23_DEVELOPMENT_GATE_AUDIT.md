# V23 Post-Lock Development Gate

- Decision: `V23_DEVELOPMENT_GATE_FAIL_NO_CONFIRMATION_REQUIRED`
- Frozen V23 contract: `2a3f6d996bd85378d7461d6f6c444b49b717eb9fe7f300048b671390f4a898d3`
- Confirmation data opened: `false`
- Full development weekdays: 22
- Primary trades: 354
- Primary frequency: 16.090909 trades/full weekday
- Primary base net: $-54.50
- Primary base PF: 0.917508
- Positive-net gate: `false`
- PF gate: `false`

## Clock Robustness

| Safety lag | Trades/day | Net | PF | Stress PF |
|---:|---:|---:|---:|---:|
| 15000 ms | 16.090909 | $-54.50 | 0.917508 | 0.821089 |
| 20000 ms | 13.227273 | $-98.63 | 0.835748 | 0.752341 |
| 30000 ms | 11.227273 | $-171.25 | 0.704206 | 0.636987 |

V23 failed before confirmation. Its direction, threshold, horizon,
costs, and filters remain frozen; same-version tuning is forbidden.
This result provides no trading or model authorization.
