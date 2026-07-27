# EURUSD Neutral causal specialist preregistration

Status: `LOCKED_BEFORE_NEUTRAL_CANDIDATE_OUTCOME_INSPECTION`

## Objective

Approximate the Regime 1 Neutral hindsight-oracle trades with rules that use only information available at decision time. The oracle ledger is evaluation-only: it cannot generate signals, select families, tune parameters, or alter exits.

All archived history has already been inspected in earlier EURUSD campaigns, so the last window is honestly called pseudo-out-of-sample rather than pristine out-of-sample evidence. A pass still requires prospective confirmation.

## Causal ownership

A completed M5 signal is eligible only when the latest available cross-asset state no later than its completion-hour minus one hour is:

- `direction == NEUTRAL`;
- not a shock;
- not joint DXY and EURUSD compression.

No current incomplete H1 state is used.

## Fixed candidate families

1. `N1_ROLLING_SWEEP_FADE`: fade a completed M5 sweep and rejection of the preceding twelve completed M5 extremes.
2. `N2_ASIA_RANGE_FADE`: from 06:00 through 11:55 UTC, fade a completed sweep back inside that date’s completed 00:00–05:55 UTC range.
3. `N3_ANCHOR_REVERSION`: fade a completed rejection bar at least 1.25 rolling M5 ATR away from a 48-bar causal EMA.
4. `N4_MICRO_BREAKOUT`: continue a completed break of the preceding twelve M5 extremes when 12/48-bar EMAs and completed-bar tick activity agree.

The exact thresholds and causal feature windows are frozen in `config/frozen_neutral_causal.json`.

## Execution

Entry is the first M5 open after signal completion. Risk is fixed at 4 pips, target at 1.50R, and maximum hold at 12 hours. Longs pay ask and exit bid; shorts mirror. A 0.70-pip minimum spread, 0.10-pip adverse slippage per side, and stop-first ambiguous-bar handling are mandatory.

Each family permits one open position. The combined stream permits one open position, no more than four entries per UTC date, and uses the frozen family priority.

## Chronological firewall

Family selection may use only:

- 2019–2020 development;
- 2021–2022 development.

A family enters the combined stream only if both development windows contain at least 50 trades, PF at least 1.05, and positive expectancy. No family may be repaired after later outcomes are inspected.

The untouched-within-this-campaign evaluation order is:

1. 2023–2024 validation;
2. 2025 through June 2026 pseudo-OOS;
3. January–June 2026 recent diagnostic.

## Admission

Both evaluation windows must contain at least 50 trades with 45–55% wins, realized payoff 1.35–1.75, PF at least 1.10, and positive expectancy. Overall drawdown must not exceed 30R. Removing the top 5% of winners and charging another 0.50-pip round trip must both leave positive net R.

Oracle imitation is secondary evaluation only. A greedy one-to-one match requires the same UTC date and direction within 60 minutes. Matching cannot rescue an unprofitable or unstable causal strategy.
