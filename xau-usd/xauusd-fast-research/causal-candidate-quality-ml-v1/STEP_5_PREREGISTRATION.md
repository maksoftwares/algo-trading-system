# Step 5 Shared-Account Portfolio Preregistration

## Purpose

Step 4 found that the locked ML model did not improve candidate selection. Step
5 therefore keeps ML offline and answers a different question: what happens when
the mechanically generated candidates are expressed together on one account
under fixed broker, risk, overlap, and cost rules?

## Evidence status

All candidate outcomes through June 30, 2026 are already exposed to research.
This is a deterministic historical accounting and risk experiment, not a fresh
confirmation test. A passing result remains research-only and cannot authorize
MT5, shadow, demo, or live execution. No policy field may be changed after the
combined result is opened in this version.

## Frozen populations

Four portfolios are reported:

1. The five regime families under their historical acceptance policy.
2. Every executable candidate from the five regime families under the new fixed
   account governor.
3. All nine families under their historical acceptance policy.
4. Every executable candidate from all nine families under the fixed account
   governor. This is the primary portfolio.

The historical comparators deliberately retain their as-recorded duplicates so
they reconcile to the prior 2,194-trade V59/V60 population. Governed portfolios
select only one candidate per structural episode using an outcome-blind fixed
tie break. Historical rejection is not treated as a loss and is not used by the
new governor.

## Fixed account expression

- Starting equity is USD 3,654.45.
- Every accepted trade is fixed at 0.01 lot, one ounce of XAUUSD.
- Maximum concurrent positions is three.
- At most two positions may share a direction.
- At most one position may be open per family and broad mechanism.
- At most four entries may occur on one UTC date.
- One trade may risk at most 0.75% of starting equity.
- Aggregate open initial risk may not exceed 1.5% of starting equity.
- Same-direction initial risk may not exceed 1.0% of starting equity.
- Conservative estimated margin may not exceed 25% of starting equity.
- A 2% UTC-day realized loss blocks later entries that day.
- Closed drawdown suspends entries at 10%, resumes below 8%, and permanently
  stops entries at 15%.
- Exits at one timestamp are applied as one batch before entries at that time.
- There is no dynamic sizing and no forced-liquidation claim.

## P&L and floating equity

The Step 3 stressed bid/ask labels are authoritative. USD P&L is stressed net R
times source-native initial USD risk at 0.01 lot. Endpoint P&L is independently
reconciled from executable entry and exit prices. Implied ticket, holding, and
stress costs are charged when a position opens for conservative mark-to-market
accounting.

Floating equity uses the previously audited Dukascopy bid/ask M5 history from
January 2010 through June 2026. Long positions are marked to bid and shorts to
ask. Each M5 bar assumes the favorable envelope before the adverse envelope,
which is conservative for drawdown. This is an M5 envelope, not an exact
tick-by-tick liquidation simulation.

## Required reports

Every policy reports 3M, 6M, 1Y, 2Y, 3Y, 5Y, 10Y, and full-history trade count,
frequency, net USD, profit factor, win rate, mean stressed R, closed drawdown,
floating-equity drawdown, positive-day and positive-month shares, concentration,
and top-five-winner removal. Daily P&L, six-month stability, specialist and
direction attribution, all decisions, accepted trades, and the primary M5 equity
curve are retained as hash-bound artifacts.

## Decision

The primary all-nine-family governed portfolio must pass every registered gate.
Even a pass is `RESEARCH_ONLY`; prospective post-freeze confirmation and exact
MT5 parity remain mandatory. ML predictions, ML thresholds, journey rows, COMEX,
Databento, new data acquisition, and runtime changes are prohibited.
