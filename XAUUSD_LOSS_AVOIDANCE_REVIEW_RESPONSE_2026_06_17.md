# Review Response — XAUUSD Loss-Avoidance Findings (2026-06-17)

Reviewer: Claude. Scope: **XAUUSD, demo only.** Reviews `XAUUSD_LOSS_AVOIDANCE_FINDINGS_FOR_CLAUDE_2026_06_17.md`.
**Boundary: review only. No runtime, EA, preset, order, chart, or account change is authorized here.**

## Verdict

**The findings document is numerically accurate and its direction is disciplined.** I independently
recomputed every family/session/scenario figure from the source rows
(`XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16_ROWS.csv`, 586 deduped signals) and they match to the
cent. The cost table matches its own source CSVs. The conclusions (quarantine round first, don't
hard-block shorts yet, promote nothing without forward proof) are sound.

Three things are **under-caveated**, and they shape the answers below:
1. **Two universes.** Family/session evidence = **586** signals; cost evidence = **704** bucketed
   (from a 906-signal set). They are different dedups and must not be composed as one expectancy.
2. **The cost cutoff is fragile** — the cumulative kept-PnL is highly non-monotonic and a single day
   (June 10) drove much of it in prior verification.
3. **Period exposure is not only about shorts** — the evening/night preference (79 signals, one
   fortnight) carries the same regime risk and deserves the same "unproven" tag.

## Verification ledger (claim → independently recomputed)

| Claim in findings doc | Source value | My recompute | Verdict |
|---|---:|---:|:--:|
| Deduped total | −554.52 (586) | −554.52 (586) | ✅ exact |
| Remove round (selected) | +804.89 (154) | +804.89 (154) | ✅ exact |
| Breakout core | +1059.34 (112) | +1059.34 (112) | ✅ exact |
| Breakout evening/night | +1027.32 (79) | +1027.32 (79) | ✅ exact |
| Round family | −1359.41 (432) | −1359.41 (432) | ✅ exact |
| symbol_normalized_round | −1270.55 (410) | −1270.55 (410) | ✅ exact |
| session_extreme | −143.78 (38) | −143.78 (38) | ✅ exact |
| No afternoon | −31.49 (504) | −31.49 (504) | ✅ exact |
| Sessions (aft/eve/night/morn) | −523.03 / +339.46 / −159.99 / −210.96 | same | ✅ exact |
| Cost cutoff flips +→− | 0.11 = +139.86 → 0.12 = −67.94 | same (cutoffs CSV) | ✅ exact |
| Cost universe size | (implied 586) | **704 bucketed / 906 signals** | ⚠️ different set |

Note: doc win-rates read ~0.3–1 pt higher only because it drops the 4 FLAT trades from the
denominator. Immaterial. (Also: my own earlier "round = −1382" was the approximation — the source and
the doc agree at **−1359.41**.)

---

## Answers to the ten questions

### Q1 — Is quarantining `round_family` justified? — **YES (strongest call in the doc).**
Round family is **−1,359.41 over 432 deduped signals at 36.3% win** — the bulk of the −554.52 book.
Removing it flips the book to **+804.89** (154 signals). It loses across regimes: down-trending prior
fortnight *and* both tracked up-days (Day 2 A3 round −125.21). So it's a no-edge **mechanism** (fading
levels into moving markets), not a direction artifact. It is disjoint from breakout_core, so quarantine
removes **zero** protected breakout trades (verified: protected 79 / +1027.32 unchanged).
**Honest framing:** "+804.89" is retrospective — the forward claim is "stop a persistent bleed," not
"book +805 of new profit." Already done on A3; the doc effectively proposes extending fleet-wide
(A1 still runs round lanes). **Recommend:** yes, first — but on A1 run it observer-only/reversible to
confirm forward before detaching, since A1 is the "accepted" account.

### Q2 — Is breakout evening/night a valid protected cluster, or too small? — **VALID TO PROTECT, too small to OPTIMIZE toward.**
79 signals, **+1,027.32**, ~52% win — genuinely captures +1,027 of breakout_core's +1,059 with 33
fewer trades (verified). But 79 signals / one fortnight is period-exposed: "evening/night is best" is
partly "this fortnight's evening/night caught the moves." **Protect** it (no filter may delete these
trades); do **not** build a rule that trades *only* evening/night — that optimizes toward a 79-signal
in-sample peak. The doc's guard pseudocode blurs this by making `session in Evening/Night` an ALLOW
condition; keep "protect" and "route-only-to" separate.

### Q3 — Is 0.11–0.12R a reasonable cost veto? — **DIRECTION yes, THRESHOLD not yet (fragile).**
Buckets support cheap > expensive (cheap three positive, expensive three negative). But the single
worst bucket is **0.09–0.11 (−408.86)**, not the >0.13 tail — so "danger above 0.11" is slightly
mis-stated; trouble starts at ~0.09. The 0.11→0.12 break-even is real in the cutoffs file
(+139.86 → −67.94) but the cumulative curve is wildly non-monotonic (+817 @0.04, +9 @0.06, +790 @0.08,
+140 @0.11), and prior verification found **June 10 drove much of the cost edge**. It's also computed
on the 704/906 universe, not the 586 set. **Recommend:** treat cost as a soft veto on *clearly*
expensive trades only (e.g., ≥~0.13–0.15, where every view agrees), shadow-only. Do **not** promote a
0.11–0.12 line until it is recomputed on the **same** deduped set as the family analysis and survives
best-day-removed forward.

### Q4 — Does the duplicate key (`symbol+direction+family+M5 bar`) miss cases? — **YES, three.**
(a) **Cross-family duplicates** — different families firing the *same* bet on the same bar (breakout +
round both SELL same bar — pervasive in Day-2 co-fires). Putting `family` in the key means these are
**not** deduped, yet they're the same market exposure. (b) **Adjacent-bar duplicates** — the same level
retested one M5 bar later. (c) **Price-cluster duplicates** — same level hit at slightly different
prices. **Recommend separating the two purposes:** for **exposure control** key on
`symbol + direction + M5 bar + entry-level band` (drop family, so cross-family same-bar stacking is
caught); for **attribution** keep family in the key. One key can't serve both.

### Q5 — `family+direction+M5 bar`, or add level proximity? — **Add level proximity for the exposure guard.**
Yes — for the mutex/exposure guard include an entry-level tolerance band (e.g., within a few points or
~0.5×ATR), because the same retest fires across bars and at slightly different prices; exact-bar
matching misses it. Keep it simple though: the dominant measured duplication is same-bar same-direction
across lanes/accounts, so start with `symbol+direction+bar(+small level band)`, measure residual
duplicates, and only add wider proximity if residuals are material. Don't over-engineer the key before
the data shows it's needed.

### Q6 — Are we overfitting to recent demo by preferring evening/night? — **PARTLY, yes.**
Two weeks of demo, 79 evening/night signals — the preference is in-sample. The *protect* logic is fine;
the *restrict-to* logic is where overfit enters. **Mitigation:** protect, don't restrict — keep taking
breakout across sessions, never let a filter remove the evening/night ones, and re-test the session
preference forward and across regimes. The **afternoon block** is better grounded than the evening/night
*preference* (afternoon bad in both the 2-week data −523 and both tracked days), but even that needs a
down-day before it's called regime-independent.

### Q7 — Safest to promote first (if only one)? — **ROUND-FAMILY QUARANTINE.**
Most evidence, most regime-independent, mechanism-understood, zero impact on protected breakout,
reversible, easy to audit. Nothing else clears that bar: cost is fragile, evening/night is period-exposed,
the duplicate-mutex is an exposure refinement. Round is the one rule whose case is already proven across
both regimes.

### Q8 — Evidence required before changing runtime EAs? — **the full gate set.**
1. Computed on deduped **real broker fills**, on **one** canonical universe (not raw, not replay, not a
   586/704 mix). 2. Net benefit **survives removing the best 1–2 days**. 3. Confirmed **forward in
   shadow** ≥3–4 weeks / ≥~30 affected unique signals. 4. **Protected breakout cluster unharmed**
   (audit attached). 5. Improvement clearly **outside noise** and holds on **up and down days**.
   6. **Any direction/session rule** additionally requires a **down or range day** in the sample.
   7. Owner + reviewer sign-off.

### Q9 — How to measure whether profitable trades are accidentally blocked? — **net-R accounting + protected audit.**
For each candidate filter, replay it over the deduped set and report: (a) losers blocked (n, R, AED);
(b) **winners blocked (n, R, AED)** — the number that matters; (c) **NET = saved − clipped** in R and
AED; (d) the same net with best 1–2 days removed; (e) protected-cluster delta (breakout evening/night
trades touched — must be ≈0). Promote only if net is clearly positive, protected clipping ≈0, and it
survives best-day-removal. **Never** judge a filter by losers-blocked alone — that's the hindsight trap.
The live A/B (plain vs improved) already *is* this instrument for the trend guard's winner-clipping.

### Q10 — Quarantine `session_extreme_retest_v0` now, or shadow? — **SHADOW (don't hard-quarantine yet).**
It's a loser (−143.78, 38 signals, 26% win) but **small** and not the main drain (round is −1,359). On
38 signals you'd risk acting on noise, and it doesn't clear the "large, consistent, mechanism-understood"
bar round meets. **Recommend:** keep it observer/shadow, fold into the same forward-eval; quarantine
only if it stays negative across regimes with ≥~30 more signals. Low priority. (On A3 it's already gone,
since A3 now runs only breakout — this is mainly an A1 question.)

---

## Consolidated promotion order (verified-evidence-ranked)

1. **Round-family quarantine** — fleet-wide, observer-first on A1 (already live on A3). *Proven both regimes.*
2. **Cross-lane same-bar exposure mutex** — key `symbol+direction+bar(+level band)`, *not* family (Q4/Q5). *Exposure control, low risk.*
3. **Afternoon reduction** — after a down-day confirms it isn't regime. *Well-grounded, needs one more regime.*
4. **Cost veto** — worst tier only (≥~0.13), and only after recompute on the 586 universe + best-day-removed. *Fragile; soft prior.*
5. **session_extreme decision** — after forward data. *Low priority.*

**Explicitly NOT yet:** hard short-block, and evening/night-only *routing* (protect ≠ restrict).

## One required reconciliation before composing any rules
Recompute the cost analysis on the **same** deduped signal set as the family/session evidence (the 586),
or rebuild everything on one canonical deduped set. The current proposal stacks rules measured on
different universes (586 vs 704/906); the combined expectancy is not trustworthy until they share a set.

## Boundary
Review only. No MT5 runtime, EA, preset, order, chart, or account change is authorized by this document.
Demo only throughout.
