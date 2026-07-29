# EURUSD Neutral H4 Walk-Forward Preregistration

Frozen at UTC: 2026-07-29T13:15:27.6900266Z

Status: `FROZEN_BEFORE_CANDIDATE_OUTCOMES_AND_MODEL_SELECTIONS`

Boundary: research only; no broker, terminal, account, order, or position access is authorized.

## Purpose

Test a genuinely different Regime 1 mechanism after rejecting the quiet-session controls and macro extreme-reversal transfer: a slow H4 probability model that refits monthly using only outcomes already closed before each refit boundary.

This is causal walk-forward replay but not pristine out-of-sample evidence because the wider campaign has inspected the archived price history.

## Frozen Contract

- Ownership: only completed H4 `chop` or `compression` states; the next H4 open is the entry.
- Candidate clock: every complete neutral-owned H4 bar from 2017 onward.
- Proposed sides: long and short are scored symmetrically.
- Target label: whether a fixed `1.5R` target hits before a `0.75 ATR` stop or 12-H4-bar time exit.
- Features: seven direction-independent H4 state/clock features and twelve side-oriented price, macro, location, momentum, and mean-reversion features listed in the frozen config.
- Macro: official FRED `DFII10` and `DTWEXBGS`, available only after observation date plus one day.
- Model: L2 logistic regression, `C=0.10`, standardized using the training slice only.
- Refit: first of every month; trailing three years; every training outcome must have exited before the refit boundary.
- Minimum training: 500 side rows and 100 targets.
- Selection: best side probability at least `0.50` and at least `0.03` above the opposite side.
- Evaluation: 2020-01-01 through 2026-06-30.
- One open position; overlapping later selections remain cash.

## Execution and Gates

Execution uses exact M5 bid/ask, a 0.7-pip spread floor, 2.0-pip entry ceiling, 0.1-pip adverse slippage per side, stop-first same-bar policy, another 0.5-pip stress, and the frozen October 2024 quarantine.

The full walk-forward must have at least 100 trades, 45%-55% wins, payoff 1.35-1.75, PF at least 1.30, stressed PF at least 1.15, every two-year/2026 block profitable, latest-12-month PF at least 1.15 and positive, at least 55% positive active months, PF at least 1.0 after removing the best 5% of winners, and drawdown no more than 15R.

No feature, side, month, hour, probability threshold, training length, stop, or target may be changed after viewing the result. A historical pass would still require prospective confirmation and cannot authorize demo trading.
