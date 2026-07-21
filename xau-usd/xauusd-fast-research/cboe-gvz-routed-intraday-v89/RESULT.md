# V89 Result

Decision: `V89_DISCOVERY_FAIL_TERMINAL`

The official Cboe GVZ history passed its source audit and all 1,000 policies were
locked before any post-entry quote was opened. Discovery then rejected every
policy. Replication, development 2, confirmation, and final outcomes remain
sealed.

## Evidence

- Densest policy: `663` trades over `652` calendar weekdays (`1.0169/day`),
  stress PF `0.5505`, stress net `-166.20R`.
- Best stress PF among policies with at least `220` trades: `0.7954`, with
  `224` trades (`0.3436/day`) and stress net `-31.97R`.
- Only `9/1000` policies had positive stress net and only `4/1000` reached PF
  `1.20`; none met the density, stability, drawdown, winner-removal, segment, and
  significance gates together.
- Smallest unadjusted weekly p-value: `0.10933`; smallest FDR q-value: `1.0`.
- No policy passed all gates even when the FDR check is temporarily excluded.

## Terminal Rule

V89 may not be mirrored, retuned, re-sessioned, re-exited, or quota-filled on
these outcomes. The evidence rejects prior-day GVZ level, change, and
implied-minus-realized premium as direct routers for these completed H1 breakout
and reversion geometries. V59/V60 remain byte-identical and outside this result.

No model, EA, demo, live, payment, Databento, or broker authority is granted.
