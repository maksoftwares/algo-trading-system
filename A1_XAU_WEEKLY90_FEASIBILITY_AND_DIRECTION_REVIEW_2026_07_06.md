# INDEPENDENT REVIEW — 90% POSITIVE WEEKS: FEASIBILITY MATH AND NEXT DIRECTION
Date: 2026-07-06 | Reviewer: Independent (Claude) | Builds on A1_XAU_HYBRID_FRONTIER_WEEKLY_CONDITION_REVIEW_2026_07_06.md (ledger verified there; tail-carried compliance and 29/48 monthly shape established there).

## THE CENTRAL FINDING: the problem is the SHAPE of the profits, not the gates
The math that decides everything: weekly-positive probability is driven by the MEDIAN week, not the
mean. A true +0.5R/trade book at ~18 signals/week with EVENLY distributed profits would run a weekly
Sharpe ≈ 1.4 → ~90–92% green weeks. So the owner's 90% target is NOT mathematically absurd — it is
exactly what a genuine +0.5R book should print IF its expectancy arrives smoothly.
The current hybrid has the right mean (+0.5R nominal) and the wrong shape: its expectancy is
deposited by ~1% of trades (top-38 winners) via the 333-trade H4/D1 engine, in a minority of weeks.
That is why it shows 58.65% green weeks instead of 90%: most weeks never contain a mega-winner, and
H4/D1 losses cluster. **No overlay can fix this; the profit distribution itself must change.**
Direct consequence — the two owner constraints are structurally opposed WITHIN the current book:
W/L ≥ 2.0 is currently achieved by tail-capture; 90% green weeks demands smoothness. The resolution
is not choosing between them; it is converting mega-winners into several medium winners (§3).

## Q1 — Is 90% a valid HARD historical gate? NO — two-tier it.
Even a TRUE 92%-green book fails an observed ≥90%/208-week gate ~14% of the time (binomial). Worse:
iterating variants until one shows ≥90% historically is the most direct form of equity-curve fitting
that exists — the gate would manufacture its own overfit. Recommended structure:
- HISTORICAL gate: green weeks ≥ 70–75%, worst week ≥ −2× avg weekly net, rolling-4-week positive
  ≥ 85%, positive months ≥ 70% — plus all standing core/stress/concentration gates.
- FORWARD-DEMO acceptance gate: rolling green-week ratio ≥ 75–80% during the test, no week beyond
  the historical worst-week bound. 90% remains the ASPIRATION the owner tracks on live demo data —
  where it cannot be curve-fit.

## Q2 — Week definition (same ruling as yesterday, now binding)
Broker-time calendar week (Mon 00:00 through the Friday/Saturday close); CLOSED P&L by EXIT date —
composition ledgers must add exit_time before the anatomy diagnostic runs; zero-trade weeks EXCLUDED
from the green-week ratio (the activity gate polices them separately); floating equity reported as
information only.

## Q3 — Weekly-state overlays: methodologically legal, strategically a trap. REJECTED as primary path.
They are causal (current-week realized P&L is observable), so this is not leakage. But run the
logic against THIS book's shape:
- **Weekly profit-lock** (stop after +$X): buys green weeks by truncating the big weeks — and the
  big weeks ARE the expectancy. Same amputation as the count caps and stop-ceiling, in weekly dress.
- **Weekly max-loss stop**: REDUCES green-week percentage (a −$300 mid-week that would have
  recovered to +$50 becomes permanently red). It improves worst-week only.
- **Post-drawdown source throttling**: the only defensible member (it's loss-responsive sizing by
  another name) — and it belongs inside the geometry grid, not as a standalone overlay pass.
Overlay experiments may be revisited ONLY if the geometry pass fails, at ≤4 preregistered cells.

## Q4 — Order of work: anatomy → geometry v2 → (only then) anything else
1. **Losing-week anatomy FIRST** (their step 1 — APPROVED as specified, plus exit-time fix). It is
   descriptive, costs no selection budget, and will confirm/deny the working hypothesis: red weeks =
   clustered H4/D1 losses + absent mega-winner. Required additions: green-week anatomy too (what %
   of green weeks contain a top-1% winner — this measures tail-dependence of the weekly shape
   directly), and per-week signal-count distribution.
2. **Geometry v2 grid — the 24-cell grid from yesterday's review stands, minus the burned
   stop-ceiling cell, PLUS the one idea aimed exactly at profit redistribution: an H4/D1 PARTIAL
   LADDER** {none; bank 1/3 at +2R, 1/3 at +4R, run the rest; bank 1/2 at +3R, run the rest}.
   Rationale: the ladder converts each rare mega-win into several medium wins deposited across
   days/weeks — raising the MEDIAN week (green-week %) while roughly preserving total expectancy and
   keeping realized W/L high because banked partials are still ≥2R multiples. This is the only
   mechanism on the table that attacks the §1 shape problem at its root. (Precedent: the split-entry
   partial structure was the only exit intervention that ever beat its baseline in this project.)
   Judged per cell on the RECOMPOSED book: WR / W-L post-stress / active% / green-week% / worst week
   / worst month / last-12 / June-2026 / ex-top-1% rows. One pass, hash-logged prereg, then frozen.
3. The stop-ceiling one-iteration was handled correctly (prereg → honored rejection when W/L broke)
   — and its result is informative, not wasted: it proved loss-shape improves the moment H4/D1 risk
   is bounded. Geometry v2 must find the version that pays for that bounding out of the tail (via
   the ladder) instead of out of the W/L ratio.

## Q5 — Cell budget before it's overfit
Geometry v2: ≤ 24 recomposed cells TOTAL (including the ladder variants), one declared pass. The
anatomy diagnostic is unlimited (descriptive) but may only motivate preregistered cells, never
direct picks. Weekly overlays if ever: ≤ 4. Cumulative rule: after geometry v2, the H4/D1 family is
FROZEN regardless of outcome — further XAU work would move to the smooth-book family (below).

## Q6 — Minimum gates before the next review token
(a) exit_time present in all composition ledgers; (b) anatomy report (red AND green week anatomy);
(c) geometry v2 grid declared+hash-logged BEFORE any run; (d) results as one full table, all cells,
with ex-top-1%/2% rows and stress column; (e) any "progress" claim must beat baseline green-week%
AND hold WR ≥ 50% / W-L ≥ 2.0 AFTER +$0.30/ticket stress. Anything less: no review.

## Q7 — The missing path to 90% (if geometry v2 falls short)
A structurally smooth SECOND book, stacked at portfolio level — not more surgery on this one. The
natural candidates, in order: gold/silver relative-value (the one family whose native distribution
is many-small-wins/weekly-smooth — already approved in the four-family plan and untouched), and
book-level volatility targeting over the combined portfolio. Honesty note for the owner: stacking a
smooth book dilutes composed W/L below 2.0 almost by arithmetic necessity — at that point the owner
choice becomes explicit: EITHER 2.0 W/L on the aggressive book alone, OR 90% green weeks on the
blended portfolio, with both books individually honest. The constraint set as currently written is
satisfiable by one book only if geometry v2's ladder works; otherwise it needs two books and a
relaxation of where W/L is measured.

## VERDICT
- Methodology since last review: SOUND (prereg honored, rejection honored, honest reporting).
- Proposed plan: APPROVED WITH MODIFICATIONS — anatomy first (with green-week anatomy + exit-time
  fix), then geometry v2 including the partial-ladder cells; weekly-state overlays demoted to
  last-resort with the §3 reasoning; 90% split into historical 70–75% + forward aspiration.
- For the owner, one sentence: your 90% target is what a genuinely smooth +0.5R book would print —
  we have the +0.5R but in the wrong shape, and the next iteration is specifically designed to
  reshape it; if it cannot, the honest route to 90% weeks is a two-book portfolio and a decision
  about which book carries the 2.0 W/L requirement.
