# Review — XAUUSD Observer Lessons & Improvement Plan (2026-06-16)

Reviewer: Claude. Scope: XAUUSD only. Verdict on `XAUUSD_OBSERVER_LESSONS_AND_IMPROVEMENT_PLAN_2026_06_16.md`.

## VERDICT

**Endorse the plan's *method and direction*; do not trust its cluster *magnitudes* yet.**

The plan is unusually disciplined — it protects the core, refuses blanket bans, applies exit
rules to winners as well as losers, and demands forward proof before any runtime change. That
framework is right and I support it. But the numbers it reasons from are inflated by two effects
I verified on the broker table, so the *sizes* of the edges (and the case for some "protected"
clusters) are overstated. Fix the evidence first, then the staged plan is sound.

Three things I verified that change the picture:

1. **Duplication ~doubles the breakout family.** `breakout_retest` + `swing_breakout_retest_v0`
   = 149 raw trades summing to +1,507 AED — but they are **97 unique signals worth +769** once
   you collapse the stacked clones (~1.5× inflation; swing is largely breakout's co-fire). So the
   real breakout edge is ≈ **+769, not the ~+1,805** implied by listing the two separately, and the
   "breakout family +2,353" / "strong list +2,701" counterfactuals are inflated accordingly.
2. **`p2weakness_br_v1` is not an edge — it's a duplication artifact.** Of its 10 trades, **9 are
   duplicates; 1 is unique. Deduped PnL = −14.4 AED**, not +548. It must not be on the protected
   or "strong" list.
3. **The "strongest cluster in the book," SELL-evening (+~2,034), is two days.** June 9 (+1,727)
   and June 10 (+1,719) carry it; remove the single top day and it falls to **+307**, and on the
   actual crash days (June 11 −799, June 12 −1,111) SELL-evening *lost*. It is a few-day artifact,
   not a stable edge.

## ANSWERS TO THE SEVEN QUESTIONS

**1. Round-family quarantine first? — AGREE.** It is the most consistent, mechanism-understood,
broad-based drag (round_number −1,291 + symbol_normalized −949 ≈ −2,240, negative in every
session), and we have established repeatedly that the round entry has no edge. Quarantine
(observer-only, reversible — *not* delete) is the right first shadow test. Caveat: the "+2,889
improvement" is retrospective *and* duplication-inflated; the honest expectation is "stop a ~−2,240
forward bleed," not "+2,889 of new profit." Recompute the benefit on deduped signals.

**2. Direction/session guard better than a blanket ban? — AGREE on the principle, DISAGREE with
the specifics.** A blanket session ban is too blunt (same session is good one direction, bad the
other — evening SELL +2,406 vs evening BUY −893). But the specific direction×session edges are
almost certainly **this fortnight's trend**, not structure: gold fell, so SELL won — and we saw the
mirror live on June 15 (an up-day) where BUY won and SELL lost. So the guard must be a **dynamic
trend-alignment guard** ("don't take trades against the prevailing H1/H4 trend"), *not* a static
"block BUY evening / always protect SELL evening." A fixed direction×session rule overfits to which
way gold happened to move and will be backwards on the next up-trending fortnight.

**3. Which good clusters to protect? — The breakout family, and essentially only that.** Protect
`breakout_retest` and `swing_breakout_retest_v0` (treat them as **one** edge — the breakout entry —
since ~1.5× of their combined PnL is the same signal duplicated). Protect it in its genuinely strong
context (evening, and to a lesser extent night). **Do NOT protect `p2weakness_br_v1` (dedup −14,
artifact) or `session_extreme_retest_v0_repair_v1` (12 trades, an overfit SHORT-only repair lane).**
Elevating those to "protected" locks in noise. "SELL-evening / BUY-night" are not clusters to
protect — they're period-trend snapshots.

**4. Exact shadow rules to test first (in order):**
- **Rule 0 — deduplicate the evidence.** Recompute every cluster and counterfactual on unique
  signals before anything else. This is the prerequisite; the current magnitudes are not decision-grade.
- **Rule 1 — round-family quarantine (observer-only).** Pre-register: does removing round improve
  the *deduped* forward result without harming the breakout family?
- **Rule 2 — dynamic trend-alignment guard (shadow).** Suppress trades against the higher-timeframe
  trend. NOT static direction×session.
- **Rule 3 — exit protection (shadow/backtest), see Q5.**
Skip a static direction×session rule entirely; it is the overfit version of Rule 2.

**5. Exit-protection rules + avoiding curve-fit.** Test **one or two pre-chosen** rules, not the
whole menu: `BE at +0.5R` and `partial at +1.0R`. Anti-curve-fit guards: (a) apply to *all* trades,
winners included (the plan got this right); (b) **pre-register the threshold — do not grid-search
0.5/0.75/1.0 and keep the best**, that is overfitting; (c) **measure the cost explicitly** — the
MFE/MAE data shows winners' average adverse excursion is 0.46R, which sits right under the 0.5R
breakeven trigger, so a BE rule will clip a meaningful share of winners. Required output: of trades
that reached +0.5R, how many then retraced to entry and would have hit target anyway — i.e. the *net*
of losses-saved minus winners-clipped, not just the 32% give-back number; (d) confirm the net holds
with the best day removed and forward, not just in-sample.

**6. Evidence required before runtime promotion.** Keep the plan's Step-5 list, and add four hard
gates it is missing: (i) computed on **deduped** signals and **real broker fills** (not replay);
(ii) **net benefit survives removing the best 1–2 days** (the June-10 / June-9-10 trap that just
sank both the "profitable hours" and the cost gate); (iii) confirmed **forward** over a stated
minimum (≥3–4 weeks / ≥N independent days / ≥~30 affected trades), not just retrospectively;
(iv) **protected breakout clusters are not harmed.** And the improvement must be clearly outside
noise, not marginal.

**7. Hidden risks / alternative explanations.**
- **Period-trend masquerading as edge (biggest).** Every direction and direction×session number is
  contingent on gold's June 1–16 path (down, then partial recovery). SELL +1,878 / BUY −1,228 is
  "gold fell this fortnight," not "sell gold." Different fortnight → flips.
- **Duplication inflation** (verified): breakout family ~1.5×, p2weakness fabricated. All cluster
  PnLs and counterfactuals overstated until deduped.
- **Few-day dominance** (verified): SELL-evening is two days; expect the same fragility in other clusters.
- **Small samples:** p2weakness (10), session-repair (12), best EA/session cells (8–25) — not significant.
- **Multiple comparisons:** slicing EA × direction × session manufactures extreme cells by chance;
  the "strongest cluster" is partly selection.
- **Retrospective counterfactuals always flatter** — removing realized losers in hindsight guarantees a better past.
- **Exit-rule winner-clipping** — the give-back stat ignores the cost of stopping winners early.

## DISAGREEMENTS (explicit)
1. Treating direction×session clusters as stable edges. They are period-trend; use a dynamic
   trend-aligned guard instead.
2. Listing `p2weakness_br_v1` and `session_extreme_repair` as protected/"strong." Deduped, p2weakness
   is −14; both are tiny-sample. Demote to "watch, unproven."
3. Reasoning from raw (stacked) cluster PnLs. Dedup first; the breakout edge is ~+769, not ~+1,805.
4. The "+2,889 from removing round" headline. Inflated and retrospective; reframe as "stop a ~−2,240 bleed."

## NO-GO CONDITIONS (block promotion if any are true)
- The rule's benefit disappears when the best 1–2 days are removed.
- The benefit exists only retrospectively, not forward in shadow on real fills.
- It removes or harms protected breakout-family evening/night trades to manufacture PnL.
- It relies on a static long/short or session bias rather than dynamic trend state.
- The supporting cluster is < ~30 deduped trades or spans < ~5 independent days.
- The "edge" is really the period's trend (test: does it hold on both up and down days?).

## EXACT NEXT IMPLEMENTATION STEPS
1. **Re-cut the evidence on deduped, real-fill signals** (one row per unique signal). Reissue the
   cluster, counterfactual, and direction×session tables with per-day and best-day-removed columns.
   Nothing is decision-grade until this exists.
2. **Stand up the round-family quarantine as observer-only** (log would-be round outcomes; place no
   round trades). Pre-register the success bar. Reversible.
3. **Stand up a dynamic trend-alignment guard in shadow** (log-only): tag each signal as with/against
   the H1/H4 trend and record outcomes — to test the *real* version of the direction lesson.
4. **Backtest + shadow one or two pre-chosen exit rules** (BE +0.5R, partial +1R) on the full
   winner+loser path data, reporting net effect and winners-clipped.
5. **Run the protected-cluster audit** as a standing check on every proposed filter.
6. Change **no runtime EA** until a rule clears all the gates in Q6 with owner + reviewer sign-off.

## One-line summary
Right plan, wrong-sized numbers: quarantine round (yes), make the direction rule *dynamic* not
static, drop p2weakness/session-repair from "protected," and rebuild every figure on deduped,
day-stress-tested, real-fill data before trusting a single magnitude.
