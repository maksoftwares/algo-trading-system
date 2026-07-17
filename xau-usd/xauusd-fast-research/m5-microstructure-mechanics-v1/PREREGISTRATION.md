# XAUUSD M5 Microstructure Mechanics V1

Date: `2026-07-17`

## Research question

Prior campaigns tested price structure, macro state, cross-asset state, event
reactions, H1/M30 machine-learning rankers, and pooled H1 microstructure. They
did not test direct, next-bar M5 rules built around completed-bar quote pressure.
This campaign asks whether native Dukascopy Bid/Ask information supports a
short-horizon specialist after realistic side-correct costs.

## Frozen attempt family

Exactly 1,000 policies are generated before outcomes are opened: 200 variants
for each of five mechanics.

1. `FLOW_CONTINUATION`: signed quote movement, tick imbalance, and book pressure
   agree while the spread remains controlled.
2. `FLOW_EXHAUSTION`: an extended move retains one-sided tick pressure while
   closing rejection and book pressure point the other way.
3. `BOOK_ABSORPTION`: price and signed ticks move one way while top-of-book
   pressure points the other way.
4. `LIQUIDITY_SHOCK_REVERSION`: price displacement occurs with a spread,
   variance, and quote-intensity shock, followed by rejection.
5. `POST_SHOCK_NORMALIZATION`: a prior spread shock normalizes while tick and
   book pressure establish a direction.

The manifest uses attempt numbers 6,094 through 7,093. Parameter combinations
are selected deterministically by SHA-256 from the frozen grids. Each mechanic
has one frozen stop, target, and hold geometry; V1 does not optimize exits.

## Causality and execution

Only a completed M5 bar and rolling baselines shifted by one bar may create a
signal. Entry is the immediately following contiguous M5 Bid/Ask open. Longs
enter at Ask and exit on Bid; shorts enter at Bid and exit on Ask. Stop-first
handling is used when stop and target occur in the same bar. The simulator also
includes gap-through-stop behavior, a fixed ticket cost, holding cost, and
0.05R stress slippage. Trades spanning missing bars or a stage boundary are
rejected.

## Chronological firewall

- Discovery: `2016-07-01` to `2021-01-01`, including three fixed subperiods.
- Confirmation: `2021-01-01` to `2023-01-01`.
- Internal test: `2023-01-01` to `2025-01-01`.
- Exam: `2025-01-01` to `2026-07-01`.

Discovery evaluates all 1,000 policies and applies Benjamini-Hochberg correction
to one-sided daily-return p-values. At most one policy per mechanic can advance.
Each later stage is run by a separate command and remains sealed until the
preceding advancement lock exists and passes integrity checks.

## Authority

This is retrospective research only. A four-stage passer is a near-survivor
requiring independent-era replication and prospective read-only shadowing. It
does not authorize model training, Python prediction serving, EA consumption,
demo orders, live orders, broker actions, paid data, or Databento use.
