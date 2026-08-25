# V60 Mature Virtual-Health Rank Veto V3

Status: retrospective challenger research only.

V2 exposed a live-state mismatch: its long replay uses mature rolling health,
while the broker account has too few actual executions per source to recreate
that state quickly. The live candidate generator already resolves every
specialist's mechanical candidates causally and reports recent-20 virtual
profit factor before a new entry.

V3 tests one locked, directly observable rule:

1. Apply identically to every specialist with at least 50 earlier completed
   baseline executions in the replay.
2. Use the source's latest 20 mechanically resolved candidate outcomes,
   regardless of whether V60 executed them.
3. Veto only when that causal virtual PF is below `1.0` and the candidate's
   causal rank is below `0.10`.
4. Missing ranks or incomplete health retain the trade.

The full tick replay and all original V2 gates are unchanged. Outcomes were
already exposed before nomination, so a pass remains ineligible for broker
action and must collect new forward evidence.
