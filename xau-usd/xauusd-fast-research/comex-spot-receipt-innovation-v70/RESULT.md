# COMEX-Spot Receipt Innovation V70 Result

Date: 2026-07-20
Decision: `V70_DEVELOPMENT_FAIL_TERMINAL`
Authority: historical research only

V70 corrected V69's invalid cross-clock assertion while changing no policy
grid, selected threshold, execution rule, split, or economic gate. Its
outcome-blind calibration reproduced the same policy and the immutable contract
was frozen before any development outcome was written.

Development resolved 385 trades over 491 eligible full weekdays, or 0.784114
trades per weekday. The sample contained 184 longs and 201 shorts. It passed
frequency, sample size, direction balance, profitable-day share, and the USD
150 closed-drawdown ceiling, but it did not retain edge after realistic costs:

- base net: USD 18.71;
- stress net: USD -21.45;
- base PF: 1.0540;
- stress PF: 0.9414;
- profitable-day share: 40.12%;
- positive-month share: 43.48%;
- first/second-half stress PF: 0.9783 / 0.9057;
- stress net after removing five winners: USD -54.95;
- closed stress drawdown: USD 37.55; and
- one-sided block-bootstrap p-value: 1.0.

The stage recorded 78,822 rows where the publisher event clock exceeded the
Databento receive clock. No row was filtered for that cross-clock relationship;
all ordering and decisions used `ts_recv`, as preregistered.

Validation and exam remain sealed. The event-time receipt-innovation family is
terminal on these exposed outcomes and cannot be rescued by changing its clock,
horizon, threshold, direction, exit, cost, or quota.

Contract SHA-256:
`cc71627134dd00c051756cbe9587686717ad70b49245bff071032a01325d297a`

Development audit SHA-256:
`66d9fd77b0d671188b2d8b335189d32808bcc6239d13c050046af1b54e36e867`
