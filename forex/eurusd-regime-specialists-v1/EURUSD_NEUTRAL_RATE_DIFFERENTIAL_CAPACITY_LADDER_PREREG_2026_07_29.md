# EURUSD Neutral rate-differential capacity ladder preregistration

The exact five-basis-point census failed only because 2026 H1 contained four
candidates rather than the frozen minimum of five. It loaded no EURUSD price,
return, oracle, or P&L.

This one adaptive successor is therefore restricted to source capacity. It
tests thresholds of 5, 4, and 3 basis points in descending order and selects
the highest threshold passing every unchanged parent capacity gate. The
official sources, two-calendar-day lag, Neutral 00:00 UTC clock, direction
mapping, one-candidate-per-date rule, windows, and gates cannot change.

The ladder is not allowed to inspect profitability. If a threshold passes, its
candidate manifest is hashed and only a separately preregistered execution
contract may open EURUSD paths. If none passes, the rate-differential family
stops without P&L. No later threshold selection is allowed.
