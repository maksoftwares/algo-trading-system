# Deep Dive — Were Last Week's Profits Real? Does Multi-EA Agreement Mean Anything? (2026-06-13)

All numbers recomputed from `PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv` (1,510 rows,
2026-06-01 → 2026-06-13 00:15, account 1025742/"A1"). "Raw" = every closed trade
including duplicate clones. "Kept"/"dedup" = one row per duplicate-key group
(`duplicate_role != duplicate`), i.e. what survives the T0 mutex fix.

---

## 1. The "+1000 last week / +2000 the other day" feeling — what the ledger actually shows

| Day | Raw closed PnL | Dedup (kept-only) PnL | Raw intraday peak |
|---|---:|---:|---:|
| Jun 1 | -78.68 | -25.35 | +19.6 |
| Jun 2 | +54.54 | +21.60 | +217.4 |
| Jun 3 | -90.62 | -48.54 | +247.2 |
| Jun 4 | -45.36 | +20.65 | +85.3 |
| Jun 5 | +325.05 | +64.21 | +630.7 |
| Jun 8 | +185.52 | +32.72 | +416.7 |
| Jun 9 | **+391.89** | **-384.39** | **+866.9** |
| Jun 10 | **+530.89** | **-361.99** | +696.7 |
| Jun 11 | -795.64 | -379.52 | +390.9 |
| Jun 12 | -2456.43 | -1078.01 | +71.1 |
| Jun 13 (partial) | +14.97 | -17.96 | +65.9 |
| **Cum. through Jun 10** | **+1273.23** | **-681.09** | — |
| **Cum. Jun 1–13** | **-1963.87** | **-2156.58** | — |

**The "+1000 last week" number is real on the raw ledger** — cumulative raw PnL
peaked at **+1,273 AED through Jun 10**, and Jun 9 alone touched **+867 intraday**
(closest match to "the other day, ~2000" — the live terminal equity swing was
likely larger still, since this file only counts closed trades, not floating P/L
of positions still open at that moment).

**But on the de-duplicated ledger, Jun 9 and Jun 10 are losing days (-384, -362),
and the cumulative-through-Jun-10 figure is -681, not +1,273.** The entire
"+1,273 feeling" is concentrated in two days where duplicate clones happened to
be on the winning side of the trade more often, in larger clusters, than the
"kept" representative of each duplicate-group. Removing duplication (T0) doesn't
selectively cut losers — on Jun 9–10 specifically, it cuts what *looked* like the
best two days of the project.

---

## 2. Why de-dup flips Jun 9 / Jun 10 from + to −

Per-candidate kept vs. duplicate split (closed trades only):

**Jun 9:** `symbol_normalized_round_retest_v0` kept = **-326.34** (n=47);
`round_number_retest_v0` = 0 kept / **-90.88** all-duplicate (n=40);
`session_extreme_retest_v0` kept = **-126.07** (n=12).
**Jun 10:** `symbol_normalized_round_retest_v0` kept = **-308.66** (n=98);
`round_number_retest_v0` mostly duplicate again.

Checked against Review 13's pairing logic: **156 of 157 duplicate-groups on these
two days are same-sign** (one mixed-sign pair found, EURUSD 12:40 on Jun 10).
So this is *not* "duplicates lost while the kept trade won" — it's that **the
round-family kernel itself lost on Jun 9/10** (symbol_normalized alone: -326 and
-309), and those losses happened to be in *smaller* duplicate-clusters than the
winning clusters elsewhere (breakout/session/repair lanes), so raw totals came
out positive while the de-duped "one trade per signal" reality was negative.

**Conclusion: the round-family kernel was already losing money on what felt like
the two best days of the project. Duplication was masking that, not causing it.**

---

## 3. Would the brakes (G3 streak-breaker + G4 daily stop, round-family only) have made it worse?

Simulated chronologically on **kept (deduped)** trades only, G3 = 3 SLs in 2h →
pause to next 4h boundary, G4 = round-family day PnL ≤ -150 → no more entries
that day. Breakout and session families left untouched (matches the A3 design —
G1–G4 apply to round-family only).

| Day | Round raw | Round + G3/G4 | Blocked trades | Breakout (untouched) | Session (untouched) | **Day total w/ brakes** | Day total (dedup, no brakes) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Jun 1 | -113.80 | -114.96 | 4 | +39.55 | +48.90 | -26.51 | -25.35 |
| Jun 2 | +70.63 | +36.20 | 1 | +31.29 | -80.32 | -12.83 | +21.60 |
| Jun 4 | -157.54 | -92.93 | 4 | +160.90 | +17.29 | +85.26 | +20.65 |
| Jun 5 | +28.51 | +110.00 | 3 | +94.81 | -37.98 | +145.70 | +64.21 |
| Jun 8 | +15.37 | +15.14 | 2 | +70.94 | -0.72 | +32.49 | +32.72 |
| **Jun 9** | -348.57 | **-162.16** | 36 | +90.25 | -126.07 | **-197.98** | -384.39 |
| **Jun 10** | -296.90 | **-167.21** | 91 | -49.42 | -15.67 | **-232.30** | -361.99 |
| **Jun 11** | -384.67 | **+17.43** | 86 | -48.44 | +53.59 | **+22.58** | -379.52 |
| **Jun 12** | -417.90 | **-138.60** | 65 | **-530.77** | -129.34 | **-798.71** | -1078.01 |
| Jun 13 | -17.96 | -17.96 | 0 | 0 | 0 | -17.96 | -17.96 |
| **12-day total** | | | | | | **≈ -1030** | -2156.58 |

**Honest answers to your question:**

- The brakes *help* — round-family-with-brakes total ≈ **-1030 vs -2157** dedup-only
  (a ~+1,126 AED improvement over 12 days), and they turn **Jun 11 from -380 to
  +23** (the streak-breaker would have stopped round-family before the worst of
  that day's damage).
- They do **not** turn Jun 9/Jun 10 back into winning days. Round-family is still
  negative on both (-162, -167) even with brakes — just less negative than
  uncapped (-348, -297). The day-level totals (-198, -232) stay negative because
  round-family's loss now exceeds breakout/session's contribution.
- **Jun 12 is not fixed by any of this.** Even with round-family capped at -139,
  the day is still -799 — because **breakout_retest itself lost -531 (deduped),
  across XAUUSD, EURUSD, AND GBPUSD, in every time bucket** (see §5). None of
  G1–G4 touch breakout by design (it's frozen on A2). This is the gap that
  matters most for "next week."

So: yes, under de-dup + the round-family brake stack, the period Jun1–13 looks
like **a smaller, steadier loss (-1030) instead of a rollercoaster that peaked at
+1,273 and crashed to -1,964** — net less bad, but it never produces the "+1000
feel-good" number, because that number was mostly duplicate-driven on a kernel
that was already losing.

---

## 4. Does "multiple EAs agreeing on direction" mean anything?

Grouped all kept trades by (symbol, direction, entry M5-bar) and counted how many
**distinct families** (ROUND / SESSION / BREAKOUT / WR50) fired in that bar+direction
— this captures *genuine cross-logic agreement*, not exact-duplicate clones (which
Review 13 already showed carry zero extra information — same kernel, same bars).

| Group | n | Win rate | Total PnL | Avg PnL |
|---|---:|---:|---:|---:|
| Single family only | 714 | 34.5% | -2648.20 | -3.71 |
| **2+ distinct families agree** | 62 | **41.9%** | **+491.62** | **+7.93** |
| — of which BREAKOUT + ROUND | 27 | 48.1% | +268.54 | +9.94 |
| — of which ROUND + SESSION | 18 | 38.9% | +206.41 | +11.47 |
| — of which BREAKOUT + SESSION | 15 | 33.3% | -6.15 | -0.41 |

**Your intuition has support, with a real caveat on sample size (n=62).** When a
structure-based signal (breakout) and a level-based signal (round) independently
point the same direction in the same 5-minute bar, win rate jumps from 34.5% to
48.1% and the bucket is profitable (+268 over 27 trades) — that's *different
logic reaching the same conclusion*, which is closer to genuine confirmation.
BREAKOUT+SESSION agreement (n=15) shows no edge — so it's not "any agreement
helps," it's specific to which families agree.

**This is NOT the same question as "duplicate clones agree."** Two clones of the
same kernel (symbol_normalized vs round_number_retest) always "agree" because
they're running the same code on the same bar — that's the 331=331 finding from
Review 11, and it carries zero extra information. The 41.9%/48.1% numbers above
exclude exact-duplicate clones; they measure independent-logic confluence.

**Recommendation:** this is promising but n=62 is too small to act on. Add a
`cross_family_confluence` flag to the signal/observer logs now (cheap — just the
group-membership computation above, done at signal time) so that by the time A3's
2-week window closes, there's enough data to evaluate this as a candidate filter
or position-size modifier for Phase B. **Shadow only, not a runtime change.**

---

## 5. Why Jun 12 (Friday) was different — breakout's own worst day

Breakout family (`breakout_retest` + `swing_breakout_retest_v0`), kept trades,
Jun 12: **37 trades, 6 wins, -530.77 AED** — every time bucket lost (Night -177,
Morning -119, Afternoon -92, Evening -142). This is the EA the whole portfolio
leans on, having its worst day on record, on every symbol, all day. This matches
the forensics' "Jun 12 = reversal day, trend-confirmed entries fought the fresh
impulse" finding — but the impulse-veto plan (A3) doesn't apply to breakout, and
correctly so (forensics showed breakout's counter-impulse trades normally win
50%). Jun 12 looks like a regime tail-event that the current design has **no
answer for on the breakout side**.

One concrete, evidence-backed observation: **23 of breakout's 26 EURUSD/GBPUSD
losses on Jun 12 were SL at 0.05 lot (-341.90 total)**. At XAUUSD's 0.01 lot, the
same SL hits would have cost roughly **-68 to -85 AED** — a ~260 AED difference
on this one day alone. The EUR/GBP lot-size question (A5, previously declined)
keeps resurfacing in the worst days specifically; it may be worth re-presenting
with this data point, separate from the A3 work.

I also tested a "portfolio circuit breaker" idea (pause everything if 3+ symbols
each take an SL within a rolling hour) — **it fires on Jun 9, 10, 11, AND 12** (all
four days hit "3 symbols, 1 hour"), so it doesn't discriminate good days from bad
ones on symbol-count alone. Not a usable rule as-is; parking it.

---

## 6. Bottom line for "how do we make next week better"

1. **T0 (A1 mutex fix) and A3 (round-family guarded lane, 1033669) proceed as
   planned** — nothing above changes that recommendation. If anything, §2–3 make
   the case *stronger*: the round-family kernel was losing even on the "good"
   days once you remove duplication, so the repair experiment is targeting a real
   problem, not a phantom one.
2. **Set expectations now, in writing, for the owner-authorization packet**: post
   T0, the account's headline PnL number will likely look *smaller and less
   exciting* on good days (no more +1,273-style peaks), because those peaks were
   substantially duplicate-driven. The honest trajectory (≈ -1030 over 12 days
   with brakes) is worse-feeling but more real, and it's the only thing the
   sizing ladder can safely be built on top of.
3. **New shadow item (cheap, additive):** log cross-family same-bar confluence
   (§4) on every signal row. No runtime effect; gives Phase B a second,
   evidence-aligned filter candidate (distinct from G1) by the time A3's window
   ends.
4. **Open question for the owner, not yet a recommendation:** Jun 12 shows
   breakout_retest itself can have a -530 day across the whole portfolio, with
   EUR/GBP's 0.05 lot contributing roughly half of that via SL size alone. A3
   doesn't address this (breakout is frozen by design — correctly, per the
   forensics). This may warrant its own small research item later, but it should
   not block or modify the A3 work order already sent to Codex.

Nothing here changes or delays the CODEX_WORK_ORDER_A3_REPAIR_LANE_2026_06_13.md
already sent. Item 3 can be added as a low-priority addendum task if you want it
in the same batch; item 4 is a flag for discussion only.
