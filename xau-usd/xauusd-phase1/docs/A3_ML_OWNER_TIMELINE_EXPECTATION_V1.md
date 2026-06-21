# A3 ML Owner Timeline Expectation V1

Status: PRELOCK_CONTRACT

This contract owns multi-month evidence expectation, CONTINUE_EVIDENCE semantics, and no schedule-based gate relaxation.

## Expected Sequence

C00 and C01:

- contract merge;
- pre-lock verification;
- SHA256 lock.

C02 through C08:

- source inventory;
- grouping, labels, slippage, dataset;
- splits, feature budget, power/MDE;
- deterministic benchmarks;
- logistic baseline;
- calibration, thresholding, historical OOS comparison.

C14:

- forward checkpoint after at least 100 retained trades and at least 4 weeks.

C15:

- forward confirmation after at least 300 retained trades, at least 12 active weeks, and adequate MDE/power.

On one symbol and one signal family, multi-month evidence accumulation is normal.

## Valid States

Valid terminal or continuation states:

- FAIL;
- CONTINUE_EVIDENCE;
- FORWARD_CONFIRMATION_PASS.

CONTINUE_EVIDENCE means the implementation is operating correctly but the sample is still too weak to distinguish edge from noise.

It is not a project failure and must not trigger threshold relaxation.

No deadline may override:

- sample gates;
- MDE adequacy;
- confidence bounds;
- regime coverage;
- safety boundary;
- reviewer signoff.
