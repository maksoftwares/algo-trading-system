# A3 ML Live Refresh Status

Overall status: NOT_READY
Mode: EXECUTE_LIVE_READONLY
Requested start UTC: 2026-06-01T00:00:00Z
Publish requested: false

## Stage Summary

| Stage | Status |
| --- | --- |
| C02 account verification | PASS |
| C02 bars/ticks export | PASS |
| C03 readiness | NO_GO |
| C05 training | REFUSED_NOT_READY |
| C04 shadow bridge | DISABLED_FAIL_CLOSED |
| C06 EA handoff | REFUSED_NOT_READY |
| C07 pipeline | NOT_READY |

## Steps

| Step | Status | Detail |
| --- | --- | --- |
| C02-01 account verification | PASS | report_status=PASS |
| C02-02 bars/ticks export | PASS | report_status=PASS |
| C02-03 history/log snapshot | PASS | report_status=PASS |
| C07 offline readiness pipeline | PASS | report_status=NOT_READY |

## Failed C03 Gates

- dataset_status observed PIPELINE_ONLY required EXPLORATORY_MODEL or higher
- market_setup_groups observed 223 required >=300
- active_weeks observed 3.37 required >=8
- at_least_two_regimes observed FALLING required >=2 non-UNKNOWN regimes
- feature_budget observed 0 required >=6
- slippage_readiness observed INSUFFICIENT required ADEQUATE

## Boundary

- MT5 connection attempted: true.
- Data export attempted: true.
- Terminal runtime change authorized: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Continue collecting A1/A2/A3 live data, then rerun C08.
