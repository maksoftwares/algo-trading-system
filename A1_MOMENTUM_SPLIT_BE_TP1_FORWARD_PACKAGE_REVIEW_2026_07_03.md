# INDEPENDENT REVIEW — SPLIT-ENTRY BE-ON-TP1 FORWARD-TEST PACKAGE
Date: 2026-07-03 | Reviewer: Independent (Claude) | Offline only.

## VERDICT: REVISE — two narrow blockers, then pre-authorized APPROVE_FOR_SMALL_DEMO (no re-review needed)

This is the best-constructed spec the project has produced. It resolves, in writing, every condition
I have carried across three reviews: dedicated magic 932280, dedicated comment prefix, DEDICATED
kill-switch filename (the collision is finally closed for this lane), USD package-guard confirmation,
pinned tie-break priority, pinned start timestamp, explicit owner-acceptance block, the May
anti-overfit clause, gates matching my recommended numbers, weekly attribution checks, and the
long-window debt with a pre-committed 15% degradation trigger. Checksums verified independently:
spec SHA `8daa…b560` ✓ matches its .sha256.json; EA source SHA `3b54…84bf` ✓ matches.

## Blocker 1 — the priority stack exists on paper, not in the runtime
The forward book's evidence (recent-3M and 4-year) was composed OFFLINE: three separate tester runs,
then cross-component 4-minute same-direction dedupe with fixed priority (v6 → weak_hours → v13).
I inspected the EA: GlobalVariables track only per-ticket BE/partial state. There is NO cross-instance
mechanism that enforces "if multiple components fire, keep only the highest-priority one" on a live
chart set. As specified, three attached charts would sometimes ALL fire on overlapping signals —
the demo lane would trade a different (heavier, overlap-stacked) book than the one reviewed.
Required: implement runtime cross-instance signal claim (e.g., GlobalVariable lock keyed by
direction+bar-time: first-priority component claims the slot; lower-priority instances check and
skip within the 4-minute window), plus a smoke test showing a simultaneous-signal case resolving to
one component. This is a small, mechanical piece of code — but without it the forward test does not
test the reviewed candidate.

## Blocker 2 — quantify the exposure in the owner-acceptance block
"Two minimum-lot tickets" understates the practical worst case. With `InpUseRiskNormalizedLots=true`
(target $10/1R) and the min-lot-pair fallback dominating at typical XAU stops, the REAL per-signal
worst case is ≈ 2 × stop distance ≈ −$20 to −$36 (stop ceiling $18). The recent window's average
signal LOSS was −$28.37 — consistent with this, not with $10. Add one line: "worst case per signal
≈ −$36; typical loss −$20 to −$30; ~⅓ of signals lose both tickets." The owner should sign a number,
not a lot size. (Also note `InpMaxRiskLots=0.05` permits larger-than-min tickets when stops are
small; if that path is unwanted for V0, cap it at 0.02 in the frozen preset.)

## Answers to the eight questions
1. **May overfitting** — PASS. The spec forbids May-fitting explicitly, gates are May-agnostic, May's
   PF 0.54 is disclosed rather than repaired. Correct posture.
2. **Frozen tightly enough?** — Yes on identity/inputs/SHA; No on runtime composition (Blocker 1).
3. **Owner terms complete?** — Nearly; exposure must be quantified (Blocker 2). Everything else
   (demo-only, no Phase 2, no live, both-ticket loss, May clause) is present and clear.
4. **Recent 3M evidence sufficient?** — Yes, at experimental-lane standard, per my prior review
   (65.6% signal WR, PF 1.58, n=64, CI 53–77%, one day = 48.5% of net → hence the 30% day gate).
5. **Does the completed weak-hours long-window leg change my confidence?** — Yes, modestly UP with a
   caveat. The fixed component is solidly positive over four years (1,614 trades, +1,857, PF 1.486,
   DD 11%) — the structure survives the full window with the fix. The caveat: the fix cost this
   component −13.6% net vs its unfixed twin (PF unchanged) — just inside the 15% pause line, and it
   confirms my prediction that BE-on-TP1 buys its protection by clipping retrace-then-run winners.
   If V6/max2 shows worse than −15%, the pre-committed pause fires; watch it.
6. **V6 timeout at 3600s** — acceptable engineering debt, not an attach blocker. The narrowing
   (weak_hours completed at the same timeout) supports the log-volume hypothesis. Debt deadline
   stays: all three components + recomposed ledger within 4 weeks of attach.
7. **Reduced/aggregate management logging** — yes, the correct fix, tester-only, keep aggregate
   counts (BE_MODIFY_OK totals etc.) so management behavior stays auditable. Do not alter strategy
   logic to fix a logging problem.
8. **Gates strict enough?** — Yes. They match my recommended numbers (WR≥55% vs 57.8%… note: at
   W/L 0.79 signal-level, breakeven WR ≈ 56% — the 55% floor is tight-but-acceptable given PF≥1.25
   and the cost-haircut net>0 must ALSO pass; keep all three conjunctive as written). Kill gates
   sound; no-streak-kill clause is correct for a 33%-both-lose book.

## Sequence to attach
1. Codex: Blocker 1 (runtime claim/dedupe + smoke evidence) and Blocker 2 (one-line exposure quant,
   optional 0.02 lot cap) → re-hash spec + EA, update .sha256.json.
2. Owner: sign the acceptance block (with the quantified exposure).
3. Attach per process; pin first-fill timestamp; I check week-1 fills for magic/comment/BE events and
   for overlap-stacking (Blocker 1 verification in real data).
4. Codex: logging fix → V6/max2 + v13 long-window reruns → recomposed fixed ledger within 4 weeks;
   auto-pause if any component degrades >15% vs unfixed.
