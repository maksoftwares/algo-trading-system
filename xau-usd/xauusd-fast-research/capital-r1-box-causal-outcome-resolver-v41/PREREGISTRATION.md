# Capital R1 Box Causal Outcome Resolver V41 Preregistration

## Purpose

The repaired R1 sidecar emits immutable candidate facts but publishes outcomes
as a replaceable latest snapshot. V41 creates the missing append-only causal
label path. It does not change the specialist, select a parameter, aggregate
profit, train a model, or authorize an order.

## Frozen source

- Forward boundary: `2026-07-20T00:00:00Z`.
- Specialist: `R1_UPTREND_LONG_V1`.
- Source contract SHA-256:
  `27fef83d1a57aa28a1e4d4e6968b2854184a673cdff6769da16828fbe4084908`.
- Candidate identity, stop distance, 2R target, entry gap, spread limits, ticket
  cost, holding cost, and stress slippage must exactly match the source contract.
- The consumed candidate and resolution byte prefixes are immutable. Mutation,
  truncation, partial output, schema drift, or enabled authority fails closed.

## Causal execution

The first Capital quote at or after the H4 signal within ten minutes is the
entry quote. Long entry uses ask and long exit uses bid. The stop pays the first
observed executable crossing price; the target fills at the frozen target price.
There is no time exit. An accepted position stays pending until a stop or target
is observed.

Only `PORTFOLIO_CONSTRAINED_PRIMARY` is eligible: at most two concurrent R1 box
positions and at most one new entry per UTC day. Policy rejections are final at
the entry quote and cannot be resurrected after later outcomes are known.

## Historical parity

The exact Dukascopy portability implementation must regenerate 354 candidates,
345 executable candidate trades, and 119 primary-policy trades. Candidate,
all-policy, and primary-policy canonical digests are fixed before forward labels
are read.

## Evidence boundary and authority

V41 may append individual `EXECUTED` and `REJECTED` labels and expose counts. It
may not calculate aggregate economics, tune a rule, admit the sleeve, serve a
model, consume an EA signal, place a demo order, place a live order, or call a
broker API. Validation and confirmation remain separate sealed decisions.
