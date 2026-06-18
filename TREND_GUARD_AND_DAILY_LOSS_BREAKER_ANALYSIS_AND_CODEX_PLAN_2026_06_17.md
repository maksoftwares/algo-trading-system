# What Went Wrong on the Flip — Analysis + Codex Plan (2026-06-17)

Author: Claude. Scope: **XAUUSD, demo only.** Analysis of the Day-3 down-day loss and a disciplined,
shadow-first plan for Codex. **No runtime change is authorized here; promotion is owner-gated.**

---

## Part A — What went wrong, step by step

**Step 0 — what the system is.** These EAs are a mean-reversion / break-retest system that fires in
**both directions mechanically** and closes each trade at its own stop or 1.5R target. There is no big
open position to "book" — each trade already books itself. So the loss wasn't "failing to take profit";
it was *what trades we kept taking*.

**Step 1 — Days 1–2 (UP).** Trend was up; the long side won; the account rose cumulatively. This felt
like "we were profitable."

**Step 2 — the system had no idea the trend was up.** No active trend filter was running — the trend
guard is **shadow-only** on the improved/compat lanes and **off** on the plain and A1 lanes. So the
"profit" on Days 1–2 was just the mechanical longs happening to align with an up market, not a system
that *knew* it was long-biased-correct.

**Step 3 — Day 3 the trend flipped DOWN** (gold ≈ −106 pts open→close). Nobody can predict that flip;
"profitable until the flip" is only knowable *after* it.

**Step 4 — the EAs kept buying into the fall.** With no active trend filter, the mechanical longs kept
firing **against** the down trend and got stopped out in bulk:

| Side (down day) | Trades | Win % | PnL_001 |
|---|---:|---:|---:|
| BUY (counter-trend) | 60 | 21.7% | **−728** |
| SELL (with-trend) | 22 | 40.9% | −114 |

On the breakout lanes alone, counter-trend longs won just **8.7%**.

**Step 5 — nothing stopped the bleed.** There is no active account-level loss limit, so the system fed
trades into the trend **all day** and gave back the Days 1–2 gains. The equity guardian that could have
halted it exists only as a **shadow observer**.

**Net:** −842 raw / −345 deduped on the day — driven by counter-trend longs, uncapped.

### The two structural gaps (this is the real "fix")
- **Gap A — direction risk: no *active* trend filter.** We take counter-trend trades. On *any* strong
  trend day the counter-trend side bleeds (today longs; on a strong up day it would be shorts).
- **Gap B — portfolio risk: no *active* daily-loss circuit breaker.** Once a day goes wrong we don't stop.

### What we honestly could NOT have done
- Predicted the flip, or "booked" a non-existent open profit.
- Fit a rule to "stop at the Day-2 peak" — pure hindsight; it also caps winners on continuation days.
- Statically banned longs — we'd lose on the next up week. The right tool is **dynamic** (follows trend).

### The proof we now have (today is the evidence, not the enemy)
- **Trend guard works:** the one lane with the guard *active* (improved 933300) lost **−36** today vs the
  plain lane's **−277** — same day, same market. And the up/down flip confirms *counter-trend* loses, not
  just "shorts lose." H3 is now supported across regimes (one down day).
- **Equity guardian is ready:** `AccountEquityGuardianShadow` already runs as a Stage-A observer, so we
  have the equity path to set a loss threshold from data.

So the fix is **not a new invention** — it is promoting **two things already in shadow** to active, with
pre-registered thresholds and owner approval.

---

## Part B — The fix (ranked)

1. **Activate the dynamic trend guard** (Gap A). Block entries against the prevailing H1/H4 trend.
   Dynamic, so it protects on down *and* up weeks. Strongest evidence we've had; directly addresses the flip.
2. **Activate a daily-loss circuit breaker** (Gap B). Pre-registered: halt new entries for the session
   once the day's drawdown hits a set limit. A *loss* limit, not a flip prediction — not hindsight. This is
   the principled version of "book / protect."
3. (Optional, lower priority) A daily profit give-back lock — workable but leaves money on the table;
   needs its own shadow test. Do not lead with it.

Both #1 and #2 must clear shadow evidence (incl. ≥1 more down/range day) and owner sign-off before going active.

---

## Part C — Codex Work Order (step-by-step, shadow-first, owner-gated)

Owner: Ali. **Demo only. Phase 1 is READ-ONLY. No EA/preset/arming/runtime change until Phase 3 with
explicit owner approval.** Anti-curve-fit rule throughout: **thresholds come from the full multi-day
distribution, never fit to the 2026-06-17 day.** End every phase with `git status` proving scope.

### Phase 1 — Quantify both fixes on real data (READ-ONLY)

**Step 1 — Trend-guard net effect, across regimes.**
- Use the committed shadow logs (`trend_shadow_pass` / `trend_shadow_reason`) plus the deduped real-fill
  rows for all tracked days (Day 1–3, both up and the down day).
- Tag every signal with/against the H1/H4 trend **using the existing shadow definition only** — do NOT
  grid-search `InpTrendH1LookbackBars` / `H4` / `MinMovePoints` (that is curve-fitting).
- Report, split by regime (up-days vs the down-day) and overall: counter-trend vs with-trend win rate and
  PnL_001; and the **net if the active guard had blocked counter-trend** = (losers saved − winners
  clipped) in R and AED, with **best-day-removed**.
- Output: `TREND_GUARD_NET_EFFECT_2026_06_xx.md`. Pass bar to pre-register: net positive on *both*
  regimes and survives best-day-removed.

**Step 2 — Daily-loss circuit breaker, replayed on the equity path.**
- Reconstruct each tracked day's intraday cumulative PnL path (per account, and book-level) from real fills.
- Pre-register **2–3 candidate thresholds from the distribution**, e.g. a daily-loss halt at the ~80–90th
  percentile of historical daily losses, or a fixed multiple of the median good-day range — **stated
  before** looking at today's number.
- For each threshold replay every day and report: loss averted, **winning days prematurely halted** (the
  cost), trades avoided, and net across all days. Show the tradeoff curve.
- Output: `DAILY_LOSS_BREAKER_REPLAY_2026_06_xx.md`. Pass bar: meaningfully caps bad days while halting
  ~no good days.

**Step 3 — Combined effect.** Replay both together (guard + breaker) across all days; report the joint net
and confirm they don't double-count. Output: `FLIP_PROTECTION_COMBINED_2026_06_xx.md`.

### Phase 2 — Shadow-deploy (NO broker action)
- Keep the trend guard **shadow** on all lanes; ensure the A1/Phase2 lanes also log a with/against-trend
  shadow tag (the A3 lanes already do).
- Run `AccountEquityGuardianShadow` as an **active-shadow**: it **logs a `WOULD_HALT` event** when a
  candidate threshold is breached, but **halts nothing**.
- Accumulate forward days, especially **≥1 more down or range day**. Output a rolling
  `FLIP_PROTECTION_SHADOW_FORWARD_2026_06_xx.md`.

### Phase 3 — Owner-gated promotion (only if Phase 1–2 pass)
- Promote **one at a time**, trend guard first (it's the direct fix), then the breaker.
- Pre-registered gates (all required): net positive **across up and down regimes**, survives
  best-1–2-days-removed, confirmed **forward in shadow**, **protected breakout evening/night untouched**,
  owner + reviewer sign-off.
- Runtime safeguards (per repo convention): profile backup → 0/0 compile → startup-log verify →
  zero pre-existing exposure → reconciliation → reversible. Commit no execution-enabled preset; arm via
  local owner preset only.

### Hard boundaries (do not)
- Do **not** change any running EA, preset, or arming in Phase 1–2.
- Do **not** tune trend or threshold parameters to fit 2026-06-17 (or any single day).
- Do **not** statically ban a direction; the guard must be dynamic (trend-following).
- Do **not** promote on up-regime-only or single-day evidence.
- Do **not** touch the protected breakout-core or the round quarantine via this work.
- Do **not** authorize live/real capital.

### Acceptance criteria
- Phase 1 reports exist with regime-split net, best-day-removed, and pre-registered thresholds.
- Shadow `WOULD_HALT` logging is live with broker action off.
- No runtime behavior changed without a separate owner-approved promotion packet.
- `git status` shows only analysis/report/shadow-logging files changed.

---

**Boundary:** analysis + plan only. Demo only. No MT5 runtime, EA, preset, order, chart, or account
change is authorized by this document.
