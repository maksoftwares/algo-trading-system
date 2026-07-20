# XAUUSD One-Trade-Per-Day Portfolio V51 Preregistration

## Purpose

V51 asks one narrow question: can one fixed, account-feasible Expansion sleeve
raise the unchanged V50 Core to at least one completed trade per UTC weekday in
later chronological periods while retaining positive stressed expectancy and a
controlled closed drawdown?

The one-trade-per-day value is an acceptance threshold, not a quota. V51 may
abstain whenever no candidate passes. It cannot alter any Core signal, stop,
target, position, or P/L.

## Known evidence and selection

High-Frequency Expansion V1 previously evaluated exactly 1,000 policies on the
2019-2021 selection period. Its `M060` PRICE_REGIME model had stable positive
selection results around 1.4 trades per weekday but failed only the old minimum
frequency and positive-month gates. No policy earned access to the later test.

For V51, 12 development-only risk/action variants were observed. The fixed
successor uses `M060`, a rolling 60th-percentile score threshold with a zero
floor, FAST and INTRADAY actions only, at most two entries per weekday, and one
open add-on position. On the already-open development period, the add-on made
734 completed trades, 0.936 per weekday, USD 178.13 stressed net, PF 1.192, and
USD 128.92 closed drawdown. Combined with the V50 Core it exceeded one trade per
weekday. These figures selected the policy; they are not acceptance evidence.

The original search did not enforce its `current_account_feasible` label. V51
does. Every accepted add-on must be expressible at the broker minimum 0.01 lot
with initial risk no greater than USD 8.165487.

## Frozen model and policy

- HistGradientBoostingRegressor with learning rate 0.03, 120 iterations, seven
  leaves, 50 minimum samples per leaf, L2 1.0, 127 bins, and seed 314218.
- PRICE_REGIME features only. Labels, entry/exit outcomes, P/L, MFE, MAE,
  future regimes, event IDs, and timestamps are excluded.
- For each evaluation window, fit only rows whose signals and exits are before
  that window. Clip the training target to [-1.5R, 2.25R].
- Select the highest-scored allowed action per event, then require the score to
  exceed both zero and the lagged 500-event 60th percentile. The current event
  is excluded from its threshold.
- Reject shock, weekend, and account-infeasible candidates.
- Maximum two add-on entries per UTC weekday and one open add-on position.
- V50 Core keeps priority and remains byte-for-byte sourced from its frozen
  ledger and one-R1-position policy. Add-on and Core positions may overlap; the
  overlap is measured and reported, not silently discarded.

## Chronology

| Stage | Period | Role |
|---|---|---|
| Development | 2019-01-01 to 2022-01-01 | Policy selection; already observed |
| Validation | 2022-07-01 to 2024-07-01 | First later evaluation |
| Final exam | 2024-07-01 to 2026-07-01 | Second later evaluation |
| Recent tail | 2025-07-01 to 2026-07-01 | Diagnostic subset of final exam |

The later periods are chronological tests, but V51 makes no pristine-holdout
claim because the underlying specialist families were developed during the
broader research program.

## Acceptance

Validation and final exam must each independently meet every locked gate. The
add-on must average at least 0.60 trades per weekday, have PF at least 1.10,
positive stressed net after removing the largest locked number of winners, and
closed drawdown no greater than USD 175.

The combined portfolio must average at least 1.00 trade per weekday, have PF at
least 1.50, positive stressed net and positive net in each chronological half,
at least 55% positive calendar months, positive net after winner removal, and
closed drawdown no greater than USD 300. At the frozen 1.25 safety buffer, USD
300 becomes USD 375, below 15% of the USD 2,998.45 reference equity.

The recent tail must also meet its separately frozen gates. A pass means the
historical frequency/economics milestone is met; it does not authorize trading.

## Limitations and stop rule

The normalized Core ledger lacks intratrade marks for every specialist. V51 can
measure exact completed-trade drawdown and overlap, but cannot prove whole-
account floating equity drawdown. Demo/live remains fail-closed pending the
existing prospective shared-account gate.

After the contract is locked, no model, feature, action, threshold, split,
portfolio limit, cost, or gate may change in V51. Any failed validation, final,
or recent gate makes V51 terminal. No same-version rescue is allowed.
