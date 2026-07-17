# XAUUSD Post-Boundary Specialist Campaign Status

Date: `2026-07-17`

## Current Decision

There are still zero execution-eligible new specialists and one credible
near-survivor, frozen R1. Four additional locked campaigns were completed after
the prior information-boundary report. None passed its first chronological
economic gate. COMEX exam outcomes remained sealed, and the adaptive campaign
also kept each later stage unopened after the preceding failure.

| Campaign | Mechanical candidates | Opened labels | Selected trades | Survivors |
|---|---:|---:|---:|---:|
| COMEX auction profile | 613 | 80 | 70 | 0 |
| COMEX initial balance | 943 | 133 | 122 | 0 |
| COMEX session swing | 55 | 30 | 30 | 0 |
| Adaptive H4 price rankers | 3,561 | 1,877 | 97 | 0 |

The COMEX campaigns tested prior-value acceptance and failure, opening-balance
expansion and failure, POC migration, completed-session trend carry, and
balanced excess reversal. The adaptive campaign tested trend continuation,
post-shock reversal, and range breakout with a model retrained on trailing
history before each six-month block. These failures cannot be repaired by
same-version threshold changes or by inverting losing trades after inspection.

## R1 Prospective State

The exact frozen R1 observer is active on demo account `1033669`. It reads MT5,
records every completed H4 decision, and has no order method or broker
authority. The current state is `ABSTAIN_D1_TREND`; no prospective candidate has
occurred yet. Historical R1 remains a near-survivor because development had 28
trades against a frozen minimum of 30 while all economic, drawdown, and
concentration checks passed.

## Data Boundary

The zero-payment Databento download is `GC.v.0`, one volume-based continuous
contract. It contains trades but no cross-contract curve and no order-book
depth. It therefore cannot support front/second spread, roll-pressure, MBP-10,
or MBO specialists. Creating additional identities for promotional credit is
not authorized, and paid acquisition is not authorized.

The synchronized Dukascopy dollar and Treasury cache has already been tested as
direct M15 lead, dislocation, fixed H4 confluence, and broader cross-asset
residual information. Repackaging it into another model would not create an
independent information source.

## Next Defensible Inputs

At least one of the following is required for a genuinely new historical
campaign:

1. Zero-payment primary COMEX depth with auditable timestamps and sufficient
   history, including MBP-10 or MBO.
2. A causal historical gold-options surface containing implied volatility,
   skew, term structure, and publication timestamps.
3. Synchronized executable XAUUSD bid/ask quotes from additional brokers for
   venue-dislocation and execution-quality specialists.
4. More prospective frozen-R1 candidates and outcomes from the active shadow
   runtime.
5. An objective change that permits additional instruments or accepts the
   empirically supported lower XAUUSD frequency.

MT5 backtests and observer logs remain useful for producing labels and checking
execution parity, but replaying more years of the same price information does
not create a new source of edge. No ML execution training should begin by
labeling rejected candidates as good trades.

## Authorization

- Python prediction: not authorized.
- EA consumption: not authorized.
- Demo or live orders from these campaigns: not authorized.
- Paid Databento acquisition: not authorized.
