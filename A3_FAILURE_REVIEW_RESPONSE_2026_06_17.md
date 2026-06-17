# Review — Why A3 Is Losing (response to A3_FAILURE_DIAGNOSIS_2026_06_17)

Reviewer: Claude. Scope: **XAUUSD, demo only.** Evidence-based review of `A3_FAILURE_DIAGNOSIS_2026_06_17.md`.
**Boundary:** review only; no edit to any running EA is recommended here. Any runtime change is a
separate, later, owner-approved step.

## Plain-English verdict

The diagnosis is **mostly right and well-evidenced on its core mechanism, but it over-credits one of
its two "biggest" causes, and both accounts' results are too small to be conclusive.**

A3's −99.62 is **not a broad A3 problem — it is almost entirely the 6-trade plain-breakout lane
(−96.39).** The two retired round lanes net to roughly flat over A3's full history (guarded −38.20,
structured **+34.97**). So the real question is narrow: *why did the plain-breakout lane go 0-for-6?*

The honest answer: A3 plain takes the **unfiltered slice A2 throws away.** A2 only trades a late/evening
window (all 8 of its trades fell 16:00–19:10 Dubai) where breakout signals have **wide natural stops**
(A2 losers averaged ~884-point stops). A3 plain has **no session gate**, so it traded morning/afternoon/
night signals with **tighter stops** (~340–440 points) — worse sessions, higher cost-in-R, and several
counter-trend. That is a real structural disadvantage. But it is **one cause wearing two hats** (the
session gate), not two independent causes — and 6 trades is far too few to call the lane "broken"
rather than "structurally disadvantaged and also unlucky."

I verified the two load-bearing source claims directly: **both are true in the code.** I also found the
**stop-floor claim is mis-attributed** as a cause of this loss cluster (details below).

## Confirmed causes (verified against source and data)

| # | Cause | Evidence | Confidence |
|---|---|---|---|
| 1 | A3's loss is the **plain-breakout lane**, not the round lanes | A3 history: plain −96.39 of −99.62; round lanes net ≈ −3 (guarded −38.20, structured +34.97) | **High** |
| 2 | **A2 has a session gate; A3's breakout base has none** | `Phase2…Executor.mq5` `ServerHourInTradeSession()` + gate at line 1300, preset `InpTradeSessionGateEnabled=true` (12–15 server). `A3BreakoutExecutorBase.mqh` has no session/hour gate input | **High (source)** |
| 3 | A3 plain trades **outside** A2's window | All 6 plain trades were Afternoon/Morning/Night; **zero** in the evening window; A2 logged `server_hour_session_gate` blocks on overlapping signals | **High** |
| 4 | **A2 enforces a stop-distance floor; A3 does not** | A2 lines 1388–1395: `min_distance ≥ 3×spread` and `≥300 pts` for XAUUSD, then `signal_risk = max(...)`. A3 base lines 653–661 send **raw observer risk**, no floor | **High (source)** |
| 5 | A3 plain runs with **trend guard + exit protection OFF** | A3 plain preset `InpTrendGuardEnabled=false`, `InpBreakevenEnabled=false`, `InpPartialTakeProfitEnabled=false` (by design — it's the control) | **High** |
| 6 | A2's stops are genuinely **wide**, A3 plain's **tighter** → higher cost-R on A3 | A2 losers' moves ≈ 884 pts avg (1085/1042/1040/370); A3 plain ≈ 340–440 pts; cost_R ≈ 0.06 (A2) vs ≈ 0.13 (A3) | **High** |
| 7 | A3 **improved** lane blocked the same signals (so far) | Day-2 + diagnosis: improved blocked all would-signals via `TREND_AGAINST_SIGNAL` / `COST_R_CAP_BLOCK`; 0 improved orders | **Medium** (small n) |

## Uncertain / challenged causes

| Claim | My finding | Verdict |
|---|---|---|
| "Wider **stop floor** is one of the two biggest causes of A3's higher cost-R" | The 300-pt floor is **non-binding** for the actual trades: A2 stops avg 884 (≫300), A3 plain stops 336/442 (>300). The cost-R gap comes from **which signals each took** (A2 evening = wide stops; A3 all-day = tighter), i.e. a **consequence of the session gate**, not the floor. | **Over-credited.** Floor is a real *latent* gap, not the proximate cause here |
| "A2's session gate is why A2 is positive" | The gate's *value* rests on the big session evidence (evening +339 vs afternoon −523 over 586 signals), **not** on A2's 8 trades. A2's +104 on 8 trades can't prove the gate by itself | **Over-credited from A2 alone**; supported by the larger dataset |
| A3 plain is a failed strategy | 0/6 under a ~45% win assumption has a **2.8%** chance by luck — unlikely but not conclusive. The slice is structurally worse *and* the sample is tiny | **Mostly structural, partly variance** |
| A3 losses are "normal variance" | Round lanes ≈ flat; plain lane's loss is amplified by a biased (worse) signal slice + small-sample bad luck. Not *pure* variance, not *proven* skill gap | **Mixed** |
| Any source/config bug | The **stop-floor asymmetry** is a real design inconsistency (not a crash). No other bug: A3 scope-locks, magic locks, arming gate all correct | **One design gap, no bug** |
| "Round structured works on A3" (+34.97) | 25 trades, contradicts the 432-signal deduped round evidence (−1,359). Small-sample noise | **Do not believe** |
| A3 improved "fix works" | It blocked **6/6** losers (good) but has blocked **100%** of signals → **zero trades**. A guard that never lets a trade through isn't yet a viable lane | **Encouraging, unproven** |

## A2 vs A3 — which differences matter, and what to do with each

| Difference | Matters? | Action |
|---|---|---|
| **Session gate** (A2 evening-only; A3 none) | **Most** — drives session quality *and* the stop-width/cost-R gap | **Preserve / copy** to the repair lane |
| **Stop-distance floor** (A2 ≥300/≥3×spread; A3 none) | Latent robustness gap; non-binding now | **Copy** for parity/safety (cheap insurance) |
| **Trend guard + exits** (A2 n/a; A3 plain off, improved on) | Unproven; improved blocks 100% so far | **Shadow-test** in the new lane, don't hard-enable |
| **Cost cap** (A2 0.30 vs A3 0.15) | A3's is *tighter*; not the problem | Keep A3-style cap; not a cause |
| **Breakout kernel** | Identical (`Phase1BreakoutRetest`) — this is the edge | **Preserve unchanged** |
| **Magic/comment/logs** | Already separated | **Keep strict separation** |

## Recommended repair plan

**Yes — build a new copy, `A3_BREAKOUT_TIER1_COMPAT_V1`. Do not change A2 or the running A3 lanes.**

1. **Copy A2's session gate** (same server-hour window) — the single highest-value change.
2. **Copy A2's XAUUSD stop-distance floor** (≥3×spread, ≥300 pts) — parity + robustness, even though
   non-binding on current data.
3. **Keep the breakout kernel byte-identical** to A2/A3 (it's the edge; don't touch it).
4. **Trend guard = SHADOW-only first** (log would-block, place no block) — we cannot yet measure how
   many *winners* it clips, and it's currently blocking 100% of signals. Promote to active only after
   shadow shows net-positive (losers-saved − winners-clipped), best-day-removed.
5. **Breakeven/partial = test separately, not bundled.** Note partial **cannot** leave a runner at
   0.01 lot (broker min/step) — so it's breakeven-only in practice. Don't enable on day one.
6. **Required separation:** new magic (e.g., A3 933400 band), new comment `A3_BREAKOUT_TIER1_COMPAT`,
   new log files — must never merge with 933200/933300 or A2.
7. **Run it head-to-head with A2** on the same evening signals: configured identically (gate + floor),
   it should **match A2**. If it does, that *proves* the gate/floor were the difference.

## Pass/fail criteria for the repair experiment (pre-register before running)

| Criterion | Bar |
|---|---|
| Minimum sample | **≥30 closed trades** in the evening window, ≥ one fortnight, including **≥1 non-up regime** day-set |
| Max allowed loss (demo) | Pre-set halt-and-review threshold (owner sets, e.g. net ≤ −150 AED or a fixed drawdown) |
| Win-rate target | **≥ ~45%** (breakout-core baseline) and **not worse than A2's evening cohort** |
| PnL / PF target | Net **positive**, **PF ≥ ~1.2**, surviving **best-day-removed** |
| Fair comparison to A2 | Same symbol, same window, same kernel, same lot, same period; compare on **overlapping signals**. Compat ≈ A2 = gate/floor confirmed as the difference |
| Proof the fix worked | (a) Compat lane ≈ A2 on shared evening signals; **and** (b) once the trend-guard graduates from shadow, net-of-clipped improves vs plain, best-day-removed, forward — not retrospectively |

## Strict "do not do" list

- **Do not edit A2 or any running EA** to fix A3. Repair happens in a new, separately-magicked copy;
  any runtime change is a later owner-approved step.
- **Do not judge A3 plain or A2 on 6 / 8 trades.** Both are inside noise; conclusions need ≥~30.
- **Do not credit the stop floor** as the cause of the cost-R gap — it's non-binding here; the driver
  is the session gate / signal selection.
- **Do not hard-enable the trend guard** in the new lane first — shadow it (it's blocking 100%, and its
  winner-clip cost is unknown).
- **Do not bundle breakeven + partial** — partial can't leave a runner at 0.01 lot; test breakeven alone.
- **Do not retire A3 plain as a "failed product."** It's the **control** — its job is to take the
  unfiltered trades so we can measure what the filters save. Keep it as the baseline (pause only if the
  demo loss becomes material to the owner).
- **Do not conclude "round works on A3"** from the +34.97 structured lane (25 trades vs 432-signal
  evidence that round has no edge).
- **Do not over-fit to evening** — copy A2's gate to compare fairly, but the evening preference itself
  is still only one fortnight of demo (protect, don't optimize toward it).

## Reviewer-ready conclusion

The diagnosis correctly identifies the **mechanism**: A3 plain loses because, lacking A2's session gate,
it trades the non-evening, tighter-stop, partly counter-trend slice that A2 deliberately filters out —
and A3's headline loss is essentially this 6-trade lane, since the round lanes are ~flat on A3. Two
qualifications: the **stop floor is over-credited** (verified non-binding for these trades; the cost-R
gap is a *consequence* of the session gate, not the floor), and **both accounts' samples are too small**
to treat A2 as proven-good or A3 plain as proven-bad. The correct next step is exactly a **new
`A3_BREAKOUT_TIER1_COMPAT_V1` copy** — A2's gate + floor, strict magic/log separation, trend guard
**shadow-first**, breakeven tested separately — measured head-to-head against A2 on the same evening
signals with the pre-registered pass/fail above. No edit to A2 or the live A3 lanes is warranted on this
evidence. **A3 plain should be kept as the control lane, not retired.**

**Boundary:** review only. Demo only. No MT5 runtime, EA, preset, order, chart, or account change is
authorized by this document.
