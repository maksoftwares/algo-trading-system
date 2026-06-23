# A3 ML Demo Shadow Post-Attach Monitor Status

Overall status: DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS
Dataset version: xauusd_c02_multiacct_202606212303_geffebb6d_c9221d066

## Monitor

- Timeout seconds: 5.
- Poll seconds: 1.
- Elapsed seconds: 0.094.
- Attempt count: 1.
- Timed out: false.

## Upstream Statuses

- C22 post-attach runtime monitor: RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS
- C27 research preview runtime verifier: RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS

## Evidence Summary

- Post-attach runtime evidence all accounts: true.
- Research preview read path confirmed all accounts: true.
- Handoff research preview ready all accounts: true.
- Broker shadow tap exists all accounts: true.

## Attempts

| Attempt | Elapsed | C22 | C27 | Status |
| --- | --- | --- | --- | --- |
| 1 | 0.094 | RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS | RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS | DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS |

## Authorization

- Official model training authorized: false.
- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Broker action authorized: false.

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime launch attempted: false.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Demo-shadow runtime is confirmed: MT5 is logging observers and broker-shadow EAs can read Python preview rows. Continue collecting/exporting data until official C03/C05/C04/C06 gates pass.
