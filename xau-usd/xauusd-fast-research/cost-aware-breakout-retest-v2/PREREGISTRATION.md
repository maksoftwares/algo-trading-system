# XAUUSD Cost-Aware Breakout-Retest V2 Preregistration

Date: `2026-07-17`

## Purpose

Test whether the existing breakout-retest behavior remains positive when cost
feasibility is part of the setup definition rather than a filter added after a
result. V1 remains `COST_SUSPENDED_CANONICAL`; V2 receives no inherited approval.

## Frozen Event

- Decision timeframe: completed M5 bars.
- Levels: previous completed UTC-day high/low, previous completed UTC-week
  high/low, and latest swing confirmed with four bars on each side.
- Break: a close at least `0.30 * ATR(14)` beyond a level in the prior 20 bars.
- Retest: the next candidate bar trades within `$0.05` of the level and closes on
  the continuation side.
- Confirmation: the immediately following completed bar has the continuation
  color.
- Entry: stop order `$0.01` beyond the retest extreme, valid for five M5 bars.
- Stop: retest opposite extreme plus `0.10 * ATR(14)`.
- Target: `1.50R` from the actual executable entry.
- Maximum hold: 72 elapsed hours.
- One family position at a time; stop-first for ambiguous M5 bars.

## Cost-Aware Boundary

- Planned stop distance must be at least `$3.75`.
- Native Dukascopy Ask/Bid prices determine baseline fills.
- Historical native entry spread may not exceed `$0.75`.
- Pre-entry estimated stress cost is `$0.75` spread plus `$0.30` execution cost
  and `0.05R` slippage; candidates above `0.30R` are blocked.
- Report the preferred `0.20R` share separately; do not silently discard valid
  `0.20R` to `0.30R` candidates.
- Stress P&L replaces native spread with `$0.75`, then subtracts `$0.30`, `0.05R`,
  and `$0.35` per 24 hours held.

## Causality

All levels and ATR values are available at or before the completed signal bar.
Daily and weekly levels are grouped by M5 bar start, so the 23:55-00:00 bar
belongs to the day it actually opened. Pending entry begins after confirmation.
Long entries use Ask and long exits use Bid; short entries use Bid and short exits
use Ask. Gap-through stops receive the worse executable open.

## Chronological Firewall

- Train: 2016-07-01 through 2020-06-30.
- Validation: 2020-07-01 through 2022-06-30.
- Internal test: 2022-07-01 through 2024-06-30.
- Exam: 2024-07-01 through 2026-06-30.
- Recent tail: 2025-07-01 through 2026-06-30.

Later stages are decision-ineligible after the first failed stage. The recent tail
was not used by the 2026-05 Phase 0 matrix, but it has been inspected elsewhere in
this repository and is not called untouched.

## No-Tuning Rule

V2 has one parameter set and zero search trials. A failure cannot be repaired,
inverted, session-filtered, or threshold-tuned in V2.

## Authorization

Research only. A pass would be one same-family retrospective survivor requiring
exact-tick parity and prospective shadow evidence. It gives no diversification
credit and cannot unsuspend V1.
