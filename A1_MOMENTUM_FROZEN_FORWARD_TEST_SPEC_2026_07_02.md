# FROZEN FORWARD-TEST SPEC — A1 XAU M5 MOMENTUM (directional_session_htf_both)
Date: 2026-07-02 | Author: Independent Reviewer (Claude) | Status: DRAFT FOR OWNER APPROVAL
Verdict basis: APPROVE_FOR_SMALL_FORWARD_DEMO (reconfirmed 2026-07-02 with new caveats, §8)

## 0. Purpose
Convert the diagnostic Q2-2026 backtest edge of the `directional_session_htf_both` variant into
decision-grade evidence via a pre-registered, frozen, small-size demo forward test. The forward
test is the correction for the best-of-7 selection bias; nothing in this spec may be tuned after start.

## 1. Candidate identity (FREEZE)
- Strategy: A1 XAU M5 Momentum, variant `directional_session_htf_both` (both directions, session
  filter + HTF (H1/D1) trend-alignment gate), exactly as backtested in
  `outputs/reports/mt5_backtests/a1_momentum_variants_q2_2026_20260701/`.
- Freeze procedure: commit the EA source + .set parameter file; record SHA256 of both in this doc
  before attach. Any source or parameter change after attach = TEST VOID, restart from week 0.
- Dedicated magic number (new, unused — proposal: 940101) and unique comment `A1_M5_MOM_FWD_V1`
  so forward fills are separable in deals.csv. Must not collide with any existing 9xxxxx lane.
- No sibling variants may run live during the test window (re-introduces selection at forward stage).

## 2. Reference expectations (from Q2 backtest, recomputed by reviewer 2026-07-02)
- n=101, net +1,997 AED, WR 57.4%, PF 2.14; ex-top-5 +1,544; 3/3 months positive; max day 11% of net.
- LONG 20 / +554; SHORT 81 / +1,443. Sessions: night 58/+886, evening 23/+557, morning 20/+554.
- Trade rate ~7.9/week. Avg win +64.6, avg loss −40.7 AED (0.01 lot). Max trade-seq DD −238 AED;
  worst day −170; max consecutive losses 5.

## 3. Runtime configuration (demo only)
- Account: demo (Capital.ComMena-Demo). Fixed 0.01 lot, no scaling, no martingale, no averaging.
- Hard guards in EA/preset: max 4 trades/day; daily loss stop −150 AED; global kill switch at
  cumulative −600 AED (≈2.5× backtest max DD) → EA disables itself, test ends as FAIL_DD.
- Demo-only + symbol allowlist (XAUUSD) + magic check enforced in code. broker_action semantics:
  this lane places demo orders by design; all other governance flags unchanged (no real capital,
  not canonical Phase 2, no ML consumption).
- Attach is owner-approved manual action. Reviewer does not touch runtime.

## 4. Duration and sample
- Window: 8 calendar weeks from first fill, or until n≥60 closed trades, whichever is LATER;
  hard cap 12 weeks (if n<60 by week 12 → INCONCLUSIVE_LOW_ACTIVITY, likely filter/regime mismatch).
- No interim parameter review. Weekly evidence export only (§6). No peeking-based stops other than §5 fail gates.

## 5. Pre-registered gates (set BEFORE start; no post-hoc additions)
PASS (all required):
- n ≥ 60 closed trades; PF ≥ 1.30; net > 0 after removing top-5 winners;
- no single day > 25% of gross net; both directions have ≥1 winner;
- max drawdown ≥ −600 AED never breached; ≥ 2 of the test months net-positive.
FAIL (any triggers stop/reject):
- kill switch (−600 AED cumulative) hit;
- PF < 0.80 once n ≥ 40;
- 10 consecutive losses (backtest max was 5);
- evidence of config drift (checksum mismatch) → VOID.
GREY ZONE: n ≥ 60 and PF in [1.00, 1.30) → EXTEND once by 4 weeks; if still <1.30 → REJECT.
Statistical note: at n=60, a true WR of 57% has a ~±12.5pp 95% CI; PF 1.30 (vs backtest 2.14) is the
lower bound consistent with a real but regressed edge at this sample size. Backtest is frictionless
vs demo fills — expect PF shrinkage from spread/slippage; that is part of what this test measures.

## 6. Evidence discipline
- Money truth = A1 demo deals.csv (entry/exit paired by position_id; net = profit+commission+swap+fee).
- Weekly export: closed-trade CSV + cumulative scoreboard vs §2 expectations (no action taken on it).
- Session bucketing: deal time epoch UTC +4h (Dubai). Formal reads at week 4 (health check: activity
  rate and guard integrity only — NOT performance) and at test end (gates §5).

## 7. Outcomes
- PASS → candidate promoted to "validated on forward demo"; owner may consider size/scope extension
  under a new spec. Still not live capital.
- REJECT/FAIL → candidate archived; no re-tuning-and-rerun of the same family without a new
  hypothesis registered first.
- INCONCLUSIVE → one extension max (§5); then archive or re-register.

## 8. Reviewer caveats attached to this test (new evidence, 2026-07-02)
Recomputed from `a1_momentum_variants_two_year_2024_07_2026_06_core_usd_20260701/`:
- TWO-YEAR baseline_both (2024-07→2026-06): n=2,845, net −400, PF 0.97, 9/24 months positive.
- TWO-YEAR short_only: n=1,695, net −996, PF 0.87.
- TWO-YEAR baseline evening-only subset: PF 0.81 → the SESSION filter alone does NOT generalize.
Implication: the unfiltered strategy has no long-run edge; all of the Q2 edge is attributable to the
HTF-alignment component and/or the Q2 regime. CONDITION: Codex must run the two-year backtest of
`directional_session_htf_both` itself (same freeze) BEFORE or in parallel with the forward test.
- If two-year filtered PF ≥ ~1.2 with ≥55% positive months → forward test proceeds with full standing.
- If the filtered variant is flat/negative over two years → the candidate is a regime-specific play;
  forward test may still proceed (it is cheap and demo-only) but the PASS outcome must be labeled
  REGIME_CONDITIONAL and any extension requires an explicit regime-gate definition.
Long side remains thin (n=20 in Q2): forward long-side results are monitored but cannot alone
qualify or disqualify the candidate at n<20 forward longs.

## 9. Approval block
- Owner approval to attach: ______  Date: ______
- EA source SHA256: ______  |  .set SHA256: ______
- First fill timestamp (Dubai): ______
