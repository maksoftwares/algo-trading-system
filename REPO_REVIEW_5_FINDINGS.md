# REPO_REVIEW_5_FINDINGS

**Reviewer:** Claude (independent technical reviewer)
**Date:** 2026-05-23 (late)
**Repo:** `maksoftwares/algo-trading-system` @ `main`
**Commits since Review #4:** 8 (66 → 74)
**Scope:** Six new candidates were evaluated since Review #4. Three are provisional passes. The team explicitly labels all three as same-family. This review tests whether that label is accurate and what the empirical pattern says about long-term survival design.

---

## Headline

**Rating: 8.75 / 10** (unchanged from Review #4).

I considered moving it up. The team shipped 6 new candidate evaluations in ~12 hours, including 3 that passed the 9-cell matrix, all three honestly labeled as same-family despite being marketable as diversification. D2 was re-run against 27 candidates and the result actually **improved** (max pairwise SPA p moved 0.0336 → 0.0308). The rejected-candidate audit grew to 24 entries with zero frequency-only failures, further confirming the gates are not the constraint.

I held the rating at 8.75 because the new evidence reinforces — not relieves — the load-bearing weakness from Review #4:

**Of 6 new candidate attempts, the 3 that passed are all level-and-pullback mechanics on M5. The 3 that failed include the only candidates that tried to operate in different timeframes or different mechanic families.** Edge defensibility and long-term survival sub-scores cannot move on this evidence.

Two new findings (N4, N5) follow. One Review #4 soft concern (S1) is downgraded.

---

## What Closed Since Review #4

### D2 Reality Check, 27-candidate universe — **HOLDS, AND IMPROVES**

| Universe | White p | Max SPA p | Iterations |
|---:|---:|---:|---:|
| 3 candidates (pre R#3) | 0.0200 | 0.0234 | 5000 |
| 18 candidates (R#3 rerun) | 0.0200 | 0.0336 | 5000 |
| **27 candidates (R#5)** | **0.0200** | **0.0308** | **5000** |

Counter-intuitive but explainable: adding clearly-losing candidates (liquidity_sweep_continuation: PF<1.0 in all 9 cells; symbol_round_sweep_reversal: 50.46% max DD; etc.) does not inflate the multiple-comparison correction the way adding near-winners would. `breakout_retest`'s relative dominance widened, not narrowed.

**Practical effect:** the R#4 soft concern S1 ("D2 SPA p drifting toward α=0.05 as universe grows") is empirically wrong. **Downgrade S1 to closed.** The team can author more clearly-rejected hypotheses without paying a D2 penalty. The only thing that would close p toward 0.05 is another *near-winner*, and none have appeared.

### Rejected-candidate gate audit, n=24 — **CONFIRMS R#4 closure**

| Universe size | n | sample_size fails | activity fails | multi_cell fails | concentration fails | frequency-only fails |
|---:|---:|---:|---:|---:|---:|---:|
| R#4 (n=17) | 17 | 4 (24%) | 4 (24%) | 13 (76%) | 15 (88%) | **0** |
| R#5 (n=24) | 24 | 4 (17%) | — | 22 (92%) | — | **0** |

Per agent.md L113: "audited 24 rejected/research candidates; 4 had sample-size failures, 22 had multi-cell expectancy failures, and 0 were frequency-only failures."

The signal is robust at larger n. My original §4 frequency-bias hypothesis is properly retired.

### Three new provisional passes — **CORRECTLY LABELED same-family**

| Candidate | Status | Matrix PF range | Decile | Multisymbol | Family attribution |
|---|---|---|---|---|---|
| `round_number_retest_v0` | PROVISIONAL_PASS_PENDING_GATE9 | 1.351–1.560 (9/9) | 10/10 | XAU-only (EUR 0 trades, JPY PF 1.435) | Same-family (level + break + retest) |
| `symbol_normalized_round_retest_v0` | PROVISIONAL_PASS_PENDING_GATE9 | 1.351–1.560 (9/9) | 10/10 PF 1.371–1.558 | **Better:** EUR PF 1.298, JPY PF 1.559 | Same-family |
| `session_extreme_retest_v0` | PROVISIONAL_PASS_PENDING_GATE9 | 1.328–1.596 (9/9) | 10/10 PF 1.321–1.657 | P95 cost: EUR 1.181, JPY 1.236 | Same-family |

The team labels each one explicitly: *"This is still same-family breakout-retest logic, so continue searching for a genuinely independent behavior family."* (agent.md L184, L187). This is the correct call. See N5 below for why the *pattern* is more important than any individual label.

---

## What Did NOT Move

| R#4 finding | Status | Note |
|---|---|---|
| V1 (measured cost still assumed) | Slight progress | 6390 → 6495 spread rows, still 2 of 5 days |
| V6 (5-day soak) | Flat | 56 rows, 8.26% — unchanged. Weekend pause |
| N1 (continuous-streak soak gate) | Not adopted | No `soak_longest_streak_hours` field in PHASE1_STATUS_SUMMARY.json |
| N2 (+0.10R threshold defended or raised) | Not adopted | Still +0.10R, still no MDE justification |
| N3 (H4+ hypothesis in backlog) | Attempted, missed | See N4 below |

---

## New Findings

### N4 — `daily_pivot_reclaim_v0` was branded as the diversification candidate. The implementation is not diversification. **(Long-Term Survival)**

The hypothesis file says (line 15): *"It is not a breakout-retest, trend-pullback, session-range breakout, liquidity-sweep high/low, VWAP, or compression strategy."* The reference level is the previous UTC day's classic HLC pivot — sounds like swing.

The implementation:

- **Market and timeframe (line 19):** "XAUUSD with M5 entries and M5 trigger candles."
- **Eligible window (line 20):** "completed M5 bars whose bar start time is from 07:00 UTC through 16:55 UTC."
- **Expected trade count (line 6):** 120–500 per year.
- **Realized trade count:** 486–558 per 9-cell block over the matrix horizon — i.e., ~150–180 trades per year. Matches the expected band.
- **Cost-sensitivity profile:** identical to other M5 intraday strategies. Spread/slippage in points per round-turn dominates the small 1.5R target.

**This is an intraday M5 strategy that uses a D1-derived reference level.** Its sensitivity to broker cost, its execution-quality requirements, and its decision frequency are intraday. The fact that the *level* is computed from D1 OHLC does not give it any cost-noise advantage over `breakout_retest`.

It was also REJECTED first-pass (0/9 cells reached PF ≥ 1.30). So the question of whether it would have been diversification is moot — but it would not have been, regardless.

**The R#4 N3 finding stands. The team's "diversify timeframe" attempt produced another intraday cost-sensitive strategy.**

**Recommend** the team add a hard rule before authoring the next candidate: **a candidate qualifies as timeframe-diversifying only if its expected median hold time exceeds 24 hours and its expected trade count is below 100 per year.** Track this as a mandatory field in every new hypothesis file:

```
expected_median_hold_bars_M5: ___
expected_median_hold_hours: ___
expected_decisions_per_week: ___
```

Then re-evaluate whether the *next* candidate authored actually meets the diversification claim, instead of inferring family from the reference-level source.

### N5 — Three provisional passes all level-and-pullback is empirical, not coincidence. **(Long-Term Survival)**

Of the 6 candidates tested since R#4:

| Mechanic family | Candidates tried | Passes |
|---|---:|---:|
| Level-and-pullback (breakout-retest variants) | 3 | **3** |
| Genuinely different (reversal, continuation off sweeps, daily pivot reaction) | 3 | **0** |

Plus the existing approved: `breakout_retest` (level-and-pullback) and `swing_breakout_retest_v0` (level-and-pullback at H1).

**Five of five passes — and provisional passes — in this project are level-and-pullback.**

There are three explanations and they have different consequences:

| Hypothesis | Implication if true | How to falsify |
|---|---|---|
| (a) Level-and-pullback is the only real edge in XAUUSD intraday | One-family portfolio is the correct answer; capital should reflect that | Find one non-level edge that passes |
| (b) The 9-cell matrix gates select for level-and-pullback specifically | The team's research engine has a hidden bias toward this mechanic; other edges exist but the gates don't see them | Author a candidate that intentionally violates level-and-pullback structure but uses a valid edge thesis (e.g., COT positioning divergence, intermarket correlation breakdown, volatility-regime breadth) and test it through the same gates |
| (c) The team's hypothesis-authoring style converges on level-and-pullback because that's the trading instinct of the author(s) | Strategic prior. Diversification will not come from this team without a deliberate constraint change | Have a non-trader (or a different trader with different instincts) author the next 3 candidates |

These are not mutually exclusive. Likely (a) and (c) both contribute, with (b) possibly contributing at the margin.

**Recommend** the team explicitly rank these three hypotheses by their own credence and pick one to test. The current research backlog adds level-and-pullback variants indefinitely; without a deliberate exit from this mechanic family, Phase 2 will go live with five level-and-pullback candidates and the team's earlier honest acknowledgment ("not diversification") will quietly become "five-expert portfolio" in marketing language.

A concrete forcing function:

> **No new same-family candidate is authored until at least one genuinely-non-level candidate has been registered, hash-locked, and result-producing run completed.**

This costs the team nothing (round_number_retest, symbol_normalized_round_retest, and session_extreme_retest are already passed and parked). It forces the next candidate to be a real diversification attempt.

---

## Soft Concerns Updated

### S1 — D2 sequential-testing concern — **CLOSED**

Adding 9 more clearly-rejected candidates moved max SPA p from 0.0336 → 0.0308 (improved). The mathematical mechanism is right (Holm-like corrections amplify weak alternatives more than rejected ones). Empirically, the team can grow the universe without paying a D2 penalty, as long as the additions are real-edge tests rather than near-winners.

### S2 — Single-execution-eligible expert in Phase 2 paper — **CARRY-FORWARD**

Still applies. Same-family count is now likely to be 5 (breakout_retest, swing_breakout_retest_v0, plus 3 provisional passes that may be promoted). Running 5 same-family experts in paper would be a telemetry confound disaster. Phase 2 paper should ship with **one** execution-eligible expert and the rest as observer-only.

---

## Sub-Score Breakdown

| Dimension | R#3 | R#4 | R#5 | Trend | Note |
|---|---:|---:|---:|---:|---|
| Plan quality | 9.0 | 9.0 | 9.0 | flat | Comprehensive |
| Edge defensibility | 5.5 | 5.5 | 5.5 | flat | Still assumed cost. New same-family passes don't move this. |
| Execution discipline | 9.5 | 9.5 | 9.5 | flat | Continues |
| Operational maturity | 8.5 | 9.0 | 9.0 | flat | Dashboard + ledger + protocol all shipped |
| Code quality (inferred) | 8.0 | 8.0 | 8.0 | flat | — |
| Long-term survival design | 6.0 | 6.5 | 6.5 | flat | Honest labelling is good; mechanic concentration is bad. Net flat. |
| Validation rigor | 8.0 | 8.5 | 8.75 | up | D2 held at 27-candidate scale; audit n grew with same result |
| **Composite** | **8.5** | **8.75** | **8.75** | flat | |

Validation rigor moves up +0.25. The other sub-scores hold.

---

## Pre-Phase-2 Gating Summary

Six things should clear before Phase 2 paper is authorized. Three are wall-clock dependent (cannot accelerate). Three are paperwork.

| # | Item | Type | Status |
|---:|---|---|---|
| 1 | Measured cost ≥ 5 days + revalidation | Wall-clock | 2/5 days |
| 2 | Continuous soak streak ≥ 72 h | Wall-clock | Not tracked |
| 3 | Five-day cumulative soak target | Wall-clock | 8.26% |
| 4 | +0.10R threshold defended or raised | Paperwork | Not addressed |
| 5 | Phase 2 paper limited to 1 execution-eligible expert | Paperwork | Not addressed |
| 6 | Forcing function for non-level-family next candidate | Paperwork | Not addressed (new in this review) |

Items 4, 5, 6 are 1-day commitments. None of them require new code. They are governance choices.

---

## Closing Note

This review covers a 12-hour window in which the team shipped six candidate evaluations, two new policy documents (cost measurement protocol, single-edge risk plan in the prior cycle), and re-ran D2 against an expanded universe. The discipline-per-hour metric continues to be exceptional.

The honest summary is this: **the project's process is at a 9+. The project's edge is at a 5.5.** Process cannot patch that. Only measured cost data (incoming) or a genuinely non-level-family edge (not incoming) can. The team knows this — agent.md L184 and L187 explicitly say so — but the *next-candidate-authored* pattern keeps producing the same mechanic family. N5 names the question. The team should pick which of (a)(b)(c) they believe and act accordingly.

— End of Review #5
