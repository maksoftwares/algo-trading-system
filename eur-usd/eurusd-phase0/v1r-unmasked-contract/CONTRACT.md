# EURUSD V1R Corrected Unmasked Baseline Contract

Candidate:

`EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT`

Stage 0 status:

`STAGE0_PARITY_PASS_RECLAIM_NOT_RUN`

## Authorized scope

This package implements only the independent reviewer's contract-repair action:

1. copy the reviewed mean-reversion source into a candidate-specific source;
2. freeze the actual executed body-fraction threshold at `0.40`;
3. retain no blocked-hour mask;
4. initialize the native M30 bar latch fail-closed;
5. add evidence-only environment, state, execution, and transaction telemetry;
6. use a declared-input-only tester INI with effective leverage `1:50`;
7. rerun the exact retrospective MT5 baseline;
8. require canonical parity with the 1,145-trade unmasked benchmark.

Frozen V1 and `unmasked-audit-v1` remain immutable.

The immediate next-bar reclaim is not implemented or run in this package.

## Frozen trading contract

| Field | Value |
|---|---|
| Symbol | EURUSD |
| Test chart | M5 |
| Signal timeframe | Native M30 |
| Direction | Long only |
| Period | `[2022-07-01, 2026-07-02)` |
| Fixed lot | 0.01 |
| Magic | 26723003 |
| Signal | Completed close at/below lower BB(20, 2.0), RSI(14) at/below 35, body fraction at/above 0.40 |
| Blocked hours | None |
| Maximum spread | 100 points |
| Daily filled-entry cap | 20 |
| Owned positions | Maximum one |
| ATR | Completed M30 ATR(14), shift 1 |
| Swing low | Six completed M30 bars, shifts 1 through 6 |
| Stop | Lower of six-bar low and Ask minus max(1.4 ATR, 30 points) |
| Stop ceiling | Reject above 700 points; do not truncate |
| Target | Pre-request Ask plus 0.8 times requested stop distance |
| Fill re-anchoring | None |
| Retry | None |
| Tester model | Model 0, Every tick; may contain generated ticks |
| Deposit / currency | USD 1,000 / USD |
| Requested and required report leverage | 1:50 |
| Runtime boundary | Strategy Tester only |

## Startup invariant

`OnInit()` stores the current native M30 bar-open timestamp and evaluates
nothing. The first eligible evaluation occurs only after a later native M30
transition. Reinitialization cannot process a pre-initialization completed bar.

## Stage 0 parity gates

All gates are conjunctive:

- exactly 2,957 canonical signals;
- exactly 2,957 canonical decision/attempt rows;
- exactly 1,145 trades;
- exactly 659 wins and 486 losses;
- net USD 77.26;
- gross profit USD 779.61;
- gross loss USD 702.35;
- ledger PF `779.61 / 702.35`;
- identical canonical signal, decision, entry, exit, price, commission, swap,
  and per-trade P&L fields;
- MT5 maximum floating-equity drawdown USD 27.56, subject only to report
  serialization;
- source, includes, compiler, EX5, inputs, tester, report, and evidence hashes
  frozen;
- zero errors and zero warnings;
- INI and report leverage both 1:50;
- no unknown or silently ignored tester input.

Any unexplained failure produces `STOP_REPAIR`. It does not authorize reclaim.

The exact result passed every listed gate with zero canonical signal,
decision, or trade mismatches. This freezes the repaired baseline; it does not
establish a robust edge or authorize the reclaim run by itself.
