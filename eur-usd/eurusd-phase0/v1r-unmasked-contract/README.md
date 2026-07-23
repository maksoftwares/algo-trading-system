# EURUSD V1R Unmasked Contract Repair

This package is the reviewer-authorized Stage 0 repair for the EURUSD
RSI/Bollinger close-fade research family.

It creates a source-bound, candidate-specific baseline, adds a fail-closed
startup latch and evidence-only telemetry, aligns requested and reported
leverage to 1:50, and tests canonical parity against the exact 1,145-trade
unmasked benchmark.

It is retrospective MT5 Strategy Tester research only. It does not authorize a
chart attachment, demo order, live order, shadow execution, or broker runtime.

The immediate next-bar reclaim remains blocked until every Stage 0 parity gate
passes.

## Exact Stage 0 result

Status:

`STAGE0_PARITY_PASS_RECLAIM_NOT_RUN`

- 2,957 signal rows with zero canonical mismatches.
- 2,957 decision rows with zero canonical mismatches.
- 1,145 trades with zero canonical mismatches.
- 659 wins and 486 losses.
- Net USD 77.26.
- Gross profit/loss USD 779.61 / USD 702.35.
- Unrounded PF 1.1100021356873353.
- MT5 maximal equity drawdown USD 27.56 / 2.68%.
- INI and report leverage both 1:50.
- 2,290 entry/exit deals reconciled.
- 1,145 requested-versus-actual SL/TP geometries reconciled.
- Clean compile with zero errors and zero warnings.

Run the exact baseline:

```powershell
python eur-usd/eurusd-phase0/v1r-unmasked-contract/run_v1r_baseline.py
```

Build the canonical parity report:

```powershell
python eur-usd/eurusd-phase0/v1r-unmasked-contract/build_stage0_parity.py
```

Primary result:

`outputs/audit/STAGE0_PARITY_RESULT.md`

The corrected baseline is an immutable retrospective research benchmark. A
separate, frozen preregistration is still required before any reclaim source
can be created or tested.
