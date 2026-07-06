# INDEPENDENT REVIEW — FOREX RESEARCH LANE
Date: 2026-07-03 | Reviewer: Independent (Claude) | Offline only; no runtime touched by this review.
Scope: `forex-research/` runner (12,538 lines, key paths inspected), screen/stress reports, status files.

## VERDICT: METHODOLOGY SOUND — CONFIRM EXPECTED CONCLUSION.
No Forex EA approved; no demo-forward spec; broker-authoritative EURUSD/USDJPY H1+H4 refresh with
measured spread is the correct next evidence requirement. I found no error that changes the verdicts.

## Q1 — Lookahead / joins / dedupe / cost / proxy audit
Inspected the highest-risk paths; all pass:
- **Daily-to-intraday joins are lookahead-safe by construction**: every external context series
  (MOVE, FRED, ETF ratios, CNY, curve) gets `available_utc = observation_utc + 1 day` and is merged
  via `merge_asof(direction="backward")` on availability time. For the USDJPY ASIA-session candidate
  (the classic trap: Asia trades on date D must not see date-D US closes), the gate correctly uses
  the prior US close, with ~3h extra conservatism. Explicit `lag_policy` strings in every context —
  exemplary practice.
- **Signal/entry mechanics causal**: decisions on completed bar `idx`, entry at `idx+1` OPEN, session
  filter applied to the entry bar, one-position (`open_until`), warm-up guard (idx≥260), NaN guards.
- **Conservative intrabar rule**: both-hit bars resolve as SL-first (`SL_ADVERSE_FIRST`).
- **Costs are per-trade and stop-scaled**: `net_r = gross_r − (spread+slippage)/stop_points`, spread
  from measured broker bars historically and from disclosed historical spread PROXIES on the recent
  Yahoo window; slippage varies by exit reason; sub-5-point stops rejected.
- Residual (minor, disclosed): recent Yahoo H1 FX bars are mid-quality proxy data with historical
  spread overlays — correctly labeled "recency triage, not broker-authoritative" everywhere.

## Q2 — Gates
The rejection ladder (sample → net edge → expectancy → top-winner dependence → DD → monthly/weekly
stability → WATCHLIST max) is coherent and correctly caps at WATCHLIST_NEEDS_SECOND_PASS — a single
screen cannot produce a "survivor." Recent-stress gates return `..._CLUE_NOT_SURVIVOR`. One DESIGN
note, not an inconsistency: for sparse session-restricted H4 candidates, the ~1-year recent proxy
window can only ever produce REJECT_LOW_SAMPLE (7–11 trades) — recency triage carries ≈ zero
information for them either way. The fix is the broker refresh (2–3 years, measured spread), which is
exactly what the lane already requests.

## Q3 — Clue classification: CORRECT
All three "best clues" are labeled watchlist/research-only in reports and status files; none is
called a survivor; `No Forex demo-forward spec is prepared` appears where it should. One sharpening:
the USDJPY bond-vol **v1** thresholds (calm −4/−4, stress +6/z 0.5) were iterated after v0 — its
PF 2.06/125-trade historical headline carries within-family selection and should be read as inflated.
The broker-refresh evaluation must test v0 and v1 together, frozen, no new thresholds.

## Q4 — Broker refresh justified? YES
Not by any single candidate, but by the portfolio of three clues that all hinge on the same two gaps:
local bars end ~2025-06/07 and the recent window is proxy-grade. One refresh (EURUSD + USDJPY, H1+H4,
2022→current, measured spread per the existing refresh spec) unblocks all three families at once.
Cheapest possible next evidence. Priority: EURUSD H4 (two clues) then USDJPY H4.

## Q5 — Anything to drop as misleading? Not entirely, but one demotion
- USDJPY carry/session pullback family: already effectively dead (failed second-pass gates AND the
  41-trade recent proxy at PF 0.66) — status says so; keep it dead.
- USDJPY bond-vol v1: HOLD as watchlist despite recent PF 0.32 — 7 trades decide nothing — but demote
  expectations per the v1-tuning note above. Its all-splits-positive history earns the broker-data
  look, nothing more.
- EURUSD rates/dollar and macro-reversal: legitimate watchlist; the 2-trade "confirmation" is
  correctly given no weight.

## Q6 — Status files: ACCURATE
`status_summary.md` reports failures prominently (including the embarrassing ones: −249.96R,
−88.78R), labels clues as clues, carries the staleness caveat, and repeats the no-approval line.
Numbers spot-checked against the underlying reports match. This is what honest status reporting
looks like; no inflation found.

## Q7 — Next highest-value step
1. Execute `FOREX_BROKER_DATA_REFRESH_SPEC_2026_07_03.md` (EURUSD/USDJPY H1+H4, 2022→current,
   measured spread). Read-only data export; within boundaries.
2. Re-run the three clue families on refreshed data with FROZEN v0/v1 definitions (no threshold
   changes — any edit restarts the family's evidence at zero), gates unchanged.
3. If any clue passes the full ladder on broker data including the true recent window, THEN a
   pre-registered second-pass with the standard robustness suite (splits, top-N, rolling windows)
   before any spec drafting.
4. Design tweak: for sparse candidates, replace recent-proxy triage with the refreshed broker recent
   window in the gate itself (per Q2 note).
