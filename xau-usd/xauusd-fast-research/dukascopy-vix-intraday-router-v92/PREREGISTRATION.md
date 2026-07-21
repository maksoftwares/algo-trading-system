# V92 Dukascopy Intraday VIX Router Preregistration

## Purpose

V60 already passed the one-trade-per-weekday milestone. V92 is not another
attempt to prove that result. It asks whether free intraday `VOL.IDX/USD` ticks
provide enough independent information to add the opportunities required for at
least two combined XAUUSD trades per weekday in every modern window.

V92 is additive beside byte-identical V59/V60. It cannot remove, resize, delay,
or relabel any accepted V59 trade.

## Causality

- Only an immutable, completed Dukascopy VIX M5 bar may be used.
- A VIX M5 bar is available only at its bar-end timestamp.
- VIX and XAUUSD H1 features use completed source bars and backward-only rolling
  baselines. Missing VIX hours are not forward-filled.
- The final VIX M5 update must be no more than 15 minutes old at the H1
  decision; older sparse-hour states are unavailable.
- Entry is the first contiguous XAUUSD M5 quote after the completed H1 decision,
  at Ask for long and Bid for short.
- Same-bar stop/target ambiguity is stop-first. Spread, ticket cost, holding
  cost, and 0.05R additional stress slippage are charged.

## Registered Mechanics

1. `VIX_SHOCK_BREAKOUT`: an intraday VIX shock routes a completed XAU channel
   break in the XAU break direction.
2. `VIX_SAFE_HAVEN_CATCHUP`: a directional VIX move routes XAU catch-up after a
   weak or opposite prior XAU impulse and a completed confirming bar.
3. `VIX_DIVERGENCE_REJECTION`: VIX direction and prior XAU displacement diverge;
   a completed XAU rejection trades toward the VIX-implied direction.
4. `VIX_NORMALIZATION_TREND`: VIX declines after an elevated intraday state while
   completed XAU trend structure supplies either long or short direction.
5. `VIX_XAU_COEXPANSION`: unusually large absolute VIX movement and a completed
   XAU channel break route the XAU break direction.

Exactly 200 deterministic, coverage-eligible policies per mechanic are admitted
for attempts `123001` through `124000`. Coverage selection may inspect source
features, candidate timestamps, direction, and density only. It may not inspect
entry prices, exits, MAE, MFE, P&L, or any post-decision quote.

At most one London and one New York trade per policy per UTC date are allowed.
Splitting tickets and repeated entries inside the same session slot are forbidden.

## Sequential Windows

1. Discovery: January 2023 through June 2024.
2. Confirmation: July 2024 through June 2025.
3. Final: July 2025 through June 2026.

Only Discovery may open after source and policy hashes are locked. A later stage
remains sealed unless the prior stage writes a hash-bound advancement naming an
unchanged policy. Benjamini-Hochberg correction applies to every policy entering
each stage, with zero-trade calendar weeks retained.

Each policy must produce at least 0.20 standalone trades per weekday and pass
its economic, stability, winner-removal, drawdown, and full-family BH FDR gates.
The full missing frequency is a portfolio requirement, not a demand that one
specialist manufacture every opportunity. Up to one unchanged policy per
mechanic may advance. The surviving ensemble must collectively supply enough
risk-routed trades to lift byte-identical V59/V60 to at least two trades per
weekday in every required window.

The shared router keeps every V59/V60 trade unchanged. V92 candidates use fixed
attempt-number priority, duplicate entry timestamps are rejected, and no more
than two V92 entries are accepted per UTC date. At each decision, the frozen
two-add-on and USD 45 concurrent initial-risk limits are applied using only
positions then known to be open. The completed shared history must also remain
inside those limits after every later V59 entry, reach two combined trades per
weekday in each required window, retain combined stress PF of at least 1.50,
keep absolute daily P&L correlation at or below 0.50, and keep buffered floating
drawdown at or below USD 449.7675.

Failure is terminal for the exposed policy or family. No mirror, threshold,
session, stop, target, hold, cost, or quota rescue is allowed on opened outcomes.

No payment, Databento request, model training, Python serving, EA consumption,
demo order, live order, or broker action is authorized.
