# H4 Macro Confluence Portability V1 Preregistration

## Frozen hypothesis

The unchanged H4 macro-confluence implementation may define a low-frequency independent XAUUSD sleeve when replayed on one continuous Dukascopy feed with native Bid/Ask execution.

No entry, macro vote, D1 trend, H4 reclaim, stop, target, throttle, or holding parameter is changed. The executable Phase 0 source and every macro input are SHA-256 locked in the configuration.

## Chronology

- Train: 2016-07-01 through 2021-12-31.
- Validation: 2022-01-01 through 2024-12-31. This overlaps the original Dukascopy matrix and is portability confirmation, not new evidence.
- Exam: 2025-01-01 through 2026-05-15. The original matrix ended before this period.

## Execution

- Entry on the first M5 bar starting at the completed H4 signal time.
- Long entry at Ask and exit on Bid; short entry at Bid and exit on Ask.
- Side-specific M5 stop/target paths, stop-first ambiguous bars, and gap-through-stop handling.
- One open position at a time, 0.01 lot equivalent, maximum USD 50 initial risk.
- Stress adds observed M5 maximum-spread expansion, 0.05R slippage, USD 0.30 ticket cost, and USD 0.35 per holding day.

## Decision

Every train, validation, exam, and full-period gate must pass. Failure is recorded without same-version tuning. A pass creates only a retrospective low-frequency research survivor requiring MT5 parity and prospective evidence.
