# A3 ML R1/R2 Dukascopy Portability Preregistration

Date: 2026-07-16

## Purpose

Test whether the frozen R1 and R2 XAUUSD specialists retain useful edge when reconstructed and replayed on complete Dukascopy Bid/Ask ticks. The rules and acceptance gates are frozen before the 47 missing full months are acquired and before their Dukascopy outcomes are inspected.

This is a cross-feed portability exam, not an untouched strategy-development holdout. MT5 outcomes through 2026-06-30 are already known. The first genuinely prospective holdout begins 2026-07-01.

## Frozen Specialists

- R1: `r1_box_clean_strict_uptrend`, long only, signal mode 7, strict R1 router, fixed 2R.
- R2: `r2_pullback_short_h1_confirm`, short only, signal mode 21, strict R2 router, H1 confirmation, fixed 2R.
- Execution reconstruction uses observed Dukascopy Bid/Ask ticks. No synthetic spread may replace the source spread.
- The replay permits a maximum 1,440-hour research hold plus a 72-hour quote grace. This exceeds the longest 1,167.83-hour R1 reference trade; it is a finite research boundary for an EA that otherwise has no time exit.
- Stress deducts an additional USD 0.30 per trade and USD 0.35 per 24 held hours after native Bid/Ask execution.
- No threshold, session, regime, stop, target, or direction parameter may change after this preregistration.

The machine-readable source hashes and effective-input assertions are in `config/ml/a3_ml_r1_r2_dukascopy_portability_v1.json`.

## Data Windows

- Historical backcast: 2016-07-01 through 2024-06-30.
- Recent cross-feed exam: 2024-07-01 through 2026-06-30.
- Prospective holdout: starts 2026-07-01 and remains unopened for development decisions.

All 120 months from 2016-07 through 2026-06 must have complete, checksum-valid monthly acquisition manifests. Sparse event-window extracts are ineligible.

## Frozen Gates

The exam passes only when all machine-readable gates pass, including:

- every expected month is complete and valid;
- portfolio stress PF is at least 1.20 in each window;
- each specialist stress PF is at least 1.05 and stress net is positive in each window;
- at least 60% of calendar years and 65% of rolling six-month blocks are positive;
- the top exposure episode contributes no more than 35% of profit;
- net remains positive after removing the top three exposure episodes;
- closed drawdown is no more than 50% of net profit;
- candidate counts and timestamps reconcile plausibly with the MT5 reference.

The stress calculation must include native spread plus the separately frozen execution and holding-cost assumptions used by the replay implementation.

## Decision Policy

- `PORTABILITY_PASS`: the frozen pair may advance to account-level risk engineering and prospective shadow validation. This does not authorize demo trading.
- `PORTABILITY_FAIL`: reject or structurally redesign the failing specialist. Do not rescue it by tuning against Dukascopy outcomes.
- `DATA_NOT_READY`: acquisition or integrity is incomplete. No strategy conclusion is permitted.

No model, EA, terminal, account, order, or position is authorized or changed by this work.
