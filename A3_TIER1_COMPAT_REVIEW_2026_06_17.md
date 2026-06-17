# Pre-Attachment Review — A3_BREAKOUT_TIER1_COMPAT_V1 (2026-06-17)

Reviewer: Claude. Scope: **XAUUSD, A3 demo `1033669`, repo-side only.** Reviews the new tier1-compat
lane against source, preset, tests, and the diagnosis it implements.
**This review does NOT authorize MT5 attachment.** Attachment requires a separate owner packet (§Q9).

## Verdict: **PASS_WITH_CONDITIONS**

The build is **correct and safe repo-side.** The breakout kernel is untouched, the A2-style session
gate and stop floor are implemented correctly and in the right place, the trend guard is genuinely
shadow-only, the new shared-base macros default OFF so the live plain/improved lanes are preserved, and
committed defaults are non-executing. There are **no code blockers.** The conditions are process gates
(owner packet, real compile proof, observer-first attach) plus two recommended test additions.

## What I verified (source-level)

| Check | Result | Evidence |
|---|:--:|---|
| Breakout **kernel unchanged** | ✅ | Wrapper is 22-line macro+include; base calls the same `g_breakout_observer.Evaluate(...)` (base line 1029). Gate/floor/shadow wrap the kernel, don't alter it |
| **Session gate** correct + fail-safe | ✅ | `ServerHourInTradeSession()` (208): disabled→`return true`; enabled→in-window with wrap-around; blocks at line 617 `SERVER_HOUR_SESSION_GATE`. Server-hour basis matches A2 |
| **Stop floor** correct + fixes tight stops | ✅ | `SendMarketOrder` lines 728–742: `≥stops_level+5`, `≥3×spread`, `≥300pt XAUUSD`; widens risk and **recomputes SL, TP, and cost_R** (745, 772) from the floored stop |
| **Plain/improved unaffected** by new macros | ✅ | New macros default **false** in base `#ifndef` (lines 37–44); plain/improved don't define them → gate/floor/shadow OFF. Pre-existing cost/spread caps unchanged |
| **Trend guard is shadow-only** | ✅ | `trend_shadow_pass` computed + logged (1038–1040, 1042) but never feeds `guard_pass`; active guard off (`InpTrendGuardEnabled=false`) so it cannot block (1043) |
| **Magic/comment/log separation** | ✅ | Magic `933400` hard-locked at init (line 994); comment `A3_BREAKOUT_TIER1_COMPAT`; `a3_breakout_tier1_compat_*` logs — distinct from plain/improved/A2 |
| **Committed defaults non-executing** | ✅ | Base `InpDryRunOnly=true`, `InpBrokerActionAllowed=false` (52–53); preset reaffirms; arming gate `ARMING_DISABLED`; no armed preset committed |
| **Compiles by inspection** | ✅ (pending real compile) | `CurrentSpreadPoints` @165, `TrendDirection` @522, `stops_level`/`spread_distance` defined locally @730–732. No undefined symbols seen — but a MetaEditor compile is still required (§Q9) |

## Answers to the ten review questions

**Q1 — Copies A2 protections without changing the kernel?** **Yes.** Same unchanged `Evaluate` kernel;
gate + floor are added around it. Thin wrapper, identical pattern to plain/improved.

**Q2 — Session gate correct and safe?** **Yes.** Disabled returns "in session" (so other lanes are
unaffected); enabled passes only inside `[start,end]` server hours with wrap-around; outside →
hard block. Hour-granular and server-time-based, matching A2's 12–15 gate.

**Q3 — Stop floor correct, and does it fix the tight-stop weakness?** **Yes.** It lifts the stop to the
max of broker stops-level, 3×spread, and 300pts (XAUUSD), then rebuilds SL/TP and recomputes cost_R
from the wider stop. *Honest nuance:* the floor only **binds** on sub-300-pt stops; A3 plain's actual
stops were already >300, so its main value here is parity/safety, not the primary fix — the **session
gate** is the bigger lever. Correctly implemented regardless.

**Q4 — Old plain/improved unaffected by the new default-macro design?** **Yes — and this is the most
important check.** The three new macros (`SESSION_GATE_DEFAULT`, `STOP_FLOOR_DEFAULT`,
`TREND_SHADOW_DEFAULT`) default **false** in the base; plain/improved don't define them, so they inherit
gate/floor/shadow OFF. Running lanes are compiled `.ex5` (untouched now); on any future recompile they'd
keep safe behavior **as long as those base defaults stay false** — which is exactly why I want a test
locking them (below).

**Q5 — Magic/comment/log separation clean enough?** **Yes.** `933400` is hard-locked (init fails on
mismatch), with its own comment and four dedicated log files. No merge risk with `933200`/`933300`/A2.
*Add:* document/reserve the `933400` band in the magic manifest (it currently lists only 933200–933299).

**Q6 — Committed defaults non-executing and safe?** **Yes.** Dry-run + broker-action-off in both source
and preset; full scope locks (symbol, demo server, login `1033669`, kill switch); no armed preset
committed. Tested.

**Q7 — Tests sufficient for repo-side approval?** **Sufficient to lock the safety strings, with gaps.**
The five tests cover kernel-share, magic separation, non-executing defaults, scope locks, per-lane
guard/exit flags, preset safety, and the compat gate/floor/shadow wiring. Gaps (non-blocking, add before
or alongside attach):
1. **No test that the base `#ifndef` defaults for the 3 new macros are `false`** — the exact invariant
   protecting plain/improved (Q4). Add it.
2. No test that plain/improved **omit** the new macro defines.
3. Tests are **static-string only** — they cannot catch compile errors or logic bugs, so a real
   MetaEditor compile (0/0) remains required.

**Q8 — Is the PnL estimate honest?** **Honest in direction and properly labeled, but two of three numbers
are tiny-sample and must not be read as forecasts.**
- *Strict A3 replay (0 trades, 0 AED, −96.39 avoided):* **Solid and the right primary claim.** All six
  A3-plain losers were outside 12–15 server, so the gate allows 0 → avoids the loss cluster. **But note:**
  this proves it *avoids losers*, not that it *makes money* — it also captured 0 upside. Avoiding loss ≠ profit.
- *A2 proxy (8 trades, 50%, +104.92):* Honest **as a labeled proxy** (it's A2's record, not A3's), but
  8 trades is too small to predict.
- *Evening breakout since 06-01 (12 trades, 83.3%, +478.66):* Honest as a proxy but **regime-flattered** —
  10/12 wins over an up-trending fortnight is not a sustainable rate. Do **not** promote on this number.
- **Required framing:** lead with the strict replay (avoids the loss cluster); present both proxies as
  small-sample, regime-exposed, indicative-only. The profit case is unproven until forward evening fills.

**Q9 — Runtime packet/checklist required before attaching** (per the repo's established convention):
1. **Owner authorization packet** explicitly APPROVING A3 `933400` attach (separate doc, APPROVE/DECLINE recorded).
2. **MetaEditor compile proof: 0 errors / 0 warnings.**
3. **Profile backup** of the A3 terminal (quarantine copy) before attach.
4. Attach with the **committed safe preset** (dry-run) or a **separate owner-armed local preset** — never commit an armed preset.
5. **Startup-log verification:** login `1033669`, server Demo, magic `933400`, comment, dry_run/broker_action flags, scope-lock PASS, kill-switch present.
6. **Zero pre-existing `933400`** orders/positions baseline.
7. **A1, A2, A3-plain (933200), A3-improved (933300) untouched** — process + magic proof.
8. **Pre-registered pass/fail criteria** recorded before any broker-action arming.
9. **Reconciliation report** after attach; **kill-switch tested.**

**Q10 — Attach as broker-action, observer-only first, or not yet?** **Observer/dry-run first — not
broker-action yet.** Attach with the safe preset so it logs would-signal + gate + floor + trend-shadow
on live ticks **without placing orders.** This confirms (a) the lane actually *generates* evening-window
signals (the strict replay produced 0 trades — we must verify it trades at all in 12–15), (b) gate/floor
behave on live data, (c) shadow accumulates would-block evidence. Promote to broker-action demo only
after the dry-run validates those **and** the owner packet approves.

## Critical blockers (to attachment)
None are code defects. Attachment is blocked until: **(1)** a separate owner authorization packet exists,
**(2)** a MetaEditor compile proof (0/0) is attached, and **(3)** it is attached observer/dry-run first,
not broker-action. (These are the boundaries the owner already set; this review enforces them.)

## Non-blocking improvements
1. Add a test asserting the base defaults `SESSION_GATE_DEFAULT`/`STOP_FLOOR_DEFAULT`/`TREND_SHADOW_DEFAULT`
   to **false** (locks the plain/improved-protection invariant).
2. Reserve/document magic `933400` in the magic-band manifest.
3. In the design doc, re-label the +104.92 and +478.66 proxies as **small-sample / regime-exposed,
   indicative-only**, and lead with the strict-replay "loss-cluster avoided" number.
4. Optional: make the session gate minute-aware if A2 is ever changed to a non-hour boundary (today hour-granular parity with A2 is correct).

## Exact changes required before MT5 attachment
- Produce the **owner authorization packet** (APPROVE A3 933400 observer attach).
- Produce the **0/0 MetaEditor compile proof** for `Account3BreakoutTier1CompatExecutor`.
- (Recommended, can be concurrent) add the base-macro-default test and the manifest entry.
- Attach **observer/dry-run** using the committed safe preset; verify startup logs and zero pre-existing 933400 orders.

## Should owner approval authorize A3 attachment for this lane?
**Yes — but only an OBSERVER/DRY-RUN attach, via a separate packet.** The build earns a repo-side PASS.
Owner approval should authorize attaching the **safe (non-executing) preset** to A3 to collect live
gate/floor/shadow evidence. **Broker-action arming is a later, separate decision** contingent on the
dry-run showing the lane generates evening signals and behaves, plus the pre-registered pass/fail and
owner sign-off. Do not commit an armed preset.

**Boundary:** review only. Demo only. No MT5 runtime, EA, preset, chart, order, or account change is
authorized by this document.
