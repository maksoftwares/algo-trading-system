# Review — XAUUSD Dynamic Profit-Lock Proposal (2026-06-17)

Reviewer: Claude. Scope: **XAUUSD, demo only.** Reviews `XAUUSD_DYNAMIC_PROFIT_LOCK_PROPOSAL_2026_06_17.md`
+ MFE/MAE evidence. **Analysis only — does not approve any broker-action/live/demo deployment; canonical
Phase 2/3 unchanged.**

## Verdict: **REVISE_BEFORE_TEST**

The idea is sound, the proposal is unusually disciplined (real 10-second **path** replay, not an MFE/MAE
shortcut; "don't deploy"; separate exit-EA; forward-week first), and because it's shadow-only the risk is
zero. But the scorer must be **revised before it's built**, for one decisive reason: its headline result
**contradicts our own prior `REJECTED_FOR_DEPLOYMENT` exit-rule finding**, and that contradiction has to be
reconciled or the shadow scorer will hand us a false green light. Fix the methodology (below), start with
the conservative rung, then test.

## Main concerns

**1. It contradicts the prior rejected exit test — reconcile before trusting the numbers.**
Our prior exact-path work rejected Partial+BE (reduced duplicate-hidden PnL by 134 AED, dragged 21 winners,
**saved 0 losers**) and BE-only (0 saved, 0.00 improvement). This proposal shows **BE-after-+1.0R = +580**
and lock variants up to **+1,113**. Both can't be right on the same book. The likely reconcilers:
- **PnL basis.** The prior used **duplicate-hidden (deduped)** PnL; this control (−1,638.80) looks like it
  may be **raw/co-fired**. Duplication would inflate the gain (the same saved trade counted ~2×). **Recompute
  the replay on the deduped unique-signal universe** — if the gain shrinks materially, the contradiction is
  explained and the rule is weaker than it looks.
- **Trigger depth.** Prior BE likely armed at +0.5R (which clips winners — their avg MAE is **0.4739R**);
  here BE arms at +1.0R. Deeper arming genuinely clips fewer winners, so "BE" isn't the same rule. State this.

**2. Coverage is 28% and recent.** Only **356 / 1,282** closed trades have path snapshots (the observer is
new). Conclusions apply to a recent, regime-limited subset — enough to justify a shadow test, **not** to
generalize. Treat every replay number as "covered-subset, retrospective."

**3. The aggressive rung sits inside normal winner noise.** Winners' average adverse excursion is **0.4739R**.
The `+0.75R → lock +0.25R` rung requires only a **0.5R** retrace to fire — i.e. about the *average* winning
trade's pullback. So that rung will clip a large share of eventual-TP winners; its +1,113 is the most
sample-/regime-fragile result in the table, not the safest. (It also touches the most trades: 89 vs 23.)

**4. Hindsight risk is low but not zero.** The path replay is the right method (it counts winners cut early).
Residual issues: 10-second granularity can mis-order an arm-then-breach inside one interval, and the virtual
floor assumes a **clean fill at the floor on a reversing market** — real fills will be worse. Add a
**slippage haircut** and report sensitivity; otherwise the replay is optimistic.

**5. Duplicate handling — right intent, must be enforced in the net.** Scoring "by family" is good, but the
**net must be computed on deduped representatives** (one per unique signal) so a saved/clipped co-fire isn't
counted 2–3×. Separately, a "shared family-level lock" **across accounts** can't be done by a single
per-terminal manager — it needs the FILE_COMMON / GlobalVariable shared mechanism. Within-account is fine.
Spec the scope explicitly.

## Recommended rule version (for the shadow test)

Start the shadow with the **conservative near-TP rung as the primary candidate**, ladder tracked beside it:

```text
PRIMARY (least invasive):  arm at +1.25R  -> lock +0.80R     (23/356 changed; targets near-TP reversals)
SECONDARY (compare):       arm at +1.00R  -> lock +0.50R     (55/356 changed)
DEFER (highest clip risk):  arm at +0.75R  -> lock +0.25R     (89/356; only if dedup + cross-regime support it)
Keep TP +1.50R · keep SL until a floor arms · never widen risk — all correct as proposed.
```

Rationale: the +1.25R/+0.80R rung only fires on trades already 0.25R from target, so it rarely clips a real
winner and directly fixes the "almost-TP then reversal to SL" pain (the exact 18:55 flip case). Earn the
lower rungs forward; don't anchor on the aggressive one.

## Acceptance criteria (all required before any broker-action deployment)
1. **Net positive on the DEDUPED universe** (losers-saved − winners-clipped), in R and AED — not raw.
2. **Reconciled** with the prior rejected BE/partial result (basis + trigger-depth explanation attached).
3. **Survives best-1–2-days-removed.**
4. **Holds across regimes** — includes the 2026-06-17 down day **and** ≥1 more down/range day, not just up days.
5. **Confirmed forward** in a fresh shadow week, not only retrospectively on the 356.
6. **Protected breakout evening/night cluster** net-improved or unharmed (report its delta explicitly).
7. **Winner-clip cost stated** (how much TP-R is given up) and **slippage-haircut sensitivity** shown.
8. Owner + reviewer sign-off; **separate exit-manager EA**; reversible; no execution-enabled preset committed.

## Failure conditions (reject the rule)
- Net is negative on deduped data, or only positive because of duplication.
- Benefit is regime-specific / single-day-driven, or vanishes best-day-removed.
- The forward shadow week doesn't replicate the retrospective gain.
- It harms the protected breakout cluster (clips evening winners).
- The prior-rejection contradiction can't be reconciled.
- Path-order can't be validated (hindsight) or gains evaporate under a realistic slippage haircut.

## Implementation notes for Codex (before building the shadow scorer)
1. **Build it as a separate guardian/exit-manager EA** (read-only scorer first) — do **not** edit any entry
   EA. Agree fully with the proposal here; preserves kernel parity and makes the family lock feasible.
2. **Scorer walks the 10-second path in chronological order:** arm a floor only when the path reaches its
   trigger; exit at the floor only if the path later breaches it **before** TP; record control vs each variant.
3. **Compute the net on the canonical deduped universe**; report raw vs deduped side by side (this is the
   prior-rejection reconciler).
4. **Slice every result by regime (up/down), session, direction, and family; add best-day-removed.**
5. **Apply a slippage haircut** to floor exits and report how much of the edge survives.
6. **Expand path-snapshot coverage going forward** so the forward week isn't 28%-covered.
7. Keep it **shadow-only** (broker action off); emit `WOULD_LOCK` / `WOULD_EXIT` log rows, change nothing.
8. Defer the cross-account family lock to a later phase; note it needs the shared-file/mutex mechanism.

## Answers to the ten questions (quick map)
1. Enough for a shadow test? **Yes**, with the coverage/dedup caveats. 2. Hindsight? **Method is sound
(path-based); add dedup + slippage.** 3. Cuts too many TP winners? **The aggressive rung, yes; conservative,
minimal.** 4. +0.75/+0.25 too aggressive? **Yes — defer it.** 5. +1.25/+0.80 safer first? **Yes — make it
primary.** 6. Separate exit-manager EA? **Yes, strongly.** 7. Acceptance criteria? **Above.** 8. Failure
conditions? **Above.** 9. Duplicates handled? **Intent yes; enforce deduped net + clarify cross-account
lock.** 10. Change before building? **Reconcile vs prior rejection on deduped basis; start conservative; add
regime-split, best-day-removed, slippage, forward week.**

**Boundary:** review/analysis only. Demo only. No MT5 runtime, EA, preset, order, chart, or account change is
authorized. Not approved for broker-action; canonical Phase 2/3 unchanged.
