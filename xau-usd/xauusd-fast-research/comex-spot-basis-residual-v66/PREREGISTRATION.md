# V66 COMEX-Spot Basis Residual

V66 tests a roll-safe absolute futures-minus-spot basis event clock. Earlier
COMEX campaigns tested return gaps, flow sequences, auction profiles, VWAP, and
lead/lag. They did not retain raw instrument identity and therefore prohibited
absolute basis features. V66 restores that identity from immutable DBN metadata.

At each synchronized completed M5 bar, basis is `GC close - XAU mid close`.
Within each raw COMEX instrument, the causal center and MAD use only prior bars.
A candidate requires an extreme residual, same-session widening, and a futures-
driven return gap. `CATCHUP` trades spot toward futures; `FADE` tests the exact
opposite action. Both actions are registered before outcomes are opened.

The bounded manifest contains 288 variants. Selection uses development-1,
development-2, and confirmation ending before `2025-07-01`. The final year is
not loaded by the discovery runner. At most one unchanged policy may be locked
before a separate final-year run.

Entries occur on the first contiguous M5 bar after the completed signal. Longs
enter Ask and exit Bid; shorts enter Bid and exit Ask. Gap stops use the worse
open, same-bar ambiguity is stop-first, and ticket, holding, spread, and 0.05R
slippage stress are charged. One open trade, a 30-minute event cooldown, and two
entries per UTC day prevent repeated tickets from being counted as frequency.

This is retrospective research only. It authorizes no network request, paid
data, prediction service, EA, demo/live order, broker action, or change to the
frozen V59/V60 portfolio.
