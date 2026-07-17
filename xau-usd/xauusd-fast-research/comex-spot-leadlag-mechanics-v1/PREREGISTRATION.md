# XAUUSD COMEX-Spot Lead/Lag Mechanics V1

Date: `2026-07-18`

## Research question

Primary COMEX trade-flow, auction-profile, initial-balance, session-VWAP, and
balanced-horizon campaigns did not produce an eligible specialist. Those tests
did not mechanically trade the completed-bar return gap between the exchange
future and executable spot XAUUSD. This campaign asks whether intraday GC price
discovery leads a delayed or excessive move in spot after realistic Bid/Ask
costs.

The old `h1_gc_xau_basis_reversion_v0` test is not this experiment. It used a
shifted Yahoo daily continuous-futures proxy. V1 uses the already-downloaded
primary exchange trade cache synchronized to the native Dukascopy M5 Bid/Ask
cache. It makes no network request and authorizes no paid data operation.

## Frozen attempt family

Exactly 1,000 policies are registered before outcomes are opened: 200 variants
for each of five mechanics.

1. `GC_LEADS_XAU_CATCHUP`: GC and XAU move in the same direction, but the
   completed GC move is materially larger; trade the GC direction.
2. `GC_IMPULSE_XAU_STALE`: GC moves while spot remains nearly stationary;
   trade a short-horizon spot catch-up.
3. `XAU_LEADS_GC_FADE`: spot moves without equivalent futures confirmation and
   closes with rejection; fade the spot move.
4. `DIRECTIONAL_DISAGREEMENT_GC_AUTHORITY`: GC and spot move in opposite
   directions while futures delta supports GC; trade the GC direction.
5. `GAP_CONVERGENCE_IGNITION`: a prior GC-versus-spot gap starts closing because
   spot begins following the GC direction; trade the observed convergence.

The manifest uses attempt numbers 7,094 through 8,093. Parameter combinations
are ordered deterministically by SHA-256 from frozen grids. An outcome-blind
coverage screen admits a policy only when its completed features create at
least 120 raw discovery signals. The raw count is stored in the frozen policy
manifest. The screen does not simulate an entry, read a label, or calculate a
return. Exit geometry is fixed per mechanic and is not optimized inside the
1,000 attempts.

## Roll, causality, and execution controls

The Databento volume-continuous cache does not retain instrument IDs in its
derived auction bars. Therefore every GC return is reset at the New York
session boundary. No overnight futures level, cross-session return, or absolute
futures/spot basis is permitted. A return is valid only when all required M5
bars are contiguous inside one session.

Signals use completed GC and spot M5 bars at the same availability timestamp.
Entry is the immediately following contiguous spot M5 bar. Longs enter at Ask
and exit on Bid; shorts enter at Bid and exit on Ask. Stops use gap-through
behavior, same-bar ambiguity is stop-first, and results include ticket cost,
holding cost, and 0.05R stress slippage.

## Chronological firewall

- Discovery: `2022-07-01` to `2023-07-01`, split into four fixed quarters.
- Confirmation: `2023-07-01` to `2024-07-01`, split into four fixed quarters.
- Internal test: `2024-07-01` to `2025-07-01`, split into four fixed quarters.
- Exam: `2025-07-01` to `2026-07-01`, split into four fixed quarters.

Discovery evaluates all 1,000 policies and applies Benjamini-Hochberg
correction to one-sided daily-return p-values. At most one policy per mechanic
may advance. Each later stage requires a hashed advancement lock from the prior
stage. The data periods have been used by other repository campaigns, so even a
four-stage passer is only a near-survivor requiring independent-era replication
and prospective read-only shadowing.

## Authority

This is retrospective research only. It does not authorize model training,
Python prediction serving, EA consumption, demo orders, live orders, broker
actions, account changes, network acquisition, paid data, or Databento use.
