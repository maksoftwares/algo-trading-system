# Reviewer Sign-Off — Round-Family Quarantine as First Runtime-Change Candidate (2026-06-17)

Reviewer: Claude. Scope: **XAUUSD, demo only.** Reviews `XAUUSD_AFTERNOON_ROUND_FAMILY_EVIDENCE_STEP`,
`XAUUSD_CANONICAL_LOSS_AVOIDANCE`, and the canonical rows CSV.
**This sign-off authorizes moving to the Owner Decision Step only. It does NOT authorize any runtime change.**

## Reviewer question

> Does the duplicate-hidden XAUUSD evidence support round-family quarantine/restriction as the first
> runtime-change candidate, while avoiding a broad afternoon ban and preserving breakout-core
> evening/night behavior?

## Answer: **YES — agree on all three parts.** This is the most robust call in the evidence base.

I independently recomputed every figure from the canonical 586-row CSV; all match to the cent (ledger
below). I also confirm the canonical report fixed the prior two-universe problem — family, session,
duplicate, protected-cluster, and cost views now sit on one 586-row universe, with cost restricted to
its cost-known subset. That correction is properly done.

**1) Round-family quarantine as the first candidate — supported, and uniquely robust.**
- Round family is the dominant drag: **−1,359.41** over 432 signals (36.6% win), and the two named
  candidates *are* exactly the round family — `symbol_normalized_round_retest_v0` (−1,270.55) +
  `round_number_retest_v0` (−88.86) = −1,359.41 (verified).
- It is the **most robust** finding here: best-day-removed −1,424 and best-two-days-removed −1,484 — i.e.
  it gets *worse* when its best days are removed. No lucky day is propping it up. That is the opposite of
  the few-day-artifact trap, and it is why round clears the bar that the direction/cost ideas do not.
- Removing it flips the deduped book from −554.52 to **+804.89** (154 signals).
- **Regime-independent:** it loses across the prior down-trending fortnight *and* both tracked up-days, so
  unlike the short/counter-trend ideas it does **not** need a down-day to be trusted. Safe to promote now.

**2) Avoid a broad afternoon ban — supported.**
- Afternoon −523.03 is **86% round** (−452.13). After quarantining round, the non-round afternoon residual
  is only **−70.90** over 27 signals — small and noisy.
- A blanket `no_afternoon` rule would remove **23 winners**, and its kept set goes **negative when the best
  day is removed** (−411). It would also delete the 11 afternoon breakout-core trades and any future good
  afternoon trades. Unnecessary and blunt — the round quarantine already captures the afternoon loss.

**3) Preserve breakout-core evening/night — supported and guaranteed by construction.**
- Protected cluster = 79 signals, **+1,027.32**, survives best-two-days-removed (+484).
- Round quarantine removes **0** protected rows (verified — round and breakout-core are disjoint by
  selected family). The fix cannot touch the protected cluster.

## Verification ledger

| Item | Report | Recompute | Verdict |
|---|---:|---:|:--:|
| Deduped baseline | −554.52 (586) | −554.52 (586) | ✅ |
| round_family | −1,359.41 (432) | −1,359.41 (432) | ✅ |
| two named candidates combined | −1,359.41 | −1,359.41 | ✅ |
| breakout_core | +1,059.34 (112) | +1,059.34 (112) | ✅ |
| quarantine kept (non-round) | +804.89 (154) | +804.89 (154) | ✅ |
| afternoon round / non-round | −452.13 / −70.90 | identical | ✅ |
| protected evening/night | +1,027.32 (79) | +1,027.32 (79) | ✅ |
| protected rows removed by quarantine | 0 | 0 | ✅ |

## Conditions to carry into the Owner Decision Step
1. **Scope = exactly these two candidates:** `symbol_normalized_round_retest_v0`, `round_number_retest_v0`.
   Do not bundle an afternoon ban, a cost rule, or any direction rule into the same change.
2. **Honest framing:** the +804.89 is retrospective. The forward claim is "stop a persistent, robust
   bleed," not "earn +805 of new profit."
3. **Reversible restriction** (observer-only / quarantine, not delete), so it can be unwound.
4. **Account context:** this canonical universe is account `1025742` (the lab account); these are its
   round lanes. (A3's round lanes were already dropped.)
5. **Runtime safeguards** from the evidence step apply: owner approves the exact item → profile backup →
   before/after chart report → startup/order-log verification after restart → score one fresh week against
   protected breakout-core impact.
6. **Do not** convert evening/night into evening/night-only routing; protect ≠ restrict.

## Reviewer decision
**AGREE — proceed to the Owner Decision Step.** Round-family quarantine/restriction is the first,
best-evidenced, most robust, regime-independent runtime-change candidate; a broad afternoon ban is not
justified; the protected evening/night breakout cluster is unaffected. **No EA/runtime change before
owner approval of the two named candidates.**

**Boundary:** review only. Demo only. No MT5 runtime, EA, preset, chart, order, or account change is
authorized by this document.
