# Strict Review — A3 Soft Retest V2 Candidate (`A3_SQ_SOFT_RETEST_W15_B45_C60_RCM05_V2`) — 2026-06-18

Reviewer: Claude. Scope: XAUUSD, A3 `1033669`, **paused**. Repo/shadow-only review of commit chain
`3a42a4c…4ea352f`. I read `run_a3_signal_quality_extended_discovery.py` and the base
`run_a3_signal_quality_offline_discovery.py` in full.

## Verdict: **BUILD_ONLY** — observer/shadow only, **after** two blockers are fixed. NOT shadow-attach-ready, NOT demo-ready.
The candidate is methodologically *mostly* clean (no hard lookahead), but the headline numbers are
**gross of cost** and **in-sample threshold-selected**, so they are not evidence of a real net edge. It's a
legitimate *hypothesis to carry into forward validation*, not a result. Two blockers must be fixed before any
MQL build, and the discovery/June numbers must be restated as non-evidence.

## Blockers (fix before proceeding)
**B1 — Backtest is GROSS of cost (the big one).** In `simulate_trade`, `final_r` is **always exactly +1.5
or −1.0**; spread/slippage are never applied. `cost_r` is computed and logged but **not deducted** from any
PnL/PF/expectancy. So every reported figure ignores ~0.15–0.25R/trade of real XAUUSD cost. This is almost
certainly why the **B0 baseline shows +0.14R / PF 1.25 in backtest while the live A3 breakout lost money** —
live pays the spread, this model doesn't. Net of cost, B0 is ~breakeven-to-negative, and V2's +0.40R gross is
materially lower net. **Re-run all metrics with cost_r applied to net R, and re-check the eligibility gate net.**
Until then the gates ("PF after measured spread/cost", expectancy) are simply **not evaluated**.

**B2 — Threshold-selection overfit.** The name encodes four tuned parameters (window **15**, body **0.45**,
close-loc **0.60**, retest margin **0.05 ATR**) — values sitting precisely between `F_RETEST_LIGHT`
(0.40/0.65/10) and strict V1 (0.60/0.80/5). These were chosen on the Jan–Jul 2025 discovery data, so PF 1.92 /
+0.40R / 56% WR are **upward-biased by selection** and will regress out-of-sample. **Disclose the provenance**
(how many parameter combinations were searched — the more tried, the larger the bias) in the threshold-
provenance doc, and treat the discovery numbers as **zero promotion evidence**. The lock-for-fresh-validation
discipline is the correct mitigation *only if the validation window was not used in selection.*

## Answers to the ten questions

**1. Logically sound & deterministic from completed bars?** **Yes.** Indexing is chronological and
completed-bar based: `shift_index(i,s)=i−s+1` ⇒ break (i−21…i−2) < retest (**i−1**) < confirmation (**i**);
`decision_time = m5[i].end` (confirmation close). EMA (seeded SMA→recursive) and ATR are from completed bars.
Deterministic (level choice = tightest-stop among daily/weekly/swing). No randomness.

**2. Lookahead / leakage / indexing / ATR / doc-vs-code?** No hard lookahead, and the filter↔outcome
separation is clean (outcomes computed once in `raw_outcomes`, filters only *select*). Same-bar SL+TP is
resolved **adverse-first** (`final_r=-1.0 if hit_sl else 1.5`) — correctly conservative. **But:**
- **Doc-vs-code ATR mismatch (must fix).** The candidate doc says ATR is "14 completed bars **ending before the
  retest bar**." The code `average_range(m5, confirmation_index, 2, 14)` spans i−1…i−14 — i.e. it **includes
  the retest bar (i−1).** Not lookahead (i−1 is completed), but the documented rule ≠ the implemented rule;
  MQL parity will fail or ship the wrong rule unless reconciled.
- **Frictionless fills** (B1): entry at exact `entry_price`, exits at exact SL/TP, no spread/slippage.

**3. Is the baseline correction correct?** **Yes.** `apply_b0_comparisons` uses B0's **opened** (one-position-
gated) trades as the denominator: `virtual_trade_retention_pct = pct(opened, b0_opened)`; B0 itself passes
through the same `candidate_available_at_index` one-position gate (1453 accepted → 885 opened); median-weekly
retention is gated vs B0's median weekly. Correct.

**4. Enough to justify locking as a V2 candidate for fresh validation?** **Conditionally.** It clears the
*discovery eligibility* gate (retention 40%/55%, ≥100 trades, PF≥1.20, exp≥+0.10R, deltas, blocked<kept, bad-
signal −28.5%, both regimes) — which our plan treats as "worth a fresh validation," nothing more. But the
eligibility was computed **gross of cost** and **in-sample-selected**, so re-state it net (B1) before locking,
and lock it **only** as a fresh-validation hypothesis. It is **not** evidence of edge.

**5. Overfit from 15 / 0.45 / 0.60 / 0.05 ATR?** **Yes — high risk** (see B2). The oddly specific tuned values
+ the name-encoded parameters are the classic optimization signature. Require provenance and OOS validation.

**6. Treat the June 2026 replay as supporting only?** **Weaker than that — treat it as essentially
non-evidence.** 38 trades, gross of cost, on the *exact period being repaired*. +1001 AED / +27R / 68% WR on
38 cost-free trades is well within noise and the +1001 overstates net. Context at most; do not cite it.

**7. Tests to add before MQL.** Cost-applied-metrics test (net = gross − cost_r); ATR-window definition test
pinning the *reconciled* spec; same-bar SL+TP adverse-first test; explicit no-lookahead/index-order assertions
(break<retest=i−1<confirmation=i; sim starts at i+1); one-position-gating test; EMA-seed + Wilder-ATR golden
test; determinism/golden-file test on a fixed fixture; first-retest / invalid-close-between edge tests.

**8. MQL parity checks before attach.** MQL must reproduce, ≥99% of decisions / **100% of accepted**: the
indexing + decision-at-close, EMA seeding and the **reconciled** ATR window, every filter boolean, entry/SL/TP
geometry **within 1 point**, the adverse-first same-bar exit, and the cost_r computation — **and apply cost
identically.** Any UNKNOWN mismatch on an accepted signal = NO-GO.

**9. Fresh validation gates before demo trading on 1033669.** Forward **tick-level**, **cost-applied**, on a
window **not used in selection**: ≥100 closed trades / ≥20 days / ≥4 weeks / ≥25 long + 25 short / ≥3 weeks×15,
both rising+falling regimes; **net** PF ≥1.30, **net** expectancy ≥+0.15R, frequency floor (retention ≥40%),
P95 cost_R ≤0.15, concentration caps, max consec ≤8, DD ≤8R, parity ≥99%/100%, zero duplicate-family events,
mutex + containment built, reviewer signoff, owner approval of exact source/binary/hypothesis/contract hashes.

**10. Verdict — `BUILD_ONLY`.** Implement the shadow observer + tick engine + Python parity (no broker action,
isolated terminal), **after** fixing B1 (apply cost) and B2 (provenance) and the ATR doc-code mismatch. Do
**not** shadow-*attach* until those are fixed and the metrics are restated net. Do **not** demo-trade. A3 stays paused.

## Bottom line
No leakage, good discipline (promotion_evidence=False everywhere, discovery≠validation, adverse-first exits) —
but the impressive numbers are **gross-of-cost and in-sample-tuned**, so the real net edge is unproven and may
be small or zero. Fix the cost model, disclose the threshold search, reconcile the ATR definition, then carry
it forward as a shadow hypothesis. The forward, cost-applied, out-of-sample window is what decides it — and the
honest prior remains that it may not survive.

**Boundary:** review only. Demo only. A3 paused. No reactivation; canonical Phase 2/3 unchanged.
