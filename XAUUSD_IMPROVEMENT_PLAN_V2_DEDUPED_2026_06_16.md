# XAUUSD Improvement Plan — v2 (deduped, real-fill evidence) — 2026-06-16

Scope: **XAUUSD only.** Demo-only. Status: `REVIEW_READY`.
Boundary: evidence + planning document. It approves **no** live trading change and requests no
change to running EAs without separate owner/reviewer sign-off. Nothing this week touches runtime.

Supersedes `XAUUSD_OBSERVER_LESSONS_AND_IMPROVEMENT_PLAN_2026_06_16.md` (v1). v1's conclusions were
built on **raw, stacked** broker rows; this v2 is built on **deduped, real-fill, day-stress-tested**
evidence (`XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16`), independently verified.

---

## 1. Corrected conclusion (the headline changed)

v1 said: "a profitable core being diluted by weak variants." **That was a duplication artifact.**
On unique signals the gold system is **not profitable — it is a net loser.**

| View | Signals | Win rate | PnL | Profit factor |
|---|---:|---:|---:|---:|
| Raw closed XAUUSD fills | 1,163 | 39.29% | **+649.74** | 1.03 |
| **Deduped unique signals** | 586 | 37.80% | **−554.52** | 0.95 |

The same signal was counted ~2× by stacked EAs (577 duplicate rows, **+1,204 AED of phantom PnL**),
which flipped a real −554 loss into an apparent +650 profit. **Use deduped numbers for every
decision from here.**

The real structure of the book, deduped, is simple:

- **One genuine, robust edge: the breakout core (+1,059 AED).**
- **One large drag: the round family (−1,382 AED).**
- **Everything else is small and negative** (session-extreme −144, p2weakness −14, repairs −22,
  WR50 −74).

So the objective is not "trim a profitable system." It is:

```text
Isolate the breakout core, quarantine the round family, and stop counting duplicates as edge.
```

---

## 2. The one real edge — and it is robust

| Group | Signals | Win rate | PnL | Best day removed | Best 2 days removed |
|---|---:|---:|---:|---:|---:|
| **breakout_core** (breakout_retest + swing) | 112 | 47.8% | **+1,059** | +772 | **+506** |
| round_family | 432 | 36.6% | −1,382 | −1,425 | −1,485 |
| session_extreme | 38 | 26.3% | −144 | — | — |
| p2weakness | 1 | — | −14 | — | — |
| session-extreme repair | 0 | n/a | 0 | — | — |

The breakout core is the only cluster that **stays clearly positive after removing its best two
days (+506).** That is the test the other clusters fail — and it is what makes breakout the thing
we protect and build around.

Note: `breakout_retest` (101 signals, +893) and `swing_breakout_retest_v0` (11 signals, +166 after
dedup) are **one edge, not two** — swing is largely breakout's co-fire (raw 84 → 11 unique). Treat
them as a single breakout entry.

---

## 3. What evaporated under dedup (do NOT protect these)

| Cluster | Raw PnL | Deduped PnL | Reality |
|---|---:|---:|---|
| swing_breakout_retest_v0 | +912 | **+166** | clone of breakout; ~85% was duplicates |
| p2weakness_br_v1 | +548 | **−14** | 9 of 10 trades were duplicates; no edge |
| session_extreme_repair_v1 | +348 | **0** | every signal was a duplicate |
| **"SELL evening"** | +2,407 | +679 → **−92** (best 2 days removed) | a 2-day artifact (Jun 9–10), not an edge |
| **"BUY night"** | +845 | +327 → **−491** (best **1** day removed) | one-day artifact |

v1 listed several of these as "strong/protected." On deduped, day-stress-tested data they are
noise or period-luck. **Demote them; do not let them anchor any rule.**

---

## 4. Sessions and direction, corrected

Deduped sessions: Afternoon is the only robustly-bad window (−523, stays bad); Evening is the
least-bad (+339) but **thins to −64 when its best two days are removed** — i.e. "evening is good"
is mostly "breakout-in-evening," not a standalone session edge.

Deduped direction×session: every "good" cluster is day-fragile (SELL-evening and BUY-night both go
negative when 1–2 days are removed), while **BUY-afternoon is robustly terrible (−592, 16% win).**

**Conclusion:** there is no stable static direction/session edge. A static "protect SELL-evening /
block BUY-afternoon" rule would be fitting to the period's down-trend. The only defensible
directional idea is a **dynamic trend-alignment guard** (don't trade against the prevailing
higher-timeframe trend), which must be shadow-proven, not assumed.

---

## 5. The plan

### Step 0 — Decide on deduped numbers only (done)
All figures above are deduped/real-fill/day-stress-tested and independently verified. This is the
baseline of record.

### Step 1 — Protect the core (the only thing we cannot break)
Protected set = **the breakout entry** (breakout_retest + its swing co-fire), with emphasis on its
strong contexts (evening, night). Standing rule:

```text
No proposed filter may be promoted if it improves total PnL by removing protected breakout signals.
Every filter must report how many protected breakout trades it would have blocked.
```

### Step 2 — Round-family quarantine (first shadow test, highest impact)
Move `round_number_retest_v0` and `symbol_normalized_round_retest_v0` to **observer-only** (log
would-be outcomes; place no round trades). Reversible. Deduped non-round PnL is ≈ **+828** and the
pure breakout core is **+1,059**, so quarantining round is what turns the book from −554 to positive
— it is necessary, not optional. Pre-register the success bar; confirm forward that round keeps
losing and breakout is untouched.

### Step 3 — Dynamic trend-alignment guard (shadow only)
Tag each signal as with/against the H1/H4 trend and **log** outcomes. Do NOT deploy a static
direction×session rule. Only if with-trend signals robustly beat against-trend across up-days,
down-days, and chop — best-days removed — does this graduate.

### Step 4 — Exit protection for the breakout core (backtest + shadow)
MFE/MAE evidence (237 path-covered trades): breakout trades run far in favor (avg MFE **+1.04R**),
and ~44% of breakout losers first went ≥+0.5R green. Test **one or two pre-chosen** rules only —
`breakeven at +0.5R` and `partial at +1.0R` — applied to **winners and losers alike.**
Curve-fit guard: winners' average adverse excursion is **0.46R**, just under the 0.5R trigger, so a
breakeven rule **will clip some winners** — the required output is the *net* (losers saved minus
winners clipped), not the give-back count.

### Step 5 — Promote only after forward proof (gates in §7)

---

## 6. Research tickets (priority order)

| # | Ticket | Why |
|---|---|---|
| 1 | `XAU_ROUND_FAMILY_QUARANTINE_SHADOW` | Removes the −1,382 drag; turns the book positive. Lowest complexity. |
| 2 | `XAU_DYNAMIC_TREND_GUARD_SHADOW` | The only defensible (non-static) version of the direction lesson. |
| 3 | `XAU_BREAKOUT_EXIT_PROTECTION_BACKTEST` | Breakout losers often go green first; test BE/partial on full paths. |
| 4 | `XAU_PROTECTED_CLUSTER_AUDIT` | Standing guard so no filter ever deletes the breakout edge. |
| 5 | `XAU_BREAKOUT_FORWARD_WEEK` | Keep accumulating real-fill days on the one real edge. |

(Dropped from v1: any rule resting on p2weakness, session-repair, or static SELL-evening/BUY-night.)

## 7. Promotion gates (ALL required before any runtime change)
1. Computed on **deduped, real broker fills** (not raw, not replay).
2. Net benefit **survives removing the best 1–2 days.**
3. Confirmed **forward in shadow** over ≥3–4 weeks / ≥~30 affected unique signals — not just retrospectively.
4. **Protected breakout signals unharmed** (protected-cluster audit attached).
5. Improvement is clearly **outside noise**, and not the period's trend (holds on up-days and down-days).
6. Owner + reviewer sign-off.

## 8. No-go conditions (block if any are true)
- Benefit disappears when the best 1–2 days are removed.
- Benefit exists only retrospectively, not forward.
- It removes or harms protected breakout evening/night signals to manufacture PnL.
- It relies on a static long/short or session bias instead of dynamic trend state.
- The supporting cluster is < ~30 deduped signals or < ~5 independent days.
- The "edge" is the realized trend of the sample (test on both up and down days).

## 9. Hidden risks / alternative explanations
- **Period-trend masquerading as edge** (biggest): SELL +1,878 / BUY −1,228 raw is "gold fell this
  fortnight," not "sell gold." Confirmed by the best-day-removed collapses.
- **Duplication** (now corrected): inflated the entire baseline by +1,204; still latent in any
  un-deduped slice.
- **Few-day dominance:** SELL-evening = Jun 9–10; BUY-night = one day. Re-check every new cluster.
- **Small samples:** session-extreme/repair/p2weakness/WR50 are tiny and negative deduped.
- **Multiple comparisons:** slicing EA×direction×session manufactures extreme cells by chance.
- **Exit-rule winner-clipping:** the 0.5R breakeven trigger sits under winners' 0.46R adverse excursion.

## 10. Exact next implementation steps (this week = observe only)
1. Stand up **round-family quarantine as observer-only** (no round trades placed; would-be outcomes logged).
2. Stand up the **dynamic trend-alignment guard in shadow** (log with/against-trend outcomes).
3. **Backtest + shadow** the two pre-chosen exit rules on full winner+loser paths; report net effect.
4. Run the **protected-cluster audit** against every proposed filter.
5. Continue the **nightly deduped real-fill scan**; accumulate forward days on the breakout core.
6. Change **no runtime EA, preset, or arming** until a rule clears all §7 gates with sign-off.

## One-line summary
On real unique signals the gold book loses (−554); the only durable edge is the breakout core
(+1,059, survives best-2-days-removed). Quarantine the round family to recover it, make any
directional rule dynamic not static, drop the duplicate-inflated "strong" clusters, and promote
nothing until it survives best-day-removal and forward shadow on deduped real fills.
