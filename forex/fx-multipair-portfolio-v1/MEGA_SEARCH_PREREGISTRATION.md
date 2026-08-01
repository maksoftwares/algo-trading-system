# Mega-Search Preregistration — 10,000+ strategy attempts

Status: `PREREGISTERED_BEFORE_RUN`
Written 2026-08-01, before any result was generated.

## The problem this document exists to solve

A 10,000-attempt search is a **multiple-testing machine**. If every strategy
were pure noise, roughly 500 would still clear p < 0.05, and the best would look
spectacular. Any single "winner" pulled from 10,000 tries is worthless without
the accounting below.

This repository has already paid for that error four times: PF 1.99 → 0.82, a
claimed PF 2.03 that was really 1.20, an EURUSD portfolio at PF 1.3075 whose PF
fell to 1.019 ex-top-5%, and a US500 system inflated by 96.5 percentage points.
The search is therefore designed so its *survivor count* is interpretable, not
just its best cell.

## Execution model — fixes the error that killed the last lane

All simulation runs on **M5 bid/ask bars**, so:

* the **full 24-hour path** is modelled, including the overnight session. U11/U12
  showed that testing a 24h instrument against 6.5h daily index bars inflated
  results by 96.5pp. That mistake is structurally impossible here.
* longs pay the ask and are stopped on the bid path; shorts mirror.
* stops fill worse than the level; targets get no mirror improvement.
* a bar spanning both stop and target resolves to the **stop**.

Costs are the measured Capital.com spreads already embedded in the quotes, plus
2 points entry and 2 points stop slippage.

## Data and partitions

Primary instrument **US500** (measured range/cost 74.0x, the best on the
account after XAUUSD/US30), on 8 complete Dukascopy years of CFD quotes:
489,245 M5 bars, 2016–2023.

| Partition | Window | Years | Use |
|---|---|---|---|
| Design | 2016-01 .. 2020-01 | 4 | screen all attempts |
| Validation | 2020-01 .. 2022-01 | 2 | test design survivors |
| **Holdout** | 2022-01 .. 2024-01 | 2 | touched **once**, at the end |

The holdout contains 2022 — the worst year for every candidate this project has
produced. That is deliberate.

## Search space (≥10,000 attempts)

Cartesian product of:

- **entry families (8):** RSI extreme, Bollinger band touch, N-bar breakout,
  N-bar fade, MA distance reversion, consecutive-bar reversal, volatility
  expansion, session range break
- **decision timeframes (4):** M15, M30, H1, H4
- **direction (2):** long, short
- **stop (4):** 1.0 / 1.5 / 2.0 / 3.0 × ATR(14)
- **reward:risk (4):** 1.0 / 1.5 / 2.0 / 3.0
- **session filter (3):** all hours, US cash session, non-US hours
- plus family-specific lookbacks

Total ≥ 12,000 configurations.

## Staged gates (fixed now)

**Stage 1 — design.** A configuration passes if, on 2016–2019:
PF ≥ 1.20, ≥ 100 trades, net > 0.

**Stage 2 — validation.** Design survivors are re-run on 2020–2021 and must hold
PF ≥ 1.10 with ≥ 30 trades.

**Stage 3 — holdout.** Stage-2 survivors run **once** on 2022–2023.

## The chance benchmark — the number that decides everything

At each stage the survivor count is compared with what pure noise would produce.
If N configurations are tested and each has probability p of passing by chance,
the expected count is N·p with sd √(N·p·(1−p)).

**A stage is only informative if survivors exceed chance expectation by more than
3 standard deviations.** If 12,000 attempts yield ~600 design survivors and
chance predicts ~600, the correct conclusion is *no edge found*, regardless of
how good the best cell looks.

p is estimated empirically by rerunning the identical pipeline on **sign-flipped
returns** (a market with the same volatility structure and no drift), not
assumed.

## Reporting rules

- The best cell is reported **only** alongside the survivor-vs-chance count.
- Any survivor is discounted by this repo's measured selection-leak ladder
  (PF 1.99 → 1.45 → 0.82).
- A survivor must also beat **buy-and-hold on the same window** to be called a
  system. U12 rejected a candidate that was profitable yet returned a third of
  buy-and-hold for the same drawdown.
- Every stage count is recorded whether or not anything survives.
